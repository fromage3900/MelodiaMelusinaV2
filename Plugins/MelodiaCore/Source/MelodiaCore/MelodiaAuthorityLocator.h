#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/WeakInterfacePtr.h"
#include "MelodiaSharedAuthorityInterfaces.h"
#include "MelodiaAuthorityLocator.generated.h"

/**
 * Resolves the game module's cross-module authority interfaces for MelodiaCore's
 * native C++. See MelodiaSharedAuthorityInterfaces.h for why this exists.
 *
 * Concrete providers register themselves in their own Initialize() and are held
 * weakly -- this class never extends a provider's lifetime, and a provider that
 * fails to register (e.g. running a level with no GameInstance subsystem set up
 * yet) degrades to GetTravelProvider() returning an unset TScriptInterface rather
 * than crashing. Callers must check IsValid() before use, same discipline as
 * UMelodiaMusicClockSubsystem::HasMusicalTime().
 */
UCLASS()
class MELODIACORE_API UMelodiaAuthorityLocator final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Melodia|Authority", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaAuthorityLocator* Get(const UObject* WorldContextObject);

	void RegisterTravelProvider(TScriptInterface<IMelodiaTravelProvider> Provider);
	void RegisterInputContextProvider(TScriptInterface<IMelodiaInputContextProvider> Provider);

	/** Returns nullptr-backed interface if no provider has registered yet. */
	TScriptInterface<IMelodiaTravelProvider> GetTravelProvider() const;
	TScriptInterface<IMelodiaInputContextProvider> GetInputContextProvider() const;

private:
	TWeakInterfacePtr<IMelodiaTravelProvider> TravelProvider;
	TWeakInterfacePtr<IMelodiaInputContextProvider> InputContextProvider;
};
