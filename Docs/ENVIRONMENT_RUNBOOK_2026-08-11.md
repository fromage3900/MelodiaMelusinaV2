# Melodia Environment Runbook

This is the executable setup path for the Windows workspace described in
`ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md`. It intentionally separates
machine prerequisites, optional services, Unreal/editor work, and website work.

## 1. Install the machine prerequisites

Install these outside the repository:

- Unreal Engine 5.8 with the C++ desktop target.
- Visual Studio 2022 with Desktop development with C++, Windows SDK, and
  compatible MSVC toolsets.
- Git and Git LFS.
- Python 3.11.
- Node.js 20 for the website lane.
- Blender 5.2 for the production DCC lane. Blender 5.1 can be selected through
  `MELODIA_BLENDER_ROOT` when maintaining an older compatible addon setup.

Marketplace/Fab plugins such as QuillScript, KawaiiPhysics, and MeshBlend may
still require an Epic Games Launcher installation even when their project
entries are enabled.

## 2. Configure paths without machine-specific commits

The canonical config is `Config/paths.json`. Prefer environment variables for
each machine:

```powershell
$env:MELODIA_UNREAL_ROOT = "C:\Program Files\Epic Games\UE_5.8"
$env:MELODIA_BLENDER_ROOT = "C:\Program Files\Blender Foundation\Blender 5.2"
$env:MELODIA_WEBSITE_ROOT = "C:\EnvironmentPortfolio\my-site-clean"
```

Optional tools use `VOICEVOX_ROOT` and `MATERIAL_MAKER_ROOT`. Empty values are
valid; an optional service must not be represented by a fixed mirror path.

Run the non-destructive validator:

```powershell
.\deploy\validate_setup.ps1 -CheckWebsite
```

Optional service checks can be skipped during code-only work:

```powershell
.\deploy\validate_setup.ps1 -SkipServices
```

The validator fails only hard prerequisites and website lockfile absence when a
website checkout is selected. Services are warnings unless `-StrictOptional`
is supplied.

## 3. Create Python environments

The bootstrap script never installs Unreal, Blender, Marketplace content,
external services, or secrets. It creates local ignored `.venv` folders only
when requested:

```powershell
.\deploy\bootstrap_environment.ps1 -CreateVenvs
.\deploy\bootstrap_environment.ps1 -InstallPythonTooling
```

This creates the UEBlueprintMCP environment from
`Plugins/UEBlueprintMCP/Python/requirements.txt`. The optional quantum lane is:

```powershell
.\deploy\bootstrap_environment.ps1 -CreateVenvs -InstallQuantumTooling
```

Use the corresponding `Scripts\python.exe` when running those tools instead of
assuming the global Python has every optional dependency.

## 4. Choose an onboarding tier

From Git Bash:

```bash
bash deploy/collaborator_onboarding.sh docs
bash deploy/collaborator_onboarding.sh blender
bash deploy/collaborator_onboarding.sh lightweight
bash deploy/collaborator_onboarding.sh full
bash deploy/validate_collaborator_setup.sh . ue
```

The `docs` tier does not pull LFS content. The `blender` tier is intentionally
Blender-only and does not include `BS_GodFile.uproject` or Unreal plugins. The
`lightweight` tier is the UE-capable plugin tier: it includes the project file,
tracked plugin source/manifests, and targeted gameplay/plugin LFS content. The
`full` tier is for build, PIE, and packaging work and may require the full LFS
checkout.

UE plugin binaries are not tracked. After a `lightweight` or `full` checkout,
install VS 2022 Desktop development with C++ and the Windows SDK, close Unreal,
and build:

```powershell
$ueRoot = if ($env:MELODIA_UNREAL_ROOT) { $env:MELODIA_UNREAL_ROOT } else { "C:\Program Files\Epic Games\UE_5.8" }
& "$ueRoot\Engine\Build\BatchFiles\Build.bat" BS_GodFileEditor Win64 Development -Project="$PWD\BS_GodFile.uproject" -NoUBA -MaxParallelActions=1
.\deploy\validate_setup.ps1 -SkipServices -CheckLfsHydration -RequirePluginBinaries
```

## 5. Start the Unreal lane

1. Open `BS_GodFile.uproject` in Unreal Engine 5.8.
2. Allow shaders, asset discovery, and Monolith indexing to finish.
3. Confirm exactly one editor instance exposes Monolith on `9316`.
4. Start with the tracked `L_KaleidoNave` or `L_MelusinaMorning` route; do not
   assume the old local-only `L_Template` map is present in a sparse checkout.

The ECHO control commands are:

```powershell
python Tools/echo_run.py list
python Tools/echo_run.py status
python Tools/echo_run.py run static_gates
python Tools/echo_run.py run runtime_gates
```

`HOLD` means the editor or required evidence is unavailable. It is not a pass.
The runner does not write ledger rows automatically.

## 6. Validate ECHO content

JSON proposals can be checked offline. Proposals containing `melodia:` intents
must use either an exported allowlist or the live data asset:

```powershell
python Tools/echo_run.py validate-spec path\to\proposal.json --allowlist-file path\to\echo_allowlist.json
python Tools/echo_run.py validate-spec Content\MelodiaIntegration\Narrative\MelodiaQuillSmoke.qsc --live-allowlist
```

The live authority is
`/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`. The validator
checks verb arity, flag values, integer deltas/counts, allowlisted identifiers,
duplicate consume-once identities, and rejects the logging-only `item:give`
verb from promotion.

After reviewing actual evidence, record only the exact gate observed:

```powershell
python Tools/echo_run.py record runtime fail --note "describe the observed failure and artifacts"
python Tools/echo_run.py record save_load pass --note "full process restart; canonical slot restored"
```

Do not record a pass for probe-injected rhythm calls, a cook without a package
launch, or a screenshot without its assertion report.

## 7. Run the environment-art lane

The repeatable generic path is:

```text
Blender style/genome
  -> LiveLink :9876
  -> Unreal /Game/LiveLink
  -> material crosswalk and PCG
  -> tracked L_KaleidoNave route or another checked-in validation map
  -> capture/statistics manifests
  -> portfolio_package.json
  -> website handoff JSON
```

Use the environment pipeline documents for style/material constraints. Keep
final Sakura art human-owned and do not use it as a prerequisite for generic
material or PCG validation.

## 8. Run the portfolio and website lanes

From the Unreal project:

```powershell
python Content\Python\generate_portfolio.py
```

The command must return non-zero if required capture/stat/package steps fail;
`portfolio_package.json` existing by itself is insufficient. The output is
consumed by `package_to_website_handoff.py` and written under
`_github_deploy/generated/`.

From the selected website checkout:

```powershell
npm ci
npm run lint
npm run lint:css
npm run verify:all
```

Wix deployment requires `WIX_CLI_TOKEN` and `WIX_SITE_ID`. GitHub Pages can run
without Wix credentials. Figma values belong in local `.env.local` files based
on `.env.local.example`; never commit a real token.

## 9. Evidence and escalation

Run checks in this order:

1. Offline JSON/Python/site checks.
2. Monolith/editor static and runtime tools.
3. Real-input PIE campaigns.
4. Full-process save/load and packaged launch.
5. Ledger recording and reviewable promotion.

When a step is unavailable, capture the command, exit code, log path, and
missing dependency in the handoff. Do not replace a missing runtime proof with
an older document claim.
