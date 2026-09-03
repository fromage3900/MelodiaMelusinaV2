# Collaborator slice manifests

JSON packs for `bash deploy/collaborator_onboarding.sh <tier>`.

| File | Tier | Max MB | Notes |
|------|------|--------|-------|
| `docs50.json` | `docs50` | 50 | Source/Docs/Python — text review |
| `slice50.json` | `slice50` | 50 | MelodiaIntegration BPs (~9.6 MB measured) |
| `placement50.json` | `placement50` | 50 | Universal PCG/physics; EnvSandbox required on workstation |
| `envsandbox_pull_checklist.json` | (checklist) | — | Windows `git lfs pull` steps for placement50 |

Measure without onboarding:

```bash
python Tools/lfs_health_audit.py --manifest specs/collab_slices/slice50.json
```

Authority: `Docs/LIVEOPS_GIT_SOP_2026-08-11.md`. Echo gameplay claims still need ledger rows.
