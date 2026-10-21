# Nous Portal for the Claireon "Claude Code" button

`claude.cmd` shim -> `nous_anthropic_proxy.py` (Anthropic /v1/messages -> Nous chat completions).
Only launches containing `--strict-mcp-config` (the Claireon button) are routed to Nous; plain `claude` is untouched.
The Nous key is re-read from Hermes' `auth.json` on every request (it is short-lived; run Hermes to refresh,
the proxy refreshes it itself via Hermes' venv; override with `NOUS_REFRESH_CMD`). Model: `ensure_proxy.ps1` sets `NOUS_MODEL` to `deepseek/deepseek-v4.1-flash` unless you exported one. The proxy reads the model at start — after a change, kill the running proxy (the listener on the port) and relaunch. Without `NOUS_MODEL`, Hermes `config.yaml` `model.default` is used.

Install: `powershell -File scripts/nous_proxy/install.ps1`, then restart Unreal.
Bypass for one launch: `NOUS_PROXY_DISABLE=1`. Remove: delete `%USERPROFILE%\.claude\nous-shim` and its PATH entry.
