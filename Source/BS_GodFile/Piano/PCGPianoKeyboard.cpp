#include "PCGPianoKeyboard.h"

// Live Coding reload marker: keep the actor implementation rebuildable after editor restart.

#include "Components/BoxComponent.h"
#include "Components/SplineComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "PCGComponent.h"
#include "PCGGraph.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "../PCG/MelodiaCymaticFieldComponent.h"
#include "../MelodiaIntegration/MelodiaQuantumDrawSubsystem.h"
#include "Engine/GameInstance.h"
#include "Metadata/PCGMetadata.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

APCGPianoKey::APCGPianoKey()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);

	KeyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("KeyMesh"));
	KeyMesh->SetupAttachment(SceneRoot);
	KeyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	KeyMesh->SetGenerateOverlapEvents(false);

	KeyBlocker = CreateDefaultSubobject<UBoxComponent>(TEXT("KeyBlocker"));
	// Attached to the root, not the mesh: KeyMesh is scaled to the profile dimensions and a
	// scaled parent would scale the collision box with it. Tick moves it with the key.
	KeyBlocker->SetupAttachment(SceneRoot);
	KeyBlocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	KeyBlocker->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	KeyBlocker->SetGenerateOverlapEvents(false);

	StepTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("StepTrigger"));
	StepTrigger->SetupAttachment(SceneRoot);
	StepTrigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	StepTrigger->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	StepTrigger->SetGenerateOverlapEvents(true);
	StepTrigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	StepTrigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

}

APCGPianoWhiteKey::APCGPianoWhiteKey()
{
	bIsBlackKey = false;
}

APCGPianoBlackKey::APCGPianoBlackKey()
{
	bIsBlackKey = true;
}

void APCGPianoKey::BeginPlay()
{
	Super::BeginPlay();
	// Bind only on live instances. Binding from the constructor also touches
	// the class default object during module load, before reflected UFUNCTION
	// metadata is guaranteed to be available.
	if (StepTrigger)
	{
		StepTrigger->OnComponentBeginOverlap.AddUniqueDynamic(this, &APCGPianoKey::HandleStepBegin);
		StepTrigger->OnComponentEndOverlap.AddUniqueDynamic(this, &APCGPianoKey::HandleStepEnd);
	}
	ResolveKeyboard();
	ApplyProfileGeometry();
}

void APCGPianoKey::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (KeyboardOwner.IsValid())
	{
		KeyboardOwner->UnregisterKey(this);
	}

	PressingActors.Reset();
	Super::EndPlay(EndPlayReason);
}

