// MelodiaWardrobe — wardrobe state authority (Decision 043).
//
// Owns the owned-set and equipped-map through the canonical narrative record's
// additive v3 fields. Reads and writes through UMelodiaNarrativeSubsystem, so
// wardrobe state survives the same save/load round-trip as quests and stats.

#include "MelodiaWardrobeSubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaTokenWalletSubsystem.h"
#include "MelodiaCosmeticDefinition.h"
#include "MelodiaWardrobeComponent.h"
#include "MelodiaTraversalCapabilityProvider.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/GameInstance.h"
#include "Engine/Engine.h"

namespace
{
	const FString CatalogPath = TEXT("/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog");
}

UMelodiaWardrobeSubsystem* UMelodiaWardrobeSubsystem::Get(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr)
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			return GI->GetSubsystem<UMelodiaWardrobeSubsystem>();
		}
	}
	return nullptr;
}

void UMelodiaWardrobeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UGameInstance* GI = GetGameInstance())
	{
		Narrative = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		if (Narrative)
		{
			Narrative->OnRewardRequested.AddUniqueDynamic(this, &UMelodiaWardrobeSubsystem::HandleNarrativeReward);
		}
		Wallet = GI->GetSubsystem<UMelodiaTokenWalletSubsystem>();
		CapabilityRegistry = GI->GetSubsystem<UMelodiaTraversalCapabilityRegistry>();
		if (CapabilityRegistry.IsValid())
		{
			CapabilityRegistry->RegisterProvider(this, *this);
		}
	}
}

void UMelodiaWardrobeSubsystem::Deinitialize()
{
	if (Narrative)
	{
		Narrative->OnRewardRequested.RemoveDynamic(this, &UMelodiaWardrobeSubsystem::HandleNarrativeReward);
	}
	if (CapabilityRegistry.IsValid())
	{
		CapabilityRegistry->UnregisterProvider(this);
		CapabilityRegistry.Reset();
	}

	Super::Deinitialize();
}

void UMelodiaWardrobeSubsystem::HandleNarrativeReward(const FName RewardId)
{
	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	if (!Catalog || RewardId.IsNone())
	{
		return;
	}

	for (const FMelodiaCosmeticRecord& Cosmetic : Catalog->Cosmetics)
	{
		if (Cosmetic.UnlockRewardId != RewardId
			|| !GrantCosmetic(Cosmetic.CosmeticId, RewardId)
			|| !Cosmetic.bAutoEquipOnUnlock)
		{
			continue;
		}

		APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
		APawn* Pawn = PlayerController ? PlayerController->GetPawn() : nullptr;
		UMelodiaWardrobeComponent* Component = Pawn ? Pawn->FindComponentByClass<UMelodiaWardrobeComponent>() : nullptr;
		if (!Component || !Component->EquipCosmetic(Cosmetic.CosmeticId))
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE reward %s granted %s but auto-equip failed."),
				*RewardId.ToString(), *Cosmetic.CosmeticId.ToString());
		}
	}
}

FMelodiaWardrobeState UMelodiaWardrobeSubsystem::GetState() const
{
	FMelodiaWardrobeState State;
	if (Narrative)
	{
		const FMelodiaNarrativeRecord& Record = Narrative->GetNarrativeRecord();
		State.OwnedCosmeticIds = Record.OwnedCosmeticIds;
		State.EquippedCosmeticIds = Record.EquippedCosmeticIds;
	}
	return State;
}

bool UMelodiaWardrobeSubsystem::IsOwned(const FName CosmeticId) const
{
	return Narrative && Narrative->GetNarrativeRecord().OwnedCosmeticIds.Contains(CosmeticId);
}

FName UMelodiaWardrobeSubsystem::GetEquipped(const EMelodiaWardrobeSlot Slot) const
{
	if (Narrative)
	{
		// GetNarrativeRecord() returns BY VALUE. Calling .Find() straight on the
		// temporary and keeping the pointer is a use-after-free: the temporary dies
		// at the end of the full expression, before *Found is read. It reads
		// plausible garbage rather than crashing, which is why it went unnoticed.
		// Binding to a named const ref extends the temporary's lifetime to the scope,
		// matching GetState() above.
		const FMelodiaNarrativeRecord& Record = Narrative->GetNarrativeRecord();
		if (const FName* Found = Record.EquippedCosmeticIds.Find(Slot))
		{
			return *Found;
		}
	}
	return NAME_None;
}

