#include "MelodiaCosmicOrreryWidget.h"

#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Input/Events.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaCompendiumWidget.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaPersonaSubsystem.h"

UMelodiaCosmicOrreryWidget::UMelodiaCosmicOrreryWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	OrbitRadiusX = 260.0f;
	OrbitRadiusY = 110.0f;
	RingRotationSpeed = 8.0f;
}

void UMelodiaCosmicOrreryWidget::NativeConstruct()
{
	Super::NativeConstruct();

	SetIsFocusable(true);
	SetKeyboardFocus();

	if (!OwnContextHandle.IsValid())
	{
		if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
		{
			if (InputSubsystem->GetActiveContext() != EMelodiaInputContext::Menu)
			{
				OwnContextHandle = InputSubsystem->PushContext(EMelodiaInputContext::Menu, this);
			}
		}
	}

	Planets.Reset();
	if (Planet_1) { Planets.Add(Planet_1); }
	if (Planet_2) { Planets.Add(Planet_2); }
	if (Planet_3) { Planets.Add(Planet_3); }
	if (Planet_4) { Planets.Add(Planet_4); }
	if (Planet_5) { Planets.Add(Planet_5); }
	if (Planet_6) { Planets.Add(Planet_6); }
	if (Planet_7) { Planets.Add(Planet_7); }
	if (Planets.IsEmpty() && Planet_0) { Planets.Add(Planet_0); }

	MenuItems.Reset();
	if (MenuItem_1) { MenuItems.Add(MenuItem_1); }
	if (MenuItem_2) { MenuItems.Add(MenuItem_2); }
	if (MenuItem_3) { MenuItems.Add(MenuItem_3); }
	if (MenuItem_4) { MenuItems.Add(MenuItem_4); }
	if (MenuItem_5) { MenuItems.Add(MenuItem_5); }
	if (MenuItem_6) { MenuItems.Add(MenuItem_6); }
	if (MenuItem_7) { MenuItems.Add(MenuItem_7); }
	if (MenuItems.IsEmpty() && MenuItem_0) { MenuItems.Add(MenuItem_0); }

	MenuTexts.Reset();
	if (MenuItem_1_Text) { MenuTexts.Add(MenuItem_1_Text); }
	if (MenuItem_2_Text) { MenuTexts.Add(MenuItem_2_Text); }
	if (MenuItem_3_Text) { MenuTexts.Add(MenuItem_3_Text); }
	if (MenuItem_4_Text) { MenuTexts.Add(MenuItem_4_Text); }
	if (MenuItem_5_Text) { MenuTexts.Add(MenuItem_5_Text); }
	if (MenuItem_6_Text) { MenuTexts.Add(MenuItem_6_Text); }
	if (MenuItem_7_Text) { MenuTexts.Add(MenuItem_7_Text); }
	if (MenuTexts.IsEmpty() && MenuText_0) { MenuTexts.Add(MenuText_0); }

	StardustWidgets.Reset();
	if (Stardust_1) { StardustWidgets.Add(Stardust_1); }
	if (Stardust_2) { StardustWidgets.Add(Stardust_2); }
	if (Stardust_3) { StardustWidgets.Add(Stardust_3); }
	if (Stardust_4) { StardustWidgets.Add(Stardust_4); }
	if (Stardust_5) { StardustWidgets.Add(Stardust_5); }
	if (Stardust_6) { StardustWidgets.Add(Stardust_6); }
	if (StardustWidgets.IsEmpty() && Stardust_0) { StardustWidgets.Add(Stardust_0); }

	// Setup render transform pivots for centered scaling and rotation
	if (Orrery_Rings_Img) { Orrery_Rings_Img->SetRenderTransformPivot(FVector2D(0.5f, 0.5f)); }
	if (Orrery_Hub_Img) { Orrery_Hub_Img->SetRenderTransformPivot(FVector2D(0.5f, 0.5f)); }
	if (Orrery_Glow_Img) { Orrery_Glow_Img->SetRenderTransformPivot(FVector2D(0.5f, 0.5f)); }

	for (UWidget* Widget : Planets)
	{
		if (Widget) { Widget->SetRenderTransformPivot(FVector2D(0.5f, 0.5f)); }
	}
	for (UWidget* Widget : MenuItems)
	{
		if (Widget) { Widget->SetRenderTransformPivot(FVector2D(0.5f, 0.5f)); }
	}

	// Dynamic click delegate bindings for buttons if instantiated as UButton
	if (UButton* Btn = Cast<UButton>(Planet_1)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet1Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_2)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet2Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_3)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet3Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_4)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet4Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_5)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet5Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_6)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet6Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_7)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet7Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_0)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet0Clicked); }

	if (UButton* Btn = Cast<UButton>(MenuItem_1)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem1Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_2)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem2Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_3)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem3Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_4)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem4Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_5)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem5Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_6)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem6Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_7)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem7Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_0)) { Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem0Clicked); }

	if (UButton* Btn = Cast<UButton>(Close_Button))
	{
		Btn->OnClicked.AddDynamic(this, &UMelodiaCosmicOrreryWidget::HandleCloseButtonClicked);
	}

	// Canonical Storybook key prompt glyphs
	if (Key_Orbit)
	{
		Key_Orbit->SetText(FText::FromString(TEXT("[ \u2190 ] [ \u2192 ] Orbit")));
	}
	if (Key_Select)
	{
		Key_Select->SetText(FText::FromString(TEXT("[ Enter ] Select")));
	}
	if (Key_Close)
	{
		Key_Close->SetText(FText::FromString(TEXT("[ Esc ] Close")));
	}
	if (BottomLegendText)
	{
		BottomLegendText->SetText(FText::FromString(TEXT("[ \u2190 / \u2192 ] Orbit   [ \u2191 / \u2193 ] Archetype   [ Enter ] Select   [ Esc ] Close")));
	}
	if (BottomCurrencyText)
	{
		BottomCurrencyText->SetText(FText::FromString(TEXT("\u2726 1,420 Starlight Shards   \u00B7   6 Harmonic Prisms")));
	}

	InitArchetypesIfEmpty();
	RefreshActivePresentation();
}

