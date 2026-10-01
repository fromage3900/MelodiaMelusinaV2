// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "CCMPlayerCameraManager.h"
#include "CCMCameraFunctionLibrary.h"
#include "CCMCameraSplineComponent.h"
#include "Engine/Engine.h"
#include "Components/SceneComponent.h" 
#include <Camera/CameraActor.h>
#include <Camera/CameraComponent.h>
#include <CineCameraComponent.h>
#include <Engine/World.h>
#include <GameFramework/Actor.h>
#include <GameFramework/Character.h>
#include <GameFramework/CharacterMovementComponent.h>
#include <GameFramework/SpringArmComponent.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>
#include <TimerManager.h>
#include <Net/UnrealNetwork.h>

#include "ACFCameraPointComponent.h"
#include "LevelSequence.h"
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "DefaultLevelSequenceInstanceData.h"

class UACFBattleManagerComponent;

ACCMPlayerCameraManager::ACCMPlayerCameraManager()
{
	PrimaryActorTick.bStartWithTickEnabled = true;
	CameraActorClass = ACameraActor::StaticClass();
}



void ACCMPlayerCameraManager::BeginPlay()
{
	Super::BeginPlay();
	if (GetLocalRole() == ROLE_Authority) {
		BindEvents();
	}

	if (!UKismetSystemLibrary::IsDedicatedServer(this)) {

		UpdateCameraReferences();
		FinalMov.FovInterpSpeed = 0.f;
		FinalMov.InterpSpeed = 0.f;
	}
}


void ACCMPlayerCameraManager::BlendToPoint(AActor* OwnerWithPoints, FGameplayTag CameraTag, float BlendTime,
	TEnumAsByte<EViewTargetBlendFunction> BlendFunc, float BlendExp, bool bLockOutgoing)
{
	APlayerController* PlayerController = GetOwningPlayerController();
	if (!PlayerController || !IsValid(OwnerWithPoints))
	{
		UE_LOG(LogTemp, Warning, TEXT("[CCM] Invalid PC or TargetActor"));
		ensureAlwaysMsgf(false, TEXT("[CCM] Invalid PC or TargetActor"));
		return;
	}

	AActor* ViewTargetActor = nullptr;
	UACFCameraPointComponent* CameraComp = ResolveCameraPoint(OwnerWithPoints, CameraTag, ViewTargetActor);

	if (!CameraComp || !ViewTargetActor)
	{
		UE_LOG(LogTemp, Warning, TEXT("[CCM] Camera Component not found for tag: %s"), *CameraTag.ToString());
		return;
	}

	if (CameraComp == currentCameraComp.Get())
	{
		return;
	}

	if (currentCameraComp)
	{
		currentCameraComp->OnCameraDeactivated();
	}

	currentCameraComp = CameraComp;

	// Deactivate other cameras on the view target actor
	TArray<UCameraComponent*> AllCams;
	ViewTargetActor->GetComponents<UCameraComponent>(AllCams);
	for (UCameraComponent* Cam : AllCams)
	{
		if (Cam != CameraComp)
		{
			Cam->Deactivate();
		}
	}

	CameraComp->Activate(true);
	CameraComp->OnCameraActivated();

	PlayerController->SetViewTargetWithBlend(ViewTargetActor, BlendTime, BlendFunc, BlendExp, bLockOutgoing);
}


