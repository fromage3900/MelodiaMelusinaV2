# Phone Artist Bridge — handoff for next agent (2026-08-11)

**Audience:** next Cursor mobile / cloud agent. Read this before inventing process.
**Owner:** artist shipping Melodia (turn-based rhythm JRPG + portfolio). Not an AI-sandbox customer.
**Repo:** `github.com/fromage3900/MelodiaMelusinaV2` (`BS_GodFile` UE 5.8).

---

## What the owner actually wants

One continuous studio from phone + laptop + PC:

1. **Capture while out** — phone photos, scans, ZBrush iPad exports, Grok notes, research dumps.
2. **Agent consolidates into git** — research → short notes in repo; named code tasks → real PRs.
3. **PC/laptop stays productive** — pull, build, PIE, Blender, Rokoko, art. No overlapping writers.
4. **No ops theater** — do not invent PhoneOps frameworks, ranking tables, or “platform redesigns.” Ship the ask.

They are **not** asking phone Cursor to drive Blender, Unreal, or Rokoko directly.
They **are** asking phone Cursor to be the bridge: Drive/Grok/camera → GitHub → PC.

---

## Hard truths (stop rediscovering these)

| Fact | Implication |
|---|---|
| Phone Cursor runs **cloud agents** on a Linux VM + git. | Code/docs/PRs yes. Local UE/Blender/Rokoko no (unless Remote Control — below). |
| GitHub from phone **already works**. | Proof: PR `#2` wired `RestorePartyAfterBattle` on `cursor/restore-party-callsite-0f00`. |
| Google Drive / Gmail / Calendar MCP = **`needsAuth`** as of this handoff. | Until owner connects them (Cursor Settings → MCP, or agents dashboard MCP), agents cannot pull Drive files. |
| Bulk `Content/` art is mostly gitignored; binaries use LFS. | Prefer Drive / drop folders for heavy scans & FBX; git for code + thin research notes. |
| Local jcode / OpenCode / UE on Windows must not fight a phone cloud agent on the same paths. | One writer. Phone steers or does repo-only; PC owns editor/art. |

---

## Cursor phone capabilities that match this artist (researched 2026-08-11)

