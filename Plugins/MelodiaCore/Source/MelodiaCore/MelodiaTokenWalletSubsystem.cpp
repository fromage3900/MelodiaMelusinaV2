#include "MelodiaTokenWalletSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "MelodiaCurrencyRegistry.h"
#include "MelodiaSaveGame.h"

namespace
{
	/** Matches gmm/game/tokens.py TokenWallet.shards default key set, in the same order. */
	const TArray<FName> GMelodiaElements = {
		TEXT("Forte"), TEXT("Tide"), TEXT("Gale"), TEXT("Stone"),
		TEXT("Radiant"), TEXT("Umbral"), TEXT("Arcane")
	};
}

const TArray<FName>& UMelodiaTokenWalletSubsystem::GetElementNames()
{
	return GMelodiaElements;
}

UMelodiaTokenWalletSubsystem* UMelodiaTokenWalletSubsystem::Get(const UObject* WorldContextObject)
{
	if (!WorldContextObject)
	{
		return nullptr;
	}
	const UWorld* World = WorldContextObject->GetWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaTokenWalletSubsystem>() : nullptr;
}

void UMelodiaTokenWalletSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	EnsureElementKeys();
	SyncLegacyViews();
}

void UMelodiaTokenWalletSubsystem::EnsureElementKeys()
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	if (!Registry)
	{
		return;
	}

	for (const FMelodiaCurrencyDefinition& Row : Registry->Currencies)
	{
		if (Row.CurrencyId.IsNone())
		{
			continue;
		}

		if (Row.Kind == EMelodiaCurrencyKind::Resource)
		{
			const float MaxValue = FMath::Max(0.0f, Row.MaxValue);
			ResourceMax.FindOrAdd(Row.CurrencyId, MaxValue);
			Resources.FindOrAdd(Row.CurrencyId, FMath::Clamp(Row.DefaultValue, 0.0f, MaxValue));
		}
		else
		{
			Balances.FindOrAdd(Row.CurrencyId, FMath::Max(0, FMath::RoundToInt(Row.DefaultValue)));
		}
	}

	SyncLegacyViews();
}

const UMelodiaCurrencyRegistry* UMelodiaTokenWalletSubsystem::GetRegistry() const
{
	return UMelodiaCurrencyRegistry::Get(this);
}

void UMelodiaTokenWalletSubsystem::SyncLegacyViews()
{
	Shards.Reset();
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	if (Registry)
	{
		for (const FMelodiaCurrencyDefinition& Row : Registry->Currencies)
		{
			if (Row.Kind == EMelodiaCurrencyKind::Shard && !Row.CurrencyId.IsNone())
			{
				Shards.Add(Row.CurrencyId, Balances.FindRef(Row.CurrencyId));
			}
		}
	}

	GoldenTokens = Balances.FindRef(TEXT("Golden"));
	ManaCurrent = Resources.FindRef(TEXT("Mana"));
	ManaMax = ResourceMax.FindRef(TEXT("Mana"));
	if (ManaMax <= 0.0f)
	{
		ManaMax = 100.0f;
	}
}

FMelodiaWalletSnapshot UMelodiaTokenWalletSubsystem::GetSnapshot() const
{
	FMelodiaWalletSnapshot Snapshot;
	Snapshot.Balances = Balances;
	Snapshot.Resources = Resources;
	Snapshot.ResourceMax = ResourceMax;
	Snapshot.Shards = Shards;
	Snapshot.ManaCurrent = ManaCurrent;
	Snapshot.ManaMax = ManaMax;
	Snapshot.GoldenTokens = GoldenTokens;
	Snapshot.TotalCollected = TotalCollected;
	return Snapshot;
}

void UMelodiaTokenWalletSubsystem::BroadcastChanged()
{
	OnWalletChanged.Broadcast(GetSnapshot());
}

int32 UMelodiaTokenWalletSubsystem::GetShards(const FName Element) const
{
	const int32* Found = Balances.Find(Element);
	return Found ? *Found : 0;
}

float UMelodiaTokenWalletSubsystem::GetBalance(const FName CurrencyId) const
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	if (!Row || Row->Kind == EMelodiaCurrencyKind::Resource)
	{
		return 0.0f;
	}
	return static_cast<float>(Balances.FindRef(CurrencyId));
}

float UMelodiaTokenWalletSubsystem::GetResource(const FName CurrencyId) const
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	if (!Row || Row->Kind != EMelodiaCurrencyKind::Resource)
	{
		return 0.0f;
	}
	return Resources.FindRef(CurrencyId);
}

