#include "MelodiaOutfitComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Character.h"

UMelodiaOutfitComponent::UMelodiaOutfitComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaOutfitComponent::BeginPlay()
{
	Super::BeginPlay();
}

USkeletalMeshComponent* UMelodiaOutfitComponent::FindOrCreateSlotComponent(const EMelodiaOutfitSlot Slot)
{
	if (TObjectPtr<USkeletalMeshComponent>* Existing = SlotComponents.Find(Slot))
	{
		return *Existing;
	}

	ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
	if (!OwningCharacter || !OwningCharacter->GetMesh())
	{
		return nullptr;
	}

	const FName ComponentName = *FString::Printf(TEXT("OutfitSlot_%s"), *UEnum::GetValueAsString(Slot));
	USkeletalMeshComponent* SlotComp = NewObject<USkeletalMeshComponent>(OwningCharacter, ComponentName);
	SlotComp->SetupAttachment(OwningCharacter->GetMesh());
	// Same technique as the hair's leader-pose sharing: the garment shares
	// the body's bone transforms directly rather than running its own
	// animation, so it moves with the body for free.
	SlotComp->SetLeaderPoseComponent(OwningCharacter->GetMesh());
	SlotComp->RegisterComponent();

	SlotComponents.Add(Slot, SlotComp);
	return SlotComp;
}

void UMelodiaOutfitComponent::EquipGarment(const EMelodiaOutfitSlot Slot, USkeletalMesh* GarmentMesh)
{
	USkeletalMeshComponent* SlotComp = FindOrCreateSlotComponent(Slot);
	if (!SlotComp)
	{
		return;
	}

	if (!GarmentMesh)
	{
		SlotComp->SetVisibility(false);
		return;
	}

	SlotComp->SetSkeletalMesh(GarmentMesh);
	SlotComp->SetVisibility(true);
}

USkeletalMeshComponent* UMelodiaOutfitComponent::GetSlotComponent(const EMelodiaOutfitSlot Slot) const
{
	const TObjectPtr<USkeletalMeshComponent>* Found = SlotComponents.Find(Slot);
	return Found ? Found->Get() : nullptr;
}

bool UMelodiaOutfitComponent::IsSlotEquipped(const EMelodiaOutfitSlot Slot) const
{
	const USkeletalMeshComponent* SlotComp = GetSlotComponent(Slot);
	return SlotComp && SlotComp->IsVisible() && SlotComp->GetSkeletalMeshAsset();
}
