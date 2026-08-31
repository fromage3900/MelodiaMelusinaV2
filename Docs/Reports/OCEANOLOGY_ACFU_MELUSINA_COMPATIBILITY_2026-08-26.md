# Oceanology Expanded / ACFU / Melusina Compatibility — 2026-08-26

## Verdict

Neither vendor plugin is ready for a live-game compatibility build because
the purchased Oceanology package and the ACFU vendor source are not currently
available on disk.

- Oceanology: the project contains two old editor DLLs and content under
  `Plugins/Oceanology_Plugin`, but no `.uplugin` descriptor and no source. The
  project descriptor keeps `Oceanology_Plugin` disabled. This is an unusable
  binary remnant, not evidence that Oceanology Expanded is installed.
- Purchased Oceanology staging: `G:/EnvironmentPortfolio/Imports/Oceanology`
  contains only `PROVENANCE.md`. It still says the download/archive hash is
  pending. No archive or plugin descriptor was found.
- UCFU/ACFU: no UCFU descriptor was found. The located experiment is the ACFU
  4.2.3 scaffold at
  `G:/EnvironmentPortfolio/CompatibilityLabs/ACFUMelusinaUE58`. Its isolation
  contract is valid, but the Ascent Combat Framework vendor plugin/source is
  absent, so it cannot compile.
- F: was mounted but did not answer directory enumeration within the test
  window. It remains an unresolved archive location rather than negative proof.

Do not copy the binary Oceanology remnant, enable Oceanology, or add ACFU to
`BS_GodFile.uproject`. The next valid step is an isolated compile after the
real vendor packages are restored.

## Deterministic compatibility tooling

Added:

- `Tools/audit_oceanology_acfu_compat.py`
- `Tools/test_oceanology_acfu_compat.py`

The auditor is read-only and fail-closed. It distinguishes provenance, vendor
descriptor/archive presence, source/build metadata, binary-only remnants,
ACFU isolation, MelodiaCore dependencies, and permitted integration scope.

Result:

```text
python -B -m unittest Tools.test_oceanology_acfu_compat -v
Ran 3 tests — OK
```

Current evidence is written to
`Saved/Audit/oceanology_acfu_compat_20260826.json` and its Markdown companion.
The JSON result is `ready_for_live_integration=false` with blockers:

- `oceanology_vendor_descriptor_or_archive_missing`
- `acfu_vendor_source_plugin_missing`

## Melusina and MelodiaCore baseline

### Editor automation — PASS 14/14

| Prefix | Passed | Coverage |
| --- | ---: | --- |
| `Melodia.CoreRules.Rhythm` | 5/5 | rhythm rules, reactivity, execution gating, damage ordering, result payload |
| `Melodia.Integration.PresentationRhythm` | 1/1 | presentation grade calculation |
| `Melodia.RhythmCombat` | 2/2 | session lifecycle and grade boundaries |
| `Melodia.WaterGameplay` | 1/1 | water gameplay state/save model |
| `Melodia.Wiring` | 5/5 | battle UI construction, charts, mapping, Persona allowlist, stock contract |

These tests prove the current MelodiaCore contracts before vendor integration.
They do not prove Oceanology or ACFU coexistence because those plugins did not
load.

### Melusina_BP preflight — PASS

- Blueprint registry/fixture parity: 7 templates.
- Blueprint readiness inventory: 7 templates and 7 fixtures; live proof pending.
- Materialization preflight: 7 templates; no assets created.
- Puzzle → water → quest offline preconditions pass; live graph/save proof pending.
- Melusina skin topology contract: 7 checks pass.
- Melodia skill bridge: 7 checks pass.
- Native adapter contract passes.
- HUD single-writer source contract passes; live viewport proof remains pending.

### Existing headless harness findings

`Tools/test_e2e_melusina_release.py` had an unterminated mojibake token and
could not start. That syntax defect is repaired. The suite now runs 17 tests
and reports 15 passing, one failing, and one error:

- Failure: README uses `UE 5.8` but the harness requires the literal phrase
  `Unreal Engine`.
- Error: nested `Tools/test_melodia_mcp.py` exceeds the harness's 45-second
  timeout.

