#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaWaveHarpHUDWidget.generated.h"
class UFont;

/** Read-only player guidance over the existing UI bridge. */
UCLASS()
class BS_GODFILE_API UMelodiaWaveHarpHUDWidget final : public UUserWidget
{
 GENERATED_BODY()
public:
 virtual void NativeConstruct() override;
 virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geometry,
  const FSlateRect& Cull, FSlateWindowElementList& Elements, int32 Layer,
  const FWidgetStyle& Style, bool bEnabled) const override;
private:
 UPROPERTY(Transient) TObjectPtr<UFont> InterFont;
};
