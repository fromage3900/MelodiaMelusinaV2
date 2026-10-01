// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actors/ACFActor.h"
#include "ACFTeamManagerSubsystem.h"
#include "ARSStatisticsComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Net/UnrealNetwork.h"
#include <Components/AudioComponent.h>
#include <Engine/DamageEvents.h>
#include <Engine/World.h>
#include <GameFramework/Actor.h>
#include <GameFramework/Controller.h>
#include <Kismet/KismetSystemLibrary.h>
#include <Perception/AIPerceptionStimuliSourceComponent.h>
#include <Perception/AISense_Sight.h>

// Sets default values
AACFActor::AACFActor()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;

    bReplicates = true;

    StatisticsComp = CreateDefaultSubobject<UARSStatisticsComponent>(
        TEXT("Statistic Component"));

    AIPerceptionStimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(
        TEXT("Perception Stimuli Component"));
    DamageHandlerComp = CreateDefaultSubobject<UACFDamageHandlerComponent>(
        TEXT("Damage Handler Component"));
    EffetsComp = CreateDefaultSubobject<UACFEffectsManagerComponent>(TEXT("Effexts Component"));
    AIPerceptionStimuliSource->bAutoRegister = true;
    AIPerceptionStimuliSource->RegisterForSense(UAISense_Sight::StaticClass());

    EquipmentComp = CreateDefaultSubobject<UACFEquipmentComponent>(
        TEXT("Equipment Component"));

    AudioComp = CreateDefaultSubobject<UAudioComponent>(TEXT("Audio Component"));
    TeamComponent = CreateDefaultSubobject<UACFTeamComponent>(TEXT("TeamComponent"));

    AudioComp->SetRelativeLocation(FVector::ZeroVector);
    AudioComp->bAllowSpatialization = true;
    AudioComp->bOverrideAttenuation = false;

    RootComp = CreateDefaultSubobject<UPrimitiveComponent>(TEXT("Primitive Component"));
    RootComponent = RootComp;
}

// Called when the game starts or when spawned
void AACFActor::BeginPlay()
{

    Super::BeginPlay();

    if (UKismetSystemLibrary::IsServer(this)) {

        if (EquipmentComp) {
            EquipmentComp->InitializeStartingItems();
        }

        if (StatisticsComp) {
            StatisticsComp->InitializeAttributeSet();
        }

        if (DamageHandlerComp) {
            DamageHandlerComp->OnOwnerDeath.AddDynamic(
                this, &AACFActor::HandleDeath);
        }
    }
}

float AACFActor::TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
    return DamageHandlerComp->TakeDamage(this, Damage, DamageEvent, EventInstigator, DamageCauser);
}

void AACFActor::HandleDeath()
{
    if (EquipmentComp) {
        EquipmentComp->OnEntityOwnerDeath();
    }
    OnActorDestroyed();
}

void AACFActor::OnActorDestroyed_Implementation()
{
}

float AACFActor::GetEntityExtentRadius_Implementation() const
{
    FVector origin, extent;
    GetActorBounds(true, origin, extent, false);
    return extent.X;
}

FACFDamageEvent AACFActor::GetLastDamageInfo() const
{
    return DamageHandlerComp->GetLastDamageInfo();
}


FGameplayTag AACFActor::GetEntityCombatTeam_Implementation() const
{
    return TeamComponent ? TeamComponent->GetTeam() : FGameplayTag();
}

void AACFActor::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
    if (UWorld* World = GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            const FGenericTeamId GenericTeamId = TeamSubsystem->FromTagToTeamId(inCombatTeam);
            SetGenericTeamId(GenericTeamId);
        }
    }
}

FGenericTeamId AACFActor::GetGenericTeamId() const
{
    return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

void AACFActor::SetGenericTeamId(const FGenericTeamId& TeamID)
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        const FGameplayTag TeamTag = TeamSubsystem->FromTeamIdToTag(TeamID);
        if (TeamComponent) {

            TeamComponent->ServerRequestTeamChange(TeamTag);
        }
    }
}

ETeamAttitude::Type AACFActor::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {

        return TeamSubsystem->GetAttitudeBetweenActors(this, &OtherTeam);
    }
    return ETeamAttitude::Neutral;
}
