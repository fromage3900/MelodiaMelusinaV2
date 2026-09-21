# DISK_RECLAIM 2026-09-15 (measured, not prose)

## Volumes (measured via measure_disk.py + df)
| Volume | Total | Free start | Free end |
|---|---|---|---|
| C: | 1022.8 GB | 13.7 GB | 15.3 GB |
| D: | 2000.4 GB | 158.2 GB | 158.2 GB |
| G: | 1000.2 GB | 57.3 GB | 51.2 GB (lost ~6 GB mid-session, writer unknown) |

## Cleared without asking (all regenerable, measured)
- uv cache clean: 755.4 MB (self-reported, 44447 files)
- pip cache purge: 0 (already empty)
- Chrome Cache + Code Cache: ~310 MB
- NVIDIA DXCache + GLCache: ~563 MB
- CrashDumps: ~152 MB
- JetBrains logs only (Rider2026.2 + IntelliJIdea, caches untouched, Rider live): ~235 MB
- VS Code Cache/CachedData: ~58 MB
- Net C: gain: +1.6 GB (13.7 -> 15.3 GB)

## Cleared with owner go-ahead (measured)
- BS_GodFile Intermediate 5.5 GB: deleted with no UnrealEditor running; regenerates on next
  build (first build/touch of C++ will take longer, routine UE practice).
- Downloads 3.01 GB: copied to G:/Downloads, byte-verified ALL-MATCH, source cleared.
  Contents are live production assets (kb3d_jpn, Cascadeur, MotionSymphony, VRM4U, UE plugins).
- Net C: gain this round: +5 GB (13 -> 18 GB free; lanes wrote ~3 GB meanwhile, Temp still growing).

## C: standing (measured, end of session)
~18 GB free. Still below the ~30 GB UE-build comfort line. The rest needs owner hands
(Epic 14 GB via Launcher, VS cache 2.2 GB via admin, old Blender versions ~2.5 GB via
Settings > Apps) — all proposed above, none taken from this lane.

## Untouched (owner rules)
- BS_GodFile Saved/ (29 GB), Content/, .ollama, CompatibilityLabs, Saved/Recovery
- %TEMP%/opencode 26.1 GB: entire TEMP tree newer than 2d, live sessions own it
- JetBrains caches (12.0 + 8.8 GB): Rider is running, off-limits from this lane
- C:/$Recycle.Bin: 73K, nothing to take

## Destination probes (measured)
- D:: WRITES FAIL from two independent writers (python open EINVAL x2, bash redirect ENOENT) while reads + free-space report fine. Matches historical D: hardware-error pattern. NOT a move target until owner re-verifies.
- G:: writable (probe file created + deleted), but free fell 57.3 -> 51.2 GB during this session. Find the writer before bulk moves.

## Proposed moves (GB-for-yes, owner decides, no action taken)
1. VS Packages cache 2.19 GB: regenerable installer cache, needs one elevated delete (UAC).
2. Epic uninstalls via Epic Launcher's own buttons: Twinmotion2026.1 9.05 + DuetNightAbyss 4.45 + RealityScan 0.61 = ~14.1 GB. UE_5.8 39.8 GB KEEP.
3. Downloads 3.01 GB (native-measured; MSYS du reads 0, do not trust MSYS here): move to G: only after G: churn explained.
4. BS_GodFile Intermediate 5.5 GB: regenerable build artifacts, costs a rebuild. Owner call.
5. pagefile: already explicit per standing record, no-op. hibernation: not re-probed this session, claimed 0 before.
