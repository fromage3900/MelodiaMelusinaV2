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
#include "Net/UnrealNetwork.h"
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
#include "GameplayTagContainer.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "Sound/SoundBase.h"

 // ---------------------------------------------------------------------------
 // FLOW DODGE. The dodge is a real ACFU action ability, not a second custom move:
 // it runs inside UACFAbilitySystemComponent (GAS ASC: montage lifecycle, priority,
 // ability buffering, cooldown). Same law as the scythe swing - BS_GodFile does NOT
 // link ActionsSystem, the ACFU surface is located by class path and driven through
 // ProcessEvent. Damage never lives here: the counter resolves through the one
 // ResolveWorldFlowAttack authority, and the rhythm is judged at the PRESS.
 namespace MelodiaFlowDodge
 {
  UE_DEFINE_GAMEPLAY_TAG_STATIC(DodgeAbilityTag, "Actions.Melodia.Dodge");
  // Mirrors ACFU's EActionPriority: ENone 0 / ELow 1 / EMedium 2 / EHigh 3 / EHighest 4.
  constexpr uint8 EvasionPriority = 3;
 }

 namespace MelodiaACFReflect
 {
  /** Set one UFunction parameter by reflection name into an allocated params buffer.
   *  Name/offset driven, never a hand-copied layout, so ACFU class drift fails loudly. */
  static bool SetParam(UFunction* Fn, void* Params, const TCHAR* Name, const void* Value)
  {
   for (FFieldIterator It(Fn); It; ++It)
   {
    if (FProperty* Prop = CastField<FProperty>(*It))
    {
     if (Prop->GetFName() == FName(Name))
     {
      // Engine API takes non-const source; the copy itself is read-only on it.
      Prop->CopyCompleteValue(Prop->ContainerPtrToValuePtr<void>(Params), const_cast<void*>(Value));
      return true;
     }
    }
   }
   return false;
  }

  static bool GetBoolParam(UFunction* Fn, void* Params, const TCHAR* Name)
  {
   for (FFieldIterator It(Fn); It; ++It)
   {
    if (FBoolProperty* B = CastField<FBoolProperty>(*It))
     if (B->GetFName() == FName(Name))
      return B->GetPropertyValue(B->ContainerPtrToValuePtr<void>(Params));
   }
   return false;
  }

  /** GAS's InitializeAbilitySystem is static and positional-safe (ASC, Owner, Avatar):
   *  fill the object parameters in declaration order without assuming names. */
  static void FillObjectParamsInOrder(UFunction* Fn, void* Params, UObject* A, UObject* B, UObject* C)
  {
   int32 Slot = 0;
   for (FFieldIterator It(Fn); It; ++It)
   {
    FObjectProperty* Op = CastField<FObjectProperty>(*It);
    if (!Op || Op->GetFName() == FName("ReturnValue")) continue;
    UObject* Val = Slot == 0 ? A : (Slot == 1 ? B : C);
    Op->CopyCompleteValue(Op->ContainerPtrToValuePtr<void>(Params), &Val);
    ++Slot;
   }
  }

  static void InitGASAvatar(UObject* AbilityComponent, AActor* OwnerActor)
  {
   UClass* Library = FindObject<UClass>(nullptr, TEXT("/Script/GameplayAbilities.AbilitySystemBlueprintLibrary"));
   UFunction* Fn = Library ? Library->FindFunction(FName("InitializeAbilitySystem")) : nullptr;
   if (!Fn) return;
   TArray<uint8> Buffer;
   Buffer.SetNumZeroed(FMath::Max(Fn->GetStructureSize(), 1));
   void* Params = Buffer.GetData();
   FillObjectParamsInOrder(Fn, Params, AbilityComponent, OwnerActor, OwnerActor);
   Library->GetDefaultObject()->ProcessEvent(Fn, Params);
  }

  static bool CallTriggerAction(UObject* AbilityComponent, const FGameplayTag& AbilityTag, uint8 Priority, bool bCanBeStored)
  {
   UFunction* Fn = AbilityComponent ? AbilityComponent->FindFunction(FName("TriggerAction")) : nullptr;
   if (!Fn) return false;
   TArray<uint8> Buffer;
   Buffer.SetNumZeroed(FMath::Max(Fn->GetStructureSize(), 1));
   void* Params = Buffer.GetData();
   // Names verified from ActionsSystem/Public/Components/ACFAbilitySystemComponent.h line 48.
   SetParam(Fn, Params, TEXT("abilityTag"), &AbilityTag);
   SetParam(Fn, Params, TEXT("Priority"), &Priority);
   SetParam(Fn, Params, TEXT("bCanBeStored"), &bCanBeStored);
   AbilityComponent->ProcessEvent(Fn, Params);
   return GetBoolParam(Fn, Params, TEXT("ReturnValue"));
  }
 }

