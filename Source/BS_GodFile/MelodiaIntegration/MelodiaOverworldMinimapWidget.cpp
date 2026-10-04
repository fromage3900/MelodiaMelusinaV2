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
	// Prefixed because a unity build merges this file with MelodiaCalibrationWidget.cpp,
	// which declares its own MinimapPearl/MinimapRose/MinimapLavender/MinimapCyan/MinimapNight in the same anonymous
	// namespace: identical names in one blob are C2374/C2872 errors for the whole module.
	// A nested namespace plus `using namespace` does NOT fix it -- the unqualified name
	// then resolves ambiguously (C2872) instead. The values are deliberately per-file
	// (lavender and night carry different alphas here), so this is disambiguation, not a
	// shared palette.
	const FLinearColor MinimapPearl(0.96f, 0.93f, 0.90f, 1.0f);
	const FLinearColor MinimapRose(0.91f, 0.71f, 0.63f, 1.0f);
	const FLinearColor MinimapLavender(0.73f, 0.65f, 0.94f, 0.7f);
	const FLinearColor MinimapCyan(0.62f, 0.91f, 0.97f, 1.0f);
	const FLinearColor MinimapEmber(1.0f, 0.45f, 0.45f, 1.0f);
	const FLinearColor MinimapNight(0.043f, 0.035f, 0.125f, 0.72f);

	FLinearColor MarkerColor(const EMelodiaMinimapMarkerType Type)
	{
		switch (Type)
		{
		case EMelodiaMinimapMarkerType::NPC: return MinimapPearl;
		case EMelodiaMinimapMarkerType::Encounter: return MinimapEmber;
		case EMelodiaMinimapMarkerType::Exit: return MinimapCyan;
		case EMelodiaMinimapMarkerType::SavePoint: return MinimapLavender;
		default: return MinimapRose;
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

	// Idle motion: the dial breathes on a slow ~4 s cycle so the HUD never
	// sits fully static. Time-only, no new state, const-safe.
	const float IdleT = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	const float Breathe = 0.5f * (1.0f - FMath::Cos(IdleT * 1.5708f));
	const float RimPulse = 0.75f + 0.25f * Breathe;

	// Dial body: a soft disc approximated by a thick ring fill, then the orbit rings.
	for (float R = Radius * 0.1f; R < Radius; R += 6.0f)
	{
		UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, R), MinimapNight, true, 7.0f);
	}
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius), MinimapRose, true, (1.2f + 0.8f * Breathe) * RimPulse);
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius * 0.62f), MinimapLavender, true, 1.0f);
	UWidgetBlueprintLibrary::DrawLines(Context, Circle(Center, Radius * 0.3f), MinimapLavender, true, 0.8f);

	// Compass: ticks and cardinal letters rotate against the camera yaw.
	static const TCHAR* Letters[] = {TEXT("N"), TEXT("E"), TEXT("S"), TEXT("W")};
	for (int32 Tick = 0; Tick < 24; ++Tick)
	{
		const float WorldYaw = Tick * 15.0f;
		const float ScreenAngle = FMath::DegreesToRadians(WorldYaw - HeadingDegrees);
		const FVector2D Dir(FMath::Sin(ScreenAngle), -FMath::Cos(ScreenAngle));
		const float Inner = (Tick % 6 == 0) ? Radius * 0.9f : Radius * 0.95f;
		UWidgetBlueprintLibrary::DrawLine(Context, Center + Dir * Inner, Center + Dir * Radius, MinimapRose, true, 1.0f);
		if (Tick % 6 == 0 && Font)
		{
			const bool bNorth = Tick == 0;
			const FVector2D At = Center + Dir * (Radius * 0.78f) - FVector2D(5.0f, 9.0f);
			UWidgetBlueprintLibrary::DrawTextFormatted(Context, FText::FromString(Letters[Tick / 6]), At, Font, bNorth ? 15 : 12,
				NAME_None, bNorth ? MinimapRose : MinimapPearl);
		}
	}

	// Markers (pulse gently out of phase so the dial feels alive).
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
		const float Pulse = 0.8f + 0.35f * (0.5f * (1.0f - FMath::Cos(IdleT * 2.4f + P.X * 0.05f)));
		const float S = (bClamped ? 3.5f : 5.5f) * Pulse;
		const FVector2D M = Center + P;
		TArray<FVector2D> Diamond = {M + FVector2D(0, -S), M + FVector2D(S, 0), M + FVector2D(0, S), M + FVector2D(-S, 0), M + FVector2D(0, -S)};
		UWidgetBlueprintLibrary::DrawLines(Context, Diamond, MarkerColor(Entry.Type), true, bClamped ? 1.2f : 2.4f);
	}

	// Player: a sparkle-arrow pointing to camera forward (always up).
	TArray<FVector2D> Arrow = {Center + FVector2D(0, -9), Center + FVector2D(6, 7), Center + FVector2D(0, 3), Center + FVector2D(-6, 7), Center + FVector2D(0, -9)};
	UWidgetBlueprintLibrary::DrawLines(Context, Arrow, MinimapPearl, true, 2.0f);
	return Context.MaxLayer;
}
