#!/usr/bin/env python3
"""tag_path_params.py — Monolith param-kind tagging maintenance tool.

Rewrites `.Required(TEXT("x_path"), TEXT("string"), TEXT("desc"))` style
FParamSchemaBuilder calls into the path-kind sugar overloads
(`RequiredAssetPath` / `OptionalAssetPath` / `RequiredDiskPath` /
`OptionalDiskPath`, plus the `*WithDefault` and alias variants) defined in
`MonolithCore/Public/MonolithParamSchema.h`.

Only string-typed params whose NAME matches a path pattern are considered.
Classification (AssetPath vs DiskPath vs leave-Other) is heuristic, driven by
the param name + description text. Conservative: when ambiguous, LEAVE as Other.

Usage:
    python tag_path_params.py            # dry-run: report only, no writes
    python tag_path_params.py --apply    # apply edits in place

The transform is deterministic. Review the printed classification report and
hand-correct any misclassification afterwards.
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Plugins/Monolith

# A single .Required/.Optional call. Captures the method and the raw arg list.
# We then sub-parse the arg list manually because TEXT("...") strings can
# contain commas, parens, and escaped quotes.
CALL_RE = re.compile(
    r'\.(Required|Optional)\s*\(',
)

# Param-name patterns that *could* be paths. Tight enough to avoid output_type,
# target_expression, from_output, output_index, etc. We require the token to be
# a path-y suffix/word, not merely containing "path".
NAME_IS_PATH = re.compile(
    r'^('
    r'asset_path|asset_paths|'              # asset_paths(array) excluded later by type check
    r'file_path|files_path|'
    r'package_path|content_path|'
    r'blueprint_path|bp_path|'
    r'destination_path|dest_path|'
    r'output_path|source_path|target_path|'
    r'save_path|export_path|import_path|load_path|'
    r'folder_path|directory_path|dir_path|path|'
    r'folder|directory|out_dir|output_dir|source_dir|dest_dir|target_dir|'
    r'source_file|texture_folder|new_folder|'
    r'path_prefix|save_path_prefix|asset_path_a|asset_path_b|'
    r'.*_asset_path|.*_save_path|.*_folder_path|.*_package_path|.*_file_path|'
    r'.*_path'
    r')$'
)

# Names that LOOK path-y by the broad ".*_path" but are NOT filesystem/asset
# paths — property paths, pin names, struct member paths, etc. Leave Other.
NAME_NEVER_PATH = re.compile(
    r'^('
    r'source_path|target_path|'   # frequently property paths — decided by DESC
    r'property_path|member_path|struct_path|binding_path|'
    r'render_target_path'         # decided by desc
    r')$'
)

# Desc signals that a "*_path" is actually a PROPERTY path / node path / not a
# real asset-or-disk path. Strong leave-Other signal.
DESC_NOT_A_PATH = re.compile(
    r'property\s+path|StructID|\.PropertyName|RootComponent\.|'
    r'dotted\s+path|node\s+path|pin\s+name|GUID|member\s+path|'
    r'/Script/|script\s+struct|'          # /Script/... is a class/struct path, not /Game
    r'glob\s+pattern|substring\s+filter|substring|\*\s+and\s+\?',  # filters, not real paths
    re.IGNORECASE,
)

# Desc signals for DiskPath (native OS filesystem).
DESC_DISK = re.compile(
    r'on\s+disk|file\s+on\s+disk|absolute\s+path|native\s+path|'
    r'\.png|\.jpg|\.jpeg|\.fbx|\.obj|\.tga|\.exr|\.wav|\.csv|\.json|\.ini|'
    r'\.cpp|\.h\b|\.uasset|\.txt|'
    r'export\s+to|import\s+from|screenshot|'
    r'[A-Z]:[\\/]|'                     # C:\ or D:/ drive letter
    r'D:/|C:/|'
    r'source\s+file|image\s+file|output\s+directory\s+on\s+disk',
    re.IGNORECASE,
)

# Desc signals for AssetPath (content-browser virtual path).
DESC_ASSET = re.compile(
    r'/Game/|/Engine/|content\s+folder|content\s+browser|content\s+path|'
    r'asset\s+path|blueprint\s+path|package\s+path|virtual\s+path|'
    r'outliner\s+folder|world\s+outliner|/Game\b|UE\s+content|'
    r'asset\s+to|blueprint|material\s+asset|texture\s+asset|widget\s+path|'
    r'class\s+name',  # save_path "asset path OR class name" -> still asset
    re.IGNORECASE,
)


def find_calls(text):
    """Yield (start, end, method, args_str) for each .Required/.Optional call."""
    for m in CALL_RE.finditer(text):
        method = m.group(1)
        open_paren = m.end() - 1  # index of '('
        # walk to matching close paren, respecting string literals
        depth = 0
        i = open_paren
        n = len(text)
        in_str = False
        while i < n:
            c = text[i]
            if in_str:
                if c == '\\':
                    i += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        yield (m.start(), i + 1, method, text[open_paren + 1:i])
                        break
            i += 1


def split_top_args(args_str):
    """Split a call's argument string on top-level commas (ignoring strings,
    nested parens, and brace-lists)."""
    parts = []
    depth = 0
    in_str = False
    cur = []
    i = 0
    n = len(args_str)
    while i < n:
        c = args_str[i]
        if in_str:
            cur.append(c)
            if c == '\\':
                if i + 1 < n:
                    cur.append(args_str[i + 1])
                    i += 2
                    continue
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            cur.append(c)
        elif c in '([{':
            depth += 1
            cur.append(c)
        elif c in ')]}':
            depth -= 1
            cur.append(c)
        elif c == ',' and depth == 0:
            parts.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur:
        parts.append(''.join(cur).strip())
    return parts


TEXT_LIT = re.compile(r'^TEXT\(\s*"((?:[^"\\]|\\.)*)"\s*\)$', re.DOTALL)


def text_literal(arg):
    """Return the inner string of TEXT("...") or None if arg isn't a plain literal."""
    m = TEXT_LIT.match(arg.strip())
    if m:
        return m.group(1)
    return None