UMelodiaWaveHarpCombatComponent::UMelodiaWaveHarpCombatComponent()
{
 PrimaryComponentTick.bCanEverTick = true;
 SetIsReplicatedByDefault(true);
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
 // The refined wand (shaft + Carillon head). It is the head-swap carrier: a form
 // change swaps the MESH, never a morph bake. Both wand meshes are loaded up front
 // so the swap never hitches, and the component stays hidden until the owner turns
 // the head-swap path on.
 if (UStaticMesh* WandMesh = WandCasterMesh.LoadSynchronous())
 {
  Wand = NewObject<UStaticMeshComponent>(GetOwner(), TEXT("WaveHarpWandPresentation"));
  Wand->SetStaticMesh(WandMesh);
  Wand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  Wand->SetupAttachment(Character->GetRootComponent());
  Wand->RegisterComponent();
  Wand->SetVisibility(false);
  WandMeleeMesh.LoadSynchronous();
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
 if (bEnableWaterChorus && GetWorld())
 {
  WaterChorus.Start(*GetWorld());
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHORUS enabled"));
 }
}
void UMelodiaWaveHarpCombatComponent::CalibrateHold()
{
 if (!Character.IsValid()) return;
 USkeletalMeshComponent* Mesh = Character->GetMesh();
 if (!Mesh) return;
 // The socket lives on the hand bone, so the grip offset is expressed in the hand's
 // frame. Measure that frame at this (settled) pose and solve the offset that stands the
 // instrument up in the BODY's frame:
 //     Grip * Socket = Target   =>   Grip = Target * Socket^-1
 // Target maps weapon +Z -> body up and weapon +Y -> body forward, so the bow's belly
 // still faces the aim direction and the scythe's blade still sweeps forward.
 const FQuat Socket = Mesh->GetSocketTransform(InstrumentSocket, RTS_Component).GetRotation();
 const FQuat TargetRot = FQuat(FRotator(0.f, -90.f, 0.f));
 const FQuat Grip = TargetRot * Socket.Inverse();
 BowGrip.SetRotation(Grip);
 // Each form keeps its own solved hold: the three heads sit at different points on the
 // shaft, so one grip cannot hold three heads (C8).
 FormGrips.Add(CurrentForm, BowGrip);
 bHoldCalibrated = true;
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP hold calibrated: socket=%s grip=%s"),
  *Socket.ToString(), *Grip.ToString());
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
 if (Wand) Wand->DestroyComponent();
 WaterChorus.Stop();
 if (auto* UI = UMelodiaUIBridgeSubsystem::Get(this)) UI->ReleaseWorldCombatUI();
 Super::EndPlay(Reason);
}
void UMelodiaWaveHarpCombatComponent::TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Tick)
{
 Super::TickComponent(Delta, Type, Tick);
 if (!Character.IsValid()) return;
 // Hold calibration runs for every pawn (not only the locally controlled one) and before
 // the instrument is placed this tick.
 if (bGripFollowsCharacter && bAutoCalibrateHold && !bHoldCalibrated)
 {
  if (USkeletalMeshComponent* Mesh = Character->GetMesh())
  {
   if (Mesh->GetAnimInstance())
   {
    const FQuat Socket = Mesh->GetSocketTransform(InstrumentSocket, RTS_Component).GetRotation();
    const float Drift = FMath::Abs((Socket * LastSocketRotation.Inverse()).GetAngle());
    PoseStabilityTicks = (Drift < 0.01f) ? (PoseStabilityTicks + 1) : 0;
    LastSocketRotation = Socket;
    if (PoseStabilityTicks >= 2)
    {
     CalibrateHold();
    }
   }
  }
 }
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
 UpdateFormTransition(Delta);
 UpdateInstruments(Delta);
 if (bEnableWaterChorus) WaterChorus.Tick(Delta, Character.Get());
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
 Input->BindKey(EKeys::G, IE_Pressed, this, &ThisClass::TriggerDodge);
 // R cycles the form. It is a deliberate press: the ring advances one step and the
 // flourish takes over from there.
 Input->BindKey(EKeys::R, IE_Pressed, this, &ThisClass::CycleForm);
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
 bool bBuffered = false;
 if (!AcceptAttackDuringTransition(bFormTransitionActive, bBufferAttacksDuringFormChange, bBuffered))
 {
  bBufferedAttack = bBuffered;
  StatusText = bBuffered
   ? TEXT("FORM  /  Attack queued behind the transformation.")
   : TEXT("FORM  /  Transforming.");
  return;
 }
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
  if (bEnableWaterChorus) WaterChorus.Splash(Bell->GetActorLocation(), 1.f);
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
  if (bEnableWaterChorus) WaterChorus.Splash(Other->GetActorLocation(), Ring);
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
 bool bBuffered = false;
 if (!AcceptAttackDuringTransition(bFormTransitionActive, bBufferAttacksDuringFormChange, bBuffered))
 {
  // The flourish must never eat an input: remember the swing and fire it the moment
  // the transformation lands.
  bBufferedMelee = bBuffered;
  StatusText = bBuffered
   ? TEXT("FORM  /  Swing queued behind the transformation.")
   : TEXT("FORM  /  Transforming.");
  return;
 }
 if (!CanAct() || !GetWorld() || bScytheHitArmed || bScytheResolveQueued) return;
 // The rhythm is judged at the ACTION - the swing's start - never at impact. The arrow
 // samples its phase at launch; the melee must judge the same way.
 ScytheActionBeatPhase = SampleBeatPhase();
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

// ---------------------------------------------------------------------------
// FLOW DODGE - the action is ACFU's; the judgement and the counter are Melodia's.
// ---------------------------------------------------------------------------
bool UMelodiaWaveHarpCombatComponent::IsWithinDodgeCounterWindow(const double Now, const double DodgeStartedAt, const float WindowSeconds)
{
 // World-free so the committed harness can gate it: the counter lives strictly inside
 // the dodge's own span. A never-taken dodge (-100 sentinel) can never answer an attack.
 if (DodgeStartedAt <= -50.) return false;
 return Now >= DodgeStartedAt && Now - DodgeStartedAt <= FMath::Max(WindowSeconds, 0.f);
}

UObject* UMelodiaWaveHarpCombatComponent::ResolveACFAbilityComponent()
{
 if (ACFAbilityComponent.IsValid()) return ACFAbilityComponent.Get();
 AActor* Owner = GetOwner();
 if (!Owner) return nullptr;
 // Reflection law (same as the ACM swipe): the class is located by path, never linked.
 UClass* AbilityClass = FindObject<UClass>(nullptr, TEXT("/Script/ActionsSystem.ACFAbilitySystemComponent"));
 UActorComponent* Comp = AbilityClass ? Owner->FindComponentByClass(AbilityClass) : nullptr;
 if (!Comp) return nullptr;
 if (!bACFGASAvatarInitAttempted)
 {
  // The canonical pawn is not an ACF character by owner canon - it wears components.
  // GAS still needs its avatar bound before any ability can activate; the BlueprintCallable
  // library does exactly that, once, without a GameplayAbilities link here.
  bACFGASAvatarInitAttempted = true;
  MelodiaACFReflect::InitGASAvatar(Comp, Owner);
 }
 ACFAbilityComponent = Comp;
 return Comp;
}

void UMelodiaWaveHarpCombatComponent::TriggerDodge()
{
 if (!CanAct() || !GetWorld()) return; // FLOW only: CanAct already refuses Sequence and remote.
 UObject* AbilityComponent = ResolveACFAbilityComponent();
 if (!AbilityComponent)
 {
  UE_LOG(LogTemp, Display, TEXT("MELODIA_HYBRID_DODGE acf=missing pawn=%s"), *GetNameSafe(GetOwner()));
  StatusText = TEXT("FLOW  /  ACFU ability component not on the pawn.");
  return;
 }
 // The rhythm is judged at the ACTION - the dodge press - the same law as the arrow's
 // release and the swing's start. Never at landing, never at recovery.
 DodgeActionBeatPhase = SampleBeatPhase();
 LastDodgeStart = GetWorld()->GetTimeSeconds();
 // bCanBeStored=true: ACFU's own action buffering, so a dodge pressed mid-montage is
 // not eaten - it fires the moment the lane clears. This is the plugin's input-buffer,
 // not a second one of ours.
 const bool bTriggered = MelodiaACFReflect::CallTriggerAction(AbilityComponent,
  MelodiaFlowDodge::DodgeAbilityTag.GetTag(), MelodiaFlowDodge::EvasionPriority, true);
 UE_LOG(LogTemp, Display, TEXT("MELODIA_HYBRID_DODGE phase=%.3f window=%.2f triggered=%d"),
  DodgeActionBeatPhase, DodgeCounterWindow, bTriggered ? 1 : 0);
 if (!bTriggered)
  StatusText = TEXT("DODGE  /  Action refused (cooldown or locked state).");
}

bool UMelodiaWaveHarpCombatComponent::NotifyDodgedAttack(AActor* Attacker)
{
 // The FLOW reward for a correct dodge: the attacker's hit was intercepted inside the
 // dodge's window, so the answer is ONE counter through the single FLOW damage
 // authority - exactly like an arrow release or a swing start. No new damage math.
 if (!GetWorld() || !IsValid(Attacker)) return false;
 if (!IsWithinDodgeCounterWindow(GetWorld()->GetTimeSeconds(), LastDodgeStart, DodgeCounterWindow))
  return false;
 auto* Encounter = Attacker->FindComponentByClass<UMelodiaHybridEncounterComponent>();
 if (!Encounter) return false;
 auto* Bridge = UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(GetWorld()->GetGameInstance());
 const bool bResolved = Bridge && Bridge->ResolveWorldFlowAttack(Encounter, DodgeActionBeatPhase);
 UE_LOG(LogTemp, Display, TEXT("MELODIA_HYBRID_DODGE_COUNTER attacker=%s phase=%.3f resolved=%d"),
  *GetNameSafe(Attacker), DodgeActionBeatPhase, bResolved ? 1 : 0);
 if (bResolved)
 {
  // The window is spent: one dodge answers at most one attack, and it cannot be
  // farmed by repeated calls (idempotency law, Issue #51).
  LastDodgeStart = -100.;
  DodgeActionBeatPhase = -1.f;
  UMelodiaCymaticFieldComponent::BroadcastHit(GetWorld(), Attacker->GetActorLocation(), 1.f);
  if (auto* Audio = GetWorld()->GetGameInstance()->GetSubsystem<UMelodiaAudioReactivePresentationSubsystem>())
   Audio->PulseImpact(1.f);
  StatusText = FString::Printf(TEXT("DODGE COUNTER  /  Resonance %d%%"),
   FMath::RoundToInt(Encounter->GetResonanceNormalized() * 100.f));
 }
 return bResolved;
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
 // A running form change owns the upper body: the flourish must not be interrupted by
 // the stance or cast pose.
 if (bFormTransitionActive) return;
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
 // The committed form is a second axis on top of the caster/archer hybrid: while the
 // crescent form is live the astrolabe/bow blend stands down so the two never fight.
 const float MeleeForm = GetMeleeFormWeight();
 const bool bScytheForm = bScytheMontage || ScytheAlpha > 0.02f || MeleeForm > 0.02f;
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
  ScytheMontageAlpha = DesiredScythe;
 }
 else ScytheMontageAlpha = FMath::FInterpConstantTo(ScytheMontageAlpha, 0.f, Delta, 1.f / FMath::Max(TransformSeconds, .05f));
 // The crescent unfolds with the committed form (eased by the transition) and with the
 // melee swing clip (the shipped path). Whichever asks for more of it wins.
 ScytheAlpha = FMath::Max(ScytheMontageAlpha, MeleeForm);
 const float HandAlpha = FMath::Max(FormAlpha, ScytheAlpha);
 const float Tension = GetDrawTension();
 const FVector Float = AstrolabeOffset + FVector(0, 0, AstrolabeBobCm * FMath::Sin(Now * 2.0));
 const float Spin = FMath::Fmod(Now * AstrolabeSpinDegPerSecond, 360.0);
 // One placement for every representation of the instrument: the refined wand and the
 // shipped skeletal mesh stand in the same place, so a form change never moves the
 // hold.
 const FTransform Actor = Character->GetActorTransform();
 FTransform Astro(Actor.GetRotation() * FQuat(FRotator(0, Spin, 0)), Actor.TransformPosition(Float), HarpGrip.GetScale3D());
 FTransform InHand = BowGrip;
 if (USkeletalMeshComponent* Mesh = Character->GetMesh())
 {
  if (bGripFollowsCharacter)
  {
   // Compose the grip offset in the body's frame: the socket relative to the mesh,
   // then the mesh's world transform. A world-space grip offset drifts as the
   // character turns; this keeps the hold locked to her hand and arm, which is what
   // the InstrumentSocket contract already claims.
   InHand = BowGrip * Mesh->GetSocketTransform(InstrumentSocket, RTS_Component) * Mesh->GetComponentTransform();
  }
  else
  {
   InHand = BowGrip * Mesh->GetSocketTransform(InstrumentSocket);
  }
 }
 FTransform Out;
 Out.Blend(Astro, InHand, HandAlpha);
 if (Wand)
 {
  // The wand's origin sits 13 cm below its grip point, so the grip correction is
  // applied in the wand's own local space.
  Wand->SetWorldTransform(Out * FTransform(FQuat::Identity, -Sockets.BowGrip));
  Wand->SetVisibility(bUseHeadSwap);
 }
 if (Instrument)
 {
  Instrument->SetWorldTransform(Out);
  UpdateIdleShimmer();
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
  Harp->SetVisibility(!bUseHeadSwap && FormAlpha < .98f);
 }
 if (Bow)
 {
  Bow->SetRelativeScale3D(BowGrip.GetScale3D() * FormAlpha);
  Bow->SetVisibility(!bUseHeadSwap && FormAlpha > .02f);
 }
}
void UAnimNotify_MelodiaScytheHit::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
 if (!MeshComp || !MeshComp->GetOwner()) return;
 if (UMelodiaWaveHarpCombatComponent* Combat = MeshComp->GetOwner()->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
  Combat->CommitScytheHit();
}
void UMelodiaWaveHarpCombatComponent::SetMorphIfPresent(FName Morph, float Value)
{
 if (!Instrument || Morph.IsNone()) return;
 // A morph the shipped mesh does not carry is skipped, not asserted: the source rig
 // names more shimmer curves than the UE mesh exposes.
 if (Instrument->GetMorphTarget(Morph)) Instrument->SetMorphTarget(Morph, Value);
}

