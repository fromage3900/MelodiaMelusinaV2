#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MelodiaEntitlementSubsystem.h"
#include "MelodiaDevEntitlementProvider.generated.h"

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaDevEntitlementProvider : public UObject, public IMelodiaEntitlementProvider
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category="Melodia|Entitlements|Dev")
	bool LoadFromFile();

	UFUNCTION(BlueprintCallable, Category="Melodia|Entitlements|Dev")
	bool SaveToFile();

	virtual TArray<FName> QueryOwnedContentPacks_Implementation() const override;

	UPROPERTY(BlueprintReadWrite, Category="Melodia|Entitlements|Dev")
	TArray<FName> ContentPacks;

	static FString GetDevFilePath();
};