def classify(name, desc):
    """Return 'AssetPath' | 'DiskPath' | None (leave Other) + reason."""
    if DESC_NOT_A_PATH.search(desc):
        return None, "desc indicates property/node path, not a file/asset path"
    if NAME_NEVER_PATH.match(name) and not DESC_ASSET.search(desc) and not DESC_DISK.search(desc):
        # source_path/target_path with no asset/disk signal -> likely property
        return None, "name in never-path set with no asset/disk desc signal"
    disk = bool(DESC_DISK.search(desc))
    asset = bool(DESC_ASSET.search(desc))
    if disk and not asset:
        return "DiskPath", "desc has disk/filesystem signal"
    if asset and not disk:
        return "AssetPath", "desc has /Game or content/asset signal"
    if asset and disk:
        # both — prefer disk only if drive-letter / file-extension present
        if re.search(r'[A-Z]:[\\/]|\.png|\.fbx|\.jpg|\.exr|\.wav|on\s+disk', desc, re.IGNORECASE):
            return "DiskPath", "desc has explicit disk extension/drive despite /Game mention"
        return "AssetPath", "desc mixed; defaulting to AssetPath (content-path dominant)"
    # No strong desc signal. Use name as a weak tiebreak: folder/dir/path on an
    # asset-manipulation API defaults to AssetPath, EXCEPT names that scream disk.
    if re.search(r'(file|export|import|screenshot|source_file|out_dir|output_dir)', name):
        return None, "ambiguous; name leans disk but no desc confirmation — left Other for review"
    return "AssetPath", "no desc signal; asset-manipulation default for path-named param"


