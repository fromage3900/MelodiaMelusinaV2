# UE 5.8 — Redirector cleanup (no “Fix Up Redirectors”)

That old Content Browser folder command **does not appear in Unreal Engine 5.8**. Agents and older runbooks kept saying it anyway. Use one of the methods below.

Official Epic doc (5.8): [Asset Redirectors](https://dev.epicgames.com/documentation/unreal-engine/asset-redirectors-in-unreal-engine)

## Method A — Editor UI (5.8)

1. Content Browser → **Filters** (funnel) → enable either:
   - **Other Filters → Show Redirectors**, or
   - **Miscellaneous → Redirectors** (shows only redirectors)
2. Browse `/Game/EnvSandbox` (and Melusina folders if needed).
3. Select redirector asset(s) → right-click → **Fixup**.
4. **Save All** when done.

Some 5.5+ builds also show **Update Redirector References** on a folder context menu. If you see that name, it is the same job — use it. If you do not, use **Fixup** on the redirector assets themselves (Epic’s documented 5.8 path).

## Method B — Python in the editor (preferred for this project)

With the project open:

```text
py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_migration_redirectors.py"
```

Or Output Log → same `py` line. Script lives at [`Content/Python/fix_migration_redirectors.py`](../Content/Python/fix_migration_redirectors.py) and targets `/Game/EnvSandbox/Materials` by default.

## Method C — Commandlet (no menu hunting)

From a shell (adjust engine path if needed):

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -run=ResavePackages -fixupredirects -projectonly -unattended -stdout
```

This rewrites referencers and cleans redirectors. It can take a while; close the interactive editor first so packages are not locked.

## What you do *not* need

- Searching for a menu item literally named **Fix Up Redirectors in Folder**
- Letting anyone tell you that exact UE4/early-UE5 label still exists in 5.8