void APCGPianoKey::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UPCGPianoKeyboardProfile* PianoProfile = KeyboardOwner.IsValid() ? KeyboardOwner->GetProfile() : nullptr;
	const float Stiffness = PianoProfile ? FMath::Max(0.0f, PianoProfile->Dimensions.SpringStiffness) : 950.0f;
	const float Damping = PianoProfile ? FMath::Max(0.0f, PianoProfile->Dimensions.SpringDamping) : 92.0f;
	const float PressDepth = PianoProfile ? FMath::Max(0.0f, PianoProfile->Dimensions.PressDepth) : 8.0f;
	const float TargetOffset = bIsPressed ? -PressDepth : 0.0f;

	// Substep: explicit integration of a stiff spring diverges on a hitch frame (a long DeltaSeconds
	// made the offset NaN, which sent the key's collision and the pawn standing on it to infinity).
	constexpr float MaxSpringStep = 1.0f / 120.0f;
	float RemainingTime = FMath::Min(DeltaSeconds, 0.25f);
	while (RemainingTime > 0.0f)
	{
		const float Step = FMath::Min(RemainingTime, MaxSpringStep);
		const float Acceleration = ((TargetOffset - CurrentPressOffset) * Stiffness) - (PressVelocity * Damping);
		PressVelocity += Acceleration * Step;
		CurrentPressOffset += PressVelocity * Step;
		RemainingTime -= Step;
	}

	if (FMath::Abs(CurrentPressOffset - TargetOffset) < 0.01f && FMath::Abs(PressVelocity) < 0.01f)
	{
		CurrentPressOffset = TargetOffset;
		PressVelocity = 0.0f;
	}

	if (KeyMID && (ColorFlash > 0.0f || bFlashDirty))
	{
		const float FadeSec = PianoProfile ? FMath::Max(0.05f, PianoProfile->PressColorFadeSec) : 1.2f;
		ColorFlash = FMath::Max(0.0f, ColorFlash - DeltaSeconds / FadeSec);
		const float Sat = PianoProfile ? PianoProfile->PressHueSaturation : 0.7f;
		const FLinearColor Hue = FLinearColor::MakeFromHSV8(static_cast<uint8>(FlashHue * 255.0f), static_cast<uint8>(Sat * 255.0f), 255);
		KeyMID->SetVectorParameterValue(FName(TEXT("DreamRimColor")), FMath::Lerp(BaseRimColor, Hue, ColorFlash));
		KeyMID->SetVectorParameterValue(FName(TEXT("BaseTint")), FMath::Lerp(BaseTint, Hue * 0.9f + BaseTint * 0.1f, ColorFlash * 0.55f));
		KeyMID->SetScalarParameterValue(FName(TEXT("DreamRimStrength")), BaseRimStrength * (1.0f + ColorFlash * 1.5f));
		bFlashDirty = ColorFlash > 0.0f;
	}

	if (KeyMesh)
	{
		KeyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
	if (KeyBlocker)
	{
		KeyBlocker->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
}

void APCGPianoKey::InitializeFromPCGPoint(const FPCGPoint Point, const UPCGMetadata* Metadata)
{
	// KeyIndex / MidiNote are assigned by the keyboard from layout order when the key registers
	// (APCGPianoKeyboard::AssignKeyIdentities); the point seed is re-seeded by PCG and not trusted.
	ResolveKeyboard();
	ApplyProfileGeometry();
}

void APCGPianoKey::ResolveKeyboard()
{
	if (KeyboardOwner.IsValid())
	{
		return;
	}

	if (APCGPianoKeyboard* ParentKeyboard = Cast<APCGPianoKeyboard>(GetAttachParentActor()))
	{
		KeyboardOwner = ParentKeyboard;
	}
	else if (UWorld* World = GetWorld())
	{
		float BestDistanceSquared = TNumericLimits<float>::Max();
		for (TActorIterator<APCGPianoKeyboard> It(World); It; ++It)
		{
			const float DistanceSquared = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
			if (DistanceSquared < BestDistanceSquared)
			{
				BestDistanceSquared = DistanceSquared;
				KeyboardOwner = *It;
			}
		}
	}

	if (KeyboardOwner.IsValid())
	{
		KeyboardOwner->RegisterKey(this);
	}
}

void APCGPianoKey::ApplyProfileGeometry()
{
	const UPCGPianoKeyboardProfile* PianoProfile = KeyboardOwner.IsValid() ? KeyboardOwner->GetProfile() : nullptr;
	const FPCGPianoKeyboardDimensions Dimensions = PianoProfile ? PianoProfile->Dimensions : FPCGPianoKeyboardDimensions();
	const bool bBlack = bIsBlackKey;
	const float Width = bBlack ? Dimensions.BlackKeyWidth : Dimensions.WhiteKeyWidth;
	const float Depth = bBlack ? Dimensions.BlackKeyDepth : Dimensions.WhiteKeyDepth;
	const float Height = bBlack ? Dimensions.BlackKeyHeight : Dimensions.WhiteKeyHeight;

	if (PianoProfile)
	{
		const TSoftObjectPtr<UStaticMesh>& MeshReference = bBlack ? PianoProfile->BlackKeyMesh : PianoProfile->WhiteKeyMesh;
		if (UStaticMesh* Mesh = MeshReference.LoadSynchronous())
		{
			KeyMesh->SetStaticMesh(Mesh);
		}
		const TSoftObjectPtr<UMaterialInterface>& MaterialReference = bBlack ? PianoProfile->BlackKeyMaterial : PianoProfile->WhiteKeyMaterial;
		if (UMaterialInterface* Material = MaterialReference.LoadSynchronous())
		{
			KeyMesh->SetMaterial(0, Material);
			KeyMID = KeyMesh->CreateDynamicMaterialInstance(0, Material);
			if (KeyMID)
			{
				KeyMID->GetVectorParameterValue(FName(TEXT("BaseTint")), BaseTint);
				KeyMID->GetVectorParameterValue(FName(TEXT("DreamRimColor")), BaseRimColor);
				KeyMID->GetScalarParameterValue(FName(TEXT("DreamRimStrength")), BaseRimStrength);
			}
		}
	}

	// Fit the visible mesh to the profile dimensions, centred on the blocker. Without this the
	// mesh keeps its native (real-piano) size while the blocker follows the profile.
	if (const UStaticMesh* KeyStaticMesh = KeyMesh->GetStaticMesh())
	{
		const FBoxSphereBounds NativeBounds = KeyStaticMesh->GetBounds();
		const FVector NativeSize = NativeBounds.BoxExtent * 2.0f;
		if (NativeSize.X > KINDA_SMALL_NUMBER && NativeSize.Y > KINDA_SMALL_NUMBER && NativeSize.Z > KINDA_SMALL_NUMBER)
		{
			const FVector FitScale(Width / NativeSize.X, Depth / NativeSize.Y, Height / NativeSize.Z);
			KeyMesh->SetRelativeScale3D(FitScale);
		}
	}

	KeyBlocker->SetBoxExtent(FVector(Width * 0.5f, Depth * 0.5f, Height * 0.5f));
	StepTrigger->SetBoxExtent(FVector(Width * 0.5f, Depth * 0.5f, FMath::Max(1.5f, Dimensions.PressTriggerHeight * 0.5f)));
	StepTrigger->SetRelativeLocation(FVector(0.0f, 0.0f, Height * 0.5f + FMath::Max(1.5f, Dimensions.PressTriggerHeight * 0.5f)));
}

FBox APCGPianoKey::GetWorldFootprint() const
{
	return KeyBlocker ? KeyBlocker->Bounds.GetBox() : FBox(GetActorLocation(), GetActorLocation());
}

float APCGPianoKey::GetKeyTopZ() const
{
	return GetWorldFootprint().Max.Z;
}

void APCGPianoKey::SetKeyboard(APCGPianoKeyboard* InKeyboard)
{
	KeyboardOwner = InKeyboard;
}

bool APCGPianoKey::IsPlayerControlledPawn(AActor* OtherActor) const
{
	const APawn* Pawn = Cast<APawn>(OtherActor);
	return Pawn && Pawn->IsPlayerControlled();
}

void APCGPianoKey::HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex, const bool bFromSweep, const FHitResult& SweepResult)
{
	if (IsPlayerControlledPawn(OtherActor) && KeyboardOwner.IsValid())
	{
		KeyboardOwner->NotifyContactBegin(this, OtherActor);
	}
}