UACFCameraPointComponent* ACCMPlayerCameraManager::ResolveCameraPoint(AActor* OwnerWithPoints, const FGameplayTag& CameraTag, AActor*& OutViewTarget) const
{
	OutViewTarget = nullptr;

	// Check direct components on the owner
	TArray<UACFCameraPointComponent*> CameraPoints;
	OwnerWithPoints->GetComponents<UACFCameraPointComponent>(CameraPoints);

	for (UACFCameraPointComponent* CameraPoint : CameraPoints)
	{
		if (IsValid(CameraPoint) && CameraPoint->GetCameraTag() == CameraTag)
		{
			OutViewTarget = OwnerWithPoints;
			return CameraPoint;
		}
	}

	// Check child actors
	TArray<UChildActorComponent*> ChildActorComps;
	OwnerWithPoints->GetComponents<UChildActorComponent>(ChildActorComps);

	for (UChildActorComponent* ChildComp : ChildActorComps)
	{
		AActor* ChildActor = ChildComp->GetChildActor();
		if (!ChildActor)
		{
			continue;
		}

		UACFCameraPointComponent* CameraPoint = ChildActor->FindComponentByClass<UACFCameraPointComponent>();
		if (CameraPoint && CameraPoint->GetCameraTag() == CameraTag)
		{
			OutViewTarget = ChildActor;
			return CameraPoint;
		}
	}

	return nullptr;
}

void ACCMPlayerCameraManager::BindEvents()
{
	APlayerController* controller = GetOwningPlayerController();
	if (controller) {
		auto& eventNewPawn = controller->GetOnNewPawnNotifier();
		eventNewPawn.AddLambda([this](APawn* newPawn) {
			HandlePawnChanged(newPawn);
			});
	}
}

void ACCMPlayerCameraManager::UpdateCamera(float deltaTime)
{
	Super::UpdateCamera(deltaTime);
	if (!UKismetSystemLibrary::IsDedicatedServer(this)) {
		if (GetOwningPlayerController() && playerCharacter != GetOwningPlayerController()->GetPawn()) {
			UpdateCameraReferences();
		}
		if (playerCamera && cameraBoom) {
			MoveCamera(deltaTime);
			UpdateLockOnTarget(deltaTime);

			if (bIsPlayingSequence) {
				UpdateCameraSequence(deltaTime);
			}
		}

		FollowPlayer(deltaTime);
	}
}

void ACCMPlayerCameraManager::UpdateLockOnTarget(float deltaTime)
{
	if (targetLockType != ETargetLockType::ENone && playerCharacter && playerCamera) {
		FVector localPos = FVector();
		if (targetLockType == ETargetLockType::EActor && localtarget) {
			localPos = localtarget->GetActorLocation();
		}
		else if (localtargetComponent) {
			localPos = localtargetComponent->GetComponentLocation();
		}

		LockCameraOnPosition(localPos, deltaTime);
	}
}

void ACCMPlayerCameraManager::UpdateCameraSequence(float deltaTime)
{
	if (currentSequence.cameraSequenceComp && currentSequence.currentTime < currentSequence.cameraSequenceComp->GetSplineLength() && currentSequenceSettings.lookAtActor) {

		UCameraComponent* cameraComp = sequenceCameraActor->GetCameraComponent();
		if (!cameraComp) {
			return;
		}
		const float interpFov = FMath::FInterpTo(cameraComp->FieldOfView, currentSequenceSettings.CameraFov, deltaTime, currentSequenceSettings.FovInterpSpeed);
		cameraComp->SetFieldOfView(interpFov);
		float currentSpeed = currentSequenceSettings.CameraSpeed;
		float const SplineLen = currentSequence.cameraSequenceComp->GetSplineLength();
		currentSequence.currentTime += currentSpeed * deltaTime * SplineLen;
		FVector const MountPos = currentSequence.cameraSequenceComp->GetLocationAtDistanceAlongSpline(currentSequence.currentTime, ESplineCoordinateSpace::World);
		sequenceCameraActor->SetActorLocation(MountPos);
		FRotator lookAtRot = UKismetMathLibrary::FindLookAtRotation(MountPos, currentSequenceSettings.lookAtActor->GetActorLocation());
		FRotator smoothedLookAt = FMath::RInterpTo(sequenceCameraActor->GetActorRotation(), lookAtRot, deltaTime, currentSequenceSettings.CameraRotationsSpeed);
		sequenceCameraActor->SetActorRotation(smoothedLookAt);
	}
	else {
		StopCurrentCameraSequence();
	}
}