float UMelodiaTokenWalletSubsystem::GetResourceMax(const FName CurrencyId) const
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	if (!Row || Row->Kind != EMelodiaCurrencyKind::Resource)
	{
		return 0.0f;
	}
	return ResourceMax.FindRef(CurrencyId);
}

bool UMelodiaTokenWalletSubsystem::IsGrantConsumed(const FName GrantId) const
{
	return !GrantId.IsNone() && ConsumedGrantIds.Contains(GrantId);
}

namespace
{
	bool ToWholeAmount(const float Amount, int32& OutAmount)
	{
		if (Amount <= 0.0f || !FMath::IsFinite(Amount))
		{
			return false;
		}
		const float Rounded = FMath::RoundToFloat(Amount);
		if (!FMath::IsNearlyEqual(Amount, Rounded))
		{
			return false;
		}
		OutAmount = FMath::RoundToInt(Rounded);
		return OutAmount > 0;
	}
}

bool UMelodiaTokenWalletSubsystem::TryGrantCurrency(const FName CurrencyId, const float Amount, const FName GrantId)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	if (!Row || CurrencyId.IsNone() || Amount <= 0.0f || !FMath::IsFinite(Amount) || IsGrantConsumed(GrantId))
	{
		return false;
	}

	if (Row->Kind == EMelodiaCurrencyKind::Resource)
	{
		const float MaxValue = ResourceMax.FindRef(CurrencyId);
		float& Balance = Resources.FindOrAdd(CurrencyId);
		Balance = FMath::Clamp(Balance + Amount, 0.0f, MaxValue);
		if (Row->bCountsTowardTotalCollected)
		{
			TotalCollected += FMath::Max(0, FMath::RoundToInt(Amount));
		}
		RecordConsumedGrant(GrantId);
		SyncLegacyViews();
		BroadcastChanged();
		return true;
	}

	int32 WholeAmount = 0;
	if (!ToWholeAmount(Amount, WholeAmount))
	{
		return false;
	}

	Balances.FindOrAdd(CurrencyId) += WholeAmount;
	if (Row->bCountsTowardTotalCollected)
	{
		TotalCollected += WholeAmount;
	}
	RecordConsumedGrant(GrantId);

	SyncLegacyViews();
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TrySpendCurrency(const FName CurrencyId, const float Amount)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	if (!Row || CurrencyId.IsNone() || Amount <= 0.0f || !FMath::IsFinite(Amount))
	{
		return false;
	}

	if (Row->Kind == EMelodiaCurrencyKind::Resource)
	{
		float* Balance = Resources.Find(CurrencyId);
		if (!Balance || *Balance < Amount)
		{
			return false;
		}
		*Balance -= Amount;
	}
	else
	{
		int32 WholeAmount = 0;
		if (!ToWholeAmount(Amount, WholeAmount))
		{
			return false;
		}
		int32* Balance = Balances.Find(CurrencyId);
		if (!Balance || *Balance < WholeAmount)
		{
			return false;
		}
		*Balance -= WholeAmount;
	}

	SyncLegacyViews();
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TryRefundCurrency(const FName CurrencyId, const float Amount)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(CurrencyId) : nullptr;
	int32 WholeAmount = 0;
	if (!Row || !Row->bRefundable || Row->Kind == EMelodiaCurrencyKind::Resource || !ToWholeAmount(Amount, WholeAmount))
	{
		return false;
	}

	Balances.FindOrAdd(CurrencyId) += WholeAmount;
	SyncLegacyViews();
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::CanAfford(const TMap<FName, int32>& Cost) const
{
	if (Cost.IsEmpty())
	{
		return false;
	}
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	for (const TPair<FName, int32>& Line : Cost)
	{
		const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(Line.Key) : nullptr;
		if (!Row || Row->Kind == EMelodiaCurrencyKind::Resource || Line.Value <= 0 ||
			GetBalance(Line.Key) < static_cast<float>(Line.Value))
		{
			return false;
		}
	}
	return true;
}

bool UMelodiaTokenWalletSubsystem::TrySpendMany(const TMap<FName, int32>& Cost)
{
	if (!CanAfford(Cost))
	{
		return false;
	}
	for (const TPair<FName, int32>& Line : Cost)
	{
		Balances.FindChecked(Line.Key) -= Line.Value;
	}
	SyncLegacyViews();
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TryGrantShards(const FName Element, const int32 Amount, const FName GrantId)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(Element) : nullptr;
	return Row && Row->Kind == EMelodiaCurrencyKind::Shard && TryGrantCurrency(Element, static_cast<float>(Amount), GrantId);
}

