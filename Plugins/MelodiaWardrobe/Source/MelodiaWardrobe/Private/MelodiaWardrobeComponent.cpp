// MelodiaWardrobe — slot-swap runtime component (Decision 044 re-host).

#include "MelodiaWardrobeComponent.h"
#include "MelodiaWardrobeSubsystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "GameFramework/Character.h"

UMelodiaWardrobeComponent::UMelodiaWardrobeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaWardrobeComponent::BeginPlay()
{
	Super::BeginPlay();
	ApplyWardrobeState();
}

void UMelodiaWardrobeComponent::ApplyWardrobeState()
{
	TSet<EMelodiaWardrobeSlot> ClaimedSlots;

	// Restore the equipped state the narrative record says we own (Decision 043
	// save/load): apply each equipped cosmetic's mesh to its slot.
	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		const FMelodiaWardrobeState State = Wardrobe->GetState();
		for (const TPair<EMelodiaWardrobeSlot, FName>& Pair : State.EquippedCosmeticIds)
		{
			// A saved slot is authoritative even if its catalog mesh is currently
			// unavailable; silently falling back would hide a broken save/catalog
			// reference.
			ClaimedSlots.Add(Pair.Key);
			if (USkeletalMesh* Mesh = Wardrobe->GetCosmeticMesh(Pair.Value))
			{
				if (!IsGarmentSkeletonCompatible(Mesh))
				{
					UE_LOG(LogTemp, Warning,
						TEXT("MELODIA_WARDROBE restore refused slot %d cosmetic %s: skeleton mismatch; "
							 "stale presentation hidden."),
						static_cast<int32>(Pair.Key), *Pair.Value.ToString());
					EquipGarment(Pair.Key, nullptr);
					continue;
				}

				EquipGarment(Pair.Key, Mesh);
				if (!IsSlotShowingMesh(Pair.Key, Mesh))
				{
					// A failed component creation or presentation bind must not
					// leave a previous save's garment visible for a slot claimed by
					// this broken record.
					EquipGarment(Pair.Key, nullptr);
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE slot %d holds saved cosmetic %s whose mesh will not "
						 "resolve; leaving the slot empty rather than substituting."),
					static_cast<int32>(Pair.Key), *Pair.Value.ToString());
				EquipGarment(Pair.Key, nullptr);
			}
		}
	}

	// Fixed V2 defaults are presentation-only references. They are applied
	// only when the save has no explicit cosmetic for that slot, so the
	// narrative wardrobe remains the authority for player-selected cosmetics.
	for (const TPair<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMesh>>& Pair : DefaultGarmentMeshes)
	{
		if (!ClaimedSlots.Contains(Pair.Key) && Pair.Value)
		{
			ClaimedSlots.Add(Pair.Key);
			if (!IsGarmentSkeletonCompatible(Pair.Value))
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE default slot %d refused: skeleton mismatch; stale presentation hidden."),
					static_cast<int32>(Pair.Key));
				EquipGarment(Pair.Key, nullptr);
				continue;
			}

			EquipGarment(Pair.Key, Pair.Value);
			if (!IsSlotShowingMesh(Pair.Key, Pair.Value))
			{
				// A broken default must not leave a previous save's garment visible
				// merely because the current narrative record has no claim.
				EquipGarment(Pair.Key, nullptr);
			}
		}
	}

	// Anything this state does not claim must be cleared. On a re-apply (save restore)
	// a slot the new record leaves empty would otherwise keep showing the previous
	// save's garment.
	for (const TPair<EMelodiaWardrobeSlot, TObjectPtr<USkeletalMeshComponent>>& Pair : SlotComponents)
	{
		if (!ClaimedSlots.Contains(Pair.Key) && Pair.Value)
		{
			Pair.Value->SetVisibility(false);
		}
	}
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::GetBodyMesh() const
{
	const ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
	return OwningCharacter ? OwningCharacter->GetMesh() : nullptr;
}

