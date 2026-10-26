# Les Emmaillotés — The Swaddled

**Editorial ID (not runtime):** `creature.faraway_mother.les_emmaillotes`  
**Region:** Faraway Mother (P1), in fold hollows beside resonance seams  
**Canon identity:** **CANON — APPROVED DESIGN**, owner approval confirmed 2026-10-26  
**Bear-like exterior:** **VISUAL CANDIDATE — owner requested documentation/research; final substitution not explicitly locked**  
**Production status:** DOCUMENTED DESIGN ONLY; no rig, UE encounter, or PIE success verified here.

> **One-sentence identity:** Little swaddled beings that cannot bear to come undone; Melusina answers their disturbed music to help them hold themselves together.

## 1. Approval ledger — do not blur the boundary

### Canon: explicitly approved design (2026-10-26)

- **Name:** Les Emmaillotés (The Swaddled), original Melodia creature; **not** a purported historical French folklore species.
- **Region:** nested in Faraway Mother's fabric fold hollows near its F=0 resonance contours; the field relationship is a *placement intention*, subject to traversability and pipeline verification.
- **Silhouette / surface:** compact ivory/cream swaddled cocoon; crossed textile bindings, slight asymmetry, one off-centre knot and unfinished seam.
- **Emotional character:** tender, eerie, vulnerable, distressed rather than hostile. They are comforted, never defeated or killed by the encounter.
- **Unwrapping:** after **two bars off-beat**, bindings loosen; something soft and unfinished is exposed within a burgundy / bruised-rose, velvet-like living interior. The earlier approved inner-form direction was a **curled, ambiguous fetal-like silhouette rather than a literal human infant**, with deliberately nonrealistic anatomy.
- **Resolution:** the established **four-beat lullaby** calms and re-swaddles them; cloth returns, a warm-gold thread can subtly confirm comfort.
- **States:** Le Sommeil (rest), L'Éveil / L'Effilochage (unwrapping/distress), Le Réconfort (comfort/rest). Three readable states, one creature family, one interaction.
- **Architecture/scope:** musical reaction uses already-owned Melodia signals; no second rhythm system, no attack AI, no extra species or doll roster.

### Leading visual candidate: “The Unstitched Bear” (discussed 2026-10-26)

This is **not yet a final replacement of the approved inner silhouette**. The user requested deeper research, a turnaround, and documentation; a bear-form visual direction emerged, but owner did not separately say “lock bear form.”

- **Proposed outer body:** antique-bear-like *living textile organism*, not a possessed toy or literal doll. Warm ivory mohair, understated embroidered muzzle, small closely spaced eyes, oversized unequal ears, asymmetric little paws, a single faded pink ribbon; swaddling covers most of the body in rest.
- **Proposed signature action:** when its tummy seam begins to open, its tiny paws desperately hold the edges together. It trembles and hums; it **does not attack**.
- **Proposed interior:** thick burgundy/crimson velvet folds like living tissue, with delicate golden structural stitches. This is the creature's own injured material, **not** cotton stuffing, a realistic anatomical wound, or a separate creature.
- **Proposed repair:** threads draw the opening together while Melusina plays; it briefly hugs its belly, ears lower, then falls asleep. Visually echoes larger wounds in Faraway Mother's landscape.
- **Proposed art simplification:** reduce unnecessary lace, bows and filigree; prioritize mohair, eye/ear expression, wound silhouette and threads. No obvious button joints or plastic toy hardware.
- **Candidate scale target:** about 45–60 cm in rest; validate to Melusina/terrain comparison; not canon measurement.
- **Working epithet only:** “The Unstitched Bear”; **species display name remains Les Emmaillotés**.

**Decision required:** approve bear outer anatomy as permanent, choose whether it supersedes or merely obscures the earlier curled inner-form reading, and approve the final three-state turnaround. Until then both the canon core and visual candidate are recorded, never silently merged.

## 2. Visual grammar and material hierarchy

| Layer | Read at distance | Material target | Meaning |
|---|---|---|---|
| Outer mass | Single compact, slightly pear-shaped swaddled form | worn ivory linen/muslin; possible mohair face/ears if bear direction approved | protective embrace / sleep |
| Bindings | Two diagonal bands, off-centre knot, one trailing edge | cream embroidered textile, restrained dusty rose ribbon | safety that may become restraint |
| Inner reveal | One concentrated central opening, not a full disintegration | burgundy / garnet velvet, blush folded membranes; stylized, nonanatomical | wounded cohesion |
| Repair motif | A few taut curves following the seam | muted warm-gold silk thread / stitching | attempts to remain whole |
| Expression | Ears / eyelids / uneven paws / trembling body, not teeth | soft pile or fine textile stitch work | fear, vulnerability, relief |

**Do not:** render a literal realistic human baby or anatomical gore, produce a possessed-doll army, default to a monster attack, swap in sharp teeth/evil glowing eyes, make the teddy a standard store-bought toy, or reinterpret generated-sheet decorative details as locked specifications.

## 3. Three-state animation brief

**A — Le Sommeil / Sleep:** compact swaddling; subtle breath; faint muffled humming and tension pulse. In bear candidate, only ears/face peek out.