void UMelodiaCosmicOrreryWidget::NativeDestruct()
{
	if (UButton* Btn = Cast<UButton>(Planet_1)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet1Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_2)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet2Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_3)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet3Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_4)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet4Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_5)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet5Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_6)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet6Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_7)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet7Clicked); }
	if (UButton* Btn = Cast<UButton>(Planet_0)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandlePlanet0Clicked); }

	if (UButton* Btn = Cast<UButton>(MenuItem_1)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem1Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_2)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem2Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_3)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem3Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_4)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem4Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_5)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem5Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_6)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem6Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_7)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem7Clicked); }
	if (UButton* Btn = Cast<UButton>(MenuItem_0)) { Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleMenuItem0Clicked); }

	if (UButton* Btn = Cast<UButton>(Close_Button))
	{
		Btn->OnClicked.RemoveDynamic(this, &UMelodiaCosmicOrreryWidget::HandleCloseButtonClicked);
	}

	if (OwnContextHandle.IsValid())
	{
		if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
		{
			InputSubsystem->PopContext(OwnContextHandle);
		}
		OwnContextHandle = FMelodiaInputContextHandle();
	}

	Super::NativeDestruct();
}

void UMelodiaCosmicOrreryWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	RunningTime += InDeltaTime;

	UpdateOrbitSimulation(InDeltaTime);
	UpdateStardustDrift(InDeltaTime);

	// Ambient Music Clock pulse layer on central orrery hub
	const float MusicPulse = UMelodiaMusicClockSubsystem::GetMusicPulse(this);
	if (Orrery_Glow_Img)
	{
		const float GlowAlpha = 0.55f + 0.35f * MusicPulse + 0.10f * FMath::Sin(RunningTime * 1.8f);
		Orrery_Glow_Img->SetRenderOpacity(FMath::Clamp(GlowAlpha, 0.0f, 1.0f));
	}
	if (Orrery_Hub_Img)
	{
		const float HubScale = 1.0f + 0.035f * MusicPulse;
		Orrery_Hub_Img->SetRenderScale(FVector2D(HubScale, HubScale));
	}
}

