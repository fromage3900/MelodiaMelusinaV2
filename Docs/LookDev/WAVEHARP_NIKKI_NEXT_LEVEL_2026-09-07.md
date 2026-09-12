# WaveHarp → Nikki Next Level — Curve Ribbons, Beads, Baked Cymatics, Editorial Drapery

**Date:** 2026-09-07 · **Subject file:** `C:\EnvironmentPortfolio\harp_bow_pipeline\ME_WaveHarp_Rev05_BakeUV.blend` (Blender 5.2 live, EEVEE, 39,398 render tris after polish pass)
**Research basis:** UE dev interview "Behind the Scenes of Infinity Nikki" (unrealengine.com), repo skills `melodia-nikki-surreal-fabric` / `melodia-cymatic-eigenmode` / `melodia-garment-motion`, `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`

---

## 1. What Rev05 actually is (detailed study, verified via MCP live read)

- **Transform rig, not bones:** 32 objects in `ME_WaveHarp_Transformation` driven by ~40 drivers off `ME_WaveHarp_Arrow_Control` (4 drivers) + deployment empties (`HarpCartridge`, `Core_Deployment`, `Grip_Deployment`) + 4 `SOCKET_*` empties. Shape keys carry the performance: `Bow_Deployment`, `Flex_Draw` (limbs), `Draw` (bowstring), `Sway_Pos/Sway_Neg` (charm chains). This is the transformation-weapon pattern (Genshin/Dmc style) — already AAA-minded.
- **Shading:** 6 `*_KomikazeHybrid` mats all share the **`Cel Shade 3 Tones (Soft)`** group (47 nodes — the Komikaze cel ramp) + `Iridescence` group (users=4) + `ME_WaveHarp_GN_InvertedHull` outline on **30 objects**. RoseGold×24, PaleBrass×13, StringSilver, crystal/violet/lilac/ivory — a coherent family.
- **Cymatics already started:** `ME_MAT_Chladni_Copernicus_REVIEW_NC.001` = BC/ORM/Emission 1024² from `harp_bow_pipeline/textures/`, live on `Grip_Main` + `Resonance_Ring_Inner`. Height/Normal not yet wired (BC/ORM/Emissive only — no parallax, no displacement).
- **FLIP:** 144 baked geometry snapshots (`ME_WaveHarp_FLIP_*`), no MESH_CACHE modifier — pure geometry, now hide_render'd. Export collection still empty (UE intake pending).
- **Zero curves in file** — everything is mesh. (Answer to "can we use curve profiles": yes, and nothing here conflicts.)

## 2. What Infinity Nikki actually does (from the UE interview — the recipe we're chasing)

1. **One versatile master cloth material** merging multiple fabric textures → fewer variants, consistent platform look. Our equivalent: KomikazeHybrid family — *keep it one graph*.
2. **Semi-transparent layered fabrics** (Fairytale Swan sheer silks): they cap translucency layers (≈2) and sort them deliberately. Our EEVEE mirror: OIT ≤2 layers, sort priority, per the Nikki doctrine already in `melodia-nikki-surreal-fabric`.
3. **Cloth = hybrid:** skeletal-physics chains for trims/ribbons + Chaos Cloth for big panels + rigid authored ornaments. Ribbons and dangling charms in Nikki are **bone chains, not sims** — that's the "next level" insight for us.
4. **Jewelry material:** opaque mesh, fake refraction/reflection via cubemap + algorithmic 3S + sharp highlights. Our crystal gems (currently Principled-only) get exactly this treatment.
5. **Day/night-responsive outfits** — lighting changes alter perceived fabric. Maps to our `W_Melodia_FadeDayNight` world.

## 3. The four asks — verdicts and method

### 3a. Curve profiles → ribbons — YES
- **In Blender (lookdev/hero plate):** create ribbons as **curves with bevel object** (a flat ribbon profile curve) → convert-to-mesh keeps flow; or Geometry Nodes **Curve to Mesh** with profile — fully procedural, width/taper driven by a Float curve along the length. Attach: parent to existing socket empties (`SOCKET_Bow_Grip` etc.) so the transformation rig carries them.
- **Motion without sim:** the Nikki trick = a 4-6 bone **chain per ribbon** with bendy stiffness, animated by simple sinusoid drivers — we already run ~40 drivers; add `Ribbon_Sway` drivers (phase-offset per bone) instead of cloth. Deterministic, game-realtime-ready (becomes UE **AnimDynamics / KawaiiPhysics** later — note the repo already has `BP_KawaiiPhysicsPlacementProbe` history).
- **Shading:** ribbon = thin double-sided strip; feed `Iridescence` group + Shorewake sheen map, outline via inverted hull (already on 30 objects — free consistency).

### 3b. Dangling beads — YES, same lane
- **Chain as curve:** bead profile (icosphere GN instance) **arrayed along a curve** via `Curve to Points` + `Instance on Points`, with a **chain-link constraint curve** so the strand hangs on a catenary. The existing `Charm_Lower_Chain`/`Charm_Right_Chain` already have `Sway_Pos/Sway_Neg` shape keys — replace that 2-pose stub with a real chain curve + bone-chain sway, and the shape keys become blend fallbacks.
- **Physics-lite:** XPBD can't self-collide (2026-09-03 limit, `melodia-garment-motion`) — beads colliding the harp body need **single-strand sims against the body as collider** (colliders work), or the driver-sinusoid chain above. For lookdev: one hero strand XPBD-baked, rest authored.
- **UE route:** beads → skeletal chain + AnimDynamics; jewelry master (3S fake + cubemap) per §2.4 on the gem tips.

