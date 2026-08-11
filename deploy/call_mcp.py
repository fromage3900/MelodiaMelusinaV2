import sys
import json
import urllib.request

def call_mcp(method, params=None):
    url = "http://127.0.0.1:9316/mcp"
    req_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    data = json.dumps(req_data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: call_mcp.py <method> [json_params]")
        sys.exit(1)
    
    method = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    result = call_mcp(method, params)
    print(json.dumps(result, indent=2))
