// MelodiaWardrobe — slot-swap runtime component.
//
// Re-host of the quarantined UMelodiaOutfitComponent algorithm (Decision 044)
// with three additions the original lacked:
//   1. Material override application (SetMaterial per slot index)
//   2. Mirror of equipped state to UMelodiaWardrobeSubsystem
//   3. Type rename + namespace (UMelodiaOutfitComponent -> UMelodiaWardrobeComponent)
//
// Same-skeleton garments leader-pose onto the owning character's main mesh;
// different-skeleton garments (out of scope this PR) would use the hair-style
// SourceMeshComponent redirect.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCompanionWardrobeBridge.h"
#include "MelodiaNarrativeTypes.h" // EMelodiaWardrobeSlot
#include "MelodiaWardrobeComponent.generated.h"

class USkeletalMesh;
class USkeletalMeshComponent;
class UMaterialInterface;
class UMelodiaWardrobeSubsystem;

UCLASS(ClassGroup=(Melodia), Blueprintable, meta=(BlueprintSpawnableComponent))
class MELODIAWARDROBE_API UMelodiaWardrobeComponent
	: public UActorComponent
	, public IMelodiaCompanionWardrobeInterface
{
	GENERATED_BODY()

public:
	UMelodiaWardrobeComponent();

	/** Equips a garment mesh into a slot, creating the slot's component on first use
	 *  and leader-posing it onto the owning character's main mesh. Null unequips the
	 *  slot (hides it) without destroying the component, so re-equipping is cheap. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	void EquipGarment(EMelodiaWardrobeSlot Slot, USkeletalMesh* GarmentMesh);

	/** Equips by cosmetic id: resolves the mesh through the wardrobe subsystem and
	 *  mirrors the equipped id into the narrative record. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	bool EquipCosmetic(FName CosmeticId);

	/**
	 * Applies an already-owned cosmetic to this actor for presentation only.
	 * Unlike EquipCosmetic, this path does not modify the equipped map or any save
	 * state. It is the default seam used by companion presentation requests.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe|Presentation")
	bool ApplyCosmeticPresentation(FName CosmeticId);

	/** Core-owned companion seam. Prototype grants are opt-in in the profile. */
	virtual EMelodiaCompanionWardrobeRequestResult RequestCompanionWardrobe_Implementation(
		const FMelodiaCompanionWardrobeProfile& Profile) override;

	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	void UnequipSlot(EMelodiaWardrobeSlot Slot);

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	USkeletalMeshComponent* GetSlotComponent(EMelodiaWardrobeSlot Slot) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe")
	bool IsSlotEquipped(EMelodiaWardrobeSlot Slot) const;

	/** Material override applied to the slot's mesh (addition #1 of Decision 044). */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	void SetSlotMaterial(EMelodiaWardrobeSlot Slot, int32 MaterialIndex, UMaterialInterface* Material);

	/**
	 * Re-applies every equipped garment from the canonical narrative record, then fills
	 * unclaimed slots from DefaultGarmentMeshes.
	 *
	 * Call after a save restore. BeginPlay used to be the only path that read wardrobe
	 * state, so loading a save mid-session left the character wearing the previous
	 * save's garments while the record said otherwise. Slots the restored state no
	 * longer claims are hidden, so stale garments do not survive the reload.
	 *
	 * Reads through UMelodiaWardrobeSubsystem -> FMelodiaNarrativeRecord. It holds no
	 * state of its own and is not a second save authority.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Wardrobe")
	void ApplyWardrobeState();

	/**
	 * Default meshes used when a save has no explicit cosmetic for a slot.
	 * The Melusina V2 pawn supplies Shirt/Skirt/Boots/Accessories here; saved
	 * cosmetic selections still take precedence during BeginPlay.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Wardrobe|Defaults")
	TMap<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMesh>> DefaultGarmentMeshes;

	/** Explicit owner gate for the deferred wear-in-battle lane. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Wardrobe|Battle")
	bool bEnableBattleWardrobe = false;

	UFUNCTION(BlueprintPure, Category="Melodia|Wardrobe|Battle")
	bool IsBattleWardrobeEnabled() const { return bEnableBattleWardrobe; }

protected:
	virtual void BeginPlay() override;

private:
	/**
	 * Returns the slot's component, creating it on first use with InitialMesh already
	 * applied. InitialMesh must be non-null and skeleton-checked by the caller: the
	 * mesh has to be set before SetLeaderPoseComponent, or the leader-pose binding is
	 * established against an empty component.
	 */
	USkeletalMeshComponent* FindOrCreateSlotComponent(EMelodiaWardrobeSlot Slot, USkeletalMesh* InitialMesh);

	/** The owning character's body mesh, or null when the owner is not a character. */
	USkeletalMeshComponent* GetBodyMesh() const;

	/**
	 * True when the garment shares the body's USkeleton. Leader-pose sharing copies
	 * bone transforms by index, so a foreign skeleton produces a silently deformed
	 * garment rather than an error.
	 */
	bool IsGarmentSkeletonCompatible(const USkeletalMesh* GarmentMesh) const;

	/** True only when the requested mesh, not a stale previous mesh, is visible. */
	bool IsSlotShowingMesh(EMelodiaWardrobeSlot Slot, const USkeletalMesh* ExpectedMesh) const;

	UPROPERTY()
	TMap<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMeshComponent>> SlotComponents;
};