void APCGPianoKey::HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex)
{
	if (IsPlayerControlledPawn(OtherActor) && KeyboardOwner.IsValid())
	{
		KeyboardOwner->NotifyContactEnd(this, OtherActor);
	}
}

void APCGPianoKey::SetLogicalPressed(AActor* SteppingActor, const bool bPressedForActor)
{
	if (!SteppingActor)
	{
		return;
	}

	const bool bWasPressed = PressingActors.Num() > 0;
	if (bPressedForActor)
	{
		PressingActors.Add(SteppingActor);
	}
	else
	{
		PressingActors.Remove(SteppingActor);
	}
	const bool bNowPressed = PressingActors.Num() > 0;

	if (bWasPressed == bNowPressed)
	{
		return;
	}

	bIsPressed = bNowPressed;
	if (bIsPressed)
	{
		BeginVisualPress(SteppingActor);
	}
	else
	{
		EndVisualPress(SteppingActor);
	}
}

void APCGPianoKey::BeginVisualPress(AActor* SteppingActor)
{
	OnKeyPressed.Broadcast(KeyIndex, MidiNote, SteppingActor);

	// Same presentation path the hero music nodes use: the reactivity subsystem owns the shared
	// material bus. Free-play keys read as a Great hit; this never enters combat or damage.
	// Command energy stays 0: it is sticky until an encounter ends, and a free-play key is a
	// decaying pulse (CommandPulse), not a held command.
	if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		Reactivity->NotifyPlayedNote(MidiNote, EMelodiaRhythmGrade::Great);
		Reactivity->NotifyCommandResolved(EMelodiaRhythmGrade::Great, 0.0f, 0.0f, 0.0f, 0);
	}

	// Playing the keys plays the landscape: every cymatic field in the world ripples from this key.
	UMelodiaCymaticFieldComponent::BroadcastHit(GetWorld(), GetActorLocation(), 0.9f);

	if (KeyboardOwner.IsValid())
	{
		KeyboardOwner->NotifyKeyPressed(this, SteppingActor);
		const UPCGPianoKeyboardProfile* PianoProfile = KeyboardOwner->GetProfile();
		if (PianoProfile && PianoProfile->bColorShiftOnPress)
		{
			const float PitchClass = static_cast<float>(((MidiNote % 12) + 12) % 12) / 12.0f;
			const float Hue = PianoProfile->PressHueOffset + PitchClass * PianoProfile->PressHueSpan;
			FlashHue = Hue - FMath::FloorToFloat(Hue);
			ColorFlash = 1.0f;
			bFlashDirty = true;
		}
		if (PianoProfile && PianoProfile->bPlayPressSound)
		{
			if (USoundBase* Sound = PianoProfile->PressSound.LoadSynchronous())
			{
				const float Pitch = FMath::Clamp(FMath::Pow(2.0f, static_cast<float>(MidiNote - PianoProfile->PressSoundRootMidi) / 12.0f), 0.25f, 4.0f);
				UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation(), PianoProfile->PressSoundVolume, Pitch);
			}
		}
	}
}

