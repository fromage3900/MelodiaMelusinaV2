# P0 / Sea Above + Runtime-Animation Goals LEDGER (2026-10-03, read-only)
Closed, NOT listed: WASD, bow, damage, gameplay loop, damage ladder, WASD proof, possessed-PIE probe (CURRENT_STATE 2026-10-01 correction).
Sources: CURRENT_STATE.md (mtime 10-02 20:04), memory project-p0-closeout-handoff-20261002.md, .hermes/plans/2026-10-01*, session facts.

| Goal | Status | Evidence | Blocker | Who | Next action |
|---|---|---|---|---|---|
| Glide polish felt in PIE (soft sink, floatier) | partial | MelodiaTraversalComponent.h/.cpp uncommitted; compiled | Untested; BP_MelusinaJRPGCharacter CDO may override | AGENT | PIE glide in MelodiaIntegrationMap; inspect CDO overrides |
| Left eye-detach intermittent (EyeIrises/EyeLashes socket->None) | unmet | handoff item 2 | No repro yet | AGENT | PIE repro, log attach events on socket |
| Mesh-variable fix on BP_MelusinaJRPGCharacter | partial | handoff item 3 (K2Node_VariableGet_31 -> DynamicCast_0) | Not re-verified on main | AGENT | get_graph_fingerprint on that node via Monolith |
| Piano key run -> water -> flower path | unmet | key->flower proven in PIE; water link not built | Not built | AGENT | Build water-to-flower driver in L_MelusinaMorning |
| Key-run completion -> Quantum-draw link | unmet | session facts; not built | Not built | AGENT | Add completion event; hook to Quantum draw |
| Piano fixes + cymatics additive pulse committed | partial | uncommitted PCGPianoKeyboard.*, MelodiaCymaticsWriterSubsystem.* | Git law: owner permission to commit | OWNER | Approve commit plan for piano/cymatics/glide set |
| Sir Melodious shoulder perch | unmet | handoff item 2; no perch exists | Design decision: socket vs BP_SirPerch | OWNER (decide), AGENT (build) | Owner picks socket or placed perch |
| Hair offset | unmet | handoff item 4; measured rigid | Needs owner reference frame | OWNER | Owner supplies reference frame/screenshot |
| Choral Sheep tail-wag / ear-flick visual | partial | .hermes 2026-10-01 sheep capstone plan | Visual check in PIE pending | AGENT | PIE check tail/ear; follow capstone plan |
| Melody-slime dungeon loop | unmet | handoff item 2 | Not run in PIE | AGENT | Run slime loop in PIE; log result |
| Oceanology biolum -> MPC_Melodia_Palette | unmet | session facts | Not wired | AGENT | Wire biolum params to MPC via material instance |
| Bell Tree Listening Quill in PIE | partial | compiled only | Not played | AGENT | Trigger Quill in PIE, verify exactly-once |
| Morning zombie actors | unmet | handoff item 5 | Perforce down | OWNER | Owner restores P4, then remove actors |
| Closed-editor 5.8 build (party bootstrap UNBUILT) | partial | CURRENT_STATE top: only open technical item | Editor must be closed | OWNER | Close editor; run full Build.bat |
| Packaged build + 60fps + showcase gates | unmet | CURRENT_STATE/handoff | Needs build first | OWNER+AGENT | After full build, package and profile fps |
| Restore RiderLink in BS_GodFile.uproject | unmet | git status: uproject modified | Owner-run | OWNER | Owner restores RiderLink entry |
| Delete 24 stale piano-key external-actor files | unmet | session facts | Owner-run | OWNER | Owner deletes files, saves level |
| Remote merged-branch deletion | unmet | session facts | Owner-run | OWNER | Owner deletes merged remote branches |

## Docs vs session facts (disagreements)
- Handoff memo body says main tree sits on docs/honcho-discord-sync, local main stale; its own UPDATE + session facts say main == origin 0b1c37a49. Trust the update.
- CURRENT_STATE 2026-10-01 entries say "main at 21edf3950", party bootstrap UNBUILT; the PR 405 slice since built Succeeded (worktree, now removed) - UNBUILT status for main is unverified.
- Handoff step 1 says "worktree/partial checkout" blocked playtests; worktree is removed, so playtests are now unblocked in main tree.
- CURRENT_STATE (389 KB) is huge and mixes stale pre-correction claims; read only its top block.

## Close-out order
1. Owner: restore RiderLink, close editor, full Build.bat (unblocks everything).
2. Agent: PIE glide feel + CDO override check + Mesh-variable re-verify.
3. Agent: eye-detach repro, sheep visuals, Bell Tree Quill, slime loop in one PIE session.
4. Agent: build water->flower and key-run completion->Quantum-draw; wire biolum to MPC.
5. Owner: decide Sir perch, give hair frame, approve commit of piano/cymatics/glide.
6. Owner: delete stale files/branches, fix P4 zombies; then package + 60fps.
