"""Equivalence harness for the Monolith transport migration.

Compares the pristine backup copy of every migrated script against its migrated
copy and checks three things:

  1. request payload - the JSON-RPC body POSTed to the mock server must be
                       identical: the migration swaps the transport only, it
                       must not change what is sent
  2. result value    - the transport helper must return the same object
  3. error mode      - with nothing listening, the helper must fail the same
                       way. urlopen() raised, so migrated call sites pass
                       raise_on_error=True; a silent {"error": ...} would mean
                       swallowed failures that used to crash loudly.

Modes:

    python verify_transport_migration.py                    # every migrated script
    python verify_transport_migration.py foo.py bar.py      # a subset
    python verify_transport_migration.py --residuals        # gate: no hand-rolled POST
    python verify_transport_migration.py --script FILE...   # straight-line scripts
    python verify_transport_migration.py --one DIR FILE NAME URL   # internal

Each helper runs in a sandbox subprocess that executes only the module's
imports/constants and the helper itself - importing whole scripts would run
their module-level work (and hang on server probes). The sandbox is built so a
comparison failure means the migration changed something, never that the
harness reached the wrong place:

  * only the harness endpoint is reachable; every other connect is refused, and
    urlopen() is redirected to the mock, so a backup copy cannot send a command
    to a real Monolith even when it builds its URL by concatenation
  * both copies are anchored to the real tree via __file__, so a path-relative
    check cannot report a difference that only exists in _stage_backup
  * the namespace is a registered module and statements are replayed with their
    decorators, so @dataclass and friends behave the same as in a real import
  * per-call uuid ids are normalised; they are correlation tokens that differ on
    every call by design, and a counter id would still be compared
"""
from __future__ import annotations

import ast
import glob
import io
import json
import os
import re
import socket
import subprocess
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, HTTPServer

BACKUP = r"C:\EnvironmentPortfolio\_stage_backup\Tools"
CURRENT = os.path.dirname(os.path.abspath(__file__))
SKIP = {"mcp_client.py", "verify_transport_migration.py", "migrate_monolith_calls.py"}
URL_RE = re.compile(r"https?://(?:127\.0\.0\.1|localhost):\d+/?[^\"')\s]*")

RESPONSE = {"jsonrpc": "2.0", "id": 1,
            "result": {"isError": False,
                       "content": [{"type": "text", "text": "MOCK_UE_OK"}]}}

