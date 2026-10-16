# Authoring Authority, Model Lanes, and Stable Ownership

Moved out of `AGENTS.md` on 2026-10-01 for the 32 KB agent-context budget. Text is
**verbatim** — this is binding policy, not commentary. `AGENTS.md` keeps a short
pointer plus the decision rule itself.

## Default decision rule - author content before changing architecture

Before changing architecture, ask:

> Can the requested experience be authored using the systems listed in
> `CURRENT_STATE.md` -> `PROVEN CREATIVE CAPABILITY SURFACE`?

If yes, author the content. Do not alter architecture. A boss, side quest, rhythm skill, cymatic
biome, wardrobe ability, and procedural setpiece are normally content/data authored through the
existing seams. Architecture work requires a demonstrated blocker recorded against the relevant
owner seam.

The surface already supports authoring boss battles, rhythm skills/attacks, side quests, encounters,
creature episodes, outfit abilities, and musical world puzzles without another gameplay framework.

The integrated rhythm-JRPG loop remains the **production authority spine until the owner-directed FLOW/SEQUENCE promotion gate passes**:

**Stable ownership - never rebuilt, wrapped, or competed with:**
- **QuillScript** is the narrative authoring authority. `UMelodiaNarrativeSubsystem` is the runtime
  bridge and owns authored narrative facts, consequences, checkpoints, and exactly-once progression
  transactions; it does not resolve stock combat.
- **TurnBased JRPG / Phoenix** owns party, turns, targeting, skills, action resolution, damage,
  inventory, terminal battle results, and stock gameplay save state.
- **Rhythm** executes on the selected JRPG action. Grade may affect the authoritative result, but
  rhythm does not create a second combat transaction or damage authority.
- **Wardrobe** owns owned/equipped fashion state and exposes the existing traversal, battle, rhythm,
  and Convergence capability hooks.
- **One writer per UI/audio surface.** `UMelodiaUIBridgeSubsystem` owns the Melodia UI surface;
  `UMelodiaAudioReactivePresentationSubsystem` owns the canonical audio palette. Cymatics reads
  that palette and its dedicated driver contract; it does not become a second audio writer.
- **MelodiaCore** is an integration/presentation layer, not a competing combat or save authority.
  Conversation2D remains excluded. The turn-based ARPG / ACFU hybrid is CANON (owner, 2026-10-11):
  ACF supplies the realtime FLOW action layer on the canonical pawn; see `CURRENT_STATE.md` "OWNER CANON".

**The four pillars converge onto those two layers.** Rhythm input rides *on top of* JRPG command
input - same Attack/Skill/Item/Flee decisions, timed. Wardrobe is a core pillar (outfits carry
presentation *and* gameplay meaning). UI has one writer per surface. World puzzle is music-as-key
and its Piano-to-Narrative edge has a scoped live-proven world-unlock path. Deeper route/package
proof remains separately tracked in `CURRENT_STATE.md`.

Shape: OMORI. Music-as-key: Zelda. Visual/wardrobe bar: Infinity Nikki.

Status and scope: [`CURRENT_STATE.md`](CURRENT_STATE.md).

**Model lanes:** pick a task class before writing (`triage|audit|code|cpp|mcp|playtest|author|
deep|review|orchestrator|vision|daemon|docs`, plus the production lanes `wardrobe_catalog|
beatmap_author|quill_author|asset_qa|anim_bindings|spout_beauty`). Router: `python Tools/model_router.py pick
<class> --detail`. Policy + local daemon models: [`Docs/Production/MODEL_LANES_2026-08-12.md`](Docs/Production/MODEL_LANES_2026-08-12.md).
Gameplay queue: [`CURRENT_STATE.md`](CURRENT_STATE.md) §4. The handoff files this line used to point
at were removed in the 2026-09-10 docs collapse.

| Class | Use for | Must not |
|---|---|---|
| `cpp` | MelodiaIntegration C++ | Rebuild JRPG in MelodiaCore |
| `mcp` | Monolith multi-step (one editor) | Second MCP surface on same graph |
| `playtest` | Real-input `runtime` gate | Probe-only ledger `pass` |
| `daemon` | Overnight local loops (Ollama) | `.uasset` writes / gate certification |
| `audit` | bp_sweep / static gates | Compensating flags for real defects |
| `wardrobe_catalog` | Outfit rows against the catalog contract | Invent slots or bypass `MelodiaWardrobeSubsystem` |
| `beatmap_author` | Rhythm beat maps | Make rhythm a second combat authority |
| `quill_author` | QuillScript dialogue + 7-verb notifications | Emit an unallowlisted id |
| `asset_qa` | art/credits/bp gates, triage | Fabricate a file path |
| `anim_bindings` | ABP state machine + pose binding checks | Write `.uasset` |
| `spout_beauty` | Live UE→TD lookdev via the canon Spout2 `UE_Beauty` sender | Second sender name / second beauty writer |

**Every lane must not:** build a fifth wardrobe track, a fourth rhythm path, a second HUD
writer, or a second beauty-feed sender. Converge onto the named owner. A new parallel implementation is a defect, not progress.

**UI/visual-artist work:** load `.claude/skills/melodia-ui-artist/SKILL.md` (the equivalent
`.agents/skills/melodia-ui-artist/SKILL.md` is also present) — it carries the
real token SSOT (`melodia-design-system/tokens.json`), the Quill dialogue WBP chain
(`Content/Melodia/UI/Quill/`, tracked), the `ui_style_audit.py` inventory flow, and the
editor-driven apply workflow. Do not hand-edit `.uasset`; `Content/Melodia/UI/Textures/` is
intentionally gitignored, do not track it.