bool UMelodiaWardrobeSubsystem::GrantCosmetic(const FName CosmeticId, const FName GrantId)
{
	if (!Narrative)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE GrantCosmetic %s rejected: no narrative subsystem."), *CosmeticId.ToString());
		return false;
	}

	// Same-session dedupe (handoff gotcha #3): a GrantId consumed this session
	// is never granted again. This set is runtime-only; the durable guard is
	// ownership, checked below.
	if (GrantId != NAME_None && ConsumedGrantIds.Contains(GrantId))
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE GrantCosmetic %s rejected: grant %s already consumed this session."), *CosmeticId.ToString(), *GrantId.ToString());
		return false;
	}

	// Catalog-first. Validate BEFORE the record is touched -- OwnedCosmeticIds is
	// persisted, so an unvalidated id is a permanent unresolvable entry in the save.
	FName Reason;
	const FMelodiaCosmeticRecord* Catalogued = FindGrantableRecord(CosmeticId, Reason);
	if (!Catalogued)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE GrantCosmetic %s rejected: %s. Narrative record untouched."),
			*CosmeticId.ToString(), *Reason.ToString());
		return false;
	}

	// Durable idempotency. Ownership survives a restart where ConsumedGrantIds does
	// not, so this is the guard that actually holds across a reload. Already owned is
	// success, but it is not a change -- re-broadcasting would make every duplicate
	// gacha pull look like a new acquisition to the UI.
	if (Narrative->GetNarrativeRecord().OwnedCosmeticIds.Contains(CosmeticId))
	{
		if (GrantId != NAME_None)
		{
			ConsumedGrantIds.Add(GrantId);
		}
		UE_LOG(LogTemp, Log,
			TEXT("MELODIA_WARDROBE GrantCosmetic %s: already owned, no-op (grant %s)."),
			*CosmeticId.ToString(), *GrantId.ToString());
		return true;
	}

	FMelodiaNarrativeRecord Record = Narrative->GetNarrativeRecord();
	Record.OwnedCosmeticIds.Add(CosmeticId);
	if (GrantId != NAME_None)
	{
		ConsumedGrantIds.Add(GrantId);
	}
	Narrative->RestoreNarrativeRecord(Record);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE granted %s into slot %d (grant %s)."),
		*CosmeticId.ToString(), static_cast<int32>(Catalogued->Slot), *GrantId.ToString());

	// The cosmetic's own slot, from the catalog record just validated. This used to
	// broadcast EMelodiaWardrobeSlot::Body unconditionally, so every listener saw a
	// hat grant as a body change.
	OnWardrobeChanged.Broadcast(Catalogued->Slot, CosmeticId);
	return true;
}

bool UMelodiaWardrobeSubsystem::EquipCosmetic(const FName CosmeticId)
{
	if (!Narrative)
	{
		return false;
	}
	if (!IsOwned(CosmeticId))
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE EquipCosmetic %s rejected: not owned."), *CosmeticId.ToString());
		return false;
	}

	// Catalog-first, same seam as GrantCosmetic. EquippedCosmeticIds is persisted, so
	// equipping an id the catalog cannot resolve writes a slot entry that no longer
	// presents anything -- and GetSlotForCosmetic() falls back to Body for an unknown
	// id, which would silently overwrite whatever the player actually had on Body.
	FName Reason;
	const FMelodiaCosmeticRecord* Catalogued = FindGrantableRecord(CosmeticId, Reason);
	if (!Catalogued)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE EquipCosmetic %s rejected: %s. Narrative record untouched."),
			*CosmeticId.ToString(), *Reason.ToString());
		return false;
	}

	const EMelodiaWardrobeSlot Slot = Catalogued->Slot;

	FMelodiaNarrativeRecord Record = Narrative->GetNarrativeRecord();
	Record.EquippedCosmeticIds.Add(Slot, CosmeticId);
	Narrative->RestoreNarrativeRecord(Record);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE equipped %s into slot %d."), *CosmeticId.ToString(), static_cast<int32>(Slot));
	OnWardrobeChanged.Broadcast(Slot, CosmeticId);
	return true;
}

