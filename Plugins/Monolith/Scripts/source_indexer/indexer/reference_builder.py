"""Cross-reference extraction — finds call sites and type references."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from tree_sitter import Node, Parser

from .cpp_parser import CPP_LANGUAGE
from .ue_preprocessor import preprocess_ue_source
from ..db.queries import insert_reference

logger = logging.getLogger(__name__)


class ReferenceBuilder:
    """Second-pass extractor: walks parsed ASTs to find call references."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        symbol_name_to_id: dict[str, int],
    ) -> None:
        self._conn = conn
        self._sym_map = symbol_name_to_id
        self._parser = Parser(CPP_LANGUAGE)

    def extract_references(self, path: Path, file_id: int) -> int:
        try:
            source_bytes = path.read_bytes()
        except OSError:
            return 0

        clean_bytes = preprocess_ue_source(source_bytes)
        tree = self._parser.parse(clean_bytes)

        count = 0
        func_nodes: set[int] = set()

        for func_node in self._find_nodes(tree.root_node, "function_definition"):
            func_nodes.add(id(func_node))
            caller_name = self._get_function_name(func_node)
            caller_id = self._resolve_symbol(caller_name)
            if caller_id is None:
                continue

            for call_node in self._find_nodes(func_node, "call_expression"):
                callee_name = self._get_call_target(call_node, func_node)
                callee_id = self._resolve_symbol(callee_name)
                if callee_id is None or callee_id == caller_id:
                    continue

                line = call_node.start_point[0] + 1
                insert_reference(
                    self._conn,
                    from_symbol_id=caller_id,
                    to_symbol_id=callee_id,
                    ref_kind="call",
                    file_id=file_id,
                    line=line,
                )
                count += 1

            count += self._extract_type_references(func_node, caller_id, file_id)

        count += self._extract_class_scope_references(tree.root_node, file_id)
        count += self._extract_global_scope_references(tree.root_node, file_id, func_nodes)

        return count

    def _extract_type_references(
        self, func_node: Node, caller_id: int, file_id: int,
    ) -> int:
        count = 0
        seen: set[int] = set()

        for node in self._find_nodes(func_node, "type_identifier"):
            type_name = node.text.decode()
            type_id = self._resolve_symbol(type_name)
            if type_id is None or type_id == caller_id or type_id in seen:
                continue
            seen.add(type_id)

            line = node.start_point[0] + 1
            insert_reference(
                self._conn,
                from_symbol_id=caller_id,
                to_symbol_id=type_id,
                ref_kind="type",
                file_id=file_id,
                line=line,
            )
            count += 1

        return count

    def _extract_class_scope_references(
        self, root: Node, file_id: int,
    ) -> int:
        count = 0
        for class_node in self._find_nodes(root, "class_specifier") + self._find_nodes(root, "struct_specifier"):
            class_name = None
            for child in class_node.children:
                if child.type == "type_identifier":
                    class_name = child.text.decode()
                    break
            if not class_name:
                name_node = class_node.child_by_field_name("name")
                if name_node:
                    class_name = name_node.text.decode()
            if not class_name:
                continue

            class_id = self._resolve_symbol(class_name)
            if class_id is None:
                continue

            seen: set[int] = set()

            for bc_node in self._find_nodes(class_node, "base_class_clause"):
                for child in bc_node.children:
                    if child.type == "type_identifier":
                        base_name = child.text.decode()
                        base_id = self._resolve_symbol(base_name)
                        if base_id is not None and base_id != class_id and base_id not in seen:
                            seen.add(base_id)
                            insert_reference(
                                self._conn,
                                from_symbol_id=class_id,
                                to_symbol_id=base_id,
                                ref_kind="type",
                                file_id=file_id,
                                line=child.start_point[0] + 1,
                            )
                            count += 1

            for field_list in self._find_nodes(class_node, "field_declaration_list"):
                for type_node in self._find_nodes(field_list, "type_identifier"):
                    type_name = type_node.text.decode()
                    type_id = self._resolve_symbol(type_name)
                    if type_id is not None and type_id != class_id and type_id not in seen:
                        seen.add(type_id)
                        insert_reference(
                            self._conn,
                            from_symbol_id=class_id,
                            to_symbol_id=type_id,
                            ref_kind="type",
                            file_id=file_id,
                            line=type_node.start_point[0] + 1,
                        )
                        count += 1

        return count

    def _extract_global_scope_references(
        self, root: Node, file_id: int, func_nodes: set[int],
    ) -> int:
        count = 0
        class_types = {"class_specifier", "struct_specifier"}

        for child in root.children:
            if id(child) in func_nodes:
                continue
            if child.type in class_types:
                continue
            if child.type not in ("declaration", "expression_statement"):
                continue

            decl_name = None
            for sub in child.children:
                if sub.type in ("identifier", "field_identifier"):
                    decl_name = sub.text.decode()
                elif sub.type == "init_declarator":
                    for d in sub.children:
                        if d.type == "identifier":
                            decl_name = d.text.decode()
                            break

            decl_id = self._resolve_symbol(decl_name) if decl_name else None

            seen: set[int] = set()
            for type_node in self._find_nodes(child, "type_identifier"):
                type_name = type_node.text.decode()
                type_id = self._resolve_symbol(type_name)
                if type_id is None or type_id in seen:
                    continue
                if decl_id is not None and type_id == decl_id:
                    continue
                seen.add(type_id)

                from_id = decl_id if decl_id is not None else type_id
                if from_id == type_id:
                    continue

                insert_reference(
                    self._conn,
                    from_symbol_id=from_id,
                    to_symbol_id=type_id,
                    ref_kind="type",
                    file_id=file_id,
                    line=type_node.start_point[0] + 1,
                )
                count += 1

        return count

    def _find_nodes(self, node: Node, type_name: str) -> list[Node]:
        results: list[Node] = []
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == type_name:
                results.append(current)
            stack.extend(current.children)
        return results

    def _get_function_name(self, func_node: Node) -> str | None:
        for child in func_node.children:
            if child.type == "function_declarator":
                for fc in child.children:
                    if fc.type == "qualified_identifier":
                        return fc.text.decode()
                    if fc.type == "identifier":
                        return fc.text.decode()
        return None

    def _get_call_target(
        self, call_node: Node, func_node: Node | None = None,
    ) -> str | None:
        if not call_node.children:
            return None
        fn = call_node.children[0]
        if fn.type == "identifier":
            return fn.text.decode()
        if fn.type == "qualified_identifier":
            return fn.text.decode()
        if fn.type == "field_expression":
            field = fn.child_by_field_name("field")
            method_name = None
            if field:
                method_name = field.text.decode()
            elif fn.named_children:
                method_name = fn.named_children[-1].text.decode()
            if not method_name:
                return None

            if func_node is not None:
                argument = fn.child_by_field_name("argument")
                if argument is None and fn.named_children:
                    argument = fn.named_children[0]
                if argument and argument.type == "identifier":
                    var_name = argument.text.decode()
                    obj_type = self._resolve_local_var_type(func_node, var_name)
                    if obj_type:
                        qualified = f"{obj_type}::{method_name}"
                        if self._resolve_symbol(qualified) is not None:
                            return qualified

            return method_name
        return None

    def _resolve_local_var_type(
        self, func_node: Node, var_name: str,
    ) -> str | None:
        body = None
        for child in func_node.children:
            if child.type == "compound_statement":
                body = child
                break
        if body is None:
            return None

        for decl in self._find_nodes(body, "declaration"):
            for child in decl.children:
                if child.type == "pointer_declarator":
                    for sub in child.children:
                        if sub.type == "identifier" and sub.text.decode() == var_name:
                            for tc in decl.children:
                                if tc.type == "type_identifier":
                                    return tc.text.decode()
                elif child.type == "reference_declarator":
                    for sub in child.children:
                        if sub.type == "identifier" and sub.text.decode() == var_name:
                            for tc in decl.children:
                                if tc.type == "type_identifier":
                                    return tc.text.decode()
                elif child.type == "init_declarator":
                    for sub in child.children:
                        if sub.type == "pointer_declarator":
                            for psub in sub.children:
                                if psub.type == "identifier" and psub.text.decode() == var_name:
                                    for tc in decl.children:
                                        if tc.type == "type_identifier":
                                            return tc.text.decode()
        return None

    def _resolve_symbol(self, name: str | None) -> int | None:
        if name is None:
            return None
        sym_id = self._sym_map.get(name)
        if sym_id is not None:
            return sym_id
        if "::" in name:
            short = name.rsplit("::", 1)[-1]
            return self._sym_map.get(short)
        return None
