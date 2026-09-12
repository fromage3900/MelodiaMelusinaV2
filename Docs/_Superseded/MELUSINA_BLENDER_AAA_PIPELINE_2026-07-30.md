# Melusina — Blender to UE5 Character Pipeline (AAA / Genshin-tier)

**Date:** 2026-07-30
**Rig:** Auto-Rig Pro · **Target:** UE 5.8 · **Look:** anime NPR, cozy/pastel
**Companion:** `Docs/MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md` (do that first)

This is the full pipeline, ordered. Phases 0–2 are prerequisites — everything after them is
wasted work if the rig is wrong.

---

## Two things about your current setup, before anything else

**1. Your textures are fighting your art style.**

You have `Melusina'sUpdatedShirt_BaseColor / Normal / Roughness / Metallic / Displacement /
Emission / Alpha` — a full PBR set. That is the *photoreal* pipeline. Genshin-tier anime uses
almost none of it:

| Map | PBR use | Anime NPR use |
|---|---|---|
| BaseColor | ✅ | ✅ — but flat, no baked lighting or AO |
| Normal | ✅ | ⚠️ subtle only; strong normals break cel bands |
| Roughness | ✅ | ❌ replaced by a **ramp/LUT** |
| Metallic | ✅ | ❌ replaced by a **matcap** |
| Displacement | ✅ | ❌ unused |
| Emission | ✅ | ✅ keep |
| — | — | ✅ **Light Map** (the Genshin secret sauce) |
| — | — | ✅ **Face SDF map** |
| — | — | ✅ **Material ID mask** |

You are not behind — you are producing the *wrong three maps* and missing the *three that matter*.
That is a one-afternoon correction, not a rebuild.

**2. You already have a Blender NPR prototype build installed.**

`C:\Program Files\Blender Foundation\blender-4.4.0-alpha+npr-prototype...` — Blender's experimental
NPR branch. Useful for look-dev previewing, but **do not author production assets in an alpha**.
Author in 5.2, preview there if you like the feedback loop.

---

## Phase 0 — Fix the rig (blocking)

Nothing below matters until `shared_bones > 0`. Follow
`MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md`. Summary: hair must ride the **same ARP armature**
as the body, `hair_root` parented under `head_x`, `HairExp_Rig` deleted, exported **Universal**
(never Humanoid), imported against the **existing** `SK_Melusina_Skeleton`.

**Do this before you touch shape keys.** Shape keys are baked against a specific mesh topology and
bone hierarchy — re-exporting the rig afterwards means re-doing them.

---

## Phase 1 — Mesh hygiene

Boring, and it is the difference between "student work" and "ships".

- [ ] **One mesh per material zone**, or one mesh with clean material slots. Decide now; UE section
      order follows Blender material slot order.
- [ ] **Apply all transforms** (Ctrl+A → All Transforms) on every exported object. Scale must be
      `1,1,1` and rotation `0,0,0` at export.
- [ ] **Origin at world zero** for the character root.
- [ ] **No n-gons** in deforming areas. Quads and tris only; quads where it bends.
- [ ] **Merge by distance** on the whole mesh (0.0001) to kill split verts that cause seams.
- [ ] **Recalculate normals outside** (Shift+N), then check with face orientation overlay — no red.
- [ ] **Custom split normals cleared** before you do the normal work in Phase 2, or you will be
      fighting stale data.
- [ ] **UVs:** no overlaps on UV0 unless intentional. Keep a **second UV channel free** — the face
      SDF and some outline tricks want it.
- [ ] **Max 4 bone influences per vertex.** Weight Paint → Weights → Limit Total → 4. UE will
      silently clamp and change your deformation if you skip this.

---

## Phase 2 — Normals: the single biggest visual upgrade

This is the one most people never do, and it is why their anime characters look lumpy while
Genshin's look clean.

Cel shading quantises lighting into hard bands. Any normal irregularity that photoreal shading
would hide becomes a **visible jagged edge** in the shadow band. The fix is to overwrite the mesh's
real normals with idealised ones.

### 2a. Hair — transfer normals from a proxy

- [ ] Add a UV Sphere (or a smoothed low-poly dome) roughly matching the skull volume.
- [ ] Select hair → add **Data Transfer** modifier → Source = the sphere.
- [ ] Enable **Face Corner Data → Custom Normals**, mapping **Projected Face Interpolated**.
- [ ] Enable **Auto Smooth** on the hair mesh (required for custom normals to take).
- [ ] Apply the modifier. Delete the sphere.

