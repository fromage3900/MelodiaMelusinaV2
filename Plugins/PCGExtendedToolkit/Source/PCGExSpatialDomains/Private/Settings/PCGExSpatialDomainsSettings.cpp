// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Settings/PCGExSpatialDomainsSettings.h"

DEFINE_LOG_CATEGORY_STATIC(LogPCGExSpatialDomainsSettings, Log, All);

UPCGExSpatialDomainsSettings::UPCGExSpatialDomainsSettings()
{
	// Seed with the always-present Default channel. NormalizeSpatialChannels
	// re-asserts this on every load/edit, so the seed is just for fresh installs.
	SpatialChannels = {FPCGExSpatialChannelDefinition{PCGExSpatialChannels::Default}};
}

void UPCGExSpatialDomainsSettings::PostInitProperties()
{
	Super::PostInitProperties();
	NormalizeSpatialChannels();
	RebuildCompiledMatrix();
}

void UPCGExSpatialDomainsSettings::PostLoad()
{
	Super::PostLoad();
	NormalizeSpatialChannels();
	RebuildCompiledMatrix();
}

#if WITH_EDITOR
void UPCGExSpatialDomainsSettings::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	NormalizeSpatialChannels();
	RebuildCompiledMatrix();
}
#endif

TArray<FName> UPCGExSpatialDomainsSettings::GetChannelKeyOptions()
{
	return GetRegisteredKeys();
}

TArray<FName> UPCGExSpatialDomainsSettings::GetRegisteredKeys()
{
	if (const UPCGExSpatialDomainsSettings* Settings = GetDefault<UPCGExSpatialDomainsSettings>())
	{
		TArray<FName> Out;
		Out.Reserve(Settings->SpatialChannels.Num());
		for (const FPCGExSpatialChannelDefinition& Definition : Settings->SpatialChannels)
		{
			Out.Add(Definition.Key);
		}
		return Out;
	}
	return {PCGExSpatialChannels::Default};
}

void UPCGExSpatialDomainsSettings::ValidateChannelKey(FName& InOutKey, const UObject* Context)
{
	const UPCGExSpatialDomainsSettings* Settings = GetDefault<UPCGExSpatialDomainsSettings>();
	if (!Settings)
	{
		return;
	}

	const bool bKnown = !InOutKey.IsNone()
		&& Settings->SpatialChannels.ContainsByPredicate(
			[Key = InOutKey](const FPCGExSpatialChannelDefinition& Existing)
			{
				return Existing.Key.IsEqual(Key, ENameCase::IgnoreCase);
			});
	if (bKnown)
	{
		return;
	}

	UE_LOG(LogPCGExSpatialDomainsSettings, Warning,
	       TEXT("Spatial channel key '%s' (context: %s) not in project registry; falling back to 'Default'."),
	       *InOutKey.ToString(),
	       Context ? *Context->GetPathName() : TEXT("<unknown>"));
	InOutKey = PCGExSpatialChannels::Default;
}

const FPCGExChannelInteractionMatrix& UPCGExSpatialDomainsSettings::GetCompiledMatrix()
{
	if (const UPCGExSpatialDomainsSettings* Settings = GetDefault<UPCGExSpatialDomainsSettings>())
	{
		return Settings->CompiledMatrix;
	}
	// Defensive fallback for the (impossible-in-practice) case where the CDO
	// isn't available -- a static all-Block matrix keeps callers safe.
	static const FPCGExChannelInteractionMatrix Fallback;
	return Fallback;
}

void UPCGExSpatialDomainsSettings::RebuildCompiledMatrix()
{
	// Snapshot the FNames in order so the matrix's bit indices match
	// SpatialChannels positions exactly.
	TArray<FName> Keys;
	Keys.Reserve(SpatialChannels.Num());
	for (const FPCGExSpatialChannelDefinition& Entry : SpatialChannels)
	{
		Keys.Add(Entry.Key);
	}

	CompiledMatrix.Compile(Keys, ChannelProfiles);
}

void UPCGExSpatialDomainsSettings::NormalizeSpatialChannels()
{
	// Drop None entries; dedupe case-insensitively while preserving order.
	TArray<FPCGExSpatialChannelDefinition> Cleaned;
	Cleaned.Reserve(SpatialChannels.Num() + 1);

	for (const FPCGExSpatialChannelDefinition& Entry : SpatialChannels)
	{
		if (Entry.Key.IsNone())
		{
			continue;
		}
		const bool bAlready = Cleaned.ContainsByPredicate(
			[Key = Entry.Key](const FPCGExSpatialChannelDefinition& Existing)
			{
				return Existing.Key.IsEqual(Key, ENameCase::IgnoreCase);
			});
		if (!bAlready)
		{
			Cleaned.Add(Entry);
		}
	}

	// Default is reserved -- always present at index 0. Re-add even if the user removed it.
	const int32 DefaultIdx = Cleaned.IndexOfByPredicate(
		[](const FPCGExSpatialChannelDefinition& E)
		{
			return E.Key.IsEqual(PCGExSpatialChannels::Default, ENameCase::IgnoreCase);
		});
	if (DefaultIdx == INDEX_NONE)
	{
		Cleaned.Insert(FPCGExSpatialChannelDefinition{PCGExSpatialChannels::Default}, 0);
	}
	else if (DefaultIdx != 0)
	{
		Cleaned.Swap(0, DefaultIdx);
	}

	SpatialChannels = MoveTemp(Cleaned);
}
