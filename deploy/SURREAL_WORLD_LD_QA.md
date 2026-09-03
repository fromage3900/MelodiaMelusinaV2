# Layer 2 Compose — LD QA Checklist

**Version:** 2.68.0  
**Automated metrics:** `surreal_world.verify_hooks.compose_metrics()`  
**Verify tier:** `_mcp_verify_world.py` → `--- LD compose metrics ---`

## Castle plan (`SurrealPlan_Castle`)

| Check | Target | Automated |
|-------|--------|-----------|
| Face count | ≥ 5 ward + keep faces | yes |
| Vertex groups | `is_corner_tower`, `is_gate`, `is_keep` present | yes |
| Instance count | ≥ 15 at detail_scale 0.8 | yes |
| Corner towers | 4 instances at tagged corners | yes |
| Gate | 1 instance at south midpoint | yes |
| Walls | ≥ 4 boundary wall segments | yes |
| Keep (large role) | ≥ 1 on inner face | yes |

## Zen Roji plan (`SurrealPlan_ZenRoji`)

| Check | Target | Automated |
|-------|--------|-----------|
| Sacred dispatch | ≥ 1 `sacred` role instance | yes |
| Torii at entry | gate or corner_tower on path start | yes |
| Instance count | ≥ 8 at detail_scale 0.9 | yes |

## Tag workflow (manual in viewport)

1. Enter Edit Mode on plan mesh
2. Select verts → use Compose panel tag operators:
   - **Tag Keep** → `is_keep` → `large` role
   - **Tag Plaza** → `is_plaza` → `monument` role
   - **Tag Sacred** → `is_sacred` → `sacred` role
   - **Tag Gate** → `is_gate` → `gate` role
   - **Tag Tower** → `is_corner_tower` → `corner_tower` role
3. **Visualize Plan** — confirm color coding matches intent
4. **Compose World** (COLLECTION mode) — inspect WorldRoot hierarchy
5. **Recompose** — edit plan tags → recompose → instance count stable ± tag changes

## Recompose loop (manual)

| Step | Pass criteria |
|------|---------------|
| Compose | WorldRoot created, instances under `{Plan}_Composed` |
| Move plan vertex | Recompose updates wall stretch / building placement |
| Toggle sacred tag | Sacred instance count changes by ±1 |
| Second recompose | No duplicate WorldRoots; same root name |

## Visual quality (manual — not automated)

- [ ] Buildings face outward from plan center
- [ ] Wall segments connect at corners without large gaps
- [ ] Scale feels consistent across ward sizes
- [ ] Zen roji path reads as sequential (torii → courtyard → teahouse)
- [ ] No overlapping instances at default detail_scale

## Failure triage

| Symptom | Likely cause |
|---------|--------------|
| 0 instances | Library not initialized |
| Missing sacred | Face verts not in `is_sacred` group |
| Duplicate roots after recompose | Old JOINED mode or patch not applied |
| Walls too short/long | Plan edge length vs wall native length (4m) |
