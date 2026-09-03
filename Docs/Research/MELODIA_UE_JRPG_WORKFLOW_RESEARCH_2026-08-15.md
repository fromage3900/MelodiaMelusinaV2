# Melodia UE/JRPG Workflow Research Checkpoint

**Date:** 2026-08-15 UTC
**Owner:** Codex integration lane
**Status:** Research and handoff checkpoint; no editor assets, V2 meshes, ABP, KawaiiPhysics graphs, materials, or `_TASK_QUEUE.md` were mutated by this checkpoint.

## Executive finding

The most durable indie-AAA workflow is a small, repeatable content loop:

```text
stable ID + data definition
        -> thin Blueprint presentation/forwarder
        -> one native authority/subsystem
        -> disposable fixture map
        -> editor compile/readback
        -> packaged/Gauntlet smoke
        -> evidence envelope + promotion
```

Melodia already has the right shape in several places: T3D safe-wire postconditions,
contract suites, a canonical integration map, explicit capability contracts, and a
single intended narrative/save seam. The current risk is not lack of future systems;
it is allowing unproven child BPs, duplicate authorities, or editor-only success to
become the foundation for future content.

## Universal UE workflow to adopt

1. **One authority per mutable concern.** C++/subsystems own battle, traversal,
   narrative/save, inventory, and rewards. BPs bind definitions, expose presentation,
   and forward requests. A BP must not silently grant a capability, award an item, or
   create a second save record.
2. **Stable IDs and hierarchical tags.** Every skill, enemy, encounter, item, recipe,
   gathering node, portal, challenge, and state anchor receives a durable content ID.
   Tags describe capability, context, state, event, and cosmetic feedback. Avoid map
   strings and display names as runtime identity.
3. **Data-driven content.** Use DataAssets/DataTables for definitions and tuning; keep
   code responsible for validation, transactions, and authority. This makes balance
   and content growth safe without multiplying bespoke graphs.
4. **Thin, composable BPs.** A content BP should mostly bind a definition, visual
   assets, prompt/presentation hooks, and the authority request. Do not generate a new
   authority subsystem for every skill or enemy.
5. **Fixture-first development.** Every family gets one disposable fixture with a
   success path, failure/abort path, reset, and save/load boundary. The integration map
   is an integration proof map; it is not a substitute for the player-facing golden
   route.
6. **Symmetric proof.** Run the same contract in the editor and Development package.
   Use Automation/Functional Tests for content and gameplay checks, Gauntlet for
   packaged sessions and multi-process roles, and BuildGraph for the dependency graph.
7. **Evidence before promotion.** Record the asset path, source/content revision,
   request ID, pre-edit fingerprint, post-edit fingerprint, compile result, fixture
   result, and package result. A disk `.uasset` is not runtime proof.
8. **Reversible ownership.** One writer per asset, one scoped commit per lane, no
   reset/checkout recovery, and no bulk T3D mutation. Keep derived data out of Git and
   use a shared DDC when the team grows.
9. **Visuals are observers.** Niagara, materials, animation, and impact polish should
   observe typed gameplay events or Gameplay Cues. They must not become the source of
   damage, reward, traversal, or persistence truth.
10. **Scale the content, not the machinery.** Prove one complete skill, enemy,
    encounter, gathering interaction, portal, and save/resume route before expanding
    the catalog.

## Architecture recommendations for Melodia

### Capability and outfit/form seam

Treat a Resonant Form as a capability provider, not as a second movement authority:

```text
Wardrobe/Form provider -> read-only capability snapshot
Narrative/progression  -> unlock and persistence truth
Capability gate        -> allowed/blocked/preview-only decision
Traversal/interaction   -> owns the state transition
BP/UI/VFX               -> presents the decision and observes the result
```

The gate should evaluate capability, context, progression, region, traversal mode,
and snapshot freshness. It should fail closed, return a typed reason, and never cache
an allow across a load or context transition.

### Gathering and crafting vertical slice

The next durable family should be a single gathering node, not a large inventory
rewrite:

```text
GatheringNodeDefinition
  node_id, required_capability, item_id, quantity_rule, respawn_rule, seed
        -> interaction request (request_id, player, node_id, context)
        -> authority validates and commits inventory transaction
        -> typed item-gained event
        -> Niagara/UI/audio observer
        -> idempotent save boundary
```

