#include "MelodiaLocomotionAnimInstance.h"

#include "GameFramework/Pawn.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "MelodiaSmokeCharacter.h"

void UMelodiaLocomotionAnimInstance::NativeUpdateAnimation(const float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	const APawn* Pawn = TryGetPawnOwner();
	PawnVelocity = Pawn ? Pawn->GetVelocity() : FVector::ZeroVector;
	const UCharacterMovementComponent* Movement = Pawn ? Cast<UCharacterMovementComponent>(Pawn->GetMovementComponent()) : nullptr;
	PawnAcceleration = Movement ? Movement->GetCurrentAcceleration() : FVector::ZeroVector;
	RuntimeGroundSpeed = PawnVelocity.Size2D();
	bRuntimeShouldMove = RuntimeGroundSpeed > 3.0f && PawnAcceleration.SizeSquared2D() > 0.0f;
	const bool bMovementIsFalling = Movement ? Movement->IsFalling() : false;
	const AMelodiaSmokeCharacter* Smoke = Cast<AMelodiaSmokeCharacter>(Pawn);
	bRuntimeIsGliding = Smoke ? Smoke->bIsGliding : false;

	// Gliding still uses MOVE_Falling for physics, but it must not keep the
	// locomotion graph's generic jump/fall state eligible at the same time.
	bRuntimeIsInAir = bMovementIsFalling && !bRuntimeIsGliding;
	bRuntimeIsGrounded = !bMovementIsFalling;
	RuntimeVerticalSpeed = PawnVelocity.Z;
}
