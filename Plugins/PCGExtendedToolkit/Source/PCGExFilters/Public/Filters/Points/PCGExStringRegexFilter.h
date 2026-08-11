// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Core/PCGExFilterFactoryProvider.h"
#include "UObject/Object.h"
#include "Utils/PCGExRegex.h"

#include "Core/PCGExPointFilter.h"


#include "PCGExStringRegexFilter.generated.h"

namespace PCGExData
{
	template <typename T>
	class TAttributeBroadcaster;
}

USTRUCT(BlueprintType)
struct FPCGExStringRegexFilterConfig
{
	GENERATED_BODY()

	FPCGExStringRegexFilterConfig()
	{
	}

	/** Attribute whose value will be tested against the regex pattern. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable))
	FName OperandA = NAME_None;

	/** Regex pattern to match against. Uses ICU regular expression syntax. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable))
	FString RegexPattern = TEXT(".*");

	/** Invert the filter result (pass becomes fail and vice versa). */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable))
	bool bInvert = false;
};


/**
 *
 */
UCLASS(MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category="PCGEx|Filter")
class UPCGExStringRegexFilterFactory : public UPCGExPointFilterFactoryData
{
	GENERATED_BODY()

public:
	UPROPERTY()
	FPCGExStringRegexFilterConfig Config;

	virtual bool DomainCheck() override;

	virtual TSharedPtr<PCGExPointFilter::IFilter> CreateFilter() const override;
	virtual bool RegisterConsumableAttributesWithData(FPCGExContext* InContext, const UPCGData* InData) const override;
};

namespace PCGExPointFilter
{
	class FStringRegexFilter final : public ISimpleFilter
	{
	public:
		explicit FStringRegexFilter(const TObjectPtr<const UPCGExStringRegexFilterFactory>& InFactory)
			: ISimpleFilter(InFactory)
			  , TypedFilterFactory(InFactory)
		{
		}

		const TObjectPtr<const UPCGExStringRegexFilterFactory> TypedFilterFactory;

		TSharedPtr<PCGExData::TAttributeBroadcaster<FString>> OperandA;
		PCGExRegex::FPattern RegexMatcher;

		virtual bool Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& InPointDataFacade) override;

		virtual bool Test(const int32 PointIndex) const override;
		virtual bool Test(const TSharedPtr<PCGExData::FPointIO>& IO, const TSharedPtr<PCGExData::FPointIOCollection>& ParentCollection) const override;

		virtual ~FStringRegexFilter() override
		{
		}
	};
}

///

UCLASS(MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category="PCGEx|Filter", meta=(PCGExNodeLibraryDoc="filters/point-filters/attribute/filter-regex"))
class UPCGExStringRegexFilterProviderSettings : public UPCGExFilterProviderSettings
{
	GENERATED_BODY()

public:
	//~Begin UPCGSettings
#if WITH_EDITOR
	PCGEX_NODE_INFOS_CUSTOM_SUBTITLE(StringRegexFilterFactory, "Filter : Regex", "Creates a filter definition that tests a string attribute against a regex pattern.", PCGEX_FACTORY_NAME_PRIORITY)
#endif
	//~End UPCGSettings

	/** Filter Config.*/
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable, ShowOnlyInnerProperties))
	FPCGExStringRegexFilterConfig Config;

	virtual UPCGExFactoryData* CreateFactory(FPCGExContext* InContext, UPCGExFactoryData* InFactory) const override;

#if WITH_EDITOR
	virtual FString GetDisplayName() const override;
#endif
};
