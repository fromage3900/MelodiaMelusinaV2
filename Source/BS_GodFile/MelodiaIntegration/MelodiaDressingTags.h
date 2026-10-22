#pragma once

#include "CoreMinimal.h"
#include "NativeGameplayTags.h"

/**
 * The dressing vocabulary: the gameplay-tag families the catalogue is keyed by.
 *
 * Why native tags and not Config: `Config/DefaultGameplayTags.ini` is an ask-first
 * file in this repo, and a catalogue that cannot be loaded is worse than one that
 * carries its own vocabulary. Native tags register themselves.
 *
 * The tag STRINGS are "Melodia.Dressing.<Family>". The artist already works in a
 * different vocabulary - the actor tags "Room_bedroom", "Prop_SM_Desk" - so the
 * catalogue keeps both: the gameplay tag is the key, and the legacy artist tag is
 * carried alongside it so a family can be found by the name the artist knows.
 */
namespace MelodiaDressingTags
{
	/** The bedroom's hero props. Artist vocabulary: "Room_bedroom". */
	BS_GODFILE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Room_Bedroom);

	/** The landing's hero props. Artist vocabulary: "Room_landing". */
	BS_GODFILE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Room_Landing);

	/** The salon's hero props. Artist vocabulary: "Room_salon". */
	BS_GODFILE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Room_Salon);

	/** Props that belong to no single room - the ones a room may borrow. */
	BS_GODFILE_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Room_Any);
}
