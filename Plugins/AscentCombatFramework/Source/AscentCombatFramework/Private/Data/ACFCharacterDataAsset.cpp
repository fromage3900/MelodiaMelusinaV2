// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFCharacterDataAsset.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/SkinnedAssetCommon.h"
#include "Materials/MaterialInterface.h"
#include "Data/ACFCharacterFragment.h"

UACFCharacterDataAsset::UACFCharacterDataAsset()
{
	MeshComponents.Add(FSkeletalMeshComponentData());
	MeshComponents[0].ComponentTag = FName("Mesh");
}

bool UACFCharacterDataAsset::GetInitialAttributes(FACFAttributeInits& OutAttributes) const
{
	if (!CharacterRow.DataTable || CharacterRow.RowName.IsNone())
	{
		return false;
	}

	const FACFAttributeInits* AttributeInits = CharacterRow.DataTable->FindRow<FACFAttributeInits>(CharacterRow.RowName, TEXT("UACFCharacterDataAsset::GetInitialAttributes"));
	if (!AttributeInits)
	{
		return false;
	}

	OutAttributes = *AttributeInits;
	return true;
}

TArray<FAttributeInit> UACFCharacterDataAsset::GetInitialStats() const
{
	FACFAttributeInits AttributeInits;
	if (GetInitialAttributes(AttributeInits))
	{
		return AttributeInits.PawnAttributesInit;
	}

	return TArray<FAttributeInit>();
}

#if WITH_EDITOR
void UACFCharacterDataAsset::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	if (PropertyChangedEvent.Property)
	{
		FName PropertyName = PropertyChangedEvent.Property->GetFName();
		if (PropertyName == GET_MEMBER_NAME_CHECKED(FSkeletalMeshComponentData, SkeletalMesh))
		{
			for (FSkeletalMeshComponentData& MeshComponent : MeshComponents)
			{
				if (MeshComponent.SkeletalMesh)
				{
					UpdateMaterialArray(MeshComponent);
				}
			}
		}
	}
}

void UACFCharacterDataAsset::PostEditChangeChainProperty(FPropertyChangedChainEvent& PropertyChangedEvent)
{
	Super::PostEditChangeChainProperty(PropertyChangedEvent);

	if (PropertyChangedEvent.Property)
	{
		FName PropertyName = PropertyChangedEvent.Property->GetFName();
		if (PropertyName == GET_MEMBER_NAME_CHECKED(UACFCharacterDataAsset, MeshComponents))
		{
			for (FSkeletalMeshComponentData& MeshComponent : MeshComponents)
			{
				if (MeshComponent.SkeletalMesh)
				{
					UpdateMaterialArray(MeshComponent);
				}
			}
		}
	}
}

void UACFCharacterDataAsset::UpdateMaterialArray(FSkeletalMeshComponentData& MeshData)
{
	if (!MeshData.SkeletalMesh)
	{
		MeshData.MaterialOverrides.Empty();
		return;
	}

	const TArray<FSkeletalMaterial>& MeshMaterials = MeshData.SkeletalMesh->GetMaterials();
	TArray<FMaterialOverrideData> ExistingOverrides = MeshData.MaterialOverrides;
	MeshData.MaterialOverrides.Empty();
	MeshData.MaterialOverrides.SetNum(MeshMaterials.Num());

	for (int32 i = 0; i < MeshMaterials.Num(); i++)
	{
		if (i < ExistingOverrides.Num() && ExistingOverrides[i].Material != nullptr)
		{
			MeshData.MaterialOverrides[i] = ExistingOverrides[i];
		}
		else
		{
			MeshData.MaterialOverrides[i].Material = MeshMaterials[i].MaterialInterface;
			MeshData.MaterialOverrides[i].SlotName = MeshMaterials[i].MaterialSlotName;
		}
	}
}
#endif

UACFCharacterFragment* UACFCharacterDataAsset::GetFragmentByClass(TSubclassOf<UACFCharacterFragment> FragmentClass) const
{
	if (!FragmentClass) return nullptr;
	for (UACFCharacterFragment* Fragment : Fragments)
	{
		if (Fragment && Fragment->IsA(FragmentClass)) return Fragment;
	}
	return nullptr;
}
