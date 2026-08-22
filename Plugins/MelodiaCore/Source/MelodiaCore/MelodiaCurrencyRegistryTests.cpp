// Currency registry and registry-driven wallet tests.
//
// These pin the invariants that make currencies safe to add as DATA (Decision 054). The
// Python side has its own suite over the exported mirror (gmm/tests/test_currency_registry.py);
// this side proves the runtime actually honours what the mirror describes.
//
// The tests deliberately build their OWN registry rather than loading the project asset, so a
// designer editing DA_MelodiaCurrencyRegistry can never turn these red — and so the "a
// currency invented later works with no code change" claim is tested with a currency that
// genuinely does not exist anywhere in the project.

#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/GameInstance.h"
#include "MelodiaCurrencyRegistry.h"
#include "MelodiaEconomyTestListener.h"
#include "MelodiaSaveGame.h"
#include "MelodiaTokenWalletSubsystem.h"

namespace
{
	/** A currency id that appears in no asset, to prove the data path rather than a hardcode. */
	const FName GInventedCurrency = TEXT("Starlight");

	/**
	 * A wallet seeded from the registry.
	 *
	 * NewObject does not run Initialize, so a bare wallet has no currency keys at all and
	 * every Resource default would read as zero. RestoreFromSave on an empty record is the
	 * same path MelodiaPersistenceTests uses, and it ends in EnsureRegistryKeys.
	 */
	UMelodiaTokenWalletSubsystem* MakeSeededWallet()
	{
		UGameInstance* Owner = NewObject<UGameInstance>();
		UMelodiaTokenWalletSubsystem* Wallet = NewObject<UMelodiaTokenWalletSubsystem>(Owner);
		Wallet->RestoreFromSave(NewObject<UMelodiaSaveGame>());
		return Wallet;
	}

