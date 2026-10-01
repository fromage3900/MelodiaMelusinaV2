// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFArmorSlotComponent.h"
#include "Items/ACFArmor.h"
#include <Engine/AssetManager.h>
#include <Engine/StreamableManager.h>
#include <Logging.h>


UACFArmorSlotComponent::UACFArmorSlotComponent()
{
	SetIsReplicatedByDefault(false);
}

void UACFArmorSlotComponent::InitArmor(UACFArmor* armorMesh)
{
	ArmorDefinition = armorMesh;
	if (ArmorDefinition) {
		skinnedArmor = GetArmorDefinition()->GetArmorMesh(GetOwner());

		FStreamableManager& Streamable = UAssetManager::GetStreamableManager();
		Streamable.RequestAsyncLoad(skinnedArmor.ToSoftObjectPath(), FStreamableDelegate::CreateUObject(this, &UACFArmorSlotComponent::OnAssetLoaded));
	}
}

void UACFArmorSlotComponent::ResetSlotToEmpty()
{
	if (EmptySlotMesh && hasEmptyVersion) {
		SetSkinnedAssetAndUpdate(EmptySlotMesh);
		skinnedArmor = nullptr; 
	}
	else {
		SetVisibility(false);
	}
}

void UACFArmorSlotComponent::BeginPlay()
{
	Super::BeginPlay();
}

void UACFArmorSlotComponent::InitializeComponent()
{
	Super::InitializeComponent();
	EmptySlotMesh = GetSkeletalMeshAsset();
	hasEmptyVersion = true;
}

void UACFArmorSlotComponent::OnAssetLoaded()
{
	USkinnedAsset* skelMesh = skinnedArmor.Get();
	if (skelMesh) {
		EmptyOverrideMaterials();
		SetSkinnedAssetAndUpdate(skelMesh);
		SetVisibility(true);
		bUseBoundsFromLeaderPoseComponent = true;
	}
	else {
		UE_LOG(ACFInventoryLog, Warning, TEXT("UACFArmorSlotComponent::OnAssetLoaded - Skinned asset is null "));
	}
}