void APCGPianoKey::EndVisualPress(AActor* SteppingActor)
{
	OnKeyReleased.Broadcast(KeyIndex, MidiNote, SteppingActor);
	if (KeyboardOwner.IsValid())
	{
		KeyboardOwner->NotifyKeyReleased(this, SteppingActor);
	}
}

APCGPianoKeyboard::APCGPianoKeyboard()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);

	GenerationBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("GenerationBounds"));
	GenerationBounds->SetupAttachment(SceneRoot);
	GenerationBounds->SetBoxExtent(FVector(1000.0f, 400.0f, 200.0f));
	GenerationBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GenerationBounds->SetGenerateOverlapEvents(false);
	GenerationBounds->SetHiddenInGame(true);

	PCGComponent = CreateDefaultSubobject<UPCGComponent>(TEXT("PianoPCG"));
	PCGComponent->SetIsPartitioned(false);
}

void APCGPianoKeyboard::BeginPlay()
{
	Super::BeginPlay();
	if (PCGComponent && PianoGraph)
	{
		PCGComponent->SetGraph(PianoGraph);
	}
}

void APCGPianoKeyboard::RegisterKey(APCGPianoKey* Key)
{
	if (!Key)
	{
		return;
	}

	RegisteredKeys.Add(Key);
	Key->SetKeyboard(this);
	RegisteredKeyCount = RegisteredKeys.Num();
	AssignKeyIdentities();
}

