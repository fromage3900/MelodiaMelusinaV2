# PBR Instance Script Commit Spec — 2026-08-30

**Source:** Untracked file `Content/Python/create_pbr_instances.py` (211 lines)
**Proposed commit:** `chore: add PBR MI creation script for 12 orphaned texture sets`
**Risk:** LOW — non-destructive editor utility; creates assets only when run in UE editor

---

## File to Commit

| Field | Value |
|---|---|
| Path | `Content/Python/create_pbr_instances.py` |
| Lines | 211 |
| Type | Python editor utility (Unreal Python API) |

---

## What It Does

Scans for 12 complete PBR texture sets (Albedo + Normal + Roughness + Metallic ± Height/ORM) that currently have **zero material instances**, and creates MIs for them:

- Parent: `M_Master_Toon_Universal`
- Target folder: `Content/EnvSandbox/Materials/Instances/Environment/Stylized/`
- Texture stems: `FloralBrickGrayScale`, `ZenTrim_Base4K`, `ZenTrim_ColourShift`, `ZenTrim_CrackedToHell`, `ZenTrim_FlowersLIttleBit`, `ZenTrim_FlowersLOTS`, `ZenTrim_FlowersMid`, `ZenTrim_Wet`, `basetrim`, `concretetrim`, `landscape_grass`, `landscapegrayscale`

Safe to commit: script is idempotent (skips existing MIs), requires UE editor to run, produces no side effects when not executed.

---

## Proposed Command

```bash
git add Content/Python/create_pbr_instances.py
git commit -m "chore: add PBR MI creation script for 12 orphaned texture sets

Scans for 12 complete PBR texture sets with zero material instances.
Creates MIs under M_Master_Toon_Universal in Environment/Stylized/.
Idempotent — skips existing MIs. Requires UE editor to execute."
```

---

## Verification

- [ ] Script compiles (`python -m py_compile Content/Python/create_pbr_instances.py`)
- [ ] No runtime side effects (UE editor-only utility)
- [ ] Does not reference any production-critical paths
- [ ] Consistent with existing Python editor utilities in `Content/Python/`