#include "MelodiaFallRecoveryVolume.h"

#include "GameFramework/Pawn.h"

AMelodiaFallRecoveryVolume::AMelodiaFallRecoveryVolume()
{
	OnActorBeginOverlap.AddUniqueDynamic(this, &AMelodiaFallRecoveryVolume::HandleActorEntered);
}

void AMelodiaFallRecoveryVolume::BeginPlay()
{
	Super::BeginPlay();
	if (!IsValid(SafeAnchor))
	{
		UE_LOG(LogTemp, Error, TEXT("Fall recovery volume '%s' has no SafeAnchor."), *GetName());
	}
}

void AMelodiaFallRecoveryVolume::HandleActorEntered(AActor* OverlappedActor, AActor* OtherActor)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!Pawn || !Pawn->IsPlayerControlled() || !IsValid(SafeAnchor))
	{
		return;
	}
	const FVector Destination = SafeAnchor->GetActorLocation() + FVector::UpVector * VerticalOffset;
	if (!Pawn->TeleportTo(Destination, SafeAnchor->GetActorRotation(), false, true))
	{
		UE_LOG(LogTemp, Error, TEXT("Fall recovery volume '%s' failed to recover pawn '%s'."),
			*GetName(), *GetNameSafe(Pawn));
	}
}
