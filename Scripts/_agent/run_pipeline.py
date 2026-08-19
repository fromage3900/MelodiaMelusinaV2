import json, urllib.request, time

def run(name, path, outfile):
    script = open(path, encoding="utf-8").read()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "editor_query",
                                  "arguments": {"action": "run_python", "command": script}}}).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:9316/mcp", data=body, headers={"Content-Type": "application/json"}), timeout=1200).read())
    res = r.get("result", {})
    print(name, "resp:", "ERR " + res.get("content", [{}])[0].get("text", "")[:200] if res.get("isError") else "ok")
    time.sleep(3)
    try:
        print(open(outfile).read())
    except Exception:
        print("no outfile")

run("CONVERT", r"C:\EnvironmentPortfolio\BS_GodFile\Scripts\_agent\convert_new_mats.py",
    r"C:\Users\froma\AppData\Local\Temp\opencode\mat_convert2.json")
run("FIXUP", r"C:\EnvironmentPortfolio\BS_GodFile\Scripts\_agent\fixup_materials.py",
    r"C:\Users\froma\AppData\Local\Temp\opencode\mi_fixup.json")
