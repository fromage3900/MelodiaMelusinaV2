"""Test material lookup via UE Python API"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"


def _mcp_call(method, params=None, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    req = urllib.request.Request(
        MCP_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# Call python action with a script
def run_py(script_lines, timeout=30):
    result = _mcp_call("tools/call", {
        "name": "python",
        "arguments": {"script": script_lines, "raise_on_failure": False},
    }, timeout=timeout)
    text = result.get("result", {}).get("content", [{}])[0].get("text", "")
    return text


print("=== Check MI assets exist ===")
for m in ["MI_Niagara_Sparkle", "MI_Niagara_Petal", "MI_Niagara_Mote", "MI_Niagara_Pond"]:
    text = run_py([
        f'import unreal',
        f'm = unreal.load_asset("/Game/EnvSandbox/VFX/Materials/{m}")',
        f'print("{m}: {{}} {{}}".format(type(m).__name__ if m else "None", m.get_path_name() if m else "N/A"))',
    ])
    print(text.strip())

print()
print("=== Try setting renderer material via UE Python ===")
text = run_py([
    "import unreal",
    'sys_path = "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle"',
    'sys = unreal.load_asset(sys_path)',
    "print(f'System: {sys}')",
    "if sys:",
    "  emitters = sys.get_emitter_handles()",
    "  for i, emitter in enumerate(emitters):",
    "    emitter_obj = emitter.get_emitter()",
    "    if emitter_obj is None:",
    "      emitter_obj = emitter.get_emitter_internal()",
    "    if emitter_obj:",
    '      print(f"  Emitter[{i}]: {emitter_obj.get_name()}")',
    "      renderers = emitter_obj.get_renderers() or []",
    "      for ri, r in enumerate(renderers):",
    "        mat = r.get_material()",
    '        print(f"    Renderer[{ri}]({type(r).__name__}): {mat.get_path_name() if mat else None}")',
    "        new_mat = unreal.load_asset('/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle')",
    "        if new_mat:",
    '          r.set_material(new_mat)',
    '          print(f"      -> set to {new_mat.get_path_name()}")',
])
print(text.strip())

# Verify the change
print()
print("=== Verify after Python change ===")
text = run_py([
    "import unreal",
    'sys = unreal.load_asset("/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle")',
    "emitters = sys.get_emitter_handles()",
    "for i, emitter in enumerate(emitters):",
    "  emitter_obj = emitter.get_emitter() or emitter.get_emitter_internal()",
    "  if emitter_obj:",
    '    print(f"  Emitter[{i}]: {emitter_obj.get_name()}")',
    "    renderers = emitter_obj.get_renderers() or []",
    "    for ri, r in enumerate(renderers):",
    "      mat = r.get_material()",
    '      print(f"    Renderer[{ri}]({type(r).__name__}): {mat.get_path_name() if mat else None}")',
])
print(text.strip())
