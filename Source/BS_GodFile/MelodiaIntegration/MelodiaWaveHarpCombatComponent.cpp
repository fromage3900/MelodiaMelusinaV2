#include "MelodiaWaveHarpCombatComponent.h"
#include "MelodiaWaveArrow.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaUIBridgeSubsystem.h"
#include "MelodiaAudioReactivePresentationSubsystem.h"
#include "MelodiaWorldSlimeNode.h"
#include "MelodiaTraversalComponent.h"
#include "../PCG/MelodiaCymaticFieldComponent.h"
#include "../Piano/PCGHeroMusic.h"
#include "Camera/CameraComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimNotifies/AnimNotifyState.h" // complete type for NewObject<UAnimNotifyState> below (latent: exposed by 2026-10-17 rebuild)
#include "Animation/AnimSequence.h"
#include "UObject/UnrealType.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/PackageName.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"

UMelodiaWaveHarpCombatComponent::UMelodiaWaveHarpCombatComponent()
{
 PrimaryComponentTick.bCanEverTick = true;
 StatusText = TEXT("Aim at an encounter, or take a practice shot.");
 // Route pose montages through the UpperBody layer so the draw/hold/fire never
 // replaces the locomotion pose underneath it. ABP_Melusina_Current layers
 // Slot 'UpperBody' over the state machine (mask: spine_01_x and below).
 PoseSlot = TEXT("UpperBody");
 BowGrip = FTransform(
  FRotator(-84.38001f, 116.13221f, -123.78024f),
  FVector(0.67016f, -9.64373f, -4.35022f),
  FVector(0.9f)
 );
}
void UMelodiaWaveHarpCombatComponent::BeginPlay()
{
 Super::BeginPlay();
 Character = Cast<ACharacter>(GetOwner());
 if (!Character.IsValid()) { SetComponentTickEnabled(false); return; }
 auto* Mesh = Character->GetMesh();
 if (Mesh && !Mesh->DoesSocketExist(InstrumentSocket))
 {
  UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP instrument socket %s missing on %s; instruments are not attached."), *InstrumentSocket.ToString(), *GetNameSafe(Mesh));
 }
 if (Mesh && Mesh->DoesSocketExist(InstrumentSocket))
 {
  USceneComponent* FloatRoot = Character->GetRootComponent();
  const FString InstrumentPackage = InstrumentMesh.ToSoftObjectPath().GetLongPackageName();
  if (FloatRoot && !InstrumentPackage.IsEmpty() && FPackageName::DoesPackageExist(InstrumentPackage))
  {
   // Real shape-key instrument: Bow_Deployment opens the harp into the bow, Flex_Draw/Draw load it.
   Instrument = NewObject<USkeletalMeshComponent>(GetOwner(), TEXT("WaveHarpInstrumentPresentation"));
   Instrument->SetSkeletalMesh(InstrumentMesh.LoadSynchronous());
   Instrument->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   Instrument->SetupAttachment(FloatRoot);
   Instrument->RegisterComponent();
  }
  else
  {
   // No morph mesh yet: the authored static harp and bow, blended by FormAlpha.
   Bow = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("WaveHarpBowPresentation"));
   Bow->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Bow_R07.SM_ME_WaveHarp_Bow_R07")));
   Bow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   Bow->SetupAttachment(Mesh, InstrumentSocket);
   Bow->SetRelativeTransform(BowGrip);
   Bow->RegisterComponent();
   Harp = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("WaveHarpHarpPresentation"));
   Harp->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Harp_R07.SM_ME_WaveHarp_Harp_R07")));
   Harp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
   Harp->SetupAttachment(FloatRoot ? FloatRoot : Mesh);
   Harp->SetRelativeTransform(HarpGrip);
   Harp->RegisterComponent();
  }
 }
 ShotNote = LoadObject<USoundBase>(nullptr, TEXT("/Game/Melodia/Audio/WaveHarp/SW_WaveHarp_Orchestra_C4.SW_WaveHarp_Orchestra_C4"));
 for (const TCHAR* Family : {TEXT("Cmaj7"), TEXT("Cmaj6"), TEXT("Cm7")})
 {
  const FString Path = FString::Printf(TEXT("/Game/Melodia/Audio/WaveHarp/SW_WaveHarp_%s_Complete.SW_WaveHarp_%s_Complete"), Family, Family);
  ChordFlourishes.Add(LoadObject<USoundBase>(nullptr, *Path));
 }
 if (UMelodiaTraversalComponent* Traversal = Character->FindComponentByClass<UMelodiaTraversalComponent>())
  PrimaryComponentTick.AddPrerequisite(Traversal, Traversal->PrimaryComponentTick);
 ScytheRibbon = NewObject<UProceduralMeshComponent>(GetOwner(), TEXT("ScytheBladeRibbon"));
 ScytheRibbon->SetupAttachment(Character->GetRootComponent());
 ScytheRibbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 ScytheRibbon->SetCastShadow(false);
 ScytheRibbon->RegisterComponent();
 ScytheRibbon->SetVisibility(false);
 if (UMaterialInterface* RibbonMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")))
  ScytheRibbon->SetMaterial(0, RibbonMat);
 UpdateInstruments(0.f);
}
void UMelodiaWaveHarpCombatComponent::EndPlay(const EEndPlayReason::Type Reason)
{
 CancelPhrase();
 bDrawing = false; bCharging = false;
 StopAim();
 StopPose();
 UnbindInput();
 if (Bow) Bow->DestroyComponent();
 if (Harp) Harp->DestroyComponent();
 if (Instrument) Instrument->DestroyComponent();
 if (ScytheRibbon) ScytheRibbon->DestroyComponent();
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
  SyncLockedTarget();
  if (!bCombatLocked) FindAimTarget();
 }
 UpdateInputOwnership();
 ResolvePendingScytheHit();
 UpdateSequenceFeel(Delta);
 UpdateLockTurn(Delta);
 const auto* Traversal = Character->FindComponentByClass<UMelodiaTraversalComponent>();
 if (bAiming && (!Traversal || !Traversal->IsRollPlaying()))
 {
  Character->SetActorRotation(FRotator(0, Controller->GetControlRotation().Yaw, 0));
 }
 UpdatePose(GetWorld()->GetTimeSeconds());
 if (!CanAct() && !IsInSequence()) { bDrawing = false; bCharging = false; StopAim(); }
 if (ComboStep > 0 && GetWorld()->GetTimeSeconds() - LastRelease > FMath::Clamp(ChordChainWindow, .6f, 2.f)) ComboStep = 0;
 if (ScytheStep > 0 && !bScytheHitArmed && GetWorld()->GetTimeSeconds() - LastScytheChain > FMath::Clamp(ChordChainWindow, .6f, 2.f)) ScytheStep = 0;
 UpdateAimCamera(Delta);
 UpdateInstruments(Delta);
 UpdateScytheRibbon();
 if (IsInSequence() && Target.IsValid())
  StatusText = FString::Printf(TEXT("SEQUENCE  /  Resonance %d%%  /  Q W O P on the hit line."), FMath::RoundToInt(Target->GetResonanceNormalized() * 100.f));
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
 // A basic click never releases the separate RMB charge.
 FInputKeyBinding BasicRelease(FInputChord(EKeys::LeftMouseButton), IE_Released);
 BasicRelease.KeyDelegate.GetDelegateForManualSet().BindLambda([this]
 {
  if (!bAiming) ReleaseDraw();
 });
 Input->KeyBindings.Add(MoveTemp(BasicRelease));
 Input->BindKey(EKeys::Tab, IE_Pressed, this, &ThisClass::ToggleSequence);
 Input->BindKey(EKeys::X, IE_Pressed, this, &ThisClass::CancelPhrase);
 Input->BindKey(EKeys::F, IE_Pressed, this, &ThisClass::TriggerScytheMelee);
 Input->BindKey(EKeys::T, IE_Pressed, this, &ThisClass::ToggleLock);
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
 // Tension belongs to the charged archery shot only; a tap is a caster cast with none.
 return bCharging && GetWorld() ? FMath::Clamp(float(GetWorld()->GetTimeSeconds()-ChargeBegan) / FMath::Clamp(DrawReadySeconds, .2f, 1.5f), 0.f, 1.f) : 0;
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
 if (auto* Traversal = Character->FindComponentByClass<UMelodiaTraversalComponent>()) Traversal->ApplyRotationPolicy();
 else
 {
  bSavedControllerYaw = Character->bUseControllerRotationYaw;
  bSavedOrientToMovement = Character->GetCharacterMovement()->bOrientRotationToMovement;
  Character->bUseControllerRotationYaw = true;
  Character->GetCharacterMovement()->bOrientRotationToMovement = false;
 }
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
 StartDraw();
 if (bDrawing) BeginCharge(GetWorld()->GetTimeSeconds());
 StatusText = TEXT("CHARGE  /  Hold RMB to draw, release RMB to fire.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_AIM_BEGIN"));
}
void UMelodiaWaveHarpCombatComponent::StopAim()
{
 if (!bAiming) return;
 if (bDrawing) ReleaseDraw();
 bAiming = false; bDrawing = false; bCharging = false;
 if (Pose != EPose::Fire) StopPose();
 if (Character.IsValid())
 {
  if (auto* Traversal = Character->FindComponentByClass<UMelodiaTraversalComponent>()) Traversal->ApplyRotationPolicy();
  else
  {
   Character->bUseControllerRotationYaw = bSavedControllerYaw;
   Character->GetCharacterMovement()->bOrientRotationToMovement = bSavedOrientToMovement;
  }
 }
 StatusText = TEXT("FLOW  /  LMB casts; hold and release RMB for a charged shot.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_AIM_END"));
}
void UMelodiaWaveHarpCombatComponent::UpdateAimCamera(float Delta)
{
 if (!CameraBoom.IsValid() && IsInSequence()) EnsureCameraBoom();
 if (!CameraBoom.IsValid()) return;
 const float Arm = bAiming ? FMath::Clamp(AimArmLength, 220.f, 450.f) : IsInSequence() ? SavedArmLength + 60.f : SavedArmLength;
 const FVector Offset = bAiming ? SavedSocketOffset + AimSocketOffset : SavedSocketOffset;
 // Frame-rate independent handoff; aiming direction still comes from the view ray.
 const float Alpha = 1.f - FMath::Exp(-FMath::Max(Delta, 0.f) / FMath::Clamp(AimBlendSeconds, .05f, .3f));
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
 if (!CanAct() || bDrawing || GetWorld()->GetTimeSeconds()-LastRelease < FMath::Clamp(MinimumShotInterval, .15f, .5f)) return;
 bDrawing = true; bCharging = false; DrawStarted = GetWorld()->GetTimeSeconds();
 StatusText = TEXT("CAST  /  Release LMB for a basic attack.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_DRAW_BEGIN"));
}
void UMelodiaWaveHarpCombatComponent::ReleaseDraw()
{
 if (!bDrawing) return;
 const float Tension = GetDrawTension();
 const bool bWasCharged = bCharging;
 bDrawing = false; bCharging = false;
 if (!CanAct()) return;
 const double Now = GetWorld()->GetTimeSeconds();
 if (Now - LastRelease > FMath::Clamp(ChordChainWindow, .6f, 2.f)) ComboStep = 0;
 FVector Eye; FRotator View; Player->GetPlayerViewPoint(Eye, View);
 FCollisionQueryParams Params(SCENE_QUERY_STAT(WaveHarpAim), false, Character.Get());
 FHitResult Hit;
 const FVector Far = Eye + View.Vector()*10000;
 // Forward is derived from the camera ray, never the hand/socket or mesh yaw.
 const FVector Origin = Character->GetActorLocation() + FVector(0,0,35) + View.Vector()*110;
 // The aim ray begins at the arrow origin's depth along the view: geometry between the camera
 // and the muzzle (an overhang behind her) can never become the aim point.
 const FVector RayStart = Eye + View.Vector()*FMath::Max(0.0, FVector::DotProduct(Origin - Eye, View.Vector()));
 const FVector AimPoint = GetWorld()->LineTraceSingleByChannel(Hit, RayStart, Far, ECC_Visibility, Params) ? Hit.ImpactPoint : Far;
 const FVector Direction = (AimPoint-Origin).GetSafeNormal();
 Character->SetActorRotation(FRotator(0, Direction.Rotation().Yaw, 0));
 FActorSpawnParameters Spawn; Spawn.Owner = Character.Get(); Spawn.Instigator = Character.Get();
 Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 bShotIsCharged = bWasCharged;
 if (auto* Arrow = GetWorld()->SpawnActor<AMelodiaWaveArrow>(Origin, Direction.Rotation(), Spawn))
 {
  Arrow->Launch(this, Direction);
  LastRelease = Now; ++ShotsFired; ++ComboStep;
  const float Semitones[] = {float(ChordIntervals.X),float(ChordIntervals.Y),float(ChordIntervals.Z),float(ChordIntervals.W),12.f};
  const float Note = FMath::Clamp(Semitones[ComboStep-1], 0.f, 24.f);
  const float Pitch = FMath::Pow(2.f, Note / 12.f);
  if (ShotNote) UGameplayStatics::PlaySoundAtLocation(this, ShotNote, Origin, .35f, Pitch);
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_NOTE shot=%d step=%d semitones=%.1f pitch=%.6f chord=%s"), ShotsFired, ComboStep, Note, Pitch, *ChordName);
  const bool bCompletedChord = ComboStep == 5;
  if (bCompletedChord)
  {
   const int32 Family = ChordIntervals == FVector4(0,4,7,11) ? 0 : ChordIntervals == FVector4(0,4,7,9) ? 1 : ChordIntervals == FVector4(0,3,7,10) ? 2 : INDEX_NONE;
   if (ChordFlourishes.IsValidIndex(Family) && ChordFlourishes[Family])
    UGameplayStatics::PlaySoundAtLocation(this, ChordFlourishes[Family], Origin, .45f);
   ++ChordsCompleted; ComboStep = 0; LastChord = Now;
   StatusText = FString::Printf(TEXT("CHORD COMPLETE  /  %s"), *ChordName);
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHORD chord=%s flourish=%d completed=%d"), *ChordName, Family, ChordsCompleted);
  }
  else StatusText = TEXT("RELEASE  /  Keep clicking to complete the chord.");
  // The existing presentation owner publishes Mid/MidIntensity; the sole
  // Cymatics writer consumes those lanes. This never writes either MPC here.
  if (auto* GI = GetWorld()->GetGameInstance())
   if (auto* Audio = GI->GetSubsystem<UMelodiaAudioReactivePresentationSubsystem>())
    Audio->PulseImpact(bCompletedChord ? .8f : .25f);
  PlayPose(bWasCharged ? ChargeFireAnim : CastShootAnim, false);
  Pose = bWasCharged ? EPose::Fire : EPose::CastShoot;
  if (bWasCharged) LastChargedRelease = Now;
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_RELEASE shots=%d step=%d tension=%.3f charged=%d"), ShotsFired, ComboStep, Tension, bWasCharged ? 1 : 0);
 }
 // Tension is presentation only. It never scales the stock damage result.
}
void UMelodiaWaveHarpCombatComponent::ResolveProjectileHit(AActor* Other, const float ReleaseBeatPhase)
{
 // A note that lands on an instrument plays it exactly like a footstep does: the
 // node's own press path owns pitch, grading and reactivity.
 if (auto* Bell = Cast<APCGHeroMusicNode>(Other))
 {
  if (!Character.IsValid()) return;
  Bell->SetPressedForActor(Character.Get(), true);
  UMelodiaCymaticFieldComponent::BroadcastHit(GetWorld(), Bell->GetActorLocation(), 1.f);
  FTimerHandle Release;
  GetWorld()->GetTimerManager().SetTimer(Release, FTimerDelegate::CreateWeakLambda(Bell,
   [Bell, Player = Character]() { if (Player.IsValid()) Bell->SetPressedForActor(Player.Get(), false); }), .25f, false);
  return;
 }
 auto* Encounter = IsValid(Other) ? Other->FindComponentByClass<UMelodiaHybridEncounterComponent>() : nullptr;
 const auto* WorldTarget = Cast<AMelodiaWorldSlimeNode>(Other);
 const float HPBefore = WorldTarget ? WorldTarget->CurrentHP : 0.f;
 auto* Bridge = UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(GetWorld()->GetGameInstance());
 if (Encounter && Bridge && Bridge->ResolveWorldFlowAttack(Encounter, ReleaseBeatPhase))
 {
  ++HitsResolved;
  // The landed note rings the world: an on-beat release is a full-strength impact.
  const bool bOnBeat = ReleaseBeatPhase < 0.f
   || FMath::Min(ReleaseBeatPhase, 1.f - ReleaseBeatPhase) <= Encounter->OnBeatWindowBeats;
  const float Ring = bOnBeat ? 1.f : .45f;
  if (auto* Audio = GetWorld()->GetGameInstance()->GetSubsystem<UMelodiaAudioReactivePresentationSubsystem>())
   Audio->PulseImpact(Ring);
  UMelodiaCymaticFieldComponent::BroadcastHit(GetWorld(), Other->GetActorLocation(), Ring);
  for (const TSoftObjectPtr<UNiagaraSystem>& Fx : {HitBurstSystem, HitRippleSystem})
   if (UNiagaraSystem* System = Fx.LoadSynchronous())
    UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, System, Other->GetActorLocation(),
     FRotator::ZeroRotator, FVector(.6f + .4f * Ring));
  // Observe the existing HP owner after resolution. This is feedback, never damage input.
  if (WorldTarget && WorldTarget->CurrentHP < HPBefore)
  {
   LastHitDamage = HPBefore - WorldTarget->CurrentHP;
   LastHit = GetWorld()->GetTimeSeconds();
   StatusText = WorldTarget->bIsDead ? TEXT("ENCOUNTER COMPLETE")
    : Encounter->IsResonanceLocked() ? TEXT("RESONANCE LOCKED  /  TAB to play the figure.")
    : FString::Printf(TEXT("HIT  /  Resonance %d%%"), FMath::RoundToInt(Encounter->GetResonanceNormalized() * 100.f));
  }
  else StatusText = TEXT("MISS");
 }
}
void UMelodiaWaveHarpCombatComponent::ResolveMeleeHit(AActor* Other, const float SwingBeatPhase)
{
 ResolveProjectileHit(Other, SwingBeatPhase);
}
void UMelodiaWaveHarpCombatComponent::TriggerScytheMelee()
{
 if (!CanAct() || !GetWorld() || bScytheHitArmed || bScytheResolveQueued) return;
 const double Now = GetWorld()->GetTimeSeconds();
 if (Now - LastMeleeSwing < FMath::Clamp(MinimumShotInterval, .15f, .5f)) return;
 LastMeleeSwing = Now;
 LastScytheChain = Now;
 ++MeleeSwings;
 ScytheStep = (ScytheStep % 3) + 1;
 const float Semitones[] = {0.f, 7.f, 12.f};
 const float Note = Semitones[ScytheStep - 1];
 const float Pitch = FMath::Pow(2.f, Note / 12.f);
 const FVector Origin = Character->GetActorLocation() + Character->GetActorForwardVector() * 95.f + FVector(0,0,40.f);
 if (ShotNote) UGameplayStatics::PlaySoundAtLocation(this, ShotNote, Origin, .45f, Pitch);
 PlayScytheMontage();
 if (!bScytheHitArmed)
 {
  StatusText = TEXT("CHIME-SCYTHE  /  Swing clip unavailable.");
  return;
 }
 StatusText = FString::Printf(TEXT("CHIME-SCYTHE  /  Step %d of 3."), ScytheStep);
}
void UMelodiaWaveHarpCombatComponent::ToggleSequence()
{
 if (IsInSequence())
 {
  if (PhraseTarget->ExitSequence()) { PhraseTarget.Reset(); StopPose(); StatusText = TEXT("FLOW  /  Movement restored."); }
  else StatusText = TEXT("Phrase / authoritative effect pending. X cancels.");
 }
 else if (CanAct() && Target.IsValid() && !Target->IsResonanceLocked())
  StatusText = TEXT("Figure not resonant yet. Land hits on the beat.");
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
 PhraseTarget.Reset(); bDrawing = false; StopPose();
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
}
void UMelodiaWaveHarpCombatComponent::RegisterLaneHit(int32 Index) { Lane(Index); }
void UMelodiaWaveHarpCombatComponent::Lane(int32 Index)
{
 if (IsInSequence()) PhraseTarget->RegisterSequenceLaneHit(Index);
}
void UMelodiaWaveHarpCombatComponent::Lane0() { Lane(0); }
void UMelodiaWaveHarpCombatComponent::Lane1() { Lane(1); }
void UMelodiaWaveHarpCombatComponent::Lane2() { Lane(2); }
void UMelodiaWaveHarpCombatComponent::Lane3() { Lane(3); }
void UMelodiaWaveHarpCombatComponent::PlayPose(const TSoftObjectPtr<UAnimSequence>& Clip, bool bLoop)
{
 if (!Character.IsValid() || !Character->GetMesh()) return;
 UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance();
 UAnimSequence* Seq = Clip.LoadSynchronous();
 if (!Anim || !Seq)
 {
  UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP pose clip unavailable: %s"), *Clip.ToString());
  return;
 }
 PoseMontage = Anim->PlaySlotAnimationAsDynamicMontage(Seq, PoseSlot, .08f, .2f, 1.f, bLoop ? 9999 : 1);
}
void UMelodiaWaveHarpCombatComponent::StopPose()
{
 if (Character.IsValid() && Character->GetMesh())
 {
  if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
  {
   if (PoseMontage) Anim->Montage_Stop(.2f, PoseMontage);
  }
 }
 PoseMontage = nullptr;
 Pose = EPose::None;
}
void UMelodiaWaveHarpCombatComponent::BeginCharge(double Now)
{
 bCharging = true;
 ChargeBegan = Now;
 PlayPose(ChargeDrawAnim, false);
 Pose = EPose::Draw;
 StatusText = TEXT("CHARGE / Release RMB to fire.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHARGE_BEGIN"));
}
void UMelodiaWaveHarpCombatComponent::UpdatePose(double Now)
{
 if (!Character.IsValid() || !Character->GetMesh()) return;
 UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance();
 const bool bPlaying = Anim && PoseMontage && Anim->Montage_IsPlaying(PoseMontage);
 if (bAiming && bDrawing && !bCharging && Now - DrawStarted >= ChargeThresholdSeconds) BeginCharge(Now);
 if (bCharging && Pose == EPose::Draw && !bPlaying)
 {
  PlayPose(ChargeHoldAnim, true);
  Pose = EPose::Hold;
 }
 else if (!bCharging && bAiming && !bDrawing && !bPlaying && Now - LastRelease > .25)
 {
  PlayPose(CastStanceAnim, true);
  Pose = EPose::Stance;
 }
 else if (!bPlaying && !bAiming && !bCharging)
 {
  Pose = EPose::None;
 }
}
void UMelodiaWaveHarpCombatComponent::UpdateInstruments(float Delta)
{
 const UWorld* World = GetWorld();
 if (!World || !Character.IsValid()) return;
 const double Now = World->GetTimeSeconds();
 ScytheMontageFraction = -1.f;
 if (Pose == EPose::ScytheSwing && PoseMontage && Character->GetMesh())
 {
  if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
  {
   if (Anim->Montage_IsPlaying(PoseMontage))
   {
    const float Len = PoseMontage->GetPlayLength();
    ScytheMontageFraction = Len > KINDA_SMALL_NUMBER ? Anim->Montage_GetPosition(PoseMontage) / Len : 0.f;
   }
  }
 }
 const bool bScytheMontage = ScytheMontageFraction >= 0.f;
 const bool bScytheForm = bScytheMontage || ScytheAlpha > 0.02f;
 const bool bBowForm = !bScytheForm && (bCharging || (Now - LastChargedRelease < BowFormHoldSeconds));
 FormAlpha = FMath::FInterpConstantTo(FormAlpha, bBowForm ? 1.f : 0.f, Delta, 1.f / FMath::Max(TransformSeconds, .05f));
 float DesiredScythe = 0.f;
 float ChordWeight = 0.f;
 float BellWeight = 0.f;
 if (bScytheMontage)
 {
  const float Hit = FMath::Clamp(ScytheHitFraction, 0.15f, 0.85f);
  DesiredScythe = ScytheMontageFraction <= Hit ? ScytheMontageFraction / Hit : 1.f;
  const float Peak = 1.f - FMath::Clamp(FMath::Abs(ScytheMontageFraction - Hit) / FMath::Max(Hit, 0.05f), 0.f, 1.f);
  float VisualBeat = 1.f;
  if (const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this))
   if (MusicClock->HasMusicalTime())
    VisualBeat = 0.65f + 0.35f * FMath::Cos(MusicClock->GetBeatPhase(UMelodiaMusicClockSubsystem::VisualTimebase) * 2.f * PI);
  ChordWeight = Peak * VisualBeat;
  BellWeight = Peak * VisualBeat;
  ScytheAlpha = DesiredScythe;
 }
 else ScytheAlpha = FMath::FInterpConstantTo(ScytheAlpha, 0.f, Delta, 1.f / FMath::Max(TransformSeconds, .05f));
 const float HandAlpha = FMath::Max(FormAlpha, ScytheAlpha);
 const float Tension = GetDrawTension();
 const FVector Float = AstrolabeOffset + FVector(0, 0, AstrolabeBobCm * FMath::Sin(Now * 2.0));
 const float Spin = FMath::Fmod(Now * AstrolabeSpinDegPerSecond, 360.0);
 if (Instrument)
 {
  const FTransform Actor = Character->GetActorTransform();
  FTransform Astro(Actor.GetRotation() * FQuat(FRotator(0, Spin, 0)), Actor.TransformPosition(Float), HarpGrip.GetScale3D());
  FTransform InHand = BowGrip;
  if (USkeletalMeshComponent* Mesh = Character->GetMesh())
  {
   InHand = BowGrip * Mesh->GetSocketTransform(InstrumentSocket);
  }
  FTransform Out;
  Out.Blend(Astro, InHand, HandAlpha);
  Instrument->SetWorldTransform(Out);
  Instrument->SetMorphTarget(MorphBowDeployment, FormAlpha);
  // Bake the authored parent/driver motion between deployment endpoints.
  // Adjacent samples retain the Blender transformation without a second rig.
  for (int32 Sample = 1; Sample < 16; ++Sample)
  {
   const FName Morph(*FString::Printf(TEXT("Transform_Residual_%02d"), Sample));
   const float Weight = FMath::Max(0.f, 1.f - FMath::Abs(FormAlpha * 16.f - Sample));
   Instrument->SetMorphTarget(Morph, Weight);
  }
  Instrument->SetMorphTarget(MorphFlexDraw, FormAlpha * Tension);
  Instrument->SetMorphTarget(MorphBowstringDraw, Tension);
  // Drive 3rd Harmonic Form: Carillon Chime-Scythe + rotational arc residuals + bell/chord vibration
  Instrument->SetMorphTarget(MorphScytheDeployment, ScytheAlpha);
  for (int32 Sample = 1; Sample <= 8; ++Sample)
  {
   const FName Morph(*FString::Printf(TEXT("Scythe_Residual_0%d"), Sample));
   const float Weight = FMath::Max(0.f, 1.f - FMath::Abs(ScytheAlpha * 9.f - Sample));
   Instrument->SetMorphTarget(Morph, Weight);
  }
  Instrument->SetMorphTarget(MorphScytheChord, ChordWeight);
  Instrument->SetMorphTarget(MorphScytheBell, BellWeight);
  return;
 }
 if (Harp)
 {
  Harp->SetRelativeLocation(Float);
  Harp->SetRelativeRotation(FRotator(0, Spin, 0));
  Harp->SetRelativeScale3D(HarpGrip.GetScale3D() * (1.f - FormAlpha));
  Harp->SetVisibility(FormAlpha < .98f);
 }
 if (Bow)
 {
  Bow->SetRelativeScale3D(BowGrip.GetScale3D() * FormAlpha);
  Bow->SetVisibility(FormAlpha > .02f);
 }
}
void UAnimNotify_MelodiaScytheHit::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
 if (!MeshComp || !MeshComp->GetOwner()) return;
 if (UMelodiaWaveHarpCombatComponent* Combat = MeshComp->GetOwner()->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
  Combat->CommitScytheHit();
}
float UMelodiaWaveHarpCombatComponent::SampleBeatPhase() const
{
 if (UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this))
 {
  if (!MusicClock->HasMusicalTime())
   MusicClock->EnsureBattleControllerMusicClock();
  if (MusicClock->HasMusicalTime())
   return MusicClock->GetBeatPhase(UMelodiaMusicClockSubsystem::InputTimebase);
 }
 return -1.f;
}
AActor* UMelodiaWaveHarpCombatComponent::FindMeleeActor() const
{
 if (!Character.IsValid() || !GetWorld()) return nullptr;
 if (Instrument && Instrument->DoesSocketExist(ScytheBladeStartSocket) && Instrument->DoesSocketExist(ScytheBladeTipSocket))
 {
  const FVector Start = Instrument->GetSocketLocation(ScytheBladeStartSocket);
  const FVector End = Instrument->GetSocketLocation(ScytheBladeTipSocket) + Character->GetActorForwardVector() * 140.f;
  if (UClass* ACMClass = FindObject<UClass>(nullptr, TEXT("/Script/CollisionsManager.ACMCollisionManagerComponent")))
  {
   if (UActorComponent* ACM = Character->FindComponentByClass(ACMClass))
   {
    if (UFunction* Fn = ACM->FindFunction(TEXT("PerformSwipeTraceShot_Local")))
    {
     struct FSwipeParams { FVector S; FVector E; float R; FHitResult Hit; bool bRet; };
     FSwipeParams P{Start, End, 85.f, FHitResult(), false};
     if (Fn->ParmsSize == sizeof(FSwipeParams))
     {
      ACM->ProcessEvent(Fn, &P);
      if (AActor* Swiped = P.Hit.GetActor())
       if (Swiped != Character.Get() && (Swiped->FindComponentByClass<UMelodiaHybridEncounterComponent>() || Cast<APCGHeroMusicNode>(Swiped)))
        return Swiped;
     }
    }
   }
  }
  FHitResult SweepHit;
  FCollisionQueryParams Query(SCENE_QUERY_STAT(WaveHarpScytheBlade), false, Character.Get());
  if (GetWorld()->SweepSingleByChannel(SweepHit, Start, End, FQuat::Identity, ECC_WorldDynamic, FCollisionShape::MakeSphere(85.f), Query))
   if (AActor* Swiped = SweepHit.GetActor())
    if (Swiped->FindComponentByClass<UMelodiaHybridEncounterComponent>() || Cast<APCGHeroMusicNode>(Swiped))
     return Swiped;
 }
 AActor* HitTarget = Target.IsValid() ? Target->GetOwner() : nullptr;
 if (HitTarget && FVector::Dist(Character->GetActorLocation(), HitTarget->GetActorLocation()) <= MeleeReachCm) return HitTarget;
 for (TActorIterator<AActor> It(GetWorld()); It; ++It)
 {
  if (*It == Character.Get() || (*It)->IsHidden()) continue;
  if (It->FindComponentByClass<UMelodiaHybridEncounterComponent>() || Cast<APCGHeroMusicNode>(*It))
   if (FVector::Dist(Character->GetActorLocation(), It->GetActorLocation()) <= MeleeReachCm) return *It;
 }
 return nullptr;
}
UAnimMontage* UMelodiaWaveHarpCombatComponent::MakeSlotMontage(UAnimSequence* Seq, float BlendOut) const
{
 if (!Seq) return nullptr;
 UAnimMontage* Montage = UAnimMontage::CreateSlotAnimationAsDynamicMontage(Seq, PoseSlot, 0.08f, BlendOut, 1.f, 1, -1.f, 0.f);
 if (Montage)
 {
  Montage->bEnableRootMotionTranslation = true;
  Montage->bEnableRootMotionRotation = false;
 }
 return Montage;
}
void UMelodiaWaveHarpCombatComponent::PlayScytheMontage()
{
 bScytheHitArmed = false;
 if (!Character.IsValid() || !Character->GetMesh()) return;
 UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance();
 UAnimSequence* Seq = MeleeSwingAnim.LoadSynchronous();
 if (!Anim || !Seq)
 {
  UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP pose clip unavailable: %s"), *MeleeSwingAnim.ToString());
  return;
 }
 UAnimMontage* Montage = MakeSlotMontage(Seq, 0.2f);
 if (!Montage) return;
 const float HitTime = FMath::Clamp(ScytheHitFraction, 0.15f, 0.85f) * FMath::Max(Seq->GetPlayLength(), 0.05f);
 UAnimNotify_MelodiaScytheHit* HitNotify = NewObject<UAnimNotify_MelodiaScytheHit>(Montage);
 FAnimNotifyEvent& Event = Montage->Notifies.AddDefaulted_GetRef();
 Event.Notify = HitNotify;
 Event.NotifyName = TEXT("MelodiaScytheHit");
 Event.Link(Montage, HitTime, 0);
 Event.SetDuration(0.f);
 Event.TriggerWeightThreshold = 0.f;
 Event.NotifyTriggerChance = 1.f;
 Event.MontageTickType = EMontageNotifyTickType::Queued;
 Event.bTriggerOnDedicatedServer = true;
 Event.TrackIndex = 0;
 Montage->RefreshCacheData();
 PoseMontage = Montage;
 Anim->Montage_Play(Montage, 1.f);
 Pose = EPose::ScytheSwing;
 bScytheHitArmed = true;
}
void UMelodiaWaveHarpCombatComponent::CommitScytheHit()
{
 if (!bScytheHitArmed || !GetWorld()) return;
 bScytheHitArmed = false;
 ScytheSwingBeatPhase = SampleBeatPhase();
 ScytheResolveTarget = FindMeleeActor();
 ScytheResolveStep = ScytheStep;
 ScytheResolveSwings = MeleeSwings;
 bScytheResolveQueued = true;
 ScytheResolveAfterTime = GetWorld()->GetTimeSeconds();
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_SCYTHE_SWING swings=%d step=%d target=%s beat_phase=%.3f"),
  ScytheResolveSwings, ScytheResolveStep, *GetNameSafe(ScytheResolveTarget.Get()), ScytheSwingBeatPhase);
 if (!ScytheResolveTarget.IsValid())
  StatusText = FString::Printf(TEXT("CHIME-SCYTHE  /  Crescent missed. Step %d of 3."), ScytheStep);
}
void UMelodiaWaveHarpCombatComponent::ResolvePendingScytheHit()
{
 if (!bScytheResolveQueued || !GetWorld()) return;
 if (GetWorld()->GetTimeSeconds() <= ScytheResolveAfterTime) return;
 bScytheResolveQueued = false;
 if (ScytheResolveTarget.IsValid()) ResolveMeleeHit(ScytheResolveTarget.Get(), ScytheSwingBeatPhase);
}
namespace
{
UActorComponent* MelodiaFindComponent(AActor* Actor, const TCHAR* ScriptPath)
{
 if (!Actor) return nullptr;
 UClass* Class = FindObject<UClass>(nullptr, ScriptPath);
 if (!Class) Class = LoadObject<UClass>(nullptr, ScriptPath);
 return Class ? Actor->FindComponentByClass(Class) : nullptr;
}
void MelodiaCall(UObject* Object, const TCHAR* FunctionName, TFunctionRef<void(uint8*, UFunction*)> Fill)
{
 if (!Object) return;
 UFunction* Function = Object->FindFunction(FName(FunctionName));
 if (!Function) return;
 uint8* Params = (uint8*)FMemory_Alloca(Function->ParmsSize);
 FMemory::Memzero(Params, Function->ParmsSize);
 Fill(Params, Function);
 Object->ProcessEvent(Function, Params);
}
AActor* MelodiaReadActor(UObject* Object, const TCHAR* FunctionName)
{
 if (!Object) return nullptr;
 UFunction* Function = Object->FindFunction(FName(FunctionName));
 if (!Function) return nullptr;
 uint8* Params = (uint8*)FMemory_Alloca(Function->ParmsSize);
 FMemory::Memzero(Params, Function->ParmsSize);
 Object->ProcessEvent(Function, Params);
 for (TFieldIterator<FProperty> It(Function); It; ++It)
  if (It->HasAnyPropertyFlags(CPF_ReturnParm))
   if (FObjectProperty* Prop = CastField<FObjectProperty>(*It))
    return Cast<AActor>(Prop->GetObjectPropertyValue_InContainer(Params));
 return nullptr;
}
void MelodiaWriteActor(UObject* Object, const TCHAR* FunctionName, AActor* Value)
{
 MelodiaCall(Object, FunctionName, [&](uint8* Params, UFunction* Function)
 {
  for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
   if (!It->HasAnyPropertyFlags(CPF_ReturnParm))
    if (FObjectProperty* Prop = CastField<FObjectProperty>(*It))
     Prop->SetObjectPropertyValue_InContainer(Params, Value);
 });
}
void MelodiaWriteBool(UObject* Object, const TCHAR* FunctionName, bool Value)
{
 MelodiaCall(Object, FunctionName, [&](uint8* Params, UFunction* Function)
 {
  for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
   if (FBoolProperty* Prop = CastField<FBoolProperty>(*It))
    Prop->SetPropertyValue_InContainer(Params, Value);
 });
}
void MelodiaWriteByte(UObject* Object, const TCHAR* FunctionName, uint8 Value)
{
 MelodiaCall(Object, FunctionName, [&](uint8* Params, UFunction* Function)
 {
  for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
  {
   FByteProperty* ByteProp = CastField<FByteProperty>(*It);
   FEnumProperty* EnumProp = CastField<FEnumProperty>(*It);
   if (ByteProp) ByteProp->SetPropertyValue_InContainer(Params, Value);
   else if (EnumProp) EnumProp->GetUnderlyingProperty()->SetIntPropertyValue(EnumProp->ContainerPtrToValuePtr<void>(Params), (int64)Value);
  }
 });
}
void MelodiaWriteNameAndVector(UObject* Object, const TCHAR* FunctionName, FName Name, FVector Location)
{
 MelodiaCall(Object, FunctionName, [&](uint8* Params, UFunction* Function)
 {
  for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
  {
   FNameProperty* NameProp = CastField<FNameProperty>(*It);
   FStructProperty* StructProp = CastField<FStructProperty>(*It);
   if (NameProp) NameProp->SetPropertyValue_InContainer(Params, Name);
   else if (StructProp && StructProp->Struct == TBaseStructure<FVector>::Get())
    *StructProp->ContainerPtrToValuePtr<FVector>(Params) = Location;
  }
 });
}
}
void UMelodiaWaveHarpCombatComponent::SyncLockedTarget()
{
 if (!Character.IsValid()) return;
 UActorComponent* ATS = MelodiaFindComponent(Character.Get(), TEXT("/Script/AscentTargetingSystem.ATSTargetingComponent"));
 AActor* Locked = MelodiaReadActor(ATS, TEXT("GetCurrentTarget"));
 if (!Locked) { bCombatLocked = false; return; }
 bCombatLocked = true;
 if (UMelodiaHybridEncounterComponent* Encounter = Locked->FindComponentByClass<UMelodiaHybridEncounterComponent>())
  Target = Encounter;
}
void UMelodiaWaveHarpCombatComponent::ToggleLock()
{
 if (!CanAct() || !Character.IsValid()) return;
 UActorComponent* ATS = MelodiaFindComponent(Character.Get(), TEXT("/Script/AscentTargetingSystem.ATSTargetingComponent"));
 if (!ATS) { StatusText = TEXT("LOCK  /  Targeting component missing."); return; }
 MelodiaWriteByte(ATS, TEXT("SetTargetingType"), 2);
 if (bCombatLocked)
 {
  MelodiaWriteBool(ATS, TEXT("TriggerTargeting"), false);
  bCombatLocked = false;
  StatusText = TEXT("FLOW  /  Lock released.");
  return;
 }
 FindAimTarget();
 AActor* LockActor = Target.IsValid() ? Target->GetOwner() : nullptr;
 if (!LockActor) { StatusText = TEXT("LOCK  /  Look at an encounter, then press T."); return; }
 MelodiaWriteActor(ATS, TEXT("SetCurrentTarget"), LockActor);
 MelodiaWriteBool(ATS, TEXT("TriggerTargeting"), true);
 if (!MelodiaReadActor(ATS, TEXT("GetCurrentTarget"))) MelodiaWriteActor(ATS, TEXT("SetCurrentTarget"), LockActor);
 SyncLockedTarget();
 if (!bCombatLocked) { StatusText = TEXT("LOCK  /  Could not hold that actor."); return; }
 const int32 Pct = Target.IsValid() ? FMath::RoundToInt(Target->GetResonanceNormalized() * 100.f) : 0;
 StatusText = FString::Printf(TEXT("LOCK  /  Resonance %d%%  /  F scythe, TAB phrase."), Pct);
 BeginLockStep(MelodiaReadActor(ATS, TEXT("GetCurrentTarget")));
}
void UMelodiaWaveHarpCombatComponent::BeginLockStep(AActor* LockActor)
{
 if (!LockActor || !Character.IsValid() || !Character->GetMesh()) return;
 const float Dist = FVector::Dist2D(Character->GetActorLocation(), LockActor->GetActorLocation());
 if (Dist < MeleeReachCm * 0.85f || Dist > 1200.f) return;
 UActorComponent* Warp = MelodiaFindComponent(Character.Get(), TEXT("/Script/MotionWarping.MotionWarpingComponent"));
 UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance();
 UAnimSequence* Seq = LockStepAnim.LoadSynchronous();
 UClass* WarpNotifyClass = FindObject<UClass>(nullptr, TEXT("/Script/MotionWarping.AnimNotifyState_MotionWarping"));
 UClass* SkewClass = FindObject<UClass>(nullptr, TEXT("/Script/MotionWarping.RootMotionModifier_SkewWarp"));
 if (!Warp || !Anim || !Seq || !WarpNotifyClass || !SkewClass) return;
 const FVector Dir = (LockActor->GetActorLocation() - Character->GetActorLocation()).GetSafeNormal2D();
 if (Dir.IsNearlyZero()) return;
 const FVector Dest = LockActor->GetActorLocation() - Dir * (MeleeReachCm * 0.55f);
 const FVector WarpPoint(Dest.X, Dest.Y, Character->GetActorLocation().Z);
 MelodiaWriteNameAndVector(Warp, TEXT("AddOrUpdateWarpTargetFromLocation"), LockWarpTarget, WarpPoint);
 UAnimMontage* Montage = MakeSlotMontage(Seq, 0.2f);
 if (!Montage) return;
 UAnimNotifyState* State = NewObject<UAnimNotifyState>(Montage, WarpNotifyClass);
 UObject* Modifier = NewObject<UObject>(Montage, SkewClass);
 if (FNameProperty* NameProp = FindFProperty<FNameProperty>(SkewClass, TEXT("WarpTargetName")))
  NameProp->SetPropertyValue_InContainer(Modifier, LockWarpTarget);
 if (FBoolProperty* Translate = FindFProperty<FBoolProperty>(SkewClass, TEXT("bWarpTranslation")))
  Translate->SetPropertyValue_InContainer(Modifier, true);
 if (FBoolProperty* IgnoreZ = FindFProperty<FBoolProperty>(SkewClass, TEXT("bIgnoreZAxis")))
  IgnoreZ->SetPropertyValue_InContainer(Modifier, true);
 if (FObjectProperty* ModifierProp = FindFProperty<FObjectProperty>(WarpNotifyClass, TEXT("RootMotionModifier")))
  ModifierProp->SetObjectPropertyValue_InContainer(State, Modifier);
 FAnimNotifyEvent& Event = Montage->Notifies.AddDefaulted_GetRef();
 Event.NotifyStateClass = State;
 Event.NotifyName = TEXT("MotionWarping");
 Event.Link(Montage, 0.05f, 0);
 Event.SetDuration(0.4f);
 Event.TriggerWeightThreshold = 0.f;
 Event.NotifyTriggerChance = 1.f;
 Event.MontageTickType = EMontageNotifyTickType::Queued;
 Event.bTriggerOnDedicatedServer = true;
 Montage->RefreshCacheData();
 if (!bRootMotionOverridden)
 {
  SavedRootMotionMode = Anim->RootMotionMode;
  bRootMotionOverridden = true;
 }
 Anim->RootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;
 WarpMontage = Montage;
 Anim->Montage_Play(Montage, 1.f);
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_LOCK_STEP dist=%.1f dest=%s"), Dist, *Dest.ToCompactString());
}
void UMelodiaWaveHarpCombatComponent::EnsureCameraBoom()
{
 if (CameraBoom.IsValid() || !Character.IsValid()) return;
 TInlineComponentArray<UCameraComponent*> Cameras(Character.Get());
 for (UCameraComponent* Camera : Cameras)
 {
  if (!Camera->IsActive()) continue;
  CameraBoom = Cast<USpringArmComponent>(Camera->GetAttachParent());
  if (CameraBoom.IsValid()) break;
 }
 if (CameraBoom.IsValid())
 {
  SavedArmLength = CameraBoom->TargetArmLength;
  SavedSocketOffset = CameraBoom->SocketOffset;
 }
}
void UMelodiaWaveHarpCombatComponent::UpdateSequenceFeel(float Delta)
{
 if (!Character.IsValid()) return;
 UCharacterMovementComponent* Move = Character->GetCharacterMovement();
 if (Move)
 {
  if (IsInSequence())
  {
   if (!bHaveSavedWalkSpeed)
   {
    SavedMaxWalkSpeed = Move->MaxWalkSpeed;
    bHaveSavedWalkSpeed = true;
    SequenceDampAlpha = 0.f;
   }
   SequenceDampAlpha = FMath::FInterpConstantTo(SequenceDampAlpha, 1.f, Delta, 5.f);
   Move->MaxWalkSpeed = FMath::Lerp(SavedMaxWalkSpeed, SavedMaxWalkSpeed * 0.12f, SequenceDampAlpha);
   bSuppressingMovement = true;
  }
  else if (bHaveSavedWalkSpeed)
  {
   SequenceDampAlpha = FMath::FInterpConstantTo(SequenceDampAlpha, 0.f, Delta, 5.f);
   Move->MaxWalkSpeed = FMath::Lerp(SavedMaxWalkSpeed, SavedMaxWalkSpeed * 0.12f, SequenceDampAlpha);
   if (SequenceDampAlpha <= 0.02f)
   {
    Move->MaxWalkSpeed = SavedMaxWalkSpeed;
    bHaveSavedWalkSpeed = false;
    bSuppressingMovement = false;
   }
  }
 }
 if (bRootMotionOverridden && Character->GetMesh())
 {
  if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
  {
   const bool bPlaying = WarpMontage && Anim->Montage_IsPlaying(WarpMontage);
   if (bPlaying && Anim->Montage_GetPosition(WarpMontage) > 0.5f) Anim->Montage_Stop(0.2f, WarpMontage);
   else if (!bPlaying)
   {
    Anim->RootMotionMode = SavedRootMotionMode;
    bRootMotionOverridden = false;
    WarpMontage = nullptr;
   }
  }
 }
 if (!IsInSequence() || !Player.IsValid() || !Target.IsValid() || !Target->GetOwner()) return;
 EnsureCameraBoom();
 FVector Eye; FRotator View;
 Player->GetPlayerViewPoint(Eye, View);
 const FVector Focus = Target->GetOwner()->GetActorLocation() + FVector(0, 0, 50);
 const FRotator Desired = (Focus - Eye).Rotation();
 Player->SetControlRotation(FMath::RInterpTo(Player->GetControlRotation(), Desired, Delta, 2.5f));
}
void UMelodiaWaveHarpCombatComponent::UpdateLockTurn(float Delta)
{
 if (!bCombatLocked || IsInSequence() || bAiming || !Target.IsValid() || !Target->GetOwner() || !Character.IsValid()) return;
 if (Character->GetVelocity().Size2D() > 30.f) return;
 const FVector To = Target->GetOwner()->GetActorLocation() - Character->GetActorLocation();
 const float DeltaYaw = FMath::FindDeltaAngleDegrees(Character->GetActorRotation().Yaw, To.Rotation().Yaw);
 if (FMath::Abs(DeltaYaw) < 45.f) return;
 const float Step = FMath::Clamp(DeltaYaw, -240.f * Delta, 240.f * Delta);
 Character->SetActorRotation(FRotator(0.f, Character->GetActorRotation().Yaw + Step, 0.f));
}
void UMelodiaWaveHarpCombatComponent::UpdateScytheRibbon()
{
 if (!ScytheRibbon) return;
 const bool bShow = Instrument && ScytheMontageFraction >= 0.f
  && Instrument->DoesSocketExist(ScytheBladeStartSocket)
  && Instrument->DoesSocketExist(ScytheBladeTipSocket);
 ScytheRibbon->SetVisibility(bShow);
 if (!bShow) return;
 const FTransform Inv = ScytheRibbon->GetComponentTransform().Inverse();
 const FVector A = Inv.TransformPosition(Instrument->GetSocketLocation(ScytheBladeStartSocket));
 const FVector B = Inv.TransformPosition(Instrument->GetSocketLocation(ScytheBladeTipSocket));
 FVector Dir = B - A;
 const float Len = Dir.Size();
 if (Len < 1.f) return;
 Dir /= Len;
 FVector Side = FVector::CrossProduct(Dir, FVector::UpVector);
 if (Side.SizeSquared() < 0.01f) Side = FVector::CrossProduct(Dir, FVector::RightVector);
 Side = Side.GetSafeNormal() * 3.f;
 const FVector N = FVector::CrossProduct(Dir, Side).GetSafeNormal();
 TArray<FVector> V = {A - Side, A + Side, B + Side, B - Side};
 TArray<int32> Tri = {0, 2, 1, 0, 3, 2};
 TArray<FVector> Normals = {N, N, N, N};
 TArray<FVector2D> UV = {{0.f, 0.f}, {0.f, 1.f}, {1.f, 1.f}, {1.f, 0.f}};
 const FLinearColor Pearl(0.85f, 0.75f, 1.f, 1.f);
 const FLinearColor Gold(1.f, 0.9f, 0.7f, 1.f);
 TArray<FLinearColor> Colors = {Pearl, Pearl, Gold, Gold};
 TArray<FProcMeshTangent> Tangents;
 Tangents.Init(FProcMeshTangent(Dir, false), 4);
 if (!bRibbonSection)
 {
  ScytheRibbon->CreateMeshSection_LinearColor(0, V, Tri, Normals, UV, Colors, Tangents, false);
  bRibbonSection = true;
 }
 else ScytheRibbon->UpdateMeshSection_LinearColor(0, V, Normals, UV, Colors, Tangents);
}
