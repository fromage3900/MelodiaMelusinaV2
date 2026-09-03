# PPV Fix Execution Spec — 2026-08-31

**Source:** `Saved/Audit/ppv_canonical_state_2026-08-31.json`
**Prerequisites:** Live Monolith MCP (`:9316`), editor open, no modal blocking

---

## Canonical PPV Stack

| Blendable | Weight | Domain |
|---|---|---|
| `MI_MelodiaInk_PortfolioHero` | 1.0 | post_process |
| `MI_MeluColorGrade_PortfolioHero` | 0.69 | post_process |
| `MI_StarryNight_Hero` | 1.0 | post_process |

**Actor label:** `PPV_NikkiDream`

---

## Drift Findings

| Issue | Current | Canonical | Severity |
|---|---|---|---|
| Actor label | `PPV_Dreamprint_Candidate` | `PPV_NikkiDream` | HIGH |
| Grade weight | 0.18 | 0.69 | HIGH |
| Outline weight | 0.57 | 1.0 | HIGH |
| StarryNight domain | `MD_SURFACE` (VanGogh) | `MD_POST_PROCESS` (Hero) | HIGH |

---

## Fix Sequence (5 steps)

### Step 1 — Rename PPV Actor Label

```python
# In editor Python console
import melodia_mcp_server
melodia_mcp_server.ppv_set_label("PPV_Dreamprint_Candidate", "PPV_NikkiDream")
```

Or via REST:
```
POST http://localhost:9316/tools/ppv_set_label
{"old_label": "PPV_Dreamprint_Candidate", "new_label": "PPV_NikkiDream"}
```

### Step 2 — Set Grade Weight to 0.69

```python
melodia_mcp_server.ppv_set_blendable_weight("PPV_NikkiDream", "grade", 0.69)
```

### Step 3 — Set Outline Weight to 1.0

```python
melodia_mcp_server.ppv_set_blendable_weight("PPV_NikkiDream", "outline", 1.0)
```

### Step 4 — Replace StarryNight Blendable

```python
# Remove surface-domain VanGogh
melodia_mcp_server.ppv_remove_blendable("PPV_NikkiDream", "MI_StarryNight_VanGogh")

# Add post-process Hero variant
melodia_mcp_server.ppv_add_blendable("PPV_NikkiDream", "MI_StarryNight_Hero", 1.0, "post_process")
```

### Step 5 — Verify Compile

```python
melodia_mcp_server.melodia_material_get_compile_stats("MI_StarryNight_Hero")
melodia_mcp_server.melodia_material_get_compile_stats("MI_MelodiaInk_PortfolioHero")
melodia_mcp_server.melodia_material_get_compile_stats("MI_MeluColorGrade_PortfolioHero")
```

---

## Pre-Flight Checks

1. Verify PPV actor exists in level:
   ```bash
   curl http://localhost:9316/tools/ppv_find_actor -d '{"label": "PPV_Dreamprint_Candidate"}'
   ```

2. Confirm `MI_StarryNight_Hero` is `MD_POST_PROCESS` domain:
   ```bash
   curl http://localhost:9316/tools/mi_get_domain -d '{"path": "Content/EnvSandbox/Materials/Instances/Showcase/MI_StarryNight_Hero.uasset"}'
   ```

3. Confirm `MI_StarryNight_VanGogh` is currently `MD_SURFACE` (the broken one):
   ```bash
   curl http://localhost:9316/tools/mi_get_domain -d '{"path": "Content/EnvSandbox/Materials/Instances/Showcase/MI_StarryNight_VanGogh.uasset"}'
   ```

---

## Safety Notes

- **Never hand-edit .uasset** — all changes via Monolith MCP
- Spec only — do not execute without owner sign-off
- After execution, run `melodia_material_audit` to confirm all 3 blendables compile clean
- If `MI_StarryNight_Hero` does not exist, flag as BLOCKED and halt