void UMelodiaCosmicOrreryWidget::UpdateOrbitSimulation(float InDeltaTime)
{
	// 1. Continuous rotation on astronomical astrolabe rings
	RingsContinuousAngle += RingRotationSpeed * InDeltaTime;
	if (RingsContinuousAngle >= 360.0f)
	{
		RingsContinuousAngle -= 360.0f;
	}
	if (Orrery_Rings_Img)
	{
		Orrery_Rings_Img->SetRenderTransformAngle(RingsContinuousAngle);
	}

	// 2. Smooth physical interpolation toward target planetary orbital angle
	CurrentOrbitAngle = FMath::FInterpTo(CurrentOrbitAngle, TargetOrbitAngle, InDeltaTime, 10.0f);

	// 3. Elliptical trigonometric orbit positions and depth scaling
	const int32 NumPlanets = Planets.Num();
	if (NumPlanets > 0)
	{
		const float Step = (2.0f * PI) / static_cast<float>(NumPlanets);
		for (int32 i = 0; i < NumPlanets; ++i)
		{
			UWidget* Planet = Planets[i];
			if (!Planet)
			{
				continue;
			}

			// Focused planet rests at bottom center (Angle = PI/2)
			const float Angle = CurrentOrbitAngle + (static_cast<float>(i) * Step);
			const float X = OrbitRadiusX * FMath::Cos(Angle);
			const float Y = OrbitRadiusY * FMath::Sin(Angle);
			Planet->SetRenderTranslation(FVector2D(X, Y));

			// Depth calculation: Sin(Angle) > 0 is front / foreground, < 0 is back
			const float DepthFactor = (FMath::Sin(Angle) + 1.0f) * 0.5f; // [0..1]
			float Scale = FMath::Lerp(0.80f, 1.15f, DepthFactor);
			float Opacity = FMath::Lerp(0.55f, 1.0f, DepthFactor);

			if (i == FocusedIndex)
			{
				Scale *= 1.10f;
				Opacity = 1.0f;
				const float MusicPulse = UMelodiaMusicClockSubsystem::GetMusicPulse(this);
				Scale += MusicPulse * 0.06f;
			}

			Planet->SetRenderScale(FVector2D(Scale, Scale));
			Planet->SetRenderOpacity(Opacity);
		}
	}
}

void UMelodiaCosmicOrreryWidget::UpdateStardustDrift(float InDeltaTime)
{
	const int32 Count = StardustWidgets.Num();
	for (int32 k = 0; k < Count; ++k)
	{
		UWidget* Dust = StardustWidgets[k];
		if (!Dust)
		{
			continue;
		}

		const float DriftX = FMath::Sin(RunningTime * (0.6f + k * 0.15f)) * (12.0f + k * 2.0f);
		const float DriftY = FMath::Cos(RunningTime * (0.5f + k * 0.18f)) * (10.0f + k * 1.5f);
		Dust->SetRenderTranslation(FVector2D(DriftX, DriftY));

		const float Twinkle = 0.40f + 0.40f * FMath::Sin(RunningTime * 2.0f + k * 1.1f);
		Dust->SetRenderOpacity(FMath::Clamp(Twinkle, 0.15f, 0.95f));
	}
}

FReply UMelodiaCosmicOrreryWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();

	if (Key == EKeys::Left || Key == EKeys::A || Key == EKeys::Gamepad_DPad_Left)
	{
		SelectPreviousArchetype();
		return FReply::Handled();
	}
	if (Key == EKeys::Right || Key == EKeys::D || Key == EKeys::Gamepad_DPad_Right)
	{
		SelectNextArchetype();
		return FReply::Handled();
	}
	if (Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up)
	{
		SelectPreviousArchetype();
		return FReply::Handled();
	}
	if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down)
	{
		SelectNextArchetype();
		return FReply::Handled();
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		ActivateCurrentArchetype();
		return FReply::Handled();
	}
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right || Key == EKeys::Gamepad_Special_Right)
	{
		CloseOrrery();
		return FReply::Handled();
	}

	// Number hotkeys 1..7 for immediate archetype selection
	if (Key == EKeys::One) { SetFocusedArchetypeIndex(0); return FReply::Handled(); }
	if (Key == EKeys::Two) { SetFocusedArchetypeIndex(1); return FReply::Handled(); }
	if (Key == EKeys::Three) { SetFocusedArchetypeIndex(2); return FReply::Handled(); }
	if (Key == EKeys::Four) { SetFocusedArchetypeIndex(3); return FReply::Handled(); }
	if (Key == EKeys::Five) { SetFocusedArchetypeIndex(4); return FReply::Handled(); }
	if (Key == EKeys::Six) { SetFocusedArchetypeIndex(5); return FReply::Handled(); }
	if (Key == EKeys::Seven) { SetFocusedArchetypeIndex(6); return FReply::Handled(); }

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply UMelodiaCosmicOrreryWidget::NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right)
	{
		CloseOrrery();
		return FReply::Handled();
	}
	return Super::NativeOnPreviewKeyDown(InGeometry, InKeyEvent);
}

FReply UMelodiaCosmicOrreryWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		const FVector2D LocalPos = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());

		// Check if click was over any Menu Item
		for (int32 i = 0; i < MenuItems.Num(); ++i)
		{
			if (UWidget* Item = MenuItems[i])
			{
				const FGeometry& ItemGeo = Item->GetCachedGeometry();
				if (ItemGeo.GetLocalSize().X > 0.0f)
				{
					const FVector2D ItemPos = ItemGeo.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
					if (ItemPos.X >= 0.0f && ItemPos.X <= ItemGeo.GetLocalSize().X &&
						ItemPos.Y >= 0.0f && ItemPos.Y <= ItemGeo.GetLocalSize().Y)
					{
						SetFocusedArchetypeIndex(i);
						ActivateCurrentArchetype();
						return FReply::Handled();
					}
				}
			}
		}

		// Check if click was over any Planet
		for (int32 i = 0; i < Planets.Num(); ++i)
		{
			if (UWidget* Planet = Planets[i])
			{
				const FGeometry& PlanetGeo = Planet->GetCachedGeometry();
				if (PlanetGeo.GetLocalSize().X > 0.0f)
				{
					const FVector2D PPos = PlanetGeo.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
					if (PPos.X >= 0.0f && PPos.X <= PlanetGeo.GetLocalSize().X &&
						PPos.Y >= 0.0f && PPos.Y <= PlanetGeo.GetLocalSize().Y)
					{
						SetFocusedArchetypeIndex(i);
						ActivateCurrentArchetype();
						return FReply::Handled();
					}
				}
			}
		}
	}

	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UMelodiaCosmicOrreryWidget::SelectPreviousArchetype()
{
	const int32 Count = Archetypes.Num();
	if (Count <= 0)
	{
		return;
	}

	const int32 NewIndex = (FocusedIndex - 1 + Count) % Count;
	SetFocusedArchetypeIndex(NewIndex);
}

void UMelodiaCosmicOrreryWidget::SelectNextArchetype()
{
	const int32 Count = Archetypes.Num();
	if (Count <= 0)
	{
		return;
	}

	const int32 NewIndex = (FocusedIndex + 1) % Count;
	SetFocusedArchetypeIndex(NewIndex);
}

void UMelodiaCosmicOrreryWidget::SetFocusedArchetypeIndex(int32 NewIndex)
{
	const int32 Count = Archetypes.Num();
	if (Count <= 0)
	{
		return;
	}

	const int32 ClampedIndex = FMath::Clamp(NewIndex, 0, Count - 1);
	if (ClampedIndex == FocusedIndex && TargetOrbitAngle != 0.0f)
	{
		return;
	}

	FocusedIndex = ClampedIndex;

	// Orbit step aligns focused node to bottom center (PI / 2)
	const float Step = (2.0f * PI) / static_cast<float>(Count);
	TargetOrbitAngle = (PI * 0.5f) - (static_cast<float>(FocusedIndex) * Step);

	if (OrbitSound)
	{
		UGameplayStatics::PlaySound2D(this, OrbitSound);
	}

	RefreshActivePresentation();
}

void UMelodiaCosmicOrreryWidget::ActivateCurrentArchetype()
{
	if (!Archetypes.IsValidIndex(FocusedIndex))
	{
		return;
	}

	const FMelodiaOrreryArchetype& Active = Archetypes[FocusedIndex];

	if (SelectSound)
	{
		UGameplayStatics::PlaySound2D(this, SelectSound);
	}

	OnArchetypeSelected.Broadcast(FocusedIndex, Active.ArchetypeId);

	// Context specific routing
	if (Active.ArchetypeId == FName(TEXT("Journal")) || Active.ArchetypeId == FName(TEXT("Archive")))
	{
		UMelodiaCompendiumWidget::Open(this);
	}
}