Result: light sweeps across the hair as one clean band instead of breaking on every strand card.
This is *the* Genshin hair look.

### 2b. Face — the same trick, gentler

- [ ] Same Data Transfer approach from a smoothed head proxy, but blend at low strength, or
- [ ] Use **Weighted Normal** modifier (Keep Sharp on) for a lighter version.

Faces are where lumpy shading is most obvious and least forgivable.

### 2c. Vertex colours — outline control

Genshin-style outlines are **inverted hull**: a duplicate mesh, normals flipped, pushed out along
vertex normals, rendered backface-only. Thickness is driven per-vertex.

- [ ] Create a vertex colour layer named `Col` (or `OutlineControl`).
- [ ] Paint **R = outline thickness** — white where you want thick lines (silhouette), black where
      you want none (inside the mouth, between fingers, eyelash roots).
- [ ] Paint **G = outline z-offset** if your shader supports it, to stop outlines poking through.
- [ ] Leave B/A for shader-specific use.

Vertex colours export in FBX automatically. In UE they arrive as the mesh's vertex colour channel.

---

## Phase 3 — The three maps that make it read as anime

### 3a. Light Map (the Genshin "secret sauce")

Not a lightmap in the UE sense. A **channel-packed control map**:

| Channel | Controls |
|---|---|
| **R** | Specular intensity / shape |
| **G** | Shadow threshold offset — where a region flips to shadow *earlier or later* than NdotL says |
| **B** | Specular / metal mask |
| **A** | Ramp row selector — which row of the ramp LUT this pixel samples |

The **G channel is the important one**. It lets you say "the underside of this sleeve goes into
shadow before the light angle says it should", which is how hand-painted anime shading cheats
look right. Paint it in Blender (Texture Paint) or Substance.

### 3b. Ramp / LUT texture

A small strip (e.g. 256×32), each **row** a different material's light-to-shadow gradient — skin,
cloth, metal, hair. Sample it with `NdotL` on X and the Light Map's A channel on Y.

- [ ] Author as a horizontal gradient per row. Hard transitions = harder cel bands.
- [ ] Skin rows want a warm shadow (never grey). Cloth rows want a cooler one.
- [ ] Export as **sRGB off**, no mipmaps, clamp not wrap.

### 3c. Face SDF shadow map — the thing that separates good from great

Anime faces must **not** use normal-based shading. A nose casting a real shadow is instantly wrong.
Genshin uses a signed-distance-style map driven by the *head's forward vector*, not by light normals.

**How to bake it in Blender:**

1. Isolate the face mesh, front-facing, flat lit.
2. Place a light and rotate it around the head's vertical axis in steps (every 5–10° from full
   left to full right).
3. At each step, bake or render the lit/unlit mask to the face UV.
4. Composite: each pixel's greyscale value = **the angle at which that pixel transitions to shadow**.
   Pixels near the nose bridge flip early; forehead centre flips late.
5. Save as a single-channel greyscale, **sRGB off**.

In the shader you compare that stored threshold against the dot product of the light direction and
the head bone's right/forward vectors. The shadow then sweeps across the face in one smooth,
art-directed shape — no nose shadow, no lumpy cheeks.

This is a half-day task and it is the highest-impact thing on this entire page for a character
whose face is on screen constantly in a VN.

### 3d. Material ID mask

Flat colour-coded regions (skin / hair / cloth A / cloth B / metal / eyes). Used to branch shader
behaviour per zone. Author as flat unfiltered colour, **sRGB off**, nearest-neighbour sampling.

---

## Phase 4 — Facial shape keys / morph targets

### Which set to author

Use the **ARKit 52** standard, even though this is not a face-tracking game:

- It is the documented standard UE tooling expects.
- MetaHuman, LiveLink, and most facial tools speak it.
- It is a complete, tested set — you will not discover a missing shape mid-production.
- If you ever want performance capture from an iPhone, it just works.

Add Melodia-specific extras on top: `mel_blush`, `mel_sparkle_eyes`, `mel_determined`, etc.

### Naming rules (get these right or UE fights you)

