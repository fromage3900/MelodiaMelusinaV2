import json
import urllib.request

def get_status():
    url = "http://127.0.0.1:9316/mcp"
    req_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "editor_query",
            "arguments": {
                "action": "get_build_status"
            }
        }
    }
    data = json.dumps(req_data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_status()
