// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actors/ACFCharacter.h"
#include "ACFActionTypes.h"
#include "ACFActionsFunctionLibrary.h"
#include "ACFCCFunctionLibrary.h"
#include "ACFTeamManagerSubsystem.h"
#include "ACMCollisionManagerComponent.h"
#include "ARSStatisticsComponent.h"
#include "ATSBaseTargetComponent.h"
#include "ATSTargetingComponent.h"
#include "Animation/ACFAnimInstance.h"
#include "CCMFadeableActorComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFRagdollComponent.h"
#include "Components/ACFTeamManagerComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "Game/ACFDamageCalculation.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFGameInstance.h"
#include "Game/ACFGameMode.h"
#include "Game/ACFPlayerController.h"
#include "GameFramework/Actor.h"
#include "Interfaces/MovementBaseInterface.h"
#include "ItemActors/ACFMeleeWeaponActor.h"
#include "ItemActors/ACFRangedWeaponActor.h"
#include "Items/ACFMeleeWeapon.h"
#include "Items/ACFRangedWeapon.h"
#include "Items/ACFWeapon.h"
#include "MotionWarpingComponent.h"
#include "Net/UnrealNetwork.h"
#include <ALSFunctionLibrary.h>
#include <Components/AudioComponent.h>
#include <Components/CapsuleComponent.h>
#include <Engine/EngineTypes.h>
#include <GameFramework/Character.h>
#include <GameFramework/CharacterMovementComponent.h>
#include <GameFramework/DamageType.h>
#include <GameFramework/Pawn.h>
#include <GenericTeamAgentInterface.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>
#include <Logging.h>
#include <Perception/AIPerceptionStimuliSourceComponent.h>
#include <PhysicalMaterials/PhysicalMaterial.h>
#include <PhysicsEngine/BodyInstance.h>

#include "Camera/CameraComponent.h"
#include "Components/ACFTeamComponent.h"
#include <Engine/TimerHandle.h>
#include "ACFItemSystemFunctionLibrary.h"
#include "Data/ACFCharacterInitializerComponent.h"
#include <TimerManager.h>

// Sets default values
AACFCharacter::AACFCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer.SetDefaultSubobjectClass<UACFCharacterMovementComponent>(ACharacter::CharacterMovementComponentName))
{
	PrimaryActorTick.bCanEverTick = true;

	bReplicates = true;
	SetReplicateMovement(true);
	ActionsComp = CreateDefaultSubobject<UACFAbilitySystemComponent>(TEXT("Actions Manager"));
	InitializerComp = CreateDefaultSubobject<UACFCharacterInitializerComponent>(TEXT("Character Initializer"));
	StatisticsComp = CreateDefaultSubobject<UARSStatisticsComponent>(TEXT("Statistic Component"));
	CollisionComp = CreateDefaultSubobject<UACMCollisionManagerComponent>(TEXT("Collisions Manager"));
	EquipmentComp = CreateDefaultSubobject<UACFEquipmentComponent>(TEXT("Equipment Component"));
	//AIPerceptionStimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(TEXT("Perception Stimuli Component"));
	DamageHandlerComp = CreateDefaultSubobject<UACFDamageHandlerComponent>(TEXT("Damage Handler Component"));
	RagdollComp = CreateDefaultSubobject<UACFRagdollComponent>(TEXT("Ragdoll Component"));
	MotionWarpComp = CreateDefaultSubobject<UMotionWarpingComponent>(TEXT("Motion Warp Component"));
	FadeComp = CreateDefaultSubobject<UCCMFadeableActorComponent>(TEXT("Materials Override Component"));
	TeamComponent = CreateDefaultSubobject<UACFTeamComponent>(TEXT("TeamComponent"));
	StimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(TEXT("StimuliSource"));
	EffetsComp = CreateDefaultSubobject<UACFEffectsManagerComponent>(TEXT("Effects Comp"));
	PrimaryActorTick.bStartWithTickEnabled = false;

	AudioComp = CreateDefaultSubobject<UAudioComponent>(TEXT("Audio Component"));
	AudioComp->SetupAttachment(GetCapsuleComponent());
	AudioComp->SetRelativeLocation(FVector::ZeroVector);
	AudioComp->bAllowSpatialization = true;
	AudioComp->bOverrideAttenuation = false;

	// Don't rotate when the controller rotates. Let that just affect the camera.
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	CharacterName = FText::FromString("ACF Dude");

	BoneNameToDamageZoneMap.Add("head", EDamageZone::EHighDamage);
}

