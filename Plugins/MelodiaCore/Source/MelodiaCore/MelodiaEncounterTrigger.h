// Encounter trigger ΓÇö overlap volume that starts a rhythm battle.
// Adapted from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/TextRenderComponent.h"
#include "MelodiaEnemyDefinition.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaEncounterTrigger.generated.h"

class UStaticMeshComponent;
class ACharacter;

UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaEncounterTrigger : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaEncounterTrigger();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Encounter")
	TObjectPtr<UBoxComponent> TriggerVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Encounter")
	TObjectPtr<UTextRenderComponent> EncounterLabel;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Encounter")
	TObjectPtr<UPointLightComponent> EncounterLight;

	/** Optional named-enemy mesh. It stays hidden until the encounter begins. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Encounter")
	TObjectPtr<UStaticMeshComponent> EnemyPresentation;

	/** Optional Blueprint enemy actor for skeletal/VFX presentation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter|Presentation")
	TObjectPtr<AActor> EnemyPresentationActor = nullptr;

	/** Combat state component attached to this actor ΓÇö serves as battle controller. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter")
	int32 EncounterLevel = 1;

	/** Named demo enemy. Leave None to use legacy encounter-level scaling. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter")
	FName EnemyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter")
	FText EncounterDisplayName = FText::FromString(TEXT("Encounter"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter")
	bool bOneShot = true;

	/** Prefer an authored, tagged stock JRPG encounter when the host project provides one. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter|Integration")
	bool bPreferStockJRPGPresentation = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Encounter")
	bool bTriggered = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Encounter")
	float CooldownSeconds = 5.0f;

	UFUNCTION(BlueprintCallable, Category="Melodia|Encounter")
	void ConfigureEnemyPresentation(const FMelodiaEnemyDef& Enemy);

	UFUNCTION(BlueprintCallable, Category="Melodia|Encounter")
	void SetEnemyPresentationVisible(bool bVisible);

	UFUNCTION(BlueprintCallable, Category="Melodia|Encounter")
	bool StartEncounterForPlayer();

protected:
	virtual void BeginPlay() override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION()
	void OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

private:
	bool TryStartStockJRPGBattle();
	bool TryStartEncounter(ACharacter* PlayerCharacter);
	double LastTriggerTime = -1000.0;
};
