"""Regex-based HLSL shader parser for .usf/.ush files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .cpp_parser import ParsedSymbol, ParseResult

# Regex patterns
_RE_INCLUDE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]', re.MULTILINE)
_RE_DEFINE = re.compile(r"^\s*#define\s+(\w+)\s*(.*?)$", re.MULTILINE)
_RE_STRUCT = re.compile(r"^\s*struct\s+(\w+)\s*\{", re.MULTILINE)
_RE_FUNCTION = re.compile(
    r"^[ \t]*"
    r"([\w:]+(?:\s*<[^>]*>)?)"
    r"\s+"
    r"(\w+)"
    r"\s*\("
    r"((?:[^)]*\n?)*?)"
    r"\)",
    re.MULTILINE,
)
_RE_BLOCK_COMMENT = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)
_RE_LINE_COMMENT = re.compile(r"^[ \t]*//(.*)$", re.MULTILINE)


class ShaderParser:
    """Parse HLSL shader files (.usf / .ush) using regex."""

    _NON_FUNCTION_KEYWORDS = frozenset(
        {"struct", "class", "enum", "namespace", "return", "if", "else",
         "for", "while", "switch", "case", "do", "#define", "#include",
         "#if", "#ifdef", "#ifndef", "#elif", "#else", "#endif", "#pragma"}
    )

    def parse_file(self, path: Path | str) -> ParseResult:
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ParseResult(path=str(path))

        lines = text.split("\n")
        result = ParseResult(path=str(path))

        self._extract_includes(text, result)
        self._extract_defines(text, lines, result)
        self._extract_structs(text, lines, result)
        self._extract_functions(text, lines, result)

        return result

    def _extract_includes(self, text: str, result: ParseResult) -> None:
        for m in _RE_INCLUDE.finditer(text):
            result.includes.append(m.group(1))
            line = text[: m.start()].count("\n") + 1
            result.symbols.append(
                ParsedSymbol(
                    name=m.group(1), kind="include",
                    line_start=line, line_end=line,
                    signature=m.group(0).strip(),
                )
            )

    def _extract_defines(self, text: str, lines: list[str], result: ParseResult) -> None:
        for m in _RE_DEFINE.finditer(text):
            name = m.group(1)
            value = m.group(2).strip()
            line = text[: m.start()].count("\n") + 1
            result.symbols.append(
                ParsedSymbol(
                    name=name, kind="define",
                    line_start=line, line_end=line,
                    signature=f"#define {name} {value}".strip(),
                )
            )

    def _extract_structs(self, text: str, lines: list[str], result: ParseResult) -> None:
        for m in _RE_STRUCT.finditer(text):
            name = m.group(1)
            start_line = text[: m.start()].count("\n") + 1
            end_line = self._find_closing_brace(lines, start_line - 1)
            result.symbols.append(
                ParsedSymbol(
                    name=name, kind="struct",
                    line_start=start_line, line_end=end_line,
                    signature=f"struct {name}",
                )
            )

    def _extract_functions(self, text: str, lines: list[str], result: ParseResult) -> None:
        for m in _RE_FUNCTION.finditer(text):
            return_type = m.group(1).strip()
            name = m.group(2).strip()
            params = m.group(3).strip()

            if return_type in self._NON_FUNCTION_KEYWORDS:
                continue
            if name in self._NON_FUNCTION_KEYWORDS:
                continue

            brace_search = re.search(r"\{", text[m.end():])
            if brace_search is None:
                continue
            between = text[m.end(): m.end() + brace_search.start()]
            if re.search(r"[;]", between):
                continue

            start_line = text[: m.start()].count("\n") + 1
            brace_line = text[: m.end() + brace_search.start()].count("\n")
            end_line = self._find_closing_brace(lines, brace_line)

            params_clean = re.sub(r"\s+", " ", params)
            signature = f"{return_type} {name}({params_clean})"
            docstring = self._find_docstring(text, m.start())

            result.symbols.append(
                ParsedSymbol(
                    name=name, kind="function",
                    line_start=start_line, line_end=end_line,
                    signature=signature, docstring=docstring or "",
                )
            )

    @staticmethod
    def _find_closing_brace(lines: list[str], open_line_idx: int) -> int:
        depth = 0
        for i in range(open_line_idx, len(lines)):
            for ch in lines[i]:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return i + 1
        return open_line_idx + 1

    @staticmethod
    def _find_docstring(text: str, func_start: int) -> Optional[str]:
        preceding = text[:func_start].rstrip()

        block_m = re.search(r"/\*\*(.*?)\*/\s*$", preceding, re.DOTALL)
        if block_m:
            raw = block_m.group(1)
            cleaned_lines = []
            for raw_line in raw.split("\n"):
                stripped = re.sub(r"^\s*\*\s?", "", raw_line).strip()
                if stripped:
                    cleaned_lines.append(stripped)
            return "\n".join(cleaned_lines) if cleaned_lines else None

        comment_lines: list[str] = []
        for line in reversed(preceding.split("\n")):
            stripped = line.strip()
            if stripped.startswith("//"):
                comment_lines.append(stripped.lstrip("/").strip())
            else:
                break
        if comment_lines:
            comment_lines.reverse()
            return "\n".join(comment_lines)

        return None
