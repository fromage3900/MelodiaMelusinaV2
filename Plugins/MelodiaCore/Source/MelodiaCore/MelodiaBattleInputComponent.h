#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InputActionValue.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaBattleInputComponent.generated.h"

class UMelodiaRhythmExecutionComponent;
class UInputMappingContext;
class UInputAction;

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second battle stack). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(ClassGroup=(Melodia), NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaBattleInputComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaBattleInputComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Input")
	FMelodiaRhythmWindows RhythmWindows;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Input")
	float InputCommandGrade = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Input")
	bool bAutoBindPlayerInput = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	bool bInputBound = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	int32 BasicInputCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	int32 SkillInputCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	int32 UltimateInputCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	FString LastInputCommandName;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	int32 ActiveSkillIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	FName ActiveSkillId = NAME_None;

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool BindBattleInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool UnbindBattleInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleBasicInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleSkillInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleUltimateInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleFleeInput();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleCycleSkillInput();

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Input")
	FString GetActiveSkillPrompt() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Input")
	bool HandleLaneTap(int32 LaneIndex);

	/** Runtime-created mapping context for battle inputs */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputMappingContext> BattleMappingContext;

	/** Runtime-created input actions */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> BasicAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> SkillAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> UltimateAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> FleeAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> CycleSkillAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> LaneTapAction0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> LaneTapAction1;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> LaneTapAction2;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Input")
	TObjectPtr<UInputAction> LaneTapAction3;

private:
	void CreateInputMappingContext();
	void OnBasicInputPressed(const FInputActionValue& Value);
	void OnSkillInputPressed(const FInputActionValue& Value);
	void OnUltimateInputPressed(const FInputActionValue& Value);
	void OnFleeInputPressed(const FInputActionValue& Value);
	void OnCycleSkillInputPressed(const FInputActionValue& Value);
	void OnLaneTapPressed(const FInputActionValue& Value, int32 LaneIndex);

	/** Track whether mapping context is added to the subsystem */
	bool bContextAdded = false;
};
