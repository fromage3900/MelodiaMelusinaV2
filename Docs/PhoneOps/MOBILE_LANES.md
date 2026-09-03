# Mobile lanes — phone vs PC (2026-08-11)

How to work MelodiaMelusinaV2 from iOS / SuperGrok / Cursor cloud without fighting the UE box.

## Lane split

| Lane | Owns | Does not own |
|------|------|--------------|
| **Phone / cloud** | Docs, issues, Quill drafts, Polycam capture → Drive, PR review, Echo *doc* hygiene | Editor writes, LFS mesh pushes, Live Link sockets, PIE |
| **PC + editor** | One Unreal, port 9316, Monolith, import/intake, RT-001…007 | Parallel second editor |
| **PC + WSL/tmux** (planned) | Private Blink/SSH → WSL agent CLIs → Git; see [REMOTE_WSL_AGENT_STACK_2026-08-25.md](REMOTE_WSL_AGENT_STACK_2026-08-25.md) | Public SSH; auto-loops; cloud agents pretending to configure Windows |

## Connectors

| Tool | From phone/Grok | Good use |
|------|-----------------|----------|
| **GitHub** | Read usually; write needs contents:write | Docs PRs, issues per RT-* |
| **Google Drive** | Yes | `Melodia/Photogrammetry/YYYY-MM-DD/`, mood boards, offline PhoneOps copies |
| **Gmail / Voice** | Yes | Dictate PIE → markdown handoff |
| **Unreal Live Link** | **No** remote socket | Phone keeps subject/port notes; PC wires Epic Live Link / Rokoko |
| **Polycam** | Capture only | OBJ/USDZ → Drive → PC `Imports/Sculpt/Inbox` → ZBrush → UE (see mobile scan SOP) |

## Polycam (practical)

1. Scan small props (not Sakura heroes).
2. Export OBJ/USDZ.
3. Drive: `Melodia/Photogrammetry/YYYY-MM-DD/`.
4. PC: sync into `Imports/Sculpt/Inbox`, run `sculpt_intake_check.py`, import new `/Game/...` path only.
5. Full SOP: [`Docs/MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`](../MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md).

## Live Link / Rokoko

- **Preview:** Rokoko Studio → Epic Live Link → `SK_MocapSource` only.
- **Game clips:** FBX → `Imports/Mocap/Rokoko/Inbox` → `import_rokoko_mocap.py` → `RTG_Mocap_to_Melusina`.
- Blender Live Link `:9876` is mesh/env sync — different system.
- Detail: [`Docs/ROKOKO_MELUSINA_MOCAP.md`](../ROKOKO_MELUSINA_MOCAP.md).

## Creative on-the-go (high value)

1. Dictate PIE failures every session → `Docs/Handoffs/PIE_YYYY-MM-DD.md`
2. One GitHub issue per RT-*
3. Grief-hook lines in markdown for later `.qsc`
4. One-bar rhythm design on paper (after highway has data)
5. Opaque JRPG HUD reference screenshots → Drive
6. Polycam “orphan prop” kit for future scatter
7. Review env pack shortlist before buying kits
8. Voice check: “Did I only test one interaction today?”

## Agent paste briefs

**Docs only**

```text
You are on MelodiaMelusinaV2. Read Docs/PhoneOps/HIGHEST_LEVERAGE_NOW.md
and Docs/Handoffs/PIE_2026-08-11.md. Docs only. One PH-* only.
```

**PC editor free**

```text
You are on the UE workstation for MelodiaMelusinaV2. One editor. Port 9316 only.
Do RT-001 then stop. Evidence = viewport + log, not “node exists.”
```
