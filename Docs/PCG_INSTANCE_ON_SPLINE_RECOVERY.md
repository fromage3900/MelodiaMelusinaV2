# BP Instance On Spline Recovery

The immutable reference is `/Game/Melodia/Actor_BP/BP_InstanceOnSpline_Old`.
The recovered working copy is `/Game/EnvSandbox/PCG/Universal/BP_InstanceOnSpline`.

`Content/Python/gmm/pcg/instance_on_spline.py` validates the file-driven
`gmm_spline_instance_request_v1` contract without importing Unreal. Unreal owns
spline sampling, construction-script regeneration, mesh components, and lights.
The editor adapter `Content/Python/validate_instance_on_spline.py` writes
`Saved/Audit/instance_on_spline_validation.json` after spawning a deterministic
fixture spline and a test actor.

The first recovery attempt exposed stale struct/enum pins in the legacy graph
after consolidation. The working copy is intentionally retained in that state
until the four canonical data assets are remapped and the Blueprint is repaired
in the editor. The old asset remains reference-only and is not modified.
