#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "../Piano/PCGHeroMusic.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaPCGWaterGameplayBridgeComponent.generated.h"

class UMelodiaWaterGameplaySubsystem;

/** Bridges the existing hero-music judgement/completion events into water state. */
UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaPCGWaterGameplayBridgeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaPCGWaterGameplayBridgeComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	FGameplayTag WaterNetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	FGameplayTag TargetWaterNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	FGameplayTag ResonanceChannel;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	TMap<EMelodiaRhythmGrade, float> GradeStrength;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	EMelodiaRhythmGrade MinimumAcceptedGrade = EMelodiaRhythmGrade::Good;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	FGameplayTag CompletionPuzzleId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|PCG Bridge")
	FGameplayTag PlatformRouteId;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|PCG Bridge")
	FMelodiaWaterResonanceRequested OnResonanceRequested;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|PCG Bridge")
	bool RebindToHost();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|PCG Bridge")
	bool UnregisterWaterBindings();

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|PCG Bridge")
	float GetLastAppliedStrength() const { return LastAppliedStrength; }

private:
	UFUNCTION()
	void HandleNoteJudged(FPCGHeroMusicNoteEvent Event);

	UFUNCTION()
	void HandlePatternCompleted();

	float GetStrengthForGrade(EMelodiaRhythmGrade Grade) const;
	void SubmitResonance(float Strength, FGameplayTag PuzzleId, FGameplayTag RouteId, AActor* SourceActor);

	UPROPERTY(Transient)
	TWeakObjectPtr<APCGHeroMusicGraphHost> BoundHost;

	UPROPERTY(Transient)
	float LastAppliedStrength = 0.0f;

	bool bBound = false;
};
