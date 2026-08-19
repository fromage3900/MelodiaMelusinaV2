#include "MelodiaTraversalCapabilityProvider.h"

void UMelodiaTraversalCapabilityRegistry::RegisterProvider(
	UObject* ProviderObject,
	IMelodiaTraversalCapabilityProvider& Provider)
{
	if (!IsValid(ProviderObject))
	{
		return;
	}

	for (FProviderEntry& Entry : Providers)
	{
		if (Entry.Object.Get() == ProviderObject)
		{
			Entry.Provider = &Provider;
			return;
		}

		if (Entry.Object.IsValid())
		{
			UE_LOG(LogTemp, Error,
				TEXT("MelodiaTraversalCapabilityRegistry: rejected second provider %s; canonical provider is %s"),
				*GetNameSafe(ProviderObject), *GetNameSafe(Entry.Object.Get()));
			return;
		}
	}

	FProviderEntry& Entry = Providers.AddDefaulted_GetRef();
	Entry.Object = ProviderObject;
	Entry.Provider = &Provider;
}

void UMelodiaTraversalCapabilityRegistry::UnregisterProvider(UObject* ProviderObject)
{
	if (!ProviderObject)
	{
		return;
	}

	Providers.RemoveAll([ProviderObject](const FProviderEntry& Entry)
	{
		return Entry.Object.Get() == ProviderObject;
	});
}

bool UMelodiaTraversalCapabilityRegistry::QueryCapability(
	const FName CapabilityId,
	const FName ContextId,
	FName& OutBlockReason) const
{
	OutBlockReason = TEXT("capability_provider_missing");

	for (const FProviderEntry& Entry : Providers)
	{
		if (!Entry.Object.IsValid() || !Entry.Provider)
		{
			continue;
		}

		return Entry.Provider->QueryTraversalCapability(CapabilityId, ContextId, OutBlockReason);
	}

	return false;
}

int32 UMelodiaTraversalCapabilityRegistry::GetRegisteredProviderCount() const
{
	int32 Count = 0;
	for (const FProviderEntry& Entry : Providers)
	{
		if (Entry.Object.IsValid() && Entry.Provider)
		{
			++Count;
		}
	}
	return Count;
}