void AACFCharacter::PostInitProperties()
{
	Super::PostInitProperties();

	LocomotionComp = Cast<UACFCharacterMovementComponent>(GetCharacterMovement());

	if (!LocomotionComp) {
		UE_LOG(ACFLog, Warning, TEXT("Your Character Movement component MUST BE an ACFCharacterMovementComponent - AACFCharacter::PostInitProperties"));
	}
}

void AACFCharacter::EndPlay(EEndPlayReason::Type reason)
{
	Super::EndPlay(reason);
	// Safety net: if the character is removed from the world without going through the
	// normal death path (e.g. map unload, streaming out, dedicated-server cleanup),
	// destroy any still-live weapon actors so they don't persist as orphaned replicated actors.
	// IMPORTANT: pass bSpawnDrops=false. This path must NEVER spawn equipped/inventory drops
	// in the world (a streamed-out character that re-streams in must not have already dropped
	// its loot). Only the actual death path (OnEntityOwnerDeath) is allowed to spawn drops.
	// DestroyEquippedItems is a Server RPC that executes in-place when called on authority.
	if (HasAuthority() && EquipmentComp)
	{
		EquipmentComp->DestroyEquippedItems(/*bSpawnDrops=*/false);
	}
}

void AACFCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(AACFCharacter, CombatType);
	DOREPLIFETIME_CONDITION(AACFCharacter, ReplicatedAcceleration, COND_SimulatedOnly);
}

void AACFCharacter::PreReplication(IRepChangedPropertyTracker& ChangedPropertyTracker)
{
	Super::PreReplication(ChangedPropertyTracker);

	if (UCharacterMovementComponent* MovementComponent = GetCharacterMovement()) {
		// Compress Acceleration: XY components as direction + magnitude, Z component as direct value
		const double MaxAccel = MovementComponent->MaxAcceleration;
		const FVector CurrentAccel = MovementComponent->GetCurrentAcceleration();
		double AccelXYRadians, AccelXYMagnitude;
		FMath::CartesianToPolar(CurrentAccel.X, CurrentAccel.Y, AccelXYMagnitude, AccelXYRadians);

		ReplicatedAcceleration.AccelXYRadians = FMath::FloorToInt((AccelXYRadians / TWO_PI) * 255.0); // [0, 2PI] -> [0, 255]
		ReplicatedAcceleration.AccelXYMagnitude = FMath::FloorToInt((AccelXYMagnitude / MaxAccel) * 255.0); // [0, MaxAccel] -> [0, 255]
		ReplicatedAcceleration.AccelZ = FMath::FloorToInt((CurrentAccel.Z / MaxAccel) * 127.0); // [-MaxAccel, MaxAccel] -> [-127, 127]
	}
}

void AACFCharacter::OnRep_ReplicatedAcceleration()
{
	if (LocomotionComp) {
		// Decompress Acceleration
		const double MaxAccel = LocomotionComp->MaxAcceleration;
		const double AccelXYMagnitude = double(ReplicatedAcceleration.AccelXYMagnitude) * MaxAccel / 255.0; // [0, 255] -> [0, MaxAccel]
		const double AccelXYRadians = double(ReplicatedAcceleration.AccelXYRadians) * TWO_PI / 255.0; // [0, 255] -> [0, 2PI]

		FVector UnpackedAcceleration(FVector::ZeroVector);
		FMath::PolarToCartesian(AccelXYMagnitude, AccelXYRadians, UnpackedAcceleration.X, UnpackedAcceleration.Y);
		UnpackedAcceleration.Z = double(ReplicatedAcceleration.AccelZ) * MaxAccel / 127.0; // [-127, 127] -> [-MaxAccel, MaxAccel]

		LocomotionComp->SetReplicatedAcceleration(UnpackedAcceleration);
	}
}

