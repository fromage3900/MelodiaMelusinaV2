#include "MelodiaWaveHarpHUDWidget.h"
#include "MelodiaWaveHarpCombatComponent.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaWorldSlimeNode.h"
#include "Engine/Font.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

void UMelodiaWaveHarpHUDWidget::NativeConstruct()
{
 Super::NativeConstruct();
 InterFont = LoadObject<UFont>(nullptr, TEXT("/Game/Melodia/UI/Fonts/InterTokens/F_Inter_Token.F_Inter_Token"));
}

int32 UMelodiaWaveHarpHUDWidget::NativePaint(const FPaintArgs& Args, const FGeometry& G,
 const FSlateRect& Cull, FSlateWindowElementList& E, int32 L, const FWidgetStyle& Style, bool Enabled) const
{
 L = Super::NativePaint(Args, G, Cull, E, L, Style, Enabled);
 const APawn* Pawn = GetOwningPlayer() ? GetOwningPlayer()->GetPawn() : nullptr;
 const auto* Combat = Pawn ? Pawn->FindComponentByClass<UMelodiaWaveHarpCombatComponent>() : nullptr;
 if (!Combat) return L;
 const FVector2D Size = G.GetLocalSize();
 const FSlateBrush Brush = *FCoreStyle::Get().GetBrush("WhiteBrush");
 // Current tokens.json primitives. The on-disk DA is a PrimaryDataAsset
 // placeholder, not a populated MelodiaDesignTokens asset; do not load/cast it.
 const FLinearColor Ivory = FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("FFF8EE")));
 const FLinearColor Gold = FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("DDC79B")));
 const FLinearColor Cyan = FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("8AA9D6")));
 FLinearColor Plate = FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("1C1426"))); Plate.A = .8f;
 const FSlateRoundedBoxBrush Rounded(FLinearColor::White, 10.f);
 const auto Box = [&](FVector2D P, FVector2D S, FLinearColor C) {
  FSlateDrawElement::MakeBox(E, L + 1, G.ToPaintGeometry(S, FSlateLayoutTransform(P)), &Brush, ESlateDrawEffect::None, C);
 };
 const auto Panel = [&](FVector2D P, FVector2D S) {
  FSlateDrawElement::MakeBox(E, L + 1, G.ToPaintGeometry(S, FSlateLayoutTransform(P)), &Rounded, ESlateDrawEffect::None, Plate);
 };
 const auto Text = [&](FVector2D P, const FString& T, int32 FontSize, FLinearColor C) {
  FSlateDrawElement::MakeText(E, L + 2, G.ToPaintGeometry(FVector2D(1,1), FSlateLayoutTransform(P)), T,
   InterFont ? FSlateFontInfo(InterFont, FontSize) : FCoreStyle::GetDefaultFontStyle("Regular", FontSize), ESlateDrawEffect::None, C);
 };
 const bool Sequence = Combat->IsInSequence();
 // Leave the stock minimap/quest column and bottom party/skill row clear.
 const FVector2D Card(FMath::Max(24.f, Size.X - 276.f), FMath::Max(240.f, Size.Y - 356.f));
 Panel(Card, {252,156});
 Text(Card + FVector2D(14,12), Sequence ? TEXT("RHYTHM PHRASE") : TEXT("WAVEHARP"), 14, Gold);
 if (Sequence)
 {
  Text(Card + FVector2D(14,42), TEXT("Q  W  O  P   Follow the hit line"), 11, Ivory);
  Text(Card + FVector2D(14,72), TEXT("TAB  Return after the phrase"), 11, Ivory);
  Text(Card + FVector2D(14,96), TEXT("X  Cancel"), 11, Ivory);
 }
 else
 {
  const float Chord = Combat->GetChordFeedback();
  Text(Card + FVector2D(14,37), Chord > 0 ? TEXT("C major 7  /  chord complete") : TEXT("C   E   G   B   C"), 12, Ivory);
  for (int32 Note = 0; Note < 5; ++Note)
   Box(Card + FVector2D(14 + Note*44,62), {34,4}, Chord > 0 || Note < Combat->ComboStep ? Gold : FLinearColor(.25f,.22f,.28f,.8f));
  Text(Card + FVector2D(14,82), TEXT("LMB  Draw / release"), 11, Ivory);
  Text(Card + FVector2D(14,104), TEXT("RMB  Aim    MMB  Toggle aim"), 11, Ivory);
  Text(Card + FVector2D(14,126), TEXT("TAB  Rhythm phrase on target"), 11, Gold);
 }
 if (const auto* Target = Combat->GetTarget())
 {
  const auto* Slime = Cast<AMelodiaWorldSlimeNode>(Target->GetOwner());
  if (Slime)
  {
   const FVector2D P(Size.X * .5 - 140, 112);
   Panel(P, {280,46});
   Text(P + FVector2D(12,7), FString::Printf(TEXT("ECHO     %.0f / %.0f"), Slime->CurrentHP, Slime->MaxHP), 12, Ivory);
   Box(P + FVector2D(12,33), {256,4}, FLinearColor(.06f,.06f,.08f,.9f));
   Box(P + FVector2D(12,33), {256 * (Slime->MaxHP > 0 ? FMath::Clamp(Slime->CurrentHP / Slime->MaxHP, 0.f, 1.f) : 0.f),4}, Gold);
  }
 }
 if (!Sequence && (Combat->IsAiming() || Combat->IsDrawing()))
 {
  const FVector2D C = Size * .5;
  Box(C + FVector2D(-11,-1), {5,2}, Gold); Box(C + FVector2D(6,-1), {5,2}, Gold);
  Box(C + FVector2D(-1,-11), {2,5}, Gold); Box(C + FVector2D(-1,6), {2,5}, Gold);
  if (Combat->IsDrawing())
  {
   Box(C + FVector2D(-38,26), {76,4}, Plate);
   Box(C + FVector2D(-38,26), {76 * Combat->GetDrawTension(),4}, Gold);
   Text(C + FVector2D(-22,38), Combat->GetDrawTension() >= 1.f ? TEXT("READY") : TEXT("DRAW"), 10, Ivory);
  }
 }
 const float Hit = Combat->GetHitFeedback();
 if (!Sequence && Hit > 0)
 {
  const FVector2D C = Size * .5;
  FLinearColor Feedback = Cyan; Feedback.A = Hit;
  TArray<FVector2D> Points;
  for (const FVector2D Sign : {FVector2D(-1,-1), FVector2D(1,-1), FVector2D(-1,1), FVector2D(1,1)})
  {
   Points = {C + Sign*13, C + Sign*19};
   FSlateDrawElement::MakeLines(E, L + 2, G.ToPaintGeometry(), Points, ESlateDrawEffect::None, Feedback, true, 1.5f);
  }
  Text(C + FVector2D(25,-24), FString::Printf(TEXT("-%.0f"), Combat->LastHitDamage), 13, Feedback);
 }
 return L + 3;
}
