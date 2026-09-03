#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/Interface.h"
#include "MelodiaEntitlementSubsystem.generated.h"

UINTERFACE(BlueprintType)
class MELODIACORE_API UMelodiaEntitlementProvider : public UInterface
{
	GENERATED_BODY()
};

class MELODIACORE_API IMelodiaEntitlementProvider
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Entitlements")
	TArray<FName> QueryOwnedContentPacks() const;
};

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (monetization scaffolding). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaEntitlementSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Entitlements", meta=(WorldContext="WorldContextObject"))
	static UMelodiaEntitlementSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category="Melodia|Entitlements")
	TArray<FName> QueryEntitlements() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Entitlements")
	bool OwnsContentPack(FName ContentPackId) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Entitlements")
	bool GrantDevelopmentEntitlement(FName ContentPackId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Entitlements")
	bool RefreshCatalog(UObject* Provider);

	UFUNCTION(BlueprintPure, Category="Melodia|Entitlements")
	bool ResolveCosmeticAvailability(FName RequiredContentPackId) const;

	/** Restore owned packs from a save game. Adds to the Core baseline. */
	void RestoreFromSave(const TArray<FName>& SavedPacks);

private:
	UPROPERTY(Transient)
	TSet<FName> OwnedContentPacks;
};