void ACCMPlayerCameraManager::TriggerCameraSequence(AActor* cameraOwner, FName CameraEventName)
{
	if (cameraOwner && !bIsPlayingSequence) {

		TArray<UCCMCameraSplineComponent*> CameraSequences;
		cameraOwner->GetComponents<UCCMCameraSplineComponent>(CameraSequences, true);

		for (UCCMCameraSplineComponent* cameraSeq : CameraSequences) {
			if (cameraSeq->GetCameraSequenceName() == CameraEventName) {
				// StopLookingActor();
				currentSequence.Reset(cameraSeq);
				bIsPlayingSequence = true;
				break;
			}
		}

		if (currentSequence.cameraSequenceComp) {
			SetCameraSequenceData();

			if (UKismetSystemLibrary::IsServer(this)) {
				UGameplayStatics::SetGlobalTimeDilation(this, currentSequence.cameraSequenceComp->GetCameraSequenceSettings().TimeDilatation);
			}

			APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
			if (controller) {
				controller->SetViewTargetWithBlend(sequenceCameraActor, currentSequence.cameraSequenceComp->GetCameraSequenceSettings().BlendSettingsTime);
			}
		}
	}
}

ALevelSequenceActor* ACCMPlayerCameraManager::PlayGameplaySequenceWithBinding(
	ULevelSequence* Sequence,
	const FTransform& TransformOrigin,
	const TArray<FCCMSequenceBinding>& Bindings)
{
	// Only one sequence at a time: stop any current one
	StopSequence();

	FMovieSceneSequencePlaybackSettings PlaybackSettings;
	PlaybackSettings.bAutoPlay = false;

	ALevelSequenceActor* SequenceActor = nullptr;
	ULevelSequencePlayer* SequencePlayer = ULevelSequencePlayer::CreateLevelSequencePlayer(
		this,
		Sequence,
		PlaybackSettings,
		SequenceActor);

	if (!SequenceActor || !SequencePlayer)
	{
		UE_LOG(LogTemp, Warning, TEXT("PlayGameplaySequenceWithBinding: Failed to create LevelSequencePlayer for Sequence: %s"),
			*GetNameSafe(Sequence));
		return nullptr;
	}

	SequenceActor->bOverrideInstanceData = true;

	if (UDefaultLevelSequenceInstanceData* InstanceData = Cast<UDefaultLevelSequenceInstanceData>(SequenceActor->DefaultInstanceData))
	{
		InstanceData->TransformOrigin = TransformOrigin;
	}

	for (const FCCMSequenceBinding& Binding : Bindings)
	{
		if (Binding.TagName.IsNone() || !Binding.BoundActor || !IsValid(Binding.BoundActor))
		{
			continue;
		}

		TArray<AActor*> ActorsToBind;
		ActorsToBind.Add(Binding.BoundActor);
		SequenceActor->SetBindingByTag(Binding.TagName, ActorsToBind, false);
	}

	// Store reference so it can be stopped via StopSequence(); clear when finished
	CurrentLevelSequenceActor = SequenceActor;
	SequencePlayer->OnFinished.AddDynamic(this, &ACCMPlayerCameraManager::OnLevelSequenceFinished);

	SequencePlayer->Play();

	return SequenceActor;
}

void ACCMPlayerCameraManager::StopSequence()
{
	if (!CurrentLevelSequenceActor)
	{
		return;
	}

	if (ULevelSequencePlayer* Player = CurrentLevelSequenceActor->GetSequencePlayer())
	{
		Player->OnFinished.RemoveDynamic(this, &ACCMPlayerCameraManager::OnLevelSequenceFinished);
		Player->Stop();
	}

	CurrentLevelSequenceActor = nullptr;
}

void ACCMPlayerCameraManager::OnLevelSequenceFinished()
{
	if (CurrentLevelSequenceActor)
	{
		if (ULevelSequencePlayer* Player = CurrentLevelSequenceActor->GetSequencePlayer())
		{
			Player->OnFinished.RemoveDynamic(this, &ACCMPlayerCameraManager::OnLevelSequenceFinished);
		}
		CurrentLevelSequenceActor = nullptr;
	}
}

