// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include <Components/SplineComponent.h>
#include "CCMTypes.h"
#include "CCMCameraSplineComponent.generated.h"

/**
 * 
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class CINEMATICCAMERAMANAGER_API UCCMCameraSplineComponent : public USplineComponent
{
	GENERATED_BODY()

public: 

	UFUNCTION(BlueprintPure, Category = CCM)
	FORCEINLINE FName GetCameraSequenceName() const {
		return SequenceName;
	}

	UFUNCTION(BlueprintPure, Category = CCM)
	FORCEINLINE FCCMCameraSequenceSettings GetCameraSequenceSettings() const {
		return SequenceSettings;
	}

	UFUNCTION(BlueprintPure, Category = CCM)
	class AActor* GetSequenceLookAtPointLocation() const;

	UFUNCTION(BlueprintCallable, Category = CCM)
	class AActor* GetLookAtPointLocationByName(const FName& lookAtPointName) const;


protected:

	UPROPERTY(EditDefaultsOnly, Category = CCM)
	FName SequenceName;

	UPROPERTY(EditDefaultsOnly, Category = CCM)
	FCCMCameraSequenceSettings SequenceSettings;
	
};