void AACFCharacter::PreInitializeComponents()
{
	Super::PreInitializeComponents();
}

// Called when the game starts or when spawned
void AACFCharacter::BeginPlay()
{

	EffetsComp = FindComponentByClass<UACFEffectsManagerComponent>();

	Super::BeginPlay();
	InitializeCharacter();

	if (!IsAlive()) {
		HandleCharacterDeath();
	}
}

void AACFCharacter::InitializeCharacter()
{
	// InitAbilityActorInfo must run on BOTH server and client once BeginPlay has completed.
	// It may have been called earlier in InitializerComp::BeginPlay() but at that point
	// HasBegunPlay() was still false. The client also never receives it from the DA path.
	if (ActionsComp)
	{
		ActionsComp->InitAbilityActorInfo(this, this);
	}

	if (HasAuthority() && !bInitialized && bAutoInit) {
		if (InitializerComp && InitializerComp->GetAutoInitDataAsset()) {
			// Data Asset init (abilities, stats, mesh) already ran in InitializerComp::BeginPlay().
			// InitAbilityActorInfo has been refreshed above — nothing else needed here.
		}
		else {
			if (ActionsComp) {
				ActionsComp->SetMovesetActions(FGameplayTag());
				ActionsComp->GrantInitialAbilities();
			}
			if (StatisticsComp) {
				StatisticsComp->InitializeAttributeSet();
			}
			if (EquipmentComp) {
				if (!UALSFunctionLibrary::ShouldSaveActor(this) || UALSFunctionLibrary::IsNewGame(this)) {
					if (EquipmentComp->GetIsInitialized() == false) {
						EquipmentComp->InitializeStartingItems();
					}
				}
			}
		}
	}

	if (EquipmentComp && !EquipmentComp->OnEquipmentChanged.IsAlreadyBound(this, &AACFCharacter::HandleEquipmentChanged)) {
		EquipmentComp->OnEquipmentChanged.AddDynamic(
			this, &AACFCharacter::HandleEquipmentChanged);
	}

	if (DamageHandlerComp && !DamageHandlerComp->OnDamageReceived.IsAlreadyBound(this, &AACFCharacter::HandleDamageReceived)) {
		DamageHandlerComp->OnDamageReceived.AddDynamic(this, &AACFCharacter::HandleDamageReceived);
		DamageHandlerComp->OnDamageInflicted.AddDynamic(this, &AACFCharacter::HandleDamageInflicted);
	}

	if (CollisionComp) {
		SetupCollisionManager();
	}

	if (DamageHandlerComp && !DamageHandlerComp->OnOwnerDeath.IsAlreadyBound(this, &AACFCharacter::HandleCharacterDeath)) {
		DamageHandlerComp->OnOwnerDeath.AddDynamic(
			this, &AACFCharacter::HandleCharacterDeath);
	}
	bInitialized = true;
	OnCharacterFullyInitialized.Broadcast();
}

