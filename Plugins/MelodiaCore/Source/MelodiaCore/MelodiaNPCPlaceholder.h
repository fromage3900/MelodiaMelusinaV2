// Lightweight, data-driven silhouette used while authored NPC meshes are unavailable.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaNPCPlaceholder.generated.h"

class UPointLightComponent;
class USphereComponent;
class UStaticMeshComponent;
class UTextRenderComponent;
class UMelodiaNPCInteractionComponent;
class UPrimitiveComponent;

struct FHitResult;

UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaNPCPlaceholder : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaNPCPlaceholder();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<USphereComponent> InteractionVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UStaticMeshComponent> Head;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UTextRenderComponent> Nameplate;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UPointLightComponent> AccentLight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	TObjectPtr<UMelodiaNPCInteractionComponent> Interaction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FName NPCId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FText DisplayName = FText::FromString(TEXT("NPC"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FName Archetype = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|NPC")
	FName BattleEnemyId = NAME_None;

	UFUNCTION(BlueprintCallable, CallInEditor, Category="Melodia|NPC")
	void ApplyArchetypePresentation();

private:
	UFUNCTION()
	void HandleInteractionRangeEntered(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

	UFUNCTION()
	void HandleInteractionRangeExited(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex);

	void SetInteractionStencil(int32 StencilValue);
	static bool IsPlayerPawn(const AActor* Actor);

	TSet<TWeakObjectPtr<UPrimitiveComponent>> PlayerOverlapComponents;

	FLinearColor GetArchetypeColor() const;
};
