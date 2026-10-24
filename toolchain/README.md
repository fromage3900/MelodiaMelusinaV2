# Toolchain — third-party creative tools wired for Melodia

## Sonifold (audio-driven LB eigenmodes) — added 2026-10-24

Upstream: https://github.com/joonhyungbae/Sonifold (pinned clone `bd82441`,
MIT). Re-clone with:

    git clone https://github.com/joonhyungbae/Sonifold.git toolchain/Sonifold

Setup (CPU mode; no GPU visible from this box):

    cd toolchain/Sonifold
    python -m venv .venv
    ./.venv/Scripts/python.exe -m pip install numpy scipy trimesh gpytoolbox tqdm pandas matplotlib

Melodia integration layer (ours, committed — the upstream clone itself is NOT
committed; re-clone per machine):

    houdini/sonifold_live.py         audio FFT -> LB coefficients -> vertex amps (pure python)
    houdini/sonifold_live_sop.py     Houdini Python SOP wrapper (bake/HEU mode + CHOP live mode)
    houdini/test_sonifold_sop.py     hython integration test (TEST PASS 2026-10-24)
    houdini/melodia_eigen.py         eigenbank driver: OBJ -> watertight remesh -> npz + figure
    houdini/build_pearl_skeleton.py  builds heartgate_pearl_skeleton.hip
    houdini/heartgate_pearl_skeleton.hip  GUI: wire GUI_STEP_1 (layer conversion), optional GUI_STEP_2
    houdini/HEU_WIRING.md            full architecture + HDA/HEU/Copernicus recipe + session learnings

Reusable eigenbanks (committed): data/eigen/HeartGate_clean.npz (50 pairs,
HDA_Faraway_HeartGate), data/eigen/SM_Cymatic_A_clean.npz (WaveHarp staff).
Re-mesh sources in data/meshes/*_clean.obj; test audio data/audio/heartbeat_gate.wav.