CAPTURED = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        CAPTURED.append(self.rfile.read(length))
        data = json.dumps(RESPONSE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def helpers(path, marker):
    """Top-level functions in `path` whose code contains `marker`.

    ast.dump() over the function node picks up nested call names, which is how
    the backup's urlopen() helper and the migrated post_envelope() helper are
    matched up without a hand-maintained name list.
    """
    try:
        src = open(path, "r", encoding="utf-8-sig", errors="ignore").read()
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    return [node.name for node in tree.body
            if isinstance(node, ast.FunctionDef) and marker in ast.dump(node)]


def takes_required_args(path, name):
    """True when the helper has at least one parameter without a default.

    Several scripts keep a zero-argument probe next to the real transport
    helper (monolith_reachable(), check_monolith(), wait_for_monolith()). Both
    mention the transport, so the arity is what tells them apart: a helper that
    takes no arguments cannot be the one under test.
    """
    try:
        tree = ast.parse(open(path, "r", encoding="utf-8-sig", errors="ignore").read())
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            args = node.args
            positional = list(getattr(args, "posonlyargs", [])) + list(args.args)
            positional += list(args.kwonlyargs)
            # ast leaves default=None for a parameter that has no default.
            return any(getattr(a, "default", None) is None for a in positional)
    return False


def pick_helper(old_path, new_path):
    """Name of the transport helper shared by both copies of a script."""
    old = helpers(old_path, "urlopen")
    new = helpers(new_path, "post_envelope") + helpers(new_path, "post_text")
    common = [n for n in new if n in old]
    if not common:
        return None
    preferred = ("monolith", "mcp", "call", "rpc", "post", "invoke", "send", "request")
    common.sort(key=lambda n: (not any(p in n.lower() for p in preferred),
                               not takes_required_args(old_path, n)))
    return common[0]


SAFE_CALL = {"str", "int", "float", "bool", "list", "dict", "tuple", "set", "len",
             "min", "max", "sum", "sorted", "isinstance", "getattr", "hasattr",
             "repr", "zip", "enumerate", "range", "Path", "format"}
RISKY_ATTR = {"urlopen", "system", "popen", "call", "check_call", "check_output",
              "run", "sleep", "remove", "unlink", "rename"}
RISKY_SUBSTR = ("write", "save", "dump", "mkdir", "remove", "unlink", "delete",
                "move", "copy", "rename", "exec", "system", "popen", "urlopen",
                "sleep", "request")

PROBE_ARG = {"action": "run_python", "command": "print(1)"}
URLISH = ("url", "endpoint", "base_url", "server", "host", "address")
TOOLISH = ("tool", "name", "method", "action", "namespace", "ns", "command")
ARGSISH = ("args", "argument", "params", "payload", "body", "data", "message",
           "envelope")


def install_network_guard(allowed_port):
    """Refuse every outbound connection except the harness endpoint.

    Backup copies build their URL by concatenation ("http://127.0.0.1:" +
    str(PORT)), which a literal rewrite cannot catch - six scripts were
    reaching the real Monolith on 9316 and running commands in a live editor.
    Blocking every other port keeps verification offline and deterministic.
    """
    import errno as _errno
    import socket as _socket

    real_connect = _socket.socket.connect
    real_connect_ex = _socket.socket.connect_ex

    def port_of(address):
        if isinstance(address, (tuple, list)) and len(address) > 1:
            try:
                return int(address[1])
            except (TypeError, ValueError):
                return None
        return None

    def connect(self, address):
        if port_of(address) != allowed_port:
            raise ConnectionRefusedError(f"harness blocked connection to {address}")
        return real_connect(self, address)

    def connect_ex(self, address):
        if port_of(address) != allowed_port:
            return _errno.ECONNREFUSED
        return real_connect_ex(self, address)

    _socket.socket.connect = connect
    _socket.socket.connect_ex = connect_ex


def install_urlopen_redirect(url, ns):
    """Point every urlopen() at `url`, whatever endpoint the script built.

    The body, headers and method are passed through untouched, so the payload
    the mock captures is still the thing under test.
    """
    import urllib.request as _ur

    real_urlopen = _ur.urlopen

    def redirected(target, data=None, timeout=None, **kw):
        method, headers = kw.get("method"), {}
        if isinstance(target, _ur.Request):
            method = target.get_method()
            headers = dict(target.header_items())
            if data is None:
                data = target.data
        new = _ur.Request(url, data=data, headers=headers, method=method)
        return real_urlopen(new, timeout=timeout)

    _ur.urlopen = redirected
    # `from urllib.request import urlopen` bound the original into the script's
    # own namespace, so that name has to be rebound after the replay.
    ns["urlopen"] = redirected


def _replayable(node):
    """True when a module-level statement can run without side effects.

    Scripts end with things like `result = monolith("editor_query", {...})`, so
    replaying every assignment would fire the very call under test (and fail
    before the helper exists). Calls through a bare name are allowed only for
    builtins; attribute calls are allowed unless the attribute can reach
    outside the process or touch the filesystem (write_text, save_config, ...).
    """
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        fn = child.func
        if isinstance(fn, ast.Name):
            if fn.id not in SAFE_CALL:
                return False
        elif isinstance(fn, ast.Attribute):
            attr = fn.attr.lower()
            if fn.attr in RISKY_ATTR or any(s in attr for s in RISKY_SUBSTR):
                return False
    return True


SOCK_TARGET = re.compile(r"\(\s*['\"]127\.0\.0\.1['\"]\s*,\s*\d{2,5}\s*\)")


def rewrite_targets(url, seg):
    """Point a replayed statement at the harness endpoint.

    Two forms have to be redirected: http:// literals, and the raw socket
    reachability probes several scripts gate on before they will call Monolith
    at all. Without the second, cross_path_validation.py sees a closed port,
    short-circuits and never sends a request - both copies identically, which
    looks like a pass but compares nothing.
    """
    port = re.search(r":(\d+)", url).group(1)
    seg = SOCK_TARGET.sub(f"('127.0.0.1', {port})", seg)
    return URL_RE.sub(url, seg)


def source_with_decorators(src, node):
    """Source text of a statement, decorators included.

    ast.get_source_segment() starts a decorated node at its `def`/`class` line
    and drops the decorator lines entirely. Replaying a dataclass that way
    silently produces a field-less class, and the helper then fails with
    "CheckResult() takes no arguments" on both copies - a sandbox artefact
    that looks exactly like a migration defect.
    """
    start = node.lineno
    for decorator in getattr(node, "decorator_list", []) or []:
        start = min(start, getattr(decorator, "lineno", start))
    end = getattr(node, "end_lineno", start) or start
    return "\n".join(src.splitlines()[start - 1:end])


def sandbox_call(directory, path, name, url):
    """Execute one helper in isolation and print its outcome (--one mode).

    Only the module's imports, replayable constants and function definitions are
    executed, so module-level work (server probes, `__main__` blocks, sleeps)
    never runs. Literal 127.0.0.1 URLs are rewritten to `url` so the backup copy
    talks to the mock server rather than to a real Monolith.
    """
    src = open(path, "r", encoding="utf-8-sig", errors="ignore").read()
    tree = ast.parse(src)

    sys.path.insert(0, CURRENT)
    import mcp_client
    mcp_client.MONOLITH_URL = url

    install_network_guard(int(re.search(r":(\d+)", url).group(1)))
    # A registered module, not a bare dict: dataclasses and typing.get_type_hints
    # resolve a class's string annotations through sys.modules[cls.__module__],
    # so a namespace that is not in sys.modules makes @dataclass blow up with
    # "'NoneType' object has no attribute '__dict__'".
    sandbox_module = types.ModuleType("verify_sandbox")
    sys.modules["verify_sandbox"] = sandbox_module
    ns = sandbox_module.__dict__
    ns.update({"__name__": "verify_sandbox", "__file__": path,
               # The backup copy lives in _stage_backup, so a __file__-relative
               # lookup (sentinel file, audit output, project root) would
               # resolve somewhere else and report a difference that has
               # nothing to do with the transport. Both sides are anchored to
               # the real tree; only the transport code differs between them.
               "post_envelope": mcp_client.post_envelope})
    ns["__file__"] = os.path.join(CURRENT, os.path.basename(path))
    defs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    # Kept for the report: a statement that could not be replayed is usually
    # harmless, but when the helper then trips over a missing global, this is
    # the only way to tell a sandbox gap from a real defect.
    replay_errors = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)) or isinstance(node, defs):
            # Definitions are inert at exec time; only decorators run.
            pass
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            if not _replayable(node):
                continue
        else:
            continue
        seg = source_with_decorators(src, node)
        if not seg:
            continue
        try:
            exec(compile(rewrite_targets(url, seg), path, "exec"), ns)
        except Exception as exc:
            # Module-level constants routinely depend on names produced by a
            # loop or block the replay skips. Losing one must not abort the
            # replay - the helper is the only thing under test here.
            replay_errors.append(f"L{getattr(node, 'lineno', '?')}: "
                                  f"{type(exc).__name__}: {str(exc)[:70]}")
            continue
    install_urlopen_redirect(url, ns)

    if name not in ns:
        print("EXC=NoSuchHelper")
        return

    fn = ns[name]
    try:
        out = invoke(fn, url)
    except NameError as exc:
        print("EXC=NameError " + str(exc) + " || replayed-failed: "
              + "; ".join(replay_errors[:5]))
        return
    except TypeError as e:
        if "argument" not in str(e):
            raise
        out = fn(name="editor_query", arguments=dict(PROBE_ARG))
    print("VALUE=" + repr(out))


