// MelodiaWardrobe — gacha loop (Decision 043/045).
//
// Weighted random pull: 1 Golden per pull, idempotent on GrantId via its own
// runtime ConsumedGrantIds set (handoff gotcha #3). Quantum ranking is a later
// swap-in behind this same signature.

#include "MelodiaWardrobeGachaSubsystem.h"
#include "MelodiaWardrobeComponent.h"
#include "MelodiaWardrobeSubsystem.h"
#include "MelodiaTokenWalletSubsystem.h"
#include "MelodiaCosmeticDefinition.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	const FString PoolCatalogPath = TEXT("/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog");
	constexpr int32 GoldenCostPerPull = 1;

	/** Rarity weight table; Grandmaster is excluded from pulls. */
	int32 RarityWeight(const EMelodiaCosmeticRarity Rarity)
	{
		switch (Rarity)
		{
		case EMelodiaCosmeticRarity::Common:    return 60;
		case EMelodiaCosmeticRarity::Uncommon:  return 25;
		case EMelodiaCosmeticRarity::Rare:      return 10;
		case EMelodiaCosmeticRarity::Epic:      return 4;
		case EMelodiaCosmeticRarity::Legendary: return 1;
		default:                                return 0;
		}
	}

	/**
	 * Best-effort: equip a granted cosmetic on the first player pawn's
	 * MelodiaWardrobeComponent.
	 *
	 * Returns whether the cosmetic is ACTUALLY equipped. This previously returned true
	 * whenever the component merely existed, discarding EquipCosmetic's result -- so a
	 * refused equip (not owned, uncatalogued, incompatible skeleton) logged
	 * "equipped on character" while nothing had changed.
	 */
	bool TryEquipGrantedCosmetic(const UObject* WorldContext, UMelodiaWardrobeSubsystem* Wardrobe, const FName CosmeticId)
	{
		if (!Wardrobe) return false;

		APlayerController* PC = UGameplayStatics::GetPlayerController(WorldContext, 0);
		if (!PC) return false;

		APawn* Pawn = PC->GetPawn();
		if (!Pawn) return false;

		UMelodiaWardrobeComponent* WardrobeComp = Cast<UMelodiaWardrobeComponent>(Pawn->GetComponentByClass(UMelodiaWardrobeComponent::StaticClass()));
		if (!WardrobeComp) return false;

		return WardrobeComp->EquipCosmetic(CosmeticId);
	}
}

UMelodiaWardrobeGachaSubsystem* UMelodiaWardrobeGachaSubsystem::Get(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr)
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			return GI->GetSubsystem<UMelodiaWardrobeGachaSubsystem>();
		}
	}
	return nullptr;
}

void UMelodiaWardrobeGachaSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UGameInstance* GI = GetGameInstance())
	{
		Wardrobe = GI->GetSubsystem<UMelodiaWardrobeSubsystem>();
		Wallet = GI->GetSubsystem<UMelodiaTokenWalletSubsystem>();
	}
}

FMelodiaPullResult UMelodiaWardrobeGachaSubsystem::PullOnce()
{
	FMelodiaPullResult Result;
	if (!Wardrobe || !Wallet)
	{
		return Result;
	}

	// The wallet has no "consume without paying" primitive; the Golden check is
	// done here, then the wallet spends exactly 1.
	const FMelodiaWalletSnapshot Snapshot = Wallet->GetSnapshot();
	if (Snapshot.GoldenTokens < GoldenCostPerPull)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE pull rejected: %d Golden, need %d."), Snapshot.GoldenTokens, GoldenCostPerPull);
		return Result;
	}

	const UMelodiaCosmeticCatalog* Catalog = Cast<UMelodiaCosmeticCatalog>(StaticLoadObject(UMelodiaCosmeticCatalog::StaticClass(), nullptr, *PoolCatalogPath));
	if (!Catalog || Catalog->Cosmetics.Num() == 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE pull rejected: catalog empty or missing."));
		return Result;
	}

	// Weighted random pick across the catalog.
	int32 TotalWeight = 0;
	for (const FMelodiaCosmeticRecord& C : Catalog->Cosmetics)
	{
		TotalWeight += RarityWeight(C.Rarity);
	}
	if (TotalWeight <= 0)
	{
		return Result;
	}

	const int32 Roll = FMath::RandRange(0, TotalWeight - 1);
	int32 Accumulator = 0;
	FName PickedId = NAME_None;
	for (const FMelodiaCosmeticRecord& C : Catalog->Cosmetics)
	{
		Accumulator += RarityWeight(C.Rarity);
		if (Roll < Accumulator)
		{
			PickedId = C.CosmeticId;
			break;
		}
	}
	if (PickedId.IsNone())
	{
		return Result;
	}

	// Atomic spend + grant: the spend must be accepted before anything is granted.
	if (!Wallet->TrySpendGolden(GoldenCostPerPull))
	{
		return Result;
	}

	// Unique per-pull grant id keeps replay safe within the session.
	Result.GrantId = FName(*FString::Printf(TEXT("Gacha_%s_%lld"), *PickedId.ToString(), static_cast<int64>(FPlatformTime::Seconds())));
	if (!Wardrobe->GrantCosmetic(PickedId, Result.GrantId))
	{
		// The downstream grant is part of the pull transaction. Restore the
		// Golden token when the grant cannot be committed.
		Wallet->TryRefundGolden(GoldenCostPerPull);
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE pull rolled back: %s grant failed; Golden refunded."), *PickedId.ToString());
		return Result;
	}

	// ==== INTEGRATION: Equip the granted cosmetic ====
	// After granting ownership, attempt to equip the cosmetic on the player
	// character's wardrobe component so it appears in-game. This is a
	// best-effort integration; if no wardrobe component is found, the cosmetic
	// is still owned and OnWardrobeChanged will fire for UI/Blueprints.
	if (TryEquipGrantedCosmetic(this, Wardrobe, PickedId))
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE pull -> %s equipped on character."), *PickedId.ToString());
	}
	else
	{
		// Ownership is committed either way -- only presentation was skipped. Do not
		// roll the pull back here; the player owns what they paid for.
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE pull -> %s granted but NOT equipped (no wardrobe component, or the equip was refused). Ownership stands; UI can react via OnWardrobeChanged."), *PickedId.ToString());
	}
	// ==== END INTEGRATION ====

	Result.bSuccess = true;
	Result.CosmeticId = PickedId;
	UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE pull -> %s (grant %s)."), *PickedId.ToString(), *Result.GrantId.ToString());
	return Result;
}
