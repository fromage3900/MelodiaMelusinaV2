# Houdini Lane — Status Notes (2026-10-05)

Working notes for the Crystal Cathedral lane. **This is not a status
authority** — `CURRENT_STATE.md` is. Recorded here because these are
work-session facts that do not belong in the project's status document.

## Where the cathedral actually lives

The lane was built on the **school machine's G: drive**, not on C:.

- Authoritative builder: `G:/Melodia_Houdini_Foundry/Tools/Houdini/cathedral/build_crystal_cathedral_hda.py`
  (md5 `74e8722cc6024c1d5858eba58372fb9d`; C: copy verified identical).
- HDA: `G:/Melodia_Houdini_Foundry/hda/HDA_Melodia_CrystalCathedral_1.0.hda`
  (md5 `dc6ea1a4b579ed4e92cfa82c9a07557c`, byte-identical in the school mirror
  `G:/BS_GodFile_School_20260925/hda/`).
- `G:/Melodia_Houdini_Foundry` is a **local-only** git repo — C: is its second copy.
  Reading its history needs
  `git config --global --add safe.directory G:/Melodia_Houdini_Foundry`.
- C: only ever held the pre-finish numpy ancestors
  (`Tools/Houdini/cathedral/build_crystal_cathedral.py`, `build_fractal_cathedral.py`).

## Verified on C:, 2026-10-05

- hython 22.0.368 runs; numpy 2.3.2; license server up on localhost:1715.
- `build_crystal_cathedral_hda.py` rebuilds and self-verifies clean.
- OUT_Cathedral cooks to **9278 pts / 8641 prims** — matches the school receipt,
  so the rebuild is deterministic and the geometry is intact.
- OUT_Rose cooks to **1032 verts / 288 prims**.
- Bounding box ~12.04 × 45.46 × 25.63 m, centred near y = +22.5.
- Mantra renders headless. See
  `Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md` for the API traps and
  `Docs/Houdini/GOTHIC_GEOMETRY_REFERENCE_2026-10-05.md` for the geometry spec.

## Two environment constraints that shape the plan

**1. Houdini here is Apprentice, not Education.** The school machine had
Education; this workstation has `hou.isApprentice() == True`. Consequences:

- Every Mantra frame carries the **Houdini logo watermark** in a corner.
  Acceptable for internal review; **disqualifying for portfolio plates**, so
  final beauty frames should be captured in Unreal instead.
- CPU-only rendering. It is slow — minutes per frame even at 800×450 on 8.6k
  polys. Budget accordingly and never wrap a render in a short `timeout`.

**2. `Tools/*` is gitignored** (`.gitignore:263`, with a per-file allowlist).
AGENTS.md forbids touching `.gitignore`, and no `Tools/Houdini/cathedral/*` entry
is allowlisted. Consequence: **new tooling under `Tools/` cannot be committed**
without owner approval of a `.gitignore` change. The scripts exist on disk and
work; they are simply untracked. If they need to be durable, the options are
(a) owner adds an allowlist entry, or (b) the lane's canonical home stays
`G:/Melodia_Houdini_Foundry`, which is not ignored.

Docs and the HDA are unaffected: `Docs/Houdini/*.md` and
`hda/HDA_Melodia_CrystalCathedral_1.0.hda` are both committable
(`hda/` is already tracked for `ArpeggioStair_1.0.hda`).

## Non-manifold: diagnosed, not mysterious

`Tools/Houdini/cathedral/probe_nonmanifold.py` clusters >2-use edges by
midpoint. Result:

- **240 edges** at the **z = 0 floor/wall junction**, at y-stations 0.0 / 4.0 / 7.5.
- **2 edges** at the **rose centre hub (0, 0, 0)**.

The goal doc had this as "cause isolated to coincident points but the second
source is not yet found". It is now two named sites, both coincident-point joins,
which means both are addressable with a scoped fuse rather than a redesign.
