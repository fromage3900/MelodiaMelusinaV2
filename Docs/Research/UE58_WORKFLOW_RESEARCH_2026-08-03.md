# UE 5.8 Workflow Research — 2026-08-03

**Status:** Research brief. Reference only. No changes requested.
**Author:** Qwen-assisted research lane (local `qwen3:8b`).
**Companion:** `UE58_MaterialNotes.md` (engine quirks, append-only).

---

## 1. Substrate Material Workflow

Substrate (the new material model in UE 5.4+) replaces the legacy Shading Model
nodes with a single, composable `SubstrateMaterial` node. Key points for this project:

- **One node, many layers.** Instead of separate Simple/Default/ClearCoat/Cloth
  shading models, Substrate composes layers via a single node. Legacy
  `ConvertToSubstrate` bridges older materials.
- **This project's stance:** `M_Master_Toon_Universal` is the toon master. Review
  whether migrating to Substrate buys anything for the *stylized + Nikki* look vs.
  the risk of a large migration. Given the ship-first priority, **treat Substrate as
  a Post-ship experiment**, not a pre-ship requirement.
- **Watch:** Substrate changes dot/gloss/BBDF params; the `M_Master_Toon_Universal`
  family (916→1015 expressions, mostly gated) should be validated *before* any
  Substrate conversion, not after.

### Practical
- Keep the DBuffer/parallax/step-POM stack on the legacy path for now — it's proven.
- If experimenting, use `MI_Show_*` starter instances on a test sphere, never on
  ship levels.

---

## 2. PCG Optimization for Large Scatter

The project's biggest PCG friction is large instance counts (e.g. the 633k-spawn
`ZenForestTest` hang). Known-good patterns:

- **Verify positionally, never by instance count.** Three wrong conclusions this
  session came from trusting a count over a position.
- **`PCGVolumeSampler` emits zero project-wide**, blocking **40 graphs** — this is
  the single highest library unlock. Root-cause it before expanding scatter.
- **Avoid `PCGSpawnActor` in heavy graphs** — it hangs on World Partition external
  actors with `delete_actors_before_generation`. Use ISM/HISM for scatter.
- **Check for compensating scale first.** The 3200 m colonnade was a double
  correction (mesh scale + graph scale). ~49% of graphs spawn a broken-scale mesh.

### Practical
- Use ISM (Instanced Static Mesh) for dense scatter; reserve `PCGSpawnActor` for
  gameplay-relevant, sparse actors.
- Test actor-spawning graphs in a **light level first**, never `ZenForestTest`.
- Queue the `PCGVolumeSampler` diagnosis as a dedicated task (it's worth 40 graphs).

---

## 3. AI-Agent Automation Patterns for Headless UE

This project runs a multi-agent ecosystem (Cline, DeepSeek, Kiro, Qwen, etc.) over
the Unreal editor. The proven headless pattern:

```
UnrealEditor-Cmd <project> -unattended -nullrhi -run=pythonscript:script.py
```

- **Headless rule (critical):** **every** `UnrealEditor-Cmd` launch must include
  `-DisablePlugins=Monolith` alongside `-unattended` / `-nullrhi`. Monolith crashes
  at `UMonolithSettings::Get()` during plugin init even when disabled in `.uproject`.
- **Monolith MCP** (`localhost:9316`) is the live editor surface when the editor is
  open; it-is-unreal (`127.0.0.1:8088`) is down when the editor is closed (rebuild gate).
- **Never save `ZenForestTest`** — owner art sits dirty there.
- **Never open/save `MelodiaHairComponent.cpp`** (agent coordination rule).
- **No rebuild** until all merges are done and the editor is closed.

### Agent lane recommendation
- **Qwen (local)** is the right lane for: doc generation, orphaned `.pyc`
  reconstruction, pacing/skill DataAsset drafting, and read-only C++ review.
  It keeps the cloud models (DeepSeek/Kimi) free for single-owner authority.
- **DeepSeek (Rider, compiler in the loop)** handles mechanical, no-look decisions.
- **Kiro** owns Blueprint gameplay work (token pickup/HUD, battle UI).
- **Cline** is the project lead for architecture + authority decisions.

---

## 4. Known Project-Wide Blocker: `PCGVolumeSampler`

- **Symptom:** emits zero instances project-wide.
- **Impact:** blocks **40 graphs** — the single highest unlock in the PCG library.
- **Lead:** could be a coordinate-space or volume-extent issue; check whether the
  sampler's volume is actually overlapping the graph's surface, and whether it's
  World Space vs Local Space.
- **Discipline:** verify positionally (a single placed instance in the right place),
  not by raw count. Fix it in a light level, then re-run the PCG library audit.

---

## Summary of recommended next actions

1. **Tag the placed `BP_InteractionBattle`** in KaleidoNave with `melodia_smoke_encounter`
   (unblocks the PIE battle — see `Content/Python/tag_kaleido_encounter.py`).
2. **Fix QuillScript rendering** (Cline's diagnostic logs are live) — unblocks all
   narrative content.
3. **Run PIE §4** (save/load/restart) — the gating foundation; unlocks Continue/Load.
4. **Queue `PCGVolumeSampler` diagnosis** as a dedicated task (worth 40 graphs).
5. Keep Substrate **Post-ship**; validate the toon master before any migration.

---

*End of research brief.*
