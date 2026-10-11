# Universal Wardrobe — Slot Contract Design — 2026-10-08

Read-only audit against the live editor (GUI PID 21012, Monolith :9316). No asset mutated.
Receipt: `Saved/Audit/MelusinaKineFXAudit_20261008/slotfacts_live.json` (machine-readable) and
`wardrobe_slot_audit.py` (the script that produced it).

## 1. The gap, stated precisely

- `EMelodiaWardrobeSlot` exists (`MelodiaNarrativeTypes.h:94-110`): Body, Hat, Gloves, Shawl,
  Trail, HairCharm, Shirt, Skirt, Boots, Accessories. It is **serialized into save records** and
  must never be renumbered — it is a real contract.
- **The slot vocabulary has no runtime owner in `Source/`.** (CORRECTED in §10: the real owner is
  the enabled `Plugins/MelodiaWardrobe` plugin, which this audit's first pass missed by searching
  only `Source/BS_GodFile`.)
- The pawn `BP_MelusinaJRPGCharacter` has exactly four CDO components: `CollisionCylinder`,
  `Arrow`, `CharMoveComp`, `CharacterMesh0` (= `SK_Melusina_V2_Body`). No hat, no gloves, no leader.
- `SK_Melusina_V2_Hat` **is referenced by** the pawn BP (as a catalog mesh) but is never placed —
  which is why it floats. This is not a hat bug; it is the missing wardrobe runtime.

## 2. Verified skeleton facts (the part only a live read can give)

| slot | mesh | skeleton | bones | head_x | hand_l/r | foot_l/r | c_kilt_master_x | hair_root |
|---|---|---|---:|---|---|---|---|---|
| Body | SK_Melusina_V2_Body | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| Hat | SK_Melusina_V2_Hat | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| Shirt | SK_Melusina_V2_Shirt | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| Skirt | SK_Melusina_V2_Skirt | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| Boots | SK_Melusina_V2_Boots | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| Accessories | SK_Melusina_V2_Accessories | SK_Melusina_Skeleton | 465 | yes | yes | yes | yes | no |
| HairCharm | SK_MelusinaHair | SK_Melusina_Hair_Skeleton | 148 | no | no | no | no | **yes** |

**Two decisive consequences:**

1. **The `MelodiaHairComponent` attach pattern applies verbatim to the hat and every garment.**
   All six garment meshes share the full 465-bone skeleton and all contain `head_x`. The existing
   warning (CURRENT_STATE line 237) that "the hat's own 434-bone mesh lacks `head_x`" is **not true
   of the shipped `SK_Melusina_V2_Hat`** — it is either stale or refers to a proxy candidate. The
   attach recipe (attach to `head_x`, `SetRelativeTransform(bind-pose inverse)`, `leader = null`,
   match custom depth/stencil) is directly reusable.
2. **Hair is the exception, not the rule.** `SK_MelusinaHair` uses its **own 148-bone skeleton**
   (`SK_Melusina_Hair_Skeleton`) with `hair_root` and no body bones at all. It must stay a separate
   component with its own AnimBP (`ABP_Melusina_WaterHair`) — it cannot be folded into a
   body-relative slot without breaking Kawaii and the music-sway external force.

## 3. The slot contract

Each slot needs: mesh, attach bone, offset, and whether to match body custom depth. Proposed
defaults, derived from the verified bone facts:

| slot | attach bone | offset | match body custom depth | notes |
|---|---|---|---|---|
| Body | — (is the body) | — | n/a | `CharacterMesh0`, the pose leader |
| Hat | `head_x` | bind-pose inverse | yes | garment-space geometry; needs the offset cancel |
| Gloves | `hand_l` / `hand_r` | bind-pose inverse | yes | mirrored pair — two components per slot instance |
| Shawl | `spine_03_x` | bind-pose inverse | yes | upper-back drape |
| Trail | `spine_01_x` | bind-pose inverse | yes | follows torso, longest settle |
| HairCharm | `hair_root` (hair skeleton) | none | yes | **separate skeleton — own AnimBP, do not merge** |
| Shirt | `spine_01_x` | bind-pose inverse | yes | torso garment |
| Skirt | `c_kilt_master_x` | bind-pose inverse | yes | already the Kawaii chain root in the ABP |
| Boots | `foot_l` / `foot_r` | bind-pose inverse | yes | ground-contact garment; interacts with FootPlacement |
| Accessories | per-asset | per-asset | yes | heterogeneous; needs a per-asset attach table |

Mirrored slots (Gloves, Boots) are one logical slot with two physical components. The subsystem
should key on slot and carry an optional side suffix.

## 4. The one hard robustness rule

`GetBoneIndex` must be guarded with `INDEX_NONE` on every attach. Even though all six shipped
garments contain `head_x`, the wardrobe is meant to accept **future** garments and the DollKit
segment meshes (`MEL_seg_*`) show the project already produces partial meshes. A mesh missing its
requested bone must fall back to `NAME_None` (mesh root) and log
`MELODIA_WARDROBE_MISSING_BONE` with the mesh and bone names — never crash, never silently attach
to the wrong place.

## 5. What this design deliberately does not do

- Does not renumber or reorder `EMelodiaWardrobeSlot` (save-record compatibility).
- Does not merge Hair into a body-relative slot (separate skeleton + AnimBP).
- Does not touch the ABP, the frozen skeleton, or any `.uasset`.
- Does not introduce a second cloth solver — Kawaii and `M_Master_Nikki` remain the owners.

## 7. Disk-side slot coverage (filename inventory — 2026-10-08)

`Saved/Audit/MelusinaKineFXAudit_20261008/garment_slot_inventory.json` (+ the script that
produced it). Filenames only; bone facts come from §2's live read.

