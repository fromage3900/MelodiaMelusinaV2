# Melodia skill / tooltip / motion authoring kit

**Status:** authoring contract / UI lookdev guidance  
**Date:** 2026-09-17  
**Scope:** content-first skill presentation, tooltip copy, motion grammar, agent execution guidance  
**Runtime authority:** unchanged

## Why this exists

The project can already compose new content around working narrative, rhythm, traversal, companion, UI, save, and world-response systems. Agents should not invent a new UI vocabulary or a new gameplay authority layer every time they author a skill, encounter, traversal verb, companion interaction, boss response, or side-quest reward.

This document defines one reusable content contract:

`semantic gameplay result -> authored skill data -> tooltip states -> motion/presentation -> evidence`

The UI and motion layers visualize existing semantics. They do **not** become authoritative for rhythm timing, grade, damage, traversal, save ownership, rewards, or other gameplay truth.

## Canonical content anchors already in the project

Established instrument verbs:

- **Sonic Scepter** — reveals hidden paths.
- **Phase Bell** — bends local time.
- **Crescendo Fan** — releases waves from soft to cataclysmic.

Established Choral Sheep authored interactions:

- **Graze**
- **Harmonize**
- **Guide**

Choral Sheep is currently defined as a non-combat exploration companion. Do not silently turn its interactions into combat abilities.

The UI-kit display names below (for example `Resonance Reveal`, `Held Moment`, `Crescendo Wave`) are **lookdev / authoring examples**, not new canonical runtime names unless a content owner explicitly promotes them.

## Figma source of truth for this pass

Editable file:

`https://www.figma.com/file/ewS0yt17hiWq2KXPa5RfCX?node-id=0:1&type=design`

Important frames:

- `01 — Compendium / Desktop` — original static production reference.
- `04 — Compendium / UI Lookdev v2` — non-destructive polished variant; Figma Motion timeline is live.
- `05 — Skills / Tooltips / Motion Authoring Kit` — canonical visual/content contract for skill authoring; Figma Motion timeline is live.

Reference reel supplied by the art owner on 2026-09-17: a Figma-built Honkai-style dimensional book / medallion interface. Preserve the **motion behavior** (layered assembly, radial depth, staggered rotation, bloom, resolve), not the franchise styling.

## Motion grammar

Use four beats rather than animating every layer simultaneously.

| Beat | Intent | Typical timing | Presentation |
| --- | --- | ---: | --- |
| **ASSEMBLE** | establish hierarchy | 0–240 ms | layers converge / panel enters |
| **BLOOM** | communicate selection or semantic success | 180–520 ms | core scale, glow, small overshoot |
| **ORBIT** | reveal system depth | 420–900 ms | radial pieces rotate / counter-rotate, secondary layers arrive |
| **RESOLVE** | return control to player | 760–1200 ms | tooltip lands, motion quiets, rests remain readable |

Motion priority:

1. position;
2. scale;
3. glow / opacity;
4. ornamental particles / secondary rings.

Do not animate all four categories at maximum strength together. The player must still read the underlying state.

### Recommended motion tokens

These are presentation tokens, not rhythm-game timing authority.

- `motion.enter.fast`: 0.18–0.28 s
- `motion.enter.panel`: 0.32–0.48 s
- `motion.bloom`: 0.36–0.56 s
- `motion.resolve`: 0.70–1.20 s total sequence
- selected-item overshoot: `1.08–1.18x`, then settle to `1.0x`
- translation entrance: `8–48 px`, depending on hierarchy
- selected glow: one strong focal bloom plus at most one secondary halo
- reduced-motion fallback: opacity + small translation only; no continuous orbit requirement

## Skill content contract

Every new player-facing skill / verb must define the following before an agent treats it as implementation-ready.

### Identity

- `skill_id`
- `display_name`
- `owner` (character / instrument / companion / encounter)
- `chapter_or_unlock_source`
- `role` (`combat`, `traversal`, `puzzle`, `companion`, `world_response`, or a deliberate combination)
- `status` (`concept`, `authored`, `runtime_proven`, `presentation_proven`)

### Gameplay semantics

- `semantic_result` — what actually changes in authoritative gameplay state
- `input_or_trigger`
- `rhythm_phrase_or_window` when applicable
- `target_rules`
- `cost_or_resource` when applicable
- `cooldown_or_reuse_rule` when applicable
- `persistence_expectation` — none, transient, checkpointed, or canonical-save-owned

