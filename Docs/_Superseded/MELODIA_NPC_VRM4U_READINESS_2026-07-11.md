# Melodia NPC and VRM4U Readiness - 2026-07-11

## Current State

The NPC system is a **prepared data and pipeline lane**, not a runtime-complete
feature yet.

- `UMelodiaNPCDataAsset` has a rich definition contract: identity, mesh,
  animation personality, behavior, interaction, battle mapping, and affinity
  rewards.
- GMM defines 11 planned NPC variants across Sakura Dreamer, Cosmic Weaver,
  and Mirage Dancer archetypes. Their battle-stat variants generate correctly.
- The NPC audit dispatcher and its no-editor coverage are now valid.
- The repository currently contains **11 source manifests (`.vrm.json`) but no
  actual `.vrm` source files**.
- No VRM4U plugin directory or enabled-plugin declaration was found by the
  read-only audit.
- Every registry record is marked `imported=false`; no generated NPC Blueprint
  has been evidenced in the map.

Therefore, do not run the full `generate_npc_batch()` pipeline yet. It would
produce misleading failures and risks a large asset churn during gameplay
polish.

## Minimum Viable NPC Slice

Use **one stationary dialogue NPC**, not a shop, quest system, or ten-character
population. Recommended first identity: `SD_02_PetalPriestess` because its
planned role is guiding the player toward the first encounter.

1. Obtain a local, release-cleared `.vrm` source and record its author,
   license, and attribution in `vrm_registry.json`.
2. Install/enable a UE 5.8-compatible VRM4U build, restart the editor, and
   import only this one model under `/Game/NPCs/Imported/SakuraDreamer/`.
3. Make one `BP_NPC_SD_02_PetalPriestess` from the imported mesh with an idle
   animation, collision, and a short interaction radius.
4. Place it near the `ZenForestTest` approach route. Its feedback loop is:
   approach -> prompt -> one or two lines -> clear direction to encounter.
5. Only after that works, allow the NPC to initiate a battle handoff using an
   existing `FMelodiaEnemyDef`. Do not use the generated NPC battle catalog as
   runtime C++ source until a deliberate data-import path exists.
6. Run the editor NPC audit after import, then confirm dialogue, prompt,
   encounter direction, and return-to-exploration in PIE.

## Feedback Loops Worth Finalizing

| Loop | Current state | Next refinement |
| --- | --- | --- |
| Exploration -> encounter | Working trigger proof | Add a landmark/readable enemy silhouette and one approach cue. |
| Command -> rhythm -> result | Mechanically ready; latest feedback code awaits rebuild | Use the established HUD event pass for selected Skill, Perfect, Break, and victory punctuation. |
| Enemy turn -> recovery | Functional, but presentation-light | Add one readable intent/telegraph beat before damage. |
| Victory -> exploration | Functional | Add a short result acknowledgement and remove battle UI cleanly. |
| NPC -> player direction | Data only | Implement the one-NPC dialogue proof above. |
| NPC -> progression | Planned only | Do not add quests, shops, affinity, or schedules before the dialogue proof is fun. |
| Songcraft -> authored chart | Rules and recipes exist | Add UDataAsset chart loading only after the first chart feels good in play. |
| Audio -> action feedback | Grade tones/metronome exist | Map one shared encounter BGM cue before capture; enemy-specific music can wait. |

## PC and Mobile Boundary

This NPC plan is Windows desktop-first. VRM spring bones, cloth, Lumen, and
high-detail MToon materials should be profiled as a separate mobile track.
Do not use the NPC pipeline as evidence that mobile gameplay is ready.

## Acceptance Evidence

- The read-only GMM suite remains green.
- One actual `.vrm` source has release-cleared provenance.
- VRM4U is enabled and its editor import completes once.
- One placed NPC has visible idle, prompt, dialogue, and a reliable return to
  player control.
- The existing Zen battle loop still completes after the NPC is present.