bool UMelodiaTokenWalletSubsystem::TrySpendShards(const FName Element, const int32 Amount)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(Element) : nullptr;
	return Row && Row->Kind == EMelodiaCurrencyKind::Shard && TrySpendCurrency(Element, static_cast<float>(Amount));
}

bool UMelodiaTokenWalletSubsystem::TryAddMana(const float Amount)
{
	return TryGrantCurrency(TEXT("Mana"), Amount, NAME_None);
}

bool UMelodiaTokenWalletSubsystem::TrySpendMana(const float Amount)
{
	return TrySpendCurrency(TEXT("Mana"), Amount);
}

bool UMelodiaTokenWalletSubsystem::TryGrantGolden(const int32 Amount, const FName GrantId)
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	const FMelodiaCurrencyDefinition* Row = Registry ? Registry->Find(TEXT("Golden")) : nullptr;
	return Row && Row->Kind == EMelodiaCurrencyKind::Premium &&
		TryGrantCurrency(TEXT("Golden"), static_cast<float>(Amount), GrantId);
}

bool UMelodiaTokenWalletSubsystem::TrySpendGolden(const int32 Amount)
{
	return TrySpendCurrency(TEXT("Golden"), static_cast<float>(Amount));
}

bool UMelodiaTokenWalletSubsystem::TryRefundGolden(const int32 Amount)
{
	return TryRefundCurrency(TEXT("Golden"), static_cast<float>(Amount));
}

void UMelodiaTokenWalletSubsystem::RecordConsumedGrant(const FName GrantId)
{
	if (GrantId.IsNone() || ConsumedGrantIds.Contains(GrantId))
	{
		return;
	}

	ConsumedGrantIds.Add(GrantId);
	ConsumedGrantOrder.Add(GrantId);

	// Trim oldest-first. Replaying a grant older than the window can double-pay, so the cap is
	// deliberately large: it bounds save size and restore cost without making replay plausible.
	if (ConsumedGrantOrder.Num() > MaxConsumedGrantEntries)
	{
		const int32 Excess = ConsumedGrantOrder.Num() - MaxConsumedGrantEntries;
		for (int32 Index = 0; Index < Excess; ++Index)
		{
			ConsumedGrantIds.Remove(ConsumedGrantOrder[Index]);
		}
		ConsumedGrantOrder.RemoveAt(0, Excess, EAllowShrinking::No);
	}
}

void UMelodiaTokenWalletSubsystem::RefreshResourceCapsFromRegistry()
{
	const UMelodiaCurrencyRegistry* Registry = GetRegistry();
	if (!Registry)
	{
		return;
	}

	for (const FMelodiaCurrencyDefinition& Row : Registry->Currencies)
	{
		if (Row.Kind != EMelodiaCurrencyKind::Resource || Row.CurrencyId.IsNone())
		{
			continue;
		}
		const float MaxValue = FMath::Max(0.0f, Row.MaxValue);
		ResourceMax.FindOrAdd(Row.CurrencyId) = MaxValue;
		if (float* Balance = Resources.Find(Row.CurrencyId))
		{
			*Balance = FMath::Clamp(*Balance, 0.0f, MaxValue);
		}
	}
}

void UMelodiaTokenWalletSubsystem::CaptureToSave(UMelodiaSaveGame* Save) const
{
	if (!Save)
	{
		return;
	}
	Save->WalletBalances = Balances;
	Save->WalletResources = Resources;
	Save->WalletResourceMax = ResourceMax;
	Save->WalletShards = Shards;
	Save->WalletManaCurrent = ManaCurrent;
	Save->WalletManaMax = ManaMax;
	Save->WalletGoldenTokens = GoldenTokens;
	Save->WalletTotalCollected = TotalCollected;
	Save->WalletConsumedGrantIds = ConsumedGrantIds;
	Save->WalletConsumedGrantOrder = ConsumedGrantOrder;
	if (const UMelodiaCurrencyRegistry* Registry = GetRegistry())
	{
		Save->WalletRegistrySchemaVersion = Registry->RegistrySchemaVersion;
	}
	Save->bWalletMigratedFromLegacyTokens = bMigratedFromLegacy;
}

