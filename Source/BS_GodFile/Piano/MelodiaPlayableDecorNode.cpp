#include "MelodiaPlayableDecorNode.h"

#include "Components/BoxComponent.h"
#include "MelodiaAudioComponent.h"

AMelodiaPlayableDecorNode::AMelodiaPlayableDecorNode()
{
	DecorAudio = CreateDefaultSubobject<UMelodiaAudioComponent>(TEXT("DecorAudio"));

	// Walkable: the player passes through; arrows (WorldDynamic, blocking) still hit the blocker.
	if (NodeBlocker)
	{
		NodeBlocker->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
		NodeBlocker->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
		NodeBlocker->SetCollisionResponseToChannel(ECC_Visibility, ECR_Ignore);
	}
}

void AMelodiaPlayableDecorNode::BeginPlay()
{
	const FVector Extent(TriggerHalfExtentCm);
	if (NodeBlocker)
	{
		NodeBlocker->SetBoxExtent(Extent);
	}
	if (StepTrigger)
	{
		StepTrigger->SetBoxExtent(Extent * 1.5f);
	}
	// A node spawned from a PCG point already carries its seeded note (NodeIndex set by InitializeFromPCGPoint); only hand-placed
	// decor takes DecorMidiNote.
	if (GetNodeIndex() == INDEX_NONE)
	{
		SetMidiNote(DecorMidiNote);
	}
	OnNoteActivated.AddUniqueDynamic(this, &AMelodiaPlayableDecorNode::HandleDecorNote);
	Super::BeginPlay();
}

void AMelodiaPlayableDecorNode::HandleDecorNote(const FPCGHeroMusicNoteEvent Event)
{
	if (DecorAudio)
	{
		DecorAudio->PlayMusicalNote(Event.MidiNote, NoteSeconds, Event.Grade == EMelodiaRhythmGrade::Perfect ? 1.0f : 0.75f);
	}
}
