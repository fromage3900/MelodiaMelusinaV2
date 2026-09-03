// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendBPLibrary.h"

#include "EngineUtils.h"
#include "MeshBlendActivatorSubsystem.h"
#include "MeshBlendShared.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Misc/UObjectToken.h"
#include "UObject/ObjectMacros.h"
#include "UObject/Package.h"

#if WITH_EDITOR
#include "Editor.h"
#include "Logging/MessageLog.h"
#endif

#define LOCTEXT_NAMESPACE "UMeshBlendBPLibrary"

#if WITH_EDITOR
bool MaterialHasMeshBlendActivator(const UMaterialInterface* Material)
{
	if (Material)
	{
		bool bIsChecked = false;
		FGuid ExpressionGuid;

		if (Material->GetStaticSwitchParameterValue(TEXT("Use Static Value"), bIsChecked, ExpressionGuid))
		{
			return true;
		}
	}

	return false;
}
#endif

void UMeshBlendBPLibrary::SetBlendUserDataOnMesh(UStaticMesh* Mesh, const EAutoBlendOption NewBlendOption)
{
	if (Mesh)
	{
#if WITH_EDITOR
		const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
		bool bHasMaterialWithMeshBlendActivator = false;

		for (const FStaticMaterial& StaticMaterial : StaticMaterials)
		{
			if (MaterialHasMeshBlendActivator(StaticMaterial.MaterialInterface))
			{
				bHasMaterialWithMeshBlendActivator = true;
			}
		}

		if (!bHasMaterialWithMeshBlendActivator)
		{
			FMessageLog("MapCheck")
				.Warning()
				->AddToken(FAssetNameToken::Create(Mesh->GetPackage()->GetPathName()))
				->AddToken(FTextToken::Create(LOCTEXT(
					"MapCheck_MeshBlendMaterialNotSetup",
					"The mesh does not have any materials set up with the MeshBlend activator. MeshBlend needs this to work.")))
				->AddToken(FURLToken::Create(
					"https://meshblend.lervik.com",
					LOCTEXT("MapCheck_MeshBlendDocumentation_UrlText", "Click to open documentation")));

			FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
		}
#endif

		bool bHasChanged = false;

		if (UAssetUserData* ExistingData = Mesh->GetAssetUserDataOfClass(UAutoBlendUserData::StaticClass()))
		{
			if (UAutoBlendUserData* ExistingAutoBlendUserData = Cast<UAutoBlendUserData>(ExistingData))
			{
				if (ExistingAutoBlendUserData->AutoBlendOption != NewBlendOption)
				{
					ExistingAutoBlendUserData->AutoBlendOption = NewBlendOption;
					bHasChanged = true;
				}
			}
		}
		else
		{
			UAutoBlendUserData* NewAssetUserData = NewObject<UAutoBlendUserData>(Mesh, NAME_None, RF_Public | RF_Transactional);
			NewAssetUserData->AutoBlendOption = NewBlendOption;
			Mesh->AddAssetUserData(NewAssetUserData);
			bHasChanged = true;
		}

		if (bHasChanged)
		{
			Mesh->MarkPackageDirty();

#if WITH_EDITOR
			if (GWorld)
			{
				RefreshActorsReferencingAsset(Mesh, GWorld);
			}
#endif
		}
	}
}

void UMeshBlendBPLibrary::ClearBlendUserDataFromMesh(UStaticMesh* Mesh)
{
	if (Mesh)
	{
		if (Mesh->GetAssetUserDataOfClass(UAutoBlendUserData::StaticClass()))
		{
			Mesh->RemoveUserDataOfClass(UAutoBlendUserData::StaticClass());
			Mesh->MarkPackageDirty();

#if WITH_EDITOR
			if (GWorld)
			{
				RefreshActorsReferencingAsset(Mesh, GWorld);
			}
#endif
		}
	}
}

