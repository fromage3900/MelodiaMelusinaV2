"""AST-precise transport migration for Tools/ scripts using UE :9316 Monolith RPC.

Convergence strategy (behaviour preserving):

  Hand-rolled:                      After:
    body = {...}                      body = {...}          <- untouched
    req = Request(URL, data=...)      from mcp_client import post_envelope
    with urlopen(req, t) as resp:     data = post_envelope(body, timeout=t,
        data = json.loads(...)                          raise_on_error=True)

Only the HTTP transport is replaced. Each script keeps its own envelope
construction, error handling and result parsing, so behaviour is identical
while there is exactly one socket implementation in the repo.

raise_on_error=True is what preserves error handling: urlopen() raised on a
dead endpoint, whereas post_envelope() defaults to returning {"error": ...}
for its other callers.

Shapes that cannot be migrated mechanically (raw SSE framing, extra field
access on the parsed result, reuse of the raw response text) are reported as
`manual` with the responsible line instead of being guessed at.

Usage:
    python migrate_monolith_calls.py            # dry run, report only
    python migrate_monolith_calls.py --apply    # rewrite files
    python migrate_monolith_calls.py --apply --only anim_diagnostic.py
"""
from __future__ import annotations

import argparse
import ast
import glob
import os
import re
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
EXCLUDED = {"mcp_client.py", "staging_core.py", "inspect_map_actors.py",
            "migrate_monolith_calls.py", "melodia_ue_stage_worker.py"}

IMPORT_LINE = "from mcp_client import post_envelope"


class _CallFinder(ast.NodeVisitor):
    """Locate urlopen(...) calls and the Request(...) assignments feeding them."""

    def __init__(self):
        self.urlopen_calls = []
        self.request_assigns = {}

    def visit_Call(self, node):
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name == "urlopen":
            self.urlopen_calls.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call)):
            fname = getattr(node.value.func, "attr", None) or getattr(node.value.func, "id", None)
            if fname == "Request":
                self.request_assigns[node.targets[0].id] = node
        self.generic_visit(node)

def find_sites(src):
    """Return list of (scope_node, urlopen_call, request_assign_or_None)."""
    tree = ast.parse(src)
    sites = []
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        finder = _CallFinder()
        for stmt in func.body:
            finder.visit(stmt)
        for call in finder.urlopen_calls:
            req = None
            if call.args and isinstance(call.args[0], ast.Name):
                req = finder.request_assigns.get(call.args[0].id)
            sites.append((func, call, req))

    # The module body is a scope too. Scanning only functions made a
    # module-level POST invisible, so get_hlsl_schema.py and
    # run_melodia_cpp_tests.py read as "no urlopen call site" and were reported
    # clean while still hand-rolling the transport. They are picked up here and
    # refused as manual, which is the honest answer for straight-line code.
    top = _CallFinder()
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        top.visit(stmt)
    for call in top.urlopen_calls:
        req = None
        if call.args and isinstance(call.args[0], ast.Name):
            req = top.request_assigns.get(call.args[0].id)
        sites.append((tree, call, req))
    return sites


def _timeout_expr(call):
    for k in call.keywords:
        if k.arg == "timeout":
            return ast.unparse(k.value)
    return "30"


def _statement_at(func, lineno):
    """Innermost statement of `func` that starts on the given 1-based line.

    Sites nest arbitrarily deep (a `with urlopen(...)` inside a `for` inside a
    `try` is the shape in overnight_persona_pie_loop.py), so a depth-1 scan is
    not enough. The smallest span wins, which resolves an inline body
    (`if x: raw = urlopen(...)`) to the assignment rather than the `if`.
    """
    best = None
    for node in ast.walk(func):
        if not isinstance(node, ast.stmt) or getattr(node, "lineno", None) != lineno:
            continue
        if best is None or node.end_lineno <= best.end_lineno:
            best = node
    return best


