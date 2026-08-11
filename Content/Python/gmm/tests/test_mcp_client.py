from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from gmm.core.mcp_client import MonolithClient


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class MonolithClientTransportTests(unittest.TestCase):
    def test_status_uses_health_endpoint(self) -> None:
        with patch("urllib.request.urlopen", return_value=_Response({"status": "ok", "version": "0.20.3"})) as mocked:
            result = MonolithClient().status()
        self.assertEqual("ok", result["status"])
        self.assertEqual("http://localhost:9316/health", mocked.call_args.args[0])

    def test_editor_action_uses_mcp_json_rpc(self) -> None:
        tool_result = {"ok": True, "success": True, "output": []}
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": json.dumps(tool_result)}],
                "isError": False,
            },
        }
        with patch("urllib.request.urlopen", return_value=_Response(response)) as mocked:
            result = MonolithClient().run_python("print('ok')")

        request = mocked.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual("http://localhost:9316/mcp", request.full_url)
        self.assertEqual("tools/call", body["method"])
        self.assertEqual("editor_query", body["params"]["name"])
        self.assertEqual("run_python", body["params"]["arguments"]["action"])
        self.assertTrue(result["success"])

    def test_discover_uses_special_tool(self) -> None:
        payload = {"namespace": "editor", "actions": [], "total": 0}
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps(payload)}]},
        }
        with patch("urllib.request.urlopen", return_value=_Response(response)) as mocked:
            result = MonolithClient().discover("editor")
        request = mocked.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual("monolith_discover", body["params"]["name"])
        self.assertEqual({"namespace": "editor"}, body["params"]["arguments"])
        self.assertEqual(0, result["total"])


if __name__ == "__main__":
    unittest.main()