float UMelodiaWaveHarpCombatComponent::GetEffectScale() const
{
 // The effect budget follows what the player can actually see (the reference scales
 // its fur layers by screen size): a flourish seen from across the lane is restrained,
 // one seen from arm's length is full size.
 if (!Player.IsValid() || !Character.IsValid()) return 1.f;
 FVector Eye; FRotator View;
 Player->GetPlayerViewPoint(Eye, View);
 const float Distance = FVector::Distance(Eye, Character->GetActorLocation());
 return FMath::Clamp(1.2f - 0.02f * Distance, 0.4f, 1.2f);
}

void UMelodiaWaveHarpCombatComponent::UpdateIdleShimmer()
{
 if (!Instrument) return;
 const float Phase = UMelodiaMusicClockSubsystem::GetMusicBeatPhase(this);
 if (Phase < 0.f) return; // no music: the instrument holds still rather than faking it
 const float Pulse = UMelodiaMusicClockSubsystem::GetMusicPulse(this);
 const float Breath = 0.5f + 0.5f * FMath::Cos(Phase * 2.f * PI);
 const float Sway = FMath::Sin(Phase * 2.f * PI);
 const float Strength = FMath::Clamp(ShimmerStrength, 0.f, 1.f);
 SetMorphIfPresent(MorphShimmerPluck, Breath * 0.30f * Strength);
 SetMorphIfPresent(MorphShimmerVibrate, Pulse * 0.45f * Strength);
 SetMorphIfPresent(MorphShimmerSwayPos, FMath::Max(0.f, Sway) * 0.35f * Strength);
 SetMorphIfPresent(MorphShimmerSwayNeg, FMath::Max(0.f, -Sway) * 0.35f * Strength);
 SetMorphIfPresent(MorphShimmerResonance, Breath * 0.40f * Strength);
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
 FVector Start = FVector::ZeroVector;
 FVector End = FVector::ZeroVector;
 bool bHaveSweep = false;
 // The crescent is measured geometry, not a skeleton socket: Blender's FBX armature
 // export lands the bones ~90-100x too far out (defect D8), which is what turned the
 // melee into a 42 m sweep. The measured head-local offsets give a ~41 cm blade with a
 // ~37 cm swing radius.
 if (GetBladeWorldPoints(Start, End))
 {
  End += Character->GetActorForwardVector() * MeleeForwardExtensionCm;
  bHaveSweep = true;
 }
 // There is deliberately NO fallback to the skeletal sockets. Blender's FBX armature
 // export lands those bones ~90-100x too far out; clamping them would still be a
 // guess. Without the measured geometry the melee simply has no blade, and the reach
 // search below is the honest fallback.
 if (bHaveSweep)
 {
  if (UClass* ACMClass = FindObject<UClass>(nullptr, TEXT("/Script/CollisionsManager.ACMCollisionManagerComponent")))
  {
   if (UActorComponent* ACM = Character->FindComponentByClass(ACMClass))
   {
    if (UFunction* Fn = ACM->FindFunction(TEXT("PerformSwipeTraceShot_Local")))
    {
     struct FSwipeParams { FVector S; FVector E; float R; FHitResult Hit; bool bRet; };
     FSwipeParams P{Start, End, MeleeSweepRadiusCm, FHitResult(), false};
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
  if (GetWorld()->SweepSingleByChannel(SweepHit, Start, End, FQuat::Identity, ECC_WorldDynamic, FCollisionShape::MakeSphere(MeleeSweepRadiusCm), Query))
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
 // Judged at the action, not at impact. The action phase was sampled when the swing
 // started; fall back to the notify only if the swing never sampled one.
 ScytheSwingBeatPhase = ScytheActionBeatPhase >= 0.f ? ScytheActionBeatPhase : SampleBeatPhase();
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
 // The trail follows the MEASURED crescent, like the sweep does. Reading the shipped
 // skeleton sockets here drew a 42 m ribbon (defect D8).
 FVector BladeStart = FVector::ZeroVector;
 FVector BladeEnd = FVector::ZeroVector;
 const bool bBlade = GetBladeWorldPoints(BladeStart, BladeEnd);
 const bool bShow = bBlade && ScytheMontageFraction >= 0.f;
 ScytheRibbon->SetVisibility(bShow);
 if (!bShow) return;
 const FTransform Inv = ScytheRibbon->GetComponentTransform().Inverse();
 const FVector A = Inv.TransformPosition(BladeStart);
 const FVector B = Inv.TransformPosition(BladeEnd);
 FVector Dir = B - A;
 const float Len = Dir.Size();
 if (Len < 1.f) return;
 Dir /= Len;
 FVector Side = FVector::CrossProduct(Dir, FVector::UpVector);
 if (Side.SizeSquared() < 0.01f) Side = FVector::CrossProduct(Dir, FVector::RightVector);
 // The ribbon follows the screen-size budget like everything else.
 Side = Side.GetSafeNormal() * (3.f * GetEffectScale());
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

// ---------------------------------------------------------------------------
// THE FORM: one type, one entry point, one writer.
//
// SetForm is the only writer of CurrentForm. The f90 FormHandoff notify confirms a
// transition; it never starts one. This mirrors the single-writer rule the hybrid
// combat canon already applies to damage, resonance and the HUD.
// ---------------------------------------------------------------------------
namespace
{
const TCHAR* MelodiaFormName(EMelodiaWaveHarpForm Form)
{
 switch (Form)
 {
 case EMelodiaWaveHarpForm::Harp: return TEXT("HARP");
 case EMelodiaWaveHarpForm::Bow: return TEXT("BOW");
 case EMelodiaWaveHarpForm::CarillonMelee: return TEXT("CARILLON");
 default: return TEXT("FORM");
 }
}
}

EMelodiaWaveHarpForm UMelodiaWaveHarpCombatComponent::GetNextForm(EMelodiaWaveHarpForm Form)
{
 switch (Form)
 {
 case EMelodiaWaveHarpForm::Harp: return EMelodiaWaveHarpForm::Bow;
 case EMelodiaWaveHarpForm::Bow: return EMelodiaWaveHarpForm::CarillonMelee;
 default: return EMelodiaWaveHarpForm::Harp;
 }
}

float UMelodiaWaveHarpCombatComponent::EaseFormTransition(float T)
{
 const float Clamped = FMath::Clamp(T, 0.f, 1.f);
 return Clamped * Clamped * (3.f - 2.f * Clamped);
}

float UMelodiaWaveHarpCombatComponent::ComputeMeleeFormWeight(
 EMelodiaWaveHarpForm From, EMelodiaWaveHarpForm To, float Alpha)
{
 const float FromWeight = From == EMelodiaWaveHarpForm::CarillonMelee ? 1.f : 0.f;
 const float ToWeight = To == EMelodiaWaveHarpForm::CarillonMelee ? 1.f : 0.f;
 return FMath::Lerp(FromWeight, ToWeight, FMath::Clamp(Alpha, 0.f, 1.f));
}

float UMelodiaWaveHarpCombatComponent::ComputeBeatLockDelay(
 const float SecondsToNextBeat, const float TransitionSeconds)
{
 // The flourish lasts TransitionSeconds and the head swaps at its midpoint, so the
 // START is delayed by half a transition less than the distance to the next downbeat.
 const float Half = 0.5f * FMath::Max(TransitionSeconds, 0.2f);
 return FMath::Max(0.f, SecondsToNextBeat - Half);
}

bool UMelodiaWaveHarpCombatComponent::AcceptAttackDuringTransition(
 const bool bTransitionActive, const bool bBufferEnabled, bool& bOutBuffered)
{
 bOutBuffered = false;
 if (!bTransitionActive) return true;
 bOutBuffered = bBufferEnabled;
 return false;
}

bool UMelodiaWaveHarpCombatComponent::SetForm(EMelodiaWaveHarpForm NewForm)
{
 if (!Character.IsValid() || !GetWorld()) return false;
 if (bFormTransitionActive)
 {
  // One transition at a time. A new request re-aims the running flourish instead of
  // starting a second one.
  if (NewForm == PendingForm) return false;
  PendingForm = NewForm;
  StatusText = TEXT("FORM  /  Re-aimed behind the running transformation.");
  return true;
 }
 if (NewForm == CurrentForm) return false;
 if (IsInSequence())
 {
  StatusText = TEXT("FORM  /  Not during a phrase.");
  return false;
 }
 if (!CanAct())
 {
  StatusText = TEXT("FORM  /  Movement is locked.");
  return false;
 }

 FormTransitionFrom = CurrentForm;
 PendingForm = NewForm;
 bFormTransitionActive = true;
 bHeadSwappedThisTransition = false;
 // Every transition gets its beats: the fired-marker is cleared with the transition.
 LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
 FormTransitionAlpha = 0.f;

 // Beat lock: the flourish's HANDOFF must land on a downbeat. The head swaps at the
 // transition's midpoint, so the start waits for (beat distance - half a transition).
 // The music clock returns 0 when there is no music, which degrades to acting at once.
 const float Delay = ComputeBeatLockDelay(SecondsUntilNextBeat(), FormTransitionSeconds);
 const double Now = GetWorld()->GetTimeSeconds();
 FormTransitionStart = Now + FMath::Max(0.f, Delay);
 FormTransitionEnd = FormTransitionStart + FMath::Max(FormTransitionSeconds, .2f);

 ApplyFormCameraPush(true);
 PlayFormTransformFlourish();

 // The authored henshin montage drives the transition when it exists: its FormAlpha
 // curve replaces the timer (defect D3, the 0.22 s linear pop).
 if (UAnimMontage* Montage = FormTransitionMontage.LoadSynchronous())
 {
  if (Character->GetMesh())
   if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
   {
    Anim->Montage_Play(Montage, 1.f);
    PoseMontage = Montage;
   }
 }

 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_FORM from=%s to=%s delay=%.3f duration=%.3f"),
  MelodiaFormName(FormTransitionFrom), MelodiaFormName(NewForm), FMath::Max(0.f, Delay),
  FMath::Max(FormTransitionEnd - FormTransitionStart, 0.f));
 StatusText = FString::Printf(TEXT("FORM  /  %s"), MelodiaFormName(NewForm));
 return true;
}

void UMelodiaWaveHarpCombatComponent::CycleForm()
{
 SetForm(GetNextForm(CurrentForm));
}

float UMelodiaWaveHarpCombatComponent::GetMeleeFormWeight() const
{
 if (!bFormTransitionActive)
  return CurrentForm == EMelodiaWaveHarpForm::CarillonMelee ? 1.f : 0.f;
 return ComputeMeleeFormWeight(FormTransitionFrom, PendingForm, FormTransitionAlpha);
}

void UMelodiaWaveHarpCombatComponent::UpdateFormTransition(float Delta)
{
 if (!bFormTransitionActive)
 {
  FormTransitionAlpha = 1.f;
  if (FormStage != EMelodiaWaveHarpFormStage::Idle)
  {
   // The aftermath is over: the stage goes home and the beats can fire again.
   if (GetWorld() && GetWorld()->GetTimeSeconds() > AftermathUntil)
   {
    FormStage = EMelodiaWaveHarpFormStage::Idle;
    LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
    OnFormStageChanged.Broadcast(FormStage, CurrentForm);
   }
  }
  return;
 }
 if (!GetWorld()) return;
 const double Now = GetWorld()->GetTimeSeconds();
 const float Duration = FMath::Max((float)(FormTransitionEnd - FormTransitionStart), .05f);
 const float T = FMath::Clamp((float)((Now - FormTransitionStart) / Duration), 0.f, 1.f);

 // The authored clip's curve wins when it is playing (C3). Otherwise the timer drives
 // a smoothstep, so the change is never the old linear pop.
 float CurveValue = 0.f;
 bool bCurveDriven = false;
 if (FormTransitionMontage && Character.IsValid() && Character->GetMesh())
 {
  if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
   if (Anim->Montage_IsPlaying(FormTransitionMontage.Get()))
    bCurveDriven = Anim->GetCurveValueWithDefault(FormAlphaCurve, 0.f, CurveValue);
 }
 FormTransitionAlpha = bCurveDriven ? FMath::Clamp(CurveValue, 0.f, 1.f) : EaseFormTransition(T);

 // The stage machine: PREPARE while the flourish waits for its beat, TRANSFORM while
 // the head is covered and changes, AFTERMATH once the weight has to land.
 {
  const EMelodiaWaveHarpFormStage Stage = T <= 0.f
   ? EMelodiaWaveHarpFormStage::Prepare
   : (T < 1.f ? EMelodiaWaveHarpFormStage::Transform : EMelodiaWaveHarpFormStage::Aftermath);
  if (Stage != FormStage)
  {
   FormStage = Stage;
   OnFormStageChanged.Broadcast(Stage, PendingForm);
   if (Stage != LastFiredStage)
   {
    LastFiredStage = Stage;
    PlayFormVfxBeats(Stage);
   }
  }
 }

 // The head swaps at the midpoint: the caster head unfurls first, the crescent lands
 // in the second half. That is the f90 handoff of the authored performance.
 if (!bHeadSwappedThisTransition && FormTransitionAlpha >= .5f)
 {
  bHeadSwappedThisTransition = true;
  ApplyFormVisuals(true);
  PlayFormTransformFlourish();
 }

 if (T < 1.f) return;

 // The transition landed. The form is committed here and nowhere else.
 bFormTransitionActive = false;
 FormTransitionAlpha = 1.f;
 AftermathUntil = GetWorld() ? GetWorld()->GetTimeSeconds() + FMath::Max(0.f, FormAftermathSeconds) : 0;
 CurrentForm = PendingForm;
 ApplyFormVisuals();
 ApplyFormCameraPush(false);
 StatusText = FString::Printf(TEXT("FORM  /  %s"), MelodiaFormName(CurrentForm));
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_FORM_LANDED form=%s head_melee=%d"),
  MelodiaFormName(CurrentForm), bWandIsMelee ? 1 : 0);

 // A queued attack fires the moment the flourish lands: the transformation never eats
 // an input.
 if (bBufferedMelee)
 {
  bBufferedMelee = false;
  TriggerScytheMelee();
 }
 else if (bBufferedAttack)
 {
  bBufferedAttack = false;
  StartDraw();
 }
}

void UMelodiaWaveHarpCombatComponent::PlayFormVfxBeats(EMelodiaWaveHarpFormStage Stage)
{
 if (!Character.IsValid()) return;
 for (const FMelodiaWaveHarpVfxBeat& Beat : FormVfxBeats)
 {
  if (Beat.Stage != Stage) continue;
  UNiagaraSystem* System = Beat.System.LoadSynchronous();
  if (!System)
  {
   UE_LOG(LogTemp, Verbose, TEXT("MELODIA_WAVEHARP_VFX beat skipped: no system for stage %d"), (int32)Stage);
   continue;
  }
  const FVector Where = GetFormVfxLocation(Beat);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, System, Where, FRotator::ZeroRotator,
   FVector(Beat.Scale));
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_VFX stage=%d system=%s at=%s scale=%.2f"),
   (int32)Stage, *System->GetName(), *Where.ToCompactString(), Beat.Scale);
 }
}

FVector UMelodiaWaveHarpCombatComponent::GetFormVfxLocation(const FMelodiaWaveHarpVfxBeat& Beat) const
{
 if (!Character.IsValid()) return FVector::ZeroVector;
 USkeletalMeshComponent* Mesh = Character->GetMesh();
 if (Beat.Socket != NAME_None && Mesh && Mesh->DoesSocketExist(Beat.Socket))
  return Mesh->GetSocketLocation(Beat.Socket);
 // The head is the heart of the weapon: a beat with no socket plays there.
 return Character->GetActorLocation() + FVector(0.f, 0.f, 95.f);
}

void UMelodiaWaveHarpCombatComponent::SetWaterChorusEnabled(const bool bEnabled)
{
 if (bEnableWaterChorus == bEnabled) return;
 bEnableWaterChorus = bEnabled;
 if (bEnabled)
 {
  if (GetWorld()) WaterChorus.Start(*GetWorld());
  StatusText = TEXT("CHORUS  /  The water sings with the beat.");
 }
 else
 {
  WaterChorus.Stop();
  StatusText = TEXT("CHORUS  /  Off.");
 }
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHORUS_TOGGLE enabled=%d"), bEnabled ? 1 : 0);
}

void UMelodiaWaveHarpCombatComponent::SetHeadSwapEnabled(const bool bEnabled)
{
 if (bUseHeadSwap == bEnabled) return;
 bUseHeadSwap = bEnabled;
 // The wand path hides the shipped representation; turning it off puts it back.
 if (Instrument) Instrument->SetVisibility(true);
 ApplyFormVisuals();
 StatusText = bEnabled
  ? TEXT("HEAD SWAP  /  The refined Carillon wand is live.")
  : TEXT("HEAD SWAP  /  The shipped representation is live.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_HEADSWAP_TOGGLE enabled=%d"), bEnabled ? 1 : 0);
}