def probe_value(param, url):
    """A fixed stand-in for one helper parameter.

    Any deterministic choice is sound here: both copies receive the same
    argument, so a captured payload still proves the migration preserved what
    goes on the wire. Only the endpoint is forced to the harness mock.
    """
    name = param.name.lower()
    if any(k in name for k in URLISH):
        return url
    if any(k in name for k in ARGSISH):
        return dict(PROBE_ARG)
    if any(k in name for k in TOOLISH):
        return "editor_query"
    if name in ("timeout", "deadline", "seconds", "wait"):
        # Short on purpose: against the dead endpoint a retry loop such as
        # wait_for_monolith() would otherwise spin for the whole probe value,
        # and the mock answers instantly anyway.
        return 2
    ann = param.annotation
    text = ann if isinstance(ann, str) else getattr(ann, "__name__", "")
    if text in ("int", "float"):
        return 45
    if text in ("dict", "Dict", "Mapping", "MutableMapping"):
        return dict(PROBE_ARG)
    if text in ("list", "List", "tuple", "Tuple", "Sequence"):
        return []
    return "editor_query"


def invoke(fn, url):
    """Call `fn` with arguments that actually fit its signature.

    Helpers in this tree take (tool, args), (url, payload), (action, args) or a
    single namespace string. Guessing one shape made ten scripts raise
    TypeError on both copies and compare nothing at all.
    """
    import inspect

    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        sig = None

    attempts = []
    if sig is not None:
        # Every parameter gets a value, defaults included: helpers such as
        # check_monolith(variant_filter=None) and wait_for_monolith(timeout=120)
        # have nothing required, so passing only the mandatory ones left them
        # uncallable and the comparison never happened.
        params = [p for p in sig.parameters.values()
                  if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD,
                                p.KEYWORD_ONLY)]
        pos = [p for p in params
               if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        kw = {p.name: probe_value(p, url) for p in params
              if p.kind is p.KEYWORD_ONLY}
        if pos:
            attempts.append(lambda: fn(*[probe_value(p, url) for p in pos], **kw))
        if kw:
            attempts.append(lambda: fn(**kw))

    attempts.append(lambda: fn("editor_query", dict(PROBE_ARG)))
    attempts.append(lambda: fn(name="editor_query", arguments=dict(PROBE_ARG)))

    last = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            if "argument" not in str(exc):
                raise
            last = exc
    raise last


def norm_exc(tag):
    """Exception class name only (messages carry port numbers and paths)."""
    if not tag.startswith("EXC="):
        return tag
    return tag.split("=", 1)[1].split(".")[-1]


HEX_ID = re.compile(r"^[0-9a-f]{8,}$")


def norm_id(obj):
    """Collapse per-call JSON-RPC ids so two runs can be compared.

    An id built from uuid4().hex is a correlation token that is different on
    every call by design, so it can never match across the two runs. Numeric
    ids are left alone: a counter that changed would be a real difference.
    """
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key == "id" and isinstance(value, str) and HEX_ID.match(value):
                out[key] = "<per-call-id>"
            else:
                out[key] = norm_id(value)
        return out
    if isinstance(obj, list):
        return [norm_id(v) for v in obj]
    return obj


def norm_payloads(payloads):
    out = []
    for raw in payloads:
        try:
            out.append(norm_id(json.loads(raw.decode("utf-8"))))
        except Exception:
            out.append(raw)
    return out


def leaks(src):
    """Residual hand-rolled transport in a file the migrator migrated."""
    found = []
    if re.search(r"\burlopen\s*\(", src):
        found.append("urlopen")
    if re.search(r"\bRequest\s*\(", src):
        found.append("Request")
    return found


def run(path, directory, name, url):
    """Invoke one helper in a sandbox subprocess; return (tag, payloads)."""
    del CAPTURED[:]
    try:
        proc = subprocess.run([sys.executable, os.path.abspath(__file__), "--one",
                               directory, path, name, url],
                              capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return "EXC=TimeoutExpired", list(CAPTURED)

    for line in (proc.stdout or "").splitlines():
        if line.startswith("VALUE="):
            return line, list(CAPTURED)

    err = [ln for ln in (proc.stderr or "").strip().splitlines() if ln.strip()]
    if not err:
        # No value and no traceback: the helper never ran (sandbox gap), which
        # must never be mistaken for equivalence.
        return "UNVERIFIED=no-output", list(CAPTURED)
    last = err[-1]
    match = re.match(r"([A-Za-z_.]*(?:Error|Exception)[A-Za-z_.]*)", last)
    return "EXC=" + (match.group(1) if match else last[:60]), list(CAPTURED)


MONOLITH_EP = re.compile(r"(127\.0\.0\.1|localhost):9316")


def _hits_monolith(node, mono_vars, src):
    """True when this expression evaluates to a Monolith endpoint.

    `Request(MONOLITH_URL, ...)` and `Request("http://127.0.0.1:" + str(P))`
    have to be recognised through the names they were bound to, which is what
    the fixed-point pass over assignments in monolith_residuals builds up.
    """
    if node is None:
        return False
    text = ast.get_source_segment(src, node) or ""
    if "9316" in text:
        return True
    return any(isinstance(n, ast.Name) and n.id in mono_vars for n in ast.walk(node))


def monolith_residuals(src):
    """Hand-rolled Monolith transport still present, with the lines to fix.

    The other HTTP clients in this tree are not MCP envelopes and must keep
    urllib: Ollama on 11434, Voicevox on 50021, OpenRouter and the bearer-auth
    vision lane. Endpoint resolution is per call site, so a dashboard that
    polls both Monolith and Ollama only reports the Monolith half.
    """
    if not MONOLITH_EP.search(src):
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()

    mono_vars = set()
    for _ in range(3):  # transitive: req -> MONOLITH_URL -> "...:9316..."
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not _hits_monolith(node.value, mono_vars, src):
                continue
            mono_vars.update(t.id for t in targets if isinstance(t, ast.Name))

    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        label = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if label not in ("urlopen", "Request"):
            continue
        if not _hits_monolith(node.args[0] if node.args else None, mono_vars, src):
            continue
        hits.append(f"L{node.lineno}: {lines[node.lineno - 1].strip()[:88]}")
    return sorted(set(hits))


def scan_residuals(only=None):
    """Repo-wide gate: no script may hand-roll the Monolith envelope."""
    out = []
    for path in sorted(glob.glob(os.path.join(CURRENT, "*.py"))):
        name = os.path.basename(path)
        if name in SKIP or (only and name not in only):
            continue
        src = open(path, "r", encoding="utf-8-sig", errors="ignore").read()
        hits = monolith_residuals(src)
        if hits:
            out.append((name, hits))
    return out


SCRIPT_RESPONSE = {"jsonrpc": "2.0", "id": 1,
                   "result": {"isError": False,
                              "content": [{"type": "text", "text": "MOCK_UE_OK"}]}}


def payload_bytes(body):
    """The bytes each transport would put on the wire, for a like-for-like diff."""
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    if isinstance(body, str):
        return body.encode()
    return json.dumps(body).encode()


def stub_new_transport(captured):
    """Replace post_envelope/post_text so nothing leaves the process."""
    import mcp_client

    saved = (mcp_client.post_envelope, mcp_client.post_text)

    def envelope(body, **kw):
        captured.append(payload_bytes(body))
        return json.loads(json.dumps(SCRIPT_RESPONSE))

    def text(body, **kw):
        captured.append(payload_bytes(body))
        return json.dumps(SCRIPT_RESPONSE)

    mcp_client.post_envelope = envelope
    mcp_client.post_text = text
    return saved


def stub_old_transport(captured):
    """Replace urlopen so the backup copy cannot reach a real Monolith."""
    import urllib.request

    saved = urllib.request.urlopen

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(SCRIPT_RESPONSE).encode()

    def fake_urlopen(target, timeout=None, *a, **kw):
        data = getattr(target, "data", None)
        captured.append(payload_bytes(data) if data is not None else None)
        return FakeResponse()

    urllib.request.urlopen = fake_urlopen
    return saved


def run_script_side(path, stub):
    """Execute a top-level script with its transport stubbed.

    Some scripts are straight-line code with no helper function, so the
    function-level sandbox has nothing to call. Running the whole file is only
    safe because the transport is stubbed - it is never opt-in per file inside
    main(), the operator names the files explicitly via --script.
    """
    import contextlib
    import importlib.util

    captured = []
    saved = stub(captured)
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            spec = importlib.util.spec_from_file_location("script_under_test", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["script_under_test"] = module
            spec.loader.exec_module(module)
    finally:
        if isinstance(saved, tuple):
            import mcp_client
            mcp_client.post_envelope, mcp_client.post_text = saved
        else:
            import urllib.request
            urllib.request.urlopen = saved
    return captured, buffer.getvalue()


def compare_script(name):
    """Payload + stdout + stderr parity for a top-level script."""
    old_path = os.path.join(BACKUP, name)
    if not os.path.exists(old_path):
        print(f"  skip {name}: no backup to compare")
        return True
    old_pay, old_out = run_script_side(old_path, stub_old_transport)
    new_pay, new_out = run_script_side(os.path.join(CURRENT, name), stub_new_transport)
    problems = []
    if [norm_payloads([p])[0] for p in old_pay] != [norm_payloads([p])[0] for p in new_pay]:
        problems.append(f"payloads {len(old_pay)} -> {len(new_pay)}: "
                        f"{old_pay[:2]} -> {new_pay[:2]}")
    if not new_pay:
        problems.append("no request captured on the migrated side")
    if old_out != new_out:
        problems.append(f"output {old_out.strip()[:120]!r} -> {new_out.strip()[:120]!r}")
    if problems:
        print(f"  DIVERGENT  {name:44} (top-level script)")
        for p in problems:
            print(f"   - {p[:300]}")
        return False
    print(f"  equivalent {name:44} (top-level script, {len(new_pay)} request(s))")
    return True


def main():
    only = set(sys.argv[1:])
    port = free_port()
    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    dead = free_port()  # nothing ever listens here
    mock = f"http://127.0.0.1:{port}/mcp"
    gone = f"http://127.0.0.1:{dead}/mcp"
    print(f"mock Monolith on {mock}, dead endpoint on {gone}\n")

    clean, broken, skipped, residual = [], [], [], []
    for path in sorted(glob.glob(os.path.join(CURRENT, "*.py"))):
        name = os.path.basename(path)
        if name in SKIP or (only and name not in only):
            continue
        src = open(path, "r", encoding="utf-8-sig", errors="ignore").read()
        residual_hits = monolith_residuals(src)
        if residual_hits:
            residual.append((name, residual_hits))
        if "post_envelope" not in src and "post_text" not in src:
            continue
        old_path = os.path.join(BACKUP, name)
        if not os.path.exists(old_path):
            skipped.append((name, "no backup to compare"))
            continue
        helper = pick_helper(old_path, path)
        if helper is None:
            skipped.append((name, "no shared helper name "
                                 "(verify with --script " + name + ")"))
            continue

        old_tag, old_body = run(old_path, BACKUP, helper, mock)
        new_tag, new_body = run(path, CURRENT, helper, mock)
        old_dead, _ = run(old_path, BACKUP, helper, gone)
        new_dead, _ = run(path, CURRENT, helper, gone)

        # A NameError on both sides means the sandbox could not supply a module
        # global (not a migration defect) - but a NameError on one side only is
        # exactly the payload-variable bug this harness exists to catch.
        if "NoSuchHelper" in old_tag + new_tag:
            skipped.append((name, f"helper missing from sandbox ({old_tag}/{new_tag})"))
            continue
        if "NameError" in old_tag and "NameError" in new_tag:
            skipped.append((name, f"sandbox missing globals ({old_tag})"))
            continue

        # A run that never reached the server proves nothing. Two shapes count:
        # both copies returned a value, or both failed identically *after* their
        # request went out - failing the same way is equivalence too.
        ran = [t for t in (old_tag, new_tag) if t.startswith("VALUE=")]
        reached = bool(old_body) and bool(new_body)
        proved = ((len(ran) == 2 and reached)
                  or (reached and old_tag == new_tag and old_tag.startswith("EXC=")))
        if not proved:
            skipped.append((name, f"not verifiable (old={old_tag[:40]!r} "
                                  f"new={new_tag[:40]!r} payloads={len(old_body)}/{len(new_body)})"))
            continue

        problems = []
        if norm_payloads(old_body) != norm_payloads(new_body):
            problems.append(f"payload {old_body} -> {new_body}")
        if old_tag != new_tag:
            problems.append(f"result {old_tag} -> {new_tag}")
        if norm_exc(old_dead) != norm_exc(new_dead):
            problems.append(f"error-mode {norm_exc(old_dead)} -> {norm_exc(new_dead)}")
        if residual_hits:
            problems.append("residual " + " | ".join(residual_hits))

        if problems:
            broken.append((name, helper, problems))
            print(f"  DIVERGENT  {name:44} ({helper})")
        else:
            clean.append(name)
            print(f"  equivalent {name:44} ({helper})")

    server.shutdown()
    print(f"\nequivalent: {len(clean)}   divergent: {len(broken)}   skipped: {len(skipped)}")
    for name, why in skipped:
        print(f"  skip {name}: {why}")
    for name, helper, problems in broken:
        print(f"\n!! {name} ({helper})")
        for p in problems:
            print(f"   - {p[:400]}")
    stragglers = residual + [row for row in scan_residuals(only)
                             if row[0] not in {name for name, _ in residual}]
    if stragglers:
        print("\n!! hand-rolled Monolith transport still present")
        for name, hits in stragglers:
            for hit in hits:
                print(f"   - {name} {hit}")
    return 1 if (broken or stragglers) else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--one":
        sandbox_call(*sys.argv[2:6])
    elif len(sys.argv) > 1 and sys.argv[1] == "--script":
        ok = all([compare_script(n) for n in sys.argv[2:]])
        sys.exit(0 if ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--residuals":
        found = scan_residuals(set(sys.argv[2:]) or None)
        for name, hits in found:
            for hit in hits:
                print(f"{name} {hit}")
        print(f"files with hand-rolled Monolith transport: {len(found)}")
        sys.exit(1 if found else 0)
    else:
        sys.exit(main())
