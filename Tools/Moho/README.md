# Moho Worker Scaffold

Moho is a planned authoring lane for the Melodia laptop worker. This folder is
scaffolding only: the repository does not currently contain a Moho plugin,
automation API, executable contract, or native Moho project format.

## Worker role

The laptop is a measured 16 GB worker-first machine:

- stage Moho source files and job manifests on `P:`;
- run one bounded asset job at a time;
- keep generated output outside the live Unreal `Content/` tree until reviewed;
- record hashes and job results for handoff;
- promote approved outputs through an explicit Git branch or asset-transfer
  process.

Do not treat a staged file as an Unreal asset, and do not invent a headless Moho
command until the installed Moho version and its supported automation surface
are verified.

## Planned layout

```text
Tools/Moho/
  README.md
  run_moho_worker.ps1
  jobs/       local, ignored job inputs and manifests
  output/     local, ignored generated candidates
```

The runner creates `jobs/` and `output/` when used. It currently performs only
safe staging and inventory checks; it does not launch Moho or modify Unreal.

## Next integration gate

Before adding real execution, document:

1. licensed Moho version and install path;
2. supported command-line, scripting, or UI automation entry point;
3. accepted source and export formats;
4. deterministic output and failure semantics;
5. review and Unreal handoff rules.