void AACFCharacter::HandleEquipmentChanged(const FEquipment& equipment)
{
	FGameplayTag movesetTag, overlayTag, actionsTag;

	if (EquipmentComp) {
		actionsTag = EquipmentComp->GetCurrentDesiredMovesetActionTag();
		overlayTag = EquipmentComp->GetCurrentDesiredOverlayTag();
		movesetTag = EquipmentComp->GetCurrentDesiredMovesetTag();

		if (movesetTag == FGameplayTag()) {
			movesetTag = UACFCCFunctionLibrary::GetMovesetTypeTagRoot();
		}
		if (overlayTag == FGameplayTag()) {
			overlayTag = UACFCCFunctionLibrary::GetAnimationOverlayTagRoot();
		}

		if (!EquipmentComp->GetCurrentMainWeapon()) {
			CombatType = ECombatType::EUnarmed;
		}
		else if (EquipmentComp->GetCurrentMainWeapon()->IsA<AACFMeleeWeaponActor>()) {
			CombatType = ECombatType::EMelee;
		}
		else if (EquipmentComp->GetCurrentMainWeapon()->IsA<AACFRangedWeaponActor>()) {
			CombatType = ECombatType::ERanged;
		}
	}
	else {
		movesetTag = UACFCCFunctionLibrary::GetMovesetTypeTagRoot();
		overlayTag = UACFCCFunctionLibrary::GetAnimationOverlayTagRoot();
		CombatType = ECombatType::EUnarmed;
	}

	if (movesetTag == FGameplayTag()) {
		movesetTag = UACFCCFunctionLibrary::GetMovesetTypeTagRoot();
	}
	if (overlayTag == FGameplayTag()) {
		overlayTag = UACFCCFunctionLibrary::GetAnimationOverlayTagRoot();
	}

	UACFAnimInstance* acfAnimInst = GetACFAnimInstance();
	if (acfAnimInst) {
		if (movesetTag != FGameplayTag() && movesetTag != acfAnimInst->GetCurrentMovesetTag()) {
			acfAnimInst->SetMoveset(movesetTag);
		}
		if (overlayTag != acfAnimInst->GetCurrentOverlay()) {
			acfAnimInst->SetAnimationOverlay(overlayTag);
		}
	}

	if (ActionsComp && HasAuthority()) {
		ActionsComp->SetMovesetActions(actionsTag);
	}

	OnCombatTypeChanged.Broadcast(CombatType);
}

void AACFCharacter::OnActorLoaded_Implementation()
{
	if (!GetController()) {
		SpawnDefaultController();
	}
}

void AACFCharacter::OnActorSaved_Implementation() {}

TArray<UActorComponent*> AACFCharacter::GetComponentsToSave_Implementation() const
{
	TArray<UActorComponent*> Components;
	if (StatisticsComp) {
		Components.Add(StatisticsComp);
	}
	if (DamageHandlerComp) {
		Components.Add(DamageHandlerComp);
	}
	if (EquipmentComp) {
		Components.Add(EquipmentComp);
	}
	return Components;
}

void AACFCharacter::DestroyIfLoadedDead()
{
	if (IsAlive() || !HasAuthority() || IsActorBeingDestroyed() || !IsValid(this)) {
		return;
	}
	if (EquipmentComp) {
		EquipmentComp->OnEntityOwnerDeath();
	}
	Destroy();
}

void AACFCharacter::OnLoaded_Implementation()
{
	// Covers the full world-load path (GFinishLoad -> ExecuteFunctionsOnSavableActor).
	if (!IsAlive()) {
		DestroyIfLoadedDead();
		return;
	}

	OnActorLoaded();
}

FGameplayTag AACFCharacter::GetCombatTeam() const
{
	return IACFEntityInterface::Execute_GetEntityCombatTeam(this);
}

void AACFCharacter::HandleDamageReceived(const FACFDamageEvent& damageReceived)
{
	OnDamageReceived.Broadcast(damageReceived);

	// Client-side prediction: activate hit reaction locally when replicated damage arrives,
	// so motion warp / montage start with LocalPredicted instead of waiting for server replicate RPC.
	if (!HasAuthority() && IsLocallyControlled() && damageReceived.HitResponseAction.IsValid() && IsAlive() && ActionsComp) {
		FACFAbilityPayload newDamage;
		newDamage.HitResult = damageReceived.hitResult;
		newDamage.TargetActor = damageReceived.DamageDealer;
		ActionsComp->TriggerActionWithPayload(damageReceived.HitResponseAction, newDamage, EActionPriority::EHighest, false);
	}
}

void AACFCharacter::HandleDamageInflicted(const FACFDamageEvent& damage)
{
	OnDamageInflicted.Broadcast(damage);
}



void AACFCharacter::SetupCollisionManager()
{
	if (CollisionComp) {
		CollisionComp->OnCollisionDetected.RemoveAll(this);
		CollisionComp->SetupCollisionManager(GetMesh(), UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels());
		CollisionComp->SetActorOwner(this);
		CollisionComp->AddCollisionChannels(GetEnemiesCollisionChannel());
		CollisionComp->AddActorToIgnore(this);
	}
}


