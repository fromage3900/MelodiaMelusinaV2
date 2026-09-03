#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaPresentationDiagnosticsLibrary.generated.h"

/** On-demand diagnostics for live prototype handoff; never changes gameplay state. */
UCLASS()
class BS_GODFILE_API UMelodiaPresentationDiagnosticsLibrary final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|Diagnostics", meta=(WorldContext="WorldContextObject"))
	static void LogPrototypePresentationState(const UObject* WorldContextObject);

	/** Logs read-only authority/lifecycle state for the accepted JRPG, Persona, and Harmonic foundation. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Diagnostics", meta=(WorldContext="WorldContextObject"))
	static void LogGameplayFoundationState(const UObject* WorldContextObject);
};