void APCGPianoKeyboard::AssignKeyIdentities()
{
	TArray<APCGPianoKey*> Whites;
	TArray<APCGPianoKey*> Blacks;
	for (APCGPianoKey* Key : RegisteredKeys)
	{
		if (Key)
		{
			(Key->IsBlackKey() ? Blacks : Whites).Add(Key);
		}
	}

	const FTransform KeyboardTransform = GetActorTransform();
	// Straight keyboards order by local X; a walkway orders by distance along its spline so bends keep MIDI order.
	const AActor* PathActor = OrderPathActor.Get();
	const USplineComponent* PathSpline = PathActor ? PathActor->FindComponentByClass<USplineComponent>() : nullptr;
	auto OrderKey = [&KeyboardTransform, PathSpline](const APCGPianoKey* Key)
	{
		if (PathSpline)
		{
			const float InputKey = PathSpline->FindInputKeyClosestToWorldLocation(Key->GetActorLocation());
			return PathSpline->GetDistanceAlongSplineAtSplineInputKey(InputKey);
		}
		return static_cast<float>(KeyboardTransform.InverseTransformPosition(Key->GetActorLocation()).X);
	};
	// TArray<T*>::Sort dereferences the elements, so the predicate takes references.
	auto ByOrder = [&OrderKey](const APCGPianoKey& A, const APCGPianoKey& B) { return OrderKey(&A) < OrderKey(&B); };
	Whites.Sort(ByOrder);
	Blacks.Sort(ByOrder);

	const int32 FirstMidi = Profile ? Profile->FirstMidiNote : 21;
	const int32 LastMidi = Profile ? Profile->LastMidiNote : 108;
	int32 NextWhite = 0;
	int32 NextBlack = 0;
	int32 LayoutIndex = 0;
	for (int32 Midi = FirstMidi; Midi <= LastMidi; ++Midi, ++LayoutIndex)
	{
		switch (Midi % 12)
		{
		case 1: case 3: case 6: case 8: case 10:
			if (Blacks.IsValidIndex(NextBlack))
			{
				Blacks[NextBlack++]->SetIdentity(LayoutIndex, Midi);
			}
			break;
		default:
			if (Whites.IsValidIndex(NextWhite))
			{
				Whites[NextWhite++]->SetIdentity(LayoutIndex, Midi);
			}
			break;
		}
	}
}

void APCGPianoKeyboard::UnregisterKey(APCGPianoKey* Key)
{
	if (!Key)
	{
		return;
	}

	RegisteredKeys.Remove(Key);
	for (auto It = ContactsByActor.CreateIterator(); It; ++It)
	{
		It.Value().Remove(Key);
		if (It.Value().Num() == 0)
		{
			It.RemoveCurrent();
		}
	}
	RegisteredKeyCount = RegisteredKeys.Num();
	UpdateActiveKeyCount();
}

void APCGPianoKeyboard::NotifyContactBegin(APCGPianoKey* Key, AActor* SteppingActor)
{
	if (!Key || !SteppingActor)
	{
		return;
	}

	ContactsByActor.FindOrAdd(SteppingActor).Add(Key);
	RecomputePressedKeysForActor(SteppingActor);
}

void APCGPianoKeyboard::NotifyContactEnd(APCGPianoKey* Key, AActor* SteppingActor)
{
	if (!Key || !SteppingActor)
	{
		return;
	}

	if (TSet<TObjectPtr<APCGPianoKey>>* Contacts = ContactsByActor.Find(SteppingActor))
	{
		Contacts->Remove(Key);
		if (Contacts->Num() == 0)
		{
			RemoveActorContact(SteppingActor);
		}
		else
		{
			RecomputePressedKeysForActor(SteppingActor);
		}
	}

	Key->SetLogicalPressed(SteppingActor, false);
	UpdateActiveKeyCount();
}