**B — L'Éveil / L'Effilochage / Distress:** after two off-beat bars, ribbons pull loose and belly seam parts; burgundy velvet interior revealed. In bear candidate, paw reach/hold-together is the *primary emotional action*. Keep face readable; no lunging, no attack. The sound grows more exposed and dissonant.

**C — Le Réconfort / Comfort:** correct lullaby triggers thread draw-in / re-wrap; soft relief and self-hug before sleep. Restore state predictably. Do not author a separate destroyed/dead phase.

These are **three presentation states**, not three gameplay systems or three independent meshes. Prefer a shared character body and authored transition clips, with pre-baked cloth motion / shape keys / limited bones as suits the current pipeline.

## 4. Musical encounter and six-beat reconciliation

- Existing environmental phrase context: Faraway Mother's **six-beat bars**.
- The approved response is the **four-beat lullaby**. Working interpretation: **four notes inside an existing six-pulse phrase**, leaving space for breath. Example candidate accents on pulses 1, 2, 4, 5; this rhythm is **not canonized** without listening/gameplay tests.
- Distress trigger: two off-beat bars; no attack damage.
- Comfort response: one accepted phrase returns toward rest; no hidden alternate meter, new musical authority, or punishment loop.
- Audio identity: muffled, wool-filtered humming while bound; higher and more fragile voice + thread-tension timbre when unbound; warm, stable tone after the repair. Use existing audio-reactive/PhraseBus interfaces rather than inventing new services.
- “Two off-beat bars” and “four-beat lullaby” are **authored encounter intentions**, not verified implementation claims.

## 5. Placement and world-field relation

Faraway static field includes the signed `(3,5)` Chladni basis. Candidate F=0 hollows may organize resting placement. Evaluate in **world UV** and filter against existing collision, playable route, camera readability, and static field contracts. The wider seam band is not automatically safe traversable terrain.

See:
- [P1 resonance integration spec](../../Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md)
- [Fabric mountain build / signed-field and coordinate notes](../../Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md)
- [Faraway ecology roster](../Regions/FARAWAY_MOTHER.md)

**Do not overwrite** `Houdini/FarawayDrape.hip`, `FARAWAY_DRAPE_GRID`, `TENSION_MASK`, `Cymatic_BeatPulse`, or authored curvature/tension networks. Probe in a named experimental copy; offline bakes only where possible. UE remains encounter authority; TD presentation-only.

## 6. Research / visual provenance

This species is original fiction. Inspirations to research, not folklore proofs:
- Historical European/French swaddling: diagonal cloth bands, linen, lace, protective yet restrictive packaging. A prior research pass discussed Mucem's swaddled-child model: <https://mucem.org/notice/c/15360/>.
- Early mohair teddy construction: small eyes, long pile, stitched muzzle, irregular proportions; late-19th/early-20th-century bear references are **material/style inspiration**, not medieval Poitou folklore.
- Textile repair: *couching / point de Boulogne* motivates structural golden threads; this is a fantasy biological interpretation, not an authenticity claim.
- The generated Les Emmaillotés visual board from the design conversation is **exploration**; no artwork binary added to this commit. Its decorative motifs, size comparisons, and invented labels are not automatic canon.

## 7. Production envelope — one bounded creature

1. **Art approval gate:** 3-state paired reference; swaddled front/side/back; exposed front/3-quarter; one extreme close-up of interior repair; scale cue. Owner specifically approves the bear variant or returns to the approved ambiguous fetal-like interior.
2. **Single prototype:** one low-cost creature mesh/rig; one swaddling motion; one seam-open/close presentation; one audio motif. Use existing material-instance families and pre-baked animation in preference to live tearing simulation.
3. **Level stage:** one isolated actor in `LV_FarawayMother_Prototype`, placed at a valid field-adjacent fold and linked to already-supported musical input; no mass scatter or new PCG grammar until validated.
4. **PIE proof:** sleep -> off-beat -> unravel -> correct lull -> comfort -> sleep; visual and audio feedback, reset/retry, collision, camera, log clean, performance check. Verify no unintended damage and no duplicate interactions.
5. **Only after PIE:** consider optional placement repetitions and a future `Motif Creature` Compendium entry. Do not infer save semantics; follow existing progression and narrative flags.

**Done for this document:** canonical identity and proposed bear direction recorded, explicit contradictions managed, production slice bounded.  
**Not done:** bear final sign-off, concept-art approval, rig, UE spawn, live music integration, release proof.

## 8. Draft Compendium seed (NOT runtime registration)

- **Category:** Motif Creature
- **Proposed EntryId:** `creature.faraway_mother.les_emmaillotes` (editorial placeholder; never assume gameplay ID)
- **DisplayName:** Les Emmaillotés
- **Subtitle:** The Swaddled
- **Summary (draft):** Small wrapped beings resting where Faraway Mother's fabric folds become still. Discordant music loosens their bindings; a gentle lullaby helps them settle.
- **MusicalIdentity (draft):** Muffled lull hum; destabilizes after two off-beat bars; answers a four-note/beat lullaby within Faraway's existing phrase context.
- **Melusina FieldNote (draft, subject to voice review):** “I thought it wanted to frighten me. Then it tried to hold itself together. I sang more quietly after that.”
- **UnlockFlagId:** UNDECIDED — use a verified existing narrative flag only; do not create a new discovery ledger.
- **Artwork/VoiceNote:** No committed art, audio, or production asset yet.
