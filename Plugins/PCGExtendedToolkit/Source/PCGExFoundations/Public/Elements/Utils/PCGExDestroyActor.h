// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

#include "PCGExCoreMacros.h"
#include "PCGExCoreSettingsCache.h"
#include "Core/PCGExContext.h"
#include "Core/PCGExElement.h"
#include "Core/PCGExSettings.h"

#include "PCGExDestroyActor.generated.h"

UCLASS(MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category="PCGEx|Sampling", meta=(PCGExNodeLibraryDoc="utilities/discarding/destroy-actor"))
class UPCGExDestroyActorSettings : public UPCGExSettings
{
	GENERATED_BODY()

public:
	//~Begin UPCGSettings
#if WITH_EDITOR
	PCGEX_NODE_INFOS(DestroyActor, "Destroy Actor", "Destroy target actor references that have been previously spawned by the PCG component this note is currently executing on.");

	virtual FLinearColor GetNodeTitleColor() const override
	{
		return PCGEX_NODE_COLOR_NAME(MiscRemove);
	}

	virtual EPCGSettingsType GetType() const override
	{
		return EPCGSettingsType::Sampler;
	}
#endif

	// Output pin mirrors the input shape, so e.g. points-in stays points-out.
	virtual bool HasDynamicPins() const override
	{
		return true;
	}

protected:
	virtual TArray<FPCGPinProperties> InputPinProperties() const override;
	virtual TArray<FPCGPinProperties> OutputPinProperties() const override;
	virtual FPCGElementPtr CreateElement() const override;
	//~End UPCGSettings

public:
	/** Attribute holding the actor references to destroy. FString-typed attributes are parsed as soft object paths. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta = (PCG_Overridable))
	FName ActorReferenceAttribute = FName(TEXT("ActorReference"));
};

struct FPCGExDestroyActorContext final : FPCGExContext
{
};

class FPCGExDestroyActorElement final : public IPCGExElement
{
protected:
	PCGEX_ELEMENT_CREATE_CONTEXT(DestroyActor)

	// Actor destruction is game-thread only; run the whole (lightweight) node there and do it
	// synchronously in a single pass -- no async, no deferral.
	virtual bool CanExecuteOnlyOnMainThread(FPCGContext* Context) const override { return true; }

	virtual bool AdvanceWork(FPCGExContext* InContext, const UPCGExSettings* InSettings) const override;
};