def _envelope_var(req_assign):
    """Recover the exact payload expression passed as Request(data=...).

    Using the script's real expression (`b`, `payload`, `body`) instead of
    assuming `body` is what keeps migrated helpers free of NameError.
    """
    req_call = req_assign.value
    for kw in req_call.keywords:
        if kw.arg == "data":
            return ast.unparse(kw.value)
    if len(req_call.args) > 1:
        return ast.unparse(req_call.args[1])
    return None


def _parent_map(scope):
    """Map every node in `scope` to its direct parent."""
    pmap = {}
    for node in ast.walk(scope):
        for child in ast.iter_child_nodes(node):
            pmap[child] = node
    return pmap


def _call_name(node):
    """'loads' for json.loads(...), 'urlopen' for ...urlopen(...)."""
    if not isinstance(node, ast.Call):
        return None
    return getattr(node.func, "attr", None) or getattr(node.func, "id", None)


def _ancestors(pmap, node):
    chain, cur = [], node
    while cur in pmap:
        cur = pmap[cur]
        chain.append(cur)
    return chain


def _contains(pmap, outer, inner):
    """True when `outer` is `inner` or one of its ancestors."""
    return inner is outer or outer in _ancestors(pmap, inner)


def _stmt_list(parent, stmt):
    """The body/orelse/finalbody list that directly contains `stmt`."""
    for field in ("body", "orelse", "finalbody"):
        seq = getattr(parent, field, None)
        if isinstance(seq, list) and any(s is stmt for s in seq):
            return seq
    return None


def _surviving_names(new_src, pairs):
    """Function-scoped check that a replaced raw variable really disappeared.

    Module-wide name searches give false positives (`r`, `resp` are popular
    names elsewhere), so each name is only looked for inside the function that
    hosted the original call.
    """
    try:
        tree = ast.parse(new_src)
    except SyntaxError:
        return pairs[0][1] if pairs else None

    lines = new_src.splitlines()
    for fname, name in pairs:
        body = new_src
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fname:
                body = "\n".join(lines[node.lineno - 1:node.end_lineno])
                break
        body = re.sub(r"post_envelope\([^)]*\)", "", body, flags=re.S)
        if re.search(rf"\b{re.escape(name)}\b", body):
            return name
    return None


