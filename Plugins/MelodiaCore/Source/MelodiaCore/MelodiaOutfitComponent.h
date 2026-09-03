// Modular outfit slot system - the piece "swap 40 dresses on one body" needs
// and previously had zero infrastructure for. A garment is a separate
// USkeletalMeshComponent leader-posed onto the owning character's main mesh
// (same technique already proven for hair in AMelodiaSmokeCharacter, but as a
// reusable named-slot system instead of a one-off). Content authoring (which
// mesh goes in which slot, unlock/token cost) belongs to a DataAsset layered
// on top of this - this component is pure runtime plumbing.
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaOutfitComponent.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;

/** One equippable garment slot (dress, hat, gloves, shawl, trail, hair_charm -
 * matches the vocabulary already used by the wardrobe content drafts). */
UENUM(BlueprintType)
enum class EMelodiaOutfitSlot : uint8
{
	Body,
	Hat,
	Gloves,
	Shawl,
	Trail,
	HairCharm
};

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (deferred wardrobe). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(ClassGroup=(Melodia), NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaOutfitComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaOutfitComponent();

	/** Equips a garment mesh into a slot, creating the slot's component on
	 * first use and leader-posing it onto the owning character's main mesh.
	 * Passing null unequips the slot (hides it) without destroying the
	 * component, so re-equipping is cheap. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Outfit")
	void EquipGarment(EMelodiaOutfitSlot Slot, USkeletalMesh* GarmentMesh);

	UFUNCTION(BlueprintPure, Category="Melodia|Outfit")
	USkeletalMeshComponent* GetSlotComponent(EMelodiaOutfitSlot Slot) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Outfit")
	bool IsSlotEquipped(EMelodiaOutfitSlot Slot) const;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY()
	TMap<EMelodiaOutfitSlot, TObjectPtr<USkeletalMeshComponent>> SlotComponents;

	USkeletalMeshComponent* FindOrCreateSlotComponent(EMelodiaOutfitSlot Slot);
};
