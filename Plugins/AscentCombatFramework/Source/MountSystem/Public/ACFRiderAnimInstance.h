// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Animation/ACFRiderLayer.h"
#include "ACFRiderAnimInstance.generated.h"

/**
 * 
 */
UCLASS()
class MOUNTSYSTEM_API UACFRiderAnimInstance : public UACFRiderLayer
{
	GENERATED_BODY()
public: 

	/* begin play */
	virtual void NativeBeginPlay() override;

    void SetReferences();

    /* tick */
	virtual void NativeThreadSafeUpdateAnimation(float DeltaTime) override;


protected:

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	bool bIsRiding;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	float MountSpeed;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	float MountTurn;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	class UACFRiderComponent* RiderComp;

};