def _plan_site(func, call_node, req, lines):
    """Rewrite plan for one urlopen site.

    Returns (status, reason, start, end, repl, orphans) where [start, end) is
    the exclusive line range to replace and `orphans` lists (function, name)
    pairs that must not survive the swap.

    Modelled shapes (everything else is refused rather than guessed at):

      Tier 1  x = json.loads(urlopen(...).read())      -> x = post_envelope(...)
              return json.loads(urlopen(...).read())   -> return post_envelope(...)

      Tier 2  with urlopen(...) as r:
                  body = r.read().decode()             <- single statement
              return json.loads(body)                  -> return post_envelope(...)

      Tier 3  resp = urlopen(...)                      <- optional .read()/.decode()
              data = json.loads(resp.read())           -> data = post_envelope(...)

    Manual SSE framing, extra field access on the parsed result and reuse of the
    raw response text all break under a transport-only swap, so they are
    reported for hand migration instead.
    """
    # A module-level site has no .name; "<module>" keeps the orphan bookkeeping
    # working, and _surviving_names() then checks the whole file for it.
    fname = getattr(func, "name", "<module>")
    pmap = _parent_map(func)
    stmt = _statement_at(func, call_node.lineno)
    if stmt is None:
        return "manual", "unresolved statement", None, None, None, []

    tmo = _timeout_expr(call_node)
    payload = (_envelope_var(req) if req is not None else None) or "body"

    def repl_at(idx, expr):
        indent = " " * (len(lines[idx]) - len(lines[idx].lstrip()))
        return indent + expr + "\n"

    def call_expr(is_return, target=None):
        # raise_on_error=True keeps the script's own error handling intact: the
        # urlopen() being replaced raised on a dead endpoint, it did not return
        # {"error": ...}.
        body = f"post_envelope({payload}, timeout={tmo}, raise_on_error=True)"
        return f"return {body}" if is_return else f"{target} = {body}"

    def consumer(after, value_name):
        """The statement right after `after` that json.loads()es `value_name`."""
        parent = pmap.get(after)
        seq = _stmt_list(parent, after) if parent is not None else None
        if seq is None:
            return None
        idx = next((i for i, s in enumerate(seq) if s is after), None)
        if idx is None or idx + 1 >= len(seq):
            return None
        nxt = seq[idx + 1]
        val = getattr(nxt, "value", None)
        if _call_name(val) != "loads":
            return None
        if not re.search(rf"\b{value_name}\b", ast.unparse(val)):
            return None
        if isinstance(nxt, ast.Return):
            return nxt, True, None
        if isinstance(nxt, ast.Assign) and len(nxt.targets) == 1 \
                and isinstance(nxt.targets[0], ast.Name):
            return nxt, False, nxt.targets[0].id
        return None

    # ---- Tier 1: this very statement reads and parses the response ---------
    if isinstance(stmt, (ast.Assign, ast.Return)):
        val = stmt.value
        if _call_name(val) == "loads" and _contains(pmap, val, call_node):
            if isinstance(stmt, ast.Return):
                expr = call_expr(True)
            elif isinstance(stmt.targets[0], ast.Name):
                expr = call_expr(False, stmt.targets[0].id)
            else:
                return "manual", "assignment target is not a name", None, None, None, []
            start = stmt.lineno - 1
            return "ok", "json.loads(urlopen())", start, stmt.end_lineno, repl_at(start, expr), []

    # ---- Tier 2: `with urlopen(...) as r:` ---------------------------------
    if isinstance(stmt, ast.With):
        item = next((it for it in stmt.items if _contains(pmap, it.context_expr, call_node)), None)
        if item is None:
            return "manual", "urlopen is not the with context expression", None, None, None, []
        if not isinstance(item.optional_vars, ast.Name):
            return "manual", "with target is not a simple name", None, None, None, []
        tgt = item.optional_vars.id
        if len(stmt.body) != 1:
            return "manual", "with body has multiple statements", None, None, None, []
        inner = stmt.body[0]
        ival = getattr(inner, "value", None)
        start = stmt.lineno - 1
        if _call_name(ival) == "loads" and re.search(rf"\b{tgt}\b", ast.unparse(ival)):
            if isinstance(inner, ast.Return):
                expr = call_expr(True)
            elif isinstance(inner.targets[0], ast.Name):
                expr = call_expr(False, inner.targets[0].id)
            else:
                return "manual", "with body parse target is not a name", None, None, None, []
            return "ok", "with urlopen(): json.loads()", start, stmt.end_lineno, \
                   repl_at(start, expr), [(fname, tgt)]
        if isinstance(inner, ast.Assign) and len(inner.targets) == 1 \
                and isinstance(inner.targets[0], ast.Name) \
                and re.search(rf"\b{tgt}\b", ast.unparse(ival)):
            text_var = inner.targets[0].id
            found = consumer(stmt, text_var)
            if found is None:
                return "manual", f"raw text '{text_var}' reused outside a json.loads() swap", None, None, None, []
            nxt, is_ret, name = found
            return "ok", "with urlopen(): read + json.loads()", start, nxt.end_lineno, \
                   repl_at(start, call_expr(is_ret, name)), [(fname, tgt), (fname, text_var)]
        return "manual", "with body shape not modelled", None, None, None, []

    # ---- Tier 3: `resp = urlopen(...)` producer + `json.loads(resp...)` ----
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
            and isinstance(stmt.targets[0], ast.Name) \
            and _contains(pmap, stmt.value, call_node):
        raw_var = stmt.targets[0].id
        found = consumer(stmt, raw_var)
        if found is None:
            return "manual", f"raw value '{raw_var}' reused outside a json.loads() swap", None, None, None, []
        nxt, is_ret, name = found
        start = stmt.lineno - 1
        return "ok", "response object + json.loads()", start, nxt.end_lineno, \
               repl_at(start, call_expr(is_ret, name)), [(fname, raw_var)]

    return "manual", "urlopen site shape not modelled", None, None, None, []