void ACCMPlayerCameraManager::DeactivateCurrentCameraPoint()
{
	if (currentCameraComp)
	{
		currentCameraComp->StopMovement();
		currentCameraComp->OnCameraDeactivated();
		currentCameraComp = nullptr;
	}
}

void ACCMPlayerCameraManager::StopCurrentCameraSequence()
{
	bIsPlayingSequence = false;
	if (UKismetSystemLibrary::IsServer(this)) {
		UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
	}

	APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
	if (controller && sequenceCameraActor) {
		controller->SetViewTargetWithBlend(playerCharacter, currentSequence.cameraSequenceComp->GetCameraSequenceSettings().OutBlendSettings);
	}
}

void ACCMPlayerCameraManager::AddSequenceEventModifier(const FCCMSequenceEvent& modifier)
{
	if (!bIsPlayingSequence) {
		return;
	}
	if (modifier.bChangeTimeDilation && GetOwningPlayerController()->HasAuthority()) {
		UGameplayStatics::SetGlobalTimeDilation(this, modifier.TimeDilatation);
	}
	if (modifier.bEditCameraSpeed) {
		currentSequenceSettings.CameraSpeed = modifier.CameraSpeed;
	}
	if (modifier.bEditFov) {
		currentSequenceSettings.CameraFov = currentSequenceSettings.CameraFov += modifier.CameraFovOffset;
		currentSequenceSettings.FovInterpSpeed = modifier.FovOffsetInterpSpeed;
	}
	if (modifier.bSwitchLookAt) {
		currentSequenceSettings.lookAtActor = currentSequence.cameraSequenceComp->GetLookAtPointLocationByName(modifier.LookAtPoint);
	}
}

void ACCMPlayerCameraManager::RemoveSequenceEventModifier(const FCCMSequenceEvent& modifier)
{
	if (!bIsPlayingSequence) {
		return;
	}
	if (!currentSequence.cameraSequenceComp) {
		return;
	}

	if (modifier.bChangeTimeDilation) {
		UGameplayStatics::SetGlobalTimeDilation(this, currentSequence.cameraSequenceComp->GetCameraSequenceSettings().TimeDilatation);
	}
	if (modifier.bEditCameraSpeed) {
		currentSequenceSettings.CameraSpeed = currentSequence.cameraSequenceComp->GetCameraSequenceSettings().CameraSpeed;
	}
	if (modifier.bEditFov) {
		currentSequenceSettings.CameraFov = currentSequence.cameraSequenceComp->GetCameraSequenceSettings().CameraFov;
	}
	if (modifier.bSwitchLookAt) {
		currentSequenceSettings.lookAtActor = currentSequence.cameraSequenceComp->GetLookAtPointLocationByName(currentSequence.cameraSequenceComp->GetCameraSequenceSettings().LookAtPoint);
	}
}

void ACCMPlayerCameraManager::OverrideCameraReferences(class UCameraComponent* inPlayerCamera, class USpringArmComponent* inCameraBoom)
{
	playerCamera = inPlayerCamera;
	cameraBoom = inCameraBoom;
}

void ACCMPlayerCameraManager::SetCameraSequenceData()
{
	if (!sequenceCameraActor) {
		sequenceCameraActor = GetWorld()->SpawnActor<ACameraActor>(CameraActorClass);
	}

	currentSequenceSettings = currentSequence.cameraSequenceComp->GetCameraSequenceSettings();
	currentSequenceSettings.lookAtActor = currentSequence.cameraSequenceComp->GetLookAtPointLocationByName(currentSequenceSettings.LookAtPoint);
	sequenceCameraActor->GetCameraComponent()->SetFieldOfView(currentSequenceSettings.CameraFov);
	FVector startingLoc = currentSequence.cameraSequenceComp->GetLocationAtTime(0.f, ESplineCoordinateSpace::World);
	FRotator rot = UKismetMathLibrary::FindLookAtRotation(startingLoc, currentSequenceSettings.lookAtActor->GetActorLocation());
	sequenceCameraActor->SetActorLocationAndRotation(startingLoc, rot);
}

