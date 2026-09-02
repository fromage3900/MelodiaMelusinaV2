#include "MelodiaStarskiffPawn.h"

#include "Components/InputComponent.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaTravelSubsystem.h"
#include "MelodiaTraversalCapabilityProvider.h"
#include "Engine/GameInstance.h"

AMelodiaStarskiffPawn::AMelodiaStarskiffPawn()
{
	PrimaryActorTick.bCanEverTick = false;
	Movement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("StarskiffMovement"));
	Movement->MaxSpeed = 900.0f;
	Movement->Acceleration = 1800.0f;
	Movement->Deceleration = 2200.0f;
}

void AMelodiaStarskiffPawn::BeginPlay()
{
	Super::BeginPlay();
	if (Movement)
	{
		Movement->UpdatedComponent = GetRootComponent();
	}
}

void AMelodiaStarskiffPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	if (!PlayerInputComponent)
	{
		return;
	}
	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &AMelodiaStarskiffPawn::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &AMelodiaStarskiffPawn::MoveRight);
}

bool AMelodiaStarskiffPawn::CanBoard(AActor* InteractingActor, FName& OutBlockReason) const
{
	OutBlockReason = NAME_None;
	const APawn* Pawn = Cast<APawn>(InteractingActor);
	if (!Pawn || !Pawn->IsPlayerControlled())
	{
		OutBlockReason = TEXT("boarding_requires_player");
		return false;
	}
	if (FVector::DistSquared(Pawn->GetActorLocation(), GetActorLocation()) > FMath::Square(BoardingRadius))
	{
		OutBlockReason = TEXT("boarding_out_of_range");
		return false;
	}

	const UGameInstance* GI = GetGameInstance();
	const UMelodiaNarrativeSubsystem* Narrative = GI ? GI->GetSubsystem<UMelodiaNarrativeSubsystem>() : nullptr;
	const bool bReadyFlag = Narrative && Narrative->GetNarrativeRecord().Flags.FindRef(TEXT("flag.sea_above.starskiff_ready"));
	const UMelodiaTraversalCapabilityRegistry* Registry = GI ? GI->GetSubsystem<UMelodiaTraversalCapabilityRegistry>() : nullptr;
	FName CapabilityReason;
	const bool bCapabilityReady = Registry && Registry->QueryCapability(RequiredCapabilityId, TraversalCapabilityContextId, CapabilityReason);
	if (!bReadyFlag && !bCapabilityReady)
	{
		OutBlockReason = CapabilityReason.IsNone() ? FName(TEXT("starskiff_not_unlocked")) : CapabilityReason;
		return false;
	}
	return true;
}

bool AMelodiaStarskiffPawn::TryBoard(AActor* InteractingActor)
{
	FName BlockReason;
	if (bBoarded || !CanBoard(InteractingActor, BlockReason))
	{
		return false;
	}

	APawn* Pawn = Cast<APawn>(InteractingActor);
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC)
	{
		return false;
	}
	BoardedPawn = Pawn;
	bBoarded = true;
	PC->Possess(this);
	UE_LOG(LogTemp, Log, TEXT("MELODIA_STARSKIFF boarded pawn=%s"), *GetNameSafe(Pawn));
	return true;
}

bool AMelodiaStarskiffPawn::TryBoardNearestPlayer()
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	return PC && TryBoard(PC->GetPawn());
}

void AMelodiaStarskiffPawn::Disembark()
{
	if (!bBoarded)
	{
		return;
	}
	APlayerController* PC = Cast<APlayerController>(GetController());
	APawn* Pawn = BoardedPawn.Get();
	bBoarded = false;
	BoardedPawn.Reset();
	if (PC && Pawn)
	{
		PC->Possess(Pawn);
	}
}

bool AMelodiaStarskiffPawn::RequestBoatTraversal(FName DestinationMap, FName DestinationSpawnTag)
{
	if (!bBoarded)
	{
		return false;
	}
	if (DestinationMap.IsNone())
	{
		DestinationMap = DefaultDestinationMap;
	}
	if (DestinationSpawnTag.IsNone())
	{
		DestinationSpawnTag = DefaultDestinationSpawnTag;
	}
	UMelodiaTravelSubsystem* Travel = UMelodiaTravelSubsystem::Get(this);
	return Travel && Travel->TravelTo(DestinationMap, DestinationSpawnTag);
}

void AMelodiaStarskiffPawn::MoveForward(float Value)
{
	if (bBoarded && !FMath::IsNearlyZero(Value))
	{
		AddMovementInput(GetActorForwardVector(), Value);
	}
}

void AMelodiaStarskiffPawn::MoveRight(float Value)
{
	if (bBoarded && !FMath::IsNearlyZero(Value))
	{
		AddMovementInput(GetActorRightVector(), Value);
	}
}