- [ ] **No spaces, no dots.** `eyeBlinkLeft`, not `eye blink.L`. Dots break UE morph target names.
- [ ] Consistent case. Pick camelCase and never deviate.
- [ ] The **Basis** key must be first and must be the neutral mesh.
- [ ] Every key's value **0.0 at export**. A key left at 1.0 bakes into the base mesh.

### Authoring rules

- [ ] Sculpt shapes on the **final topology**. Any retopo after this invalidates every key.
- [ ] **Never move a vertex that should not move** — stray verts read as facial glitches.
- [ ] Use **Shape Key Mirror** (with topology mirror if your mesh is symmetrical) rather than
      sculpting both sides.
- [ ] Combination shapes (e.g. `mouthSmile` + `eyeSquint`) are driven in-engine, not authored as a
      third key, unless the combination breaks.

### The export trap that catches everyone

Your mesh modifier stack must contain **exactly one Armature modifier and nothing else** at export.

- [ ] If a **Subdivision Surface** modifier sits above Armature and you export with **Apply
      Modifiers ON**, every shape key is silently destroyed. Either move Subsurf below, or keep a
      separate no-modifier export copy.
- [ ] Do not enable **Apply Modifiers** unless you specifically need it — it bakes the shape key
      stack flat.
- [ ] **Export Shape Keys** must be ticked (default on in recent Blender, verify anyway).
- [ ] Include **both** Armature and Mesh in the FBX Include panel.

### UE import

- [ ] **Import Morph Targets** ✅
- [ ] **Update Skeleton Reference Pose** ✅ when the rig changed
- [ ] Skeleton = existing `SK_Melusina_Skeleton`
- [ ] After import, open the mesh and confirm the morph target list is populated. If it is empty,
      the modifier stack was the cause 90% of the time.

---

## Phase 5 — Weight painting

### Where it actually matters

Ranked by how visible failure is, for a character seen in VN close-ups and third-person:

1. **Shoulders / deltoid** — the classic candy-wrapper collapse. Most visible in idle.
2. **Neck → jaw** — where body and head meet. Breaks in every dialogue shot.
3. **Elbows / knees** — volume loss on bend.
4. **Hips / skirt attachment** — where cloth sim meets skin.
5. **Fingers** — only if you do close-up hand acting.

### Method

- [ ] Start from ARP's automatic weights — they are genuinely good. Do not hand-paint from zero.
- [ ] Fix by **subtracting**, not adding. Most bad deformation is a bone having influence it should
      not, not missing influence.
- [ ] Use **Weight Paint → Smooth** at low strength across joints rather than brushing manually.
- [ ] Turn on **Show Zero Weights → Active Group** to find orphan vertices.
- [ ] **Limit Total → 4** at the end, then **Normalize All**.
- [ ] Test with the **pose library**, not the rest pose. Rotate each joint to its extreme and look.

### Hair and skirt — do not hand-weight the dynamics

Your hair already runs **Kawaii Physics** under `hair_root`. Weight the hair chain rigidly to its
own bones and let physics do the motion. Same approach for the skirt: bone chains + Kawaii Physics,
not cloth sim, for a game character.

- [ ] Hair cards weighted to `A_DEF_hair_bbone_*` chains with clean falloff between segments.
- [ ] The topmost hair bones weighted 100% to `hair_root` so the whole mass follows the head.

---

## Phase 6 — Animations to author

Grouped by what the game actually needs, with the current gap called out.

### Locomotion (partly exists)
- [ ] Idle — the most-seen animation in the game. Give it a breathing loop and a subtle weight shift.
- [ ] Walk / Run cycles
- [ ] Jump: start / loop / land
- [ ] Glide loop (exists) — plus glide start / end transitions
- [ ] Turn-in-place (left / right)

**Priority:** replacing the third-person placeholders you have been asking to remove for weeks.
Those are the single biggest thing making the game read as a template.

### Battle (stock JRPG lane)
- [ ] Battle idle (distinct from explore idle — weight forward, ready)
- [ ] Basic attack
- [ ] **Petal Cadence** — the Resonance applier. This one carries the game's identity; it should
      read as *offering* something to Sir, not attacking.
- [ ] Hit reaction (light)
- [ ] Victory pose
- [ ] Defeat / down
- [ ] Turn-start step-forward, turn-end step-back

### VN / dialogue
- [ ] Talking idle with facial morph layer
- [ ] 3–4 emotional idle variants (happy / worried / determined / tired)
- [ ] Sitting idle (bedroom bookends)