void UMelodiaTokenWalletSubsystem::RestoreFromSave(const UMelodiaSaveGame* Save)
{
	if (!Save)
	{
		return;
	}

	Balances = Save->WalletBalances;
	Resources = Save->WalletResources;
	ResourceMax = Save->WalletResourceMax;
	if (Balances.IsEmpty() && Resources.IsEmpty() && ResourceMax.IsEmpty())
	{
		Balances = Save->WalletShards;
		Balances.FindOrAdd(TEXT("Golden")) = Save->WalletGoldenTokens;
		Resources.FindOrAdd(TEXT("Mana")) = Save->WalletManaCurrent;
		ResourceMax.FindOrAdd(TEXT("Mana")) = Save->WalletManaMax;
	}
	TotalCollected = Save->WalletTotalCollected;
	ConsumedGrantIds = Save->WalletConsumedGrantIds;
	// Legacy saves have no order array; rebuild one so trimming has something to work with.
	ConsumedGrantOrder = Save->WalletConsumedGrantOrder;
	ConsumedGrantOrder.RemoveAll([this](const FName GrantId)
	{
		return GrantId.IsNone() || !ConsumedGrantIds.Contains(GrantId);
	});
	{
		TSet<FName> Seen(ConsumedGrantOrder);
		for (const FName GrantId : ConsumedGrantIds)
		{
			if (!Seen.Contains(GrantId))
			{
				Seen.Add(GrantId);
				ConsumedGrantOrder.Add(GrantId);
			}
		}
	}
	bMigratedFromLegacy = Save->bWalletMigratedFromLegacyTokens;
	EnsureElementKeys();

	// EnsureElementKeys uses FindOrAdd, so a cap already present from the save wins. When the
	// registry schema has moved since capture, the save's caps are stale and must be replaced.
	if (const UMelodiaCurrencyRegistry* Registry = GetRegistry())
	{
		if (Save->WalletRegistrySchemaVersion != Registry->RegistrySchemaVersion)
		{
			RefreshResourceCapsFromRegistry();
		}
	}

	// One-way migration from the legacy per-variant ints. Heart maps to Forte and Swirl to
	// Arcane, per the variant->element table in the token contract. The legacy fields are
	// left untouched: UMelodiaRoguelikeRunSubsystem still owns them for run-scoped purposes,
	// and silently zeroing another subsystem's state would be a cross-authority write.
	if (!bMigratedFromLegacy)
	{
		if (Save->HeartMelodyTokens > 0)
		{
			Balances.FindOrAdd(TEXT("Forte")) += Save->HeartMelodyTokens;
			TotalCollected += Save->HeartMelodyTokens;
		}
		if (Save->SwirlMelodyTokens > 0)
		{
			Balances.FindOrAdd(TEXT("Arcane")) += Save->SwirlMelodyTokens;
			TotalCollected += Save->SwirlMelodyTokens;
		}
		// Flag lives on the wallet; CaptureToSave writes it back into the record on next save.
		bMigratedFromLegacy = true;

		UE_LOG(LogTemp, Log,
			TEXT("MELODIA_WALLET migrated legacy tokens: Heart=%d -> Forte, Swirl=%d -> Arcane"),
			Save->HeartMelodyTokens, Save->SwirlMelodyTokens);
	}

	// Legacy saves carry a zeroed mana block; restore sane defaults rather than a dead wallet.
	if (ResourceMax.FindRef(TEXT("Mana")) <= 0.0f)
	{
		ResourceMax.FindOrAdd(TEXT("Mana")) = 100.0f;
		Resources.FindOrAdd(TEXT("Mana")) = FMath::Clamp(Resources.FindRef(TEXT("Mana")), 0.0f, 100.0f);
	}

	SyncLegacyViews();
	BroadcastChanged();
}

// ---------------------------------------------------------------------------------------------
// Console commands — TEST HARNESS ONLY.
//
// These exist so the wallet can be exercised in PIE without first building pickup or HUD assets
// (those are Kiro's lane). They call exactly the same public API a Blueprint would, so proving
// the behaviour here proves it for the real consumers too.
//
//   melodia.Wallet.Dump
//   melodia.Wallet.Grant <Element> <Amount> [GrantId]
//   melodia.Wallet.Spend <Element> <Amount>
//   melodia.Wallet.AddMana <Amount>
//   melodia.Wallet.SpendMana <Amount>
//
// The restart-idempotency check: Grant with a GrantId, save, fully exit, relaunch, load, then
// Grant with the SAME GrantId — it must be rejected.
// ---------------------------------------------------------------------------------------------
namespace
{
	UMelodiaTokenWalletSubsystem* WalletFromWorld(const UWorld* World)
	{
		UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
		return GI ? GI->GetSubsystem<UMelodiaTokenWalletSubsystem>() : nullptr;
	}

