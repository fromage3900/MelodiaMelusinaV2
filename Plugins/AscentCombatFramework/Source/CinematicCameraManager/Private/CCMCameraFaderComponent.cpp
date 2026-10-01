// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "CCMCameraFaderComponent.h"

#include "CCMFadeableActorComponent.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include <GameFramework/Actor.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>
#include <UObject/UObjectGlobals.h>
#include <GameFramework/Pawn.h>

// Sets default values for this component's properties
UCCMCameraFaderComponent::UCCMCameraFaderComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = true;
    FadeableComponentClass = UCCMFadeableActorComponent::StaticClass();
    // ...
}

void UCCMCameraFaderComponent::AddActorToIgnore(AActor* newActor)
{
    if (newActor && !IgnoredActors.Contains(newActor)) {
        IgnoredActors.Add(newActor);
    }
}

void UCCMCameraFaderComponent::RemoveActorToIgnore(AActor* newActor)
{
    if (newActor && IgnoredActors.Contains(newActor)) {
        IgnoredActors.Remove(newActor);
    }
}

// Called when the game starts
void UCCMCameraFaderComponent::BeginPlay()
{
    Super::BeginPlay();

    ActiveController = Cast<APlayerController>(GetOwner());
    auto& eventNewPawn = ActiveController->GetOnNewPawnNotifier();
    eventNewPawn.AddLambda([this](APawn* newPawn) {
        HandlePawnChanges(newPawn);
    });
    HandlePawnChanges(nullptr);
}

// Called every frame
void UCCMCameraFaderComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    CheckOcclusion();
}

void UCCMCameraFaderComponent::HandlePawnChanges(APawn* newPawn)
{
    // Skip auto-detection when the caller has explicitly set a camera override.
    if (bCameraOverridden) {
        return;
    }

    if (IsValid(ActiveController) && IsValid(ActiveController->GetPawn())) {

        ActiveSpringArm = Cast<
            USpringArmComponent>(ActiveController->GetPawn()->GetComponentByClass(USpringArmComponent::StaticClass()));
        ActiveCamera = Cast<UCameraComponent>(ActiveController->GetPawn()->GetComponentByClass(UCameraComponent::StaticClass()));
    }
}

void UCCMCameraFaderComponent::SetActiveCamera(UCameraComponent* Camera)
{
    ActiveCamera = Camera;
    bCameraOverridden = IsValid(Camera);
}

UCameraComponent* UCCMCameraFaderComponent::GetActiveCamera() const
{
    return ActiveCamera;
}

void UCCMCameraFaderComponent::ClearActiveCameraOverride()
{
    bCameraOverridden = false;
    HandlePawnChanges(nullptr);
}

void UCCMCameraFaderComponent::CheckOcclusion()
{
    if (!GetOcclusionEnabled()) {
        return;
    }

    if (ActiveCamera && ActiveController && ActiveController->GetPawn()) {
        const FVector Start = ActiveCamera->GetComponentLocation();
        const FVector End = ActiveController->GetPawn()->GetActorLocation();
        APawn* activePawn = ActiveController->GetPawn();

        TArray<AActor*> ActorsToIgnore;
        TArray<FHitResult> OutHits;
        // The list of actors hit by the line trace, that means that they are occluded from view
        TSet<const AActor*> newActors;

        ActorsToIgnore.Append(IgnoredActors);
        ActorsToIgnore.Add(activePawn);
        const EDrawDebugTrace::Type ShouldDebug = bShowDebug ? EDrawDebugTrace::ForDuration : EDrawDebugTrace::None;

        const bool bGotHits = UKismetSystemLibrary::LineTraceMultiForObjects(GetWorld(), Start, End, CollisionObjectTypes, true,
            ActorsToIgnore, ShouldDebug, OutHits, true, FLinearColor::Blue, FLinearColor::Green, 0.f);
        
        if (activePawn && bFadePlayer && !bPlayerOccluded && FMath::Abs((Start - activePawn->GetActorLocation()).Size()) < MaxPlayerFadeDistance) {
            HideActor(activePawn);
            bPlayerOccluded = true; 
        } else if (bFadePlayer && bPlayerOccluded && FMath::Abs((Start - activePawn->GetActorLocation()).Size()) > MaxPlayerFadeDistance) {
            ShowActor(activePawn);
            bPlayerOccluded = false; 
        }
        if (bGotHits) {

            // Hide actors that are occluded by the camera
            for (const FHitResult& hit : OutHits) {
                AActor* hitActor = Cast<AActor>(hit.GetActor());
                if (FMath::Abs((Start - hit.Location).Size()) < MaxOccludingDistance) {
                    newActors.Add(hitActor);
                    if (hitActor && CanOccludeActor(hitActor) && !OccludedActors.Contains(hitActor)) {
                        HideOccludedActor(hitActor);
                    }
                }
            }

            // Show actors that are currently hidden but that are not occluded by the camera anymore
            for (auto& Elem : GetOccludedActors()) {
                if (!newActors.Contains(Elem) && Elem) {
                    ShowOccludedActor(Elem);
                }
            }
        } else {
            ForceShowOccludedActors();
        }
    }
}

bool UCCMCameraFaderComponent::HideOccludedActor(AActor* Actor)
{
    if (OccludedActors.Contains(Actor)) {
        return true;
    }
    if (HideActor(Actor)) {

        OccludedActors.Add(Actor);
        return true;
    }
    return false;
}

bool UCCMCameraFaderComponent::HideActor(AActor* Actor)
{
    UCCMFadeableActorComponent* fadeComp = Actor->FindComponentByClass<UCCMFadeableActorComponent>();
    if (!fadeComp && bForceFaderComponent) {
        UCCMFadeableActorComponent* newComp = NewObject<UCCMFadeableActorComponent>(Actor, FadeableComponentClass);
        if (newComp == nullptr) {
            UE_LOG(LogTemp, Error, TEXT("Failed to add CCMFadeableComponent to actor "));
            return false;
        }
        newComp->RegisterComponent();
    }

    if (!fadeComp) {
        return false;
    }

    fadeComp->SetMaterialOverride(FadeMaterial);
    return true;
}

void UCCMCameraFaderComponent::ShowOccludedActor(AActor* Actor)
{
    if (OccludedActors.Contains(Actor)) {
        ShowActor(Actor);
        OccludedActors.Remove(Actor);
        return;
    }
    UE_LOG(LogTemp, Error, TEXT("Failed to restore actor materials - UCCMCameraFaderComponent::ShowOccludedActor"));
}

void UCCMCameraFaderComponent::ShowActor(AActor* Actor)
{
    UCCMFadeableActorComponent* fadeComp = Actor->FindComponentByClass<UCCMFadeableActorComponent>();
    if (fadeComp) {
        fadeComp->RestoreMaterials();
        return;
    }
}

void UCCMCameraFaderComponent::ForceShowOccludedActors()
{
    if (!OccludedActors.IsEmpty()) {
        for (auto& actor : OccludedActors) {
            UCCMFadeableActorComponent* fadeComp = actor->FindComponentByClass<UCCMFadeableActorComponent>();
            if (fadeComp) {
                fadeComp->RestoreMaterials();
            }
        }
        OccludedActors.Empty();
    }
}

bool UCCMCameraFaderComponent::CanOccludeActor(const AActor* Actor) const
{
    const UCCMFadeableActorComponent* fadeComp = Actor->FindComponentByClass<UCCMFadeableActorComponent>();
    return fadeComp || bForceFaderComponent;
}
