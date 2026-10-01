// 2020 - All Rights Reserved - Pakyman Prod.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "CCMLookAtPointComponent.h"
#include "ATSTargetPointComponent.generated.h"


UCLASS(ClassGroup = (ATS), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTTARGETINGSYSTEM_API UATSTargetPointComponent : public UCCMLookAtPointComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UATSTargetPointComponent();


	/*Returns desired camera offset for this point*/
	UFUNCTION(BlueprintPure, Category = ATS)
	FORCEINLINE	FName GetPointCameraEvent() const {
		return CameraEvent;
	}

protected:

	/*The camera event triggered when this point gets targeted*/
	UPROPERTY(EditDefaultsOnly, Category = ATS)
	FName CameraEvent;
		
};
