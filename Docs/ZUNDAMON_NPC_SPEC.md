# Zundamon ΓÇö NPC Blueprint Specification
## BP_Zundamon_NPC

### Inheritance
```
BP_Zundamon_NPC : Character
```

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| **SkeletalMesh** | USkeletalMeshComponent | SK_Zundamon |
| **AnimationBP** | TSubclassOf<UAnimInstance> | ABP_Zundamon |
| **DialogueWidget** | UWidgetComponent | Dialogue bubble above head |
| **QuestInterface** | Implemented Interface | IQuestGiver |
| **ShopInventory** | UDataAsset | ZundamonShopInventory |
| **VOICEVOXAudio** | TMap<FString, USoundWave> | Pre-generated voice lines |
| **BehaviorTree** | UBehaviorTree | BT_Zundamon_NPC |

### Behavior Tree ΓÇö BT_Zundamon_NPC

```
Root (Selector)
Γö£ΓöÇΓöÇ Sequence: Combat
Γöé   Γö£ΓöÇΓöÇ Condition: Enemy in range
Γöé   ΓööΓöÇΓöÇ Action: Ranged attack (Zunda Arrow)
Γöé
Γö£ΓöÇΓöÇ Sequence: Quest Interaction
Γöé   Γö£ΓöÇΓöÇ Condition: Player targeting & within range
Γöé   Γö£ΓöÇΓöÇ Action: Face player
Γöé   ΓööΓöÇΓöÇ Action: Open quest UI
Γöé
Γö£ΓöÇΓöÇ Sequence: Shop Interaction
Γöé   Γö£ΓöÇΓöÇ Condition: Player targeting & within range
Γöé   ΓööΓöÇΓöÇ Action: Open shop UI
Γöé
Γö£ΓöÇΓöÇ Sequence: Idle
Γöé   Γö£ΓöÇΓöÇ Action: Look around (random head rotation)
Γöé   Γö£ΓöÇΓöÇ Action: Hum/sing (trigger voice line)
Γöé   Γö£ΓöÇΓöÇ Action: Snack on mochi (eat animation)
Γöé   ΓööΓöÇΓöÇ Action: Stretch
Γöé
ΓööΓöÇΓöÇ Sequence: Wander
    Γö£ΓöÇΓöÇ Action: Find random nav point
    Γö£ΓöÇΓöÇ Action: Walk to point
    ΓööΓöÇΓöÇ Wait: 3-8 seconds
```

### Animation Set

| Animation | Type | Purpose |
|-----------|------|---------|
| `A_Zundamon_Idle` | AnimSequence | Gentle idle sway, tail wag |
| `A_Zundamon_Walk` | AnimSequence | Bouncy walk cycle |
| `A_Zundamon_Run` | AnimSequence | Energetic run |
| `A_Zundamon_Greet` | AnimSequence | Wave + head tilt + smile |
| `A_Zundamon_QuestGive` | AnimSequence | Point at board, nod |
| `A_Zundamon_ShopOpen` | AnimSequence | Present mochi on palm |
| `A_Zundamon_Unlucky_Trip` | AnimSequence | Stumble, fall, dust off |
| `A_Zundamon_MochiMagic` | AnimSequence | Summon mochi, sparkle VFX |
| `A_Zundamon_Eat` | AnimSequence | Eat mochi, satisfied expression |
| `A_Zundamon_ArrowFire` | AnimSequence | Draw Zunda Arrow, fire |

### Shop Inventory ΓÇö DA_ZundamonShop

| Item | Price | Effect | Category |
|------|-------|--------|----------|
| `Zunda Mochi (Small)` | 50g | Restore 30% HP | Consumable |
| `Matcha Mochi` | 75g | Restore 20% MP | Consumable |
| `Intelligence Mochi` | 200g | +15% EXP for 5 min | Buff |
| `Zunda Arrow Charm` | 500g | +10% Crit Rate (permanent accessory) | Accessory |
| `Lucky Mochi` | 100g | Random positive effect | Consumable |
| `Green East Silk` | 300g | Crafting material | Material |
| `Zunda Bean Paste` | 25g | Cooking ingredient | Material |