void ACCMPlayerCameraManager::LockCameraOnPosition(FVector localPos, float deltaTime)
{
	if (!playerCharacter || !playerCamera) {
		return;
	}

	if (!playerCharacter->GetController()) {
		return;
	}

	const FRotator OldRotation = playerCharacter->GetController()->GetControlRotation();
	FRotator TargetRotation = UKismetMathLibrary::FindLookAtRotation(playerCamera->GetComponentLocation(), localPos);
	FRotator NewRotation = OldRotation;
	TargetRotation.Roll = OldRotation.Roll;
	TargetRotation.Pitch += GlobalLockOffset.Y;
	TargetRotation.Yaw += GlobalLockOffset.X;
	TargetRotation.Pitch = FMath::Clamp(TargetRotation.Pitch, -CameraLockPitchLowerLimit, CameraLockPitchUpperLimit);

	if (currentLockType == ELockType::EYawOnly) {
		TargetRotation.Pitch = OldRotation.Pitch;
	}
	NewRotation = FMath::RInterpTo(OldRotation, TargetRotation, deltaTime, _lockStrength);
	playerCharacter->GetController()->SetControlRotation(NewRotation);
}

void ACCMPlayerCameraManager::TriggerCameraEvent(FName CameraEventName)
{
	if (CameraEventName == NAME_None) {
		return;
	}

	if (UKismetSystemLibrary::IsDedicatedServer(this)) {
		return;
	}

	if (CameraMovements) {
		FCCMCameraMovementSettings* mov = CameraMovements->FindRow<FCCMCameraMovementSettings>(CameraEventName, "Searching for camera event");

		if (currentlyActiveCameraEvents.Find(CameraEventName)) {
			UE_LOG(LogTemp, Warning, TEXT("Camera Event Already Triggered - Cinematic Camera Manager"));
			return;
		}

		if (mov) {
			FinalMov += *(mov);
			currentlyActiveCameraEvents.Add(CameraEventName, *mov);
		}
	}
}

void ACCMPlayerCameraManager::StopCameraEvent(FName CameraEventName)
{
	if (CameraEventName == NAME_None) {
		return;
	}

	if (currentlyActiveCameraEvents.Contains(CameraEventName)) {
		FCCMCameraMovementSettings* mov = currentlyActiveCameraEvents.Find(CameraEventName);
		if (mov) {
			FinalMov -= *(mov);
			currentlyActiveCameraEvents.FindAndRemoveChecked(CameraEventName);
		}
	}
}

void ACCMPlayerCameraManager::TriggerTimedCameraEvent(FName CameraEventName, float duration)
{
	if (!UKismetSystemLibrary::IsDedicatedServer(this)) {
		if (currentlyActiveCameraEvents.Find(CameraEventName)) {
			UE_LOG(LogTemp, Warning, TEXT("Camera Event Already Triggered - Cinematic Camera Manager"));
			return;
		}

		UWorld* world = GetWorld();
		if (world) {
			FTimerDelegate TimerDel;
			FTimerHandle TimerHandle;
			TimerDel.BindUFunction(this, FName("StopCameraEvent"), CameraEventName);
			world->GetTimerManager().SetTimer(TimerHandle, TimerDel, duration, false);
			TriggerCameraEvent(CameraEventName);
		}
	}
}

void ACCMPlayerCameraManager::ResetCameraPosition(bool bInstantReset /*= false*/)
{
	// StopCurrentCameraRotationEvent();

	if (!UKismetSystemLibrary::IsDedicatedServer(this)) {
		TArray<FName> iterator;
		currentlyActiveCameraEvents.GetKeys(iterator);

		TArray<FName> iteratorCopy = iterator;
		for (FName cameraevent : iteratorCopy) {
			StopCameraEvent(cameraevent);
		}

		if (bInstantReset && playerCamera && cameraBoom) {
			playerCamera->FieldOfView = originalFov;
			cameraBoom->SocketOffset = originalPos;
		}
	}
}