void UMelodiaCosmicOrreryWidget::CloseOrrery()
{
	if (CloseSound)
	{
		UGameplayStatics::PlaySound2D(this, CloseSound);
	}

	OnOrreryClosed.Broadcast();

	if (OwnContextHandle.IsValid())
	{
		if (UMelodiaInputContextSubsystem* InputSubsystem = UMelodiaInputContextSubsystem::Get(this))
		{
			InputSubsystem->PopContext(OwnContextHandle);
		}
		OwnContextHandle = FMelodiaInputContextHandle();
	}

	RemoveFromParent();
}

const FMelodiaOrreryArchetype& UMelodiaCosmicOrreryWidget::GetArchetype(int32 Index) const
{
	check(Archetypes.IsValidIndex(Index));
	return Archetypes[Index];
}

void UMelodiaCosmicOrreryWidget::InitArchetypesIfEmpty()
{
	if (!Archetypes.IsEmpty())
	{
		return;
	}

	Archetypes.Reset();

	// 1. Melusina & Party
	FMelodiaOrreryArchetype Party;
	Party.ArchetypeId = FName(TEXT("Party"));
	Party.Title = FText::FromString(TEXT("\u2726 MELUSINA & COMPANIONS"));
	Party.Subtitle = FText::FromString(TEXT("RESONANCE HARMONY \u00B7 CHAPTER IV"));
	Party.Description = FText::FromString(TEXT("Align the starlight bonds of your travel party. Synchronized tempo increases radiant melody resonance during rhythmic cantrips."));
	Party.MetricLabel = FText::FromString(TEXT("PARTY RESONANCE"));
	Party.MetricValue = 1.0f;
	Party.AccentColor = FLinearColor(0.98f, 0.85f, 0.65f, 1.0f);
	Archetypes.Add(Party);

	// 2. Sacred Instruments
	FMelodiaOrreryArchetype Instruments;
	Instruments.ArchetypeId = FName(TEXT("Instruments"));
	Instruments.Title = FText::FromString(TEXT("\u2726 SACRED INSTRUMENTS"));
	Instruments.Subtitle = FText::FromString(TEXT("CELESTIAL HARP & HARMONIC LYRE"));
	Instruments.Description = FText::FromString(TEXT("Attune handcrafted melodic instruments to ancient leylines. Pure Pythagorean 432 Hz frequencies unseal forgotten astral paths."));
	Instruments.MetricLabel = FText::FromString(TEXT("TUNING ACCURACY"));
	Instruments.MetricValue = 0.94f;
	Instruments.AccentColor = FLinearColor(0.85f, 0.75f, 1.0f, 1.0f);
	Archetypes.Add(Instruments);

	// 3. Stellar Cantrips & Skills
	FMelodiaOrreryArchetype Skills;
	Skills.ArchetypeId = FName(TEXT("Skills"));
	Skills.Title = FText::FromString(TEXT("\u2726 STELLAR CANTRIPS"));
	Skills.Subtitle = FText::FromString(TEXT("RHYTHM HIGHWAY \u00B7 4-LANE STRIKE"));
	Skills.Description = FText::FromString(TEXT("Master precision timing windows across Q/W/O/P chords. Perfect rhythm ratings multiply battle damage through singular harmony."));
	Skills.MetricLabel = FText::FromString(TEXT("CANTRIP MASTERY"));
	Skills.MetricValue = 0.88f;
	Skills.AccentColor = FLinearColor(0.65f, 0.90f, 1.0f, 1.0f);
	Archetypes.Add(Skills);

	// 4. Storybook Chronicle & Journal
	FMelodiaOrreryArchetype Journal;
	Journal.ArchetypeId = FName(TEXT("Journal"));
	Journal.Title = FText::FromString(TEXT("\u2726 STORYBOOK CHRONICLE"));
	Journal.Subtitle = FText::FromString(TEXT("TALES OF THE VEILED SHORE"));
	Journal.Description = FText::FromString(TEXT("The handwritten leaves of your personal fairy-tale journal. Chronicles active objectives, constellation echoes, and spoken memories."));
	Journal.MetricLabel = FText::FromString(TEXT("CHRONICLE PROGRESS"));
	Journal.MetricValue = 0.65f;
	Journal.AccentColor = FLinearColor(1.0f, 0.78f, 0.82f, 1.0f);
	Archetypes.Add(Journal);

	// 5. Astral Cartography / World Map
	FMelodiaOrreryArchetype Map;
	Map.ArchetypeId = FName(TEXT("Map"));
	Map.Title = FText::FromString(TEXT("\u2726 ASTRAL CARTOGRAPHY"));
	Map.Subtitle = FText::FromString(TEXT("MELUSINA LAKE & SHORELINE"));
	Map.Description = FText::FromString(TEXT("Chart the celestial coordinates of shrines and singing bells. Resonant leylines guide the traveler through foggy mornings."));
	Map.MetricLabel = FText::FromString(TEXT("SHRINES AWAKENED"));
	Map.MetricValue = 0.70f;
	Map.AccentColor = FLinearColor(0.70f, 0.95f, 0.80f, 1.0f);
	Archetypes.Add(Map);

	// 6. Celestial Archive & Bestiary
	FMelodiaOrreryArchetype Archive;
	Archive.ArchetypeId = FName(TEXT("Archive"));
	Archive.Title = FText::FromString(TEXT("\u2726 CELESTIAL ARCHIVE"));
	Archive.Subtitle = FText::FromString(TEXT("LULLABIES & ENCOUNTER FOLIO"));
	Archive.Description = FText::FromString(TEXT("A compendium of mythical beasts, restored ancient hymns, and starry fragments gathered across your journey."));
	Archive.MetricLabel = FText::FromString(TEXT("ARCHIVE COMPLETION"));
	Archive.MetricValue = 0.82f;
	Archive.AccentColor = FLinearColor(0.92f, 0.80f, 0.60f, 1.0f);
	Archetypes.Add(Archive);

	// 7. Astrolabe Calibration & Settings
	FMelodiaOrreryArchetype Settings;
	Settings.ArchetypeId = FName(TEXT("Settings"));
	Settings.Title = FText::FromString(TEXT("\u2726 ASTROLABE CALIBRATION"));
	Settings.Subtitle = FText::FromString(TEXT("TEMPO SYNC & SLATE PREFERENCES"));
	Settings.Description = FText::FromString(TEXT("Calibrate rhythm audio latency, visual fidelity, control mappings, and fairy-tale UI styling for optimal resonance."));
	Settings.MetricLabel = FText::FromString(TEXT("CALIBRATION LATENCY"));
	Settings.MetricValue = 1.0f;
	Settings.AccentColor = FLinearColor(0.80f, 0.85f, 0.90f, 1.0f);
	Archetypes.Add(Settings);
}

