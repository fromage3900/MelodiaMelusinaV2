// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFCharacterInitializerComponent.h"
#include "Data/ACFCharacterDataAsset.h"
#include "Data/ACFCharacterFragment.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFTeamComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Config/ACFEffectsConfigDataAsset.h"
#include "ACFGASAttributesComponent.h"
#include "GameFramework/Character.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "Animation/AnimInstance.h"
#include "AbilitySystemComponent.h"
#include <ALSFunctionLibrary.h>

#if !UE_BUILD_SHIPPING
#include "Logging.h"
#endif
#include "TimerManager.h"

UACFCharacterInitializerComponent::UACFCharacterInitializerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	bWantsInitializeComponent = true;
	SetIsReplicatedByDefault(true);
}

void UACFCharacterInitializerComponent::Init()
{
	InitFromDataAsset(CharacterInitDataAsset, CharacterInitLevel);
}

void UACFCharacterInitializerComponent::InitializeComponent()
{
	Super::InitializeComponent();

	AActor* Owner = GetOwner();
	OwningPawn = Cast<AACFCharacter>(Owner);
	if (!IsTemplate() && Owner && CharacterInitDataAsset)
	{
		CharacterDataAsset = CharacterInitDataAsset;
		ApplyAllMeshData();
		bAppliedAutoAppearanceBeforeBeginPlay = true;
	}
}

void UACFCharacterInitializerComponent::BeginPlay()
{
	Super::BeginPlay();
	OwningPawn = Cast<AACFCharacter>(GetOwner());

	if (CharacterInitDataAsset)
	{
		if (GetOwner()->HasAuthority())
		{
			// Run Init() synchronously so ASC / attributes are fully set up in the same
			// BeginPlay wave — GASStatisticsComponent::BeginPlay needs the ASC cache to be
			// populated (abilityComp) before it can bind the health attribute delegate.
			CharacterDataAsset = CharacterInitDataAsset;
			InternalHandleServerInit(CharacterInitLevel, !bAppliedAutoAppearanceBeforeBeginPlay);
		}
		else
		{
			// Client already has the asset from the archetype — run client init directly
			// instead of waiting for OnRep which may not fire for placed-in-level actors.
			CharacterDataAsset = CharacterInitDataAsset;
			InternalHandleClientInit(!bAppliedAutoAppearanceBeforeBeginPlay);
		}
	}
}

void UACFCharacterInitializerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFCharacterInitializerComponent, CharacterDataAsset);
}

void UACFCharacterInitializerComponent::InitFromDataAsset(UACFCharacterDataAsset* charData, int32 Level)
{
	if (!charData) {
		return;
	}
	if (!GetOwner()->HasAuthority()) {
		return;
	}

	CharacterDataAsset = charData;
	InternalHandleServerInit(Level);
}

void UACFCharacterInitializerComponent::OnRep_CharacterDataAsset()
{
	if (!OwningPawn) OwningPawn = Cast<AACFCharacter>(GetOwner());
	if (!CharacterDataAsset) return;
	InternalHandleClientInit();
}

void UACFCharacterInitializerComponent::ApplyFragmentsData()
{
	if (!OwningPawn) OwningPawn = Cast<AACFCharacter>(GetOwner());
	if (OwningPawn && CharacterDataAsset)
	{
		for (UACFCharacterFragment* Fragment : CharacterDataAsset->Fragments)
		{
			if (Fragment) Fragment->ApplyFragment(OwningPawn);
		}
	}
}

