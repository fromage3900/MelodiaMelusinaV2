"""Cascadeur-side MCP execution command.

Installed into ``<Cascadeur>/resources/scripts/python/commands/externals/`` so that
Cascadeur registers it as a command. The MCP server launches it once per call with::

    cascadeur.exe --run-script commands.externals.csc_mcp_exec

``run(scene)`` is invoked on Cascadeur's main thread, connects back to the MCP server
(which is acting as a TCP server), receives a request, executes it with full ``csc``
access, and returns the result. This mirrors the proven cascadeur_bridge pattern, so
all scene access happens safely on the main thread.

Source: ysk424/cascadeur-mcp (MIT), file cascadeur_side/externals/csc_mcp_exec.py,
verified against the 2025.1 install in this project on 2026-08-08.
"""

import csc
import socket
import json
import os
import io
import tempfile
import contextlib
import traceback

_HEADER = 64
_PORT_FILE = os.path.join(tempfile.gettempdir(), "cascadeur_mcp.json")


def command_name():
    return "External commands.MCP Exec"


def command_description():
    return "Bridge command used by the Cascadeur MCP server"


def _read_port():
    with open(_PORT_FILE, "r", encoding="utf-8") as f:
        return int(json.load(f)["port"])


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed before expected bytes were received")
        buf += chunk
    return buf


def _recv_json(sock):
    length = int(_recv_exact(sock, _HEADER).decode("utf-8").strip())
    return json.loads(_recv_exact(sock, length).decode("utf-8"))


def _send_json(sock, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = str(len(data)).encode("utf-8")
    header += b" " * (_HEADER - len(header))
    sock.sendall(header)
    sock.sendall(data)


def _jsonable(obj):
    """Best-effort: return obj if JSON serialisable, else its repr."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return repr(obj)


def run(scene):
    try:
        port = _read_port()
    except Exception:
        # No port file -> MCP server is not expecting us. Nothing to do.
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("localhost", port))
        request = _recv_json(sock)
        code = request.get("code", "")

        app = csc.app.get_application()
        namespace = {
            "csc": csc,
            "scene": scene,
            "app": app,
            "result": None,
        }
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                exec(code, namespace)
            response = {
                "status": "success",
                "result": _jsonable(namespace.get("result")),
                "stdout": out.getvalue(),
            }
        except Exception:
            response = {
                "status": "error",
                "message": traceback.format_exc(),
                "stdout": out.getvalue(),
            }
        _send_json(sock, response)
    except Exception:
        # Connection problems: surface in Cascadeau's log and give up.
        try:
            scene.error("MCP Exec failed:\n" + traceback.format_exc())
        except Exception:
            pass
    finally:
        try:
            sock.close()
        except Exception:
            pass