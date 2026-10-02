// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ACFRagdollMasterComponent.generated.h"


UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFRagdollMasterComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UACFRagdollMasterComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	void AddComponent(class UACFRagdollComponent* compToAdd);

	void RemoveComponent(class UACFRagdollComponent* compToAdd);

private:

	UPROPERTY()
	TArray<class UACFRagdollComponent*> currentlyActiveComponents;

	UPROPERTY()
	TArray<class UACFRagdollComponent*> pendingDelete;
		
};
