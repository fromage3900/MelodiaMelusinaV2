# Luna #2 — MiMo Hermes Canary + Grok Bot Launcher — 2026-09-24

You are Luna #2. Luna #1 is handling the HappyOyster/Jev-gated experiment. Your lane is separate.

Your mission has two bounded phases:

1. run the **MiMo V2.6 Pro Hermes setup/canary** safely;
2. locate and launch the **already-installed Grok Bot app** on the Windows PC so the owner can manually dispatch Grok workers.

Do not overlap Luna #1's Oyster/Jev lane.

## Read first

Read:

- `AGENTS.md`
- `CURRENT_STATE.md`
- `Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md`
- `Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md`
- `Docs/Prompts/HERMES_SPECIALIST_FLEET_BOOTSTRAP_MISSION_2026-09-23.md`
- `specs/orchestration/hermes_specialist_fleet.candidates.v1.json`
- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`

Do not infer missing local state from GitHub.

## Phase A — local truth and safe sync

From the actual `BS_GodFile` Git root:

1. report branch, HEAD, and `git status --short --branch`;
2. `git fetch origin`;
3. verify the above docs exist on `origin/main`;
4. if local `main` is clean and behind, use `git pull --ff-only origin main`;
5. if dirty or on another intentional branch, do not reset/rebase/clean/stash without owner instruction.

Preserve all local work.

## Phase B — MiMo V2.6 Pro Hermes canary

Goal: prove one clean MiMo/Hermes integration without changing permanent routing.

### B0. Audit first

Report, without exposing secret values:

- Hermes version;
- `hermes doctor`;
- current Hermes provider/base/model;
- whether `MIMO_API_KEY` is present;
- whether MiMo/Hermes configuration already exists;
- current `Tools/model_router.py` HEAD and current orchestrator/deep/code policies.

If `MIMO_API_KEY` is missing:

- do not invent one;
- do not install unrelated tooling;
- report the exact owner action required;
- skip to Phase C so the Grok Bot app can still be launched.

### B1. Snapshot current Hermes config

Before changing provider configuration:

- create a timestamped local backup of `~/.hermes/config.yaml` outside Git;
- record only the backup path and the non-secret current provider/model fields;
- never print or commit credentials.

### B2. Configure MiMo only through supported Hermes/provider methods

Use the current first-party MiMo Hermes integration instructions referenced in the fleet plan.

Target model:

`mimo-v2.6-pro`

Do not change `Tools/model_router.py`.

Do not make MiMo the permanent default.

### B3. Connectivity canary

Run `hermes doctor`.

Then run the B0 schema probe:

Return exactly one JSON object with:

- `model_seen`
- `task_class`
- `ready`

Pass only if:
- JSON parses;
- no invented tool result;
- exact model id is visible/confirmable;
- wall time is recorded.

### B4. Universe Foundry planning canary

Give MiMo:

- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`
- the Faraway Mother genome;
- the current generated mission DAG if present;
- the authority rule that Hermes dispatches, Jev decides closed sets, and existing World Compiler/Hython/TD/UE owners implement.

Task:

> Identify only the next unblocked mission node and return one bounded Hermes worker brief. Do not mutate the repo or propose a parallel subsystem.

Record:

- exact model id;
- wall time;
- tokens/cost if actually reported;
- accepted/rejected;
- authority violations if any;
- exact output artifact path.

### B5. Restore Hermes

After the MiMo probe:

- restore the exact pre-canary Hermes config unless the owner explicitly says otherwise;
- rerun `hermes doctor`;
- verify the previous provider/default is back.

### B6. Result

Report:

```text
MIMO CANARY
model:
connectivity:
B4 result:
wall time:
cost if known:
authority adherence:
config restored:
recommended status: PROMOTE | SPECIALIST | WATCH | PARK
owner action required:
```

Do not promote it yourself.

---

## Phase C — launch the existing Grok Bot app

Goal: get the owner's existing Grok Bot UI/app open and ready for manual dispatch.

### C0. Discovery rules

This is a local Windows app-launch task only.

Do not:
- install Grok;
- update Grok;
- log in/out;
- alter credentials;
- create a new Grok account;
- change app settings;
- kill unrelated processes;
- launch duplicate instances if one is already running.

First determine whether an existing Grok/Grok Bot app or launcher is present.

Check safely, in this order:

1. currently running processes/windows with names plausibly matching Grok/GrokBot/xAI;
2. Start Menu/app registrations;
3. desktop/start-menu shortcuts;
4. documented project-local launcher references;
5. installed-app inventory if needed.

Do not guess an executable path.

### C1. Launch

If an existing Grok Bot app is already running:
- bring its existing window to foreground if supported;
- do not spawn a duplicate.

If installed but not running:
- launch the discovered existing app/shortcut using the normal Windows app launch path;
- do not elevate unless the existing app normally requires it;
- do not modify the repo.

If multiple plausible Grok apps are found:
- do not choose silently;
- report names/paths and ask owner which one.

If none is installed:
- stop and report that clearly;
- do not download/install anything.

### C2. Ready state

After launch, verify only that:
- the process/window is alive;
- the app reaches its normal home/chat screen;
- no login/auth intervention is required.

Do not send messages on the owner's behalf.

### C3. Print three paste-ready Grok dispatches

Once the app is open, print these three short dispatch options for the owner to paste manually:

#### GROK DISPATCH A — Grok 4.7 B1 convergence benchmark

> Read AGENTS.md, CURRENT_STATE.md, and one scoped subsystem contract. Identify the smallest correct next action without proposing a parallel implementation. Read-only. Cite exact repo paths. Do not mutate anything.

#### GROK DISPATCH B — Grok 4.7 Universe Foundry planner benchmark

> Read the Universe Foundry contract, Faraway Mother genome, and current mission DAG. Identify only the next unblocked mission node and produce one bounded worker brief. Preserve Hermes/Jev/World Compiler/Hython/TD/UE authority. No repo mutation.

#### GROK DISPATCH C — fresh-eyes showcase audit

> Read CURRENT_STATE.md and the current showcase-day lock. Perform a read-only audit for one visible presentation defect that can be fixed without reopening parked architecture. Return evidence, exact owner/path, and the smallest safe fix proposal. Do not execute it.

## Final response

Return:

- MiMo canary status;
- whether Hermes config was restored;
- Grok Bot discovery result;
- Grok Bot launched/already-running/not-found;
- any owner action required;
- the three paste-ready Grok dispatches.

Then STOP.
