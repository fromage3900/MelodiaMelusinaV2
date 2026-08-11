#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaReactiveMeshRegistrar.generated.h"

UCLASS()
class MELODIACORE_API UMelodiaReactiveMeshRegistrar : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Tag that actors must carry to have their meshes auto-registered for beat reactivity. */
	static const FName ReactiveTag;
};
