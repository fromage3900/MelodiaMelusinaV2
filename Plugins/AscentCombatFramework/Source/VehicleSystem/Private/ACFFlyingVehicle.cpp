// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFFlyingVehicle.h"

#include "ACFFlyComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/CollisionProfile.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"

AACFFlyingVehicle::AACFFlyingVehicle()
{
    PrimaryActorTick.bCanEverTick = true;

    bUseControllerRotationYaw = false;
    bUseControllerRotationPitch = false;
    bUseControllerRotationRoll = false;

    // -----------------------------------------------------------------------
    // Root: skeletal mesh. It is BOTH the visual and the movement collision
    // shape: the FlyComponent uses it as its UpdatedComponent so all
    // SafeMoveUpdatedComponent sweeps test the Physics Asset bodies of the
    // ship instead of a loose capsule. This eliminates the wing/hull
    // compenetration with terrain and other actors that the previous capsule
    // root caused on large meshes.
    // Collision profile and Physics Asset are intentionally left as defaults
    // here so child Blueprints can tailor them to each ship.
    // -----------------------------------------------------------------------
    Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("CharacterMesh0"));
    Mesh->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->SetGenerateOverlapEvents(true);
    Mesh->BodyInstance.bSimulatePhysics = false;
    Mesh->SetShouldUpdatePhysicsVolume(true);
    Mesh->SetCanEverAffectNavigation(false);
    Mesh->bReceivesDecals = true;
    
    RootComponent = Mesh;

    FlyComponent = CreateDefaultSubobject<UACFFlyComponent>(TEXT("FlyComponent"));
}

void AACFFlyingVehicle::BeginPlay()
{
    Super::BeginPlay();

    // Anchor the movement component to the skeletal mesh so SafeMoveUpdatedComponent
    // always sweeps the ship's Physics Asset bodies, regardless of any Blueprint root
    // override. This is what makes the ship actually stop at its hull instead of
    // clipping into terrain/enemies as the old capsule root did.
    if (FlyComponent && Mesh) {
        FlyComponent->SetUpdatedComponent(Mesh);
    } else {
        UE_LOG(LogTemp, Error, TEXT("ACFFlyingVehicle [%s]: FlyComponent or Mesh is null in BeginPlay."), *GetName());
    }

    if (USpringArmComponent* SpringArm = FindComponentByClass<USpringArmComponent>()) {
        SpringArm->SetUsingAbsoluteRotation(false);
        SpringArm->bUsePawnControlRotation = false;
        SpringArm->bInheritPitch = true;
        SpringArm->bInheritYaw = true;
        SpringArm->bInheritRoll = true;
    }

    if (UCameraComponent* Camera = FindComponentByClass<UCameraComponent>()) {
        Camera->SetUsingAbsoluteRotation(false);
        Camera->bUsePawnControlRotation = false;
    }

    if (UACFAbilitySystemComponent* ASC = FindComponentByClass<UACFAbilitySystemComponent>())
    {
        ASC->InitAbilityActorInfo(this, this);
    }
}

void AACFFlyingVehicle::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RemoveSpaceshipMappingContext();
    Super::EndPlay(EndPlayReason);
}

void AACFFlyingVehicle::PawnClientRestart()
{
    Super::PawnClientRestart();

     // Owning client after ClientRestart/DispatchRestart; default PawnClientRestart may create the
    // PlayerInput component first — then register the spaceship mapping on the local player.
    AddSpaceshipMappingContext();
}

void AACFFlyingVehicle::UnPossessed()
{
    // APawn::UnPossessed nulls Controller before returning; remove mapping while GetController()
    // is still the possessing PC.
    RemoveSpaceshipMappingContext();
    Super::UnPossessed();
}

void AACFFlyingVehicle::AddSpaceshipMappingContext()
{
    if (!InputMappingContext) {
        return;
    }

    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !PC->IsLocalController()) {
        return;
    }
    if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
            ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
    {
        Subsystem->AddMappingContext(InputMappingContext, InputMappingPriority);
    }
}

void AACFFlyingVehicle::RemoveSpaceshipMappingContext()
{
    if (!InputMappingContext) {
        return;
    }

    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !PC->IsLocalController()) {
        return;
    }

    if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
            ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(InputMappingContext);
    }
}
