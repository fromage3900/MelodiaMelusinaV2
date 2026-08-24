# Melodia External Adapter Ledger

This ledger separates Melodia-owned runtime contracts from public research
repositories. No external repository is authoritative for companion identity,
save state, rhythm time, or material style.

| Repository | License / compatibility | Pinned revision | Status | Allowed use |
|---|---|---|---|---|
| [PCGExtendedToolkit](https://github.com/Nebukam/PCGExtendedToolkit) | MIT; local plugin declares UE 5.8 | `0de0e3c69e643c38cf947262b115a28ec3043e11` | Existing validated project dependency | Route topology and habitat queries through a thin adapter; do not duplicate the plugin. |
| [gFurPro](https://github.com/GiM-GamesInMotion/gFurPro) | License and exact revision must be audited before import; open compatibility/render issues are tracked upstream | Not vendored | Research only | Time-boxed UE fur comparison; never a production dependency until license, UE 5.8, and render-thread checks pass. |
| [TressFX](https://github.com/GPUOpen-Effects/TressFX) | MIT; Unreal integration is historical and not a UE 5.8 drop-in | Not vendored | Research reference only | Strand/simulation ideas and benchmark comparison; no direct project dependency. |
| [CTRL.StateTree](https://github.com/ntystudio/CTRL.StateTree) | MIT; external utility layer is unnecessary for the first slice | Not integrated | Rejected for v1 | Use native StateTree/Mass/Smart Objects first. |

## Integration rules

1. Any future adapter must be isolated from `MelodiaCore` through
   `UMelodiaFurBackendAdapter` or a similarly narrow interface.
2. The repository URL, license file, engine version, commit SHA, patch list,
   and known issues must be added here before source or binaries enter the
   project build.
3. No live GitHub fetches are allowed during a build.
4. Third-party assets, binaries, and unreviewed licenses are not eligible for
   webfront promotion.

