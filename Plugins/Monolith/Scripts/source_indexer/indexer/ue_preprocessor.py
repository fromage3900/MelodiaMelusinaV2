"""
UE Macro Preprocessor — strip Unreal Engine macros before tree-sitter parsing.

Problem:
    Tree-sitter's C++ grammar doesn't understand UE-specific macros like
    UCLASS(...), ENGINE_API, or GENERATED_BODY(). These produce ERROR nodes
    in the AST, which breaks class hierarchy extraction and symbol indexing.

Solution:
    Replace macro text with same-length whitespace *before* feeding source to
    tree-sitter. Every non-newline byte in a macro span becomes a space (0x20).
    Newlines are preserved at their original byte offsets so that line numbers
    and column positions remain exactly correct.

Critical invariant:
    len(output) == len(input)  AND  every '\\n' is at the same byte offset.

Three categories of macros are handled:

1. Class-level macros with nested parentheses:
       UCLASS(...), USTRUCT(...), UENUM(...), UINTERFACE(...)
   These can contain arbitrarily nested parens:
       UCLASS(BlueprintType, meta=(DisplayName="Foo", Categories=(A, B)))
   A balanced-parenthesis scanner is used (regex cannot handle this).

2. API export macros:
       ENGINE_API, CORE_API, COREUOBJECT_API, MYMODULE_API, ...
   Pattern: [A-Z][A-Z0-9]*_API as whole words. Simple regex suffices.

3. GENERATED_BODY variants:
       GENERATED_BODY(), GENERATED_UCLASS_BODY(), GENERATED_USTRUCT_BODY()
   Simple regex suffices.

All operations work on bytes (tree-sitter expects bytes input).
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CLASS_MACROS: tuple[bytes, ...] = (
    b"UCLASS",
    b"USTRUCT",
    b"UENUM",
    b"UINTERFACE",
)

# Regex for GENERATED_BODY() and variants.  The parens are always empty.
_GENERATED_BODY_RE = re.compile(
    rb"\bGENERATED_(?:UCLASS_|USTRUCT_)?BODY\s*\(\s*\)"
)

# Regex for API export macros: one or more uppercase letters/digits followed
# by _API, as a whole word.  Negative lookbehind/lookahead ensure word
# boundaries without consuming characters.
_API_MACRO_RE = re.compile(
    rb"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*_API(?![A-Za-z0-9_])"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _replace_with_spaces(m: re.Match[bytes]) -> bytes:
    """Regex replacement callback: spaces for every byte except newlines."""
    span = m.group(0)
    return bytes(
        b if b == ord("\n") else ord(" ")
        for b in span
    )


def _strip_balanced_macro(source: bytearray, macro_names: tuple[bytes, ...]) -> None:
    """In-place replacement of ``MACRO_NAME(...)`` spans with whitespace.

    Uses a simple linear scan with balanced-parenthesis counting so that
    arbitrarily nested parentheses inside the macro argument list are handled
    correctly.  Only non-newline bytes are replaced; newlines stay in place.
    """
    i = 0
    length = len(source)

    while i < length:
        matched = False

        for macro in macro_names:
            macro_len = len(macro)

            # Quick bounds check.
            if i + macro_len > length:
                continue

            # Check for macro name at current position.
            if source[i : i + macro_len] != macro:
                continue

            # Word-boundary check: preceding character must NOT be alnum/_.
            if i > 0 and (chr(source[i - 1]).isalnum() or source[i - 1] == ord("_")):
                continue

            # Word-boundary check after macro name: next char must NOT be
            # alnum/_ (it should be whitespace or '(').
            after = i + macro_len
            if after < length and (chr(source[after]).isalnum() or source[after] == ord("_")):
                continue

            # Skip whitespace between macro name and opening '('.
            j = after
            while j < length and source[j] in (ord(" "), ord("\t"), ord("\r")):
                j += 1

            if j >= length or source[j] != ord("("):
                # No opening paren — not a macro invocation; skip.
                continue

            # Scan for balanced closing ')'.
            depth = 1
            k = j + 1
            while k < length and depth > 0:
                ch = source[k]
                if ch == ord("("):
                    depth += 1
                elif ch == ord(")"):
                    depth -= 1
                k += 1

            if depth != 0:
                # Unbalanced — likely truncated source.  Leave it alone.
                continue

            # Replace the entire span [i, k) with spaces, preserving '\n'.
            for idx in range(i, k):
                if source[idx] != ord("\n"):
                    source[idx] = ord(" ")

            i = k
            matched = True
            break

        if not matched:
            i += 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess_ue_source(source_bytes: bytes) -> bytes:
    """Return *source_bytes* with UE macros replaced by same-length whitespace.

    The output has the identical byte length and newline positions as the
    input, so tree-sitter line/column mappings remain valid.

    Parameters
    ----------
    source_bytes:
        Raw file content (UTF-8 encoded C++ source).

    Returns
    -------
    bytes
        Cleaned source suitable for tree-sitter parsing.
    """
    # Phase 1 — balanced-paren macros (must mutate a bytearray).
    buf = bytearray(source_bytes)
    _strip_balanced_macro(buf, _CLASS_MACROS)

    # Phase 2 — regex-based macros (operate on immutable bytes).
    result = bytes(buf)
    result = _GENERATED_BODY_RE.sub(_replace_with_spaces, result)
    result = _API_MACRO_RE.sub(_replace_with_spaces, result)

    # Sanity: length must be unchanged.
    assert len(result) == len(source_bytes), (
        f"preprocess_ue_source: length mismatch "
        f"({len(result)} != {len(source_bytes)})"
    )

    return result
