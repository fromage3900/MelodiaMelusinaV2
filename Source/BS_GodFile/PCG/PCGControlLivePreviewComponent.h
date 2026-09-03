#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PCGControlLivePreviewComponent.generated.h"

class UPCGComponent;

/**
 * Opt-in, debounced preview bridge for BP_MelodiaPCGControl.
 *
 * It watches the existing eleven driver properties and requests PCG
 * regeneration only after the user stops dragging a control. It never owns a
 * clock, material collection, or music/audio subsystem. Authored point-array
 * graphs still need their normal builder rebuild when a discrete layout must
 * be changed; data-driven PCG branches can react immediately here.
 */
UCLASS(ClassGroup = (PCG), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UPCGControlLivePreviewComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UPCGControlLivePreviewComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Enable the preview bridge explicitly on a proof/staging control actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview")
	bool bEnabled = false;

	/** Regeneration is editor-tickable, so controls update without entering PIE. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview")
	bool bTickInEditorPreview = true;

	/** Quiet time after the last knob change before generation is requested. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview", meta = (ClampMin = "0.05"))
	float ChangeDebounceSeconds = 0.20f;

	/** 0 means all world PCG components; proof levels should use a finite radius. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview", meta = (ClampMin = "0.0"))
	float DiscoveryRadius = 5000.0f;

	/** If set, only these components are regenerated; otherwise nearby discovery is used. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview")
	TArray<TObjectPtr<UPCGComponent>> TargetComponents;

	/** Optional graph-name filter. Empty means any graph in the selected scope. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PCG|Live Preview")
	FString GraphNameFilter = TEXT("PCG_");

	UFUNCTION(BlueprintCallable, Category = "PCG|Live Preview")
	void RequestRegeneration();

	UFUNCTION(BlueprintCallable, Category = "PCG|Live Preview")
	void SetLivePreviewEnabled(bool bInEnabled);

	UFUNCTION(BlueprintPure, Category = "PCG|Live Preview")
	int32 GetLastRegeneratedComponentCount() const { return LastRegeneratedComponentCount; }

	UFUNCTION(BlueprintPure, Category = "PCG|Live Preview")
	bool IsRegenerationPending() const { return bRegenerationPending; }

private:
	uint32 BuildControlFingerprint() const;
	void DiscoverAndRegenerate();
	bool IsGraphAllowed(const UPCGComponent* Component) const;

	uint32 LastControlFingerprint = 0;
	float TimeSinceChange = 0.0f;
	bool bRegenerationPending = false;
	int32 LastRegeneratedComponentCount = 0;
};
