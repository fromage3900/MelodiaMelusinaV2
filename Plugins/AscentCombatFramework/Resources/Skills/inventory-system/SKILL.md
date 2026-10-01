---
name: inventory-system
description: Create and configure items, inventory, equipment slots, weapons, armor, and consumables using the ACF Inventory System module.
globs: []
alwaysApply: false
---

# Inventory System — ACF Ultimate

The **Inventory System** module manages every aspect of items in ACF: collecting, storing, equipping, dropping, and using items. `UACFInventoryComponent` holds a replicated list of items on any actor. `UACFEquipmentComponent` (which extends inventory) handles equip slots, weapon attachment to the skeleton, modular armor mesh swaps, and death drops. Items themselves are Blueprint subclasses of `UACFItem`, `UACFWeapon`, `UACFArmor`, or `UACFConsumable`. World pickups are represented by `AACFItemActor` / `AACFWeaponActor`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample weapon item | `UACFWeapon` | `/AscentCombatFramework/Items/Weapons/` | DataAsset defining a weapon's stats, slots, moveset |
| Sample armor item | `UACFArmor` | `/AscentCombatFramework/Items/Armor/` | DataAsset defining armor stats, modular mesh |
| Sample consumable | `UACFConsumable` | `/AscentCombatFramework/Items/Consumables/` | DataAsset for usable items (potions, food) |
| Sample world item | `AACFItemActor` | `/Game/FullSample/Integrations/Ultimate/Items/` | World pickup actor for generic items |
| Sample world weapon | `AACFWeaponActor` | `/Game/FullSample/Integrations/Ultimate/Items/` | World pickup actor for weapons |

> **Never edit sample assets.** Duplicate into your own content folder (e.g. `Content/YourGame/Items/`) and customize your copy.

### Key classes

| Class | Role |
|---|---|
| `UACFInventoryComponent` | Holds the replicated `FACFInventoryList`; handles add/remove/weight |
| `UACFEquipmentComponent` | Extends inventory; equip slots, weapon actors, armor mesh, death drops |
| `UACFItem` | Base item DataAsset; defines name, icon, weight, max stack, tags |
| `UACFWeapon` | Weapon-specific item: damage, slots, moveset tag, one-hand/two-hand |
| `UACFArmor` | Armor-specific item: defense, modular mesh, slot tag |
| `UACFConsumable` | Consumable item: GAS GameplayEffect to apply on use |
| `AACFItemActor` | World actor representing a pickup; contains `UACFInventoryComponent` |
| `AACFWeaponActor` | Spawned and attached to the character skeleton when a weapon is equipped |
| `FInventoryItem` | Runtime struct wrapping a `UACFItem` instance with GUID, equipped state, slot |
| `FEquippedItem` | Runtime struct representing an item in an equipment slot |
| `FStartingItem` | Config struct listing items given to a character at spawn |

---

## 2 — Setup / Configuration

### A. Create an item DataAsset

1. In the Content Browser, right-click → **Miscellaneous → Data Asset**.
2. Choose `UACFWeapon`, `UACFArmor`, or `UACFConsumable` as the class.
3. Save under `Content/YourGame/Items/`.
4. Open the DataAsset and fill in:
   - **Name / Icon / Description** for UI.
   - **Weight** (contributes to `MaxInventoryWeight`).
   - **MaxStack** — how many stack in one inventory slot.
   - **bCanBeSold / bCanBeDropped** flags.
   - *(Weapons)* **ItemSlots** — GameplayTags matching the slots defined on the character (e.g. `ItemSlot.RightHand`).
   - *(Weapons)* **MovesetTag / MovesetActionsTag** — tags that switch the character's moveset when equipped.
   - *(Armor)* **ItemSlots** — e.g. `ItemSlot.Chest`.
   - *(Armor)* **SkeletalMeshData** — modular mesh to swap onto the character.
   - *(Consumables)* **GameplayEffectToApply** — a `UGameplayEffect` class that is applied to the target pawn.

### B. Configure equipment slots on the character

1. Open your character Blueprint and select the `UACFEquipmentComponent` in the component list.
2. In **Details**, set `AvailableEquipmentSlot` to the array of `FGameplayTag` your character can use (e.g. `ItemSlot.RightHand`, `ItemSlot.LeftHand`, `ItemSlot.Chest`, `ItemSlot.Legs`).
3. Set `AllowedWeaponTypes` to restrict which weapon tags this character can equip.
4. Set `bAutoEquipItem = true` to auto-equip items picked up from the world.
5. Set drop behavior: `bDropItemsOnDeath`, `bDestroyItemsOnDeath`, `bCollapseDropInASingleWorldItem`.

### C. Add starting items via DataAsset

In the character's `UACFCharacterDataAsset`, add entries to `StartingItems`:
- **ItemClass** — the item DataAsset class to spawn.
- **Count** — how many.
- **bAutoEquip** — equip immediately at spawn.
- **DropChancePercentage** — 0–100 drop chance on death.

### D. Configure inventory limits

On the `UACFEquipmentComponent`:
- `MaxInventorySlots` (default 40) — maximum number of item stacks.
- `MaxInventoryWeight` (default 180) — maximum cumulative weight.

### E. Create world pickup actors

1. Duplicate a sample `AACFItemActor` or `AACFWeaponActor` from the sample folder.
2. Save under `Content/YourGame/Items/`.
3. In the actor's `UACFInventoryComponent`, add the item(s) to its inventory. When the player interacts with the actor, items transfer to the player's inventory.

---