void UMeshBlendBPLibrary::SetBlendOptionOnActor(AActor* Actor, const EAutoBlendOption NewBlendOption)
{
	if (Actor)
	{
#if WITH_EDITOR

		bool bHasMaterialWithMeshBlendActivator = false;

		for (UActorComponent* Component : Actor->GetComponents())
		{
			if (const UMeshComponent* MeshComponent = Cast<UMeshComponent>(Component))
			{
				for (const UMaterialInterface* Material : MeshComponent->GetMaterials())
				{
					if (MaterialHasMeshBlendActivator(Material))
					{
						bHasMaterialWithMeshBlendActivator = true;
					}
				}
			}
		}

		if (!bHasMaterialWithMeshBlendActivator)
		{
			FMessageLog("MapCheck")
				.Warning()
				->AddToken(FUObjectToken::Create(Actor))
				->AddToken(FTextToken::Create(LOCTEXT(
					"MapCheck_MeshBlendMaterialNotSetup",
					"The mesh does not have any materials set up with the MeshBlend activator. MeshBlend needs this to work.")))
				->AddToken(FURLToken::Create(
					"https://meshblend.lervik.com",
					LOCTEXT("MapCheck_MeshBlendDocumentation_UrlText", "Click to open documentation")));

			FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
		}

#endif

		FName AutoBlendTag;

		switch (NewBlendOption)
		{
		case Small:
			AutoBlendTag = GName_AutoBlendSmall;
			break;
		case Medium:
			AutoBlendTag = GName_AutoBlendMedium;
			break;
		case Large:
			AutoBlendTag = GName_AutoBlendLarge;
			break;
		case Extra_Large:
			AutoBlendTag = GName_AutoBlendExtraLarge;
			break;
		case Disabled:
			AutoBlendTag = GName_Disabled;
			break;
		default:
			return;
		}

		TArray<FName> Tags = Actor->Tags;

		if (Tags.Contains(AutoBlendTag))
		{
			return;
		}

		const auto Property = Actor->GetClass()->FindPropertyByName("Tags");
		const auto TagsProperty = CastField<FArrayProperty>(Property);
		const auto ArrayPtr = TagsProperty->ContainerPtrToValuePtr<TArray<FName>>(Actor);
		FScriptArrayHelper ArrayHelper(TagsProperty, ArrayPtr);

		Tags.Remove(GName_AutoBlendSmall);
		Tags.Remove(GName_AutoBlendMedium);
		Tags.Remove(GName_AutoBlendLarge);
		Tags.Remove(GName_AutoBlendExtraLarge);
		Tags.Remove(GName_Disabled);
		Tags.Add(AutoBlendTag);

		ArrayHelper.Resize(Tags.Num());

		for (int32 i = 0; i < Tags.Num(); i++)
		{
			FName* NamePtr = reinterpret_cast<FName*>(ArrayHelper.GetRawPtr(i));
			*NamePtr = Tags[i];
		}

		Actor->MarkPackageDirty();
		RefreshBlendOnActor(Actor, false);
	}
}

void UMeshBlendBPLibrary::DisableBlendOnActor(AActor* Actor)
{
	SetBlendOptionOnActor(Actor, Disabled);
}

void UMeshBlendBPLibrary::RefreshBlendOnActor(AActor* Actor, const bool bSoftReset)
{
	if (UMeshBlendActivatorSubsystem* Subsystem = UMeshBlendActivatorSubsystem::GetInstance(Actor->GetWorld()))
	{
		Subsystem->RefreshActor(Actor, bSoftReset);
	}
}

void UMeshBlendBPLibrary::ClearBlendOptionFromActor(AActor* Actor)
{
	if (Actor)
	{
		TArray<FName> Tags = Actor->Tags;
		const auto Property = Actor->GetClass()->FindPropertyByName("Tags");
		const auto TagsProperty = CastField<FArrayProperty>(Property);
		const auto ArrayPtr = TagsProperty->ContainerPtrToValuePtr<TArray<FName>>(Actor);
		FScriptArrayHelper ArrayHelper(TagsProperty, ArrayPtr);

		Tags.Remove(GName_AutoBlendSmall);
		Tags.Remove(GName_AutoBlendMedium);
		Tags.Remove(GName_AutoBlendLarge);
		Tags.Remove(GName_AutoBlendExtraLarge);
		Tags.Remove(GName_Disabled);

		ArrayHelper.Resize(Tags.Num());

		for (int32 i = 0; i < Tags.Num(); i++)
		{
			FName* NamePtr = reinterpret_cast<FName*>(ArrayHelper.GetRawPtr(i));
			*NamePtr = Tags[i];
		}

		Actor->MarkPackageDirty();
		RefreshBlendOnActor(Actor, false);
	}
}

#if WITH_EDITOR

void UMeshBlendBPLibrary::RefreshActorsReferencingAsset(const UStaticMesh* Mesh, const UWorld* World)
{
	if (Mesh && Mesh->IsAsset())
	{
		if (UMeshBlendActivatorSubsystem* Subsystem = UMeshBlendActivatorSubsystem::GetInstance(World))
		{
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				if (AActor* Actor = *It)
				{
					TArray<UObject*> ReferencedObjects;
					Actor->GetReferencedContentObjects(ReferencedObjects);

					for (const UObject* ReferencedObject : ReferencedObjects)
					{
						if (ReferencedObject == Mesh)
						{
							Subsystem->RefreshActor(Actor, false);
							break;
						}
					}
				}
			}
		}
	}
}

#endif

#undef LOCTEXT_NAMESPACE