void ACCMPlayerCameraManager::LockCameraOnActor(AActor* ActorLookAt, ELockType lockType, float lockStrength)
{
	if (ActorLookAt) {
		localtarget = ActorLookAt;
		currentLockType = lockType;
		targetLockType = ETargetLockType::EActor;
		_lockStrength = lockStrength;
	}
}

void ACCMPlayerCameraManager::LockCameraOnComponent(class USceneComponent* ComponentToLookAt, ELockType lockType, float lockStrength /*= 5.f*/)
{
	if (ComponentToLookAt) {
		localtargetComponent = ComponentToLookAt;
		currentLockType = lockType;
		targetLockType = ETargetLockType::EComponent;
		_lockStrength = lockStrength;
	}
}

void ACCMPlayerCameraManager::StopLookingActor()
{
	targetLockType = ETargetLockType::ENone;
}

void ACCMPlayerCameraManager::PlayCameraBlend(AActor* TargetActor, const FGameplayTag& ComponentTag, float BlendTime, TEnumAsByte<EViewTargetBlendFunction> BlendFunc, float BlendExp, bool bLockOutgoing)
{
	BlendToPoint(TargetActor, ComponentTag, BlendTime, BlendFunc, BlendExp, bLockOutgoing);

}



void ACCMPlayerCameraManager::UpdateCameraReferences()
{
	if (PCOwner && CameraMovements) {
		ResetCameraPosition(true);
		playerCharacter = PCOwner->GetPawn();
		if (playerCharacter) {
			playerCamera = playerCharacter->FindComponentByClass<UCameraComponent>();
			cameraBoom = playerCharacter->FindComponentByClass<USpringArmComponent>();
			if (playerCamera && cameraBoom) {
				originalFov = playerCamera->FieldOfView;
				originalPos = cameraBoom->SocketOffset;

				return;
			}
		}
	}

	UE_LOG(LogTemp, Warning, TEXT("Invalid Camera References !! - Cinematic Camera Manager"));
}

void ACCMPlayerCameraManager::MoveCamera(float deltaTime)
{
	if (cameraBoom) {
		const FVector targetpos = FinalMov.CameraOffset + originalPos;
		cameraBoom->SocketOffset = FMath::VInterpTo(cameraBoom->SocketOffset, targetpos, deltaTime, FinalMov.InterpSpeed);
	}

	if (playerCamera) {
		const float finalfov = FinalMov.FOV + originalFov;
		playerCamera->FieldOfView = FMath::FInterpTo(playerCamera->FieldOfView, finalfov, deltaTime, FinalMov.FovInterpSpeed);
	}

	if (FinalMov.bShakeLooping && PCOwner) {
		PCOwner->ClientStartCameraShake(FinalMov.Shake, FinalMov.ShakeIntensity);
	}
}

void ACCMPlayerCameraManager::StoreData()
{
	if (playerCharacter) {
		_localStrafing = playerCharacter->bUseControllerRotationYaw;
		_localIsLockingAt = targetLockType;
		_localArmLength = cameraBoom->TargetArmLength;
		_localTimeDilatation = 1.f;
		UCharacterMovementComponent* _charmov = playerCharacter->FindComponentByClass<UCharacterMovementComponent>();
		if (_charmov) {
			_localOrientToMov = _charmov->bOrientRotationToMovement;
		}
	}
}

void ACCMPlayerCameraManager::RecoverStoredData()
{
	if (playerCharacter) {
		playerCharacter->bUseControllerRotationYaw = _localStrafing;
		cameraBoom->TargetArmLength = _localArmLength;
		UGameplayStatics::SetGlobalTimeDilation(this, _localTimeDilatation);

		UCharacterMovementComponent* _charmov = playerCharacter->FindComponentByClass<UCharacterMovementComponent>();
		if (_charmov) {
			_charmov->bOrientRotationToMovement = _localOrientToMov;
		}
	}
}

void ACCMPlayerCameraManager::HandlePawnChanged(APawn* newPawn)
{
	UpdateCameraReferences();
}

