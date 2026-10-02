// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFThreatManagerComponent.h"
#include "Actors/ACFActor.h"
#include "Actors/ACFCharacter.h"
#include "Interfaces/ACFEntityInterface.h"
#include <GameFramework/Actor.h>
#include <Logging.h>

// Sets default values for this component's properties
UACFThreatManagerComponent::UACFThreatManagerComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

// Called when the game starts
void UACFThreatManagerComponent::BeginPlay()
{
    Super::BeginPlay();

    DefaultThreatMap.Add(AACFActor::StaticClass(), 5.f);
    DefaultThreatMap.Add(AACFCharacter::StaticClass(), 10.f);
}

void UACFThreatManagerComponent::UpdateMaxThreat()
{
    AActor* newMax = GetActorWithHigherThreat();
    if (newMax != maxThreatening) {
        maxThreatening = newMax;
        OnNewMaxThreateningActor.Broadcast(maxThreatening);
    }
}

void UACFThreatManagerComponent::AddThreat(AActor* threatening, float ThreatToAdd)
{
    if (!threatening || threatening == GetOwner() || ThreatToAdd <= 0.f) {
        return;
    }

    if (!Cast<IACFEntityInterface>(threatening)) {
        return;
    }

    if (!IACFEntityInterface::Execute_IsEntityAlive(threatening)) {
        RemoveThreatening(threatening);
        return;
    }

    const float CurrentThreat = ThreatMap.Contains(threatening) ? ThreatMap[threatening] : 0.f;
    const float ThreatMult = GetThreatMultForActor(threatening);

    const float NewThreat = CurrentThreat + (ThreatToAdd * ThreatMult);
    ThreatMap.Add(threatening, NewThreat);

    UpdateMaxThreat();
}

void UACFThreatManagerComponent::RemoveThreat(AActor* threatening, float ThreatToRemove)
{
    if (!threatening || ThreatToRemove <= 0.f) {
        return;
    }

    if (!Cast<IACFEntityInterface>(threatening)) {
        return;
    }

    if (!IACFEntityInterface::Execute_IsEntityAlive(threatening)) {
        RemoveThreatening(threatening);
        return;
    }

    if (!ThreatMap.Contains(threatening)) {
        return;
    }

    const float CurrentThreat = ThreatMap[threatening];
    const float NewThreat = CurrentThreat - ThreatToRemove;

    if (NewThreat > 0.f) {
        ThreatMap.Add(threatening, NewThreat);
    } else {
        ThreatMap.Remove(threatening);
    }

    UpdateMaxThreat();
}
class AActor* UACFThreatManagerComponent::GetActorWithHigherThreat()
{
    float maxThreat = -1.f;
    AActor* target = nullptr;
    TArray<AActor*> pendingDelete;

    for (const auto& elem : ThreatMap) {
        IACFEntityInterface* entity = Cast<IACFEntityInterface>(elem.Key);

        if (!entity || !elem.Key || !IACFEntityInterface::Execute_IsEntityAlive(elem.Key)) {
            pendingDelete.Add(elem.Key);
        } else if (elem.Value > maxThreat) {
            maxThreat = elem.Value;
            target = elem.Key;
        }
    }

    for (auto* toDelete : pendingDelete) {
        RemoveThreatening(toDelete);
    }

    return target;
}

bool UACFThreatManagerComponent::IsActorAPotentialThreat(class AActor* threatening) const
{
    if (!threatening) {
        UE_LOG(ACFAILog, Warning, TEXT("invalid Threatening Actor -  UACFThreatManagerComponent"));

        return false;
    }

    if (GetThreatMultForActor(threatening) == 0.f) {
        return false;
    }
    if (DefaultThreatMap.Contains(threatening->GetClass())) {
        return true;
    }

    for (const auto& elem : DefaultThreatMap) {
        if (elem.Key && threatening->GetClass()->IsChildOf(elem.Key)) {
            return true;
        }
    }

    return false;
}

bool UACFThreatManagerComponent::IsThreatening(class AActor* threatening) const
{
    return ThreatMap.Contains(threatening);
}

float UACFThreatManagerComponent::GetThreatMultForActor(class AActor* threatening) const
{
    if (!threatening) {
        UE_LOG(ACFAILog, Warning, TEXT("invalid Threatening Actor -  UACFThreatManagerComponent"));
        return -1.f;
    }

    if (ThreatMultipliersByActor.Contains(threatening->GetClass())) {
        return *ThreatMultipliersByActor.Find(threatening->GetClass());
    }

    for (const auto& elem : ThreatMultipliersByActor) {
        if (elem.Key && threatening->GetClass()->IsChildOf(elem.Key)) {
            return elem.Value;
        }
    }
    return 1.f;
}

float UACFThreatManagerComponent::GetDefaultThreatForActor(AActor* threatening)
{
    const float* threat = DefaultThreatMap.Find(threatening->GetClass());

    if (threat && *threat) {
        return *threat;
    }

    for (const auto& elem : DefaultThreatMap) {
        if (elem.Key && threatening->GetClass()->IsChildOf(elem.Key)) {
            return elem.Value;
        }
    }
    return 0.f;
}

void UACFThreatManagerComponent::RemoveThreatening(AActor* threatening)
{
    if (ThreatMap.Contains(threatening)) {
        ThreatMap.FindAndRemoveChecked(threatening);
    }

    if (maxThreatening == threatening) {
        maxThreatening = nullptr;
      /*  OnNewMaxThreateningActor.Broadcast(maxThreatening);*/
    }
}

void UACFThreatManagerComponent::RemoveAllThreatenings()
{
    ThreatMap.Empty();
    OnNewMaxThreateningActor.Broadcast(nullptr);
}