	void DumpWallet(UMelodiaTokenWalletSubsystem* Wallet)
	{
		const FMelodiaWalletSnapshot Snap = Wallet->GetSnapshot();
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WALLET mana=%.1f/%.1f golden=%d total=%d"),
			Snap.ManaCurrent, Snap.ManaMax, Snap.GoldenTokens, Snap.TotalCollected);
		for (const FName& Element : UMelodiaTokenWalletSubsystem::GetElementNames())
		{
			const int32* Found = Snap.Shards.Find(Element);
			UE_LOG(LogTemp, Log, TEXT("MELODIA_WALLET   %s = %d"),
				*Element.ToString(), Found ? *Found : 0);
		}
	}

	FAutoConsoleCommandWithWorldAndArgs GMelodiaWalletDump(
		TEXT("melodia.Wallet.Dump"),
		TEXT("Log the authoritative Melody Token wallet snapshot."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World)
			{
				if (UMelodiaTokenWalletSubsystem* Wallet = WalletFromWorld(World))
				{
					DumpWallet(Wallet);
				}
				else
				{
					UE_LOG(LogTemp, Warning, TEXT("MELODIA_WALLET no wallet subsystem (need a running world)"));
				}
			}));

	FAutoConsoleCommandWithWorldAndArgs GMelodiaWalletGrant(
		TEXT("melodia.Wallet.Grant"),
		TEXT("melodia.Wallet.Grant <Element> <Amount> [GrantId] - grant shards; repeat GrantId must be rejected."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World)
			{
				UMelodiaTokenWalletSubsystem* Wallet = WalletFromWorld(World);
				if (!Wallet || Args.Num() < 2)
				{
					UE_LOG(LogTemp, Warning, TEXT("MELODIA_WALLET usage: melodia.Wallet.Grant <Element> <Amount> [GrantId]"));
					return;
				}
				const FName Element(*Args[0]);
				const int32 Amount = FCString::Atoi(*Args[1]);
				const FName GrantId = Args.Num() > 2 ? FName(*Args[2]) : NAME_None;
				const bool bAccepted = Wallet->TryGrantShards(Element, Amount, GrantId);
				UE_LOG(LogTemp, Log, TEXT("MELODIA_WALLET Grant %s x%d id=%s -> %s"),
					*Element.ToString(), Amount, *GrantId.ToString(),
					bAccepted ? TEXT("ACCEPTED") : TEXT("REJECTED"));
				DumpWallet(Wallet);
			}));

	FAutoConsoleCommandWithWorldAndArgs GMelodiaWalletSpend(
		TEXT("melodia.Wallet.Spend"),
		TEXT("melodia.Wallet.Spend <Element> <Amount> - spend shards; unaffordable must be rejected."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World)
			{
				UMelodiaTokenWalletSubsystem* Wallet = WalletFromWorld(World);
				if (!Wallet || Args.Num() < 2)
				{
					UE_LOG(LogTemp, Warning, TEXT("MELODIA_WALLET usage: melodia.Wallet.Spend <Element> <Amount>"));
					return;
				}
				const bool bAccepted = Wallet->TrySpendShards(FName(*Args[0]), FCString::Atoi(*Args[1]));
				UE_LOG(LogTemp, Log, TEXT("MELODIA_WALLET Spend %s x%s -> %s"),
					*Args[0], *Args[1], bAccepted ? TEXT("ACCEPTED") : TEXT("REJECTED"));
				DumpWallet(Wallet);
			}));

	FAutoConsoleCommandWithWorldAndArgs GMelodiaWalletAddMana(
		TEXT("melodia.Wallet.AddMana"),
		TEXT("melodia.Wallet.AddMana <Amount> - add mana; must clamp at ManaMax."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World)
			{
				UMelodiaTokenWalletSubsystem* Wallet = WalletFromWorld(World);
				if (!Wallet || Args.Num() < 1) { return; }
				Wallet->TryAddMana(FCString::Atof(*Args[0]));
				DumpWallet(Wallet);
			}));

	FAutoConsoleCommandWithWorldAndArgs GMelodiaWalletSpendMana(
		TEXT("melodia.Wallet.SpendMana"),
		TEXT("melodia.Wallet.SpendMana <Amount> - spend mana; unaffordable must be rejected."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World)
			{
				UMelodiaTokenWalletSubsystem* Wallet = WalletFromWorld(World);
				if (!Wallet || Args.Num() < 1) { return; }
				const bool bAccepted = Wallet->TrySpendMana(FCString::Atof(*Args[0]));
				UE_LOG(LogTemp, Log, TEXT("MELODIA_WALLET SpendMana %s -> %s"),
					*Args[0], bAccepted ? TEXT("ACCEPTED") : TEXT("REJECTED"));
				DumpWallet(Wallet);
			}));
}