def migrate_file(path, apply=False):
    # utf-8-sig: several Tools scripts carry a BOM, which ast.parse rejects.
    # Reading it transparently keeps the line offsets aligned for the rewrite.
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        src = f.read()

    had_bom = open(path, "rb").read(3) == b"\xef\xbb\xbf"

    if "tools/call" not in src or "urlopen" not in src:
        return "skip", "no raw transport"

    try:
        sites = find_sites(src)
    except SyntaxError as e:
        return "error", f"syntax error: {e}"

    if not sites:
        return "skip", "no urlopen call site"

    lines = src.splitlines(keepends=True)
    edits = []
    orphan_names = []
    for func, call_node, req in sites:
        status, reason, start, end, repl, orphans = _plan_site(func, call_node, req, lines)
        if status != "ok":
            return "manual", f"line {call_node.lineno}: {reason}"
        if end > len(lines):
            return "error", "block out of range"
        edits.append((start, end, repl))
        # Drop the now-dead `req = Request(...)` assignment that precedes the
        # block. Ranges are [start, end) exclusive: req.end_lineno is the
        # 1-based inclusive final line, so the exclusive index is end_lineno.
        if req is not None and req.lineno - 1 < start:
            edits.append((req.lineno - 1, req.end_lineno, ""))
        orphan_names.extend(orphans)

    edits.sort(key=lambda e: e[0], reverse=True)
    out = list(lines)
    for s, e, repl in edits:
        out[s:e] = [repl] if repl else []

    new_src = "".join(out)
    if orphan_names:
        survived = _surviving_names(new_src, orphan_names)
        if survived:
            return "manual", f"surviving code still references '{survived}'"

    if IMPORT_LINE not in new_src:
        # Legal insertion point: after the module docstring AND after every
        # `from __future__ import ...` statement. A future import must
        # precede all other imports, so inserting the line *before* it is a
        # SyntaxError ("from __future__ imports must occur at the beginning
        # of the file") that ast.parse does not report — only compile() does.
        lines_new = new_src.splitlines(keepends=True)
        insert_at = 0
        try:
            for node in ast.parse(new_src).body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                        and isinstance(node.value.value, str):
                    insert_at = node.end_lineno
                    continue
                if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                    insert_at = max(insert_at, node.end_lineno)
                    continue
                break
        except SyntaxError:
            insert_at = 0
        head = "".join(lines_new[:insert_at])
        tail = "".join(lines_new[insert_at:])
        new_src = head + "\n" + IMPORT_LINE + "\n" + tail

    try:
        ast.parse(new_src)
    except SyntaxError as e:
        return "error", f"post-migration syntax error: {e}"

    if apply:
        encoding = "utf-8-sig" if had_bom else "utf-8"
        try:
            with open(path, "w", encoding=encoding) as f:
                f.write(new_src)
        except PermissionError:
            return "skipped-readonly", f"{len(sites)} call site(s) found, file is read-only"
        except OSError as e:
            return "error", f"write failed: {e}"
    return "migrated", f"{len(sites)} call site(s)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(TOOLS_DIR, "*.py")))
    if args.only:
        files = [f for f in files if os.path.basename(f) == args.only]

    counts = {"migrated": 0, "skip": 0, "error": 0, "skipped-readonly": 0}
    for path in files:
        if os.path.basename(path) in EXCLUDED:
            continue
        status, detail = migrate_file(path, apply=args.apply)
        counts[status] = counts.get(status, 0) + 1
        if status != "skip":
            print(f"[{status:16}] {os.path.basename(path):45} {detail}")

    print(f"\nmigrated={counts['migrated']} readonly={counts['skipped-readonly']} "
          f"error={counts['error']} skip={counts['skip']} "
          f"mode={'APPLY' if args.apply else 'DRY-RUN'}")
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