void AACFCharacter::SwitchOverlay_Implementation(FGameplayTag overlayTag)
{
	if (GetACFCharacterMovementComponent()) {
		GetACFCharacterMovementComponent()->SetCurrentOverlay(overlayTag);
	}
}

void AACFCharacter::SwitchMoveset_Implementation(FGameplayTag moveType)
{
	if (GetACFCharacterMovementComponent()) {
		GetACFCharacterMovementComponent()->SetCurrentMoveset(moveType);
	}
}

void AACFCharacter::SwitchMovesetActions_Implementation(FGameplayTag moveType)
{
	if (ActionsComp) {
		ActionsComp->SetMovesetActions(moveType);
	}
}



TArray<TEnumAsByte<ECollisionChannel>> AACFCharacter::GetEnemiesCollisionChannel() const
{

	if (const UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {

		return TeamSubsystem->GetHostileCollisionChannels(GetCombatTeam());
	}

	return TArray<TEnumAsByte<ECollisionChannel>>();
}

bool AACFCharacter::CanBeRanged() const
{
	return EquipmentComp->HasOnBodyAnyWeaponOfType(UACFRangedWeapon::StaticClass());
}

// Called to bind functionality to input
void AACFCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	SetupPlayerInputComponentBP(PlayerInputComponent);
}

void AACFCharacter::HandleCharacterDeath()
{

	switch (DeathType) {
	case EDeathType::EDeathAction:
		ForceAction(UACFFunctionLibrary::GetDefaultDeathState());
		break;
	case EDeathType::EGoRagdoll:
		RagdollComp->GoRagdollFromDamage(GetLastDamageInfo());
		break;
	default:
		break;
	}
	if (EquipmentComp) {
		EquipmentComp->OnEntityOwnerDeath();
	}
	if (GetCharacterMovement()) {
		GetCharacterMovement()->DisableMovement();
	}
	if (bAutoDestroyOnDeath && HasAuthority()) {
		SetLifeSpan(DestroyTimeOnDeath);
	}

	if (bDisableCapsuleOnDeath && GetCapsuleComponent()) {
		GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
		GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	}
	OnDeath.Broadcast(this);
}


AActor* AACFCharacter::GetTarget() const
{
	const AController* controller = GetController();
	if (controller) {
		const UATSBaseTargetComponent* targetContr = controller->FindComponentByClass<UATSBaseTargetComponent>();
		if (targetContr) {
			return targetContr->GetCurrentTarget();
		}
	}
	return nullptr;
}

class UATSBaseTargetComponent* AACFCharacter::GetTargetingComponent() const
{
	const AController* controller = GetController();
	if (controller) {
		return controller->FindComponentByClass<UATSBaseTargetComponent>();
	}
	return nullptr;
}

bool AACFCharacter::IsAlive() const
{
	return GetDamageHandlerComponent()->GetIsAlive();
}

FGameplayTag AACFCharacter::GetCurrentMoveset() const
{
	const USkeletalMeshComponent* mesh = GetMesh();
	const UAnimInstance* AnimInstance = mesh ? mesh->GetAnimInstance() : nullptr;
	const UACFAnimInstance* ACFAnimInstance = Cast<UACFAnimInstance>(AnimInstance);

	if (!ACFAnimInstance) {
		UE_LOG(ACFLog, Warning, TEXT("AACFCharacter::GetCurrentMoveset - Invalid AnimInstance for %s"), *GetName());
		return FGameplayTag();
	}

	return ACFAnimInstance->GetCurrentMovesetTag();
}

UACFAnimInstance* AACFCharacter::GetACFAnimInstance() const
{
	return Cast<UACFAnimInstance>(GetMesh()->GetAnimInstance());
}


void AACFCharacter::ForceAction(FGameplayTag Action)
{
	TriggerAction(Action, EActionPriority::EHighest);
}

