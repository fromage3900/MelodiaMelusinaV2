#include "MelodiaCosmeticDefinition.generated.h"
#include "MelodiaWardrobeSubsystem.h"

void UMelodiaCosmeticDefinition::PostLoad()
{
	Super::PostLoad();
	// Validation: ensure SourceDraftPath is relative and points to an existing draft JSON.
	// In production, each cosmetic's draft JSON would be checked here. For now,
	// bValid defaults to false until a draft JSON is shipped with the asset.
}