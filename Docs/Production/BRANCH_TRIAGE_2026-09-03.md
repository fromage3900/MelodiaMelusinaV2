# Git Branch Triage — 2026-09-03
> **Total branches:** 70 (excluding main)
> **Goal:** Triage all branches into main in committed, isolated, healthy merged batches.

---

## Triage Categories

| Category | Count | Action |
|----------|-------|--------|
| **A. Recovery/Snapshot** | 4 | DELETE — temporary backups |
| **B. Temp/Merge** | 2 | DELETE — scratch branches |
| **C. Integrate (merge-train)** | 9 | MERGE in order (B00→B08) |
| **D. Docs-only** | 7 | SQUASH MERGE — docs don't need full history |
| **E. Feature (shipped)** | 9 | MERGE via PR — proper review |
| **F. Feat (WIP)** | 5 | EVALUATE — some may be dead |
| **G. Agent branches** | 28 | TRIAGE per-agent — many are dead |
| **H. PR** | 1 | MERGE if not already |
| **I. Safety** | 1 | DELETE — pre-sync backup |

---

## Branch Inventory

### A. Recovery/Snapshot (DELETE)
| Branch | Last Commit | Action |
|--------|-------------|--------|
| `recovery/melodia-main-sync-20260811` | content: stage post-snapshot leftovers | DELETE |
| `recovery/snapshot-20260903` | snapshot: full working tree at a8957b41 | DELETE |
| `recovery/snapshot-20260903-1840` | snapshot: BS_GodFile working tree at 19c1 | DELETE |
| `recovery/worktree-save-20260903` | (unknown) | DELETE |

### B. Temp/Merge (DELETE)
| Branch | Last Commit | Action |
|--------|-------------|--------|
| `temp-merge` | (unknown) | DELETE |
| `temp_clean` | feat(cymatics): close out material wiring | DELETE |

### C. Integrate (MERGE IN ORDER)
| Branch | Ahead | Behind | Last Commit |
|--------|-------|--------|-------------|
| `integrate/2026-09-02-b00-governance` | 1 | 456 | merge-train B00: governance config |
| `integrate/2026-09-02-b01-docs-fixtures` | 3 | 456 | merge-train B01: docs fixtures |
| `integrate/2026-09-02-b02-runtime-source` | 5 | 456 | merge-train B02: first-party runtime |
| `integrate/2026-09-02-b03-first-party-plugins` | 7 | 456 | merge-train B03: first-party plugins |
| `integrate/2026-09-02-b04-houdini-engine` | 9 | 456 | merge-train B04: HoudiniEngine |
| `integrate/2026-09-02-b05-authoring-toolchain` | 11 | 456 | merge-train B05: authoring toolchain |
| `integrate/2026-09-02-b06-character-gameplay-content` | 13 | 456 | merge-train B06: character gameplay |
| `integrate/2026-09-02-b07-remaining-content` | 15 | 456 | merge-train B07: remaining content |
| `integrate/2026-09-02-b08-recovered-residue` | 17 | 456 | merge-train B08: recovered residue |

### D. Docs-Only (SQUASH MERGE)
| Branch | Ahead | Behind | Last Commit |
|--------|-------|--------|-------------|
| `docs/2026-08-29-character-p1-p2-canon-audit` | 1 | 464 | docs: capture trench sweep 04 |
| `docs/2026-08-31-mara-instrument-cymatics-plan` | 1 | 456 | docs: Mara instrument and cymatics |
| `docs/2026-09-02-endless-journey-paradigm` | 368 | 456 | docs(frontdoor): bound test evidence |
| `docs/monolith-concept-art-backlog-2026-08-26` | 3 | 514 | docs(sea-above): tonight execution |
| `docs/p1-monolith-character-concepts-2026-08-28` | ? | ? | (unknown) |
| `docs/sea-above-system-shader-breakdowns-2026-08-26` | ? | ? | (unknown) |
| `docs/toolchain-consolidation-2026-08-31` | 39 | 456 | docs: index Mara Elletra visual |

### E. Feature (MERGE VIA PR)
| Branch | Ahead | Behind | Last Commit |
|--------|-------|--------|-------------|
| `feature/p0-closeout-2026-09-02` | 6 | 680 | docs: complete verified work log |
| `feature/p0-phase1-allowlist-quill-trigger` | ? | ? | (unknown) |
| `feature/cymatics-closeout-main` | ? | ? | (unknown) |
| `feature/echo-topo-chapter2` | 0 | 643 | feat(echo-topo): topological Echo gate |
| `feature/credits-20260813` | 0 | 640 | ci: run credits_gate.py |
| `feature/repo-lockin-20260813` | 9 | 643 | chore: gitignore venv-guardrails |
| `feature/sea-above-choralsheep-20260826` | ? | ? | (unknown) |
| `feature/zenforest-glam-headless` | ? | ? | (unknown) |
| `feature/claireon-test-20260819` | 0 | 638 | docs: session handoff + README |

### F. Feat (EVALUATE)
| Branch | Ahead | Behind | Last Commit |
|--------|-------|--------|-------------|
| `feat/2026-09-02-front-door-cymatic-sanctuary` | 369 | 456 | docs: carry second-workstation onboarding |
| `feat/2026-09-02-github-pages-atmosphere` | 375 | 456 | feat(site): wise Three.js — atmosphere |
| `feat/2026-09-02-melodia-folio-threejs` | 361 | 456 | docs(ui): define 3D Folio |
| `feat/2026-09-02-music-key-threejs` | 360 | 456 | feat(web): add Mara-style Folio viewer |
| `feat/2026-09-02-runtime-persistence-closure` | 13 | 456 | fix(save): reject inconsistent equipped |

### G. Agent Branches (TRIAGE)
| Agent | Branches |
|-------|----------|
| **cursor** | 11 branches (git-health, docs, phone-party, etc.) |
| **copilot** | 7 branches (fix-runners, git-status, etc.) |
| **claude** | 2 branches (magical-williamson, cymatic-ecology) |
| **codex** | 4 branches (p0-closeout, weapon-gallery, perforce) |

### H. PR (MERGE)
| Branch | Ahead | Behind | Last Commit |
|--------|-------|--------|-------------|
| `pr/melusina-v22-sync` | 0 | 526 | fix(melusina): sync body MIs to v22 |

### I. Safety (DELETE)
| Branch | Last Commit | Action |
|--------|-------------|--------|
| `safety/pre-g-sync-20260821` | (unknown) | DELETE |

---

## Execution Plan

### Phase 1: Delete Dead Branches
1. Delete all `recovery/` branches
2. Delete all `temp*` branches
3. Delete `safety/`
4. Delete agent branches that are clearly dead

### Phase 2: Merge Integrate Batch
1. Merge B00→main, then B01→main, ... B08→main
2. Delete integrate branches after merge

### Phase 3: Squash Merge Docs
1. Squash merge each docs branch
2. Delete docs branches after merge

### Phase 4: Merge Features
1. Create PRs for feature branches
2. Merge after review

### Phase 5: Evaluate Feat
1. Check if feat branches have unique content
2. Merge or delete

---

*Created: 2026-09-03 | Status: IN PROGRESS*