bool UMelodiaWardrobeComponent::IsGarmentSkeletonCompatible(const USkeletalMesh* GarmentMesh) const
{
	if (!GarmentMesh)
	{
		return false;
	}

	const USkeletalMeshComponent* BodyMesh = GetBodyMesh();
	const USkeletalMesh* BodyAsset = BodyMesh ? BodyMesh->GetSkeletalMeshAsset() : nullptr;
	if (!BodyAsset)
	{
		return false;
	}

	// Leader-pose sharing copies the body's bone transforms by index. A garment built
	// on a different USkeleton still renders, just wrongly -- so this has to be an
	// explicit refusal, not a best-effort attach.
	return GarmentMesh->GetSkeleton() == BodyAsset->GetSkeleton();
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::FindOrCreateSlotComponent(
	const EMelodiaWardrobeSlot Slot, USkeletalMesh* InitialMesh)
{
	if (TObjectPtr<USkeletalMeshComponent>* Existing = SlotComponents.Find(Slot))
	{
		return *Existing;
	}

	ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
	USkeletalMeshComponent* BodyMesh = GetBodyMesh();
	if (!OwningCharacter || !BodyMesh)
	{
		return nullptr;
	}

	const FName ComponentName = *FString::Printf(TEXT("WardrobeSlot_%s"), *UEnum::GetValueAsString(Slot));
	USkeletalMeshComponent* SlotComp = NewObject<USkeletalMeshComponent>(OwningCharacter, ComponentName);

	// Garments are pure presentation. A SkeletalMeshComponent defaults to query+physics
	// collision, so without this each equipped piece added an extra collider to the
	// pawn -- overlap volumes and traces would hit the dress before the character.
	SlotComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SlotComp->SetCollisionProfileName(TEXT("NoCollision"));
	SlotComp->SetGenerateOverlapEvents(false);
	SlotComp->CanCharacterStepUpOn = ECB_No;

	SlotComp->SetupAttachment(BodyMesh);

	// Order matters: the mesh must exist before the leader-pose binding, or the
	// binding is built against an empty component and the garment never follows the
	// body until something reassigns it.
	SlotComp->SetSkeletalMesh(InitialMesh);

	// Same technique as the hair's leader-pose sharing: the garment shares the
	// body's bone transforms directly rather than running its own animation.
	SlotComp->SetLeaderPoseComponent(BodyMesh);

	SlotComp->RegisterComponent();

	// Register with the actor's instance-component list. NewObject + RegisterComponent
	// alone leaves the component outside the owner's bookkeeping: it does not appear in
	// GetComponents(), is not serialised with the actor, and is not torn down with it.
	OwningCharacter->AddInstanceComponent(SlotComp);

	SlotComponents.Add(Slot, SlotComp);
	return SlotComp;
}

void UMelodiaWardrobeComponent::EquipGarment(const EMelodiaWardrobeSlot Slot, USkeletalMesh* GarmentMesh)
{
	// Unequip: hide an existing slot without destroying it, so re-equipping is cheap.
	// Never create a component just to hide it.
	if (!GarmentMesh)
	{
		if (USkeletalMeshComponent* Existing = GetSlotComponent(Slot))
		{
			Existing->SetVisibility(false);
		}
		return;
	}

	if (!IsGarmentSkeletonCompatible(GarmentMesh))
	{
		UE_LOG(LogTemp, Error,
			TEXT("MELODIA_WARDROBE slot %d refused garment %s: skeleton does not match the body "
				 "mesh, so leader-pose sharing would deform it. Slot left unchanged."),
			static_cast<int32>(Slot), *GetNameSafe(GarmentMesh));
		return;
	}

	USkeletalMeshComponent* SlotComp = FindOrCreateSlotComponent(Slot, GarmentMesh);
	if (!SlotComp)
	{
		return;
	}

	// On the create path FindOrCreateSlotComponent already applied the mesh in the
	// correct order; this covers the swap-an-existing-slot case.
	if (SlotComp->GetSkeletalMeshAsset() != GarmentMesh)
	{
		SlotComp->SetSkeletalMesh(GarmentMesh);
	}
	SlotComp->SetVisibility(true);
}

bool UMelodiaWardrobeComponent::EquipCosmetic(const FName CosmeticId)
{
	UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (!Wardrobe)
	{
		return false;
	}

	// Presentation preflight must happen before the authority writes the equipped
	// map. A catalog record can be valid while its mesh is incompatible with the
	// pawn's body skeleton; persisting that selection would create an equipped
	// cosmetic that can never be presented.
	USkeletalMesh* Mesh = Wardrobe->GetCosmeticMesh(CosmeticId);
	if (!Mesh || !IsGarmentSkeletonCompatible(Mesh))
	{
		return false;
	}

	const EMelodiaWardrobeSlot Slot = Wardrobe->GetSlotForCosmetic(CosmeticId);
	const FName PreviousCosmeticId = Wardrobe->GetEquipped(Slot);

	// Authority first after the component-local presentation preflight: the
	// canonical narrative record remains the only durable wardrobe state.
	if (!Wardrobe->EquipCosmetic(CosmeticId))
	{
		return false;
	}

	EquipGarment(Slot, Mesh);

	// EquipGarment can still fail if the owner/body component disappears during
	// teardown. Roll the canonical map back to the previous selection rather than
	// reporting success with a state the player cannot see.
	if (IsSlotShowingMesh(Slot, Mesh))
	{
		return true;
	}

	if (PreviousCosmeticId.IsNone())
	{
		Wardrobe->UnequipSlot(Slot);
		EquipGarment(Slot, nullptr);
	}
	else if (USkeletalMesh* PreviousMesh = Wardrobe->GetCosmeticMesh(PreviousCosmeticId))
	{
		Wardrobe->EquipCosmetic(PreviousCosmeticId);
		EquipGarment(Slot, PreviousMesh);
	}
	else
	{
		Wardrobe->UnequipSlot(Slot);
		EquipGarment(Slot, nullptr);
	}
	return false;
}

void UMelodiaWardrobeComponent::UnequipSlot(const EMelodiaWardrobeSlot Slot)
{
	if (UMelodiaWardrobeSubsystem* Wardrobe = UMelodiaWardrobeSubsystem::Get(this))
	{
		Wardrobe->UnequipSlot(Slot);
	}
	EquipGarment(Slot, nullptr);
}

USkeletalMeshComponent* UMelodiaWardrobeComponent::GetSlotComponent(const EMelodiaWardrobeSlot Slot) const
{
	const TObjectPtr<USkeletalMeshComponent>* Found = SlotComponents.Find(Slot);
	return Found ? Found->Get() : nullptr;
}

bool UMelodiaWardrobeComponent::IsSlotEquipped(const EMelodiaWardrobeSlot Slot) const
{
	const USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot);
	return SlotComp && SlotComp->IsVisible() && SlotComp->GetSkeletalMeshAsset();
}

bool UMelodiaWardrobeComponent::IsSlotShowingMesh(
	const EMelodiaWardrobeSlot Slot, const USkeletalMesh* ExpectedMesh) const
{
	const USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot);
	return ExpectedMesh
		&& SlotComp
		&& SlotComp->IsVisible()
		&& SlotComp->GetSkeletalMeshAsset() == ExpectedMesh;
}

void UMelodiaWardrobeComponent::SetSlotMaterial(const EMelodiaWardrobeSlot Slot, const int32 MaterialIndex, UMaterialInterface* Material)
{
	if (USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot))
	{
		SlotComp->SetMaterial(MaterialIndex, Material);
	}
}
