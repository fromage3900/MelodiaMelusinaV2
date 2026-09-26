#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaOrreryChassis.generated.h"

class USceneComponent;
class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UPointLightComponent;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class UMaterialParameterCollection;
class UUserWidget;

/**
 * Presentation-only 3D orrery chassis for the menu layer: rings, petals and a core that unfold
 * closed -> latch -> bloom -> ignite -> settle on beat-locked times (0/117/234/469/703 ms at
 * 128 BPM, scaled by BPM). Renders itself through its own capture into RenderTarget against a
 * backdrop, so a widget can show it as a brush. Owns no menu state or input.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaOrreryChassis : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaOrreryChassis();

	/** Starts the unfold on the next beat (or after MaxBeatWaitSeconds). */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery")
	void Open();

	/** Folds back; the capture stops once fully closed. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery")
	void Close();

	UFUNCTION(BlueprintPure, Category = "Melodia|Orrery")
	bool IsOpen() const { return bOpening; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Orrery")
	UTextureRenderTarget2D* GetRenderTarget() const { return RenderTarget; }

	/** Finds or spawns the world's chassis (parked off-world), opens it and shows its capture in
	 * the widget's Image named ImageName. Returns the chassis, or null if the image is missing. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery", meta = (WorldContext = "WorldContextObject"))
	static AMelodiaOrreryChassis* ShowInWidget(UObject* WorldContextObject, UUserWidget* Widget, FName ImageName = TEXT("OrreryView"));

	/** Folds every chassis in the world. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Orrery", meta = (WorldContext = "WorldContextObject"))
	static void CloseAll(UObject* WorldContextObject);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery")
	float BPM = 128.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery", meta = (ClampMin = "0.0"))
	float MaxBeatWaitSeconds = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery", meta = (ClampMin = "1", ClampMax = "5"))
	int32 RingCount = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery", meta = (ClampMin = "3", ClampMax = "16"))
	int32 PetalCount = 8;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Orrery", meta = (ClampMin = "64"))
	int32 RenderTargetSize = 1024;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UStaticMesh> RingMesh;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UStaticMesh> PetalMesh;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UStaticMesh> CoreMesh;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UMaterialInterface> RingMaterial;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UMaterialInterface> PetalMaterial;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UMaterialInterface> CoreMaterial;

	UPROPERTY(EditAnywhere, Category = "Melodia|Orrery|Look")
	TObjectPtr<UMaterialInterface> BackdropMaterial;

	UPROPERTY(VisibleAnywhere, Category = "Melodia|Orrery")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "Melodia|Orrery")
	TObjectPtr<UStaticMeshComponent> Core;

	UPROPERTY(VisibleAnywhere, Category = "Melodia|Orrery")
	TObjectPtr<UStaticMeshComponent> Backdrop;

	UPROPERTY(VisibleAnywhere, Category = "Melodia|Orrery")
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(VisibleAnywhere, Category = "Melodia|Orrery")
	TObjectPtr<USceneCaptureComponent2D> Capture;

private:
	void BuildParts();
	void ApplyPose(float Ms, float DeltaSeconds);
	float ReadBeatPhase() const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Rings;

	UPROPERTY(Transient)
	TArray<TObjectPtr<USceneComponent>> PetalPivots;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Petals;

	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> RenderTarget;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> Palette;

	bool bOpening = false;
	bool bWaitingForBeat = false;
	float BeatWait = 0.0f;
	float LastBeatPhase = 0.0f;
	/** Position on the 128-BPM timeline in ms; 0 = closed. */
	float TimelineMs = 0.0f;
	float SpinDegrees = 0.0f;
	float BaseLightIntensity = 0.0f;
};