void UACFCharacterInitializerComponent::InternalHandleServerInit(int32 Level, bool bApplyAppearance)
{
	if (!OwningPawn || !CharacterDataAsset) return;

	// Init ASC (owner/avatar) first so attribute replication works when we set stats
	UACFAbilitySystemComponent* AbilityComp = OwningPawn->FindComponentByClass<UACFAbilitySystemComponent>();
	if (AbilityComp)
	{
		AbilityComp->InitAbilityActorInfo(OwningPawn, OwningPawn);
		AbilityComp->ClearAllAbilities();
		AbilityComp->GrantAbilitySet(CharacterDataAsset->DefaultAbilitySet, FGameplayTag());
		for (const auto& AbilitySet : CharacterDataAsset->MovesetAbilities)
		{
			AbilityComp->GrantAbilitySet(AbilitySet.Value, AbilitySet.Key);
		}
	}

	UACFGASAttributesComponent* AttributesComp = OwningPawn->FindComponentByClass<UACFGASAttributesComponent>();
	if (AttributesComp)
	{
		AttributesComp->SetLevelingType(CharacterDataAsset->LevelingType);
		AttributesComp->SetCharacterRow(CharacterDataAsset->CharacterRow);
		AttributesComp->SetAttributesByLevelCurve(CharacterDataAsset->AttributesByLevelCurve);
		AttributesComp->SetAffectedByDifficultyLevel(CharacterDataAsset->bAffectedByDifficultyLevel);
		AttributesComp->ForceSetLevel(Level);
		AttributesComp->InitializeAttributeSet();
	}

	UACFTeamComponent* TeamComp = OwningPawn->FindComponentByClass<UACFTeamComponent>();
	if (TeamComp) TeamComp->SetTeam(CharacterDataAsset->Team);

	if (UACFCharacterMovementComponent* MovementComp = OwningPawn->FindComponentByClass<UACFCharacterMovementComponent>())
	{
		MovementComp->SetRotationMode(CharacterDataAsset->RotationMode);
	}

	if (CharacterDataAsset->CharacterPortrait) {
		OwningPawn->SetCharacterPortrait(CharacterDataAsset->CharacterPortrait);
	}
	OwningPawn->SetCharacterName(CharacterDataAsset->ChatacterName);

	ApplyCapsuleSize();
	if (bApplyAppearance)
	{
		ApplyAllMeshData();
	}
	ApplyFragmentsData();
	ApplyEquipData();

	if (CharacterDataAsset->CharacterEffectsConfig)
	{
		if (UACFEffectsManagerComponent* EffectsComp = OwningPawn->FindComponentByClass<UACFEffectsManagerComponent>())
		{
			EffectsComp->SetCharacterEffectsConfig(CharacterDataAsset->CharacterEffectsConfig);
		}
	}

	RefreshAnimationLayers();

	HandleServerInit();
}

void UACFCharacterInitializerComponent::InternalHandleClientInit(bool bApplyAppearance)
{
	ApplyCapsuleSize();
	if (bApplyAppearance)
	{
		ApplyAllMeshData();
	}
	ApplyFragmentsData();

	if (OwningPawn && CharacterDataAsset)
	{
		OwningPawn->SetCharacterName(CharacterDataAsset->ChatacterName);
		if (CharacterDataAsset->CharacterPortrait)
		{
			OwningPawn->SetCharacterPortrait(CharacterDataAsset->CharacterPortrait);
		}
		if (UACFCharacterMovementComponent* MovementComp = OwningPawn->FindComponentByClass<UACFCharacterMovementComponent>())
		{
			MovementComp->SetRotationMode(CharacterDataAsset->RotationMode);
		}
	}

	if (CharacterDataAsset && CharacterDataAsset->CharacterEffectsConfig)
	{
		if (UACFEffectsManagerComponent* EffectsComp = OwningPawn->FindComponentByClass<UACFEffectsManagerComponent>())
		{
			EffectsComp->SetCharacterEffectsConfig(CharacterDataAsset->CharacterEffectsConfig);
		}
	}

	RefreshAnimationLayers();

	HandleClientInit();
}

void UACFCharacterInitializerComponent::RefreshAnimationLayers()
{
	// Re-broadcast OnEquipmentChanged so AACFCharacter::HandleEquipmentChanged runs and
	// (re)links the AnimBP layers via SetMoveset / SetAnimationOverlay. Without this,
	// characters with no starting weapon never trigger HandleEquipmentChanged and the
	// AnimBP layers stay unlinked → T-pose. Equipping a weapon later normally fires
	// the broadcast and "fixes" the pose; we just make it always happen at init.
	if (!OwningPawn) return;
	if (UACFEquipmentComponent* EquipComp = OwningPawn->FindComponentByClass<UACFEquipmentComponent>())
	{
		EquipComp->OnEquipmentChanged.Broadcast(EquipComp->GetCurrentEquipment());
	}
}

void UACFCharacterInitializerComponent::ApplyEquipData()
{
	UACFEquipmentComponent* InventoryComp = OwningPawn ? OwningPawn->FindComponentByClass<UACFEquipmentComponent>() : nullptr;
	if (InventoryComp && CharacterDataAsset)
	{
		InventoryComp->SetCurrency(CharacterDataAsset->Currency);
		if (!UALSFunctionLibrary::ShouldSaveActor(OwningPawn) || UALSFunctionLibrary::IsNewGame(OwningPawn))
		{
			InventoryComp->SetStartingItems(CharacterDataAsset->StartingItems);
			InventoryComp->RefreshEquipment();
		}
	}
}

void UACFCharacterInitializerComponent::ApplyCapsuleSize()
{
	if (!CharacterDataAsset || !OwningPawn) return;

	if (UCapsuleComponent* Capsule = OwningPawn->GetCapsuleComponent())
	{
		// SetCapsuleSize updates the shape and notifies the physics engine.
		// On the server the new values are replicated to all clients automatically
		// via UCapsuleComponent's built-in property replication.
		// We also call this on the client path so placed-in-level actors get the
		// correct size immediately, before any replication round-trip arrives.
		Capsule->SetCapsuleSize(CharacterDataAsset->CapsuleRadius, CharacterDataAsset->CapsuleHalfHeight);
	}
}

