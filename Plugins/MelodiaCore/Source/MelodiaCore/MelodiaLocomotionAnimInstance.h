#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "MelodiaLocomotionAnimInstance.generated.h"

/** Small native data bridge for thread-safe locomotion graphs. */
UCLASS(Blueprintable)
class MELODIACORE_API UMelodiaLocomotionAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	FVector PawnVelocity = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	FVector PawnAcceleration = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	float RuntimeGroundSpeed = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	bool bRuntimeShouldMove = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	bool bRuntimeIsInAir = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	bool bRuntimeIsGrounded = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	float RuntimeVerticalSpeed = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	bool bRuntimeIsGliding = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Locomotion")
	bool bRuntimeIsSprinting = false;
};
