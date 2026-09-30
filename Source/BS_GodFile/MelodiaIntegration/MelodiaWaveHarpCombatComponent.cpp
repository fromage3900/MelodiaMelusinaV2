#include "MelodiaWaveHarpCombatComponent.h"
#include "MelodiaWaveArrow.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaUIBridgeSubsystem.h"
#include "MelodiaWorldSlimeNode.h"
#include "Camera/CameraComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

UMelodiaWaveHarpCombatComponent::UMelodiaWaveHarpCombatComponent()
{
 PrimaryComponentTick.bCanEverTick = true;
 StatusText = TEXT("Aim at an encounter, or take a practice shot.");
}
void UMelodiaWaveHarpCombatComponent::BeginPlay()
{
 Super::BeginPlay();
 Character = Cast<ACharacter>(GetOwner());
 if (!Character.IsValid()) { SetComponentTickEnabled(false); return; }
 auto* Mesh = Character->GetMesh();
 if (Mesh && Mesh->DoesSocketExist(TEXT("hand_l")))
 {
  Bow = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("WaveHarpBowPresentation"));
  Bow->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Bow_R07.SM_ME_WaveHarp_Bow_R07")));
  Bow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Bow->SetupAttachment(Mesh, TEXT("hand_l"));
  Bow->SetRelativeScale3D(FVector(.9));
  Bow->RegisterComponent();
  Harp = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("WaveHarpHarpPresentation"));
  Harp->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Harp_R07.SM_ME_WaveHarp_Harp_R07")));
  Harp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Harp->SetupAttachment(Mesh, TEXT("hand_l"));
  Harp->SetRelativeScale3D(FVector(.9));
  Harp->RegisterComponent();
 }
 AttackMontage = LoadObject<UAnimMontage>(nullptr, TEXT("/Game/Melodia/Characters/Melusina/Animations/Polish_20260919/AM_Melusina_BowAttack_Gameplay.AM_Melusina_BowAttack_Gameplay"));
 DrawMontage = LoadObject<UAnimMontage>(nullptr, TEXT("/Game/Melodia/Characters/Melusina/Animations/AM_RangeAttack.AM_RangeAttack"));
 ShotNote = LoadObject<USoundBase>(nullptr, TEXT("/Game/Melodia/CombatTrial/Audio/SW_WaveHarpTrial_C4.SW_WaveHarpTrial_C4"));
 UpdateWeaponVisibility();
}
void UMelodiaWaveHarpCombatComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 CancelPhrase();
 StopAim();
 UnbindInput();
 if (Bow) Bow->DestroyComponent();
 if (Harp) Harp->DestroyComponent();
 if (auto* UI = UMelodiaUIBridgeSubsystem::Get(this)) UI->ReleaseWorldCombatUI();
 Super::EndPlay(Reason);
}
void UMelodiaWaveHarpCombatComponent::TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Tick)
{
 Super::TickComponent(Delta, Type, Tick);
 if (!Character.IsValid()) return;
 auto* Controller = Cast<APlayerController>(Character->GetController());
 if (!Character->IsLocallyControlled() || !Controller)
 {
  CancelPhrase(); StopAim(); UnbindInput(); Player.Reset(); return;
 }
 Player = Controller;
 BindInput();
 if (auto* Input = UMelodiaInputContextSubsystem::Get(this)) Input->SetActionPointerCapture(this, true);
 if (IsInSequence())
 {
  Target = PhraseTarget;
 }
 else
 {
  if (PhraseTarget.IsValid()) PhraseTarget.Reset();
  FindAimTarget();
 }
 UpdateInputOwnership();
 if (bAiming)
 {
  Character->SetActorRotation(FRotator(0, Controller->GetControlRotation().Yaw, 0));
 }
 if ((bAiming || bDrawing) && DrawMontage)
 {
  if (auto* Anim = Character->GetMesh()->GetAnimInstance())
  {
   // Use the existing bow montage through the canonical ABP slot. Keep the
   // release readable before returning to the held aim/draw pose.
   if (!AttackMontage || !Anim->Montage_IsPlaying(AttackMontage))
   {
    if (!Anim->Montage_IsActive(DrawMontage)) Anim->Montage_Play(DrawMontage);
    if (Anim->Montage_GetPosition(DrawMontage) >= .45f)
    {
     Anim->Montage_SetPosition(DrawMontage, .45f);
     Anim->Montage_Pause(DrawMontage);
    }
   }
  }
 }
 if (!CanAct() && !IsInSequence()) { bDrawing = false; StopAim(); }
 if (ComboStep > 0 && GetWorld()->GetTimeSeconds() - LastRelease > 1.25) ComboStep = 0;
 UpdateAimCamera(Delta);
 UpdateWeaponVisibility();
 if (auto* UI = UMelodiaUIBridgeSubsystem::Get(this)) UI->EnsureWorldCombatUI(Controller, IsInSequence());
}
void UMelodiaWaveHarpCombatComponent::BindInput()
{
 if (!Player.IsValid() || (BoundInput && BoundPlayer == Player)) return;
 UnbindInput();
 // Stock controller mouse bindings precede the pawn. Give this scoped action
 // surface its own stack entry while preserving the existing movement bindings.
 auto* Input = NewObject<UInputComponent>(this, TEXT("WaveHarpPlayerInput"));
 Input->Priority = 10;
 Input->bBlockInput = false;
 Input->RegisterComponent();
 BoundInput = Input;
 BoundPlayer = Player;
 Input->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &ThisClass::StartAim);
 Input->BindKey(EKeys::RightMouseButton, IE_Released, this, &ThisClass::StopAim);
 Input->BindKey(EKeys::MiddleMouseButton, IE_Pressed, this, &ThisClass::ToggleAim);
 Input->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &ThisClass::StartDraw);
 Input->BindKey(EKeys::LeftMouseButton, IE_Released, this, &ThisClass::ReleaseDraw);
 Input->BindKey(EKeys::Tab, IE_Pressed, this, &ThisClass::ToggleSequence);
 Input->BindKey(EKeys::X, IE_Pressed, this, &ThisClass::CancelPhrase);
 Input->BindKey(EKeys::Q, IE_Pressed, this, &ThisClass::Lane0).bConsumeInput = false;
 Input->BindKey(EKeys::W, IE_Pressed, this, &ThisClass::Lane1).bConsumeInput = false;
 Input->BindKey(EKeys::O, IE_Pressed, this, &ThisClass::Lane2).bConsumeInput = false;
 Input->BindKey(EKeys::P, IE_Pressed, this, &ThisClass::Lane3).bConsumeInput = false;
 Player->PushInputComponent(Input);
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_INPUT_BOUND pawn=%s input=%s"), *Character->GetName(), *Input->GetName());
}
void UMelodiaWaveHarpCombatComponent::UnbindInput()
{
 RestoreAimCamera();
 if (auto* Input = UMelodiaInputContextSubsystem::Get(this)) Input->SetActionPointerCapture(this, false);
 if (auto* Input = BoundInput.Get())
 {
  if (BoundPlayer.IsValid()) BoundPlayer->PopInputComponent(Input);
  Input->DestroyComponent();
 }
 BoundInput = nullptr;
 BoundPlayer.Reset();
}
bool UMelodiaWaveHarpCombatComponent::CanAct() const
{
 const auto* Context = UMelodiaInputContextSubsystem::Get(this);
 return Character.IsValid() && Character->IsLocallyControlled() && Player.IsValid()
  && !IsInSequence() && (!Context || Context->IsMovementAllowed());
}
UMelodiaHybridEncounterComponent* UMelodiaWaveHarpCombatComponent::GetTarget() const { return Target.Get(); }
bool UMelodiaWaveHarpCombatComponent::IsInSequence() const
{
 return PhraseTarget.IsValid() && PhraseTarget->GetPresentationMode() == EMelodiaHybridPresentationMode::Sequence;
}
float UMelodiaWaveHarpCombatComponent::GetDrawTension() const
{
 return bDrawing && GetWorld() ? FMath::Clamp(float(GetWorld()->GetTimeSeconds()-DrawStarted) / .8f, 0.f, 1.f) : 0;
}
float UMelodiaWaveHarpCombatComponent::GetHitFeedback() const
{
 return GetWorld() ? FMath::Clamp(1.f - float(GetWorld()->GetTimeSeconds()-LastHit) / .3f, 0.f, 1.f) : 0.f;
}
float UMelodiaWaveHarpCombatComponent::GetChordFeedback() const
{
 return GetWorld() ? FMath::Clamp(1.f - float(GetWorld()->GetTimeSeconds()-LastChord) / .6f, 0.f, 1.f) : 0.f;
}
void UMelodiaWaveHarpCombatComponent::FindAimTarget()
{
 if (!Player.IsValid() || !Character.IsValid()) return;
 FVector Eye; FRotator Rotation; Player->GetPlayerViewPoint(Eye, Rotation);
 float Best = .98f;
 Target.Reset();
 for (TActorIterator<AActor> It(GetWorld()); It; ++It)
 {
  auto* Encounter = It->FindComponentByClass<UMelodiaHybridEncounterComponent>();
  if (!Encounter || !It->CanBeDamaged() || It->IsHidden()) continue;
  const FVector Delta = It->GetActorLocation()-Eye;
  if (Delta.SizeSquared() > FMath::Square(3500.f)) continue;
  const float Dot = FVector::DotProduct(Delta.GetSafeNormal(), Rotation.Vector());
  if (Dot <= Best) continue;
  FHitResult Occlusion; FCollisionQueryParams Params(SCENE_QUERY_STAT(WaveHarpTarget), false, Character.Get());
  const bool Blocked = GetWorld()->LineTraceSingleByChannel(Occlusion, Eye, It->GetActorLocation(), ECC_Visibility, Params);
  if (Blocked && Occlusion.GetActor() != *It) continue;
  Best = Dot; Target = Encounter;
 }
}
void UMelodiaWaveHarpCombatComponent::StartAim()
{
 if (!CanAct() || bAiming) return;
 bAiming = true;
 bSavedControllerYaw = Character->bUseControllerRotationYaw;
 bSavedOrientToMovement = Character->GetCharacterMovement()->bOrientRotationToMovement;
 Character->bUseControllerRotationYaw = true;
 Character->GetCharacterMovement()->bOrientRotationToMovement = false;
 if (!CameraBoom.IsValid())
 {
  // Follow the active player camera, not the stock party members' camera booms.
  TInlineComponentArray<UCameraComponent*> Cameras(Character.Get());
  for (auto* Camera : Cameras)
  {
   if (Camera->IsActive())
   {
    CameraBoom = Cast<USpringArmComponent>(Camera->GetAttachParent());
    if (CameraBoom.IsValid()) break;
   }
  }
  if (CameraBoom.IsValid())
  {
   SavedArmLength = CameraBoom->TargetArmLength;
   SavedSocketOffset = CameraBoom->SocketOffset;
  }
 }
 StatusText = TEXT("AIM  /  Hold LMB to draw, release to fire.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_AIM_BEGIN"));
}
void UMelodiaWaveHarpCombatComponent::StopAim()
{
 if (!bAiming) return;
 bAiming = false; bDrawing = false;
 if (Character.IsValid())
 {
  Character->bUseControllerRotationYaw = bSavedControllerYaw;
  Character->GetCharacterMovement()->bOrientRotationToMovement = bSavedOrientToMovement;
  if (auto* Anim = Character->GetMesh()->GetAnimInstance()) if (DrawMontage) Anim->Montage_Stop(.15f, DrawMontage);
 }
 StatusText = TEXT("FLOW  /  Click to shoot; hold RMB to aim.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_AIM_END"));
}
void UMelodiaWaveHarpCombatComponent::UpdateAimCamera(float Delta)
{
 if (!CameraBoom.IsValid()) return;
 const float Arm = bAiming ? 320.f : SavedArmLength;
 const FVector Offset = bAiming ? SavedSocketOffset + FVector(0,70,30) : SavedSocketOffset;
 // Frame-rate independent handoff; aiming direction still comes from the view ray.
 const float Alpha = 1.f - FMath::Exp(-FMath::Max(Delta, 0.f) / .12f);
 CameraBoom->TargetArmLength = FMath::Lerp(CameraBoom->TargetArmLength, Arm, Alpha);
 CameraBoom->SocketOffset = FMath::Lerp(CameraBoom->SocketOffset, Offset, Alpha);
 if (!bAiming && FMath::IsNearlyEqual(CameraBoom->TargetArmLength, Arm, .1f)
  && CameraBoom->SocketOffset.Equals(Offset, .1f)) RestoreAimCamera();
}
void UMelodiaWaveHarpCombatComponent::RestoreAimCamera()
{
 if (CameraBoom.IsValid())
 {
  CameraBoom->TargetArmLength = SavedArmLength;
  CameraBoom->SocketOffset = SavedSocketOffset;
 }
 CameraBoom.Reset();
}
void UMelodiaWaveHarpCombatComponent::ToggleAim() { if (bAiming) StopAim(); else StartAim(); }
void UMelodiaWaveHarpCombatComponent::StartDraw()
{
 if (!CanAct() || bDrawing || GetWorld()->GetTimeSeconds()-LastRelease < .25) return;
 bDrawing = true; DrawStarted = GetWorld()->GetTimeSeconds();
 if (auto* Anim = Character->GetMesh()->GetAnimInstance())
 {
  if (DrawMontage) Anim->Montage_Play(DrawMontage);
 }
 StatusText = TEXT("DRAW  /  Release LMB to fire.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_DRAW_BEGIN"));
}
void UMelodiaWaveHarpCombatComponent::ReleaseDraw()
{
 if (!bDrawing) return;
 const float Tension = GetDrawTension();
 bDrawing = false;
 if (!CanAct()) return;
 const double Now = GetWorld()->GetTimeSeconds();
 if (Now - LastRelease > 1.25) ComboStep = 0;
 FVector Eye; FRotator View; Player->GetPlayerViewPoint(Eye, View);
 FCollisionQueryParams Params(SCENE_QUERY_STAT(WaveHarpAim), false, Character.Get());
 FHitResult Hit;
 const FVector Far = Eye + View.Vector()*10000;
 const FVector AimPoint = GetWorld()->LineTraceSingleByChannel(Hit, Eye, Far, ECC_Visibility, Params) ? Hit.ImpactPoint : Far;
 // Forward is derived from the camera ray, never the hand/socket or mesh yaw.
 const FVector Origin = Character->GetActorLocation() + FVector(0,0,35) + View.Vector()*110;
 const FVector Direction = (AimPoint-Origin).GetSafeNormal();
 Character->SetActorRotation(FRotator(0, Direction.Rotation().Yaw, 0));
 FActorSpawnParameters Spawn; Spawn.Owner = Character.Get(); Spawn.Instigator = Character.Get();
 Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 if (auto* Arrow = GetWorld()->SpawnActor<AMelodiaWaveArrow>(Origin, Direction.Rotation(), Spawn))
 {
  Arrow->Launch(this, Direction);
  LastRelease = Now; ++ShotsFired; ++ComboStep;
  static const float Pitches[] = {1.f,1.259921f,1.498307f,1.887749f,2.f};
  if (ShotNote) UGameplayStatics::PlaySoundAtLocation(this, ShotNote, Origin, .35f, Pitches[ComboStep-1]);
  if (ComboStep == 5) { ++ChordsCompleted; ComboStep = 0; LastChord = Now; StatusText = TEXT("CHORD COMPLETE  /  C major 7"); }
  else StatusText = TEXT("RELEASE  /  Keep clicking to complete the chord.");
  if (auto* Anim = Character->GetMesh()->GetAnimInstance())
  {
   if (DrawMontage) Anim->Montage_Stop(.05f, DrawMontage);
   if (AttackMontage) Anim->Montage_Play(AttackMontage, 1.6f);
  }
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_RELEASE shots=%d step=%d tension=%.3f"), ShotsFired, ComboStep, Tension);
 }
 // Tension is presentation only. It never scales the stock damage result.
}
void UMelodiaWaveHarpCombatComponent::ResolveProjectileHit(AActor* Other)
{
 auto* Encounter = IsValid(Other) ? Other->FindComponentByClass<UMelodiaHybridEncounterComponent>() : nullptr;
 const auto* WorldTarget = Cast<AMelodiaWorldSlimeNode>(Other);
 const float HPBefore = WorldTarget ? WorldTarget->CurrentHP : 0.f;
 auto* Bridge = UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(GetWorld()->GetGameInstance());
 if (Encounter && Bridge && Bridge->ResolveWorldFlowAttack(Encounter))
 {
  ++HitsResolved;
  // Observe the existing HP owner after resolution. This is feedback, never damage input.
  if (WorldTarget && WorldTarget->CurrentHP < HPBefore)
  {
   LastHitDamage = HPBefore - WorldTarget->CurrentHP;
   LastHit = GetWorld()->GetTimeSeconds();
   StatusText = WorldTarget->bIsDead ? TEXT("ENCOUNTER COMPLETE") : TEXT("HIT");
  }
  else StatusText = TEXT("MISS");
 }
}
void UMelodiaWaveHarpCombatComponent::ToggleSequence()
{
 if (IsInSequence())
 {
  if (PhraseTarget->ExitSequence()) { PhraseTarget.Reset(); StatusText = TEXT("FLOW  /  Movement restored."); }
  else StatusText = TEXT("Phrase / authoritative effect pending. X cancels.");
 }
 else if (CanAct() && Target.IsValid())
 {
  StopAim(); bDrawing = false;
  if (Target->EnterSequence(TEXT("cadence_strike")))
  {
   PhraseTarget = Target; StatusText = TEXT("SEQUENCE  /  Play Q W O P on the hit line.");
  }
  else StatusText = TEXT("Phrase unavailable; check the active encounter/session.");
 }
 else StatusText = TEXT("Aim at an encounter before pressing TAB.");
 UpdateInputOwnership();
}
void UMelodiaWaveHarpCombatComponent::CancelPhrase()
{
 if (PhraseTarget.IsValid()) PhraseTarget->CancelSequence();
 PhraseTarget.Reset(); bDrawing = false;
 UpdateInputOwnership();
 StatusText = TEXT("FLOW  /  Phrase cancelled; movement restored.");
}
void UMelodiaWaveHarpCombatComponent::UpdateInputOwnership()
{
 const bool Suppress = IsInSequence();
 if (BoundInput)
 {
  for (auto& Binding : BoundInput->KeyBindings)
  {
   if (Binding.Chord.Key == EKeys::Q || Binding.Chord.Key == EKeys::W
    || Binding.Chord.Key == EKeys::O || Binding.Chord.Key == EKeys::P)
    Binding.bConsumeInput = Suppress;
  }
 }
 if (Player.IsValid() && Suppress != bSuppressingMovement)
 {
  Player->SetIgnoreMoveInput(Suppress);
  bSuppressingMovement = Suppress;
  if (Suppress && Character.IsValid()) Character->GetCharacterMovement()->StopMovementImmediately();
 }
}
void UMelodiaWaveHarpCombatComponent::Lane(int32 Index)
{
 if (IsInSequence()) PhraseTarget->RegisterSequenceLaneHit(Index);
}
void UMelodiaWaveHarpCombatComponent::Lane0() { Lane(0); }
void UMelodiaWaveHarpCombatComponent::Lane1() { Lane(1); }
void UMelodiaWaveHarpCombatComponent::Lane2() { Lane(2); }
void UMelodiaWaveHarpCombatComponent::Lane3() { Lane(3); }
void UMelodiaWaveHarpCombatComponent::UpdateWeaponVisibility()
{
 const bool ShowBow = bAiming || bDrawing || (GetWorld() && GetWorld()->GetTimeSeconds()-LastRelease < 1.5);
 if (Bow)
 {
  Bow->SetVisibility(ShowBow);
  // Authored presentation correction only; projectile direction never uses this.
  if (Character.IsValid()) Bow->SetWorldRotation(FRotator(0, Character->GetActorRotation().Yaw+90, 0));
 }
 if (Harp) Harp->SetVisibility(!ShowBow);
}
