#include "MelodiaTokenWalletSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
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
}

void UMelodiaTokenWalletSubsystem::EnsureElementKeys()
{
	// Every element always present, so UI can bind seven rows without null-checking.
	for (const FName& Element : GMelodiaElements)
	{
		if (!Shards.Contains(Element))
		{
			Shards.Add(Element, 0);
		}
	}
}

FMelodiaWalletSnapshot UMelodiaTokenWalletSubsystem::GetSnapshot() const
{
	FMelodiaWalletSnapshot Snapshot;
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
	const int32* Found = Shards.Find(Element);
	return Found ? *Found : 0;
}

bool UMelodiaTokenWalletSubsystem::IsGrantConsumed(const FName GrantId) const
{
	return !GrantId.IsNone() && ConsumedGrantIds.Contains(GrantId);
}

bool UMelodiaTokenWalletSubsystem::TryGrantShards(const FName Element, const int32 Amount, const FName GrantId)
{
	if (Amount <= 0 || Element.IsNone())
	{
		return false;
	}
	// Idempotency gate. Consumed IDs persist, so a battle replayed after a restart, or a
	// pickup that respawns on level reload, cannot pay out twice.
	if (IsGrantConsumed(GrantId))
	{
		return false;
	}

	int32& Balance = Shards.FindOrAdd(Element);
	Balance += Amount;
	TotalCollected += Amount;

	if (!GrantId.IsNone())
	{
		ConsumedGrantIds.Add(GrantId);
	}

	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TrySpendShards(const FName Element, const int32 Amount)
{
	if (Amount <= 0)
	{
		return false;
	}
	int32* Balance = Shards.Find(Element);
	if (!Balance || *Balance < Amount)
	{
		return false; // unaffordable: no state change, no event
	}
	*Balance -= Amount;
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TryAddMana(const float Amount)
{
	if (Amount <= 0.0f)
	{
		return false;
	}
	ManaCurrent = FMath::Min(ManaMax, ManaCurrent + Amount);
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TrySpendMana(const float Amount)
{
	if (Amount <= 0.0f || ManaCurrent < Amount)
	{
		return false;
	}
	ManaCurrent -= Amount;
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TryGrantGolden(const int32 Amount, const FName GrantId)
{
	if (Amount <= 0 || IsGrantConsumed(GrantId))
	{
		return false;
	}
	GoldenTokens += Amount;
	if (!GrantId.IsNone())
	{
		ConsumedGrantIds.Add(GrantId);
	}
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TrySpendGolden(const int32 Amount)
{
	if (Amount <= 0 || GoldenTokens < Amount)
	{
		return false;
	}
	GoldenTokens -= Amount;
	BroadcastChanged();
	return true;
}

bool UMelodiaTokenWalletSubsystem::TryRefundGolden(const int32 Amount)
{
	if (Amount <= 0)
	{
		return false;
	}

	GoldenTokens += Amount;
	BroadcastChanged();
	return true;
}

void UMelodiaTokenWalletSubsystem::CaptureToSave(UMelodiaSaveGame* Save) const
{
	if (!Save)
	{
		return;
	}
	Save->WalletShards = Shards;
	Save->WalletManaCurrent = ManaCurrent;
	Save->WalletManaMax = ManaMax;
	Save->WalletGoldenTokens = GoldenTokens;
	Save->WalletTotalCollected = TotalCollected;
	Save->WalletConsumedGrantIds = ConsumedGrantIds;
	Save->bWalletMigratedFromLegacyTokens = bMigratedFromLegacy;
}

void UMelodiaTokenWalletSubsystem::RestoreFromSave(const UMelodiaSaveGame* Save)
{
	if (!Save)
	{
		return;
	}

	Shards = Save->WalletShards;
	ManaCurrent = Save->WalletManaCurrent;
	ManaMax = Save->WalletManaMax;
	GoldenTokens = Save->WalletGoldenTokens;
	TotalCollected = Save->WalletTotalCollected;
	ConsumedGrantIds = Save->WalletConsumedGrantIds;
	bMigratedFromLegacy = Save->bWalletMigratedFromLegacyTokens;

	// One-way migration from the legacy per-variant ints. Heart maps to Forte and Swirl to
	// Arcane, per the variant->element table in the token contract. The legacy fields are
	// left untouched: UMelodiaRoguelikeRunSubsystem still owns them for run-scoped purposes,
	// and silently zeroing another subsystem's state would be a cross-authority write.
	if (!bMigratedFromLegacy)
	{
		if (Save->HeartMelodyTokens > 0)
		{
			Shards.FindOrAdd(TEXT("Forte")) += Save->HeartMelodyTokens;
			TotalCollected += Save->HeartMelodyTokens;
		}
		if (Save->SwirlMelodyTokens > 0)
		{
			Shards.FindOrAdd(TEXT("Arcane")) += Save->SwirlMelodyTokens;
			TotalCollected += Save->SwirlMelodyTokens;
		}
		// Flag lives on the wallet; CaptureToSave writes it back into the record on next save.
		bMigratedFromLegacy = true;

		UE_LOG(LogTemp, Log,
			TEXT("MELODIA_WALLET migrated legacy tokens: Heart=%d -> Forte, Swirl=%d -> Arcane"),
			Save->HeartMelodyTokens, Save->SwirlMelodyTokens);
	}

	// Legacy saves carry a zeroed mana block; restore sane defaults rather than a dead wallet.
	if (ManaMax <= 0.0f)
	{
		ManaMax = 100.0f;
		ManaCurrent = FMath::Clamp(ManaCurrent, 0.0f, ManaMax);
	}

	EnsureElementKeys();
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
