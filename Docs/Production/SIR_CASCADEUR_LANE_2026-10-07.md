# Sir Melodious — Cascadeur secondary-motion lane (2026-10-07)

Owner-authorized: detailed bird/feather interaction via Cascadeur, converging
on the existing ARP v6 staging. Interactive lane (physics tuning is an artist
call) — the repo side stages inputs, scripts, and the return path.

## Inputs (already on disk, do not re-author)

- Mesh: `Saved/Audit/SirMelodious_FlightUnit_20261003/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5.fbx`
- Clips: `exports/ue_arp/A_Sir_*_v6_ARP.fbx` (v5 + feather fan ±28°/1.15×, 22/22 feathers moving, crest + tie chains present)
- Curves: `exports/ue_arp/Wingbeat_curves_v5.json` (float-curve source for UE import step)
- Script: `Tools/Houdini/sir_kinefx/cascadeur_secondary_pass.py` (in-app import of mesh + 5 takes)

## Why Cascadeur, why now

v6 already carries the **primary** wing motion (fan baked). What reads as
cheap-bird is missing **secondary**: feather overlap lag on the downstroke,
crest-tip lag, tie swing. Cascadeur's AutoPhysics + Secondary Motion slider
is exactly that tool, and its Quick Rig mirrors L/R (feather chains are
symmetric L11/R11 per the sir_flight doctor). Houdini KineFX stays the
procedural backup (PLAN §P2); Blender stays the primary-key owner.
No lane replaces another.

## Procedure (interactive, Cascadeur 2026.1.3 on this machine)

1. Empty scene at **24 fps** first (matches all v5/v6 contracts; Cascadeur
   defaults to 30 — mismatch silently retimes wingbeats).
2. Run `cascadeur_secondary_pass.py` in-app → mesh + 5 takes imported.
3. **Scale check before rigging:** withers-to-tail should read ~40 cm span
   class. If Sir is giant, it is the documented Blender-meter → Cascadeur-cm
   ×100 import trap — fix at import scale, never by re-authoring.
   (Same trap class as the sir_flight `scale_gate` HOLD.)
4. Export settings from Blender apply in reverse here: the ARP rig carries
   controllers — Cascadeur only wants **deform bones**. If the joint list is
   noisy, re-export the v6 source with Only-Deform-Bones and re-import.
5. Quick Rigging Tool → mirror L/R → Generate rig.
6. Animation Unbaking per take (baked ARP keys → editable intervals).
7. AutoPhysics preview → Secondary Motion: feathers first (small slider —
   22 light chains), then crest tip, then tie. Keep the clef readable
   (LimitAngle thinking per `KAWAII_SPEC_20261003.md`: crest ≤25°).
8. Export FBX per take to `Saved/Audit/SirMelodious_FlightUnit_20261003/exports/cascadeur/`
   (create on first export), cm, 24 fps, -Z forward.
9. Return path is the existing guarded UE animation-only import onto the
   **frozen** `SK_SirMelodious_Rigged` skeleton per `UE_IMPORT_HANDOFF.md`
   §2–3 (Force Root Lock off, Animation translation mode, Downstroke sync
   markers, Wingbeat float curves). Old `A_Sir_*_v3` assets stay untouched;
   Cascadeur takes land as new versions, never overwrites.

## Optional bridge

`Cascadeur_Bridge` (xrobinx, GPLv3, Blender 4.x–5.x ↔ Cascadeur 2024–2026)
transfers characters/animation Blender↔Cascadeur with NLA blocks. Not
installed; evaluate only if the FBX round-trip loses take names or timing.
No download has been run from this lane.

## Gates

- Take names + 24 fps survive the round trip (else fix bridge/export, not keys).
- Feather symmetry preserved (L/R travel within the Land-asymmetry fix budget).
- sir_flight doctor re-run over `exports/cascadeur/` before any UE import.
- PIE proof per PLAN §P4 stays the only acceptance; contact sheets are diagnostics.