## 3 — Core Workflow / Usage

### Adding items at runtime (Blueprint)

```
// Add by class (auto-equips if bAutoEquip = true):
EquipmentComp->AddItemToInventoryByClass(MyWeaponClass, 1, true);

// Add from a FBaseItem struct:
EquipmentComp->AddItemToInventory(BaseItemStruct, true);
```

### Equipping and unequipping

```
// Equip a specific inventory item:
EquipmentComp->EquipItemFromInventory(InventoryItem);

// Equip into a specific slot:
EquipmentComp->EquipItemFromInventoryInSlot(InventoryItem, SlotTag);

// Unequip by slot:
EquipmentComp->UnequipItemBySlot(SlotTag);

// Sheathe current weapon (moves from hand to body):
EquipmentComp->SheathCurrentWeapon();

// Unshethe first available weapon:
EquipmentComp->UnsheatheFirstAvailableWeapon();
```

### Using consumables

```
// Use a consumable slot on a target:
EquipmentComp->UseEquippedItemBySlot(ConsumableSlotTag);
EquipmentComp->UseConsumableOnActorBySlot(ConsumableSlotTag, TargetPawn);

// Use directly from inventory item reference:
EquipmentComp->UseConsumableOnTarget(InventoryItem, TargetPawn);
```

### Dropping items

```
EquipmentComp->DropItem(InventoryItem, 1);
EquipmentComp->DropItemByInventoryIndex(ItemIndex, 1);
```

### Querying inventory

```
TArray<FInventoryItem> All = EquipmentComp->GetInventory();
int32 Count = EquipmentComp->GetTotalCountOfItemsByClass(MyItemClass);
bool bHas = EquipmentComp->HasAnyItemOfType(MyItemClass);

FInventoryItem Found;
bool bFound = EquipmentComp->FindFirstItemOfClassInInventory(MyItemClass, Found);
```

### Key delegates

| Delegate | When it fires |
|---|---|
| `OnInventoryChanged` | Any add or remove |
| `OnItemAdded(FBaseItem)` | Item added to inventory |
| `OnItemRemoved(FBaseItem)` | Item removed from inventory |
| `OnEquipmentChanged(FEquipment)` | Equipment slot content changes |
| `OnEquippedArmorChanged(FGameplayTag)` | A specific armor slot changes |

---

## 4 — Wire to Characters / Blueprints

### Connecting item pickup to inventory

1. Place an `AACFItemActor` (or your duplicate) in the level.
2. Add an **Interaction trigger** (or use the built-in interactable interface) — when the player interacts, call:
   ```
   PlayerEquipmentComp->MoveItemsFromInventory(WorldItemInvComp->GetInventory(), WorldItemInvComp);
   ```
3. Alternatively, use the sample `ACFBaseInteractableBP` pattern — duplicate it and wire the pickup logic.

### Weapon Actor attachment

When a weapon is equipped, `UACFEquipmentComponent` automatically:
- Spawns the `AACFWeaponActor` (defined in the weapon DataAsset).
- Attaches it to the socket defined by `AttachSocket` on the weapon item.
- Switches the character `CombatType` (Melee / Ranged / Unarmed).
- Calls `SwitchMoveset` + `SwitchMovesetActions` using the weapon's moveset tags.

You do not need to manually spawn weapon actors — handle all this through the equipment component.

### Modular armor mesh

- The `UACFEquipmentComponent` finds a `SkeletalMeshComponent` tagged with `MainMeshTag` (default `"Mesh"`).
- When armor with a `SkeletalMeshData` is equipped, it swaps/adds mesh components automatically.
- Set `bUpdateMainMeshVisibility = true` to let armor hide the base body mesh when a full-body armor is equipped.

### Death drops

- On death, `DestroyEquippedItems(bSpawnDrops: true)` is called automatically.
- Items with `DropChancePercentage > 0` roll for a drop.
- If `bCollapseDropInASingleWorldItem = true`, all drops merge into one `AACFItemActor` in the world.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Item DataAssets are duplicated from sample and saved under `Content/YourGame/Items/`.
- [ ] `AvailableEquipmentSlot` on the character's `UACFEquipmentComponent` includes all required slot tags.
- [ ] Item DataAsset `ItemSlots` tags match the slots defined on the character.
- [ ] `AllowedWeaponTypes` on the character allows the weapon type being equipped.
- [ ] `StartingItems` in the character DataAsset (or directly on the component) has at least one entry.
- [ ] World pickup actors have items in their `UACFInventoryComponent`.
- [ ] `MaxInventorySlots` and `MaxInventoryWeight` are set to sensible values.
- [ ] Weapon DataAsset references a valid `AACFWeaponActor` Blueprint with the correct skeleton socket name.

**Common failures:**

| Symptom | Fix |
|---|---|
| Item added but not auto-equipped | `bAutoEquip = false` on `FStartingItem` or `AvailableEquipmentSlot` is empty |
| Weapon equips but no weapon actor appears | Weapon DataAsset has no `WeaponActorClass` or wrong socket name |
| Armor equips but mesh doesn't change | `bUpdateMainMeshVisibility` is off, or `MainMeshTag` doesn't match the skeletal mesh component tag |
| Inventory full despite few items | `MaxInventorySlots` is too low, or `MaxInventoryWeight` reached — check `currentInventoryWeight` |
| Consumable "uses" but no effect | `GameplayEffectToApply` is null in the consumable DataAsset |
| Items drop on death but none visible | `bDropItemsOnDeath = false` or `DropChancePercentage = 0` on all items |
