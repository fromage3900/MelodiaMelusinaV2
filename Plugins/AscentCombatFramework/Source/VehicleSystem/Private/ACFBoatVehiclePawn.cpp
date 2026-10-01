#include "ACFBoatVehiclePawn.h"
#include "ACFWaterVehicleComponent.h"
#include "ACFMountPointComponent.h"
#include "ACFMountableComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include "ARSStatisticsComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Components/ACFTeamComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/World.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Perception/AIPerceptionStimuliSourceComponent.h"
#include "Perception/AISense_Sight.h"

AACFBoatVehiclePawn::AACFBoatVehiclePawn()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;

    Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("VehicleMesh"));
    Mesh->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
    Mesh->BodyInstance.bSimulatePhysics = true;
    Mesh->BodyInstance.bNotifyRigidBodyCollision = true;
    RootComponent = Mesh;

    StatisticsComp = CreateDefaultSubobject<UARSStatisticsComponent>(TEXT("Statistic Component"));
    DamageHandlerComp = CreateDefaultSubobject<UACFDamageHandlerComponent>(TEXT("Damage Handler Component"));
    EffectsComp = CreateDefaultSubobject<UACFEffectsManagerComponent>(TEXT("Effects Component"));
    MountComponent = CreateDefaultSubobject<UACFMountableComponent>(TEXT("Mount Component"));
    TeamComponent = CreateDefaultSubobject<UACFTeamComponent>(TEXT("TeamComponent"));
    WaterVehicleComp = CreateDefaultSubobject<UACFWaterVehicleComponent>(TEXT("WaterVehicleComponent"));

    AIPerceptionStimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(TEXT("Perception Stimuli Component"));
    AIPerceptionStimuliSource->bAutoRegister = true;
    AIPerceptionStimuliSource->RegisterForSense(UAISense_Sight::StaticClass());
}

void AACFBoatVehiclePawn::BeginPlay()
{
    Super::BeginPlay();

    if (HasAuthority()) {
        if (StatisticsComp) {
            StatisticsComp->InitializeAttributeSet();
        }
        if (DamageHandlerComp) {
            DamageHandlerComp->OnOwnerDeath.AddDynamic(this, &AACFBoatVehiclePawn::HandleDeath);
        }
    }
}

float AACFBoatVehiclePawn::TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
    return DamageHandlerComp ? DamageHandlerComp->TakeDamage(this, Damage, DamageEvent, EventInstigator, DamageCauser) : 0.f;
}

FText AACFBoatVehiclePawn::GetInteractableName_Implementation()
{
    return FText::FromName(VehicleName);
}

FACFDamageEvent AACFBoatVehiclePawn::GetLastDamageInfo() const
{
    return DamageHandlerComp ? DamageHandlerComp->GetLastDamageInfo() : FACFDamageEvent();
}

void AACFBoatVehiclePawn::HandleDeath()
{
    OnVehicleDestroyed();
}

void AACFBoatVehiclePawn::OnVehicleDestroyed_Implementation() {}

float AACFBoatVehiclePawn::GetEntityExtentRadius_Implementation() const
{
    FVector Origin, Extent;
    GetActorBounds(true, Origin, Extent, false);
    return Extent.X;
}

bool AACFBoatVehiclePawn::CanBeInteracted_Implementation(class APawn* Pawn)
{
    return MountComponent && !MountComponent->IsMounted();
}

FGameplayTag AACFBoatVehiclePawn::GetEntityCombatTeam_Implementation() const
{
    return TeamComponent ? TeamComponent->GetTeam() : FGameplayTag();
}

void AACFBoatVehiclePawn::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
    if (UWorld* World = GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            SetGenericTeamId(TeamSubsystem->FromTagToTeamId(inCombatTeam));
        }
    }
}

FGenericTeamId AACFBoatVehiclePawn::GetGenericTeamId() const
{
    return TeamComponent ? TeamComponent->GetGenericTeamId() : FGenericTeamId::NoTeam;
}

void AACFBoatVehiclePawn::SetGenericTeamId(const FGenericTeamId& TeamID)
{
    if (TeamComponent && GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
            TeamComponent->ServerRequestTeamChange(TeamSubsystem->FromTeamIdToTag(TeamID));
        }
    }
}

ETeamAttitude::Type AACFBoatVehiclePawn::GetTeamAttitudeTowards(const AActor& Other) const
{
    if (UWorld* World = GetWorld()) {
        if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
            return TeamSubsystem->GetAttitudeBetweenActors(this, &Other);
        }
    }
    return ETeamAttitude::Neutral;
}