#include "MelodiaOverworldMinimapWidget.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/Font.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaPersonaSubsystem.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// Scoped so a unity build cannot merge these with the identical names in
	// MelodiaCalibrationWidget.cpp's anonymous namespace; both files landing in one
	// blob is a C2374/C2086 redefinition error for the whole module. The values are
	// deliberately per-file (lavender and night carry different alphas here), so this
	// is a scope fix, not a shared palette.
	namespace MinimapPalette
	{
		const FLinearColor Pearl(0.96f, 0.93f, 0.90f, 1.0f);
		const FLinearColor Rose(0.91f, 0.71f, 0.63f, 1.0f);
		const FLinearColor Lavender(0.73f, 0.65f, 0.94f, 0.7f);
		const FLinearColor Cyan(0.62f, 0.91f, 0.97f, 1.0f);
		const FLinearColor Ember(1.0f, 0.45f, 0.45f, 1.0f);
		const FLinearColor Night(0.043f, 0.035f, 0.125f, 0.72f);
	}
	using namespace MinimapPalette;

	FLinearColor MarkerColor(const EMelodiaMinimapMarkerType Type)
	{
		switch (Type)
		{
		case EMelodiaMinimapMarkerType::NPC: return Pearl;
		case EMelodiaMinimapMarkerType::Encounter: return Ember;
		case EMelodiaMinimapMarkerType::Exit: return Cyan;
		case EMelodiaMinimapMarkerType::SavePoint: return Lavender;
		default: return Rose;
		}
	}

	TArray<FVector2D> Circle(const FVector2D& Center, const float Radius, const int32 Segments = 72)
	{
		TArray<FVector2D> Points;
		for (int32 Index = 0; Index <= Segments; ++Index)
		{
			const float Angle = Index * 2.0f * PI / Segments;
			Points.Add(Center + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Radius);
		}
		return Points;
	}
}

UMelodiaOverworldMinimapWidget::UMelodiaOverworldMinimapWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	static ConstructorHelpers::FObjectFinder<UFont> UIFont(TEXT("/Game/Melodia/UI/Fonts/F_Melodia_UI.F_Melodia_UI"));
	Font = UIFont.Object;
}

void UMelodiaOverworldMinimapWidget::RefreshMarkers()
{
	Tracked.Reset();
	const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this);
	if (!Persona)
	{
		return;
	}
	for (const FMelodiaMinimapMarkerDefinition& Marker : Persona->GetVisibleMinimapMarkers())
	{
		if (Marker.ActorTag.IsNone())
		{
			continue;
		}
		TArray<AActor*> Actors;
		UGameplayStatics::GetAllActorsWithTag(this, Marker.ActorTag, Actors);
		for (AActor* Actor : Actors)
		{
			FTrackedMarker& Entry = Tracked.AddDefaulted_GetRef();
			Entry.Actor = Actor;
			Entry.Type = Marker.Type;
		}
	}
}

void UMelodiaOverworldMinimapWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	RefreshAccumulator -= InDeltaTime;
	if (RefreshAccumulator <= 0.0f)
	{
		RefreshAccumulator = MarkerRefreshSeconds;
		RefreshMarkers();
	}

	const APlayerController* PC = GetOwningPlayer();
	const APawn* Pawn = GetOwningPlayerPawn();
	if (!PC || !Pawn || !PC->PlayerCameraManager)
	{
		return;
	}
	HeadingDegrees = PC->PlayerCameraManager->GetCameraRotation().Yaw;
	const FRotator Yaw(0.0f, HeadingDegrees, 0.0f);
	const FVector Forward = Yaw.Vector();
	const FVector Right = FRotationMatrix(Yaw).GetScaledAxis(EAxis::Y);
	const FVector Origin = Pawn->GetActorLocation();
	for (FTrackedMarker& Entry : Tracked)
	{
		if (const AActor* Actor = Entry.Actor.Get())
		{
			const FVector Delta = Actor->GetActorLocation() - Origin;
			// Dial space: camera forward is up, right is right.
			Entry.Offset = FVector2D(FVector::DotProduct(Delta, Right), -FVector::DotProduct(Delta, Forward));
		}
	}
}

int32 UMelodiaOverworldMinimapWidget::NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const int32 SuperLayer = Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	FPaintContext Context(AllottedGeometry, MyCullingRect, OutDrawElements, SuperLayer, InWidgetStyle, bParentEnabled);
	const FVector2D Size = AllottedGeometry.GetLocalSize();
	const float Radius = FMath::Min(Size.X, Size.Y) * 0.46f;
	if (Radius < 8.0f)
	{
		return SuperLayer;
	}
	const FVector2D Center = Size * 0.5f;

	// Dial body: a soft disc approximated by a thick ring fill, then the orbit rings.
	for (float R = Radius * 0.1f; R < Radius; R += 6.0f)
	{
		UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, R), Night, true, 7.0f);
	}
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius), Rose, true, 1.6f);
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius * 0.62f), Lavender, true, 1.0f);
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius * 0.3f), Lavender, true, 0.8f);

	// Compass: ticks and cardinal letters rotate against the camera yaw.
	static const TCHAR* Letters[] = {TEXT("N"), TEXT("E"), TEXT("S"), TEXT("W")};
	for (int32 Tick = 0; Tick < 24; ++Tick)
	{
		const float WorldYaw = Tick * 15.0f;
		const float ScreenAngle = FMath::DegreesToRadians(WorldYaw - HeadingDegrees);
		const FVector2D Dir(FMath::Sin(ScreenAngle), -FMath::Cos(ScreenAngle));
		const float Inner = (Tick % 6 == 0) ? Radius * 0.9f : Radius * 0.95f;
		UWidgetBlueprintLibrary::DrawLine(Context, Center + Dir * Inner, Center + Dir * Radius, Rose, true, 1.0f);
		if (Tick % 6 == 0 && Font)
		{
			const bool bNorth = Tick == 0;
			const FVector2D At = Center + Dir * (Radius * 0.78f) - FVector2D(5.0f, 9.0f);
			UWidgetBlueprintLibrary::DrawTextFormatted(Context, FText::FromString(Letters[Tick / 6]), At, Font, bNorth ? 15 : 12,
				NAME_None, bNorth ? Rose : Pearl);
		}
	}

	// Markers.
	for (const FTrackedMarker& Entry : Tracked)
	{
		if (!Entry.Actor.IsValid())
		{
			continue;
		}
		FVector2D P = Entry.Offset / RangeCm * Radius * 0.9f;
		const bool bClamped = P.Size() > Radius * 0.9f;
		if (bClamped)
		{
			P = P.GetSafeNormal() * Radius * 0.9f;
		}
		const float S = bClamped ? 3.5f : 5.5f;
		const FVector2D M = Center + P;
		TArray<FVector2D> Diamond = {M + FVector2D(0, -S), M + FVector2D(S, 0), M + FVector2D(0, S), M + FVector2D(-S, 0), M + FVector2D(0, -S)};
		UWidgetBlueprintLibrary::DrawLines(Context, Diamond, MarkerColor(Entry.Type), true, bClamped ? 1.2f : 2.4f);
	}

	// Player: a sparkle-arrow pointing to camera forward (always up).
	TArray<FVector2D> Arrow = {Center + FVector2D(0, -9), Center + FVector2D(6, 7), Center + FVector2D(0, 3), Center + FVector2D(-6, 7), Center + FVector2D(0, -9)};
	UWidgetBlueprintLibrary::DrawLines(Context, Arrow, Pearl, true, 2.0f);
	return Context.MaxLayer;
}
