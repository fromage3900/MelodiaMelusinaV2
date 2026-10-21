#pragma once

#include "CoreMinimal.h"
#include "PCGHeroMusic.h"
#include "MelodiaPlayableDecorNode.generated.h"

class UMelodiaAudioComponent;

/**
 * A hand-placed, self-voiced instrument for room decor (bead strings, gold key plates, rod ribbons).
 *
 * It IS a hero-music node, so everything that already plays nodes keeps working with no new gameplay path: walking through the
 * step trigger presses it, and WaveHarp arrows press it through UMelodiaWaveHarpCombatComponent::ResolveProjectileHit exactly like a
 * bell. It needs no graph host: it voices itself with UMelodiaAudioComponent::PlayMusicalNote (the pitched WaveHarp sample).
 *
 * The note comes from playable.json (Houdini room_shell acoustics -> playable_decor.py): DecorMidiNote is the room-keyed MIDI note.
 * Unlike a pad it never blocks the player: pawns are ignored by the blocker, arrows (WorldDynamic) still hit it.
 * Presentation only: it writes no gameplay state.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaPlayableDecorNode : public APCGHeroMusicNode
{
	GENERATED_BODY()

public:
	AMelodiaPlayableDecorNode();

	/** MIDI note this piece sounds (clamped 0..127; the sample pitch range supports notes up to 96). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Playable Decor", meta = (ClampMin = "0", ClampMax = "127"))
	int32 DecorMidiNote = 51;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Playable Decor", meta = (ClampMin = "0.05"))
	float NoteSeconds = 0.35f;

	/** Half extent (cm) of the hit/step volumes. Beads and ribbons are small; key plates a little larger. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Playable Decor", meta = (ClampMin = "2.0"))
	float TriggerHalfExtentCm = 12.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Playable Decor")
	TObjectPtr<UMelodiaAudioComponent> DecorAudio;

	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleDecorNote(FPCGHeroMusicNoteEvent Event);
};