Two animation promotion guard fixtures also fail closed because their supplied
manifests do not satisfy live-promotion identity. This is expected guard
behavior, not an Oceanology/ACFU incompatibility.

`Tools/test_melodia_integration_map_contract.py` fails because its hard-coded
Melody Slime row counts no longer match current content. That drift needs an
owner decision before changing either the expected counts or the content.

### Live headless PIE — HOLD

The running shared editor reported four dirty UI packages and one errored
Blueprint:

- `WBP_MelodiaQuillDialog`
- `WBP_MelodiaQuillSelection`
- `WBP_MelodiaQuillChoiceEntry`
- `WBP_MelodiaRhythmHighway`
- errored: `WBP_MelodiaRhythmHighway`

No PIE session was started and none of those packages were saved or modified.
This preserves the owning UI lane's work and avoids producing false runtime
evidence from a known errored baseline.

### Unattended UE5.8 commandlet refresh — ENVIRONMENT HOLD

A fresh `UnrealEditor-Cmd.exe` run was started with `-Unattended`, `-NullRHI`,
and the targeted Melodia rhythm/water/wiring automation prefixes. The process
loaded project modules but never reached automation discovery. Its current log
is `Saved/Logs/BS_GodFile_3.log`.

The last startup evidence is:

```text
LogZenServiceInstance: Found environment variable UE-LocalDataCachePath=F:\UE_DDC
LogZenServiceInstance: Warning: Skipping local data cache path=F:\UE_DDC due to an invalid path
LogZenServiceInstance: Warning: Unable to determine a valid Zen data path
```

The log stopped advancing at that point and the bounded process was terminated.
This is an environment/startup failure caused by the unavailable F: DDC path,
not a Melusina, Blueprint, Oceanology, ACFU, or rhythm test failure. The earlier
14/14 editor-automation baseline remains the latest completed runtime-backed
automation evidence, but it was recorded without either vendor plugin loaded.

A second attempt used a process-only `UE-LocalDataCachePath` under
`Saved/DerivedDataCache/OceanologyCompat`. It did not emit a new log or reach
automation discovery within the bounded window and was terminated. This leaves
the headless gate on HOLD; it is not a passing or failing gameplay result. The
process-local override did not modify the machine-level environment.

## Integration boundaries

### Oceanology candidate seams

Safe to investigate after an isolated UE5.8 compile:

- ocean surface rendering and spectral wave presentation;
- buoyancy as an adapter beneath existing traversal/world rules;
- underwater post-process coexistence with the existing Melodia water layer;
- Niagara displacement/presentation that does not own gameplay state.

Forbidden:

- narrative, battle, rhythm, quest, inventory, or save authority;
- direct replacement of canonical water gameplay state without a migration;
- enabling in the live project before descriptor/source/version verification.

### ACFU candidate seam

The only approved experiment is the disposable Melusina character-base lab.
ACFU must not be enabled beside the stock turn-based JRPG authority in the live
project. Any useful component must first be proven in isolation and later
cherry-picked behind an existing Melodia interface; wholesale combat,
inventory, quest, or character authority adoption remains rejected.

## Exact continuation sequence

1. Finish/download Oceanology Expanded into
   `G:/EnvironmentPortfolio/Imports/Oceanology`, retaining its `.uplugin`,
   source, binaries, content, version metadata, and Fab provenance.
2. Restore ACFU source into the disposable lab only, under its expected
   `Plugins/AscentCombatFramework` path.
3. Re-run the compatibility auditor and require both vendor descriptors.
4. Compile each plugin in a separate UE5.8 compatibility host. Record the
   first compiler error without patching the live project.
5. Run an Oceanology-only water/underwater map and an ACFU-only Melusina spawn,
   animation, hair, damage-receive, and package test.
6. After the UI lane produces zero dirty packages and zero errored Blueprints,
   rerun the baseline Melusina PIE identity and rhythm tests.
7. Before the next unattended run, point `UE-LocalDataCachePath` at a verified
   writable local DDC for that process only; do not silently change the user's
   global environment or delete the existing cache configuration.
8. Only then propose a narrow live-game adapter. Do not enable either vendor
   plugin as a shortcut to proof.