Crafting consumes recipe definitions and inventory transactions. The presentation BP
can show a prompt and a result, but cannot directly increment a count. Every operation
needs an attempt ID and a repeat/reset test.

### Combat and impact polish

Keep the stock encounter/battle authority as the source of truth. Add a typed impact
event with damage/result context, then let Gameplay Cues/Niagara/animation observe it.
This gives Melusina polished hit feedback without coupling VFX to the battle result.
Enemy definitions should expose telegraph, hit, break, defeat, loot, and encounter IDs;
the enemy BP owns presentation only.

### Portal, traversal, and state

Portals should request travel with destination key, spawn tag, capability decision,
save-before-travel result, and input restoration. State anchors should use one stable
key through the canonical narrative/save path. No map-local boolean should be the only
record of a quest, unlock, reward, or defeated boss.

## Infinity Nikki lens translated into Melodia

This is a design translation, not a claim about private Infinity Nikki implementation.
Public official material describes an open-world dress-up loop where ability outfits
change traversal and interaction, gathered materials feed crafting, and home systems
extend the same ability/content loop.

| Publicly observable pattern | Melodia translation | Required contract |
| --- | --- | --- |
| Ability outfits unlock movement/interaction verbs | Resonant Forms provide Glide, Water Listening, Echo Reveal, Petal Clear, and later compound forms | Read-only capability snapshot + typed gate reason |
| Gathering is a world activity with many small discoveries | Gatherable node family with stable node/item IDs and deterministic respawn | Request/transaction/idempotency fixture |
| Materials eventually become crafted outfits/items | Recipe definition consumes inventory and produces a reward through one authority | Item/recipe DataAssets + save boundary |
| Outfit setup changes the active action set | Form selection changes capability presentation, not campaign truth | Wardrobe provider + traversal authority split |
| Home/decorating extends the loop | Optional Melodia hub/home becomes a P2 composition layer | Shareable definition data, no new save authority |
| Photo/co-op/challenge modes reuse world content | World challenges and snapshot/photo objectives consume the same event contracts | Challenge attempt/complete/reward transaction |
| Frequent updates add content without replacing the core loop | New forms, enemies, recipes, nodes, portals, and challenges should be data additions | L0-L4 readiness manifest and package proof |

The important design constraint is to borrow the *content grammar*, not the monetization
model. Core Melodia progression should not depend on gacha or a second currency system.

## Public UE and GitHub resources reviewed

### Official Epic resources