bool UMelodiaWardrobeSubsystem::UnequipSlot(const EMelodiaWardrobeSlot Slot)
{
	if (!Narrative)
	{
		return false;
	}

	FMelodiaNarrativeRecord Record = Narrative->GetNarrativeRecord();
	if (!Record.EquippedCosmeticIds.Remove(Slot))
	{
		return false;
	}
	Narrative->RestoreNarrativeRecord(Record);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE unequipped slot %d."), static_cast<int32>(Slot));
	OnWardrobeChanged.Broadcast(Slot, NAME_None);
	return true;
}

bool UMelodiaWardrobeSubsystem::PurchaseCosmetic(const FName CosmeticId, const int32 GoldenPrice)
{
	if (CosmeticId.IsNone())
	{
		return false;
	}
	if (IsOwned(CosmeticId))
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE PurchaseCosmetic %s: already owned, no-op."), *CosmeticId.ToString());
		return true;
	}
	if (GoldenPrice <= 0)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE PurchaseCosmetic %s rejected: price must be positive."),
			*CosmeticId.ToString());
		return false;
	}
	if (!Wallet)
	{
		return false;
	}
	if (!Wallet->TrySpendGolden(GoldenPrice))
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE PurchaseCosmetic %s rejected: not enough Golden."), *CosmeticId.ToString());
		return false;
	}
	const bool bGranted = GrantCosmetic(
		CosmeticId, FName(*FString::Printf(TEXT("Purchase_%s"), *CosmeticId.ToString())));
	if (!bGranted)
	{
		// GrantCosmetic is catalog-first and can still reject when the narrative
		// authority is unavailable. Never consume Golden for a refused grant.
		Wallet->TryRefundGolden(GoldenPrice);
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE PurchaseCosmetic %s: grant refused after spend; Golden refunded."),
			*CosmeticId.ToString());
	}
	return bGranted;
}

bool UMelodiaWardrobeSubsystem::PurchaseCosmeticWithShards(
	const FName CosmeticId, const TMap<FName, int32>& ElementCost)
{
	if (CosmeticId.IsNone())
	{
		return false;
	}
	if (IsOwned(CosmeticId))
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s: already owned, no-op."),
			*CosmeticId.ToString());
		return true;
	}
	if (!Wallet)
	{
		return false;
	}
	if (ElementCost.IsEmpty())
	{
		// A free purchase is almost certainly an unresolved cost map rather than an
		// intentionally free cosmetic. Refuse rather than silently gifting it.
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s rejected: empty cost. "
				 "Resolve through UMelodiaTokenCatalog::ResolveCost first."),
			*CosmeticId.ToString());
		return false;
	}

	// Check the WHOLE cost before spending anything. TrySpendShards is per-element, so
	// without this a two-element price can take the first and fail the second.
	for (const TPair<FName, int32>& Entry : ElementCost)
	{
		if (Entry.Value < 0)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s rejected: negative cost for %s."),
				*CosmeticId.ToString(), *Entry.Key.ToString());
			return false;
		}
		if (Wallet->GetShards(Entry.Key) < Entry.Value)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s rejected: needs %d %s, has %d."),
				*CosmeticId.ToString(), Entry.Value, *Entry.Key.ToString(), Wallet->GetShards(Entry.Key));
			return false;
		}
	}

	// Spend, tracking what actually left the wallet so a late failure can be undone.
	TArray<TPair<FName, int32>> Spent;
	Spent.Reserve(ElementCost.Num());
	auto RefundSpent = [this, &Spent]()
	{
		for (const TPair<FName, int32>& Refund : Spent)
		{
			// Grant with NAME_None: a refund is genuinely repeatable and must not be
			// rejected by the consumed-grant guard.
			Wallet->TryGrantShards(Refund.Key, Refund.Value, NAME_None);
		}
	};

	for (const TPair<FName, int32>& Entry : ElementCost)
	{
		if (Entry.Value == 0)
		{
			continue;
		}
		if (!Wallet->TrySpendShards(Entry.Key, Entry.Value))
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s: spend of %d %s failed after "
					 "affordability check; refunding %d prior element(s)."),
				*CosmeticId.ToString(), Entry.Value, *Entry.Key.ToString(), Spent.Num());
			RefundSpent();
			return false;
		}
		Spent.Emplace(Entry.Key, Entry.Value);
	}

	if (!GrantCosmetic(CosmeticId, FName(*FString::Printf(TEXT("Purchase_%s"), *CosmeticId.ToString()))))
	{
		// Grant refused (already-consumed grant id, or no narrative subsystem). The
		// player must not lose shards for a cosmetic they did not receive.
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_WARDROBE PurchaseCosmeticWithShards %s: grant refused after spend; refunding."),
			*CosmeticId.ToString());
		RefundSpent();
		return false;
	}

	return true;
}