### 3c. Bake Houdini textures into the Blender materials — YES, half-dawned already
- The Chladni REVIEW mat is live but only BC/ORM/Emissive. Upgrade path:
  1. `chladni_eigen.py --plate brass --freq <string freq> --m --n --bake` → physics-exact **Height + Normal** already proven (9/9 gate, maps in `Saved/Audit/eigenplate/`). Pick modes from the harp's own string frequencies — the instrument *shows its own notes*. That's the poetic next-level beat.
  2. `copernicus_cymatic_parallax.py --cook` → 9-map PBR families (490 maps exist for garments; add a `waveharp` variant set).
  3. Wire into KomikazeHybrid: the graph already has `Diffuse Color +Baked Diffuse +Range +Normal .KK` — plug eigen Height into the parallax/range lane and Normal into the `.KK` normal input **inside the group**, keeping the cel ramp untouched. Metal/rough from ORM as it is.
  4. Emissive lane = the **nodal singing lines**: Chladni zero-contours glow on BeatPulse (mirrors `MI_*` bindings in the surreal-fabric skill).
- All on `ME_BakeUV` (now active on all 71 objects after today's fix) — no UV rework needed.

### 3d. Editorialized cloth sim + Chladni drapery — YES, with the honest split
- **Editorial stills (the ask):** static XPBD sim in **A-pose on a mannequin collider**, 48-72 frames, settle, **apply as shape key `Drape_Editorial`** — pose it with the transformation rig, render the magazine shot. Blender 5.2 node cloth (XPBD Solver + Cloth Dynamics asset) handles single hero shells (veil/sleeve) fine; no self-collision so one shell at a time. This is exactly the `melodia-garment-motion` lane.
- **Chladni-inflected folds:** displace the sim result along normals by `φ_mn = sin(mπx)·sin(nπy)` eigenmode from `chladni_eigen.py` at bake resolution — *standing-wave wrinkles frozen mid-note*. Editorial + physically true + reads as "this cloth is music made visible" (core Melusina, and the game's whole thesis).
- **Game motion:** never runtime sim — tier it the Nikki way: authored shell + bone-chain trim + WPO micro-swell reading MPC.BeatPulse. VAT (tier D) only for one impossible-event moment.

## 4. Next-level gap analysis (what Nikki has that we don't yet)

| Nikki feature | Our state | Move |
|---|---|---|
| Fabric sheen/velvet lobe | absent in 4-node hybrid | add Principled **Sheen** + coat to Cel group's PBR branch (one group edit, 6 mats inherit) |
| Fake-refraction jewelry | crystals are plain Principled | cubemap refraction proxy + 3S band mat for gems |
| Ribbon/bead bone physics | shape-key stubs only | §3a/3b chains |
| Day/night outfit response | world exists, mats static | color-RAMPE driven by world light temp (already `World Color +Light Source TINT .KK` exists — connect it!) |
| Screen-space pattern on cloth | none | halftone already; add **world-space** Chladni UV so pattern doesn't slide with UV unwrap |
| Hair cards + flow (Nikki hair) | Melusina Water-Advance hair exists | tangent-flow aniso + tip-taper alpha — separate lane, noted |

## 5. Build order (one week, each step ends in a render)

1. **D1 — Cymatic bake upgrade:** eigen Height/Normal onto grip+ring, sheen added to Cel group. One beauty render before/after.
2. **D2 — Ribbons:** 2 curve-profile ribbons on `SOCKET_Bow_Grip` + `SOCKET_Arrow_Nock`, driver sway, inverted hull, iridescence. Render in draw-pose.
3. **D3 — Beads:** 1 hero XPBD chain strand + authored secondary, gems get jewelry mat pass. Render macro.
4. **D4 — Editorial drape:** one veil shell XPBD settle → shape key + eigenmode fold displacement, hero silhouette shot (Nikki poster composition).
5. **D5 — Composite + export:** fill `Export` collection (hero harp + 1 ribbon + 1 strand, ME_BakeUV intact), beauty plate + contact sheet → `Humber_FinalYear_Prep/renders/`, breakdown card for P7.

Every step is reversible, non-destructive (shape keys / curves / modifier stack), and ends with a PNG we can eyeball — the owner's viewport stays ground truth.

## 6. Risks
- XPBD experimental: API may shift; research-lane, bake to keys, never ship live sim from it.
- Driver rig is delicate: add new drivers to **new objects only**, don't rewire existing 40.
- Komikaze group is shared by 6 mats — edit once, test all, save a `.blend1`-guarded copy first (and Blender autosaves are gitignored — copy before mutating).
- FLIP geometry (144 snapshots) stays hidden; if the water-ring returns for a hero plate, reload cache from `flip_ring_cache/` rather than re-sim.