def build_replacement(method, kind, name_arg, desc_arg, default_arg, alias_arg):
    """Construct the sugar call text."""
    has_default = default_arg is not None
    has_alias = alias_arg is not None
    base = method + ("AssetPath" if kind == "AssetPath" else "DiskPath")
    if has_default:
        # Only Optional supports default sugar.
        fn = "Optional" + ("AssetPath" if kind == "AssetPath" else "DiskPath") + "WithDefault"
        if has_alias:
            return f".{fn}({name_arg}, {desc_arg}, {default_arg}, {alias_arg})"
        return f".{fn}({name_arg}, {desc_arg}, {default_arg})"
    if has_alias:
        return f".{base}({name_arg}, {desc_arg}, {alias_arg})"
    return f".{base}({name_arg}, {desc_arg})"


def process_file(path, apply, report):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    orig = text
    edits = []  # (start, end, new_text)
    for start, end, method, args_str in find_calls(text):
        args = split_top_args(args_str)
        if len(args) < 3:
            continue
        name = text_literal(args[0])
        typ = text_literal(args[1])
        desc = text_literal(args[2])
        if name is None or typ is None or desc is None:
            continue  # non-literal first three args -> skip (can't safely rewrite)
        if typ != "string":
            continue  # only string params
        if not NAME_IS_PATH.match(name):
            continue
        # Determine default + alias from remaining args.
        default_arg = None
        alias_arg = None
        rest = args[3:]
        for a in rest:
            a = a.strip()
            if a.startswith('{'):
                alias_arg = a
            else:
                # default value arg (a TEXT("...") literal). Only keep if non-empty.
                lit = text_literal(a)
                if lit is not None and lit != "":
                    default_arg = a
                elif lit == "":
                    pass  # empty default -> treat as no default
                else:
                    # non-literal default (variable / FString) -> cannot use sugar
                    default_arg = "__NONLITERAL__"
        if default_arg == "__NONLITERAL__":
            report['other'].append((path, name, "non-literal default arg; can't express in sugar"))
            continue
        # Optional with default is fine (we have WithDefault). Required with a 4th
        # positional non-alias is unusual; skip if so.
        if method == "Required" and default_arg is not None:
            report['other'].append((path, name, "Required with positional default (unexpected); left Other"))
            continue
        kind, reason = classify(name, desc)
        if kind is None:
            report['other'].append((path, name, reason))
            continue
        new_text = build_replacement(method, kind, args[0].strip(), args[2].strip(), default_arg, alias_arg)
        edits.append((start, end, new_text))
        bucket = 'asset' if kind == 'AssetPath' else 'disk'
        report[bucket].append((path, name, reason, desc[:70]))
    if not edits:
        return 0
    # apply edits back-to-front
    edits.sort(key=lambda e: e[0], reverse=True)
    for s, e, nt in edits:
        text = text[:s] + nt + text[e:]
    if apply and text != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    report['files'].add(path)
    return len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='write changes in place')
    args = ap.parse_args()
    files = glob.glob(os.path.join(ROOT, 'Source', 'Monolith*', '**', '*Actions.cpp'), recursive=True)
    report = {'asset': [], 'disk': [], 'other': [], 'files': set()}
    total_edits = 0
    for f in sorted(files):
        total_edits += process_file(f, args.apply, report)

    rel = lambda p: os.path.relpath(p, ROOT)
    print(f"=== tag_path_params.py {'APPLY' if args.apply else 'DRY-RUN'} ===")
    print(f"Files scanned: {len(files)}")
    print(f"Files touched: {len(report['files'])}")
    print(f"Tagged AssetPath: {len(report['asset'])}")
    print(f"Tagged DiskPath:  {len(report['disk'])}")
    print(f"Left Other:       {len(report['other'])}")
    print(f"Total edits:      {total_edits}")
    print("\n--- DiskPath (review these carefully) ---")
    for p, n, r, d in report['disk']:
        print(f"  [{rel(p)}] {n}: {r} | desc='{d}'")
    print("\n--- Left Other (candidates for human review) ---")
    for p, n, r in report['other']:
        print(f"  [{rel(p)}] {n}: {r}")
    print("\n--- AssetPath (sample, first 40) ---")
    for p, n, r, d in report['asset'][:40]:
        print(f"  [{rel(p)}] {n}: {r}")


if __name__ == '__main__':
    main()
