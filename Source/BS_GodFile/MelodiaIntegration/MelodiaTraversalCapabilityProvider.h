#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaTraversalCapabilityProvider.generated.h"

/**
 * Module-neutral read-only capability provider.
 *
 * The game module owns the registry and traversal decision. Feature modules may
 * register a provider, but the registry never owns progression or movement state.
 * This is intentionally a native interface rather than a Wardrobe dependency:
 * MelodiaWardrobe already depends on BS_GodFile.
 */
/**
 * Capability ids, declared once.
 *
 * These were raw string literals in two modules — `capability.melodia.glide` in both
 * MelodiaTraversalComponent.cpp and MelodiaWardrobeSubsystem.cpp — with nothing keeping
 * them in agreement. Rename one side and QueryTraversalCapability falls into its
 * `unknown_capability` branch, returns false, and the ability SILENTLY STOPS WORKING:
 * the block reason is returned but nothing surfaces it.
 *
 * The game module owns the interface, so it owns the vocabulary. Providers and callers
 * both reference these.
 *
 * Adding one is not enough on its own — a capability needs a provider that maps it and
 * a caller that asks for it, or it is a name with no behaviour behind it.
 */
namespace MelodiaTraversalCapability
{
	/** Sustained glide with stamina drain. */
	inline const FName Glide{TEXT("capability.melodia.glide")};

	/** Ground dash / burst. */
	inline const FName Dash{TEXT("capability.melodia.dash")};

	/** Sustained swim. */
	inline const FName Swim{TEXT("capability.melodia.swim")};
}

class BS_GODFILE_API IMelodiaTraversalCapabilityProvider
{
public:
	virtual ~IMelodiaTraversalCapabilityProvider() = default;

	/** Return true only when the capability is currently usable in ContextId. */
	virtual bool QueryTraversalCapability(
		FName CapabilityId,
		FName ContextId,
		FName& OutBlockReason) const = 0;
};

/**
 * Game-instance-local discovery seam for read-only traversal capability queries.
 * There should be one canonical provider (currently MelodiaWardrobe) per game
 * instance. Multiple providers are rejected to avoid split capability truth.
 */
UCLASS()
class BS_GODFILE_API UMelodiaTraversalCapabilityRegistry final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	void RegisterProvider(UObject* ProviderObject, IMelodiaTraversalCapabilityProvider& Provider);
	void UnregisterProvider(UObject* ProviderObject);

	bool QueryCapability(FName CapabilityId, FName ContextId, FName& OutBlockReason) const;
	int32 GetRegisteredProviderCount() const;

private:
	struct FProviderEntry
	{
		TWeakObjectPtr<UObject> Object;
		IMelodiaTraversalCapabilityProvider* Provider = nullptr;
	};

	TArray<FProviderEntry> Providers;
};