void AACFCharacter::TriggerAction(FGameplayTag Action, EActionPriority Priority, bool canBeStored /*= false*/)
{
	if (ActionsComp) {
		ActionsComp->TriggerAction(Action, Priority, canBeStored);
		return;
	}
	UE_LOG(ACFLog, Warning, TEXT("Attempting to trigger action (%s) without an action manager component"), *Action.ToString());
}

FGameplayTag AACFCharacter::GetCurrentActionState() const
{
	if (ActionsComp) {
		return ActionsComp->GetCurrentActionTag();
	}

	return FGameplayTag();
}

EDamageZone AACFCharacter::GetDamageZoneByBoneName(FName BoneName) const
{
	const EDamageZone* zone = BoneNameToDamageZoneMap.Find(BoneName);
	if (zone) {
		return *zone;
	}
	return EDamageZone::ENormal;
}

float AACFCharacter::GetWalkSpeed() const
{
	if (LocomotionComp)
		return LocomotionComp->GetCharacterMaxSpeedByState(ELocomotionState::EWalk);

	return 0.f;
}

float AACFCharacter::GetJogSpeed() const
{
	if (LocomotionComp)
		return LocomotionComp->GetCharacterMaxSpeedByState(ELocomotionState::EJog);

	return 0.f;
}

float AACFCharacter::GetSprintSpeed() const
{
	if (LocomotionComp)
		return LocomotionComp->GetCharacterMaxSpeedByState(
			ELocomotionState::ESprint);

	return 0.f;
}

float AACFCharacter::TakeDamage(float Damage, FDamageEvent const& DamageEvent,
	AController* EventInstigator,
	AActor* DamageCauser)
{

	const float damageReceived = DamageHandlerComp->TakeDamage(this, Damage, DamageEvent, EventInstigator, DamageCauser);

	if (GetLastDamageInfo().HitResponseAction != FGameplayTag() && IsAlive() && HasAuthority()) {
		FACFAbilityPayload newDamage;
		newDamage.HitResult = GetLastDamageInfo().hitResult;
		newDamage.TargetActor = DamageCauser;
		ActionsComp->TriggerActionWithPayload(GetLastDamageInfo().HitResponseAction, newDamage, EActionPriority::EHighest, false);
	}

	return damageReceived;
}

void AACFCharacter::Crouch(bool bClientSimulation /*= false*/)
{

	Super::Crouch(bClientSimulation);
	OnCrouchStateChanged.Broadcast(GetCharacterMovement()->IsCrouching());
}

void AACFCharacter::UnCrouch(bool bClientSimulation)
{
	Super::UnCrouch(bClientSimulation);
	OnCrouchStateChanged.Broadcast(GetCharacterMovement()->IsCrouching());
}

void AACFCharacter::OnMovementModeChanged(EMovementMode prevMovementMde,
	uint8 PreviousCustomMode /*= 0*/)
{
	Super::OnMovementModeChanged(prevMovementMde, PreviousCustomMode);

	if (GetMovementComponent()->IsFalling()) {
		ZFalling = GetActorLocation().Z;
	}
}

void AACFCharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);

	if (HasAuthority()) {
		if (ZFalling == -1.f) {
			return;
		}
		const float totalFallinDistance = ZFalling - GetActorLocation().Z;

		ZFalling = -1.f;
		const float fallDamage = GetFallDamageFromDistance(totalFallinDistance);
		if (fallDamage > 1.f && GetEnableFallDamage()) {
			FDamageEvent damageFall;
			damageFall.DamageTypeClass = UFallDamageType::StaticClass();
			TakeDamage(fallDamage, damageFall, GetController(), this);
		}
		if (GetTriggerActionOnLand() && totalFallinDistance > FallHeightToTriggerAction)
		{
			//Ensure movement mode is updated
			FTimerHandle TimerHandle;
			GetWorldTimerManager().SetTimer(TimerHandle, [this]()
				{
					ForceAction(ActionsToTriggerOnLand);
				}, 0.01f, false);
		}
	}
}