USkeletalMesh* UMelodiaWardrobeSubsystem::GetCosmeticMesh(const FName CosmeticId) const
{
	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	if (!Catalog)
	{
		return nullptr;
	}
	const FMelodiaCosmeticRecord* Record = Catalog->FindById(CosmeticId);
	return Record ? Record->Mesh.LoadSynchronous() : nullptr;
}

EMelodiaWardrobeSlot UMelodiaWardrobeSubsystem::GetSlotForCosmetic(const FName CosmeticId) const
{
	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	if (!Catalog)
	{
		return EMelodiaWardrobeSlot::Body;
	}
	const FMelodiaCosmeticRecord* Record = Catalog->FindById(CosmeticId);
	return Record ? Record->Slot : EMelodiaWardrobeSlot::Body;
}

const UMelodiaCosmeticCatalog* UMelodiaWardrobeSubsystem::ResolveCatalog()
{
	if (CachedCatalog)
	{
		return CachedCatalog;
	}

	CachedCatalog = Cast<UMelodiaCosmeticCatalog>(
		StaticLoadObject(UMelodiaCosmeticCatalog::StaticClass(), nullptr, *CatalogPath));

	if (!CachedCatalog && !bLoggedMissingCatalog)
	{
		// Loud once, not per query. Without the catalog every cosmetic id is unknown,
		// so grant and equip both fail closed -- which is correct, but silence here
		// would make it look like the ids were wrong rather than the asset absent.
		bLoggedMissingCatalog = true;
		UE_LOG(LogTemp, Error,
			TEXT("MELODIA_WARDROBE catalog missing at %s. Every grant and equip will fail "
				 "closed until this DataAsset exists."),
			*CatalogPath);
	}

	return CachedCatalog;
}

const UMelodiaCosmeticCatalog* UMelodiaWardrobeSubsystem::GetCatalog() const
{
	// Lazy resolve: the catalog may be authored after this subsystem initialises.
	return const_cast<UMelodiaWardrobeSubsystem*>(this)->ResolveCatalog();
}

const FMelodiaCosmeticRecord* UMelodiaWardrobeSubsystem::FindGrantableRecord(
	const FName CosmeticId, FName& OutReason) const
{
	OutReason = NAME_None;

	if (CosmeticId.IsNone())
	{
		OutReason = TEXT("unknown_id");
		return nullptr;
	}

	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	if (!Catalog)
	{
		OutReason = TEXT("no_catalog");
		return nullptr;
	}

	const FMelodiaCosmeticRecord* Record = Catalog->FindById(CosmeticId);
	if (!Record)
	{
		OutReason = TEXT("unknown_id");
		return nullptr;
	}

	// A record with no authored mesh can be owned but never presented: the slot
	// component would hold null forever and read as "nothing equipped". Refuse it at
	// the boundary rather than writing an id the presentation layer cannot honour.
	if (Record->Mesh.IsNull())
	{
		OutReason = TEXT("unauthored_mesh");
		return nullptr;
	}

	// A non-null soft path is not proof that the asset exists. Without this
	// load/readback, GrantCosmetic could persist an owned id that EquipCosmetic
	// cannot ever present after a stale redirector or deleted mesh. Validate the
	// resolved object before touching the canonical narrative record.
	if (!Record->Mesh.LoadSynchronous())
	{
		OutReason = TEXT("missing_mesh");
		return nullptr;
	}

	return Record;
}

// --- Resonant Forms: read-only gating queries -------------------------------

namespace
{
	/**
	 * Unlock test against an ALREADY-FETCHED record.
	 *
	 * GetNarrativeRecord() returns the record BY VALUE, so calling the public
	 * IsFormUnlocked() once per equipped slot would copy every map plus the Quill
	 * byte blob on each iteration. Callers fetch the record once and pass it here.
	 */
	bool FormUnlockedAgainst(const FMelodiaResonantForm& Form, const FMelodiaNarrativeRecord& Record)
	{
		for (const FName FlagId : Form.RequiredFlagIds)
		{
			if (!Record.Flags.FindRef(FlagId))
			{
				return false;
			}
		}
		return true; // vacuously true when RequiredFlagIds is empty = ungated
	}
}