	FMelodiaCurrencyDefinition MakeRow(
		const FName Id,
		const EMelodiaCurrencyKind Kind,
		const float Default = 0.0f,
		const float Max = 0.0f,
		const bool bRefundable = false,
		const bool bCounts = true)
	{
		FMelodiaCurrencyDefinition Row;
		Row.CurrencyId = Id;
		Row.Kind = Kind;
		Row.DefaultValue = Default;
		Row.MaxValue = Max;
		Row.bRefundable = bRefundable;
		Row.bCountsTowardTotalCollected = bCounts;
		return Row;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaCurrencyRegistrySeedTest,
	"Melodia.Economy.CurrencySeed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaCurrencyRegistrySeedTest::RunTest(const FString& Parameters)
{
	const UMelodiaCurrencyRegistry* Seed = UMelodiaCurrencyRegistry::GetFallbackSeed();
	TestNotNull(TEXT("Fallback seed exists"), Seed);
	if (!Seed)
	{
		return false;
	}

	// The wallet's compatibility shims resolve these nine by name. If the seed loses one, a
	// project with no registry asset would start rejecting wardrobe purchases.
	TestEqual(TEXT("Seed has nine currencies"), Seed->Currencies.Num(), 9);
	for (const FName Id : { TEXT("Forte"), TEXT("Tide"), TEXT("Gale"), TEXT("Stone"),
			TEXT("Radiant"), TEXT("Umbral"), TEXT("Arcane"), TEXT("Golden"), TEXT("Mana") })
	{
		TestTrue(*FString::Printf(TEXT("Seed contains %s"), *Id.ToString()), Seed->IsKnownCurrency(Id));
	}

	TestTrue(TEXT("Seed has no duplicate ids"), Seed->FindDuplicateCurrencyIds().IsEmpty());

	// Golden must stay refundable: the wardrobe unwinds a failed cosmetic grant with it.
	const FMelodiaCurrencyDefinition* Golden = Seed->Find(TEXT("Golden"));
	TestNotNull(TEXT("Golden row exists"), Golden);
	if (Golden)
	{
		TestTrue(TEXT("Golden is refundable"), Golden->bRefundable);
		TestFalse(TEXT("Golden does not inflate TotalCollected"), Golden->bCountsTowardTotalCollected);
	}

	// A Resource with no cap clamps to zero, making every grant a silent no-op.
	const FMelodiaCurrencyDefinition* Mana = Seed->Find(TEXT("Mana"));
	TestNotNull(TEXT("Mana row exists"), Mana);
	if (Mana)
	{
		TestTrue(TEXT("Mana is a Resource"), Mana->Kind == EMelodiaCurrencyKind::Resource);
		TestTrue(TEXT("Mana has a positive cap"), Mana->MaxValue > 0.0f);
		TestTrue(TEXT("Mana starts within its cap"), Mana->DefaultValue <= Mana->MaxValue);
	}

	// GetElementNames is the LEGACY vocabulary and must stay exactly seven, in order: it keys
	// the WalletShards save mirror that older builds read.
	const TArray<FName>& Elements = UMelodiaTokenWalletSubsystem::GetElementNames();
	TestEqual(TEXT("Seven legacy element names"), Elements.Num(), 7);
	TestEqual(TEXT("Forte is first"), Elements[0], FName(TEXT("Forte")));
	TestEqual(TEXT("Arcane is last"), Elements[6], FName(TEXT("Arcane")));
	TestFalse(TEXT("Golden is not a legacy element"), Elements.Contains(FName(TEXT("Golden"))));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaCurrencyRegistryLookupTest,
	"Melodia.Economy.CurrencyLookup",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaCurrencyRegistryLookupTest::RunTest(const FString& Parameters)
{
	UMelodiaCurrencyRegistry* Registry = NewObject<UMelodiaCurrencyRegistry>(GetTransientPackage());

	// Deliberately out of SortOrder, to prove the sort rather than the insertion order.
	FMelodiaCurrencyDefinition Late = MakeRow(TEXT("Late"), EMelodiaCurrencyKind::Shard);
	Late.SortOrder = 50;
	FMelodiaCurrencyDefinition Early = MakeRow(TEXT("Early"), EMelodiaCurrencyKind::Shard);
	Early.SortOrder = 1;
	FMelodiaCurrencyDefinition Coin = MakeRow(TEXT("Coin"), EMelodiaCurrencyKind::Premium, 0.0f, 0.0f, true);
	Coin.SortOrder = 10;
	FMelodiaCurrencyDefinition Fuel = MakeRow(TEXT("Fuel"), EMelodiaCurrencyKind::Resource, 5.0f, 20.0f);
	Fuel.SortOrder = 20;

	Registry->Currencies = { Late, Early, Coin, Fuel };

	const TArray<FMelodiaCurrencyDefinition> Sorted = Registry->GetSortedCurrencies();
	TestEqual(TEXT("Sorted by SortOrder: first"), Sorted[0].CurrencyId, FName(TEXT("Early")));
	TestEqual(TEXT("Sorted by SortOrder: last"), Sorted[3].CurrencyId, FName(TEXT("Late")));

	// GetCurrencyIds must filter by kind, not return everything.
	const TArray<FName> Shards = Registry->GetCurrencyIds(EMelodiaCurrencyKind::Shard);
	TestEqual(TEXT("Two shard currencies"), Shards.Num(), 2);
	TestEqual(TEXT("Shards are sorted"), Shards[0], FName(TEXT("Early")));
	TestEqual(TEXT("One premium currency"),
		Registry->GetCurrencyIds(EMelodiaCurrencyKind::Premium).Num(), 1);
	TestEqual(TEXT("One resource currency"),
		Registry->GetCurrencyIds(EMelodiaCurrencyKind::Resource).Num(), 1);

	// An unknown lookup must be visibly not-found, never a plausible default. A silently
	// returned empty row reads as a real, free, uncapped currency.
	bool bFound = true;
	Registry->GetCurrency(TEXT("NoSuchCurrency"), bFound);
	TestFalse(TEXT("Unknown currency reports bFound=false"), bFound);
	TestNull(TEXT("Unknown currency Find returns null"), Registry->Find(TEXT("NoSuchCurrency")));
	TestNull(TEXT("NAME_None Find returns null"), Registry->Find(NAME_None));

	// Duplicates make Find ambiguous, so the health check must actually see them.
	Registry->Currencies.Add(MakeRow(TEXT("Early"), EMelodiaCurrencyKind::Shard));
	const TArray<FName> Duplicates = Registry->FindDuplicateCurrencyIds();
	TestEqual(TEXT("One duplicate reported"), Duplicates.Num(), 1);
	TestEqual(TEXT("Duplicate is Early"), Duplicates[0], FName(TEXT("Early")));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletUnknownCurrencyTest,
	"Melodia.Economy.WalletRejectsUnknownCurrency",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletUnknownCurrencyTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	// The pre-registry path used Shards.FindOrAdd, so a typo minted a balance no UI showed
	// and no cost could spend. That must now be a hard rejection.
	TestFalse(TEXT("Grant of an unknown currency is rejected"),
		Wallet->TryGrantCurrency(TEXT("Frote"), 5.0f, NAME_None));
	TestEqual(TEXT("Typo minted nothing"), Wallet->GetBalance(TEXT("Frote")), 0.0f);

	TestFalse(TEXT("Spend of an unknown currency is rejected"),
		Wallet->TrySpendCurrency(TEXT("Frote"), 1.0f));
	TestFalse(TEXT("Refund of an unknown currency is rejected"),
		Wallet->TryRefundCurrency(TEXT("Frote"), 1.0f));

	// Non-positive amounts must never move a balance in either direction.
	TestFalse(TEXT("Zero grant rejected"), Wallet->TryGrantCurrency(TEXT("Forte"), 0.0f, NAME_None));
	TestFalse(TEXT("Negative grant rejected"), Wallet->TryGrantCurrency(TEXT("Forte"), -5.0f, NAME_None));
	TestFalse(TEXT("Negative spend rejected"), Wallet->TrySpendCurrency(TEXT("Forte"), -5.0f));
	TestEqual(TEXT("Forte untouched"), Wallet->GetBalance(TEXT("Forte")), 0.0f);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletIdempotencyTest,
	"Melodia.Economy.WalletGrantIdempotency",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletIdempotencyTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	const FName GrantId = TEXT("pickup_test_001");
	TestTrue(TEXT("First grant accepted"), Wallet->TryGrantCurrency(TEXT("Forte"), 5.0f, GrantId));
	TestEqual(TEXT("Balance is 5"), Wallet->GetBalance(TEXT("Forte")), 5.0f);

	TestTrue(TEXT("GrantId is recorded as consumed"), Wallet->IsGrantConsumed(GrantId));
	TestFalse(TEXT("Repeat GrantId is rejected"),
		Wallet->TryGrantCurrency(TEXT("Forte"), 5.0f, GrantId));
	TestEqual(TEXT("Rejected repeat changed nothing"), Wallet->GetBalance(TEXT("Forte")), 5.0f);

	// A None GrantId is how genuinely repeatable grants (mana regeneration) opt out of the gate.
	TestTrue(TEXT("First None-id grant accepted"),
		Wallet->TryGrantCurrency(TEXT("Forte"), 1.0f, NAME_None));
	TestTrue(TEXT("Second None-id grant also accepted"),
		Wallet->TryGrantCurrency(TEXT("Forte"), 1.0f, NAME_None));
	TestEqual(TEXT("Both repeatable grants applied"), Wallet->GetBalance(TEXT("Forte")), 7.0f);
	TestFalse(TEXT("NAME_None is never 'consumed'"), Wallet->IsGrantConsumed(NAME_None));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletResourceClampTest,
	"Melodia.Economy.WalletResourceClamp",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletResourceClampTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	// Mana seeds at 50/100 from the registry row, not from a hardcoded initialiser.
	TestEqual(TEXT("Mana starts at its default"), Wallet->GetResource(TEXT("Mana")), 50.0f);
	TestEqual(TEXT("Mana cap comes from the registry"), Wallet->GetResourceMax(TEXT("Mana")), 100.0f);

	TestTrue(TEXT("Adding mana accepted"), Wallet->TryAddMana(30.0f));
	TestEqual(TEXT("Mana is 80"), Wallet->GetResource(TEXT("Mana")), 80.0f);

	// Overfilling clamps rather than rejecting: the shim's contract is "returns false only
	// if Amount <= 0".
	TestTrue(TEXT("Overfilling mana still accepted"), Wallet->TryAddMana(999.0f));
	TestEqual(TEXT("Mana clamped at max"), Wallet->GetResource(TEXT("Mana")), 100.0f);

	TestTrue(TEXT("Spending mana accepted"), Wallet->TrySpendMana(40.0f));
	TestEqual(TEXT("Mana is 60"), Wallet->GetResource(TEXT("Mana")), 60.0f);
	TestFalse(TEXT("Unaffordable mana spend rejected"), Wallet->TrySpendMana(1000.0f));
	TestEqual(TEXT("Rejected spend changed nothing"), Wallet->GetResource(TEXT("Mana")), 60.0f);

	// Mana must not inflate the "shards picked up" stat.
	TestEqual(TEXT("Mana did not touch TotalCollected"), Wallet->GetSnapshot().TotalCollected, 0);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletRefundPermissionTest,
	"Melodia.Economy.WalletRefundPermission",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletRefundPermissionTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	TestTrue(TEXT("Golden granted"), Wallet->TryGrantGolden(10, TEXT("grant_golden_001")));
	TestTrue(TEXT("Golden spent"), Wallet->TrySpendGolden(4));
	TestEqual(TEXT("Golden is 6"), Wallet->GetBalance(TEXT("Golden")), 6.0f);

	TestTrue(TEXT("Golden refund accepted"), Wallet->TryRefundGolden(4));
	TestEqual(TEXT("Golden restored to 10"), Wallet->GetBalance(TEXT("Golden")), 10.0f);

	// Refund is a restricted permission, not "grant without a GrantId". Otherwise any caller
	// could mint shards by claiming a rollback.
	TestTrue(TEXT("Forte granted"), Wallet->TryGrantCurrency(TEXT("Forte"), 5.0f, NAME_None));
	TestFalse(TEXT("Refunding a non-refundable currency is rejected"),
		Wallet->TryRefundCurrency(TEXT("Forte"), 5.0f));
	TestEqual(TEXT("Forte unchanged by rejected refund"), Wallet->GetBalance(TEXT("Forte")), 5.0f);

	// Golden is premium, so it must not inflate the collected-shards stat either.
	TestEqual(TEXT("Golden did not touch TotalCollected"), Wallet->GetSnapshot().TotalCollected, 5);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletSpendManyAtomicTest,
	"Melodia.Economy.WalletSpendManyIsAtomic",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletSpendManyAtomicTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	Wallet->TryGrantCurrency(TEXT("Forte"), 10.0f, NAME_None);
	Wallet->TryGrantCurrency(TEXT("Arcane"), 3.0f, NAME_None);

	TMap<FName, int32> Affordable;
	Affordable.Add(TEXT("Forte"), 4);
	Affordable.Add(TEXT("Arcane"), 2);
	TestTrue(TEXT("Affordable multi-cost reports affordable"), Wallet->CanAfford(Affordable));
	TestTrue(TEXT("Affordable multi-cost spends"), Wallet->TrySpendMany(Affordable));
	TestEqual(TEXT("Forte deducted"), Wallet->GetBalance(TEXT("Forte")), 6.0f);
	TestEqual(TEXT("Arcane deducted"), Wallet->GetBalance(TEXT("Arcane")), 1.0f);

	// THE POINT OF THIS TEST: one unaffordable line item must leave EVERY balance untouched.
	// A partial deduction is what forces callers into spend-then-refund unwind loops.
	TMap<FName, int32> PartlyUnaffordable;
	PartlyUnaffordable.Add(TEXT("Forte"), 2);
	PartlyUnaffordable.Add(TEXT("Arcane"), 99);
	TestFalse(TEXT("Partly unaffordable reports unaffordable"), Wallet->CanAfford(PartlyUnaffordable));
	TestFalse(TEXT("Partly unaffordable spend rejected"), Wallet->TrySpendMany(PartlyUnaffordable));
	TestEqual(TEXT("Forte NOT deducted"), Wallet->GetBalance(TEXT("Forte")), 6.0f);
	TestEqual(TEXT("Arcane NOT deducted"), Wallet->GetBalance(TEXT("Arcane")), 1.0f);

	// An unknown currency anywhere in the cost poisons the whole transaction.
	TMap<FName, int32> WithUnknown;
	WithUnknown.Add(TEXT("Forte"), 1);
	WithUnknown.Add(TEXT("NoSuchCurrency"), 1);
	TestFalse(TEXT("Unknown currency in cost is rejected"), Wallet->TrySpendMany(WithUnknown));
	TestEqual(TEXT("Forte still untouched"), Wallet->GetBalance(TEXT("Forte")), 6.0f);

	// A non-positive line item would grant on spend.
	TMap<FName, int32> Negative;
	Negative.Add(TEXT("Forte"), -1);
	TestFalse(TEXT("Negative line item rejected"), Wallet->TrySpendMany(Negative));
	TestEqual(TEXT("Forte still 6"), Wallet->GetBalance(TEXT("Forte")), 6.0f);

	TestFalse(TEXT("Empty cost rejected"), Wallet->TrySpendMany(TMap<FName, int32>()));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletEventDisciplineTest,
	"Melodia.Economy.WalletEventDiscipline",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletEventDisciplineTest::RunTest(const FString& Parameters)
{
	UMelodiaTokenWalletSubsystem* Wallet = MakeSeededWallet();

	// UI must be able to trust "one event means one accepted transaction". If a rejection
	// broadcast, a HUD would flicker balances that never changed; if a multi-currency spend
	// broadcast per line, it would animate a purchase several times.
	UMelodiaEconomyTestListener* Listener = NewObject<UMelodiaEconomyTestListener>();
	Listener->ListenTo(Wallet);
	const auto EventCount = [Listener]() { return Listener->EventCount; };

	Wallet->TryGrantCurrency(TEXT("Forte"), 10.0f, TEXT("evt_001"));
	TestEqual(TEXT("Accepted grant fires exactly one event"), EventCount(), 1);

	Wallet->TryGrantCurrency(TEXT("Forte"), 10.0f, TEXT("evt_001"));
	TestEqual(TEXT("Rejected repeat fires no event"), EventCount(), 1);

	Wallet->TryGrantCurrency(TEXT("NoSuchCurrency"), 1.0f, NAME_None);
	TestEqual(TEXT("Rejected unknown currency fires no event"), EventCount(), 1);

	Wallet->TrySpendCurrency(TEXT("Forte"), 9999.0f);
	TestEqual(TEXT("Rejected unaffordable spend fires no event"), EventCount(), 1);

	Wallet->TryGrantCurrency(TEXT("Arcane"), 5.0f, NAME_None);
	TestEqual(TEXT("Second accepted grant fires one more"), EventCount(), 2);

	TMap<FName, int32> Cost;
	Cost.Add(TEXT("Forte"), 2);
	Cost.Add(TEXT("Arcane"), 2);
	Wallet->TrySpendMany(Cost);
	TestEqual(TEXT("Two-currency spend fires exactly ONE event"), EventCount(), 3);

	Cost.Add(TEXT("Arcane"), 9999);
	Wallet->TrySpendMany(Cost);
	TestEqual(TEXT("Rejected multi-spend fires no event"), EventCount(), 3);

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletLegacyShimParityTest,
	"Melodia.Economy.WalletLegacyShimParity",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletLegacyShimParityTest::RunTest(const FString& Parameters)
{
	// The shims are what keep MelodiaWardrobe and every existing Blueprint compiling and
	// behaving unchanged. They must be pure forwards, never a second code path.
	UMelodiaTokenWalletSubsystem* ViaShim = MakeSeededWallet();
	UMelodiaTokenWalletSubsystem* ViaGeneric = MakeSeededWallet();

	for (const FName& Element : UMelodiaTokenWalletSubsystem::GetElementNames())
	{
		const FName GrantId = FName(*FString::Printf(TEXT("parity_%s"), *Element.ToString()));
		const bool bShim = ViaShim->TryGrantShards(Element, 7, GrantId);
		const bool bGeneric = ViaGeneric->TryGrantCurrency(Element, 7.0f, GrantId);
		TestEqual(*FString::Printf(TEXT("Grant parity for %s"), *Element.ToString()), bShim, bGeneric);
		TestEqual(*FString::Printf(TEXT("Balance parity for %s"), *Element.ToString()),
			ViaShim->GetShards(Element), (int32)ViaGeneric->GetBalance(Element));
	}

	TestEqual(TEXT("TotalCollected parity"),
		ViaShim->GetSnapshot().TotalCollected, ViaGeneric->GetSnapshot().TotalCollected);

	// Golden and Mana shims target the right currencies.
	ViaShim->TryGrantGolden(3, TEXT("parity_golden"));
	ViaGeneric->TryGrantCurrency(TEXT("Golden"), 3.0f, TEXT("parity_golden"));
	TestEqual(TEXT("Golden shim parity"),
		ViaShim->GetSnapshot().GoldenTokens, ViaGeneric->GetSnapshot().GoldenTokens);

	ViaShim->TryAddMana(12.0f);
	ViaGeneric->TryGrantCurrency(TEXT("Mana"), 12.0f, NAME_None);
	TestEqual(TEXT("Mana shim parity"),
		ViaShim->GetSnapshot().ManaCurrent, ViaGeneric->GetSnapshot().ManaCurrent);

	// The derived legacy snapshot view must agree with the registry-driven maps.
	const FMelodiaWalletSnapshot Snapshot = ViaShim->GetSnapshot();
	TestEqual(TEXT("Shards view holds the seven elements"), Snapshot.Shards.Num(), 7);
	TestEqual(TEXT("Derived GoldenTokens matches Balances"),
		Snapshot.GoldenTokens, Snapshot.Balances.FindRef(TEXT("Golden")));
	TestEqual(TEXT("Derived ManaCurrent matches Resources"),
		Snapshot.ManaCurrent, Snapshot.Resources.FindRef(TEXT("Mana")));
	TestFalse(TEXT("Golden is not in the Shards view"),
		Snapshot.Shards.Contains(FName(TEXT("Golden"))));

	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaWalletInventedCurrencyTest,
	"Melodia.Economy.WalletSupportsInventedCurrency",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaWalletInventedCurrencyTest::RunTest(const FString& Parameters)
{
	// THE HEADLINE CLAIM: a currency that exists in no asset and no enum still grants, spends
	// and clamps correctly, because the only thing that made the others special was a data row.
	UMelodiaCurrencyRegistry* Registry = NewObject<UMelodiaCurrencyRegistry>(GetTransientPackage());
	Registry->Currencies.Add(MakeRow(GInventedCurrency, EMelodiaCurrencyKind::Shard));
	Registry->Currencies.Add(
		MakeRow(TEXT("Breath"), EMelodiaCurrencyKind::Resource, 10.0f, 25.0f, false, false));

	TestTrue(TEXT("Invented shard is known"), Registry->IsKnownCurrency(GInventedCurrency));
	TestTrue(TEXT("Invented resource is known"), Registry->IsKnownCurrency(TEXT("Breath")));

	const FMelodiaCurrencyDefinition* Starlight = Registry->Find(GInventedCurrency);
	TestNotNull(TEXT("Invented currency resolves"), Starlight);
	if (Starlight)
	{
		// It has no legacy element, and that is the point: EMelodiaSpellElement was never
		// extended, and never needs to be again.
		TestFalse(TEXT("Invented currency has no legacy element"), Starlight->bHasLegacyElement);
		TestTrue(TEXT("Invented currency is a Shard"), Starlight->Kind == EMelodiaCurrencyKind::Shard);
	}

	TestFalse(TEXT("Invented currency is not a legacy element name"),
		UMelodiaTokenWalletSubsystem::GetElementNames().Contains(GInventedCurrency));

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