void AACFCharacter::OnCharacterDeath_Implementation()
{
}

void AACFCharacter::DestroyCharacter_Implementation(float lifeSpan /*= 0.2*/)
{
	SetLifeSpan(lifeSpan);
	if (EquipmentComp) {
		EquipmentComp->SetDropItemsOnDeath(false);
		EquipmentComp->OnEntityOwnerDeath();
	}
}

USkeletalMeshComponent* AACFCharacter::GetMainMesh_Implementation() const
{
	return GetMesh();
}

float AACFCharacter::GetFallDamageFromDistance(float fallDistance)
{
	const float fallDamageDist = fallDistance - FallDamageDistanceThreshold;
	if (FallDamageByFallDistance && fallDamageDist > 0) {
		return FallDamageByFallDistance->GetFloatValue(fallDamageDist);
	}
	return 0.f;
}

void AACFCharacter::ActivateDamage(const EDamageActivationType& damageActType,
	const TArray<FName>& traceChannels)
{
	if (damageActType == EDamageActivationType::EPhysical && CollisionComp) {
		if (!CollisionComp->IsRegistered()) {
			CollisionComp->RegisterComponent();
		}

		if (!traceChannels.IsValidIndex(0)) {
			CollisionComp->StartAllTraces();
		}

		else {
			for (const auto& channel : traceChannels) {
				CollisionComp->StartSingleTrace(channel);
			}
		}
	}
	else if (EquipmentComp) {
		switch (damageActType) {
		case EDamageActivationType::ERight:
			EquipmentComp->SetDamageActivation(true, traceChannels, false);
			break;
		case EDamageActivationType::ELeft:
			EquipmentComp->SetDamageActivation(true, traceChannels, true);
			break;
		case EDamageActivationType::EBoth:
			EquipmentComp->SetDamageActivation(true, traceChannels, true);
			EquipmentComp->SetDamageActivation(true, traceChannels, false);
			break;
		}
	}
}

void AACFCharacter::DeactivateDamage(const EDamageActivationType& damageActType,
	const TArray<FName>& traceChannels)
{
	if (damageActType == EDamageActivationType::EPhysical && CollisionComp) {
		if (!traceChannels.IsValidIndex(0)) {
			CollisionComp->StopAllTraces();

		}
		else {
			for (const auto& channel : traceChannels)
				CollisionComp->StopSingleTrace(channel);
		}

	}
	else if (EquipmentComp) {
		switch (damageActType) {
		case EDamageActivationType::ERight:
			EquipmentComp->SetDamageActivation(false, traceChannels, false);
			break;
		case EDamageActivationType::ELeft:
			EquipmentComp->SetDamageActivation(false, traceChannels, true);
			break;
		case EDamageActivationType::EBoth:
			EquipmentComp->SetDamageActivation(false, traceChannels, true);
			EquipmentComp->SetDamageActivation(false, traceChannels, false);
			break;
		}
	}
}

bool AACFCharacter::IsMyEnemy(AACFCharacter* target) const
{
	if (!target)
		return false;

	if (UACFFunctionLibrary::GetBattleType(GetWorld()) == EBattleType::EEveryoneAgainstEveryone)
		return true;
	else {
		return UACFFunctionLibrary::AreEnemyTeams(GetWorld(), GetCombatTeam(),
			target->GetCombatTeam());
	}
}

void AACFCharacter::PostInitializeComponents()
{
	Super::PostInitializeComponents();
}

void AACFCharacter::CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult)
{
	if (CameraComponent)
	{
		CameraComponent->GetCameraView(DeltaTime, OutResult);
	}
	else
	{
		Super::CalcCamera(DeltaTime, OutResult);
	}
}

FGameplayTag AACFCharacter::GetEntityCombatTeam_Implementation() const
{
	return TeamComponent ? TeamComponent->GetTeam() : FGameplayTag();
}

void AACFCharacter::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
	if (UWorld* World = GetWorld()) {
		if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
			const FGenericTeamId GenericTeamId = TeamSubsystem->FromTagToTeamId(inCombatTeam);
			SetGenericTeamId(GenericTeamId);
		}
	}
}

