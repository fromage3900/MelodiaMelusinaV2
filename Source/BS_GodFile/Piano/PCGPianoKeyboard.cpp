#include "PCGPianoKeyboard.h"

// Live Coding reload marker: keep the actor implementation rebuildable after editor restart.

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "PCGComponent.h"
#include "PCGGraph.h"
#include "Metadata/PCGMetadata.h"
#include "Sound/SoundBase.h"
#include "UObject/ConstructorHelpers.h"

namespace PCGPianoPrivate
{
	constexpr int32 SeedIndexMask = 0xFF;
	constexpr int32 SeedMidiShift = 8;

	int32 DecodeIndex(const int32 Seed)
	{
		return Seed & SeedIndexMask;
	}

	int32 DecodeMidi(const int32 Seed)
	{
		return (Seed >> SeedMidiShift) & SeedIndexMask;
	}
}

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
	KeyBlocker->SetupAttachment(KeyMesh);
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

	const float Acceleration = ((TargetOffset - CurrentPressOffset) * Stiffness) - (PressVelocity * Damping);
	PressVelocity += Acceleration * DeltaSeconds;
	CurrentPressOffset += PressVelocity * DeltaSeconds;

	if (FMath::Abs(CurrentPressOffset - TargetOffset) < 0.01f && FMath::Abs(PressVelocity) < 0.01f)
	{
		CurrentPressOffset = TargetOffset;
		PressVelocity = 0.0f;
	}

	if (KeyMesh)
	{
		KeyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
}

void APCGPianoKey::InitializeFromPCGPoint(const FPCGPoint Point, const UPCGMetadata* Metadata)
{
	KeyIndex = PCGPianoPrivate::DecodeIndex(Point.Seed);
	MidiNote = PCGPianoPrivate::DecodeMidi(Point.Seed);
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
	if (KeyboardOwner.IsValid())
	{
		KeyboardOwner->NotifyKeyPressed(this, SteppingActor);
		const UPCGPianoKeyboardProfile* PianoProfile = KeyboardOwner->GetProfile();
		if (PianoProfile && PianoProfile->bPlayPressSound)
		{
			if (USoundBase* Sound = PianoProfile->PressSound.LoadSynchronous())
			{
				UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation());
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
