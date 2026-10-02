# Checkpoint: Realm MCP Provider

**Date:** 2026-05-29
**Branch:** plugin `pi/harness`; inso `main`
**Summary:** Realm-declared MCP servers are now first-class OMP MCP capability providers. `registerRealmMCPProvider()` registers `ueRealm.mcp` as provider `inso-realms` before OMP starts, so the Realm owns the active `ue-editor` MCP source and shadows same-named user config without writing `~/.omp/agent/mcp.json`.

## Files Changed

### Inso Realm MCP work
- `Tools/inso/packages/realm-sdk/src/mcp-provider.ts`
- `Tools/inso/packages/realm-sdk/src/index.ts`
- `Tools/inso/src/cli.ts`
- `Tools/inso/extensions/ue/realm.ts`
- `Tools/inso/CLAUDE.md`

### Existing working-tree changes present during checkpoint
- `Tools/inso/docs/design/00-mental-model.html`
- `Tools/inso/docs/design/01-consumer-contract.md`
- `Tools/inso/omp/packages/coding-agent/src/main.ts`
- `Tools/inso/omp/packages/coding-agent/src/modes/utils/ui-helpers.ts`
- `Tools/inso/omp/packages/utils/src/dirs.ts`

### Checkpoint docs
- `docs/checkpoints/2026-05-29_realm-mcp-provider.md`
- `docs/handoff.md`

## What's Working

- **Realm-owned MCP provider** — `registerRealmMCPProvider()` exposes Realm MCP declarations to OMP's MCP layer as provider `inso-realms`, with priority above normal config providers.
- **No `mcp.json` mutation** — Inso CLI registers `ueRealm.mcp` before OMP startup; `~/.omp/agent/mcp.json` is no longer the UE Realm source of truth. A stale/user `ue-editor` entry is shadowed rather than connected twice.
- **Bearer auth carried by realm** — `ueRealm.mcp` supplies the local `Authorization: Bearer` header from `UE_MCP_AUTH_TOKEN`, falling back to the local dev token for blank/unset values.
- **Verified MCP resolution** — capability load shows `ue-editor` from `inso-realms` active and the user/native `ue-editor` shadowed.
- **Verified MCP connection** — `discoverAndLoadMCPTools()` connected to `ue-editor` and `node_repl`, loaded 118 tools total, and reported no errors.

## What's Not Working / Known Issues

- **WARNING — secret material in capability data:** `UE_MCP_AUTH_TOKEN` is materialized into the Realm MCP `headers` object. Avoid dumping raw MCP server configs in diagnostics unless Authorization headers are redacted.
- **NOTE — pre-existing docs/design changes:** `Tools/inso/docs/design/00-mental-model.html` has a large pre-existing diff; it was not overwritten during this checkpoint.

## Review Findings

### Code Review

- **CRITICAL fixed:** blank `UE_MCP_AUTH_TOKEN` previously disabled the bearer header; fixed by trimming and falling back to `dev-mcp-token-local-only`.
- **WARNING fixed:** Realm MCP `SourceMeta.providerName` now records `Inso Realms`.
- **WARNING fixed:** repeat provider registration now appends unique realm objects to a mutable provider state instead of silently ignoring later calls.
- **WARNING fixed:** provider state is recorded only after `registerProvider()` succeeds.
- **WARNING fixed:** unused startup `ping()` in UE realm setup was removed.
- **WARNING fixed:** `RealmMCPProviderOptions` is exported from the SDK barrel.
- **NOTE addressed:** default priority `110` is now documented as intentionally above normal OMP/user/project config providers.

### Documentation

- Updated this checkpoint with the new Realm-owned MCP source-of-truth flow.
- Updated `docs/handoff.md` to replace stale `~/.omp/agent/mcp.json` source-of-truth language with the `ueRealm.mcp` → `inso-realms` provider flow.
- Updated `Tools/inso/CLAUDE.md` with the new Realm MCP registration flow.
- Deferred edits to `Tools/inso/docs/design/00-mental-model.html` because it already contains a large pre-existing working-tree diff.

### Performance / GAS / Network Review

- **CRITICAL:** None.
- **WARNING fixed:** repeated provider registration no longer silently drops later realms.
- **WARNING noted:** raw Authorization header is still present in capability data; redaction should be audited before exposing MCP config diagnostics.
- **WARNING fixed:** blank token fallback and unused startup ping were addressed.
- **WARNING fixed:** CLI `--extension` and `--plugin-dir` injection is now idempotent for matching resolved paths.
- **NOTE:** provider load overhead is negligible for the current UE realm; duplicate MCP server names inside a realm tree are skipped with a warning.

## Next Steps

1. Audit OMP capability/MCP diagnostics for Authorization header redaction before using non-dev MCP tokens.
2. Update targeted sections of `Tools/inso/docs/design/00-mental-model.html` to fully reflect Realm-owned MCP, taking care not to overwrite the existing design-doc diff.
3. Continue Block 3: compose `acfRealm` into the UE realm and add the ACF-specific commands/catalog entries.
