# Les Petits Accordeurs — Gameplay & Maison L'Accordeur Proposal

**Status:** design exploration; NOT an implemented UE feature. All mechanics marked PENDING.

## Design goal
Turn small acts of maintenance into visible, musical world care. Avoid a separate collection game, resource economy, quest manager, or save architecture. Keep each interaction short, characterful and reversible during early prototypes.

## Candidate discovery -> care -> resonance loop (PENDING)
1. Player discovers a small environmental problem through existing exploration or QuillScript event.
2. An Accordeur can appear as a contextual companion, never spawning an unauthorized quest branch.
3. Player performs a short musical phrase/puzzle using existing music-as-key and input systems.
4. Accordeur performs one distinctive repair animation.
5. Existing narrative/save authorities record an idempotent state transition; visual world repair is derived from it.
6. Later visits to Maison L'Accordeur reflect the recorded state with ambient stories/props.

## Seven proposed interaction verbs
| ID | Character | Prototype action | Trigger authority | Proof scene |
|----|-----------|------------------|------------------|-------------|
| ACC_COMMITTE | Monsieur Committe | Reveal archived score fragment | QuillScript flag | library ledger |
| ACC_MERGE | Mlle. Merge | Link two disconnected tone nodes | existing music puzzle success | broken string |
| ACC_CACHE | Petit Cache | Return a misplaced star-shell | quest-owned item state | quiet nook |
| ACC_BUILD | Le Build | Repair bridge plank / resonance perch | music-as-key result | damaged walkway |
| ACC_LFS | Madame L.F.S. | Hand out a needed item prop | existing inventory authority | quartermaster desk |
| ACC_REBASE | Monsieur Rebase | Reveal already unlocked route map | traversal + narrative flags | compass pedestal |
| ACC_BOT | Le Bot | Deliver an approved narrative message | QuillScript event | mail dispatch |

**MVP choose only ACC_BUILD.** Gameplay no earlier than its approved mesh and cosmetic idle.

## Maison L'Accordeur layout (PENDING)
One small shared workshop/world hub; no new level in MVP. Propose the following visual stations: archive, seamstress table, keepsake nook, miniature forge/workbench, supply closet, cartography table, dispatch shelf. Existing environment procedural/PCG tools can dress the space after art approval.

The hub **is not** authority for quest state or inventory. Stations are derived views of the existing state. Passive idle interactions are local cosmetic animation, not autonomous gameplay logic.

## Save and narrative integration constraints
- **Source of truth:** existing QuillScript narrative notifications and actual save/persistence owner from main project README; do not invent a second Accordeur state database.
- Stable semantic identifiers 'ACC_*' are design IDs, not promised runtime assets.
- UI requests must pass the existing single-writer UI bridge.
- Repair effects flow through approved material/PCG/Niagara owners with explicit event source.
- Repeated interaction and restart must be idempotent. Verify: before -> trigger -> save -> relaunch -> same repaired state, no duplicate rewards.
- Companion movement, following, and service dispatch should reuse relevant existing AI/companion patterns ONLY after audit, not copy the Melusina pawn or introduce a global manager.

## Phase gates
**G0 Source:** exact approved crop, proportional silhouette, clear source identity, no Atelier Magique contamination.
**G1 Mesh:** GLB parses, oriented upright, true scale set, all limbs separated where intended, reasonable material slots; topology classified PROXY.
**G2 Rig/anim:** neutral idle + role action; deformation proof; no bad seams.
**G3 Sandbox:** UE 5.8 isolated character asset and one interaction in designated test surface, never live level mutation.
**G4 Persistence:** single existing-authority state transition survives save/reload; screenshots/logs.
**G5 Presentation:** user signs off silhouette, shaders and readability at actual camera distance.

## Not in MVP
Seven finished rigs, autonomous chore dispatch, online agents driving NPCs, furniture customization, a new quest database, runtime inventory override, all Monolith puzzle mechanics, full soundtrack / voiceover.

## Dependencies and handoff
Read CURRENT_STATE.md for editor ownership before any UE work. Do not touch Melusina's animation/convergence, current level, or open asset packages. First task is mesh-source review and branch-local documentation, not a production Unreal edit.