void UMelodiaCosmicOrreryWidget::RefreshActivePresentation()
{
	if (!Archetypes.IsValidIndex(FocusedIndex))
	{
		return;
	}

	const FMelodiaOrreryArchetype& Active = Archetypes[FocusedIndex];

	// Detail / Storybook Context Presentation
	UTextBlock* TitleWidget = Detail_Title ? Detail_Title.Get() : ContextTitle.Get();
	if (TitleWidget)
	{
		TitleWidget->SetText(Active.Title);
	}

	UTextBlock* SubtitleWidget = Detail_Subtitle ? Detail_Subtitle.Get() : ContextCategory.Get();
	if (SubtitleWidget)
	{
		SubtitleWidget->SetText(Active.Subtitle);
	}

	UTextBlock* DescWidget = Detail_Description ? Detail_Description.Get() : ContextDesc.Get();
	if (DescWidget)
	{
		DescWidget->SetText(Active.Description);
	}

	if (Detail_MetricLabel)
	{
		Detail_MetricLabel->SetText(Active.MetricLabel);
	}
	if (Detail_MetricValue)
	{
		Detail_MetricValue->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(Active.MetricValue * 100.0f))));
	}
	if (Detail_MetricBar)
	{
		Detail_MetricBar->SetPercent(Active.MetricValue);
		Detail_MetricBar->SetFillColorAndOpacity(Active.AccentColor);
	}

	// Dynamic contextual stats
	if (ContextStats)
	{
		FString StatString;
		if (Active.ArchetypeId == FName(TEXT("Party")))
		{
			StatString = TEXT("Harmonic Resonance: 100%   \u00B7   Starlight Bond: Max   \u00B7   Melusina (Conductor)");
		}
		else if (Active.ArchetypeId == FName(TEXT("Instruments")))
		{
			StatString = TEXT("Active: Celestial Lyre   \u00B7   Pitch: 432 Hz   \u00B7   Tuning: Pure Pythagorean");
		}
		else if (Active.ArchetypeId == FName(TEXT("Skills")))
		{
			StatString = TEXT("Unlocked Cantrips: 12   \u00B7   Highway: 4 Lanes (Q/W/O/P)   \u00B7   BPM Sync: Active");
		}
		else if (Active.ArchetypeId == FName(TEXT("Journal")))
		{
			if (const UMelodiaPersonaSubsystem* Persona = UMelodiaPersonaSubsystem::Get(this))
			{
				const TArray<FMelodiaQuestDefinition> Quests = Persona->GetAvailableQuests();
				StatString = FString::Printf(TEXT("Chronicle: Chapter IV   \u00B7   Active Quests: %d   \u00B7   Constellation Echoes: 8"), Quests.Num());
			}
			else
			{
				StatString = TEXT("Chronicle: Chapter IV   \u00B7   Quests: A Song Left Unfinished   \u00B7   Progress: 65%");
			}
		}
		else if (Active.ArchetypeId == FName(TEXT("Map")))
		{
			StatString = TEXT("Active Region: Melusina Lake   \u00B7   Resonance Shrines: 4/6   \u00B7   Leyline Flow: Calm");
		}
		else if (Active.ArchetypeId == FName(TEXT("Archive")))
		{
			StatString = TEXT("Harmonic Echoes: 24   \u00B7   Bestiary Folio: 18   \u00B7   Lullabies Transcribed: 7");
		}
		else
		{
			StatString = TEXT("Master Volume: 100%   \u00B7   Music Volume: 90%   \u00B7   Latency Calibration: 0 ms");
		}
		ContextStats->SetText(FText::FromString(StatString));
	}

	// Persona presentation
	if (PersonaName)
	{
		PersonaName->SetText(FText::FromString(TEXT("Melusina")));
	}
	if (PersonaBadgeText)
	{
		PersonaBadgeText->SetText(FText::FromString(TEXT("\u2726 SONG CONDUCTOR \u2726")));
	}

	// Update Menu list items styling and text
	const int32 MenuCount = MenuItems.Num();
	for (int32 i = 0; i < MenuCount; ++i)
	{
		UWidget* Item = MenuItems[i];
		if (!Item)
		{
			continue;
		}

		const bool bIsFocused = (i == FocusedIndex);
		Item->SetRenderScale(bIsFocused ? FVector2D(1.04f, 1.04f) : FVector2D(1.0f, 1.0f));
		Item->SetRenderOpacity(bIsFocused ? 1.0f : 0.55f);

		if (MenuTexts.IsValidIndex(i) && MenuTexts[i])
		{
			if (Archetypes.IsValidIndex(i))
			{
				MenuTexts[i]->SetText(Archetypes[i].Title);
			}
			MenuTexts[i]->SetColorAndOpacity(bIsFocused ?
				FSlateColor(FLinearColor(1.0f, 0.94f, 0.70f, 1.0f)) :
				FSlateColor(FLinearColor(0.85f, 0.82f, 0.78f, 0.75f)));
		}
	}
}

