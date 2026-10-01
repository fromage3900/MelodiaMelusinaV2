// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFWheeledVehiclePawn.h"
#include "ACFMountPointComponent.h"
#include "ACFMountableComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include "ARSStatisticsComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "GenericTeamAgentInterface.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Net/UnrealNetwork.h"
#include "Perception/AIPerceptionStimuliSourceComponent.h"
#include "Perception/AISense_Sight.h"
#include <Engine/World.h>
#include <GameFramework/Controller.h>
#include "Components/ACFTeamComponent.h"

AACFWheeledVehiclePawn::AACFWheeledVehiclePawn()
{
    bReplicates = true;

    StatisticsComp = CreateDefaultSubobject<UARSStatisticsComponent>(
        TEXT("Statistic Component"));

    AIPerceptionStimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(
        TEXT("Perception Stimuli Component"));
    DamageHandlerComp = CreateDefaultSubobject<UACFDamageHandlerComponent>(
        TEXT("Damage Handler Component"));

    MountComponent = CreateDefaultSubobject<UACFMountableComponent>(TEXT("Mount Component"));
    EffetsComp = CreateDefaultSubobject<UACFEffectsManagerComponent>(TEXT("Effexts Component"));
    DismountPoint = CreateDefaultSubobject<UACFMountPointComponent>(TEXT("Enter/Exit Point"));
    TeamComponent = CreateDefaultSubobject<UACFTeamComponent>(TEXT("TeamComponent"));

    DismountPoint->SetupAttachment(RootComponent);
    AIPerceptionStimuliSource->bAutoRegister = true;
    AIPerceptionStimuliSource->RegisterForSense(UAISense_Sight::StaticClass());
}

// Called when the game starts or when spawned
void AACFWheeledVehiclePawn::BeginPlay()
{

    Super::BeginPlay();

    if (UKismetSystemLibrary::IsServer(this)) {

        if (StatisticsComp) {
            StatisticsComp->InitializeAttributeSet();
        }

        if (DamageHandlerComp) {
            DamageHandlerComp->OnOwnerDeath.AddDynamic(
                this, &AACFWheeledVehiclePawn::HandleDeath);
        }
    }
}
float AACFWheeledVehiclePawn::TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
    return DamageHandlerComp->TakeDamage(this, Damage, DamageEvent, EventInstigator, DamageCauser);
}

FText AACFWheeledVehiclePawn::GetInteractableName_Implementation()
{
    return FText::FromName(VehicleName);
}

FACFDamageEvent AACFWheeledVehiclePawn::GetLastDamageInfo() const
{
    return DamageHandlerComp->GetLastDamageInfo();
}

void AACFWheeledVehiclePawn::HandleDeath()
{
    OnVehicleDestroyed();
}

void AACFWheeledVehiclePawn::OnVehicleDestroyed_Implementation()
{
    // IMPLEMENT ME IN CHILD CLASSES!
}

float AACFWheeledVehiclePawn::GetEntityExtentRadius_Implementation() const
{
    FVector origin, extent;
    GetActorBounds(true, origin, extent, false);
    return extent.X;
}

bool AACFWheeledVehiclePawn::CanBeInteracted_Implementation(class APawn* Pawn)
{
    return !MountComponent->IsMounted();
}

FGameplayTag AACFWheeledVehiclePawn::GetEntityCombatTeam_Implementation() const
{
    return TeamComponent ? TeamComponent->GetTeam() : FGameplayTag();
}

void AACFWheeledVehiclePawn::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
    if (UWorld* World = GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            const FGenericTeamId GenericTeamId = TeamSubsystem->FromTagToTeamId(inCombatTeam);
            SetGenericTeamId(GenericTeamId);
        }
    }
}

FGenericTeamId AACFWheeledVehiclePawn::GetGenericTeamId() const
{
    return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

void AACFWheeledVehiclePawn::SetGenericTeamId(const FGenericTeamId& TeamID)
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        const FGameplayTag TeamTag = TeamSubsystem->FromTeamIdToTag(TeamID);
        if (TeamComponent) {

            TeamComponent->ServerRequestTeamChange(TeamTag);
        }
    }
}

ETeamAttitude::Type AACFWheeledVehiclePawn::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {

        return TeamSubsystem->GetAttitudeBetweenActors(this, &OtherTeam);
    }
    return ETeamAttitude::Neutral;
}