| Resource | What to borrow | Melodia use |
| --- | --- | --- |
| [Gameplay Ability System](https://dev.epicgames.com/documentation/en-us/unreal-engine/understanding-the-unreal-engine-gameplay-ability-system) | Abilities as self-contained actions, tags, attributes, effects, cooldown/cost seams, and cosmetic Gameplay Cues | Future skill execution and typed impact presentation; keep stock battle result authoritative |
| [Gameplay Tags](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-gameplay-tags-in-unreal-engine) | Hierarchical labels and restricted/tag-dictionary discipline | Capability, context, event, state, and `GameplayCue.*` namespaces |
| [Lyra abilities](https://dev.epicgames.com/documentation/en-us/unreal-engine/abilities-in-lyra-in-unreal-engine) | Data assets for ability sets and tag relationships that mediate blocking/canceling | Replace ad-hoc skill capability checks with a versioned relationship asset later |
| [Lyra interaction system](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-interaction-system-in-unreal-engine) | Interaction queries plus a single interaction ability/event route | Gathering, portal, and challenge prompts |
| [Data-driven gameplay (中文)](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/data-driven-gameplay-elements-in-unreal-engine) | External tuning, DataTables/CurveTables, and visible authoring flow | Content catalog and balance workflow |
| [Manage item and data (中文)](https://dev.epicgames.com/documentation/zh-cn/unreal-engine/coder-05-manage-item-and-data-in-an-unreal-engine-game) | Struct + DataAsset + DataTable separation | Item, recipe, material, and gathering definitions |
| [Manage item and data (日本語)](https://dev.epicgames.com/documentation/ja-jp/unreal-engine/coder-05-manage-item-and-data-in-an-unreal-engine-game) | Same data-driven pattern in the Japanese documentation track | Useful terminology cross-check for future JP research |
| [BuildGraph](https://dev.epicgames.com/documentation/en-us/unreal-engine/buildgraph-for-unreal-engine) | XML dependency graph, tagged outputs, parallelizable nodes, explicit shared storage | Echo gates, compile/cook/package/test/publish stages |
| [Gauntlet](https://dev.epicgames.com/documentation/en-us/unreal-engine/gauntlet-automation-framework-overview-in-unreal-engine) | Platform-agnostic session roles, log/crash parsing, and repeatable packaged sessions | Development package golden routes and future server/client tests |
| [Automation Test Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-test-framework-in-unreal-engine) | Unit/feature/content-stress/screenshot categories and clean-state discipline | BP compile sweeps, fixture checks, screenshot/VFX evidence |
| [Derived Data Cache](https://dev.epicgames.com/documentation/en-us/unreal-engine/derived-data-cache) | Derived data is disposable and should be external; shared DDC reduces team rebuild cost | Prevent asset churn and shader rebuilds from polluting source control |
| [Saving and Loading](https://dev.epicgames.com/documentation/en-us/unreal-engine/saving-and-loading-your-game-in-unreal-engine) | Slot-based `USaveGame`, explicit save classes, and asynchronous save/load boundaries | Versioned canonical state for portals, gathering, crafting, and restart/Continue |
| [Procedural Content Generation](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-in-unreal-engine) | Repeatable environment dressing and resource placement without making a PCG graph the gameplay authority | Use PCG for presentation/placement; keep dungeon seed, progression, and save contracts native |

### Public GitHub repositories and niche references

These are study references, not automatic dependencies. License and engine-version fit
must be reviewed before copying code or adding a plugin.

| Repository | Useful lesson | Caution |
| --- | --- | --- |
| [tomlooman/ActionRoguelike](https://github.com/tomlooman/ActionRoguelike) | A readable UE5 C++ sample with roguelike gameplay, AI, networking, and an evolving object-pooling/data-oriented experiment | Main branch is a playground; verify the repository license and isolate concepts before importing |
| [BenPyton/ProceduralDungeon](https://github.com/BenPyton/ProceduralDungeon) | Hand-authored rooms plus Blueprint/C++ generation rules, runtime regeneration, seeds, and room difficulty metadata | Source is CeCILL-C while Fab has a different EULA; do not mix licenses casually |
| [shun126/DungeonGenerator](https://github.com/shun126/DungeonGenerator) | Grid dungeon generation, mesh databases, MissionGraph progression, runtime/editor generation, replication hooks | Open-source version is GPL-3.0-or-later; closed-product adoption needs a legal decision |
| [intrxx/Obsidian](https://github.com/intrxx/Obsidian) | GAS-oriented ARPG structure, procedural item generation, abilities, and procedural level ambitions | GPL-3.0 and the author warns that ignored assets make it difficult to build; study architecture only |
| [luochuanyuewu/GenericSaveSystem](https://github.com/luochuanyuewu/GenericSaveSystem) | Save-game tags and level-streaming persistence, with support for recent UE versions | Small community project; license was not established in this review, so treat it as a design reference |
| [getnamo/GlobalEventSystem-Unreal](https://github.com/getnamo/GlobalEventSystem-Unreal) | MIT-licensed publisher/observer event routing, optional pinned state, domains, and GameplayTag variants | The README documents a C++-struct-to-BP limitation; prefer native GameplayMessageSubsystem where it fits |
| [tranek/GASDocumentation](https://github.com/tranek/GASDocumentation) | MIT community reference for ASC ownership, ability events, costs/cooldowns, prediction, and custom Ability Tasks | Match the branch to the engine version and treat it as interpretation, not Epic authority |
| [sinbad/SPUD](https://github.com/sinbad/SPUD) | MIT persistence for streamed levels, runtime-spawned actors, references, and SaveGame properties | Study stable GUID/async map-reset patterns; test against Melodia's canonical save contract before adoption |
| [JonasReich/OpenUnrealUtilities](https://github.com/JonasReich/OpenUnrealUtilities) | MIT automation fixtures, test worlds, collection assertions, test objects/widgets, and Automation Specs | Pin an engine-matched branch; use its fixture ideas for transaction/tag/save tests rather than importing wholesale |
| [wangjieest/GenericMessagePlugin](https://github.com/wangjieest/GenericMessagePlugin) | Apache-2.0 typed-message validation, Blueprint integration, sticky messages, and Chinese/English documentation | Test the UE5.8 compatibility matrix; messages remain coordination signals, not replicated state |
| [Mustafa-Kum/ue5-rpg-enemyreaction-system](https://github.com/Mustafa-Kum/ue5-rpg-enemyreaction-system) | Explicit Knocked/Airborne/Landing/GettingUp/HitReacting/Death/Ragdoll ownership and capsule-as-source-of-truth | Author labels it reference code, not plug-and-play; no license approval was inferred |
| [OpenPF2](https://github.com/OpenPF2) | A pre-alpha UE5 RPG framework split into plugin logic and playground content | Useful architecture study; custom-license and third-party-IP questions remain |
| [Incurian/AgentBridge](https://github.com/Incurian/AgentBridge) | A niche example of exposing UE editor/runtime state to external tools through a bridge | Review security, authority, and mutation controls before considering any integration |

Two additional watchlist references are useful but are not adoption candidates yet:
[Protocraft/ue5-craft](https://code.rick.me.uk/rm/ue5-craft) shows a small current
GAS/resource-node/loot/equipment prototype, while its license, tags, and compatibility
need verification; and `wangjieest/GenericMessagePlugin` is useful for typed-message
ideas but should not replace Unreal's native state/replication systems.

## Chinese and Japanese research terms used

The search deliberately included localized terms to surface documentation and regional
examples that English-only searches miss:

- 中文: `Unreal Engine 5 JRPG 回合制 战斗 开源 GitHub`, `UE5 采集 系统 背包 制作 开源 GitHub`, `虚幻引擎 数据驱动 游戏性 标签 交互 开源 GitHub`.
- 日本語: `Unreal Engine 5 JRPG ターン制 戦闘 GitHub`, `UE5 採取 システム インベントリ クラフト GitHub`, `Unreal Engine データ駆動 ゲームプレイ タグ 交互 GitHub`, `Unreal Engine 5 セーブ システム RPG GitHub`.

The highest-confidence localized hits were Epic's Chinese data-driven/item docs,
Epic's Japanese item/data docs, and the public dungeon/save/GAS repositories above.
Search-result snippets were not treated as proof of code quality or license permission.

## Recommended Melodia adoption order

### P0 — unlock the existing slice

1. Restore one clean editor/Monolith owner; do not use the stale modal process.
2. Read back `MelodiaIntegrationMap` actor/tag/roster state before changing the First
   Dream encounter CDO.
3. Close the stock encounter route with result/abort/reset evidence.
4. Resolve the skill-definition path/cooldown/SP authority mismatch before creating a
   runtime-ready skill DataAsset.
5. Keep the 6/7 BP shell status at offline/live-readback-pending until a clean editor
   provides graph and runtime evidence.

### P1 — first reusable content families

1. Single Resonance skill from one canonical definition path.
2. Single stock enemy with telegraph, hit, break, defeat, loot, and reset evidence.
3. Single gathering node that grants one material through an idempotent transaction.
4. Locked/unlocked portal plus one capability gate and alternate route.
5. One challenge and state anchor through the canonical narrative/save seam.

### P2 — Infinity Nikki-inspired composition layer

1. Additional Resonant Forms that compose existing capabilities.
2. Material catalog, recipe/crafting loop, dye/presentation layer, and a lightweight hub.
3. Photo/memory challenges and optional co-op-safe message contracts.
4. Seeded roguelike expeditions only after persistence and reset contracts are stable.

## Explicit non-adoption decisions

- Do not import a full inventory/dungeon/GAS framework into the project merely because
  it exists publicly.
- Do not copy GPL code into a closed project without a deliberate legal decision.
- Do not create a second save, currency, battle, or traversal authority to make a
  fixture appear to work.
- Do not treat V2 visual promotion, material tuning, Niagara observation, or PIE
  screenshots as proven until the Melusina lane supplies fresh evidence.
