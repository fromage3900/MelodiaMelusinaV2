// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ACFMoralityComponent.h"
#include "Net/UnrealNetwork.h"

UACFMoralityComponent::UACFMoralityComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UACFMoralityComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFMoralityComponent::AddMoralityPoint_Implementation(FGameplayTag Alignment, float Points)
{
    if (Alignment.IsValid())
    {
        for (auto& MoralityEntry : MoralityPoints)
        {
            if (MoralityEntry == FMoralityPoint(Alignment, 0))
            {
                MoralityEntry.Points += Points;
                OnRep_MoralityPoints();
                return;
            }
        }
        MoralityPoints.Add(FMoralityPoint(Alignment, Points));
        OnRep_MoralityPoints();
    }
}

float UACFMoralityComponent::GetMoralityPoints(FGameplayTag Alignment) const
{
    const FMoralityPoint* point = MoralityPoints.FindByKey(Alignment);
    if (point) {
        return point->Points;
    }
    return 0;
}

FGameplayTag UACFMoralityComponent::GetMoralityAlignment() const
{
    FGameplayTag BestAlignment;
    int32 MaxPoints = INT32_MIN;
    
    for (const auto& MoralityEntry : MoralityPoints)
    {
        if (MoralityEntry.Points > MaxPoints)
        {
            MaxPoints = MoralityEntry.Points;
            BestAlignment = MoralityEntry.Alignment;
        }
    }
    return BestAlignment;
}

void UACFMoralityComponent::ResetMorality_Implementation()
{
    MoralityPoints.Empty();
    OnRep_MoralityPoints();
}

void UACFMoralityComponent::OnRep_MoralityPoints()
{
    // Logic to handle updates on the client side if necessary
     OnMoralityChanged.Broadcast();
}

void UACFMoralityComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFMoralityComponent, MoralityPoints);
}




