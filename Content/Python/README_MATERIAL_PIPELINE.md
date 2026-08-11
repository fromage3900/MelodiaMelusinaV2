# Material Pipeline Automation — Solo-Dev Workflow

## Quick Reference

### During Active Development (Editor Open)
```python
# In editor Output Log:
py "Content/Python/enforce_material_schema.py" --validate
py "Content/Python/enforce_material_schema.py" --fix

# Or via Monolith from any terminal:
python Content/Python/enforce_material_schema.py  # auto-detects running editor
```

### Pre-Capture Gate (Before Portfolio Renders)
```bash
# Terminal (editor can stay open — uses Monolith):
python Content/Python/enforce_material_schema.py --precapture
```

### Headless CI / Overnight Validation
```bash
# Terminal — launches UE-Cmd, no editor needed:
python Content/Python/run_headless.py --validate
python Content/Python/run_headless.py --fix
python Content/Python/run_headless.py --precapture
```

---

## What Each Script Does

| Script | Mode | Action |
|---|---|---|
| `enforce_material_schema.py` | Monolith (editor open) | Validates all master materials + MPC against `material_schema.yaml` |
| `enforce_material_schema.py --headless` | UE-Cmd (no editor) | Same checks, runs inside engine directly |
| `run_headless.py --validate` | Launcher | Wraps UE-Cmd, saves output to `Saved/Audit/` |
| `material_schema.yaml` | Data | Canonical parameter definition — edit this, not the code |

---

## What Gets Checked

1. **MPC_Melodia_Palette** — all 36 scalars + 16 vectors present
2. **Each master material** — all expected parameters exist with correct type
3. **MPC references** — CollectionParameter nodes wired to expected MPC params
4. **Orphaned params** — any param in material that's not in the schema
5. **Parameter ranges** — SliderMin/SliderMax sanity

---

## File Locations

```
Content/Python/
├── enforce_material_schema.py    # Dual-mode validator + fixer
├── material_schema.yaml           # Canonical schema (edit this)
├── run_headless.py                # Headless launcher
├── material_lib.py                # Shared utilities for graph building
├── setup_portfolio_mpc.py         # MPC scaffolding
└── audit_*.py                     # Per-domain audit scripts

Saved/Audit/
└── headless_*.log                 # Headless run output
```

---

## Adding a New Parameter

1. Add it to `material_schema.yaml` under the appropriate master/group
2. Run `python enforce_material_schema.py --fix` to validate
3. If it doesn't exist in the material yet, create it in the editor
4. Re-run validation to confirm

---

## Toon Profiles (Phase 1 — Next)

Toon Profiles cannot be created via Python yet (UE 5.8 experimental, no API).
Manual authoring workflow:
1. Open any material → Substrate Toon BSDF node → Details → Toon Profile → Create New Asset
2. Tune diffuse ramp, specular ramp, GI intensity
3. Save as `TP_Character`, `TP_Foliage`, etc.
4. Assign to master materials via Material Editor or `set_expression_property`