| slot | count | assets |
|---|---:|---|
| Body | 1 | SK_Melusina_V2_Body |
| Hat | 1 | SK_Melusina_V2_Hat |
| Shirt | 1 | SK_Melusina_V2_Shirt |
| Skirt | 3 | SK_Melusina_V2_Skirt, _R1_SmoothChains, _R2_SmoothChains |
| Boots | 1 | SK_Melusina_V2_Boots |
| Accessories | 2 | SK_Melusina_V2_Accessories, SK_Accessories_HandSleeveFit |
| HairCharm | 2 | SK_MelusinaHair, SK_Melusina_FIXED_Hair |
| **Gloves** | **0** | **EMPTY** |
| **Shawl** | **0** | **EMPTY** |
| **Trail** | **0** | **EMPTY** |

**Three of ten slots have no garment on disk at all.** So the universal wardrobe is not merely
missing its runtime — it is also missing two-thirds of its content. The subsystem can be built and
proven on Hat/Skirt/Boots today, but Gloves, Shawl and Trail need assets authored before those
slots mean anything. That is authoring work, not engineering.

Two meshes matched no slot keyword and need a human ruling: `SK_ShorewakeDress_Magical` and
`SK_ShorewakeDress_Melusina465` — almost certainly **Body** replacements (a full dress), but
"dress" is not in the keyword map, so they were left unmapped rather than guessed. Also note
`SK_Regalia_v4_Earrings` was excluded by the `regalia` filter but is plausibly an **Accessories**
garment.

## 8. The N-lens gate, and its honest limits

`Tools/animation/verify_nlens.py` + `test_verify_nlens.py` (**16 tests, all passing**) enforce the
N2/N3/N5/N9 rules from `nikki_regions`. It is the checker the §4 robustness rule needed.

| rule | what it asserts | measurable from |
|---|---|---|
| N5 | mirror mean-distance vs a **mesh-adaptive** gate, across the mesh's **own** midplane (not world x=0) | point cloud |
| N9 | no sim chain root rests inside the face volume; face anatomy (`head_x`, `spine_03_x`, …) is **exempt** so the rule is not self-contradictory | bone transforms — **live-capable** |
| N2 | every *cloth* region has a bound chain (`face_clear`/`silhouette` are lens props, not cloth regions) | ABP binding table |
| N3 | garment layers sit inside the body bounds | layer geometry |

**Honest limit, by design:** the live editor exposes bone transforms, not vertex soup. So in
`--live` mode only **N9** is computed; N2/N3/N5 report `NOT MEASURABLE` with the reason rather than
being silently skipped or faked. A gate that reports "pass" because it could not measure is worse
than no gate. N5/N3 need a point-cloud source (Houdini/Blender export or a mesh-python read) to
become live.

Negative control verified: a chain placed at `head_x`'s own position **is** flagged by N9, and the
anatomy exemption does not hide it. The gate bites.

## 10. CORRECTION — the wardrobe runtime ALREADY EXISTS (2026-10-08, found by the build)

**My earlier conclusion that "no `UMelodiaWardrobeSubsystem` exists anywhere in `Source/`" was WRONG,
and the build proved it.** `Plugins/MelodiaWardrobe/` is an **enabled, compiled plugin** with its own
`UMelodiaWardrobeSubsystem`, plus `UMelodiaWardrobeComponent`, `UMelodiaWardrobeGachaSubsystem`,
`UMelodiaMagicalTransformComponent`, `UMelodiaResonantPassageComponent`, automation tests, and an
authored cosmetic catalog (`Content/Catalog/DA_MelodiaCosmeticCatalog.uasset`) with hat/dress/boot
JSON drafts. It appears in `BS_GodFile.uproject` as `{'Name': 'MelodiaWardrobe', 'Enabled': True}`.

**How the miss happened:** the search was scoped to `Source/BS_GodFile` and the pattern
`UMelodiaWardrobeSubsystem|WardrobeSubsystem` — which does not match a *plugin* path. A repo-wide
`grep -rln` would have found it. **Lesson: search plugin trees too; `Plugins/*/Source/**` is a
first-class location in this project.** AGENTS.md's "check Monolith's own namespace before
concluding a capability is impossible" is the same rule applied to a different tree.

A duplicate `Source/BS_GodFile/MelodiaIntegration/MelodiaWardrobeSubsystem.{h,cpp}` was authored in
good faith on the bad premise, then **removed** once the collision surfaced as a UHT error
(`Two headers with the same name is not allowed`). No plugin file was touched.

**The genuinely valuable finding survives the correction:** the existing
`MelodiaWardrobeComponent.cpp:239` calls `SetLeaderPoseComponent(BodyMesh)` but the plugin contains
**no `GetBoneIndex` / `INDEX_NONE` guard anywhere**. So a garment mesh lacking its requested attach
bone is unguarded — the exact crash class §4 warns about, still open, in code that already exists.
That patch belongs on the *existing* component, not on a duplicate subsystem. It is now the
highest-value next action (see §9).

Slot-coverage findings in §7 stand unchanged (they were a disk filename scan, not a source search).

## 11. Next step

`MelodiaWardrobeSubsystem.{h,cpp}` skeleton implementing §3/§4, then a runtime proof that the Hat
slot lands on her head through the subsystem — at which point the hat fix stops being a special
case and becomes slot `Hat` passing through the universal path.

> **SUPERSEDED — see §10.** The runtime already exists as the enabled `Plugins/MelodiaWardrobe`
> plugin; do not author a new subsystem. Patch the existing
> `MelodiaWardrobeComponent.cpp` with the §4 `INDEX_NONE` guard instead, then prove Hat through the
> plugin's own path.
