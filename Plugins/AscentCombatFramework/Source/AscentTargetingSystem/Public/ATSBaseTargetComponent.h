// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ATSBaseTargetComponent.generated.h"


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNewTarget, AActor*, newTarget);


class AActor;

UCLASS(ClassGroup = (ATS), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTTARGETINGSYSTEM_API UATSBaseTargetComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UATSBaseTargetComponent();

	/*Forces to target the selected actor*/
	UFUNCTION(BlueprintCallable, Category = "ATS")
	virtual	void SetCurrentTarget(class AActor* target) {
		SetTarget(target);
	}

	UFUNCTION(Server, Reliable, WithValidation, Category = "ATS")
	void SetTarget(class AActor* target);

	UFUNCTION(Server, Reliable, WithValidation, Category = "ATS")
	void SetTargetPoint(class UATSTargetPointComponent* targetPoint);

	/*Return the currently focused target*/
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ATS")
	AActor* GetCurrentTarget() const { return CurrentTarget; }

	/*Returns if there is a valid target*/
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ATS")
	bool HasTarget() const { return CurrentTarget != nullptr; }

	/*Return the TargetPointComponent focused of the Current target*/
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ATS")
	FORCEINLINE	class UATSTargetPointComponent* GetCurrentTargetPoint() const { return CurrentTargetPoint; }

	/*Returns true if the target is in sight with the actual pawn owned by the controller*/
	UFUNCTION(BlueprintPure, Category = ATS)
	bool IsTargetInSight() const;

	/*Returns true if the potential target is in sight with the actual pawn owned by the controller*/
	UFUNCTION(BlueprintPure, Category = ATS)
	bool IsPotentialTargetInSight(class AActor* potentialTarget) const;

	/*Get the world location of current target point*/
	UFUNCTION(BlueprintCallable, Category = ATS)
	FVector GetCurrentTargetPointLocation() const;

	UPROPERTY(BlueprintAssignable, Category = ATS)
	FOnNewTarget OnNewTarget;

protected:

	/*Checks if there is any blocking actor in the line sight to current target*/
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ATS")
	bool bCheckLineSight = false;
	UPROPERTY(ReplicatedUsing = OnRep_CurrentTarget)
	class AActor* CurrentTarget;

	UPROPERTY(Replicated)
	class UATSTargetPointComponent* CurrentTargetPoint;


	UFUNCTION()
	void OnRep_CurrentTarget();

	virtual void OnTargetChanged();

};
