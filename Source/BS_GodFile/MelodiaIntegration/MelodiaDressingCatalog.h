#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "MelodiaDressingCatalog.generated.h"

class UMaterialInterface;
class UStaticMesh;

/**
 * One hero prop inside a dressing family.
 *
 * A prop names an EXISTING library asset. The catalogue never points at a
 * different master: the mesh and the material instance are the ones the artist
 * already placed (or the converted Enchanted Interiors instances on
 * M_Master_Toon_Universal).
 */
USTRUCT(BlueprintType)
struct FMelodiaDressingProp
{
	GENERATED_BODY()

	/** The prop's own tag, in the artist's vocabulary: "Prop_SM_Desk". */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	FName PropTag;

	/** The legacy artist tag this prop was recorded under, if any. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	FName ArtistTag;

	/** The mesh to place. Soft, so the catalogue loads fast. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	TSoftObjectPtr<UStaticMesh> Mesh;

	/** The material instance to place it with. Optional. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	TSoftObjectPtr<UMaterialInterface> MaterialOverride;

	/** How many of this prop the family holds. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing", meta = (ClampMin = "0"))
	int32 Count = 1;

	/** True when the prop should be DROPPED and left to settle, not placed. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	bool bSettlesUnderGravity = false;

	/** Restitution for a settling prop. 0 = dead, 1 = bouncy. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Restitution = 0.25f;
};

/**
 * One dressing family: a room's hero props.
 *
 * A family is a ROOM, not a mesh list. A dressing pass asks for a room and gets
 * that room's hero props - so the pass can be re-run per room without knowing
 * what is in it.
 */
USTRUCT(BlueprintType)
struct FMelodiaDressingFamily
{
	GENERATED_BODY()

	/** The gameplay-tag family key. Melodia.Dressing.Room.Bedroom and friends. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	FGameplayTag FamilyTag;

	/** The legacy artist tag: "Room_bedroom". The pass can ask for either. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	FName ArtistTag;

	/** What this family is for. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	FText Description;

	/** The hero props in this family. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	TArray<FMelodiaDressingProp> Props;
};

/**
 * The hero-prop catalogue the art pass reads.
 *
 * Implements the Dash role's catalogue (Docs/Research/
 * DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md): a DataAsset keyed by
 * gameplay-tag family -> hero prop set, reusing the existing SM_/MI_ library
 * instead of creating a new authority.
 *
 * The CONTENT is derived from the artist's own placements and recorded in
 * specs/p0/melusina_dressing_catalog.v1.json; this class is the container that
 * lets the art pass load it.
 */
UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaDressingCatalog : public UDataAsset
{
	GENERATED_BODY()

public:
	/** Every family in the catalogue. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Dressing")
	TArray<FMelodiaDressingFamily> Families;

	/**
	 * The family for a gameplay tag, or nullptr.
	 * An invalid tag never matches.
	 */
	const FMelodiaDressingFamily* FindFamily(const FGameplayTag& FamilyTag) const;

	/**
	 * The family named by an artist tag ("Room_bedroom"), or nullptr.
	 * This is the vocabulary the artist's own actors already carry.
	 */
	const FMelodiaDressingFamily* FindFamilyByArtistTag(const FName& ArtistTag) const;

	/** The props of a family. Empty when the family is unknown. */
	TArray<FMelodiaDressingProp> PropsForFamily(const FGameplayTag& FamilyTag) const;

	/** Every family tag the catalogue knows. */
	TArray<FGameplayTag> FamilyTags() const;

	/** How many families the catalogue holds. */
	int32 FamilyCount() const { return Families.Num(); }
};