void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals(const bool bBurst)
{
 // The form brings its own hold with it, when it has been solved for this pose.
 if (const FTransform* Solved = FormGrips.Find(CurrentForm))
  BowGrip = *Solved;
 // The committed form decides the head. Nothing else may swap it.
 const bool bWantMelee = CurrentForm == EMelodiaWaveHarpForm::CarillonMelee
  || PendingForm == EMelodiaWaveHarpForm::CarillonMelee;
 if (Wand && bWantMelee != bWandIsMelee)
 {
  bWandIsMelee = bWantMelee;
  if (UStaticMesh* Mesh = bWantMelee ? WandMeleeMesh.LoadSynchronous() : WandCasterMesh.LoadSynchronous())
   Wand->SetStaticMesh(Mesh);
 }
 UpdateWandPresentation();
 // The water transform: the form change breaks the surface of the world. It belongs to
 // the midpoint, where the head actually changes.
 if (bBurst && bEnableWaterChorus) WaterChorus.Burst(Character.Get());
}

void UMelodiaWaveHarpCombatComponent::UpdateWandPresentation()
{
 if (!Wand) return;
 const bool bWandPath = bUseHeadSwap;
 Wand->SetVisibility(bWandPath);
 if (!bWandPath)
 {
  // The shipped representation is back.
  if (Instrument) Instrument->SetVisibility(true);
  return;
 }
 if (Instrument) Instrument->SetVisibility(false);
 if (Harp) Harp->SetVisibility(false);
 if (Bow) Bow->SetVisibility(false);
}