### Technical notes
- [ ] Author at **30fps** and export at 30 unless you have a reason otherwise. Be consistent.
- [ ] **Root motion:** decide per-clip and be consistent. Locomotion in-place, attacks with root
      motion, is the usual split.
- [ ] Bake to the **deform bones** before export — ARP export handles this, but verify.
- [ ] One action per FBX, or use ARP's batch exporter with actions marked.

---

## Phase 7 — Export settings (Auto-Rig Pro)

- [ ] Use **ARP → Export**, never plain FBX export.
- [ ] Type: **Universal** (Humanoid remaps to a fixed bone list and drops custom bones).
- [ ] **Only Deform Bones** ✅ — excludes `c_*` controllers. This is why your body is 465 bones and
      not double.
- [ ] Units **Centimeters**, scale **1.0**, do not double-apply unit scale.
- [ ] Axis: use ARP's **Unreal preset** if present, else Y-up / -Z-forward.
- [ ] **Add Leaf Bones: OFF** (creates junk `_end` bones in UE).
- [ ] Bake Axis Conversion: off unless ARP's preset says otherwise.
- [ ] Export selected objects only.

---

## Phase 8 — UE side, briefly

Full shader work is a separate task, but so you know the target:

- **Shading model:** Unlit with custom lighting, or Default Lit with a custom lighting function.
  Unlit gives total control and is what most Genshin-style shaders use; it costs you Lumen
  interaction, which for a stylised cozy game is an acceptable trade.
- **Outlines:** inverted hull on a second material slot, backface-only, thickness × vertex colour R
  × distance-to-camera.
- **Face:** the SDF map path, driven by `head_x`'s forward/right vectors passed in as material
  parameters.
- **Rim light:** fresnel masked by the Light Map, not global — a rim on everything reads as cheap.

Ready-made references exist if you want to study rather than build from zero — see Sources.

---

## What actually separates AAA from student work here

Not polycount, not texture resolution. In order:

1. **Normals** (Phase 2). Clean shading bands. Nobody notices when it is right and everybody feels
   it when it is wrong.
2. **The face never uses normal-based shadow** (Phase 3c). This is the single strongest anime
   "tell".
3. **Silhouette reads at 5% screen size.** Squint at it. If the shape is unclear, the texture will
   not save it.
4. **The idle animation.** It is on screen more than every other animation combined.
5. **Consistent shadow colour temperature** across every material. Nothing screams amateur like a
   character whose skin shadow is cool grey and whose cloth shadow is warm brown.

You are an animator. Items 3, 4 and 5 are **your** home turf — most technical artists are weak
exactly there. Play to it.

---

## Suggested order for tonight

Do not attempt the whole document. In order of "visible improvement per hour":

1. **Phase 0** — the hair re-export. Unblocks everything and removes the bug that has been
   bothering you all day.
2. **Phase 2a** — normal transfer on the hair. Twenty minutes, dramatic and immediately visible.
3. **Phase 5** — shoulder and neck weights. One hour, fixes every shot she appears in.

That is a genuinely good evening's work and all three are things you will *see*.

Phases 3 and 4 are separate sessions. Do not start shape keys until the rig is final.

---

## Sources

- [80.lv — Setting Up a Genshin Impact-Style Shader in UE5](https://80.lv/articles/breakdown-setting-up-a-genshin-impact-style-shader-in-unreal-engine-5)
- [Genshin Impact Character Shader for Unreal Engine (Ben Ayers, ArtStation)](https://www.artstation.com/marketplace/p/aJV1q/genshin-impact-character-shader-for-unreal-engine)
- [Genshin Impact Character Shader Breakdown, Adrian Mendez](https://www.artstation.com/artwork/wJZ4Gg)
- [Anime Character Materials and Shaders Breakdown, Erfan Ghaemian](https://www.artstation.com/artwork/OGrz8g)
- [Auto-Rig Pro — Game Engine Export documentation](https://www.lucky3d.fr/auto-rig-pro/doc/ge_export_doc.html)
- [Shape Keys and Morph Targets: Blender / Unity / UE5 workflow](https://bitsoulhosting.com/marketplace/blog/shape-keys-morph-targets-blender-unity-unreal-engine-5-workflow)
- [Blender shape key animations imported as UE morph target animations](https://continuebreak.com/articles/how-blender-shape-key-ue4-morph-target-animations/)
