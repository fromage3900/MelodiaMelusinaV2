#include "MelodiaSeamPortal.h"

#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "MelodiaNarrativeSubsystem.h"

AMelodiaSeamPortal::AMelodiaSeamPortal()
{
	PrimaryActorTick.bCanEverTick = false;

	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	SetRootComponent(Trigger);
	Trigger->SetBoxExtent(FVector(20.0, 90.0, 120.0));
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);
}

void AMelodiaSeamPortal::BeginPlay()
{
	Super::BeginPlay();
	// Bind on live instances only (not on the class default object during module load).
	Trigger->OnComponentBeginOverlap.AddUniqueDynamic(this, &AMelodiaSeamPortal::HandleOverlap);
}

FQuat AMelodiaSeamPortal::RollQuat() const
{
	const FVector Axis = RollAxis.GetSafeNormal();
	if (Axis.IsNearlyZero() || FMath::IsNearlyZero(RollDegrees))
	{
		return FQuat::Identity;
	}
	return FQuat(Axis, FMath::DegreesToRadians(RollDegrees));
}

void AMelodiaSeamPortal::ComputeSeam(const FVector& Location, const FQuat& Rotation, FVector& OutLocation, FQuat& OutRotation) const
{
	const FQuat Q = RollQuat();
	const FVector Pivot = bPivotIsActorLocation ? GetActorLocation() : PivotCm;
	OutLocation = Pivot + Q.RotateVector(Location - Pivot) + TranslationCm;
	OutRotation = (Q * Rotation).GetNormalized();
}

bool AMelodiaSeamPortal::ApplySeam(ACharacter* Traveller, const bool bUseCooldown)
{
	if (!IsValid(Traveller) || !GetWorld())
	{
		return false;
	}
	const double Now = GetWorld()->GetTimeSeconds();
	if (bUseCooldown)
	{
		if (const double* Last = LastCrossed.Find(Traveller))
		{
			if (Now - *Last < CooldownSeconds)
			{
				return false;
			}
		}
	}

	if (!NarrativeTravelId.IsNone())
	{
		// Narrative route: the travel request is the only thing this portal does.
		UMelodiaNarrativeSubsystem* Narrative = UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(this);
		const bool bAccepted = Narrative && Narrative->RequestTravel(NarrativeTravelId);
		UE_LOG(LogTemp, Log, TEXT("MELODIA_SEAM_PORTAL travel id=%s accepted=%d"), *NarrativeTravelId.ToString(), bAccepted ? 1 : 0);
		if (bAccepted)
		{
			LastCrossed.Add(Traveller, Now);
			OnSeamCrossed.Broadcast(Traveller);
		}
		return bAccepted;
	}

	const FQuat Q = RollQuat();
	FVector NewLocation;
	FQuat NewRotation;
	ComputeSeam(Traveller->GetActorLocation(), Traveller->GetActorQuat(), NewLocation, NewRotation);

	UCharacterMovementComponent* Move = Traveller->GetCharacterMovement();
	const FVector NewVelocity = Move ? Q.RotateVector(Move->Velocity) : FVector::ZeroVector;
	const bool bRolls = !Q.Equals(FQuat::Identity, 1e-6f);

	Traveller->TeleportTo(NewLocation, NewRotation.Rotator(), /*bIsATest*/ false, /*bNoCheck*/ true);
	if (Move)
	{
		Move->Velocity = NewVelocity;
		if (bRolls)
		{
			// gravity turns with the surface the traveller is now standing on
			Move->SetGravityDirection(Q.RotateVector(Move->GetGravityDirection()).GetSafeNormal());
		}
	}
	if (bRolls)
	{
		if (AController* Controller = Traveller->GetController())
		{
			Controller->SetControlRotation((Q * Controller->GetControlRotation().Quaternion()).Rotator());
		}
	}
	LastCrossed.Add(Traveller, Now);
	OnSeamCrossed.Broadcast(Traveller);
	return true;
}

void AMelodiaSeamPortal::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	ACharacter* Traveller = Cast<ACharacter>(OtherActor);
	if (!Traveller)
	{
		return;
	}
	if (bRequireCrossingDirection)
	{
		const FVector Dir = CrossingDirection.GetSafeNormal();
		const FVector Velocity = Traveller->GetVelocity();
		if (Dir.IsNearlyZero() || FVector::DotProduct(Velocity, Dir) <= KINDA_SMALL_NUMBER)
		{
			return;
		}
	}
	ApplySeam(Traveller, /*bUseCooldown*/ true);
}