void UACFCharacterInitializerComponent::ApplyAllMeshData(bool bOverrideAnimInstance)
{
	if (!CharacterDataAsset)
	{
		return;
	}
	ApplyAppearence(CharacterDataAsset->MeshComponents, bOverrideAnimInstance);
}

void UACFCharacterInitializerComponent::ApplyAppearanceFromDataAsset(UACFCharacterDataAsset* charData, bool bOverrideAnimInstance)
{
	CharacterDataAsset = charData;

#if WITH_EDITOR
	// SetActorLabel only updates the editor-visible label (FString).
	// It does NOT call Rename() nor change GetFName(), so the save system
	// (which identifies actors by FName) is unaffected.
	if (charData)
	{
		if (AActor* Owner = GetOwner())
		{
			Owner->SetActorLabel(charData->ChatacterName.ToString());
		}
	}
#endif

	ApplyAllMeshData(bOverrideAnimInstance);
}

void UACFCharacterInitializerComponent::ApplyAppearence(const TArray<FSkeletalMeshComponentData>& appearence, const bool bOverrideAnimInstance)
{
	TArray<USkeletalMeshComponent*> SkeletalComponents;
	GetOwner()->GetComponents<USkeletalMeshComponent>(SkeletalComponents);

	for (const FSkeletalMeshComponentData& MeshData : appearence)
	{
		if (MeshData.ComponentTag == NAME_None)
		{
			USkeletalMeshComponent* MeshComp = nullptr;
			const UACFEquipmentComponent* EquipComp = GetOwner()->FindComponentByClass<UACFEquipmentComponent>();
			if (EquipComp)
			{
				MeshComp = EquipComp->GetMainMesh();
			}
			if (!MeshComp)
			{
				if (const ACharacter* OwnerCharacter = Cast<ACharacter>(GetOwner()))
				{
					MeshComp = OwnerCharacter->GetMesh();
				}
			}
			ApplyMeshDataToComponent(MeshComp, MeshData, bOverrideAnimInstance);
			continue;
		}
		for (USkeletalMeshComponent* Component : SkeletalComponents)
		{
			if (Component->ComponentHasTag(MeshData.ComponentTag))
			{
				ApplyMeshDataToComponent(Component, MeshData, bOverrideAnimInstance);
				break;
			}
		}
	}
}

void UACFCharacterInitializerComponent::ApplyMeshDataToComponent(USkeletalMeshComponent* Component,
	const FSkeletalMeshComponentData& MeshData, const bool bOverrideAnimInstance)
{
	if (!Component || !MeshData.SkeletalMesh) {
		return;
	}
	// SetSkinnedAssetAndUpdate resets VisibilityBasedAnimTickOption to the component CDO default.
	// On dedicated servers (no renderer) the default disables animation ticking for invisible meshes,
	// so montages never advance and UAnimNotify events (ACFNotifyAction) never fire server-side.
	// Only force AlwaysTickPoseAndRefreshBones on dedicated server; on listen-server and standalone
	// leave the original setting so runtime retargeting and LOD/update-rate optimizations are preserved.
	if (const UWorld* World = Component->GetWorld())
	{
		if (World->GetNetMode() == NM_DedicatedServer)
		{
			Component->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		}
	}
	const bool bShouldOverrideAnimInstance = MeshData.AnimInstance && bOverrideAnimInstance;

	Component->SetSkinnedAssetAndUpdate(MeshData.SkeletalMesh);

	if (bShouldOverrideAnimInstance)
	{
		Component->SetAnimationMode(EAnimationMode::AnimationBlueprint, false);
		Component->SetAnimInstanceClass(MeshData.AnimInstance);
	}

	for (int32 i = 0; i < MeshData.MaterialOverrides.Num(); ++i)
	{
		if (MeshData.MaterialOverrides.IsValidIndex(i))
			Component->SetMaterial(i, MeshData.MaterialOverrides[i].Material);
	}
}

#if WITH_EDITOR
void UACFCharacterInitializerComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	if (PropertyChangedEvent.GetPropertyName() == GET_MEMBER_NAME_CHECKED(UACFCharacterInitializerComponent, CharacterInitDataAsset))
	{
		if (AActor* Owner = GetOwner())
		{
			if (CharacterInitDataAsset)
			{
				ApplyAppearanceFromDataAsset(CharacterInitDataAsset, true);
			}
			else
			{
				Owner->SetActorLabel(FString());
			}
		}
	}
}

void UACFCharacterInitializerComponent::ApplyAppearanceInEditor()
{
	if (CharacterInitDataAsset)
	{
		ApplyAppearanceFromDataAsset(CharacterInitDataAsset, true);
	}
}

#endif
