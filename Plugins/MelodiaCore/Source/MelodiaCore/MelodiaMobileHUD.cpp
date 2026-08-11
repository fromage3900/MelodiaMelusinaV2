// Mobile HUD ΓÇö portrait primary (see Docs/MELODIA_IOS_MOBILE_GAME_UI.md)

#include "MelodiaMobileHUD.h"
#include "MelodiaBattleInputComponent.h"
#include "Components/CanvasPanel.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"

void UMelodiaMobileHUD::NativeConstruct()
{
	Super::NativeConstruct();
	SetupTouchZones();
	InitializeMobileHUD();
}

void UMelodiaMobileHUD::NativeDestruct()
{
	if (LaneButtons.Num() == 4)
	{
		if (LaneButtons[0])
		{
			LaneButtons[0]->OnClicked.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane0Clicked);
			LaneButtons[0]->OnPressed.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane0Pressed);
			LaneButtons[0]->OnReleased.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane0Released);
		}
		if (LaneButtons[1])
		{
			LaneButtons[1]->OnClicked.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane1Clicked);
			LaneButtons[1]->OnPressed.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane1Pressed);
			LaneButtons[1]->OnReleased.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane1Released);
		}
		if (LaneButtons[2])
		{
			LaneButtons[2]->OnClicked.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane2Clicked);
			LaneButtons[2]->OnPressed.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane2Pressed);
			LaneButtons[2]->OnReleased.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane2Released);
		}
		if (LaneButtons[3])
		{
			LaneButtons[3]->OnClicked.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane3Clicked);
			LaneButtons[3]->OnPressed.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane3Pressed);
			LaneButtons[3]->OnReleased.RemoveDynamic(this, &UMelodiaMobileHUD::OnLane3Released);
		}
	}

	Super::NativeDestruct();
}

void UMelodiaMobileHUD::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
}

UMelodiaBattleInputComponent* UMelodiaMobileHUD::FindBattleInput() const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	APlayerController* PC = World->GetFirstPlayerController();
	if (!PC || !PC->GetPawn())
	{
		return nullptr;
	}
	return PC->GetPawn()->FindComponentByClass<UMelodiaBattleInputComponent>();
}

void UMelodiaMobileHUD::ForwardLaneTap(int32 LaneIndex)
{
	if (UMelodiaBattleInputComponent* InputComp = FindBattleInput())
	{
		InputComp->HandleLaneTap(LaneIndex);
	}
	else
	{
		UE_LOG(LogTemp, Verbose, TEXT("MelodiaMobileHUD: Lane %d tap ΓÇö no MelodiaBattleInputComponent on pawn"), LaneIndex);
	}
}

void UMelodiaMobileHUD::SetupTouchZones()
{
	if (LaneButtons.Num() != 4)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaMobileHUD: Expected 4 lane buttons, found %d (assign in WBP_Battle_Mobile)"), LaneButtons.Num());
		return;
	}

	// AddUniqueDynamic requires UFUNCTION ΓÇö no lambdas.
	if (LaneButtons[0])
	{
		LaneButtons[0]->OnClicked.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane0Clicked);
		LaneButtons[0]->OnPressed.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane0Pressed);
		LaneButtons[0]->OnReleased.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane0Released);
	}
	if (LaneButtons[1])
	{
		LaneButtons[1]->OnClicked.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane1Clicked);
		LaneButtons[1]->OnPressed.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane1Pressed);
		LaneButtons[1]->OnReleased.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane1Released);
	}
	if (LaneButtons[2])
	{
		LaneButtons[2]->OnClicked.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane2Clicked);
		LaneButtons[2]->OnPressed.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane2Pressed);
		LaneButtons[2]->OnReleased.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane2Released);
	}
	if (LaneButtons[3])
	{
		LaneButtons[3]->OnClicked.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane3Clicked);
		LaneButtons[3]->OnPressed.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane3Pressed);
		LaneButtons[3]->OnReleased.AddUniqueDynamic(this, &UMelodiaMobileHUD::OnLane3Released);
	}
}

