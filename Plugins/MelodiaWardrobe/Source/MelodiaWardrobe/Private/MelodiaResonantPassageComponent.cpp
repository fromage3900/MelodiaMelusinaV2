#include "MelodiaResonantPassageComponent.h"

#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaTraversalComponent.h"
#include "MelodiaWardrobeSubsystem.h"
#include "GameFramework/Actor.h"

namespace
{
	constexpr int32 PassageStageCount = 4;

	EMelodiaResonantPassageStage StageFromIndex(const int32 Index)
	{
		switch (Index)
		{
		case 0: return EMelodiaResonantPassageStage::Invocation;
		case 1: return EMelodiaResonantPassageStage::Unfolding;
		case 2: return EMelodiaResonantPassageStage::Threshold;
		case 3: return EMelodiaResonantPassageStage::Release;
		default: return EMelodiaResonantPassageStage::Inactive;
		}
	}
}

UMelodiaResonantPassageComponent::UMelodiaResonantPassageComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaResonantPassageComponent::BeginPlay()
{
	Super::BeginPlay();

	Wardrobe = UMelodiaWardrobeSubsystem::Get(this);
	if (Wardrobe)
	{
		Wardrobe->OnWardrobeChanged.AddUniqueDynamic(this, &ThisClass::HandleWardrobeChanged);
		bBoundWardrobe = true;
	}

	MusicClock = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr;
	if (MusicClock)
	{
		MusicClock->OnMelodiaBeat.AddUniqueDynamic(this, &ThisClass::HandleMusicBeat);
		bBoundMusicClock = true;
	}

	RefreshPassageVoicing();
}

void UMelodiaResonantPassageComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Unbind();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaResonantPassageComponent::Unbind()
{
	if (bBoundWardrobe && Wardrobe)
	{
		Wardrobe->OnWardrobeChanged.RemoveDynamic(this, &ThisClass::HandleWardrobeChanged);
	}
	if (bBoundMusicClock && MusicClock)
	{
		MusicClock->OnMelodiaBeat.RemoveDynamic(this, &ThisClass::HandleMusicBeat);
	}
	bBoundWardrobe = false;
	bBoundMusicClock = false;
}

bool UMelodiaResonantPassageComponent::IsRequiredFormEquipped() const
{
	if (!Wardrobe || RequiredResonantFormId.IsNone())
	{
		return false;
	}

	if (bRequireUnlockedForm && !Wardrobe->IsFormUnlocked(RequiredResonantFormId))
	{
		return false;
	}

	for (uint8 SlotValue = 0;
		SlotValue <= static_cast<uint8>(EMelodiaWardrobeSlot::Accessories);
		++SlotValue)
	{
		const EMelodiaWardrobeSlot Slot = static_cast<EMelodiaWardrobeSlot>(SlotValue);
		if (Wardrobe->GetEquippedFormId(Slot) == RequiredResonantFormId)
		{
			return true;
		}
	}
	return false;
}

bool UMelodiaResonantPassageComponent::RefreshPassageVoicing()
{
	const bool bNextVoiced = RequiredResonantFormId.IsNone()
		? true
		: IsRequiredFormEquipped();

	const bool bChanged = bNextVoiced != bVoicedByWardrobe;
	bVoicedByWardrobe = bNextVoiced;
	if (bChanged || !bVoicedByWardrobe)
	{
		StageIndex = -1;
		BeatsObserved = 0;
	}
	if (bChanged || !bVoicedByWardrobe)
	{
		BroadcastStage();
	}
	return bVoicedByWardrobe;
}

void UMelodiaResonantPassageComponent::ResetPassage()
{
	StageIndex = bVoicedByWardrobe ? 0 : -1;
	BeatsObserved = 0;
	BroadcastStage();
}

EMelodiaResonantPassageStage UMelodiaResonantPassageComponent::GetStage() const
{
	return StageFromIndex(StageIndex);
}

bool UMelodiaResonantPassageComponent::IsTraversalWindowOpen() const
{
	return bVoicedByWardrobe
		&& (StageIndex == static_cast<int32>(EMelodiaResonantPassageStage::Threshold) - 1
			|| StageIndex == static_cast<int32>(EMelodiaResonantPassageStage::Release) - 1);
}

void UMelodiaResonantPassageComponent::HandleWardrobeChanged(
	const EMelodiaWardrobeSlot Slot,
	const FName CosmeticId)
{
	RefreshPassageVoicing();
}

void UMelodiaResonantPassageComponent::HandleMusicBeat(const int32 BeatNumber, const int32 BeatInBar)
{
	if (!bAdvanceOnMusicBeat || !bVoicedByWardrobe)
	{
		return;
	}

	const int32 SafeBeatsPerStage = FMath::Max(1, BeatsPerStage);
	BeatsObserved = FMath::Min(BeatsObserved + 1, SafeBeatsPerStage * PassageStageCount);
	const int32 NextStageIndex = FMath::Min(BeatsObserved / SafeBeatsPerStage, PassageStageCount - 1);
	if (NextStageIndex != StageIndex)
	{
		StageIndex = NextStageIndex;
		BroadcastStage();
	}
}

void UMelodiaResonantPassageComponent::BroadcastStage()
{
	OnStageChanged.Broadcast(MovementId, StageIndex, GetStage(), bVoicedByWardrobe);
}

bool UMelodiaResonantPassageComponent::RequestGlideAtThreshold()
{
	if (!IsTraversalWindowOpen())
	{
		return false;
	}

	UMelodiaTraversalComponent* Traversal = GetOwner()
		? GetOwner()->FindComponentByClass<UMelodiaTraversalComponent>()
		: nullptr;
	if (!Traversal)
	{
		return false;
	}

	if (!TraversalContextId.IsNone()
		&& Traversal->GetTraversalCapabilityContextId() != TraversalContextId)
	{
		return false;
	}

	return Traversal->RequestTraversalMode(EMelodiaTraversalMode::Glide).WasAccepted();
}