float UMelodiaWaveHarpCombatComponent::SecondsUntilNextBeat() const
{
 if (const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this))
  if (MusicClock->HasMusicalTime())
   return MusicClock->GetSecondsToNextBeat();
 return 0.f;
}

bool UMelodiaWaveHarpCombatComponent::GetBladeWorldPoints(FVector& OutStart, FVector& OutEnd) const
{
 if (!Character.IsValid()) return false;
 FTransform Base;
 if (Wand && Wand->IsRegistered())
 {
  // The head-local frame the crescent was modelled in.
  Base = Wand->GetComponentTransform();
 }
 else if (Instrument && Instrument->IsRegistered())
 {
  // The shipped skeletal path: the offsets are wand-local, so seat them on the head.
  Base = Instrument->GetComponentTransform() * FTransform(FQuat::Identity, Sockets.HeadSeat);
 }
 else return false;
 OutStart = Base.TransformPosition(Sockets.BladeStart);
 OutEnd = Base.TransformPosition(Sockets.BladeTip);
 return true;
}

void UMelodiaWaveHarpCombatComponent::ApplyFormCameraPush(bool bPush)
{
 if (!CameraBoom.IsValid()) return;
 if (bPush)
 {
  if (bHaveSavedFormCameraArm) return;
  SavedFormCameraArmLength = CameraBoom->TargetArmLength;
  bHaveSavedFormCameraArm = true;
  CameraBoom->TargetArmLength = SavedFormCameraArmLength - FMath::Max(0.f, FormCameraPushCm);
 }
 else if (bHaveSavedFormCameraArm)
 {
  CameraBoom->TargetArmLength = SavedFormCameraArmLength;
  bHaveSavedFormCameraArm = false;
 }
}