void UMelodiaMobileHUD::OnLane0Clicked() { ForwardLaneTap(0); }
void UMelodiaMobileHUD::OnLane1Clicked() { ForwardLaneTap(1); }
void UMelodiaMobileHUD::OnLane2Clicked() { ForwardLaneTap(2); }
void UMelodiaMobileHUD::OnLane3Clicked() { ForwardLaneTap(3); }

void UMelodiaMobileHUD::OnLane0Pressed() { SetLaneHighlight(0, true); }
void UMelodiaMobileHUD::OnLane1Pressed() { SetLaneHighlight(1, true); }
void UMelodiaMobileHUD::OnLane2Pressed() { SetLaneHighlight(2, true); }
void UMelodiaMobileHUD::OnLane3Pressed() { SetLaneHighlight(3, true); }

void UMelodiaMobileHUD::OnLane0Released() { SetLaneHighlight(0, false); }
void UMelodiaMobileHUD::OnLane1Released() { SetLaneHighlight(1, false); }
void UMelodiaMobileHUD::OnLane2Released() { SetLaneHighlight(2, false); }
void UMelodiaMobileHUD::OnLane3Released() { SetLaneHighlight(3, false); }

void UMelodiaMobileHUD::InitializeMobileHUD()
{
	if (ComboText) ComboText->SetText(FText::GetEmpty());
	if (HPBar) HPBar->SetPercent(1.0f);
	if (SPBar) SPBar->SetPercent(1.0f);
	if (UltBar) UltBar->SetPercent(0.0f);
	if (EnemyHPBar) EnemyHPBar->SetPercent(1.0f);
	if (EnemyToughnessBar) EnemyToughnessBar->SetPercent(1.0f);
	if (GradePopupCanvas) GradePopupCanvas->SetVisibility(ESlateVisibility::Hidden);
}

void UMelodiaMobileHUD::SetLaneHighlight(int32 LaneIndex, bool bHighlight)
{
	if (LaneIndex < 0 || LaneIndex >= LaneButtons.Num()) return;

	if (UButton* Button = LaneButtons[LaneIndex])
	{
		Button->SetRenderOpacity(bHighlight ? 0.7f : 1.0f);
	}
}

void UMelodiaMobileHUD::ShowGradePopup(EMelodiaRhythmGrade Grade, float Damage)
{
	if (!GradePopupCanvas || !GradeText) return;

	FString GradeStr;
	switch (Grade)
	{
	case EMelodiaRhythmGrade::Perfect: GradeStr = TEXT("PERFECT"); break;
	case EMelodiaRhythmGrade::Great: GradeStr = TEXT("GREAT"); break;
	case EMelodiaRhythmGrade::Good: GradeStr = TEXT("GOOD"); break;
	case EMelodiaRhythmGrade::Miss: GradeStr = TEXT("MISS"); break;
	default: GradeStr = TEXT("MISS"); break;
	}

	GradeText->SetText(FText::FromString(GradeStr));
	GradePopupCanvas->SetVisibility(ESlateVisibility::Visible);
	(void)Damage;
}

void UMelodiaMobileHUD::UpdateCombo(int32 ComboCount)
{
	if (!ComboText) return;

	if (ComboCount > 1)
	{
		ComboText->SetText(FText::FromString(FString::Printf(TEXT("%dx COMBO"), ComboCount)));
	}
	else
	{
		ComboText->SetText(FText::GetEmpty());
	}
}

void UMelodiaMobileHUD::UpdateResources(float HPPercent, float SPPercent, float UltPercent)
{
	if (HPBar) HPBar->SetPercent(FMath::Clamp(HPPercent, 0.0f, 1.0f));
	if (SPBar) SPBar->SetPercent(FMath::Clamp(SPPercent, 0.0f, 1.0f));
	if (UltBar) UltBar->SetPercent(FMath::Clamp(UltPercent, 0.0f, 1.0f));
}

FVector2D UMelodiaMobileHUD::CalculateLanePosition(int32 LaneIndex) const
{
	// Portrait: 4 vertical lanes evenly spaced across highway width (min ~44pt each).
	const float LaneWidth = PortraitHighwayWidth / 4.0f;
	const float StartX = -PortraitHighwayWidth / 2.0f + LaneWidth / 2.0f;
	const float Y = ThumbZoneTopRatio; // normalized hint for WBP layout
	return FVector2D(StartX + LaneIndex * LaneWidth, Y);
}
