#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaNPCData.generated.h"

class UBehaviorTree;
class UMaterialInterface;
class USkeletalMesh;
class UStaticMesh;

UENUM(BlueprintType)
enum class EMelodiaNPCRole : uint8
{
	Ambient,
	Merchant,
	Quest,
	Companion
};

/** Minimal runtime NPC contract. Add fields only when a shipping consumer exists. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaNPCDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	FName NPCId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	FText DisplayName = FText::FromString(TEXT("NPC"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	EMelodiaNPCRole Role = EMelodiaNPCRole::Ambient;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC|Visual")
	TSoftObjectPtr<UStaticMesh> StaticMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC|Visual")
	TSoftObjectPtr<USkeletalMesh> SkeletalMesh;

	/** Keys correspond to validated drafts under Imports/Data/Dialogue. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC|Dialogue")
	TArray<FName> DialogueKeys;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC|AI")
	FName BehaviorTag = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC|AI")
	TSoftObjectPtr<UBehaviorTree> BehaviorTree;

	bool IsValid(FText* OutError = nullptr) const;
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaNPCDefinitionAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()
public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|NPC")
	FMelodiaNPCDef Definition;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};