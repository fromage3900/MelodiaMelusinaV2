#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MelodiaPersonaTypes.h"
#include "MelodiaOverworldMinimapWidget.generated.h"

class UFont;

/**
 * Overworld minimap + compass drawn as an orrery dial. The heading ring (N/E/S/W) turns with the
 * camera; markers come from UMelodiaPersonaSubsystem::GetVisibleMinimapMarkers and are placed at
 * the real positions of the actors carrying each marker's ActorTag (clamped to the rim when far).
 * Presentation only: reads the marker authority, owns no marker state.
 */
UCLASS()
class BS_GODFILE_API UMelodiaOverworldMinimapWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	UMelodiaOverworldMinimapWidget(const FObjectInitializer& ObjectInitializer);

	/** World distance (cm) that maps to the dial's rim. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Minimap", meta = (ClampMin = "500.0"))
	float RangeCm = 4000.0f;

	/** Seconds between marker/actor refreshes; positions of known actors update every frame. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Minimap", meta = (ClampMin = "0.1"))
	float MarkerRefreshSeconds = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Melodia|Minimap")
	TObjectPtr<UFont> Font;

	/** Markers currently drawn (for tests and tooltips). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Minimap")
	int32 GetDrawnMarkerCount() const { return Tracked.Num(); }

	/** Camera yaw the compass is showing, degrees. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Minimap")
	float GetHeadingDegrees() const { return HeadingDegrees; }

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	struct FTrackedMarker
	{
		TWeakObjectPtr<AActor> Actor;
		EMelodiaMinimapMarkerType Type = EMelodiaMinimapMarkerType::Objective;
		FVector2D Offset = FVector2D::ZeroVector; // player-relative, rotated into dial space, in cm
	};

	void RefreshMarkers();

	TArray<FTrackedMarker> Tracked;
	float HeadingDegrees = 0.0f;
	float RefreshAccumulator = 0.0f;
};
