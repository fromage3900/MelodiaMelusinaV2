# Sea Above Gaea landscape material contract

The Sea Above landscape uses `/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered`, whose parent is `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape`.

The exported Gaea maps are full landscape maps. They must be sampled once across the landscape with the master’s normalized world XY chain:

`Absolute World Position → subtract GaeaLandscapeMin → divide GaeaLandscapeSize → ComponentMask(RG) → Saturate`

The Glacier landscape actor is translated to `(-249752.225830, -249752.225830, 0)` and scaled to `(495.540131, 495.540131, 244.453125)`. The instance vectors match that transform: `GaeaLandscapeMin=(-249752.21875,-249752.21875,0)` and `GaeaLandscapeSize=(499504.4375,499504.4375,1)`.

`bGaeaWholeLandscapeColor=True` selects the normalized UV inputs for the Gaea albedo and mask lanes. `bTriplanarPro_Active=False` is required in this mode. Triplanar mode samples `MF_Triplanar_LandscapePro` in world space and is intended for close detail, not for the 1024² Gaea export itself. The reusable editor utility is `Content/Python/set_gaea_landscape_mode.py`:

```python
set_mode("whole_map")          # exported Gaea maps fill the landscape once
set_mode("triplanar_detail")   # deliberate world-space detail mode
```

The utility keeps the two modes mutually exclusive, updates the instance, saves it, and writes `Saved/Audit/gaea_landscape_mode.json`. After any material or instance edit, save the exact master/instance packages and confirm the target Landscape’s `landscape_material` still resolves the Glacier instance. Do not infer live behavior from the master graph alone.

The Gaea mask lanes use `Gaea_SnowMask`, `Gaea_WaterMask`, `Gaea_RockMask`, and reserved `Gaea_FlowMask` parameters. Their scalar weights are clamped to `[0,1]` in the master, so inherited or randomized instance values cannot amplify a weightmap beyond its intended coverage.
