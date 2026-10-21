"""Melodia remote client for Substance 3D Painter (11.x).

Remote scripting protocol (Adobe official):
  launch Painter with  --enable-remote-scripting
  POST base64-encoded script -> http://localhost:60041/run.json
  body {"python": "<b64>"} or {"js": "<b64>"}

Notes learned the hard way:
  - Python print() comes back as "null"; to return data, raise an exception
    whose message is a JSON string (caller unwraps from the error text).
  - JS (alg.*) returns JSON properly.
  - Long operations: run them in the injected script and have THAT script
    write log/status files to disk; only short calls should block the wire.

Owned by Melodia / Melusina. No Grok*.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request


class PainterError(Exception):
    pass


class RemotePainter:
    def __init__(self, hosts=("[::1]", "localhost", "127.0.0.1"),
                 port: int = 60041, timeout: float = 3600.0):
        # Painter 11.1.1 binds IPv6 [::1] only; try it first, then the
        # common alternatives so this client also works on other builds.
        self.hosts = list(hosts)
        self.port = port
        self.timeout = timeout
        self.host = self.hosts[0]

    # ---------------------------------------------------------------- wire
    def _url(self, host: str) -> str:
        if ":" in host and not host.startswith("["):
            host = "[%s]" % host
        return "http://%s:%d/run.json" % (host, self.port)

    def _post(self, kind: str, script: str) -> str:
        encoded = base64.b64encode(script.encode("utf-8")).decode("utf-8")
        body = json.dumps({kind: encoded}).encode("utf-8")
        last_err = None
        for host in self.hosts:
            req = urllib.request.Request(
                self._url(host), data=body,
                headers={"Content-Type": "application/json",
                         "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8", errors="replace").strip()
                self.host = host
                break
            except urllib.error.URLError as e:
                last_err = e
                continue
        else:
            raise PainterError(
                "Cannot reach Substance Painter remote script server on port "
                "%d (tried %s; %s). Is Painter running with "
                "--enable-remote-scripting?" % (self.port, self.hosts, last_err))
        # Error channel: {"error": "..."} (JS always; python via raised exc)
        if raw.startswith("{"):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, dict) and "error" in data:
                raise PainterError(str(data["error"]))
        return raw

    def exec_python(self, script: str) -> str:
        return self._post("python", script)

    def exec_js(self, script: str) -> str:
        return self._post("js", script)

    # ------------------------------------------------------------- helpers
    def ping(self) -> bool:
        try:
            self.exec_python("pass")
            return True
        except Exception:
            return False

    def wait_ready(self, timeout: float = 240.0, interval: float = 4.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.ping():
                return True
            time.sleep(interval)
        return False

    def run_file(self, path: str) -> str:
        """Execute a python file that lives on this machine inside Painter."""
        p = path.replace("\\", "/")
        bootstrap = (
            "exec(compile(open(r'%s', encoding='utf-8').read(), r'%s', 'exec'))"
            % (p, p))
        return self.exec_python(bootstrap)

    def sheet(self, expr: str):
        """Evaluate a python expression and return parsed JSON via the
        raise-Exception trick."""
        script = (
            "import json\n"
            "try:\n"
            "    _r = (%s)\n"
            "except Exception as _e:\n"
            "    raise\n"
            "raise Exception('MELODIA_RET:' + json.dumps(_r, default=str))"
            % expr)
        try:
            self.exec_python(script)
        except PainterError as e:
            msg = str(e)
            if "MELODIA_RET:" in msg:
                rest = msg.split("MELODIA_RET:", 1)[1].strip()
                # Painter may append traceback text after the payload;
                # raw_decode parses the first complete JSON value only.
                # Some payloads arrive with repr-style \' escaping (invalid
                # JSON) — repair before decoding.
                for attempt in (rest, rest.replace("\\'", "'")):
                    try:
                        value, _ = json.JSONDecoder().raw_decode(attempt)
                        return value
                    except json.JSONDecodeError:
                        continue
                raise
            raise
        raise PainterError("expected exception payload, got clean return")


if __name__ == "__main__":
    import sys
    rp = RemotePainter()
    if rp.wait_ready(timeout=float(sys.argv[1]) if len(sys.argv) > 1 else 60):
        ver = rp.sheet("__import__('substance_painter').__version__")
        print("connected; substance_painter version:", ver)
    else:
        print("NOT READY")