void UMelodiaCosmicOrreryWidget::HandlePlanet1Clicked() { SetFocusedArchetypeIndex(0); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet2Clicked() { SetFocusedArchetypeIndex(1); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet3Clicked() { SetFocusedArchetypeIndex(2); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet4Clicked() { SetFocusedArchetypeIndex(3); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet5Clicked() { SetFocusedArchetypeIndex(4); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet6Clicked() { SetFocusedArchetypeIndex(5); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet7Clicked() { SetFocusedArchetypeIndex(6); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandlePlanet0Clicked() { SetFocusedArchetypeIndex(0); ActivateCurrentArchetype(); }

void UMelodiaCosmicOrreryWidget::HandleMenuItem1Clicked() { SetFocusedArchetypeIndex(0); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem2Clicked() { SetFocusedArchetypeIndex(1); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem3Clicked() { SetFocusedArchetypeIndex(2); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem4Clicked() { SetFocusedArchetypeIndex(3); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem5Clicked() { SetFocusedArchetypeIndex(4); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem6Clicked() { SetFocusedArchetypeIndex(5); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem7Clicked() { SetFocusedArchetypeIndex(6); ActivateCurrentArchetype(); }
void UMelodiaCosmicOrreryWidget::HandleMenuItem0Clicked() { SetFocusedArchetypeIndex(0); ActivateCurrentArchetype(); }

void UMelodiaCosmicOrreryWidget::HandleCloseButtonClicked()
{
	CloseOrrery();
}
