# LFS Cold Archive — S3 Glacier

Companion to [`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md). That doc explains why LFS storage
is metered and never shrinks on its own. This one is the runbook for the only lever that actually
moves the number: getting bulk binaries **out of LFS and into cold storage**.

---

## Why the archive is beside git, not under it

Git-LFS custom transfer agents to S3 exist, and Glacier looks like a cheap LFS backend. It is not
one. Glacier restore latency is milliseconds (Instant Retrieval) to 48 hours (Deep Archive), and an
LFS remote is hit by every `clone` and every `checkout`. A Glacier-backed LFS remote would hang the
first clone that touches an archived object.

The correct shape is a cold archive **outside** the repo, with this manifest — plain text, free to
store — committed inside it. The bytes live in S3; git keeps the pointer to them.

---

## Budget

Free tier is **10 GiB** LFS storage. Live payload at HEAD is **9.19 GB — 92%**.

| Path | Files | Size | Share |
|---|---|---|---|
| `Exports/PortfolioStages/*.blend` | 3 | **5,529 MB** | **60%** |
| `Content/Melodia/**` | 1,035 | 2,299 MB | 25% |
| `Content/Characters/**` | 71 | 448 MB | 5% |
| `Content/Surfaces_CC0/**` | 82 | 245 MB | 3% |
| `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26/` | 4 | 156 MB | 2% |

Three Blender portfolio-stage snapshots at ~1.8 GB each are 60% of the entire payload. They have
distinct OIDs, so they are genuinely different files — not duplicates — but `v16` and `v17` are
superseded by `v18`.

Archiving `v16` + `v17` + the CompatibilityLabs backup reclaims **3.65 GB**, taking the payload to
**5.54 GB (55%)**. That is the whole job.

> **Timing.** GitHub bills LFS storage for every object ever associated with the repo. Untracking
> does not refund immediately — storage drops only once the object is unreferenced **and the month
> rolls over**. Do this before month end or the saving lands a month late.

---

## Manifest

`oid` is the LFS object id, which **is** the SHA-256 of the file content — verify a restore by
hashing the download and comparing against this column. Bucket keys use the OID so an object is
self-identifying.

### Set A — superseded portfolio stages → Glacier Instant Retrieval

Instant Retrieval (~$0.005/GB-mo in `ca-central-1`, millisecond restore, 90-day minimum). These are
authored Blender scenes; if a stage needs reopening you want it back in seconds, not two days.

| File | Size (bytes) | SHA-256 (LFS oid) |
|---|---|---|
| `Exports/PortfolioStages/Melodia_Portfolio_Stage_v16_SIR_VISIBLE.blend` | 1,831,301,860 | `5514ddf36c328e47fd9abece07a22673605e83303b37c6098fe985bc7e3bde3a` |
| `Exports/PortfolioStages/Melodia_Portfolio_Stage_v17_SIR_VISIBLE.blend` | 1,830,602,679 | `a5b6b6a40544c167dcfec65b2cd9b4a409f8334c386a322e498d9dd82cd3d460` |

**Keep tracked:** `Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` (1,792,267,474 bytes, oid
`e8f3aebdb9525f51180b12d2483f4fa7c02f5edc050f1bc7ad0d6b4e29109264`) — current stage, stays in LFS.

### Set B — pre-integration backup → Glacier Deep Archive

Deep Archive (~$0.0018/GB-mo, 12–48 h restore, 180-day minimum). A dated backup tree of levels that
still exist live under `Content/`. Restoring it is a disaster-recovery event, not a workflow step.

| File | Size (bytes) | SHA-256 (LFS oid) |
|---|---|---|
| `.../WorldPartition_2026-08-02/ZenForestTest.umap` | 162,613,950 | `7e454cd237aa71bfd2751d31db1a36a177521ba8d9d75d4f76096534895ced4c` |
| `.../WorldPartition_2026-08-02/EnvSandbox/Environments/L_FallenMoon.umap` | 621,123 | `c858925170978117fb68f7e419325071e991f04531a7dbc8b8b5178a8f7866f6` |
| `.../WorldPartition_2026-08-02/EnvSandbox/Environments/L_KaleidoNave.umap` | 298,318 | `a8d5000d7bb3b3405cfcd8aa25e67359bb98168962e3b422a6f970038ece7aaa` |
| `.../WorldPartition_2026-08-02/Melodia/Levels/Opening/L_MelusinaMorning.umap` | 166,819 | `9f8e9e0ca9666a0a1bf681700d0272c2dba2bf39a5ea3e8ae06ef21f279eb242` |

All paths under `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26/`.

> **Bundle Set B, do not upload it file-by-file.** Every Glacier class bills a **128 KB minimum per
> object**. Three of these four files are under 128 KB, so uploading them individually bills each at
> 128 KB. `tar` the set into one object. The Set A blends are ~1.8 GB each and are fine as-is. Any
> future `.uasset` sweep must be bundled the same way.

---

## Auth

The `default` profile is session-based (`login_session = arn:aws:iam::322037002075:root`) and its
session expires. When any command below returns *"Your session has expired"*, re-auth:

```bash
aws login
```

Note the stale static keys in `~/.aws/credentials` under `[default]` **shadow** the login session —
that is why an expired session reports `InvalidClientTokenId` rather than a clean expiry message.
Clearing that stanza makes the failure mode legible.

The `bedrock` profile (`melodia-bedrock`) is scoped to Bedrock and cannot write the archive; do not
widen it. **Region: `ca-central-1`** — matches the configured default and keeps assets in Canada.

Gate before running anything below:

```bash
aws sts get-caller-identity && aws s3 ls s3://<bucket>
```

---

## Runbook

### 1. Upload Set A (Instant Retrieval)

```bash
aws s3 cp Exports/PortfolioStages/Melodia_Portfolio_Stage_v16_SIR_VISIBLE.blend s3://<bucket>/portfolio-stages/5514ddf36c328e47fd9abece07a22673605e83303b37c6098fe985bc7e3bde3a.blend --storage-class GLACIER_IR
```

```bash
aws s3 cp Exports/PortfolioStages/Melodia_Portfolio_Stage_v17_SIR_VISIBLE.blend s3://<bucket>/portfolio-stages/a5b6b6a40544c167dcfec65b2cd9b4a409f8334c386a322e498d9dd82cd3d460.blend --storage-class GLACIER_IR
```

### 2. Bundle and upload Set B (Deep Archive)

```bash
tar -czf /tmp/preintegration-backup-2026-07-26.tar.gz CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26/
```

```bash
aws s3 cp /tmp/preintegration-backup-2026-07-26.tar.gz s3://<bucket>/backups/preintegration-backup-2026-07-26.tar.gz --storage-class DEEP_ARCHIVE
```

### 3. Verify the restore path BEFORE untracking anything

Download one archived blend and confirm its hash matches the manifest. **This gate is not optional —
it is the only thing standing between an archive and a deletion.**

```bash
aws s3 cp s3://<bucket>/portfolio-stages/5514ddf36c328e47fd9abece07a22673605e83303b37c6098fe985bc7e3bde3a.blend /tmp/verify.blend && sha256sum /tmp/verify.blend
```

Expected: `5514ddf36c328e47fd9abece07a22673605e83303b37c6098fe985bc7e3bde3a`.

### 4. Untrack — only after step 3 passes

`--cached` leaves the files on local disk; only the tracking is removed.

```bash
git rm --cached Exports/PortfolioStages/Melodia_Portfolio_Stage_v16_SIR_VISIBLE.blend Exports/PortfolioStages/Melodia_Portfolio_Stage_v17_SIR_VISIBLE.blend
```

```bash
git rm -r --cached CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26/
```

Add both paths to `.gitignore` — a **never-touch file, so get owner approval for that edit** — then
commit as one change referencing this manifest.

### 5. Confirm the payload dropped

```bash
git lfs ls-files -s
```

Expect ~5.5 GB, down from 9.19 GB.

---

## Local disk (separate from billing)

`.git/lfs` holds **31 GB**; `git lfs prune --dry-run` reports 13,244 objects with 11,571 retained, so
roughly 1,673 are prunable. This reclaims **local disk only and changes no bill.**

`PruneVerifyRemoteAlways` is `false` in this repo, so prune would delete without checking the remote
holds a copy. Always pass `--verify-remote`:

```bash
git lfs prune --verify-remote
```

---

## What this unblocks

`origin/feature/repo-lockin-20260813` is held unmerged because its `.gitignore` carve-out starts
tracking **1,456 new LFS objects totalling 2.63 GB**:

| Step | Payload | % of 10 GiB |
|---|---|---|
| now | 9.19 GB | 92% |
| + `repo-lockin` merge | 11.82 GB | **118% — overage** |
| − this archive | 8.13 GB | 81% |
| + Batch G ORM textures (361 MB) | 8.49 GB | 85% |

Archive first, then merge `repo-lockin`, then commit Batch G, then push.
