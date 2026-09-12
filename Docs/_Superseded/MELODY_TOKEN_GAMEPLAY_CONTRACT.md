# Melody Token Gameplay Contract

GMM owns deterministic token definitions, wallet arithmetic, and battle reward
fixtures. Unreal owns pickup actors, meshes, material instances, Niagara, and
HUD presentation. There is no runtime GMM-to-Unreal command channel.

## Canonical data

The current authored variants are `heart`, `star`, `swirl`, and `water`, mapped
to Forte, Radiant, Arcane, and Tide. Stone, Gale, and Umbral are explicit
elemental fallback definitions.

**Updated 2026-08-01 — the material fallback is gone.** All four variants now have
authored material instances under
`/Game/EnvSandbox/Materials/Instances/MelodyTokens/`, built on
`M_Master_Toon_Universal`. `material_fallback` has been removed from star, swirl
and water; each resolves its own material.

Two defects were fixed in the same pass. `MI_MelodyToken_Heart` had **no parent
material** — it was an orphaned glTF/Datasmith import carrying importer
parameters (`UseBaseColorTexture`, `Refraction`, `UseDisplacementTexture`),
sitting outside the toon pipeline entirely. And `heart.texture_path` pointed at
`melodsytoken_textures/MelodyToken_Heart_BaseColor`, which does not exist; Heart's
textures live under `melodsytoken/Textures/` with a `T_` prefix, unlike the other
three variants.

Star, Swirl and Water drive real parallax from their `Displacement` maps. Heart
ships no Displacement map, so its parallax is deliberately 0 rather than faked.

Their `Emission` maps are currently **unused**, because the master has no emissive
*texture sampler* — **not** because emissive is broken. Under this project's
`r.Substrate=True`, the legacy `MP_EMISSIVE_COLOR` pin is empty by design; emissive
routes through `SubstrateToonBSDF_4` pin 5 from `MaterialExpressionAdd_11`, fed by
the Nikki chain (`GlowColor`/`GlowIntensity`, `InnerGlow*`, `BloomBoost`,
`SparkleIntensity`, `DreamBloom*`, `GlobalEmissiveBoost`). The per-element glow
authored on the token instances **does emit correctly**.

Whether to add an emissive sampler so *regions* of a token can glow, rather than
the whole thing tinting uniformly, is an open art/architecture decision — it
affects every material parented to the universal master and needs owner approval.

`test_tokens.py` previously asserted the empty-`material_path` state as an
invariant, encoding the gap as a rule. It now asserts the intended end state:
every authored variant has its own material and none share one.

Victory grants are idempotent per battle instance. Wallet operations clamp mana,
reject unaffordable spending, and accumulate elemental shards by element.

Run the contract suite from `Content/Python`:

```powershell
python -m unittest discover -s gmm -p "test_*.py" -q
```

Unreal pickup and HUD integration follows only after the contract and asset
registry paths are stable.
