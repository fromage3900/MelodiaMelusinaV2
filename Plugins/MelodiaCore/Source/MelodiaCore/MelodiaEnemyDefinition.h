// Data-driven enemy definition for Melodia encounters.
// Each encounter trigger references one of these to define the enemy stats.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaEnemyDefinition.generated.h"

USTRUCT(BlueprintType)
struct FMelodiaEnemyDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	FName EnemyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	FText DisplayName = FText::FromString(TEXT("Crystal Shard"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	float MaxHP = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	float MaxToughness = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	float BaseDamage = 15.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	int32 Speed = 80;

	/** Player-facing name for the next enemy action. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Intent")
	FText PrimaryIntentName = FText::FromString(TEXT("Strike"));

	/** Deterministic multiplier applied to BaseDamage for the first slice. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy|Intent")
	float PrimaryIntentDamageMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	EMelodiaSpellElement Element = EMelodiaSpellElement::Forte;

	/** Static mesh to display for this enemy (uses existing BS_GodFile meshes). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	TSoftObjectPtr<UStaticMesh> DisplayMesh;

	/** Material instance for the enemy mesh (e.g., MI_SDF_RosyQuartz). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	TSoftObjectPtr<UMaterialInterface> DisplayMaterial;

	/** Scale multiplier for the display mesh. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	float MeshScale = 1.0f;

	/** BPM override for this enemy's battle music (0 = use level default). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	float BPMOverride = 0.0f;

	/** Boss-tier enemy: used by BossArena stages and boss presentation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	bool bIsBoss = false;
};

/**
 * DataAsset containing a catalog of enemy definitions for encounters.
 * Place in Content/EnvSandbox/Gameplay/Data/
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaEnemyDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Enemy")
	TArray<FMelodiaEnemyDef> Enemies;

	UFUNCTION(BlueprintPure, Category="Melodia|Enemy")
	bool FindEnemyById(FName EnemyId, FMelodiaEnemyDef& OutEnemy) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Enemy")
	FMelodiaEnemyDef GetEnemyByIndex(int32 Index) const;

	/** Built-in demo enemies (no DataAsset file needed for testing). */
	UFUNCTION(BlueprintPure, Category="Melodia|Enemy")
	static TArray<FMelodiaEnemyDef> GetDemoEnemies();
};
