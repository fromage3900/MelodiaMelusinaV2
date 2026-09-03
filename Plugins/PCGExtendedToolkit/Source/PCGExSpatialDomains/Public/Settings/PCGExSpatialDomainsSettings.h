// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Channels/PCGExChannelInteractionMatrix.h"
#include "Channels/PCGExSpatialChannels.h"
#include "Engine/DeveloperSettings.h"

#include "PCGExSpatialDomainsSettings.generated.h"

/**
 * A single registered spatial channel. Wraps the FName key in a struct so
 * future per-channel authoring fields (display color, description, default
 * response shorthand, ...) land as pure additions without disturbing the
 * runtime bit-index assignment -- the assignment stays driven by the array
 * order of UPCGExSpatialDomainsSettings::SpatialChannels.
 */
USTRUCT(BlueprintType)
struct PCGEXSPATIALDOMAINS_API FPCGExSpatialChannelDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Channel")
	FName Key = NAME_None;

	// Future fields land here -- e.g.
	//   UPROPERTY(EditAnywhere) FLinearColor DisplayColor = FLinearColor::White;
	//   UPROPERTY(EditAnywhere) FText Description;

	FPCGExSpatialChannelDefinition() = default;

	explicit FPCGExSpatialChannelDefinition(const FName InKey)
		: Key(InKey)
	{
	}
};

/**
 * Project-wide settings for the spatial-domain framework.
 *
 * The single source of truth for the channel registry (which channels exist,
 * in what order -- order determines the bit index in the runtime
 * ChannelMask) and the channel-vs-channel interaction matrix. Lives in the
 * toolkit-level module so consumers other than Valency can author and react
 * to channels.
 */
UCLASS(Config = Editor, DefaultConfig, meta = (DisplayName = "PCGEx | Spatial Domains"))
class PCGEXSPATIALDOMAINS_API UPCGExSpatialDomainsSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPCGExSpatialDomainsSettings();

	virtual void PostInitProperties() override;
	virtual void PostLoad() override;

#if WITH_EDITOR
	virtual void PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

	//~ Begin UDeveloperSettings Interface
	virtual FName GetContainerName() const override
	{
		return "Project";
	}

	virtual FName GetCategoryName() const override
	{
		return "Plugins";
	}

	virtual FName GetSectionName() const override
	{
		return FName("PCGEx | Spatial Domains");
	}

	//~ End UDeveloperSettings Interface

	/**
	 * Registered channels. Order is significant: each entry's array
	 * position is its bit index in the runtime ChannelMask. Inserting
	 * in the middle shifts later indices, so prefer appending. Cap: 32
	 * entries (uint32 mask width).
	 *
	 * The "Default" entry is always present (re-stamped at index 0 by
	 * NormalizeSpatialChannels) and acts as the fallback when an
	 * authored ChannelKey doesn't match any registry entry.
	 */
	UPROPERTY(EditAnywhere, Config, Category = "Channels")
	TArray<FPCGExSpatialChannelDefinition> SpatialChannels;

	/**
	 * Per-channel interaction profiles. Each profile names a candidate
	 * channel and a list of (stored channel, response) overrides;
	 * unlisted pairs default to Block. Compiled into the runtime
	 * FPCGExChannelInteractionMatrix once at module init / on edit.
	 *
	 * Empty here = the matrix is fully Block (current pre-matrix behavior).
	 */
	UPROPERTY(EditAnywhere, Config, Category = "Interaction Matrix")
	TArray<FPCGExChannelProfile> ChannelProfiles;

	/**
	 * Picker source for footprint ChannelKey UPROPERTYs (meta=GetOptions hook).
	 * Extracts the keys from SpatialChannels on demand for the editor combobox.
	 */
	UFUNCTION()
	static TArray<FName> GetChannelKeyOptions();

	/**
	 * Validate a single channel key against the project registry. Unknown
	 * or blank keys are rewritten in-place to Default and a warning is
	 * logged. Editor-only; the runtime hot path trusts the keys pre-baked
	 * at compile time.
	 */
	static void ValidateChannelKey(FName& InOutKey, const UObject* Context = nullptr);

	/** Snapshot of the registered channels (FName-only) -- convenience accessor. */
	static TArray<FName> GetRegisteredKeys();

	/**
	 * Borrow-only accessor for the compiled interaction matrix. The matrix
	 * is rebuilt on every PostInitProperties / PostLoad / PostEditChangeProperty;
	 * callers receive a reference valid for as long as the settings CDO lives
	 * (i.e. for the rest of the editor session). Hot-path callers cache it
	 * once at growth-op init and use the cached reference across queries.
	 */
	static const FPCGExChannelInteractionMatrix& GetCompiledMatrix();

private:
	/** Ensure "Default" is present at index 0; dedupe case-insensitively. */
	void NormalizeSpatialChannels();

	/** Rebuild CompiledMatrix from SpatialChannels + ChannelProfiles. */
	void RebuildCompiledMatrix();

	/**
	 * Runtime-derived matrix. Plain C++ class (not USTRUCT) held by value;
	 * the reflection system skips it entirely. Rebuilt from the non-const
	 * settings lifecycle hooks (PostInitProperties / PostLoad /
	 * PostEditChangeProperty); read-only at runtime via GetCompiledMatrix().
	 */
	FPCGExChannelInteractionMatrix CompiledMatrix;
};
