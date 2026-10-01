---
name: skill-tree
description: Create RPG skill trees with the ACF Skill Tree module (skill graph, skill nodes, the skill-tree component) that spend skill points to unlock/upgrade abilities and gameplay effects tied to RPG stats.
globs: []
alwaysApply: false
---

# Skill Tree — ACF Ultimate

The **Ascent Skill Tree** module (`AscentSkillTree`) provides graph-based RPG skill trees built on `AGSGraphRuntime`. A `UACFSkillTreeGraph` asset is a node graph where each `UACFSkillNode` references a `UACFBaseSkill` data object. A skill defines what it grants (an ability and/or a gameplay effect through `FSkillConfig`), its `MaxLevel`, requirements (`RequiredLevel`, `RequiredSkillPoint`), and UI info (`FSkillUIConfig`). Nodes are linked by `UACFSkillTransition` edges that establish prerequisites (parents must be unlocked first). A `UACFSkillTreeComponent` on the character tracks unlocked skills, spends/refunds skill points, and applies the granted abilities and effects to the owning `UACFAbilitySystemComponent` / `UACFGASAttributesComponent`. Everything is replicated and SaveGame-friendly.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample skill tree | `UACFSkillTreeGraph` | `/AscentCombatFramework/.../SkillTrees/` | The node graph of skills + prerequisites |
| Sample skill | `UACFBaseSkill` (Blueprint subclass) | Authored inline on each node | What a skill grants + UI + requirements |

> **Never edit sample assets.** Duplicate any sample skill tree into `Content/YourGame/SkillTrees/` and customize your copy — sample assets are overwritten on plugin/sample updates.

### Key classes

| Class | Role |
|---|---|
| `UACFSkillTreeGraph` | The skill tree graph (extends `UAGSGraph`). Has `SkillTreeTag`, `SkillTreeName`; finds/activates nodes by `FGuid`, checks parent prerequisites |
| `UACFBaseSkillNode` | Abstract node base (extends `UAGSGraphNode`); holds a `UACFBaseSkill`, exposes `MaxLevel`, `SkillToGrant`, `UISkillInfo` |
| `UACFSkillNode` | Concrete skill node placed in the graph |
| `UACFStartSkillNode` | Entry/root node of the tree |
| `UACFBaseSkill` | The skill data object: `MaxLevel`, `SkillToGrant` (`FSkillConfig`), `UISkillInfo` (`FSkillUIConfig`) |
| `UACFSkillTransition` | Graph edge defining a parent→child prerequisite link |
| `UACFSkillTreeComponent` | Character component: unlock/upgrade/remove skills, manage skill points, apply effects, replicate + save |
| `FSkillConfig` | `AbilityToGrant`, `GameplayEffect`, `RequiredLevel`, `RequiredSkillPoint` |
| `FSkillUIConfig` | `SkillName`, `Description`, `UnlockedIcon`, `LockedIcon`, `PreviewVideo` |
| `ECanUnlockSkillResult` | Enum reason result returned by `CanUnlockSkill` |

UI widgets are provided to render the tree: `UACFSkillTreeWidget`, `UACFSkillNodeWidget`, `UACFSkillTreeConnectionsWidget`.

---

## 2 — Setup / Configuration

### A. Create the skill tree graph

1. Duplicate a sample `UACFSkillTreeGraph` into `Content/YourGame/SkillTrees/` (or create a new one if none exists).
2. Open the graph and set:
   - **`SkillTreeTag`** — the GameplayTag identifying this tree (used for all component lookups).
   - **`SkillTreeName`** — display name for UI.
3. Place a `UACFStartSkillNode` as the root, then add `UACFSkillNode` nodes for each skill.
4. For each `UACFSkillNode`, assign a **`Skill`** (a `UACFBaseSkill` Blueprint subclass) and configure it:
   - **`MaxLevel`** — how many times the skill can be upgraded.
   - **`SkillToGrant` (`FSkillConfig`)**:
     - `AbilityToGrant` — the ability granted on unlock.
     - `GameplayEffect` — a gameplay effect applied (e.g. +stats/perks via RPG stats).
     - `RequiredLevel` — minimum character level required.
     - `RequiredSkillPoint` — skill-point cost.
   - **`UISkillInfo` (`FSkillUIConfig`)** — name, description, locked/unlocked icons, preview video.
5. Connect nodes with `UACFSkillTransition` edges to define prerequisites — a child skill requires all its parents to be active before it can unlock.

### B. Configure the component

1. Add a `UACFSkillTreeComponent` to your character (it is a `BlueprintSpawnableComponent`).
2. Add your duplicated `UACFSkillTreeGraph`(s) to the component's **`SkillTrees`** array.
3. Set the starting **`SkillPoints`** (default 2). Award more at runtime via `AddSkillPoints`.
4. The component automatically resolves the owner's `UACFGASAttributesComponent` and `UACFAbilitySystemComponent` for applying effects and abilities.

---

## 3 — Core Workflow / Runtime API

