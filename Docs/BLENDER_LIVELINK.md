# Blender ↔ Unreal Live Link (port 9876)

BS_GodFile uses the **3DRedbox Live Link** pair:

| Side | Location | UI type |
|------|----------|---------|
| **Blender** | Extension `live_link_unreal` v3.3.1 | **Sidebar panel** (not a floating window) |
| **Unreal** | `Content/Python/livelink_unreal.pyc` + `init_unreal.py` | **Main menu** (not a floating window) |

There is **no dedicated editor window** on either side — only a Blender N-panel tab and a UE menu.

---

## Quick start (correct order)

### 1. Blender — start the server

1. Open **Blender 5.1** (addon is installed under `extensions/user_default/live_link_unreal`).
2. Open any **3D View**.
3. Press **N** to open the right sidebar.
4. Open the **Unreal** tab (panel title: **Live Link to Unreal**).
   - If you do not see it: **Edit → Preferences → Get Extensions → Live Link to Unreal Engine** → ensure it is **enabled**.
   - If you use **N-Panel Orchestrator**: add category `Unreal` (or `Blender > Unreal`) to an essentials group so it is not hidden on startup.
5. Click **Start Live Link** (default **127.0.0.1:9876**).
6. Status should show **Started** / waiting for UE.

### 2. Unreal — connect the client

1. Open **BS_GodFile** in UE **5.8** (`PythonScriptPlugin` enabled in `.uproject`).
2. On editor startup, Output Log should show:
   - `[LiveLink] Menu registered — LiveLink > Blender Live Link`
   - `[LiveLink] v3.1 loaded`
3. Menu bar → **LiveLink** → **Blender Live Link** → **Start Live Link**.
4. Output Log: `[LiveLink] Connected to Blender at 127.0.0.1:9876`.
5. Back in Blender, status becomes **Connected**; use **Send Full Scene**, **Live Sync**, etc.

### 3. Verify without both apps

```bat
python Content\Python\test_livelink_server.py
python Content\Python\test_livelink_client.py
```

Server mocks Blender; client tests the UE-side protocol on port **9876**.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| **UE “Live Link” window/panels do nothing** | Epic’s **Window → Live Link** is a different system (animation capture) | Use **menu bar → LiveLink → Blender Live Link → Start Live Link** instead |
| Blender buttons grey / no Send section | UE has not connected yet | Blender **Start Live Link** first → UE **Start Live Link** → Blender status must show **Connected** |
| No Blender panel | Extension disabled or N-Panel Orchestrator hiding it | Enable extension; add `Unreal` to npanel essentials (see `config/npanel_manager/config.json`) |
| UE menu missing | `PythonScriptPlugin` off or startup script not run | Enable plugin; confirm `Config/DefaultEditor.ini` has `init_unreal.py` startup script; restart editor |
| Menu click, no log output | `livelink_unreal.pyc` missing on disk | Copy `livelink_unreal.py` from 3DRedbox purchase to `Content/Python/`; restart UE |
| `Connection refused` on UE | Blender server not running | Start Live Link in Blender **first**, then UE **Start Live Link** |
| Menu works but import fails | FBX exchange path | Check `%TEMP%\BlenderUnrealLiveLink`; imports land in `/Game/LiveLink/` |
| Wrong Blender version | Addon only in 5.1 extensions | Copy `Tools/BlenderLiveLink/` to `%APPDATA%\Blender Foundation\Blender\<ver>\extensions\user_default\live_link_unreal` |

---

## Project files

| Path | Role |
|------|------|
| `Content/Python/livelink_unreal.pyc` | UE client (socket, FBX import, actor placement) |
| `Content/Python/init_unreal.py` | Startup loader + menu registration (BS_GodFile paths) |
| `Config/DefaultEditor.ini` | `+StartupScripts` → `init_unreal.py` |
| `Tools/BlenderLiveLink/` | Blender extension source copy for reinstall |
| `Content/Python/test_livelink_*.py` | Protocol smoke tests |

---

## Reinstall Blender addon

```powershell
$dst = "$env:APPDATA\Blender Foundation\Blender\5.1\extensions\user_default\live_link_unreal"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force "G:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderLiveLink\*" $dst
```

Restart Blender → enable extension in Preferences if needed.

---

## Notes

- **Not** Epic's animation Live Link plugin — that is a different system.
- Blender is the **server** (listens on 9876); UE is the **client** (connects outbound).
- `send2ue` / Epic Blender Tools are separate pipelines; this live link is independent.
