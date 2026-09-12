# Wardrobe C++ rebuild + gameplay wiring — session close 2026-08-15

**State:** the separated V2 mesh pipeline works end to end. Seven wardrobe C++ fixes are
committed and contract-tested but have **never been compiled** — the editor owned the
checkout all session. This is the prep so the rebuild is one command.

---

## 1. The rebuild

Editor and all `UnrealEditor-Cmd` processes must be **closed**. Verify first:

```
python Tools/melodia_rebuild_preflight.py
```

Proceed only on `safe_to_compile: true`. Do not infer success from process absence, and
do not terminate processes to force it.

```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" -NoUBA -MaxParallelActions=4 -Wait -NoProfiling
```

Expect these to relink:
- `Plugins/MelodiaWardrobe/Binaries/Win64/UnrealEditor-MelodiaWardrobe.dll`
- `Binaries/Win64/UnrealEditor-BS_GodFile.dll`

Record the **exit code and DLL timestamps**, not intent. Last known-good build predates
all seven changes (`2026-08-15T03:41:23Z`).

### What the build covers

| Fix | Why it matters |
|---|---|
| Catalog-first, fail-closed grant/equip (`FindGrantableRecord`, reasons `no_catalog` / `unknown_id` / `unauthored_mesh`) | `GrantCosmetic` wrote to the canonical save record with **zero** validation. An unknown id became a permanent unresolvable entry. |
| Broadcast the cosmetic's real slot | Was hardcoded `EMelodiaWardrobeSlot::Body`; every hat grant read as a body change. |
| `AddInstanceComponent`, collision off, mesh set **before** `SetLeaderPoseComponent` | Garment components weren't in the actor's instance list, carried default query+physics collision, and bound leader pose to an empty component. |
| `IsGarmentSkeletonCompatible` | Leader-pose sharing silently deforms a foreign skeleton rather than erroring. |
| `ApplyWardrobeState()` | `BeginPlay` was the only restore path; a mid-session load left the previous save's garments on. |
| Ownership as durable idempotency | `ConsumedGrantIds` is runtime-only. A duplicate gacha pull read as a new acquisition. |
| Catalog cached in a rooted `UPROPERTY` | `StaticLoadObject` per call, unrooted and collectable, on the traversal query path. |

Offline evidence: `Tools/test_melodia_wardrobe_transaction_contract.py` 45/45,
negative-tested. Suite 19/19.

---

## 2. The blocker for gameplay: the catalog asset

**`/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog` does not exist.** The C++ now fails
closed without it and logs one loud error per session instead of failing silently — but
nothing can be granted or equipped until it is authored.

This is editor-lane work (a `UMelodiaCosmeticCatalog` DataAsset). It is now unblocked
because the separated meshes import correctly.

### First records — the five V2 pieces

`FMelodiaCosmeticRecord` needs `CosmeticId`, `Slot`, `Rarity`, `Mesh`, optional
`ResonantFormId`, optional `StyleScores`.

| CosmeticId | Slot | Mesh |
|---|---|---|
| `Cos_Body_MelusinaV2` | `Body` | `/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body` |
| `Cos_Shirt_MelusinaV2` | `Shirt` | `.../SK_Melusina_V2_Shirt` |
| `Cos_Skirt_MelusinaV2` | `Skirt` | `.../SK_Melusina_V2_Skirt` |
| `Cos_Boots_MelusinaV2` | `Boots` | `.../SK_Melusina_V2_Boots` |
| `Cos_Accessories_MelusinaV2` | `Accessories` | `.../SK_Melusina_V2_Accessories` |

Leave `ResonantFormId` as `None` on all five — these are the default outfit, decorative,
not ability-granting. That is the documented common case.

`Rarity`: the drafts use `Refined`/`Couture`, which are not in `EMelodiaCosmeticRarity`.
**Owner decision still open.** Use `Common` for these five until it is settled; 23 of 40
drafts silently import as `Common` today regardless.

---

## 3. Wiring order, once the catalog exists

1. **Verify the pawn** carries exactly one `UMelodiaWardrobeComponent`, and that
   `DefaultGarmentMeshes` holds the four V2 garments. Leave `bEnableBattleWardrobe=false`.
2. **Grant → equip → unequip** on `MelodiaIntegrationMap`. `GrantCosmetic` now validates
   against the catalog first, so an unknown id is refused rather than written.
3. **Save → full process restart → Continue.** Confirm `ApplyWardrobeState()` re-applies
   the equipped set and hides slots the restored record no longer claims. This is the fix
   that has never been runtime-proven.
4. **Only then** the wallet path — `PurchaseCosmeticWithShards` with costs resolved
   through `UMelodiaTokenCatalog::ResolveCost`. Pass resolved elements, not art-variant keys.
5. **Then** one Resonant Form end to end: form → capability → `UMelodiaTraversalComponent`
   consults the registry → Glide gate.

---

## 4. Open decisions blocking further wardrobe work

- **Leader Pose vs Copy Pose From Mesh.** Leader Pose children **cannot simulate
  physics**. KawaiiPhysics drives skirt and hair, and those are hero assets. If garments
  need sim, the component must move to Copy Pose. Expensive to reverse later.
- **Rarity ladder** — `Refined`/`Couture` vs the existing enum.
- **Traversal baseline** — do Resonant Forms *add* capabilities to a baseline, or *are*
  they the only source? This gates the whole progression design.
- **ARKit scope** — 35 shapes now populated, 17 unauthored. Only matters if Live Link Face
  capture is in scope.

---

## 5. What closed today

Melusina V2 is the live pawn (`BP_MelusinaJRPGCharacter → CharacterMesh0 →
SK_Melusina_V2_Body`), with:

- corneas re-bound to `DEF_eye_L/R`, following the head by hierarchy
- fingers rebound at export time to `index2_l`, which the retarget's chains drive
- **0** orphan-skinned bones (was 41), gated by `Tools/test_melusina_skin_topology_contract.py`
- max 4 bone influences (was up to 19), normalized
- **103** morph targets (was 68)

The durable lesson, now encoded in the export path: **a hierarchy fix does not survive
import onto an existing skeleton — UE keeps its stored hierarchy. Weights travel with the
mesh; parents do not.** The eyes worked because that was a weight change. The fingers only
worked once they became one too.
