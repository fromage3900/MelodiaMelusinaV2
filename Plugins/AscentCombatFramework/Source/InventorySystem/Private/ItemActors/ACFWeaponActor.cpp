// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ItemActors/ACFWeaponActor.h"
#include "ACMCollisionManagerComponent.h"
#include "ARSFunctionLibrary.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFTeamManagerComponent.h"
#include "GameFramework/GameStateBase.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "Items/ACFWeapon.h"
#include "Kismet/GameplayStatics.h"
#include <Animation/AnimMontage.h>
#include <Components/SceneComponent.h>
#include <Components/SkeletalMeshComponent.h>
#include <Engine/StreamableManager.h>
#include <GameFramework/DamageType.h>
#include <Logging.h>
#include <Runtime/Engine/Classes/Engine/AssetManager.h>
#include "ACFTeamManagerSubsystem.h"
#include <Components/SkeletalMeshComponent.h>
#include <Components/SceneComponent.h>
#include <Engine/World.h>
#include "ARSStatisticsComponent.h"
#include "ACFItemSystemFunctionLibrary.h"

AACFWeaponActor::AACFWeaponActor()
{
	HandlePos = CreateDefaultSubobject<USceneComponent>(TEXT("Handle"));
	SetRootComponent(HandlePos);
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));

	Mesh->SetupAttachment(HandlePos);
	Mesh->SetRelativeLocation(FVector(0.f, 0.f, 0.f));
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	CollisionComp = CreateDefaultSubobject<UACMCollisionManagerComponent>(TEXT("Collisions Manager"));
	LeftHandleIKPos = CreateDefaultSubobject<USceneComponent>(TEXT("Left Hand Handle"));
	LeftHandleIKPos->SetupAttachment(Mesh);
}

void AACFWeaponActor::PlayWeaponAnim(const FGameplayTag& weaponAnim)
{
	if (Mesh && GetWeaponDefinition()->GetWeaponAnimations().Contains(weaponAnim)) {
		UAnimMontage* weaponMontage = GetWeaponDefinition()->GetWeaponAnimations().FindChecked(weaponAnim);
		Mesh->PlayAnimation(weaponMontage, false);
	}
	else {
		UE_LOG(ACFInventoryLog, Warning, TEXT("NO  COLLISION MANAGER ON WEAPON - AACFWeapon"));
	}
}

UACFWeapon* AACFWeaponActor::GetWeaponDefinition() const
{
	return Cast<UACFWeapon>(ItemDefinition);
}

void AACFWeaponActor::InitItemActor(APawn* inOwner, UACFItem* inItemDefinition)
{
	Super::InitItemActor(inOwner, inItemDefinition);
	if (GetWeaponDefinition()) {
		TSoftObjectPtr<USkeletalMesh> skinnedAsset = GetWeaponDefinition()->GetWeaponMesh();

		FStreamableManager& Streamable = UAssetManager::GetStreamableManager();
		Streamable.RequestAsyncLoad(skinnedAsset.ToSoftObjectPath(), FStreamableDelegate::CreateUObject(this, &AACFWeaponActor::OnAssetLoaded));
	}
}

void AACFWeaponActor::OnWeaponUnsheathed_Implementation()
{

	if (CollisionComp) {
		CollisionComp->SetActorOwner(ItemOwner);
		CollisionComp->SetupCollisionManager(Mesh, UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels());
		const bool bImplements = ItemOwner->GetClass()->ImplementsInterface(UACFEntityInterface::StaticClass());
		if (bImplements) {
			const FGameplayTag combatTeam = IACFEntityInterface::Execute_GetEntityCombatTeam(ItemOwner);
			if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
				CollisionComp->AddCollisionChannels(TeamSubsystem->GetHostileCollisionChannels(combatTeam));
			}
			else {
				UE_LOG(ACFInventoryLog, Error, TEXT("Missing  TeamsManager in GameState - AACFWeaponActor"));
			}
		}
	}
	else {
		UE_LOG(ACFInventoryLog, Warning, TEXT("Missing Collision Comp! - AACFWeaponActor"));
	}
}

void AACFWeaponActor::OnWeaponSheathed_Implementation()
{
}

void AACFWeaponActor::OnEquipped_Implementation()
{
}

void AACFWeaponActor::OnUnequipped_Implementation()
{
}

void AACFWeaponActor::Internal_OnWeaponUnsheathed()
{
	AlignWeapon();
	if (GetWeaponDefinition() && GetWeaponDefinition()->GetItemOwner()) {

		UARSStatisticsComponent* statcomp = GetWeaponDefinition()->GetItemOwner()->FindComponentByClass<UARSStatisticsComponent>();
		if (statcomp) {
			UnsheatedModifierHandle = statcomp->AddAttributeSetModifier(GetWeaponDefinition()->GetUnsheatedAttributeSetModifier());
		}
	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Missing Item Definition - AACFWeaponActor"));
	}

	OnWeaponUnsheathed();
}

void AACFWeaponActor::Internal_OnWeaponSheathed()
{
	AlignWeapon();
	if (GetWeaponDefinition()) {
		GetWeaponDefinition()->RemoveModifierToOwner(UnsheatedModifierHandle);
	}
	else {
		UE_LOG(ACFInventoryLog, Error, TEXT("Missing Item Definition - AACFWeaponActor"));
	}
	OnWeaponSheathed();
}

void AACFWeaponActor::OnAssetLoaded()
{
	TSoftObjectPtr<USkeletalMesh> skinnedAsset = GetWeaponDefinition()->GetWeaponMesh();
	USkeletalMesh* skelMesh = skinnedAsset.Get();
	if (Mesh && skelMesh) {
		Mesh->SetSkeletalMesh(skelMesh);
		AlignWeapon();
		if (CollisionComp) {
			CollisionComp->SetupCollisionManager(Mesh, UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels());
		}
	}
	else {
		UE_LOG(ACFInventoryLog, Warning, TEXT("AACFWeaponActor::OnAssetLoaded - Skinned asset is null!"));
	}
}

void AACFWeaponActor::AlignWeapon()
{
	if (HandlePos) {
		FHitResult outResult;
		Mesh->SetRelativeTransform(GetWeaponDefinition()->GetAttachmentOffset(), true, &outResult, ETeleportType::TeleportPhysics);
	}
	else {
		UE_LOG(ACFInventoryLog, Warning, TEXT("NO HANDLE COMPONENT! - ACFWeapon"));
	}
}

void AACFWeaponActor::BeginPlay()
{
	Super::BeginPlay();
	Mesh->AttachToComponent(HandlePos, FAttachmentTransformRules(EAttachmentRule::SnapToTarget, false));

	// actors are only spawned when the item is equipped, so we can call this here
	OnEquipped();
}

void AACFWeaponActor::EndPlay(const EEndPlayReason::Type reason)
{

	// actors are only spawned when the item is equipped, so we can call this here
	OnUnequipped();
	Super::EndPlay(reason);
}
