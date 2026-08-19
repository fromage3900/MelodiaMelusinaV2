# VRM4U NPC placeholders — setup and use (2026-08-14)

Supersedes the state claims in [`Docs/MELODIA_NPC_VRM4U_READINESS_2026-07-11.md`](../MELODIA_NPC_VRM4U_READINESS_2026-07-11.md),
which is **stale on three counts** (see §1). Its *advice* still holds; its
*facts* do not.

---

## 1. What changed since the 07-11 readiness doc

| 07-11 doc says | Verified 2026-08-14 |
|---|---|
| "No VRM4U plugin directory or enabled-plugin declaration was found" | **Plugin is present** at `Plugins/VRM4U/`, `EngineVersion: 5.8.0`, 8 modules, **and already built** — `Binaries/Win64/UnrealEditor-VRM4U.dll` and friends exist. |
| "11 source manifests but **no actual `.vrm` source files**" | **Three real `.vrm` files exist**, ~20 MB each, dated 2026-07-12: `SD_02_PetalPriestess`, `CW_01_StarWeaver`, `MD_01_TwilightDancer` — all under `Content/NPCs/VRM_Sources/VRoidHub/`. |
| Recommends starting with `SD_02_PetalPriestess` | **Still the right call — and its `.vrm` is one of the three you have.** The MVP slice is unblocked. |

**The one thing actually blocking you:** VRM4U is **not enabled** in
`BS_GodFile.uproject`. The plugin is on disk and compiled; the project just
never declares it.

---

## 2. Blockers, in the order they will bite

### B1 — VRM4U is not enabled (hard blocker)

`BS_GodFile.uproject` has 57 plugin entries and **VRM4U is not among them**.
Nothing VRM-related can import until it is.

This is a **never-touch file** (`CLAUDE.md`) and needs `SKIP_PROTECTION=1` plus
owner sign-off. It also already carries an uncommitted `MelodiaWardrobe` addition
and a UTF-8 BOM, so the edit should be batched with that decision rather than
made in isolation.

Add, matching the file's existing PowerShell-style formatting:

```json
{
    "Name":  "VRM4U",
    "Enabled":  true
},
```

Then **restart the editor**. VRM4U's modules carry reflected types, so Live
Coding cannot register them — a full editor restart (and a `Build.bat` pass if
the binaries go stale) is required.

### B2 — the `.vrm` files are untracked and unlicensed-in-repo

All three are **untracked** (`.gitignore:99`). Two consequences:

- They exist only on this machine. A collaborator clone has the `.vrm.json`
  manifests and none of the models.
- **No `vrm_registry.json` exists anywhere in the tree**, so author, license,
  and attribution are recorded nowhere. VRoid Hub models carry per-model use
  conditions. Record them before any capture, portfolio shot, or release build.

Do not commit the `.vrm` files until the license line is written down. ~62 MB
total is trivial against the LFS budget; the licensing is the real gate.

### B3 — placeholder coordinates are for the wrong map

Fixed today, partially. `setup_melodia_npc_placeholders.py` and
`verify_melodia_npc_placeholders.py` both hardcoded `MAP_PATH = "/Game/ZenForestTest"`
— an art/greybox level, not the product route. Both now default to
`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` and honour a
`MELODIA_NPC_MAP` env override.

**The coordinates were not fixed and cannot be, from outside the editor.** The
three `location` tuples were authored against ZenForestTest geometry and will
drop the cast into arbitrary space in the new map. A run of the script now means
"the actors exist", not "the actors are placed".

---

## 3. The path, once B1 is cleared

Ordered so each step is provable before the next.

### Step 1 — placeholders first, VRM second

`UMelodiaNPCPlaceholder` (C++, `Plugins/MelodiaCore/Source/MelodiaCore/`) already
exists and needs no VRM at all. Run it and get the *interaction loop* right
before adding a 20 MB character on top:

```
approach -> prompt ("Press E to talk") -> 1-2 lines -> clear direction to the encounter
```

```powershell
# editor Python, one editor only
py Content/Python/setup_melodia_npc_placeholders.py
py Content/Python/verify_melodia_npc_placeholders.py
```

Then drag each actor to a sensible spot on the route and **copy the transforms
back into the `NPCS` tuple** so the script becomes reproducible. That closes B3.

### Step 2 — import exactly one VRM

`SD_02_PetalPriestess` only. Not all three.

- Import to `/Game/NPCs/Imported/SakuraDreamer/`.
- VRM4U produces a skeletal mesh, a skeleton, an anim BP, and a MToon material
  set. The project already has `Content/NPCs/Materials/MM_Melodia_NPC_MToon.uasset`
  and `MPC_NPC_Global` — prefer those over VRM4U's generated masters so NPCs
  match the toon spine rather than diverging from it.
- **Do not run `generate_npc_batch()`.** The 07-11 doc is right about this: with
  8 of 11 models missing it produces misleading failures and large asset churn.

### Step 3 — one Blueprint, swap the visual

`BP_NPC_SD_02_PetalPriestess` from the imported mesh, reusing the placeholder's
interaction component so dialogue/prompt/guidance carry over unchanged. The
placeholder is the contract; the VRM is a skin over it.

Idle animation, capsule collision, short interaction radius. Nothing else.

### Step 4 — only then, battle handoff

Let it request an encounter through the existing allowlist
(`DA_MelodiaIntegrationConfig` → `EncounterIds`) using an existing
`FMelodiaEnemyDef`. **Do not** use the generated NPC battle catalog as runtime
C++ until a deliberate data-import path exists.

---

## 4. Why placeholders are the right call for "unique NPC battles"

The interesting variable is not the model. Three VRoid characters with identical
skill sets, identical pattern density, and identical HP are three identical
fights wearing different hats.

Get encounter *difference* proven on placeholders — different `battle_enemy_id`,
different rhythm pattern density, different skill sets — and the VRM import
becomes a pure art swap that cannot regress the mechanics. Doing it the other
way round means every combat tuning pass drags 60 MB of character import with it.

`MelodiaNPCPlaceholder` exposes `battle_enemy_id` and it is currently set to `""`
for all three placeholders. That empty field is the actual starting point for
unique NPC battles.

---

## 5. Checklist

- [ ] **Owner:** enable VRM4U in `BS_GodFile.uproject` (`SKIP_PROTECTION=1`), batched with the pending MelodiaWardrobe/BOM decision
- [ ] Restart editor; confirm VRM4U loads without a module error
- [ ] Create `Content/NPCs/vrm_registry.json` with author + license + attribution for the three models
- [ ] Decide whether to track the three `.vrm` files (~62 MB) — licensing is the gate, not size
- [ ] Run the placeholder scripts against `MelodiaIntegrationMap`, position by hand, copy transforms back into `NPCS`
- [ ] Import `SD_02_PetalPriestess` only, to `/Game/NPCs/Imported/SakuraDreamer/`
- [ ] Repoint its materials at `MM_Melodia_NPC_MToon` / `MPC_NPC_Global`
- [ ] Populate `battle_enemy_id` per placeholder before any further VRM work
