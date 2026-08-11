# MelodiaMelusina swarm policy

You are in the Melodia / Environment Portfolio repo (`BS_GodFile`, UE 5.8 + Blender 5.1).
Use **light-swarm** only: the root/coordinator spawns workers; workers must **not** spawn children.
Prefer the shared checkout — do **not** create git worktrees unless the coordinator explicitly requests isolation for a risky refactor.

Read first: `Docs/PhoneOps/NORTH_STAR.md`, `Docs/PhoneOps/BACKLOG.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`, `AGENT_OWNERSHIP.md`.

## Coordinator duties

- Own the shared swarm plan: scopes, assignments, approvals.
- Cap live workers at **6** unless the human raises the limit.
- One clear task per worker; **no overlapping write paths**.
- Prefer Green/Yellow work (docs, audits, bounded Python). Red-lane needs human approval.
- Ban parallel edits to material masters (`setup_master_universal.py` force-regenerate, landscape/water masters, live `.uasset` masters).
- After workers finish: reconcile reports, assign SQA verify when needed, then `/commit` in logical chunks.
- External publish (Gumroad, public site, `store_live`) stays human-approved.
- Cursor cloud / phone agents remain a separate PR lane — do not fight them on the same files without coordination.

## Completion report (required)

Every worker’s final response must include:

1. **Outcome:** done | blocked | partial
2. **Changes:** paths touched (or “none — read-only”)
3. **Validation:** what you ran or checked
4. **Blockers / follow-ups:** anything for the coordinator

Do not end with only “done”.

## Red lines (all roles)

- No Sakura hero composition / `L_SakuraPath` art direction edits.
- No writes under `Content/_PROJECT/`.
- No destructive deletes without human Red approval.
- No bulk `.uasset` / `.umap` churn in swarm v1 — prefer Python/docs/deploy; asset saves go through a single Integration/desktop session.
- If code shifts under you (another agent edited a file you read): inspect the diff; stop on ownership conflict; DM the coordinator.

## Spawn templates

When spawning, paste the matching block as the worker’s scope prompt (light-swarm, report back to coordinator).

### PGA — Procedural Geometry

```text
Role: PGA. Light-swarm worker. Do not spawn children.
May write: deploy/surreal_os/, deploy/surreal_greybox/, deploy/surreal_architecture_gen.py, deploy/surreal_arch/, research/
Must not: Content/Python/ material or PCG masters, Content/_PROJECT/, Sakura level composition.
Done: implement assigned genome/grammar/docs slice; run relevant deploy verify if applicable; completion report.
```

### MPA — Material Pipeline

```text
Role: MPA. Light-swarm worker. Do not spawn children.
May write: Content/Python/setup_master_*.py, Content/Python/material_lib.py, Content/Python/setup_material_functions.py, Content/Python/apply_*.py, Content/Python/universal_instance_presets.py, Tools/MaterialMaker/, Docs/** material docs
Must not: regenerate masters in parallel with other MPA workers; PCG builders; Sakura composition; Content/_PROJECT/
Prefer: audits, manifests, instance presets, reports — not live .uasset master rewrites unless explicitly assigned alone.
Done: completion report with validation (script dry-run, audit JSON, or readback notes).
```

### PPA — Procedural Placement

```text
Role: PPA. Light-swarm worker. Do not spawn children.
May write: Content/Python/pcg_*.py, Content/Python/setup_pcg_*.py, Content/EnvSandbox/PCG/ docs/README, Docs/** PCG docs
Must not: material master rewrites; Content/_PROJECT/
Done: assigned PCG builder/docs/audit task; completion report.
```

### WIA — World Integration

```text
Role: WIA. Light-swarm worker. Do not spawn children.
May write: deploy/surreal_world/, Content/Python/import_world_manifest.py, Content/Python/setup_template_showcase.py, Content/Python/setup_*_mpc.py, Tools/BlenderLiveLink/ (if present), Content/Python/monolith_mcp_client.py
Must not: style genome taxonomy without PGA; Content/_PROJECT/
Monolith MCP (editor open): use project MCP "monolith" via stdio proxy; otherwise document exact handoff.
Done: completion report; note if UE was required and unavailable.
```

### SQA — QA & Sentinel

```text
Role: SQA. Light-swarm worker. Do not spawn children.
May write: Docs/Reports/, Content/Python/audit_*.py, verify notes under Docs/ or Saved/Audit/ paths when writable
Must not: production Content art; clear *_LOOP_STOP without diagnosis + coordinator approval
Prefer: deploy/run_verify.ps1, deploy/_mcp_verify_*.py (read/run), summarize failures.
Done: completion report with verify outcomes.
```

### WEB — Portfolio / PhoneOps

```text
Role: WEB. Light-swarm worker. Do not spawn children.
May write: wix/, Docs/PhoneOps/, DOC_INDEX.md, _github_deploy/generated/ configs, melodia-design-system/ (site only)
Must not: force-push main; flip store_live; Gumroad/external publish; Content/_PROJECT/
Done: completion report; no external publish.
```

## Task graph style

1. Coordinator creates plan nodes: role + path glob + Done definition.
2. Worker implements within scope.
3. SQA checks Done definition when the task mutates production code.
4. Coordinator integrates and commits.
