#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaNPCData.h"
#include "MelodiaNPCBase.generated.h"

class USceneComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;

UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaNPCBase : public AActor
{
	GENERATED_BODY()
public:
	AMelodiaNPCBase();
	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TSoftObjectPtr<UMelodiaNPCDefinitionAsset> NPCDefinition;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UStaticMeshComponent> StaticMeshComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	UFUNCTION(BlueprintCallable, Category="Melodia|NPC")
	bool SetNPCDefinition(UMelodiaNPCDefinitionAsset* InDefinition);

	UFUNCTION(BlueprintCallable, Category="Melodia|NPC")
	bool ApplyNPCDefinition();

	UFUNCTION(BlueprintPure, Category="Melodia|NPC")
	const FMelodiaNPCDef& GetActiveNPCDefinition() const { return ActiveDefinition; }

protected:
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Melodia|NPC")
	FMelodiaNPCDef ActiveDefinition;

	void ApplyFallbackDefinition();
};