void UMelodiaWaveHarpCombatComponent::PlayFormTransformFlourish()
{
 // Existing systems only. The flourish covers the head swap; it never decides anything.
 if (UNiagaraSystem* System = FormTransformSigilSystem.LoadSynchronous())
 {
  const FVector Where = Character.IsValid()
   ? Character->GetActorLocation() + FVector(0, 0, 95)
   : FVector::ZeroVector;
  // The effect budget follows what the player can actually see (Infinity Nikki scale
  // their fur layers by screen size): a flourish seen from across the lane is small,
  // one seen from arm's length is full size. No new system, no new graph.
  float Scale = 1.f;
  if (Player.IsValid())
  {
   FVector Eye; FRotator View;
   Player->GetPlayerViewPoint(Eye, View);
   const float Distance = FVector::Distance(Eye, Where);
   Scale = FMath::Clamp(1.15f - 0.018f * Distance, 0.4f, 1.1f);
  }
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, System, Where, FRotator::ZeroRotator, FVector(Scale));
 }
 if (ShotNote && Character.IsValid())
  UGameplayStatics::PlaySoundAtLocation(this, ShotNote,
   Character->GetActorLocation() + FVector(0, 0, 95), .5f);
}

void UMelodiaWaveHarpCombatComponent::OnRep_CurrentForm()
{
 ApplyFormVisuals();
}

void UMelodiaWaveHarpCombatComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(UMelodiaWaveHarpCombatComponent, CurrentForm);
}

// Re-derive the WaveHarp hold offset from the current pose (local player).
static FAutoConsoleCommandWithWorld GMelodiaRecalibrateWaveHarpHold(
 TEXT("Melodia.WaveHarp.RecalibrateHold"),
 TEXT("Re-derive the WaveHarp hold offset from the current settled pose (local player)."),
 FConsoleCommandWithWorldDelegate::CreateStatic([](UWorld* World)
 {
  if (!World) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   APlayerController* PC = It->Get();
   if (PC && PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char)
  {
   UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn to recalibrate."));
   return;
  }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
  {
   Combat->CalibrateHold();
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP hold recalculated."));
  }
 }));

// Force a form (PIE proof): 0 = HARP, 1 = BOW, 2 = CARILLON (melee).
static FAutoConsoleCommandWithWorldAndArgs GMelodiaSetWaveHarpForm(
 TEXT("Melodia.WaveHarp.SetForm"),
 TEXT("Force the WaveHarp form: 0 = HARP, 1 = BOW, 2 = CARILLON (melee)."),
 FConsoleCommandWithWorldAndArgsDelegate::CreateStatic([](const TArray<FString>& Args, UWorld* World)
 {
  if (!World || Args.Num() < 1) return;
  const int32 Index = FCString::Atoi(*Args[0]);
  if (Index < 0 || Index > 2)
  {
   UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP_FORM_SET bad index %d (use 0, 1 or 2)."), Index);
   return;
  }
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
  {
   Combat->SetForm(static_cast<EMelodiaWaveHarpForm>(Index));
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_FORM_SET form=%d"), Index);
  }
 }));