### Quest Data ΓÇö DT_ZundamonQuests

| ID | Name | Type | Prereq | Reward |
|----|------|------|--------|--------|
| `Q_ZUN_001` | Mochi Retrieval | Collect | None | 200g + 3x Zunda Mochi |
| `Q_ZUN_002` | Kitchen Chaos | Combat | Q_ZUN_001 | 350g + Lucky Mochi |
| `Q_ZUN_003` | Zunda Arrow Lost | Retrieve | Q_ZUN_002 | Arrow Charm + shop discount |
| `Q_ZUN_004` | Mochi Board Setup | Craft | Q_ZUN_001 | Unlock daily quests |
| `Q_ZUN_005` | Power Unstable | Boss | Q_ZUN_003 | Zundamon joins party |

### Dialogue Triggers

| Trigger | Voice ID | Subtitle |
|---------|----------|----------|
| Player approaches (first time) | zun_first_meet_01 | "Ah! Help me, na no da! My arrow is stuck..." |
| Player approaches (return) | zun_shop_open_01 | "Welcome, na no da! Today's special is matcha mochi." |
| Quest accepted | zun_quest_01 | "Please collect three escaped mochi in the village!" |
| Quest completed | zun_quest_complete_01 | "Amazing, na no da! Here's your reward." |
| Idle (every 30-60s) | zun_idle_01 | "Hmm hmm hmm~ Mochi, mochi, zunda mochi~" |
| Player leaves | zun_shop_goodbye_01 | "Come back soon, na no da!" |
| Trips (random event) | zun_unlucky_02 | "Ouch... I fell again. Maybe I'm a bit unlucky..." |
| Late game reveal | zun_power_reveal_01 | "Actually... my bad luck is just my power leaking..." |

### Folder Structure in Unreal

```
/Game/Melodia/Characters/Zundamon/
Γö£ΓöÇΓöÇ SK_Zundamon               # Skeletal Mesh
Γö£ΓöÇΓöÇ SK_Zundamon_PhysicsAsset   # Physics Asset
Γö£ΓöÇΓöÇ SK_Zundamon_Skeleton       # Skeleton
Γö£ΓöÇΓöÇ ABP_Zundamon               # Animation Blueprint
Γö£ΓöÇΓöÇ BP_Zundamon_NPC            # NPC Blueprint
Γö£ΓöÇΓöÇ BT_Zundamon_NPC            # Behavior Tree
Γö£ΓöÇΓöÇ DA_ZundamonShop            # Shop Inventory Data Asset
Γö£ΓöÇΓöÇ DT_ZundamonQuests          # Quest Data Table
Γö£ΓöÇΓöÇ Materials/
Γöé   Γö£ΓöÇΓöÇ MI_Zundamon_Body
Γöé   Γö£ΓöÇΓöÇ MI_Zundamon_Cloth
Γöé   Γö£ΓöÇΓöÇ MI_Zundamon_Hair
Γöé   Γö£ΓöÇΓöÇ MI_Zundamon_Head
Γöé   ΓööΓöÇΓöÇ MI_Zundamon_Eye
Γö£ΓöÇΓöÇ Textures/
Γöé   Γö£ΓöÇΓöÇ T_Zundamon_Body
Γöé   Γö£ΓöÇΓöÇ T_Zundamon_Cloth
Γöé   Γö£ΓöÇΓöÇ T_Zundamon_Hair
Γöé   Γö£ΓöÇΓöÇ T_Zundamon_Head
Γöé   ΓööΓöÇΓöÇ T_Zundamon_Eye
Γö£ΓöÇΓöÇ Animations/
Γöé   Γö£ΓöÇΓöÇ A_Zundamon_Idle
Γöé   Γö£ΓöÇΓöÇ A_Zundamon_Walk
Γöé   Γö£ΓöÇΓöÇ A_Zundamon_Greet
Γöé   ΓööΓöÇΓöÇ ...
ΓööΓöÇΓöÇ Audio/
    Γö£ΓöÇΓöÇ zun_first_meet_01.wav
    Γö£ΓöÇΓöÇ zun_shop_open_01.wav
    ΓööΓöÇΓöÇ ...
```
