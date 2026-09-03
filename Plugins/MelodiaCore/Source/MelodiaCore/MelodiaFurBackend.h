#pragma once

#include "CoreMinimal.h"
#include "MelodiaResonanceGardenData.h"
#include "MelodiaFurBackend.generated.h"

/**
 * Melodia-owned adapter boundary for Groom, shell/card and external fur backends.
 * Third-party code must implement this boundary in an optional adapter plugin.
 */
UCLASS(Abstract, Blueprintable, EditInlineNew, DefaultToInstanced)
class MELODIACORE_API UMelodiaFurBackendAdapter : public UObject
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Fur")
	bool Initialize(const FMelodiaFurProfile& InProfile);
	virtual bool Initialize_Implementation(const FMelodiaFurProfile& InProfile);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Fur")
	void SetDistance(float Distance);
	virtual void SetDistance_Implementation(float Distance);

	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category="Melodia|Fur")
	void ApplyResonance(float Intensity);
	virtual void ApplyResonance_Implementation(float Intensity);

	UFUNCTION(BlueprintPure, Category="Melodia|Fur")
	EMelodiaFurBackendKind GetActiveBackend() const { return ActiveBackend; }

	UFUNCTION(BlueprintPure, Category="Melodia|Fur")
	float GetResonanceIntensity() const { return ResonanceIntensity; }

protected:
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Melodia|Fur")
	FMelodiaFurProfile ActiveProfile;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Melodia|Fur")
	EMelodiaFurBackendKind ActiveBackend = EMelodiaFurBackendKind::ShellCard;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Melodia|Fur")
	float ResonanceIntensity = 0.0f;
};