void ACCMPlayerCameraManager::SetFollowPlayer(bool bFollow, float inFollowSpeed /*= 1.f*/)
{
	bFollowPlayer = bFollow;
	FollowSpeed = inFollowSpeed;
}

void ACCMPlayerCameraManager::FollowPlayer(float deltaTime)
{
	if (bFollowPlayer && playerCharacter && playerCharacter->GetController() && targetLockType == ETargetLockType::ENone) {
		const FRotator OldRotation = playerCharacter->GetController()->GetControlRotation();
		const FRotator TargetRotation = playerCharacter->GetActorForwardVector().Rotation();
		const FRotator NewRotation = FMath::RInterpTo(OldRotation, TargetRotation, deltaTime, FollowSpeed);

		const float deltaAngle = NewRotation.Yaw - OldRotation.Yaw;
		if (bPrintDebugDeltaAngle) {
			GEngine->AddOnScreenDebugMessage(1, 0.2f, FColor::Yellow, FString::Printf(TEXT("Rot Dif: %f"), deltaAngle));
		}
		if (deltaAngle < MaxFollowDeltaAngle) {
			playerCharacter->GetController()->SetControlRotation(FRotator(OldRotation.Pitch, NewRotation.Yaw, OldRotation.Roll));
		}
	}
}

/*
void ACCMPlayerCameraManager::PlayCinematicCameraAnim(UCameraAnimationSequence* CameraAnimAsset, USceneComponent* ReferencePoint)
{
	if (!CameraAnimAsset || !ReferencePoint) {
		UE_LOG(LogTemp, Warning, TEXT("Invalid camera animation or reference point"));
		return;
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC || !PC->PlayerCameraManager) {
		return;
	}

	// 1. Spawn or reuse a temporary fixed camera actor
	static ACameraActor* CachedFixedCamera = nullptr;
	if (!CachedFixedCamera || !CachedFixedCamera->IsValidLowLevel()) {
		UWorld* World = ReferencePoint->GetWorld();
		CachedFixedCamera = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass());
		CachedFixedCamera->SetActorTickEnabled(false);
	}

	// 2. Align the fixed camera with the reference point
	CachedFixedCamera->SetActorLocation(ReferencePoint->GetComponentLocation());
	CachedFixedCamera->SetActorRotation(ReferencePoint->GetComponentRotation());

	// 3. Blend to the fixed camera
	PC->SetViewTargetWithBlend(CachedFixedCamera, 0.5f);

	// 4. Retrieve or add the camera modifier used for camera animations
	UCameraAnimationCameraModifier* CamMod = Cast<UCameraAnimationCameraModifier>(
		PC->PlayerCameraManager->FindCameraModifierByClass(UCameraAnimationCameraModifier::StaticClass()));

	if (!CamMod) {
		CamMod = Cast<UCameraAnimationCameraModifier>(
			PC->PlayerCameraManager->AddNewCameraModifier(UCameraAnimationCameraModifier::StaticClass()));
	}

	// 5. Set up camera animation parameters
	FCameraAnimationParams AnimParams;
	AnimParams.PlaySpace = ECameraAnimationPlaySpace::CameraLocal;
	AnimParams.bLoop = false;
	AnimParams.bRandomStartTime = false;
	AnimParams.Scale = 1.0f;
	AnimParams.DurationOverride = -1.f; // use the asset's duration

	// 6. Play the camera animation
	if (CamMod)
	{
		CamMod->PlayCameraAnimation(CameraAnimAsset, AnimParams);
	}

	// 7. (Optional) Return to player view after the animation ends
	const float DelayBeforeReturn = CameraAnimAsset->GetPlayLength();
	FTimerHandle ReturnHandle;
	FTimerDelegate ReturnDelegate = FTimerDelegate::CreateLambda([PC]() {
		PC->SetViewTargetWithBlend(PC->GetPawn(), 0.5f);
	});

	PC->GetWorld()->GetTimerManager().SetTimer(ReturnHandle, ReturnDelegate, DelayBeforeReturn, false);
}
*/