FGenericTeamId AACFCharacter::GetGenericTeamId() const
{
	return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

void AACFCharacter::SetGenericTeamId(const FGenericTeamId& TeamID)
{
	if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
		const FGameplayTag TeamTag = TeamSubsystem->FromTeamIdToTag(TeamID);
		if (TeamComponent) {

			TeamComponent->ServerRequestTeamChange(TeamTag);
		}
	}
}

ETeamAttitude::Type AACFCharacter::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
	if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {

		return TeamSubsystem->GetAttitudeBetweenActors(this, &OtherTeam);
	}
	return ETeamAttitude::Neutral;
}

UAbilitySystemComponent* AACFCharacter::GetAbilitySystemComponent() const
{
	return ActionsComp;
}

void AACFCharacter::TryJump()
{
	if (ActionsComp->IsInActionState(UACFActionsFunctionLibrary::GetDefaultActionsState())) {
		Jump();
	}
}

void AACFCharacter::KillCharacter_Implementation()
{

	const FGameplayTag healthTag = UACFFunctionLibrary::GetHealthTag();
	const float damageToApply = StatisticsComp->GetCurrentValueForStatitstic(healthTag);

	StatisticsComp->ModifyStatistic(healthTag, -damageToApply);
}

void AACFCharacter::ReviveCharacter_Implementation(float normalizedHealthToGrant)
{
	const FGameplayTag healthTag = UACFFunctionLibrary::GetHealthTag();
	const float healthToApply = GetStatisticsComponent()->GetMaxValueForStatitstic(healthTag);
	GetDamageHandlerComponent()->Revive();
	GetStatisticsComponent()->ModifyStatistic(healthTag, healthToApply * normalizedHealthToGrant);
	GetActionsComponent()->UnlockActionsTrigger();
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
}

EACFDirection AACFCharacter::GetRelativeTargetDirection(const AActor* targetActor) const
{
	if (!targetActor)
		return EACFDirection::Front;

	const float dotProduct = GetDotProductTo(targetActor);

	if (dotProduct >= 0.5f)
		return EACFDirection::Front;

	else if (dotProduct <= -0.5f)
		return EACFDirection::Back;

	FVector dirVectorToReceiver = UKismetMathLibrary::GetDirectionUnitVector(
		GetActorLocation(), targetActor->GetActorLocation());

	float dotProductFromRight = UKismetMathLibrary::Dot_VectorVector(
		GetActorRightVector(), dirVectorToReceiver);

	if (dotProductFromRight >= 0.f)
		return EACFDirection::Right;
	else
		return EACFDirection::Left;
}

float AACFCharacter::GetCurrentMaxSpeed() const
{
	return GetCharacterMovement()->MaxWalkSpeed;
}

FACFDamageEvent AACFCharacter::GetLastDamageInfo() const
{
	return DamageHandlerComp->GetLastDamageInfo();
}

void AACFCharacter::SetBase(FMovementBaseInterfaceData* MovementBaseInterfaceData, FName BoneName, bool bNotifyActor)
{
	if (MovementBaseInterfaceData && MovementBaseInterfaceData->IsValid()) {
		AActor* BaseOwner = Cast<AActor>(MovementBaseInterfaceData->GetMovementBaseObjectOwner());
		// LoadClass to not depend on the voxel module
		static UClass* VoxelWorldClass = LoadClass<UObject>(nullptr, TEXT("/Script/Voxel.VoxelWorld"));
		if (VoxelWorldClass && BaseOwner && BaseOwner->IsA(VoxelWorldClass)) {
			UPrimitiveComponent* NewBase = Cast<UPrimitiveComponent>(BaseOwner->GetRootComponent());
			ensure(NewBase);
			FMovementBaseInterfaceData VoxelMovementBaseData(NewBase);
			Super::SetBase(&VoxelMovementBaseData, BoneName, bNotifyActor);
			return;
		}
	}

	Super::SetBase(MovementBaseInterfaceData, BoneName, bNotifyActor);
}
