// MelodiaWardrobe — cosmetic DataAsset + catalog implementation.

#include "MelodiaCosmeticDefinition.h"
#include "Engine/SkeletalMesh.h"

#if WITH_EDITOR
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/UObjectGlobals.h" // GIsEditor
#endif

#if WITH_EDITOR
namespace
{
	FString ResolveDraftPath(const FString& SourceDraftPath)
	{
		TArray<FString> Candidates;
		auto AddCandidate = [&Candidates](FString Candidate)
		{
			if (FPaths::GetExtension(Candidate).IsEmpty())
			{
				Candidate += TEXT(".json");
			}
			Candidates.Add(MoveTemp(Candidate));
		};

		AddCandidate(FPaths::ProjectDir() / SourceDraftPath);
		AddCandidate(FPaths::ProjectDir() / TEXT("Plugins/MelodiaWardrobe/Content") / SourceDraftPath);
		AddCandidate(FPaths::ProjectDir() / TEXT("Imports/Data/Cosmetics") / SourceDraftPath);

		for (const FString& Candidate : Candidates)
		{
			if (FPaths::FileExists(Candidate))
			{
				return Candidate;
			}
		}
		return FString();
	}

	bool TryParseEnumValue(const UEnum* Enum, const FString& Name, uint8& OutValue)
	{
		if (!Enum || Name.IsEmpty())
		{
			return false;
		}

		const FString NormalizedName = Name.TrimStartAndEnd();
		const int64 ExactValue = Enum->GetValueByNameString(NormalizedName);
		if (ExactValue != INDEX_NONE)
		{
			OutValue = static_cast<uint8>(ExactValue);
			return true;
		}

		for (int32 Index = 0; Index < Enum->NumEnums(); ++Index)
		{
			if (Enum->GetNameStringByIndex(Index).Equals(NormalizedName, ESearchCase::IgnoreCase))
			{
				OutValue = static_cast<uint8>(Enum->GetValueByIndex(Index));
				return true;
			}
		}

		return false;
	}
}
#endif

void UMelodiaCosmeticDefinition::PostLoad()
{
	Super::PostLoad();

	bValid = false;

#if WITH_EDITOR
	if (GIsEditor && !SourceDraftPath.IsEmpty())
	{
		const FString FullPath = ResolveDraftPath(SourceDraftPath);
		FString JsonText;
		if (!FullPath.IsEmpty() && FFileHelper::LoadFileToString(JsonText, *FullPath))
		{
			TSharedPtr<FJsonObject> Root;
			const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
			if (FJsonSerializer::Deserialize(Reader, Root) && Root.IsValid())
			{
				FString Id;
				FString SlotName;
				FString RarityName;
				FString ContentPackName;
				const bool bHasId =
					(Root->TryGetStringField(TEXT("CosmeticId"), Id)
						|| Root->TryGetStringField(TEXT("id"), Id))
					&& !Id.IsEmpty();
				const bool bHasSlot =
					(Root->TryGetStringField(TEXT("Slot"), SlotName)
						|| Root->TryGetStringField(TEXT("slot"), SlotName))
					&& !SlotName.IsEmpty();
				const bool bHasRarity =
					(Root->TryGetStringField(TEXT("Rarity"), RarityName)
						|| Root->TryGetStringField(TEXT("rarity"), RarityName))
					&& !RarityName.IsEmpty();
				const bool bHasContentPack =
					(Root->TryGetStringField(TEXT("ContentPackId"), ContentPackName)
						|| Root->TryGetStringField(TEXT("content_pack_id"), ContentPackName))
					&& !ContentPackName.IsEmpty();

				uint8 SlotValue = 0;
				uint8 RarityValue = 0;
				const bool bValidSlot = TryParseEnumValue(
					StaticEnum<EMelodiaWardrobeSlot>(), SlotName, SlotValue);
				const bool bValidRarity = TryParseEnumValue(
					StaticEnum<EMelodiaCosmeticRarity>(), RarityName, RarityValue);
				const bool bDressAlias =
					!bValidSlot && SlotName.Equals(TEXT("dress"), ESearchCase::IgnoreCase);

				if (bHasId && bHasSlot && bHasRarity && (bValidSlot || bDressAlias) && bValidRarity)
				{
					Record.CosmeticId = FName(*Id);
					Record.Slot = bDressAlias
						? EMelodiaWardrobeSlot::Body
						: static_cast<EMelodiaWardrobeSlot>(SlotValue);
					Record.Rarity = static_cast<EMelodiaCosmeticRarity>(RarityValue);
					Record.ContentPackId = NAME_None;
					if (bHasContentPack)
					{
						Record.ContentPackId = FName(*ContentPackName);
					}
					bValid = true;
				}
				else
				{
					UE_LOG(LogTemp, Warning,
						TEXT("MELODIA_WARDROBE %s: draft %s failed required CosmeticId/Slot/Rarity "
							 "mapping (id=%d slot=%d rarity=%d)."),
						*GetName(), *SourceDraftPath, bHasId, bHasSlot && bValidSlot, bHasRarity && bValidRarity);
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("MELODIA_WARDROBE %s: draft %s is not valid JSON."), *GetName(), *SourceDraftPath);
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_WARDROBE %s: source draft %s could not be resolved under the project "
					 "or plugin content roots."),
				*GetName(), *SourceDraftPath);
		}
	}
