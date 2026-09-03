#include "MelodiaEntitlementSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MelodiaDevEntitlementProvider.h"

UMelodiaEntitlementSubsystem* UMelodiaEntitlementSubsystem::Get(const UObject* WorldContextObject)
{
	if (!WorldContextObject) return nullptr;
	const UWorld* World = WorldContextObject->GetWorld();
	if (!World) return nullptr;
	UGameInstance* GI = World->GetGameInstance();
	return GI ? GI->GetSubsystem<UMelodiaEntitlementSubsystem>() : nullptr;
}

void UMelodiaEntitlementSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	OwnedContentPacks.Add(TEXT("Core"));

#if !UE_BUILD_SHIPPING
	if (UMelodiaDevEntitlementProvider* Dev = NewObject<UMelodiaDevEntitlementProvider>(this))
	{
		if (Dev->LoadFromFile())
		{
			const bool bRefreshed = RefreshCatalog(Dev);
			UE_LOG(LogTemp, Log, TEXT("MelodiaEntitlementSubsystem: startup dev catalog refresh %s with %d entitlements."),
				bRefreshed ? TEXT("succeeded") : TEXT("FAILED"), Dev->ContentPacks.Num());
		}
	}
#endif
}

TArray<FName> UMelodiaEntitlementSubsystem::QueryEntitlements() const
{
	TArray<FName> Result = OwnedContentPacks.Array();
	Result.Sort(FNameLexicalLess());
	return Result;
}

bool UMelodiaEntitlementSubsystem::OwnsContentPack(const FName ContentPackId) const
{
	return ContentPackId.IsNone() || ContentPackId == TEXT("Core") || OwnedContentPacks.Contains(ContentPackId);
}

bool UMelodiaEntitlementSubsystem::GrantDevelopmentEntitlement(const FName ContentPackId)
{
#if UE_BUILD_SHIPPING
	return false;
#else
	if (ContentPackId.IsNone())
	{
		return false;
	}
	OwnedContentPacks.Add(ContentPackId);
	return true;
#endif
}

bool UMelodiaEntitlementSubsystem::RefreshCatalog(UObject* Provider)
{
	if (!IsValid(Provider) || !Provider->GetClass()->ImplementsInterface(UMelodiaEntitlementProvider::StaticClass()))
	{
		return false;
	}

	TSet<FName> Refreshed;
	Refreshed.Add(TEXT("Core"));
	for (const FName ContentPackId : IMelodiaEntitlementProvider::Execute_QueryOwnedContentPacks(Provider))
	{
		if (!ContentPackId.IsNone())
		{
			Refreshed.Add(ContentPackId);
		}
	}
	OwnedContentPacks = MoveTemp(Refreshed);
	return true;
}

bool UMelodiaEntitlementSubsystem::ResolveCosmeticAvailability(const FName RequiredContentPackId) const
{
	return OwnsContentPack(RequiredContentPackId);
}

void UMelodiaEntitlementSubsystem::RestoreFromSave(const TArray<FName>& SavedPacks)
{
	OwnedContentPacks.Empty();
	OwnedContentPacks.Add(TEXT("Core"));
	for (const FName& Pack : SavedPacks)
	{
		if (!Pack.IsNone())
		{
			OwnedContentPacks.Add(Pack);
		}
	}
}
