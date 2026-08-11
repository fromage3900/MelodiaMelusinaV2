"""C++ parser using tree-sitter for Unreal Engine source files.

Extracts classes, structs, enums, functions, variables, and UE macro metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

from .ue_preprocessor import preprocess_ue_source

CPP_LANGUAGE = Language(tscpp.language())

UE_MACROS = {"UCLASS", "USTRUCT", "UENUM", "UFUNCTION", "UPROPERTY", "UINTERFACE"}


@dataclass
class ParsedSymbol:
    """A single extracted symbol from a C++ file."""

    name: str
    kind: str  # class, struct, function, enum, variable, macro, typedef
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""
    access: str = ""  # public, protected, private
    is_ue_macro: bool = False
    base_classes: list[str] = field(default_factory=list)
    parent_class: str | None = None


@dataclass
class ParseResult:
    """Result of parsing a single C++ file."""

    path: str
    symbols: list[ParsedSymbol] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    source_lines: list[str] = field(default_factory=list)


class CppParser:
    """Parses C++ source files using tree-sitter and extracts symbols."""

    def __init__(self) -> None:
        self._parser = Parser(CPP_LANGUAGE)

    def parse_file(self, path: str | Path) -> ParseResult:
        """Parse a C++ file and return extracted symbols."""
        path = Path(path)
        source_bytes = path.read_bytes()
        clean_bytes = preprocess_ue_source(source_bytes)  # Strip UE macros for tree-sitter
        source_text = source_bytes.decode("utf-8", errors="replace")  # Original for display
        source_lines = source_text.splitlines()

        tree = self._parser.parse(clean_bytes)  # Parse cleaned version
        root = tree.root_node

        result = ParseResult(
            path=str(path),
            source_lines=source_lines,
        )

        result.includes = self._extract_includes(root)
        self._extract_symbols(root, source_lines, result)

        return result

    def _extract_includes(self, root) -> list[str]:
        includes: list[str] = []
        for node in root.children:
            if node.type == "preproc_include":
                for child in node.children:
                    if child.type == "string_literal":
                        path_text = child.text.decode()
                        path_text = path_text.strip('"')
                        includes.append(path_text)
                    elif child.type == "system_lib_string":
                        path_text = child.text.decode()
                        path_text = path_text.strip("<>")
                        includes.append(path_text)
        return includes

    def _extract_symbols(self, root, source_lines: list[str], result: ParseResult) -> None:
        children = list(root.children)
        i = 0
        while i < len(children):
            node = children[i]
            ue_macro = self._try_get_ue_macro(node)

            if ue_macro and i + 1 < len(children):
                next_node = children[i + 1]
                if next_node.type in ("class_specifier", "struct_specifier", "enum_specifier"):
                    self._extract_class_or_struct_or_enum(next_node, source_lines, result, ue_macro=ue_macro)
                    i += 2
                    continue
                elif next_node.type == "function_definition":
                    self._extract_misparse_class_or_function(next_node, source_lines, result, ue_macro=ue_macro)
                    i += 2
                    continue
                elif next_node.type in ("ERROR", "declaration"):
                    self._extract_class_from_error_node(next_node, source_lines, result, ue_macro=ue_macro)
                    i += 2
                    continue

            # After preprocessing, UCLASS'd classes should be clean class_specifier nodes
            if node.type in ("class_specifier", "struct_specifier", "enum_specifier"):
                ue_above = self._has_ue_macro_above(node, source_lines)
                self._extract_class_or_struct_or_enum(node, source_lines, result, ue_macro=ue_above)
                i += 1
                continue

            if node.type == "function_definition":
                self._extract_misparse_class_or_function(node, source_lines, result)
                i += 1
                continue

            if node.type == "ERROR":
                self._extract_class_from_error_node(node, source_lines, result)
                i += 1
                continue

            i += 1

    def _try_get_ue_macro(self, node) -> str | None:
        if node.type == "expression_statement":
            for child in node.children:
                if child.type == "call_expression":
                    fn = child.child_by_field_name("function")
                    if fn is None and child.children:
                        fn = child.children[0]
                    if fn and fn.type == "identifier":
                        name = fn.text.decode()
                        if name in UE_MACROS:
                            return name
        return None

    def _has_ue_macro_above(self, node, source_lines: list[str]) -> str | None:
        """Check original source lines above this node for a stripped UE class macro."""
        line_idx = node.start_point[0] - 1  # 0-indexed line above
        while line_idx >= 0:
            line = source_lines[line_idx].strip()
            if not line:
                line_idx -= 1
                continue
            for macro in ("UCLASS", "USTRUCT", "UENUM", "UINTERFACE"):
                if line.startswith(macro + "(") or line.startswith(macro):
                    return macro
            break  # Non-empty, non-macro line — stop
        return None

    def _extract_class_or_struct_or_enum(
        self, node, source_lines: list[str], result: ParseResult, ue_macro: str | None = None
    ) -> None:
        kind_map = {
            "class_specifier": "class",
            "struct_specifier": "struct",
            "enum_specifier": "enum",
        }
        kind = kind_map.get(node.type, "class")

        name = self._get_type_name(node)
        if not name:
            return

        base_classes = self._get_base_classes(node)
        docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
        sig_start = node.start_point[0]
        sig_end = node.end_point[0]
        sig_lines = source_lines[sig_start:sig_end + 1]
        signature = " ".join(line.strip() for line in sig_lines).split("{")[0].strip()

        symbol = ParsedSymbol(
            name=name, kind=kind,
            line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
            signature=signature, docstring=docstring,
            is_ue_macro=ue_macro is not None, base_classes=base_classes,
        )
        result.symbols.append(symbol)

        if kind in ("class", "struct"):
            body = None
            for child in node.children:
                if child.type == "field_declaration_list":
                    body = child
                    break
            if body:
                self._extract_members_from_field_list(
                    body, source_lines, result, parent_class=name,
                    default_access="private" if kind == "class" else "public"
                )

    def _get_type_name(self, node) -> str | None:
        for child in node.children:
            if child.type == "type_identifier":
                return child.text.decode()
        name_node = node.child_by_field_name("name")
        if name_node:
            return name_node.text.decode()
        return None

    def _get_base_classes(self, node) -> list[str]:
        bases: list[str] = []
        for child in node.children:
            if child.type == "base_class_clause":
                for bc_child in child.children:
                    if bc_child.type == "type_identifier":
                        bases.append(bc_child.text.decode())
        return bases

    def _extract_members_from_field_list(
        self, body_node, source_lines: list[str], result: ParseResult,
        parent_class: str = "", default_access: str = "private"
    ) -> None:
        current_access = default_access
        children = list(body_node.children)
        i = 0

        while i < len(children):
            child = children[i]

            if child.type == "access_specifier":
                current_access = self._get_access(child)
                i += 1
                continue

            ue_macro = self._try_get_ue_macro_field(child)
            if ue_macro:
                if i + 1 < len(children):
                    next_child = children[i + 1]
                    self._extract_field_or_func_decl(
                        next_child, source_lines, result,
                        parent_class=parent_class, access=current_access, ue_macro=ue_macro
                    )
                    i += 2
                    continue
                i += 1
                continue

            if child.type in ("{", "}"):
                i += 1
                continue
            if child.type == "declaration" and "GENERATED_BODY" in (child.text.decode() if child.text else ""):
                i += 1
                continue

            self._extract_field_or_func_decl(
                child, source_lines, result,
                parent_class=parent_class, access=current_access
            )
            i += 1

    def _try_get_ue_macro_field(self, node) -> str | None:
        if node.type == "field_declaration":
            for child in node.children:
                if child.type == "type_identifier" and child.text.decode() in UE_MACROS:
                    return child.text.decode()
        return self._try_get_ue_macro(node)

    def _extract_field_or_func_decl(
        self, node, source_lines: list[str], result: ParseResult,
        parent_class: str = "", access: str = "", ue_macro: str | None = None
    ) -> None:
        if node.type not in ("field_declaration", "declaration", "function_definition"):
            return

        text = node.text.decode() if node.text else ""
        if "GENERATED_BODY" in text:
            return
        first_type = None
        for child in node.children:
            if child.type == "type_identifier":
                first_type = child.text.decode()
                break

        if first_type in UE_MACROS:
            return

        has_func_declarator = any(c.type == "function_declarator" for c in node.children)

        if has_func_declarator:
            name = self._get_func_declarator_name(node)
            if not name:
                return
            docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
            sig = text.rstrip(";").strip()
            result.symbols.append(ParsedSymbol(
                name=name, kind="function",
                line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
                signature=sig, docstring=docstring, access=access,
                is_ue_macro=ue_macro is not None, parent_class=parent_class,
            ))
        else:
            name = self._get_field_name(node)
            if not name:
                return
            docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
            sig = text.rstrip(";").strip()
            result.symbols.append(ParsedSymbol(
                name=name, kind="variable",
                line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
                signature=sig, docstring=docstring, access=access,
                is_ue_macro=ue_macro is not None, parent_class=parent_class,
            ))

    def _get_func_declarator_name(self, node) -> str | None:
        for child in node.children:
            if child.type == "function_declarator":
                for fc in child.children:
                    if fc.type == "identifier":
                        return fc.text.decode()
                    if fc.type == "field_identifier":
                        return fc.text.decode()
                    if fc.type == "qualified_identifier":
                        return fc.text.decode()
                if child.named_children:
                    return child.named_children[0].text.decode()
        return None

    def _get_field_name(self, node) -> str | None:
        for child in node.children:
            if child.type == "field_identifier":
                return child.text.decode()
        identifiers = [c for c in node.children if c.type == "identifier"]
        if identifiers:
            return identifiers[-1].text.decode()
        for child in node.children:
            if child.type == "field_identifier":
                return child.text.decode()
        return None

    _ERROR_CLASS_RE = re.compile(
        r'\b(class|struct)\s+'
        r'(?:\w+_API\s+)?'
        r'(\w+)'
        r'(?:\s*(?:final|sealed))?\s*'
        r'(?::\s*(.+?))?\s*\{',
        re.DOTALL,
    )
    _BASE_CLASS_RE = re.compile(r'(?:public|protected|private)\s+(\w+)')

    def _extract_class_from_error_node(
        self, node, source_lines: list[str], result: ParseResult, ue_macro: str | None = None
    ) -> None:
        text = node.text.decode() if node.text else ""
        m = self._ERROR_CLASS_RE.search(text)
        if not m:
            return

        kind = m.group(1)
        name = m.group(2)
        base_clause = m.group(3) or ""

        base_classes = self._BASE_CLASS_RE.findall(base_clause)
        docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
        sig_text = text.split("{")[0].strip() if text else ""

        symbol = ParsedSymbol(
            name=name, kind=kind,
            line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
            signature=sig_text, docstring=docstring,
            is_ue_macro=ue_macro is not None, base_classes=base_classes,
        )
        result.symbols.append(symbol)

        body = self._find_body_node(node)
        default_access = "private" if kind == "class" else "public"
        if body:
            if body.type == "field_declaration_list":
                self._extract_members_from_field_list(
                    body, source_lines, result, parent_class=name, default_access=default_access)
                return
            elif body.type == "compound_statement":
                self._extract_members_from_compound(
                    body, source_lines, result, parent_class=name, default_access=default_access)
                return

        self._extract_members_by_regex(
            node, source_lines, result, parent_class=name, default_access=default_access)

    def _find_body_node(self, node, depth: int = 0):
        if depth > 4:
            return None
        for child in node.children:
            if child.type in ("field_declaration_list", "compound_statement"):
                return child
        for child in node.children:
            found = self._find_body_node(child, depth + 1)
            if found:
                return found
        return None

    _MEMBER_FUNC_RE = re.compile(
        r'^\s*(?:virtual\s+|static\s+|inline\s+)*'
        r'(\w[\w:*&<>, ]*?)\s+'
        r'(\w+)\s*\([^)]*\)'
        r'[^;{]*;',
    )
    _MEMBER_VAR_RE = re.compile(
        r'^\s*(\w[\w:*&<>, ]*?)\s+'
        r'(\w+)\s*'
        r'(?:=\s*[^;]+)?;',
    )
    _ACCESS_RE = re.compile(r'^\s*(public|protected|private)\s*:')

    def _extract_members_by_regex(
        self, node, source_lines: list[str], result: ParseResult,
        parent_class: str = "", default_access: str = "private"
    ) -> None:
        start_line = node.start_point[0]
        end_line = node.end_point[0]

        current_access = default_access
        pending_ue_macro: str | None = None

        for line_idx in range(start_line, min(end_line + 1, len(source_lines))):
            line = source_lines[line_idx]
            stripped = line.strip()

            if not stripped or stripped in ("{", "}", "};"):
                continue
            if "GENERATED_BODY" in stripped:
                continue

            am = self._ACCESS_RE.match(line)
            if am:
                current_access = am.group(1)
                continue

            is_ue_macro_line = False
            for macro in UE_MACROS:
                if stripped.startswith(macro + "(") or stripped == macro:
                    pending_ue_macro = macro
                    is_ue_macro_line = True
                    break
            if is_ue_macro_line:
                continue

            fm = self._MEMBER_FUNC_RE.match(line)
            if fm:
                ret_type = fm.group(1).strip()
                func_name = fm.group(2)
                if ret_type in UE_MACROS or func_name in UE_MACROS:
                    pending_ue_macro = None
                    continue
                sig = stripped.rstrip(";").strip()
                result.symbols.append(ParsedSymbol(
                    name=func_name, kind="function",
                    line_start=line_idx + 1, line_end=line_idx + 1,
                    signature=sig, access=current_access,
                    is_ue_macro=pending_ue_macro is not None, parent_class=parent_class,
                ))
                pending_ue_macro = None
                continue

            vm = self._MEMBER_VAR_RE.match(line)
            if vm:
                var_type = vm.group(1).strip()
                var_name = vm.group(2)
                if var_type in UE_MACROS or var_name in UE_MACROS:
                    pending_ue_macro = None
                    continue
                if var_type in ("public", "protected", "private"):
                    continue
                sig = stripped.rstrip(";").strip()
                result.symbols.append(ParsedSymbol(
                    name=var_name, kind="variable",
                    line_start=line_idx + 1, line_end=line_idx + 1,
                    signature=sig, access=current_access,
                    is_ue_macro=pending_ue_macro is not None, parent_class=parent_class,
                ))
                pending_ue_macro = None
                continue

            pending_ue_macro = None

    def _extract_misparse_class_or_function(
        self, node, source_lines: list[str], result: ParseResult, ue_macro: str | None = None
    ) -> None:
        has_class_spec = any(c.type == "class_specifier" for c in node.children)
        has_struct_spec = any(c.type == "struct_specifier" for c in node.children)

        if has_class_spec or has_struct_spec:
            self._extract_misparsed_class(node, source_lines, result, ue_macro=ue_macro)
        else:
            self._extract_function_definition(node, source_lines, result, ue_macro=ue_macro)

    def _extract_misparsed_class(
        self, node, source_lines: list[str], result: ParseResult, ue_macro: str | None = None
    ) -> None:
        kind = "class"
        for child in node.children:
            if child.type == "struct_specifier":
                kind = "struct"
                break

        name = None
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode()
                break

        if not name:
            return

        base_classes: list[str] = []
        for child in node.children:
            if child.type == "ERROR":
                for ec in child.children:
                    if ec.type == "identifier":
                        base_classes.append(ec.text.decode())

        docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
        sig_text = node.text.decode().split("{")[0].strip() if node.text else ""

        symbol = ParsedSymbol(
            name=name, kind=kind,
            line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
            signature=sig_text, docstring=docstring,
            is_ue_macro=ue_macro is not None, base_classes=base_classes,
        )
        result.symbols.append(symbol)

        body = None
        for child in node.children:
            if child.type == "compound_statement":
                body = child
                break

        if body:
            self._extract_members_from_compound(
                body, source_lines, result, parent_class=name,
                default_access="private" if kind == "class" else "public"
            )

    def _extract_members_from_compound(
        self, body_node, source_lines: list[str], result: ParseResult,
        parent_class: str = "", default_access: str = "private"
    ) -> None:
        current_access = default_access
        children = list(body_node.children)
        i = 0

        while i < len(children):
            child = children[i]

            if child.type in ("{", "}"):
                i += 1
                continue

            if child.type == "labeled_statement":
                current_access, pending_macro = self._extract_from_labeled(
                    child, source_lines, result, parent_class, current_access
                )
                if pending_macro and i + 1 < len(children):
                    next_child = children[i + 1]
                    self._extract_compound_member(
                        next_child, source_lines, result,
                        parent_class=parent_class, access=current_access, ue_macro=pending_macro
                    )
                    i += 2
                    continue
                i += 1
                continue

            ue_macro = self._try_get_ue_macro(child)
            if ue_macro:
                if i + 1 < len(children):
                    next_child = children[i + 1]
                    self._extract_compound_member(
                        next_child, source_lines, result,
                        parent_class=parent_class, access=current_access, ue_macro=ue_macro
                    )
                    i += 2
                    continue
                i += 1
                continue

            if child.type == "expression_statement":
                text = child.text.decode() if child.text else ""
                if "GENERATED_BODY" in text:
                    i += 1
                    continue

            self._extract_compound_member(
                child, source_lines, result,
                parent_class=parent_class, access=current_access
            )
            i += 1

    def _extract_from_labeled(
        self, node, source_lines: list[str], result: ParseResult,
        parent_class: str, current_access: str
    ) -> tuple[str, str | None]:
        for child in node.children:
            if child.type == "statement_identifier":
                label = child.text.decode()
                if label in ("public", "protected", "private"):
                    current_access = label

        children = list(node.children)
        i = 0
        pending_macro: str | None = None
        while i < len(children):
            child = children[i]
            if child.type in ("statement_identifier", ":"):
                i += 1
                continue

            if child.type == "comment":
                i += 1
                continue

            ue_macro = self._try_get_ue_macro(child)
            if ue_macro:
                if i + 1 < len(children):
                    next_child = children[i + 1]
                    if next_child.type == "comment":
                        pending_macro = ue_macro
                        i += 1
                        continue
                    self._extract_compound_member(
                        next_child, source_lines, result,
                        parent_class=parent_class, access=current_access, ue_macro=ue_macro
                    )
                    pending_macro = None
                    i += 2
                    continue
                else:
                    pending_macro = ue_macro
                i += 1
                continue

            self._extract_compound_member(
                child, source_lines, result,
                parent_class=parent_class, access=current_access
            )
            pending_macro = None
            i += 1

        return current_access, pending_macro

    def _extract_compound_member(
        self, node, source_lines: list[str], result: ParseResult,
        parent_class: str = "", access: str = "", ue_macro: str | None = None
    ) -> None:
        if node.type == "comment":
            return

        text = node.text.decode() if node.text else ""
        if "GENERATED_BODY" in text:
            return

        if node.type == "declaration":
            has_func_declarator = any(c.type == "function_declarator" for c in node.children)
            if has_func_declarator:
                name = self._get_func_declarator_name(node)
                if name:
                    docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
                    sig = text.rstrip(";").strip()
                    result.symbols.append(ParsedSymbol(
                        name=name, kind="function",
                        line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
                        signature=sig, docstring=docstring, access=access,
                        is_ue_macro=ue_macro is not None, parent_class=parent_class,
                    ))
            else:
                name = self._get_field_name(node)
                if name:
                    docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
                    sig = text.rstrip(";").strip()
                    result.symbols.append(ParsedSymbol(
                        name=name, kind="variable",
                        line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
                        signature=sig, docstring=docstring, access=access,
                        is_ue_macro=ue_macro is not None, parent_class=parent_class,
                    ))
        elif node.type == "expression_statement":
            for child in node.children:
                if child.type == "call_expression":
                    fn = child.children[0] if child.children else None
                    if fn and fn.type == "identifier":
                        fn_name = fn.text.decode()
                        if fn_name not in UE_MACROS and fn_name != "GENERATED_BODY":
                            docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)
                            sig = text.rstrip(";").strip()
                            result.symbols.append(ParsedSymbol(
                                name=fn_name, kind="function",
                                line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
                                signature=sig, docstring=docstring, access=access,
                                is_ue_macro=ue_macro is not None, parent_class=parent_class,
                            ))

    def _extract_function_definition(
        self, node, source_lines: list[str], result: ParseResult, ue_macro: str | None = None
    ) -> None:
        func_decl = None
        for child in node.children:
            if child.type == "function_declarator":
                func_decl = child
                break

        if not func_decl:
            return

        name = None
        parent_class = None
        for child in func_decl.children:
            if child.type == "qualified_identifier":
                qname = child.text.decode()
                name = qname
                if "::" in qname:
                    parts = qname.split("::")
                    parent_class = parts[0]
                break
            if child.type == "identifier":
                name = child.text.decode()
                break

        if not name:
            return

        docstring = self._get_docstring_above(node, source_lines, ue_macro_above=ue_macro is not None)

        sig_parts = []
        for child in node.children:
            if child.type == "compound_statement":
                break
            sig_parts.append(child.text.decode() if child.text else "")
        signature = " ".join(sig_parts).strip()

        result.symbols.append(ParsedSymbol(
            name=name, kind="function",
            line_start=node.start_point[0] + 1, line_end=node.end_point[0] + 1,
            signature=signature, docstring=docstring,
            is_ue_macro=ue_macro is not None, parent_class=parent_class,
        ))

    def _get_docstring_above(
        self, node, source_lines: list[str], ue_macro_above: bool = False
    ) -> str:
        target_line = node.start_point[0]
        search_line = target_line - 1

        if ue_macro_above:
            while search_line >= 0:
                line = source_lines[search_line].strip()
                if not line or self._is_ue_macro_line(line):
                    search_line -= 1
                else:
                    break
        else:
            while search_line >= 0 and not source_lines[search_line].strip():
                search_line -= 1

        doc_lines: list[str] = []
        line_idx = search_line
        while line_idx >= 0:
            line = source_lines[line_idx].strip()
            if line.startswith("///") or line.startswith("/**") or line.startswith("*") or line.startswith("*/"):
                doc_lines.insert(0, line)
                line_idx -= 1
            else:
                break

        if not doc_lines:
            return ""

        return self._clean_docstring(doc_lines)

    @staticmethod
    def _is_ue_macro_line(line: str) -> bool:
        stripped = line.strip()
        for macro in UE_MACROS:
            if stripped.startswith(macro + "(") or stripped == macro:
                return True
        return False

    def _clean_docstring(self, lines: list[str]) -> str:
        cleaned: list[str] = []
        for line in lines:
            line = line.strip()
            if line.startswith("/**"):
                line = line[3:].strip()
            elif line.startswith("///"):
                line = line[3:].strip()
            elif line.startswith("*/"):
                continue
            elif line.startswith("*"):
                line = line[1:].strip()
            if line:
                cleaned.append(line)
        return "\n".join(cleaned)

    def _get_access(self, node) -> str:
        text = node.text.decode().rstrip(":").strip()
        if text in ("public", "protected", "private"):
            return text
        return ""
