# Canonical Melodia Project Pipeline

**Status:** CANONICAL CROSS-REPO ROUTING CONTRACT  
**Use this document for ownership and handoff boundaries only.**  
**For what is true now, open, blocked, or next: read `CURRENT_STATE.md`.**

## 1. Repository authority

| Lane | Canonical repository | Operational home | Owns |
|---|---|---|---|
| Game / Unreal / capstone | `fromage3900/MelodiaMelusinaV2` | `C:/EnvironmentPortfolio/BS_GodFile` | UE5.8 runtime, gameplay, maps, assets, C++/Blueprint contracts, capstone truth/evidence |
| Portfolio website | `fromage3900/my-site` | independent checkout | recruiter-facing pages, Three.js/browser presentation, deployment |
| TouchDesigner / AE | `fromage3900/MelodiaTouchDesigner` | `C:/MelodiaTouchDesigner` | TD show rig, concert visuals, replay/capture tooling, AE finishing |
| Historical umbrella | `fromage3900/EnvironmentPortfolio` | old root `C:/EnvironmentPortfolio/.git` only | archive/provenance only; never current authority |

`C:/EnvironmentPortfolio/` may remain a workspace container. Its retired root Git repository is not Melodia authority.

## 2. Truth and freshness rules

1. `CURRENT_STATE.md` is the only current status / priority / blocker / open-work document.
2. `main` is canonical durable game state after accepted integration.
3. Feature, workstation, recovery, and render branches are work/evidence lanes, not current project status.
4. Runtime claims require runtime evidence; repository structure alone proves source state only.
5. Dated handoffs, plans, receipts, scorecards, and session notes never override `CURRENT_STATE.md`, source, or newer evidence.
6. Do not create a new status/plan/handoff file. Current facts update `CURRENT_STATE.md`; durable rules update a contract/spec/runbook; session narrative belongs in PR/commit messages.

## 3. Game / Unreal lane

The game repo owns:

- QuillScript narrative/progression;
- JRPG combat and canonical save state;
- rhythm execution and gameplay interpretation;
- Wardrobe ownership/equip/traversal capability;
- Starskiff traversal;
- Convergence interpretation boundaries;
- environment, material, PCG, Houdini/Blender integration contracts;
- Choral Sheep runtime/companion state;
- capstone implementation evidence.

Detailed runtime ownership lives in `SYSTEM_MAP.md` and `DATA_FLOW.md`.

## 4. DCC / procedural authoring lane

Blender, Houdini, Geometry Nodes, texture tools, and procedural authoring produce content for the game; they do not create a parallel runtime authority.

```text
reference / design lock
  -> DCC / procedural authoring
  -> tracked source/spec/provenance
  -> export/import candidate
  -> UE validation
  -> runtime/render evidence
  -> main
```

Laptop-specific durable rules live in `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md` and `Docs/Production/BRANCH_WORKSTATION_POLICY.md`.

Large source binaries may live outside Git where appropriate, but promoted assets, scripts, manifests, and import contracts must resolve through the canonical game repo.

## 5. Animation / performance capture lane

The durable animation pipeline is:

```text
stable camera capture
  -> Cascadeur mocap / authored cleanup
  -> canonical Melusina skeleton/export contract
  -> Cascadeur Live Link or export
  -> UE5.8 evaluation
  -> captured evidence
```

Use the established Cascadeur/Melusina pipeline and performance-capture research as reference. Any statement about what is currently fixed, blocked, or next belongs in `CURRENT_STATE.md`, not here.

## 6. Choral Sheep / capstone lane

Durable authorities:

- visual reference entrypoint: `Docs/Art/VISUAL_REFERENCE_INDEX.md`;
- Sheep contract: `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`;
- capstone showcase thesis: Creature -> Motif -> Harmony -> World;
- current task/proof state: `CURRENT_STATE.md` only.

The approved Nikki-derived character material remains the Sheep visual-material authority; Chladni/cymatics is a presentation consumer layered through that path, not a replacement gameplay/material authority.

Do not reopen historical blockers or revive old execution plans merely because they contain unchecked boxes.

## 7. TouchDesigner / live-performance lane

Canonical repo: `fromage3900/MelodiaTouchDesigner`.

Interface boundary:

- camera/hand bridge -> OSC UDP `:7001` + Spout sender `MelodiaHandCam` where used;
- game <-> TD semantic/show-control lane -> UDP `:9000`;
- TD -> Blender auxiliary lane -> `:9001` where used;
- TD consumes game semantics and presentation data; it does not own gameplay/save/quest truth.

Durable integration contract: `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`.

After Effects remains downstream editorial/compositing, not gameplay/system authority.

## 8. Render / evidence lane

Evidence levels must remain explicit:

```text
SOURCE-BUILT
  -> LIVE-PROVEN
  -> RESTART-PROVEN
  -> PACKAGED-PROVEN
```

Do not promote a claim to a stronger level without matching evidence.

Typical machine roles:

- Humber lab -> primary interactive semester workstation;
- home Windows PC -> render/bake/long-job worker;
- ASUS Nitro -> auxiliary Blender/GN/DCC workstation.

Current deviations or temporary assignments belong in `CURRENT_STATE.md` or the active PR/task conversation, not this contract.

## 9. Website / recruiter lane

Canonical repo: `fromage3900/my-site`.

The website consumes approved proof; it never creates gameplay evidence or project truth.

```text
approved game / DCC / TD evidence
  -> curated site asset / manifest update
  -> site validation
  -> my-site/main
  -> deployed portfolio
```

Current freeze/polish status belongs in that repo's current-state/issue surface or the active task context, not in this cross-repo contract.

## 10. Cross-lane handoff

```text
GAME / DCC
authoritative state + assets + renders
        |
        v
TOUCHDESIGNER
performance interpretation + visual layers
        |
        v
AFTER EFFECTS
editorial / compositing / reel finishing
        |
        v
WEBSITE
curated recruiter-facing proof
```

Direction of authority is one-way for facts:

- TD may visualize game state but does not redefine it.
- AE may editorialize captures but does not redefine runtime state.
- website copy may summarize evidence but does not create evidence.

## 11. Branch classes

- `main` -> durable canonical game state.
- `collab/laptop/longterm` -> intentional laptop Blender/GN workstation source lane; never wholesale-merge/delete.
- recovery/salvage branches -> provenance sources; extract named reviewed work only.
- `render-queue` -> operational render infrastructure; not a gameplay/status authority.

Branch names and exact active refs may evolve. `CURRENT_STATE.md` and `BRANCH_WORKSTATION_POLICY.md` own the live interpretation.

## 12. Documentation routing

Use exactly one answer surface per question:

```text
What is true / next / blocked? -> CURRENT_STATE.md
How does runtime work?         -> SYSTEM_MAP.md / DATA_FLOW.md
How do repos/tools hand off?   -> this pipeline contract
How does a subsystem behave?   -> its durable contract/spec/runbook
What should it look like?      -> reference / visual bible
What did research find?        -> Docs/Research
What happened before?          -> Git history / HISTORICAL stub
```

Obsidian may be used as a local knowledge browser over these Markdown files, but Git files remain canonical and Obsidian must not introduce a second task/status system. See `Docs/Production/AGENTIC_STUDIO_OPERATING_MODEL.md`.
