# PLAYBOOK — PetalCascade → LeafPile settle (Package B) — 2026-09-17

**Cascade:** `/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_PetalCascade`  
**Emitters:** `PetalLoop` (CLEAN_FIXA, SubUV off, 1×1) · `PetalPile` (CLEAN settle)  
**MIs:** `MI_NS_ChoralSheep_PetalLoop` · `MI_NS_ChoralSheep_PetalPile`  
**Reference settle:** `/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop` emitter `LeafPile`  
**LeafPile Fix A:** SubUVAnimation **off**; SubImageSize **2×2 kept** (`MI_Leaves` static atlas — variants, not flipbook scrub). Receipt: [`VFX_FIXA_LEAFPILE_2026-09-17.md`](VFX_FIXA_LEAFPILE_2026-09-17.md)  
**Shared wind:** `User.BeatPulse` (ResonanceIntensity) drives wind / fall / settle energy.  
**Live this pass:** **BLOCKED_LIVE**.

Cross-links: [`PLAYBOOK_FLIPBOOK_FIXA.md`](PLAYBOOK_FLIPBOOK_FIXA.md) · BeatPulse companion bus · LeafPile Fix A receipt.

---

## Intent

Petals fall on the beat, then settle into a LeafPile-style resting carpet — soft shared BeatPulse wind, never double-scrub.

## Cascade → pile behavior

1. **PetalLoop** — airborne cascade; spawn / fall / flutter × BeatPulse.
2. **PetalPile** — ground settle (kill velocity, floor align, long lifetime / sleep). Mirror LeafPileLoop resting density, not its leaf atlas.
3. On BeatPulse peaks: short wind gust so settled petals flutter then re-settle — same curve family as LeafPileLoop wind when that NS is BeatPulse-wired.

## LeafPile reference (do not break Fix A)

| Pin | `NS_Melodia_LeafPileLoop` / `LeafPile` |
|---|---|
| SubUVAnimation | **enabled=false** |
| SubImageSize | **2×2 kept** (`MI_Leaves` SubUV Columns/Rows=2) |
| Role | Settle / pile density + wind response template |

PetalLoop stays **1×1 + SubUV off**. Do **not** copy LeafPile’s 2×2 onto PetalLoop.

## Shared BeatPulse wind

```text
User.BeatPulse (0–1)
  → wind strength / lateral force on PetalLoop + PetalPile
  → optional same curve on NS_Melodia_LeafPileLoop when wired
```

BP already sets BeatPulse on PetalCascade (companion Tick). LeafPileLoop BeatPulse is **optional env follow-up** — document only unless live session includes it.

## Live checklist

1. Read PetalCascade + LeafPileLoop pins (confirm CLEAN_FIXA).
2. Tune cascade→settle; wind × BeatPulse.
3. Verify PetalLoop SubUV off / 1×1; LeafPile 2×2 / SubUV off.
4. Dirty → owner Ctrl+S.

### Intended dirty list

- `NS_ChoralSheep_PetalCascade`
- `NS_Melodia_LeafPileLoop` only if wind/BeatPulse params actually edited

## Quarantine

Stub/TEMP/Test petal NS: docs quarantine only unless already labeled.

## Deferred

MotionTrails, FluidSplash. Do not reopen FluidSplash polish (closeout handoff).

## Acceptance

- [ ] Cascade settles to pile-like carpet
- [ ] Shared BeatPulse wind readable in PIE
- [ ] Fix A: PetalLoop 1×1 SubUV off; LeafPile 2×2 SubUV off
- [ ] Owner Ctrl+S