#endif
}

void UMelodiaCosmeticCatalog::PostLoad()
{
	Super::PostLoad();

#if WITH_EDITOR
	// Surface dangling form references at load, not in PIE. A cosmetic naming a
	// form that does not exist equips fine and grants nothing -- the silent no-op
	// this project keeps paying for. Same reasoning as the draft validation above.
	if (GIsEditor)
	{
		TSet<FName> SeenIds;
		for (const FMelodiaCosmeticRecord& Cosmetic : Cosmetics)
		{
			if (Cosmetic.CosmeticId.IsNone())
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE %s: catalog contains a cosmetic with no CosmeticId."),
					*GetName());
			}
			else if (SeenIds.Contains(Cosmetic.CosmeticId))
			{
				UE_LOG(LogTemp, Error,
					TEXT("MELODIA_WARDROBE %s: duplicate CosmeticId '%s'; catalog lookup is ambiguous."),
					*GetName(), *Cosmetic.CosmeticId.ToString());
			}
			SeenIds.Add(Cosmetic.CosmeticId);

			if (Cosmetic.Mesh.IsNull())
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_WARDROBE %s: cosmetic '%s' has no authored mesh."),
					*GetName(), *Cosmetic.CosmeticId.ToString());
			}
			else if (!Cosmetic.Mesh.LoadSynchronous())
			{
				UE_LOG(LogTemp, Error,
					TEXT("MELODIA_WARDROBE %s: cosmetic '%s' mesh path does not resolve."),
					*GetName(), *Cosmetic.CosmeticId.ToString());
			}
		}

		const TArray<FName> Dangling = FindCosmeticsWithDanglingForm();
		for (const FName CosmeticId : Dangling)
		{
			const FMelodiaCosmeticRecord* Record = FindById(CosmeticId);
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_WARDROBE %s: cosmetic '%s' names ResonantFormId '%s', which is not in ResonantForms. "
					 "It will equip and grant nothing."),
				*GetName(), *CosmeticId.ToString(),
				Record ? *Record->ResonantFormId.ToString() : TEXT("?"));
		}

	}
#endif
}

const FMelodiaCosmeticRecord* UMelodiaCosmeticCatalog::FindById(const FName CosmeticId) const
{
	const FMelodiaCosmeticRecord* Found = nullptr;
	for (const FMelodiaCosmeticRecord& Cosmetic : Cosmetics)
	{
		if (Cosmetic.CosmeticId != CosmeticId)
		{
			continue;
		}

		// Duplicate ids are ambiguous and must fail closed rather than silently
		// selecting whichever record happened to be authored first.
		if (Found)
		{
			return nullptr;
		}
		Found = &Cosmetic;
	}
	return Found;
}

float UMelodiaCosmeticCatalog::GetSlotStyleWeight(const EMelodiaWardrobeSlot Slot) const
{
	// Absent = 1.0 rather than 0.0. An unweighted slot should still count; a
	// designer forgetting to weight a slot must not silently erase it from scoring.
	const float* Found = SlotStyleWeights.Find(Slot);
	return Found ? *Found : 1.0f;
}

const FMelodiaResonantForm* UMelodiaCosmeticCatalog::FindFormById(const FName FormId) const
{
	if (FormId.IsNone())
	{
		return nullptr;
	}
	return ResonantForms.FindByPredicate([FormId](const FMelodiaResonantForm& F)
	{
		return F.FormId == FormId;
	});
}

TArray<FName> UMelodiaCosmeticCatalog::FindCosmeticsWithDanglingForm() const
{
	TArray<FName> Dangling;
	for (const FMelodiaCosmeticRecord& Cosmetic : Cosmetics)
	{
		if (Cosmetic.ResonantFormId.IsNone())
		{
			continue; // purely decorative, which is the common and correct case
		}
		if (!FindFormById(Cosmetic.ResonantFormId))
		{
			Dangling.Add(Cosmetic.CosmeticId);
		}
	}
	return Dangling;
}