void APCGPianoKeyboard::NotifyKeyPressed(APCGPianoKey* Key, AActor* SteppingActor)
{
	if (Key)
	{
		OnKeyPressed.Broadcast(Key->GetKeyIndex(), Key->GetMidiNote(), SteppingActor);
		OnKeyboardPressed.Broadcast(Key->GetKeyIndex(), Key->GetMidiNote(), SteppingActor);
		if (!Key->IsBlackKey() && !bKeyRunCompleted)
		{
			PlayedWhiteKeys.Add(Key->GetKeyIndex());
			int32 RequiredKeys = RequiredWhiteKeyCount;
			if (RequiredKeys <= 0)
			{
				for (const TObjectPtr<APCGPianoKey>& Registered : RegisteredKeys)
				{
					if (Registered && !Registered->IsBlackKey())
					{
						++RequiredKeys;
					}
				}
			}
			if (RequiredKeys > 0 && PlayedWhiteKeys.Num() >= RequiredKeys)
			{
				bKeyRunCompleted = true;
				UE_LOG(LogTemp, Log, TEXT("MELODIA_PIANO key run completed on %s (%d white keys)"), *KeyboardId.ToString(), PlayedWhiteKeys.Num());
				OnKeyRunCompleted.Broadcast();
				if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
				{
					Reactivity->NotifyVictory();
				}
				if (UGameInstance* GI = GetGameInstance())
				{
					if (UMelodiaQuantumDrawSubsystem* Draw = GI->GetSubsystem<UMelodiaQuantumDrawSubsystem>())
					{
						// One async draw per completion (never per key). Empty provider = config default.
						// Both candidates are WorldAwakening variants, so the payoff is guaranteed and the draw only
						// chooses its character: chart_0 = gentle, chart_1 = full (QuantumChoice reads 0 / 1 on
						// MPC_Melodia_Palette, which the Water bridge consumes).
						TArray<FMelodiaDrawCandidate> Candidates;
						FMelodiaDrawCandidate& Gentle = Candidates.AddDefaulted_GetRef();
						Gentle.Id = TEXT("chart_0");
						Gentle.Difficulty = 0.35f;
						Gentle.Spacing = 0.4f;
						FMelodiaDrawCandidate& Full = Candidates.AddDefaulted_GetRef();
						Full.Id = TEXT("chart_1");
						Full.Difficulty = 0.75f;
						Full.Spacing = 0.55f;
						FMelodiaDrawCompleted Done;
						Done.BindDynamic(this, &APCGPianoKeyboard::HandleKeyRunDraw);
						Draw->RequestDraw(static_cast<int32>(GetTypeHash(KeyboardId)) ^ FMath::Rand(), Candidates, FString(), Done);
					}
				}
			}
		}
	}
}

void APCGPianoKeyboard::NotifyKeyReleased(APCGPianoKey* Key, AActor* SteppingActor)
{
	if (Key)
	{
		OnKeyReleased.Broadcast(Key->GetKeyIndex(), Key->GetMidiNote(), SteppingActor);
		OnKeyboardReleased.Broadcast(Key->GetKeyIndex(), Key->GetMidiNote(), SteppingActor);
	}
}

void APCGPianoKeyboard::ResetKeyRun()
{
	PlayedWhiteKeys.Reset();
	bKeyRunCompleted = false;
}

void APCGPianoKeyboard::HandleKeyRunDraw(const FName WinnerId, const FString Backend, const bool bSuccess)
{
	UE_LOG(LogTemp, Log, TEXT("MELODIA_PIANO key-run draw winner=%s backend=%s success=%d (chart_0 = gentle awakening, chart_1 = full awakening)"), *WinnerId.ToString(), *Backend, bSuccess ? 1 : 0);
}

void APCGPianoKeyboard::RecomputePressedKeysForActor(AActor* SteppingActor)
{
	TSet<TObjectPtr<APCGPianoKey>>* Contacts = ContactsByActor.Find(SteppingActor);
	if (!Contacts)
	{
		return;
	}

	for (TObjectPtr<APCGPianoKey> Key : *Contacts)
	{
		if (!Key)
		{
			continue;
		}

		bool bShouldBePressed = true;
		for (TObjectPtr<APCGPianoKey> OtherKey : *Contacts)
		{
			if (OtherKey && OtherKey != Key && OtherKey->GetKeyTopZ() > Key->GetKeyTopZ() + 0.1f && OtherKey->GetWorldFootprint().Intersect(Key->GetWorldFootprint()))
			{
				bShouldBePressed = false;
				break;
			}
		}
		Key->SetLogicalPressed(SteppingActor, bShouldBePressed);
	}
	UpdateActiveKeyCount();
}

void APCGPianoKeyboard::RemoveActorContact(AActor* SteppingActor)
{
	if (TSet<TObjectPtr<APCGPianoKey>>* Contacts = ContactsByActor.Find(SteppingActor))
	{
		for (TObjectPtr<APCGPianoKey> Key : *Contacts)
		{
			if (Key)
			{
				Key->SetLogicalPressed(SteppingActor, false);
			}
		}
	}
	ContactsByActor.Remove(SteppingActor);
	UpdateActiveKeyCount();
}

void APCGPianoKeyboard::UpdateActiveKeyCount()
{
	int32 Count = 0;
	for (const TObjectPtr<APCGPianoKey> Key : RegisteredKeys)
	{
		if (Key && Key->IsPressed())
		{
			++Count;
		}
	}
	ActiveKeyCount = Count;
}