// Toggle the water chorus at runtime (the surfaces must exist in the level).
static FAutoConsoleCommandWithWorldAndArgs GMelodiaWaterChorusToggle(
 TEXT("Melodia.WaveHarp.WaterChorus"),
 TEXT("Turn the world's water chorus on or off: Melodia.WaveHarp.WaterChorus 0|1"),
 FConsoleCommandWithWorldAndArgsDelegate::CreateStatic([](const TArray<FString>& Args, UWorld* World)
 {
  if (!World || Args.Num() < 1) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
   Combat->SetWaterChorusEnabled(FCString::Atoi(*Args[0]) != 0);
 }));

// Toggle the refined wand (head swap) at runtime.
static FAutoConsoleCommandWithWorldAndArgs GMelodiaHeadSwapToggle(
 TEXT("Melodia.WaveHarp.HeadSwap"),
 TEXT("Turn the refined Carillon wand on or off: Melodia.WaveHarp.HeadSwap 0|1"),
 FConsoleCommandWithWorldAndArgsDelegate::CreateStatic([](const TArray<FString>& Args, UWorld* World)
 {
  if (!World || Args.Num() < 1) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
   Combat->SetHeadSwapEnabled(FCString::Atoi(*Args[0]) != 0);
 }));

// Print the resolved form state (the PIE receipt for the form system).
static FAutoConsoleCommandWithWorld GMelodiaDumpWaveHarpForm(
 TEXT("Melodia.WaveHarp.DumpForm"),
 TEXT("Print the WaveHarp form, the transition state and the measured blade geometry."),
 FConsoleCommandWithWorldDelegate::CreateStatic([](UWorld* World)
 {
  if (!World) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
  {
   FVector Start = FVector::ZeroVector;
   FVector End = FVector::ZeroVector;
   const bool bBlade = Combat->GetBladeWorldPoints(Start, End);
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_FORM_DUMP form=%d pending=%d transition=%d alpha=%.3f head_swap=%d melee_weight=%.3f"),
    (int32)Combat->GetForm(), (int32)Combat->PendingForm, Combat->IsFormTransitionActive() ? 1 : 0,
    Combat->GetFormTransitionAlpha(), Combat->bUseHeadSwap ? 1 : 0, Combat->GetMeleeFormWeight());
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_BLADE_DUMP measured=%d blade_cm=%.2f radius_cm=%.2f start=%s end=%s reach_cm=%.2f"),
    bBlade ? 1 : 0, Combat->Sockets.GetBladeLengthCm(), Combat->Sockets.GetBladeRadiusCm(),
    *Start.ToCompactString(), *End.ToCompactString(),
    bBlade ? FVector::Distance(Start, End) : 0.f);
  }
 }));