Official iOS docs: [Cursor for iOS](https://cursor.com/docs/cloud-agent/mobile) (beta). Same backend as cursor.com/agents.

**Use these — they are the “cool stuff” that is real:**

1. **Continue the PC thread (Remote Control)**  
   On desktop Cursor ≥ 3.9.8: `/remote-control` in the Agents Window. Agent loop moves to cloud; **tools still run on the PC** (files, terminal, local setup). Phone picks up the same session. Computer must stay awake/online. This is the answer to “continue chats from what’s already on my PC.”

2. **Design Mode + camera / photos**  
   Attach photos, camera shots, or files; point/draw for visual direction. Ideal outdoors: scan → attach → “turn this into a UI mock / mood ref / task list in repo.”

3. **MCP per run**  
   Pick MCP servers at launch (including Google Drive once authorized). Manage servers on web dashboard; select on mobile.

4. **PR review / merge from phone**  
   Full diffs, checks, merge. Good for landing agent PRs without opening the laptop IDE.

5. **Voice + long-running agents**  
   Dictate a task, lock phone, get push when done.

**Do not promise:** phone Cursor reading ZBrush/Rokoko app state, Live Link to Blender, or editing the UE Content folder without Remote Control / PC awake.

---

## When Google Drive is enabled — do this first

Owner will connect **Google Drive MCP**, then start a new chat with this handoff.

### Ready protocol (agent checklist)

1. Confirm Drive MCP is ready (`GetMcpTools` / server status ≠ `needsAuth`).
2. Ask only if needed: Drive folder link or folder name (default assumption: a Melodia / Melusina / scans inbox — do not invent a second taxonomy).
3. List recent files (photos, PDFs, notes, FBX/OBJ if present).
4. **Consolidate, don’t archive spam:**
   - Research / mood / reference → one short markdown under `Docs/` or `Docs/PhoneOps/` only if it earns a place; prefer `Docs/Handoffs/` or a single `Docs/Research/` note the owner named.
   - Actionable game/code work → implement or open a focused PR (one lane).
   - Heavy binaries (scans, FBX) → **do not force into git** unless owner says so; leave paths/notes (“in Drive: … → PC drop: `Imports/...`”) and optionally mirror to a documented drop folder when PC Remote Control is available.
5. Open/update a draft PR. Tell the owner in ≤5 bullets what landed.
6. Stop. No bonus frameworks.

### Example kick prompts (owner can paste)

```text
Read Docs/Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md.
Drive is connected. Pull my Melodia scan/research folder, consolidate into the repo, open one draft PR. No process docs. No UE/Blender from cloud unless Remote Control is on.
```

```text
Same handoff. One code task only: <name the bug or file>. PR when done. Do not touch Sakura / Content/_PROJECT/.
```

```text
Remote Control is on from my PC. Continue the open local session: <what to do on the machine>.
```

---

## Cool paths worth wiring (not science fiction)

Prioritize what helps Melodia **this month**. Owner is an artist; hero meshes stay ZBrush/human.

### A. Mockups from phone (available now / soon)

| Path | How | Good for |
|---|---|---|
| Design Mode + attached photo | Native Cursor iOS | UI/HUD direction, “make it look like this” |
| `GenerateImage` in agent | Cloud agent image tool when enabled | Quick concept / mood boards committed under `Docs/` or artifacts |
| HTML/CSS mock in repo | Agent writes a single static page under `wix/` or `Docs/` | Rhythm HUD / menu layout tests without UE |
| Grok research → agent | Paste or Drive-drop notes | Consolidate into one truth note + code todos |

### B. 3D without pretending phone = ZBrush

| Path | Reality | Melodia fit |
|---|---|---|
| **Math / procedural blockout** | Project already has GeometryScript / Monolith mesh actions + ornament procedural recipes (`Docs/AI_ORCHESTRATION_HANDOFFS_2026-07-17.md`). Needs **PC UE + Monolith**, ideally via Remote Control. | Prop shells, kitbash blockers, SDF/math art — not hero Melusina. |
| **Photo → 3D (AI)** | Meshy / Tripo / Rodin / TRELLIS-2 / Hunyuan3D: image→GLB/OBJ/FBX. Open pipelines: Clay, Mymeshy (MCP-capable), Meshii. | Ref props from outdoor scans. Always human-pass in ZBrush/Blender before game. |
| **Photogrammetry** | Polycam / KIRI / Luma on phone → OBJ/FBX to Drive → PC import. | Environment reference, not final characters. |
| **Rokoko** | Phone/suit → Rokoko Studio / UE Live Link on PC. Repo doc: `Docs/ROKOKO_MELUSINA_MOCAP.md`. Inbox: `Imports/Mocap/Rokoko/Inbox/`. | Animation takes. Cursor only notes + import scripts. |

**Giving the agent “the tools” (owner + next agent):**

1. Connect Google Drive MCP (blocker today).
2. Prefer **Remote Control** when the task needs the Windows box (UE, Blender, local GPU image→3D).
3. Optional later: Meshy/Tripo API key as a cloud secret, or local Mymeshy MCP on PC — only if owner asks; do not build a platform first.
4. Keep hero sculpt authority on ZBrush iPad/desktop; agents do blockout, import glue, research, code.

### C. Game code from phone (proven)

Lane already used: ship C++/Python/docs PRs while owner arts elsewhere.  
Next gameplay queue stays in `AGENTS.md` / `Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md` — do the named item, not a tour.

Open related PR: https://github.com/fromage3900/MelodiaMelusinaV2/pull/2 (`RestorePartyAfterBattle` call site).

---

## Anti-patterns (owner fatigue triggers)

- Re-explaining that phone can’t open Rokoko/ZBrush internals.
- New PhoneOps “control plane” docs when a single handoff + PR would do.
- Starting a second agent that overlaps jcode / local Cursor / UE.
- Claiming gates certified without ledger rows / real input (see `AGENTS.md` evidence standard).
- Dumping multi‑GB art into git “because Drive worked.”

---

## Success check for the next session

- [ ] Drive MCP authorized and used once (list → consolidate → PR), **or** owner pasted research and agent consolidated without Drive.
- [ ] Owner knows Remote Control exists for “same PC chat from phone.”
- [ ] At most one focused PR; art/binary path documented, not force-pushed.
- [ ] No new process layer unless owner asked for it by name.

---

## One-liner for the agent system prompt

> You are the mobile bridge for an artist’s Melodia project: pull capture/research (Drive when live), consolidate into git, ship real code PRs, never fake UE/Blender/Rokoko control from the cloud, never invent ops frameworks, stop when the ask is done.