> Each skill node has a unique `FGuid`. The API identifies skills by `(SkillTreeTag, SkillNodeId)`.

### Checking & unlocking

```
// Validate first (returns a reason if it fails)
ECanUnlockSkillResult Result;
bool bCan = SkillComp->CanUnlockSkill(TreeTag, SkillNodeId, Result);
// Result e.g. InsufficientSkillPoints, InsufficientCharacterLevel,
//             ParentNodesNotActive, AlreadyAtMaxLevel, ...

// Unlock or upgrade (server-authoritative). Applies ability/effect on first unlock,
// increments level on subsequent calls (up to MaxLevel).
SkillComp->UnlockSkillFromTree(TreeTag, SkillNodeId);
```

### Skill points

```
SkillComp->AddSkillPoints(3);          // server RPC
int32 Points = SkillComp->GetSkillPoints();
```

### Querying state

```
bool bActive   = SkillComp->IsSkillActive(SkillNodeId);
int32 Level    = SkillComp->GetSkillCurrentLevel(SkillNodeId);  // 0 if not unlocked
UACFBaseSkillNode* Node = SkillComp->GetSkillByIds(TreeTag, SkillNodeId);
UACFSkillTreeGraph* Tree = SkillComp->GetSkillTreeByTag(TreeTag);
TArray<UACFSkillTreeGraph*> AllTrees = SkillComp->GetSkillTrees();
```

### Removing & respec

```
// Remove one skill (deactivates its ability/effect; does NOT refund points)
SkillComp->RemoveSkill(TreeTag, SkillNodeId);

// Full respec: deactivate all skills, clear tracking, refund all spent points
SkillComp->Respec();
```

### Reacting to changes (UI binding)

```
SkillComp->OnActiveSkillsChanged.AddDynamic(...);          // skills (un)locked
SkillComp->OnSkillPointsChanged.AddDynamic(...);           // (int32 NewSkillPoints)
```

State is replicated (`ActiveSkills`, `SkillLevels`, `SkillPoints`) and marked `SaveGame`, so it persists and syncs to clients automatically.

---

## 4 — Wire to Characters / Blueprints

1. Add `UACFSkillTreeComponent` to your player/character Blueprint and populate `SkillTrees` with your duplicated graphs.
2. Build the skill tree UI with `UACFSkillTreeWidget` (plus `UACFSkillNodeWidget` and `UACFSkillTreeConnectionsWidget`), or duplicate the sample widget and reassign per the widget-registry workflow.
3. Bind UI buttons to `CanUnlockSkill` (to enable/disable + show the failure reason) and `UnlockSkillFromTree` (to commit).
4. Bind `OnActiveSkillsChanged` and `OnSkillPointsChanged` to refresh node states, icons (`UnlockedIcon`/`LockedIcon`), and the points counter.
5. Grant skill points from progression (e.g. on level-up) via `AddSkillPoints`.
6. Add a "Respec" button calling `Respec()` to refund and reset.
7. Granted abilities/effects flow through the character's `UACFAbilitySystemComponent` / `UACFGASAttributesComponent` (RPG stats), so the skill's `GameplayEffect` can modify attributes and perks directly.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Skill tree graph is duplicated into `Content/YourGame/SkillTrees/` (sample untouched).
- [ ] The graph has a valid `SkillTreeTag` and a `UACFStartSkillNode`.
- [ ] Each `UACFSkillNode` has a `Skill` assigned with `SkillToGrant` and `UISkillInfo` filled.
- [ ] Prerequisite edges (`UACFSkillTransition`) connect parents → children correctly.
- [ ] `UACFSkillTreeComponent.SkillTrees` contains your duplicated graph(s).
- [ ] Starting `SkillPoints` set, and `AddSkillPoints` is wired to progression.
- [ ] Character has `UACFAbilitySystemComponent` + `UACFGASAttributesComponent` for granting.
- [ ] UI binds to `CanUnlockSkill`/`UnlockSkillFromTree` and the change delegates.

**Common failures:**

| Symptom | Fix |
|---|---|
| Skill won't unlock | Check `CanUnlockSkill` result: insufficient points/level, or `ParentNodesNotActive` |
| Unlock does nothing | `SkillTreeTag` or `SkillNodeId` wrong, or component's `SkillTrees` doesn't contain the tree |
| Ability/effect not applied | `FSkillConfig.AbilityToGrant` / `GameplayEffect` empty, or no `UACFAbilitySystemComponent` on owner |
| Can't upgrade past level 1 | `MaxLevel` is 1 — raise it on the `UACFBaseSkill` |
| Points not deducted / refunded | `RequiredSkillPoint` is 0, or you bypassed `UnlockSkillFromTree`/`Respec` |
| Child unlockable before parents | Missing `UACFSkillTransition` edges defining the prerequisite |
| UI doesn't refresh | Not bound to `OnActiveSkillsChanged` / `OnSkillPointsChanged` |
| State not saved/synced | Editing source asset instead of using the replicated/SaveGame component state |