bool UMelodiaWardrobeSubsystem::IsFormUnlocked(const FName FormId) const
{
	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	const FMelodiaResonantForm* Form = Catalog ? Catalog->FindFormById(FormId) : nullptr;
	if (!Form)
	{
		// Fail closed. A typo'd or retired FormId withholds an ability rather than
		// silently granting one -- an over-grant is invisible, a missing ability is
		// reported by the player.
		return false;
	}

	if (Form->RequiredFlagIds.IsEmpty())
	{
		return true; // ungated by authorship, no record fetch needed
	}

	if (!Narrative)
	{
		return false;
	}

	// Read through the canonical record. The form does not cache unlock state --
	// there is one persistence seam and this is not it.
	const FMelodiaNarrativeRecord& Record = Narrative->GetNarrativeRecord();
	return FormUnlockedAgainst(*Form, Record);
}

FName UMelodiaWardrobeSubsystem::GetEquippedFormId(const EMelodiaWardrobeSlot Slot) const
{
	const FName CosmeticId = GetEquipped(Slot);
	if (CosmeticId.IsNone())
	{
		return NAME_None;
	}
	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	const FMelodiaCosmeticRecord* Record = Catalog ? Catalog->FindById(CosmeticId) : nullptr;
	return Record ? Record->ResonantFormId : NAME_None;
}

TArray<EMelodiaFormCapability> UMelodiaWardrobeSubsystem::GetActiveCapabilities(const FName ContextId) const
{
	TArray<EMelodiaFormCapability> Active;

	const UMelodiaCosmeticCatalog* Catalog = GetCatalog();
	if (!Catalog || !Narrative)
	{
		return Active;
	}

	// Union across every equipped slot. Two cosmetics granting the same capability
	// is legal and common -- a set that grants Glide twice grants it once.
	const FMelodiaNarrativeRecord& Record = Narrative->GetNarrativeRecord();
	for (const TPair<EMelodiaWardrobeSlot, FName>& Equipped : Record.EquippedCosmeticIds)
	{
		const FMelodiaCosmeticRecord* Cosmetic = Catalog->FindById(Equipped.Value);
		if (!Cosmetic || Cosmetic->ResonantFormId.IsNone())
		{
			continue; // decorative, the common case
		}

		const FMelodiaResonantForm* Form = Catalog->FindFormById(Cosmetic->ResonantFormId);
		if (!Form || !FormUnlockedAgainst(*Form, Record))
		{
			continue; // dangling form or gate not met -- PostLoad already warned on the former
		}

		// A restricted context removes this form's whole contribution, not one
		// capability -- restrictions are authored per form, not per capability.
		if (!ContextId.IsNone() && Form->RestrictedContextIds.Contains(ContextId))
		{
			continue;
		}

		for (const EMelodiaFormCapability Capability : Form->GrantedCapabilities)
		{
			Active.AddUnique(Capability);
		}
	}

	return Active;
}

bool UMelodiaWardrobeSubsystem::IsCapabilityActive(
	const EMelodiaFormCapability Capability, const FName ContextId) const
{
	return GetActiveCapabilities(ContextId).Contains(Capability);
}

bool UMelodiaWardrobeSubsystem::QueryTraversalCapability(
	const FName CapabilityId,
	const FName ContextId,
	FName& OutBlockReason) const
{
	OutBlockReason = NAME_None;

	// Ids come from MelodiaTraversalCapability (game module, owns the interface).
	// Previously these were raw literals duplicated from the caller side, so a rename
	// on either side silently disabled the ability.
	EMelodiaFormCapability Capability;
	if (CapabilityId == MelodiaTraversalCapability::Glide)
	{
		Capability = EMelodiaFormCapability::Glide;
	}
	else if (CapabilityId == MelodiaTraversalCapability::Dash)
	{
		Capability = EMelodiaFormCapability::Dash;
	}
	else if (CapabilityId == MelodiaTraversalCapability::Swim)
	{
		Capability = EMelodiaFormCapability::Swim;
	}
	else
	{
		OutBlockReason = TEXT("unknown_capability");
		return false;
	}

	if (IsCapabilityActive(Capability, ContextId))
	{
		return true;
	}

	OutBlockReason = ContextId.IsNone()
		? FName(TEXT("capability_not_active"))
		: FName(TEXT("capability_blocked_or_locked"));
	return false;
}
