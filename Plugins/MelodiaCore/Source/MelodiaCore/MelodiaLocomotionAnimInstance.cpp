#include "MelodiaLocomotionAnimInstance.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "MelodiaSharedAuthorityInterfaces.h"

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

	// Traversal state comes from the pawn's UMelodiaTraversalComponent through
	// the shared authority interface -- never from AMelodiaSmokeCharacter, which
	// no spawned pawn derives from anymore (that cast was silently always null,
	// which is why the Glide state never fired after the JRPG pawn switch).
	TScriptInterface<IMelodiaTraversalStateProvider> Traversal;
	if (Pawn)
	{
		for (UActorComponent* Component : Pawn->GetComponents())
		{
			if (Component && Component->Implements<UMelodiaTraversalStateProvider>())
			{
				// Use the constructor (not SetObject) so the interface vtable
				// pointer is resolved via GetInterfaceAddress. SetObject alone
				// leaves the interface pointer null, causing a null dereference
				// on Traversal->IsGliding().
				Traversal = TScriptInterface<IMelodiaTraversalStateProvider>(Component);
				break;
			}
		}
	}
	bRuntimeIsGliding = Traversal.GetObject() != nullptr && Traversal->IsGliding();
	bRuntimeIsSprinting = Traversal.GetObject() != nullptr && Traversal->IsSprinting();

	// Gliding still uses MOVE_Falling for physics, but it must not keep the
	// locomotion graph's generic jump/fall state eligible at the same time.
	bRuntimeIsInAir = bMovementIsFalling && !bRuntimeIsGliding;
	bRuntimeIsGrounded = !bMovementIsFalling;
	RuntimeVerticalSpeed = PawnVelocity.Z;
}