### Player feedback

- `telegraph`
- `success_feedback`
- `miss_or_invalid_feedback`
- `active_feedback`
- `cooldown_feedback`
- `vfx_hooks`
- `sfx_hooks`
- `animation_hooks`

### UI copy

- `tooltip_short` — one sentence; what the player can do
- `tooltip_long` — at most 2–3 short sentences; condition + result + important constraint
- `tags` — small semantic chips, not lore paragraphs
- `icon_motif`
- `accent_family` — existing Melodia palette family; do not invent arbitrary colors per skill

### Proof

At minimum:

- PIE / runtime capture showing the semantic result;
- no Blueprint / accessed-none / material / Niagara errors caused by the content pass;
- tooltip / HUD state proof;
- save/reopen proof **only if** the semantic state is expected to persist.

## Tooltip anatomy

A skill tooltip should answer questions in this order:

1. **What is it?** — owner + skill display name.
2. **What does it let me do?** — short verb-driven summary.
3. **When can I use it?** — trigger / target / timing / resource.
4. **What happens on success?** — semantic gameplay result.
5. **What will I see / hear?** — telegraph and feedback, not implementation internals.
6. **What is its state right now?** — available, selected, active, cooldown, locked, invalid.

Do not expose internal class names or debugging language in player-facing tooltips.

### Required tooltip states

- `default`
- `focused`
- `selected`
- `active`
- `cooldown` (when relevant)
- `locked` (when relevant)
- `invalid_target` / `miss` (when relevant)
- `reduced_motion`

## Minimum visual asset pack per skill family

A new family should reuse these slots rather than invent a bespoke HUD every time:

- icon glyph;
- radial halo;
- telegraph ring;
- success burst;
- miss / invalid state;
- cooldown wedge or equivalent state mask;
- tooltip plate;
- input / pitch / instrument chips;
- optional resonance / Chladni ornament when driven by real musical semantics.

The asset may be generated as vector / material / Niagara / texture depending on the implementation, but the semantic slots stay consistent.

## Example content seeds

### Sonic Scepter

**Canonical verb:** reveal hidden paths.  
**Example display name:** `Resonance Reveal`.

A valid content pass might author a new hidden-route encounter, phrase, telegraph, route-reveal response, tooltip copy, and capture proof without changing the underlying world-key authority.

### Phase Bell

**Canonical verb:** bend local time.  
**Example display name:** `Held Moment`.

Agents may author puzzle / traversal situations around an already-defined time-bending capability. They must not invent a new time-authority subsystem merely to satisfy the tooltip.

### Crescendo Fan

**Canonical verb:** release waves from soft to cataclysmic.  
**Example display name:** `Crescendo Wave`.

Content should make intensity / target / world-response rules explicit before presentation work begins.

### Choral Sheep — Harmonize

**Canonical interaction:** `Harmonize`.  
**Owner:** Choral Sheep, non-combat exploration companion.

Existing project material already treats pitch class, Harmonize state, harmonic intensity, beat phase, resonance state, and world-response strength as meaningful visual drivers. New visual content should prefer those semantics over arbitrary looping VFX.

## Agent execution recipe

When asked to "make a new Melodia skill" or equivalent:

1. read the nearest canonical content / owner definition first;
2. identify the existing runtime authority that already owns the semantic result;
3. fill the skill content contract;
4. author the smallest new content slice around that authority;
5. use the Figma kit for tooltip hierarchy and motion grammar;
6. reuse existing Melodia UI tokens and presentation systems;
7. capture proof;
8. update content docs / ledgers without rewriting settled architecture.

### Stop conditions

Stop and ask / document a blocker instead of inventing architecture when:

- no runtime owner exists for the requested semantic result;
- the requested skill contradicts the owner's established role;
- persistence ownership is unclear for a state that must survive restart;
- the implementation requires touching unrelated production maps merely to prove the content concept;
- the agent cannot distinguish presentation data from authoritative gameplay state.

## Definition of done for this authoring kit

The kit is useful when an agent can receive a content prompt such as:

> "Author a Phase Bell traversal challenge with a readable tooltip and Melodia motion treatment."

…and can produce a bounded content implementation, presentation, and proof without responding by redesigning the core game architecture.
