#include "MonolithMeshPresetActions.h"
#include "MonolithMeshStorytellingPatterns.h"
#include "MonolithMeshAcoustics.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFileManager.h"

// ============================================================================
// Directory helpers
// ============================================================================

FString FMonolithMeshPresetActions::GetPatternsDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("Patterns");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

FString FMonolithMeshPresetActions::GetAcousticProfilesDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("AcousticProfiles");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

FString FMonolithMeshPresetActions::GetTensionProfilesDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("TensionProfiles");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

FString FMonolithMeshPresetActions::GetPresetsDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("Presets");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

FString FMonolithMeshPresetActions::GetTemplatesDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("Templates");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

FString FMonolithMeshPresetActions::GetPropKitsDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("PropKits");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

// ============================================================================
// JSON I/O helpers
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshPresetActions::LoadJsonFile(const FString& FilePath, FString& OutError)
{
	FString JsonStr;
	if (!FFileHelper::LoadFileToString(JsonStr, *FilePath))
	{
		OutError = FString::Printf(TEXT("File not found: %s"), *FilePath);
		return nullptr;
	}

	TSharedPtr<FJsonObject> JsonObj;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
	if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
	{
		OutError = FString::Printf(TEXT("Failed to parse JSON: %s"), *FilePath);
		return nullptr;
	}

	return JsonObj;
}

bool FMonolithMeshPresetActions::SaveJsonFile(const FString& FilePath, const TSharedPtr<FJsonObject>& JsonObj, FString& OutError)
{
	FString JsonStr;
	TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&JsonStr);
	if (!FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer))
	{
		OutError = TEXT("Failed to serialize JSON");
		return false;
	}

	if (!FFileHelper::SaveStringToFile(JsonStr, *FilePath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		OutError = FString::Printf(TEXT("Failed to write file: %s"), *FilePath);
		return false;
	}

	return true;
}

TArray<FString> FMonolithMeshPresetActions::ListJsonFiles(const FString& Directory)
{
	TArray<FString> Files;
	IFileManager::Get().FindFiles(Files, *(Directory / TEXT("*.json")), true, false);
	return Files;
}

// ============================================================================
// Serialization helpers
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshPresetActions::StorytellingElementToJson(const FStorytellingElement& Elem)
{
	auto Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("label"), Elem.Label);
	Obj->SetStringField(TEXT("type"), Elem.Type);

	// Relative offset
	TArray<TSharedPtr<FJsonValue>> OffsetArr;
	OffsetArr.Add(MakeShared<FJsonValueNumber>(Elem.RelativeOffset.X));
	OffsetArr.Add(MakeShared<FJsonValueNumber>(Elem.RelativeOffset.Y));
	OffsetArr.Add(MakeShared<FJsonValueNumber>(Elem.RelativeOffset.Z));
	Obj->SetArrayField(TEXT("relative_offset"), OffsetArr);

	// Size
	TArray<TSharedPtr<FJsonValue>> SizeArr;
	SizeArr.Add(MakeShared<FJsonValueNumber>(Elem.Size.X));
	SizeArr.Add(MakeShared<FJsonValueNumber>(Elem.Size.Y));
	SizeArr.Add(MakeShared<FJsonValueNumber>(Elem.Size.Z));
	Obj->SetArrayField(TEXT("size"), SizeArr);

	Obj->SetBoolField(TEXT("radial"), Elem.bRadial);
	Obj->SetNumberField(TEXT("radial_min"), Elem.RadialMin);
	Obj->SetNumberField(TEXT("radial_max"), Elem.RadialMax);
	Obj->SetNumberField(TEXT("count_min"), Elem.CountMin);
	Obj->SetNumberField(TEXT("count_max"), Elem.CountMax);
	Obj->SetNumberField(TEXT("rotation_variance"), Elem.RotationVariance);
	Obj->SetNumberField(TEXT("scale_variance"), Elem.ScaleVariance);
	Obj->SetBoolField(TEXT("wall_element"), Elem.bWallElement);

	return Obj;
}

TSharedPtr<FJsonObject> FMonolithMeshPresetActions::StorytellingPatternToJson(const FStorytellingPattern& Pattern)
{
	auto Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("name"), Pattern.Name);
	Obj->SetStringField(TEXT("description"), Pattern.Description);
	Obj->SetStringField(TEXT("source"), TEXT("built-in"));

	TArray<TSharedPtr<FJsonValue>> ElementsArr;
	for (const FStorytellingElement& Elem : Pattern.Elements)
	{
		ElementsArr.Add(MakeShared<FJsonValueObject>(StorytellingElementToJson(Elem)));
	}
	Obj->SetArrayField(TEXT("elements"), ElementsArr);

	return Obj;
}

TSharedPtr<FJsonObject> FMonolithMeshPresetActions::AcousticPropsToJson(const FString& SurfaceName, float Absorption, float TransmissionLossdB, float FootstepLoudness)
{
	auto Obj = MakeShared<FJsonObject>();
	Obj->SetStringField(TEXT("surface_name"), SurfaceName);
	Obj->SetNumberField(TEXT("absorption"), Absorption);
	Obj->SetNumberField(TEXT("transmission_loss_db"), TransmissionLossdB);
	Obj->SetNumberField(TEXT("footstep_loudness"), FootstepLoudness);
	return Obj;
}

// ============================================================================
// Validation helpers
// ============================================================================

bool FMonolithMeshPresetActions::ValidateStorytellingPatternJson(const TSharedPtr<FJsonObject>& Json, FString& OutError)
{
	FString Name;
	if (!Json->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		OutError = TEXT("Pattern missing required field: name");
		return false;
	}

	FString Description;
	if (!Json->TryGetStringField(TEXT("description"), Description))
	{
		OutError = TEXT("Pattern missing required field: description");
		return false;
	}

	const TArray<TSharedPtr<FJsonValue>>* ElementsArr;
	if (!Json->TryGetArrayField(TEXT("elements"), ElementsArr) || ElementsArr->Num() == 0)
	{
		OutError = TEXT("Pattern missing or empty required field: elements");
		return false;
	}

	for (int32 i = 0; i < ElementsArr->Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* ElemObjPtr;
		if (!(*ElementsArr)[i]->TryGetObject(ElemObjPtr) || !ElemObjPtr || !(*ElemObjPtr).IsValid())
		{
			OutError = FString::Printf(TEXT("Element %d is not a valid JSON object"), i);
			return false;
		}

		FString Label;
		if (!(*ElemObjPtr)->TryGetStringField(TEXT("label"), Label))
		{
			OutError = FString::Printf(TEXT("Element %d missing required field: label"), i);
			return false;
		}

		FString Type;
		if (!(*ElemObjPtr)->TryGetStringField(TEXT("type"), Type))
		{
			OutError = FString::Printf(TEXT("Element %d missing required field: type"), i);
			return false;
		}

		if (Type != TEXT("decal") && Type != TEXT("prop"))
		{
			OutError = FString::Printf(TEXT("Element %d type must be 'decal' or 'prop', got '%s'"), i, *Type);
			return false;
		}
	}

	return true;
}

bool FMonolithMeshPresetActions::ValidateAcousticProfileJson(const TSharedPtr<FJsonObject>& Json, FString& OutError)
{
	FString Name;
	if (!Json->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		OutError = TEXT("Acoustic profile missing required field: name");
		return false;
	}

	const TArray<TSharedPtr<FJsonValue>>* SurfacesArr;
	if (!Json->TryGetArrayField(TEXT("surfaces"), SurfacesArr) || SurfacesArr->Num() == 0)
	{
		OutError = TEXT("Acoustic profile missing or empty required field: surfaces");
		return false;
	}

	for (int32 i = 0; i < SurfacesArr->Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* SurfObjPtr;
		if (!(*SurfacesArr)[i]->TryGetObject(SurfObjPtr) || !SurfObjPtr || !(*SurfObjPtr).IsValid())
		{
			OutError = FString::Printf(TEXT("Surface %d is not a valid JSON object"), i);
			return false;
		}

		FString SurfName;
		if (!(*SurfObjPtr)->TryGetStringField(TEXT("surface_name"), SurfName))
		{
			OutError = FString::Printf(TEXT("Surface %d missing required field: surface_name"), i);
			return false;
		}

		double Absorption = 0.0;
		if (!(*SurfObjPtr)->TryGetNumberField(TEXT("absorption"), Absorption))
		{
			OutError = FString::Printf(TEXT("Surface '%s' missing required field: absorption"), *SurfName);
			return false;
		}
		if (Absorption < 0.0 || Absorption > 1.0)
		{
			OutError = FString::Printf(TEXT("Surface '%s' absorption must be 0-1, got %.3f"), *SurfName, Absorption);
			return false;
		}
	}

	return true;
}

bool FMonolithMeshPresetActions::ValidateTensionProfileJson(const TSharedPtr<FJsonObject>& Json, FString& OutError)
{
	FString Name;
	if (!Json->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		OutError = TEXT("Tension profile missing required field: name");
		return false;
	}

	const TSharedPtr<FJsonObject>* FactorsPtr;
	if (!Json->TryGetObjectField(TEXT("factors"), FactorsPtr) || !FactorsPtr || !(*FactorsPtr).IsValid())
	{
		OutError = TEXT("Tension profile missing required field: factors");
		return false;
	}

	// Validate known factor names
	static const TSet<FString> KnownFactors = {
		TEXT("sightline_length"), TEXT("ceiling_height"), TEXT("room_volume"), TEXT("exit_count"),
		TEXT("lighting_level"), TEXT("audio_reverb")
	};

	for (const auto& Pair : (*FactorsPtr)->Values)
	{
		const TSharedPtr<FJsonObject>* FactorObjPtr;
		if (!Pair.Value->TryGetObject(FactorObjPtr) || !FactorObjPtr || !(*FactorObjPtr).IsValid())
		{
			OutError = FString::Printf(TEXT("Factor '%s' must be a JSON object with 'weight' field"), *Pair.Key);
			return false;
		}

		double Weight = 0.0;
		if (!(*FactorObjPtr)->TryGetNumberField(TEXT("weight"), Weight))
		{
			OutError = FString::Printf(TEXT("Factor '%s' missing required field: weight"), *Pair.Key);
			return false;
		}

		if (Weight < 0.0 || Weight > 1.0)
		{
			OutError = FString::Printf(TEXT("Factor '%s' weight must be 0-1, got %.3f"), *Pair.Key, Weight);
			return false;
		}
	}

	// Validate thresholds if present
	const TSharedPtr<FJsonObject>* ThresholdsPtr;
	if (Json->TryGetObjectField(TEXT("thresholds"), ThresholdsPtr) && ThresholdsPtr && (*ThresholdsPtr).IsValid())
	{
		double Low = 0.0, Medium = 0.0, High = 0.0;
		(*ThresholdsPtr)->TryGetNumberField(TEXT("low"), Low);
		(*ThresholdsPtr)->TryGetNumberField(TEXT("medium"), Medium);
		(*ThresholdsPtr)->TryGetNumberField(TEXT("high"), High);

		if (Low >= Medium || Medium >= High)
		{
			OutError = FString::Printf(TEXT("Thresholds must be ascending: low(%.2f) < medium(%.2f) < high(%.2f)"), Low, Medium, High);
			return false;
		}
	}

	return true;
}

bool FMonolithMeshPresetActions::ValidateGenrePresetJson(const TSharedPtr<FJsonObject>& Json, FString& OutError)
{
	FString Name;
	if (!Json->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		OutError = TEXT("Genre preset missing required field: name");
		return false;
	}

	FString Version;
	if (!Json->TryGetStringField(TEXT("version"), Version))
	{
		OutError = TEXT("Genre preset missing required field: version");
		return false;
	}

	// At least one section must be present
	bool bHasContent = false;
	static const TArray<FString> Sections = {
		TEXT("patterns"), TEXT("acoustic_profiles"), TEXT("tension_profiles"),
		TEXT("templates"), TEXT("prop_kits")
	};

	for (const FString& Section : Sections)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr;
		if (Json->TryGetArrayField(Section, Arr) && Arr->Num() > 0)
		{
			bHasContent = true;
			break;
		}
	}

	if (!bHasContent)
	{
		OutError = TEXT("Genre preset must contain at least one non-empty section (patterns, acoustic_profiles, tension_profiles, templates, prop_kits)");
		return false;
	}

	return true;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshPresetActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. list_storytelling_patterns
	Registry.RegisterAction(TEXT("mesh"), TEXT("list_storytelling_patterns"),
		TEXT("List all available storytelling patterns: built-in horror defaults + user-created patterns from Saved/Monolith/Patterns/. Returns name, description, element count, and source (built-in vs user)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::ListStorytellingPatterns),
		FParamSchemaBuilder()
			.Optional(TEXT("source_filter"), TEXT("string"), TEXT("Filter by source: 'built-in', 'user', or omit for all"))
			.Build());

	// 2. create_storytelling_pattern
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_storytelling_pattern"),
		TEXT("Author a new storytelling pattern JSON. Defines element types (decal/prop), radial distribution, size ranges, spawn counts, rotation/scale variance. Saved to Saved/Monolith/Patterns/."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::CreateStorytellingPattern),
		FParamSchemaBuilder()
			.Required(TEXT("name"), TEXT("string"), TEXT("Pattern name (used as filename)"))
			.Required(TEXT("description"), TEXT("string"), TEXT("Human-readable description of the scene"))
			.Required(TEXT("elements"), TEXT("array"), TEXT("Array of element objects: {label, type:'decal'|'prop', relative_offset:[x,y,z], size:[x,y,z], radial:bool, radial_min:float, radial_max:float, count_min:int, count_max:int, rotation_variance:degrees, scale_variance:float, wall_element:bool}"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing pattern with same name"), TEXT("false"))
			.Build());

	// 3. list_acoustic_profiles
	Registry.RegisterAction(TEXT("mesh"), TEXT("list_acoustic_profiles"),
		TEXT("List all acoustic profiles: built-in horror defaults (12 surfaces from MonolithMeshAcoustics) + user-created profiles from Saved/Monolith/AcousticProfiles/. Returns profile name, genre, surface count, and source."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::ListAcousticProfiles),
		FParamSchemaBuilder()
			.Optional(TEXT("source_filter"), TEXT("string"), TEXT("Filter by source: 'built-in', 'user', or omit for all"))
			.Build());

	// 4. create_acoustic_profile
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_acoustic_profile"),
		TEXT("Author an acoustic property set for a genre. Each surface defines absorption (0-1), transmission_loss_db, and footstep_loudness. Saved to Saved/Monolith/AcousticProfiles/."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::CreateAcousticProfile),
		FParamSchemaBuilder()
			.Required(TEXT("name"), TEXT("string"), TEXT("Profile name (used as filename)"))
			.Required(TEXT("surfaces"), TEXT("array"), TEXT("Array of surface objects: {surface_name, absorption:0-1, transmission_loss_db:float, footstep_loudness:0-1}"))
			.Optional(TEXT("genre"), TEXT("string"), TEXT("Genre label (e.g. horror, fantasy, sci-fi)"), TEXT("custom"))
			.Optional(TEXT("description"), TEXT("string"), TEXT("Human-readable description"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing profile with same name"), TEXT("false"))
			.Build());

	// 5. create_tension_profile
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_tension_profile"),
		TEXT("Define tension scoring weights for a genre. Override how sightline_length, ceiling_height, room_volume, exit_count, lighting_level, and audio_reverb contribute to the tension score. Saved to Saved/Monolith/TensionProfiles/."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::CreateTensionProfile),
		FParamSchemaBuilder()
			.Required(TEXT("name"), TEXT("string"), TEXT("Profile name (used as filename)"))
			.Required(TEXT("factors"), TEXT("object"), TEXT("Factor weight map: {factor_name: {weight: 0-1, invert: bool}}. Factors: sightline_length, ceiling_height, room_volume, exit_count, lighting_level, audio_reverb"))
			.Optional(TEXT("genre"), TEXT("string"), TEXT("Genre label"), TEXT("custom"))
			.Optional(TEXT("description"), TEXT("string"), TEXT("Human-readable description"))
			.Optional(TEXT("thresholds"), TEXT("object"), TEXT("Custom tension level thresholds: {low: 0.3, medium: 0.5, high: 0.7}"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing profile"), TEXT("false"))
			.Build());

	// 6. list_genre_presets
	Registry.RegisterAction(TEXT("mesh"), TEXT("list_genre_presets"),
		TEXT("List all available genre preset packs from Saved/Monolith/Presets/. Shows name, genre, version, and content summary (pattern count, profile count, etc.)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::ListGenrePresets),
		FParamSchemaBuilder().Build());

	// 7. export_genre_preset
	Registry.RegisterAction(TEXT("mesh"), TEXT("export_genre_preset"),
		TEXT("Bundle all user-created templates + patterns + acoustic profiles + tension profiles + prop kits into a single JSON preset file. Optionally filter by name lists."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::ExportGenrePreset),
		FParamSchemaBuilder()
			.Required(TEXT("name"), TEXT("string"), TEXT("Preset pack name (used as filename)"))
			.Optional(TEXT("genre"), TEXT("string"), TEXT("Genre label for the preset"), TEXT("custom"))
			.Optional(TEXT("description"), TEXT("string"), TEXT("Human-readable description"))
			.Optional(TEXT("include_patterns"), TEXT("array"), TEXT("Pattern names to include (omit for all user patterns)"))
			.Optional(TEXT("include_acoustic_profiles"), TEXT("array"), TEXT("Acoustic profile names to include (omit for all)"))
			.Optional(TEXT("include_tension_profiles"), TEXT("array"), TEXT("Tension profile names to include (omit for all)"))
			.Optional(TEXT("include_templates"), TEXT("array"), TEXT("Room template names to include (omit for all)"))
			.Optional(TEXT("include_prop_kits"), TEXT("array"), TEXT("Prop kit names to include (omit for all)"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Overwrite existing preset"), TEXT("false"))
			.Build());

	// 8. import_genre_preset
	Registry.RegisterAction(TEXT("mesh"), TEXT("import_genre_preset"),
		TEXT("Load a genre preset pack JSON. Extracts all sub-presets (patterns, acoustic profiles, tension profiles, templates, prop kits) into their respective directories."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshPresetActions::ImportGenrePreset),
		FParamSchemaBuilder()
			.Required(TEXT("preset_name"), TEXT("string"), TEXT("Name of the preset pack to import (without .json)"))
			.Optional(TEXT("merge_mode"), TEXT("string"), TEXT("How to handle conflicts: 'overwrite', 'skip_existing', 'rename_conflicts'"), TEXT("skip_existing"))
			.Build());
}

// ============================================================================
// 1. list_storytelling_patterns
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::ListStorytellingPatterns(const TSharedPtr<FJsonObject>& Params)
{
	FString SourceFilter;
	Params->TryGetStringField(TEXT("source_filter"), SourceFilter);

	TArray<TSharedPtr<FJsonValue>> PatternsArr;

	// Built-in patterns from MonolithMeshStorytellingPatterns.h
	if (SourceFilter.IsEmpty() || SourceFilter.Equals(TEXT("built-in"), ESearchCase::IgnoreCase))
	{
		// Enumerate all known built-in patterns
		static const FString BuiltInNames[] = {
			TEXT("violence"), TEXT("abandoned_in_haste"), TEXT("dragged"),
			TEXT("medical_emergency"), TEXT("corruption")
		};

		for (const FString& Name : BuiltInNames)
		{
			const FStorytellingPattern* Pattern = StorytellingPatterns::GetPattern(Name);
			if (Pattern)
			{
				auto Entry = MakeShared<FJsonObject>();
				Entry->SetStringField(TEXT("name"), Pattern->Name);
				Entry->SetStringField(TEXT("description"), Pattern->Description);
				Entry->SetNumberField(TEXT("element_count"), Pattern->Elements.Num());
				Entry->SetStringField(TEXT("source"), TEXT("built-in"));
				PatternsArr.Add(MakeShared<FJsonValueObject>(Entry));
			}
		}
	}

	// User-created patterns from disk
	if (SourceFilter.IsEmpty() || SourceFilter.Equals(TEXT("user"), ESearchCase::IgnoreCase))
	{
		FString PatternsDir = GetPatternsDirectory();
		TArray<FString> Files = ListJsonFiles(PatternsDir);

		for (const FString& File : Files)
		{
			FString Error;
			TSharedPtr<FJsonObject> PatternJson = LoadJsonFile(PatternsDir / File, Error);
			if (!PatternJson.IsValid())
			{
				continue;
			}

			auto Entry = MakeShared<FJsonObject>();
			FString Name;
			PatternJson->TryGetStringField(TEXT("name"), Name);
			Entry->SetStringField(TEXT("name"), Name);

			FString Description;
			if (PatternJson->TryGetStringField(TEXT("description"), Description))
			{
				Entry->SetStringField(TEXT("description"), Description);
			}

			const TArray<TSharedPtr<FJsonValue>>* ElementsArr;
			if (PatternJson->TryGetArrayField(TEXT("elements"), ElementsArr))
			{
				Entry->SetNumberField(TEXT("element_count"), ElementsArr->Num());
			}

			Entry->SetStringField(TEXT("source"), TEXT("user"));
			Entry->SetStringField(TEXT("file"), File);
			PatternsArr.Add(MakeShared<FJsonValueObject>(Entry));
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("patterns"), PatternsArr);
	Result->SetNumberField(TEXT("total_count"), PatternsArr.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. create_storytelling_pattern
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::CreateStorytellingPattern(const TSharedPtr<FJsonObject>& Params)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: name"));
	}

	FString Description;
	if (!Params->TryGetStringField(TEXT("description"), Description))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: description"));
	}

	const TArray<TSharedPtr<FJsonValue>>* ElementsArr;
	if (!Params->TryGetArrayField(TEXT("elements"), ElementsArr) || ElementsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required param: elements"));
	}

	bool bOverwrite = false;
	Params->TryGetBoolField(TEXT("overwrite"), bOverwrite);

	// Check for name collision with built-in patterns
	const FStorytellingPattern* BuiltIn = StorytellingPatterns::GetPattern(Name);
	if (BuiltIn)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("'%s' is a built-in pattern name. Choose a different name."), *Name));
	}

	// Check for existing user pattern
	FString PatternsDir = GetPatternsDirectory();
	FString FilePath = PatternsDir / Name + TEXT(".json");
	if (!bOverwrite && IFileManager::Get().FileExists(*FilePath))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Pattern '%s' already exists. Use overwrite: true to replace."), *Name));
	}

	// Build and validate the pattern JSON
	auto PatternJson = MakeShared<FJsonObject>();
	PatternJson->SetStringField(TEXT("name"), Name);
	PatternJson->SetStringField(TEXT("description"), Description);
	PatternJson->SetStringField(TEXT("source"), TEXT("user"));

	// Validate and copy elements
	TArray<TSharedPtr<FJsonValue>> ValidatedElements;
	for (int32 i = 0; i < ElementsArr->Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* ElemObjPtr;
		if (!(*ElementsArr)[i]->TryGetObject(ElemObjPtr) || !ElemObjPtr || !(*ElemObjPtr).IsValid())
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Element %d is not a valid JSON object"), i));
		}
		const TSharedPtr<FJsonObject>& ElemObj = *ElemObjPtr;

		FString Label;
		if (!ElemObj->TryGetStringField(TEXT("label"), Label))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Element %d missing required field: label"), i));
		}

		FString Type;
		if (!ElemObj->TryGetStringField(TEXT("type"), Type))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Element %d missing required field: type"), i));
		}

		if (Type != TEXT("decal") && Type != TEXT("prop"))
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Element %d type must be 'decal' or 'prop', got '%s'"), i, *Type));
		}

		// Build validated element with defaults
		auto ValidElem = MakeShared<FJsonObject>();
		ValidElem->SetStringField(TEXT("label"), Label);
		ValidElem->SetStringField(TEXT("type"), Type);

		// Offset (default: [0,0,0])
		const TArray<TSharedPtr<FJsonValue>>* OffsetArr;
		if (ElemObj->TryGetArrayField(TEXT("relative_offset"), OffsetArr) && OffsetArr->Num() >= 3)
		{
			ValidElem->SetArrayField(TEXT("relative_offset"), *OffsetArr);
		}
		else
		{
			TArray<TSharedPtr<FJsonValue>> DefaultOffset;
			DefaultOffset.Add(MakeShared<FJsonValueNumber>(0.0));
			DefaultOffset.Add(MakeShared<FJsonValueNumber>(0.0));
			DefaultOffset.Add(MakeShared<FJsonValueNumber>(0.0));
			ValidElem->SetArrayField(TEXT("relative_offset"), DefaultOffset);
		}

		// Size (default: [10,50,50])
		const TArray<TSharedPtr<FJsonValue>>* SizeArr;
		if (ElemObj->TryGetArrayField(TEXT("size"), SizeArr) && SizeArr->Num() >= 3)
		{
			ValidElem->SetArrayField(TEXT("size"), *SizeArr);
		}
		else
		{
			TArray<TSharedPtr<FJsonValue>> DefaultSize;
			DefaultSize.Add(MakeShared<FJsonValueNumber>(10.0));
			DefaultSize.Add(MakeShared<FJsonValueNumber>(50.0));
			DefaultSize.Add(MakeShared<FJsonValueNumber>(50.0));
			ValidElem->SetArrayField(TEXT("size"), DefaultSize);
		}

		// Radial distribution
		bool bRadial = false;
		ElemObj->TryGetBoolField(TEXT("radial"), bRadial);
		ValidElem->SetBoolField(TEXT("radial"), bRadial);

		double RadialMin = 0.0, RadialMax = 100.0;
		ElemObj->TryGetNumberField(TEXT("radial_min"), RadialMin);
		ElemObj->TryGetNumberField(TEXT("radial_max"), RadialMax);
		ValidElem->SetNumberField(TEXT("radial_min"), RadialMin);
		ValidElem->SetNumberField(TEXT("radial_max"), RadialMax);

		// Count range
		double CountMin = 1.0, CountMax = 1.0;
		ElemObj->TryGetNumberField(TEXT("count_min"), CountMin);
		ElemObj->TryGetNumberField(TEXT("count_max"), CountMax);
		ValidElem->SetNumberField(TEXT("count_min"), FMath::Max(1.0, CountMin));
		ValidElem->SetNumberField(TEXT("count_max"), FMath::Max(CountMin, CountMax));

		// Rotation/scale variance
		double RotVar = 360.0, ScaleVar = 0.1;
		ElemObj->TryGetNumberField(TEXT("rotation_variance"), RotVar);
		ElemObj->TryGetNumberField(TEXT("scale_variance"), ScaleVar);
		ValidElem->SetNumberField(TEXT("rotation_variance"), RotVar);
		ValidElem->SetNumberField(TEXT("scale_variance"), FMath::Clamp(ScaleVar, 0.0, 1.0));

		// Wall element flag
		bool bWallElement = false;
		ElemObj->TryGetBoolField(TEXT("wall_element"), bWallElement);
		ValidElem->SetBoolField(TEXT("wall_element"), bWallElement);

		ValidatedElements.Add(MakeShared<FJsonValueObject>(ValidElem));
	}

	PatternJson->SetArrayField(TEXT("elements"), ValidatedElements);

	// Save to disk
	FString SaveError;
	if (!SaveJsonFile(FilePath, PatternJson, SaveError))
	{
		return FMonolithActionResult::Error(SaveError);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("name"), Name);
	Result->SetStringField(TEXT("file"), FilePath);
	Result->SetNumberField(TEXT("element_count"), ValidatedElements.Num());
	Result->SetStringField(TEXT("status"), bOverwrite ? TEXT("overwritten") : TEXT("created"));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. list_acoustic_profiles
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::ListAcousticProfiles(const TSharedPtr<FJsonObject>& Params)
{
	FString SourceFilter;
	Params->TryGetStringField(TEXT("source_filter"), SourceFilter);

	TArray<TSharedPtr<FJsonValue>> ProfilesArr;

	// Built-in: expose the hardcoded defaults as a single "horror_default" profile
	if (SourceFilter.IsEmpty() || SourceFilter.Equals(TEXT("built-in"), ESearchCase::IgnoreCase))
	{
		TMap<FString, MonolithMeshAcoustics::FAcousticProperties> Defaults = MonolithMeshAcoustics::GetHardcodedDefaults();

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("name"), TEXT("horror_default"));
		Entry->SetStringField(TEXT("genre"), TEXT("horror"));
		Entry->SetStringField(TEXT("description"), TEXT("Built-in horror surface acoustics (12 surfaces calibrated from Steam Audio reference data)"));
		Entry->SetNumberField(TEXT("surface_count"), Defaults.Num());
		Entry->SetStringField(TEXT("source"), TEXT("built-in"));

		// List surface names
		TArray<TSharedPtr<FJsonValue>> SurfaceNames;
		for (const auto& Pair : Defaults)
		{
			SurfaceNames.Add(MakeShared<FJsonValueString>(Pair.Key));
		}
		Entry->SetArrayField(TEXT("surface_names"), SurfaceNames);

		ProfilesArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	// User-created profiles from disk
	if (SourceFilter.IsEmpty() || SourceFilter.Equals(TEXT("user"), ESearchCase::IgnoreCase))
	{
		FString ProfilesDir = GetAcousticProfilesDirectory();
		TArray<FString> Files = ListJsonFiles(ProfilesDir);

		for (const FString& File : Files)
		{
			FString Error;
			TSharedPtr<FJsonObject> ProfileJson = LoadJsonFile(ProfilesDir / File, Error);
			if (!ProfileJson.IsValid())
			{
				continue;
			}

			auto Entry = MakeShared<FJsonObject>();
			FString Name;
			ProfileJson->TryGetStringField(TEXT("name"), Name);
			Entry->SetStringField(TEXT("name"), Name);

			FString Genre;
			if (ProfileJson->TryGetStringField(TEXT("genre"), Genre))
			{
				Entry->SetStringField(TEXT("genre"), Genre);
			}

			FString Description;
			if (ProfileJson->TryGetStringField(TEXT("description"), Description))
			{
				Entry->SetStringField(TEXT("description"), Description);
			}

			const TArray<TSharedPtr<FJsonValue>>* SurfacesArr;
			if (ProfileJson->TryGetArrayField(TEXT("surfaces"), SurfacesArr))
			{
				Entry->SetNumberField(TEXT("surface_count"), SurfacesArr->Num());
			}

			Entry->SetStringField(TEXT("source"), TEXT("user"));
			Entry->SetStringField(TEXT("file"), File);
			ProfilesArr.Add(MakeShared<FJsonValueObject>(Entry));
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("profiles"), ProfilesArr);
	Result->SetNumberField(TEXT("total_count"), ProfilesArr.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. create_acoustic_profile
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::CreateAcousticProfile(const TSharedPtr<FJsonObject>& Params)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: name"));
	}

	const TArray<TSharedPtr<FJsonValue>>* SurfacesArr;
	if (!Params->TryGetArrayField(TEXT("surfaces"), SurfacesArr) || SurfacesArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty required param: surfaces"));
	}

	bool bOverwrite = false;
	Params->TryGetBoolField(TEXT("overwrite"), bOverwrite);

	// Block built-in name collision
	if (Name.Equals(TEXT("horror_default"), ESearchCase::IgnoreCase))
	{
		return FMonolithActionResult::Error(TEXT("'horror_default' is a built-in profile name. Choose a different name."));
	}

	// Check for existing
	FString ProfilesDir = GetAcousticProfilesDirectory();
	FString FilePath = ProfilesDir / Name + TEXT(".json");
	if (!bOverwrite && IFileManager::Get().FileExists(*FilePath))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Acoustic profile '%s' already exists. Use overwrite: true to replace."), *Name));
	}

	FString Genre = TEXT("custom");
	Params->TryGetStringField(TEXT("genre"), Genre);

	FString Description;
	Params->TryGetStringField(TEXT("description"), Description);

	// Validate and build surfaces
	TArray<TSharedPtr<FJsonValue>> ValidatedSurfaces;
	for (int32 i = 0; i < SurfacesArr->Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* SurfObjPtr;
		if (!(*SurfacesArr)[i]->TryGetObject(SurfObjPtr) || !SurfObjPtr || !(*SurfObjPtr).IsValid())
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Surface %d is not a valid JSON object"), i));
		}
		const TSharedPtr<FJsonObject>& SurfObj = *SurfObjPtr;

		FString SurfName;
		if (!SurfObj->TryGetStringField(TEXT("surface_name"), SurfName))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Surface %d missing required field: surface_name"), i));
		}

		double Absorption = 0.02;
		if (!SurfObj->TryGetNumberField(TEXT("absorption"), Absorption))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Surface '%s' missing required field: absorption"), *SurfName));
		}
		if (Absorption < 0.0 || Absorption > 1.0)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Surface '%s' absorption must be 0-1, got %.3f"), *SurfName, Absorption));
		}

		double TransLoss = 40.0;
		SurfObj->TryGetNumberField(TEXT("transmission_loss_db"), TransLoss);

		double Loudness = 0.6;
		SurfObj->TryGetNumberField(TEXT("footstep_loudness"), Loudness);

		ValidatedSurfaces.Add(MakeShared<FJsonValueObject>(
			AcousticPropsToJson(SurfName, static_cast<float>(Absorption), static_cast<float>(TransLoss), static_cast<float>(Loudness))));
	}

	// Build profile JSON
	auto ProfileJson = MakeShared<FJsonObject>();
	ProfileJson->SetStringField(TEXT("name"), Name);
	ProfileJson->SetStringField(TEXT("genre"), Genre);
	ProfileJson->SetStringField(TEXT("source"), TEXT("user"));
	if (!Description.IsEmpty())
	{
		ProfileJson->SetStringField(TEXT("description"), Description);
	}
	ProfileJson->SetArrayField(TEXT("surfaces"), ValidatedSurfaces);

	// Save
	FString SaveError;
	if (!SaveJsonFile(FilePath, ProfileJson, SaveError))
	{
		return FMonolithActionResult::Error(SaveError);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("name"), Name);
	Result->SetStringField(TEXT("genre"), Genre);
	Result->SetStringField(TEXT("file"), FilePath);
	Result->SetNumberField(TEXT("surface_count"), ValidatedSurfaces.Num());
	Result->SetStringField(TEXT("status"), bOverwrite ? TEXT("overwritten") : TEXT("created"));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 5. create_tension_profile
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::CreateTensionProfile(const TSharedPtr<FJsonObject>& Params)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: name"));
	}

	const TSharedPtr<FJsonObject>* FactorsPtr;
	if (!Params->TryGetObjectField(TEXT("factors"), FactorsPtr) || !FactorsPtr || !(*FactorsPtr).IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: factors"));
	}

	if ((*FactorsPtr)->Values.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("factors must contain at least one factor weight"));
	}

	bool bOverwrite = false;
	Params->TryGetBoolField(TEXT("overwrite"), bOverwrite);

	// Check for existing
	FString ProfilesDir = GetTensionProfilesDirectory();
	FString FilePath = ProfilesDir / Name + TEXT(".json");
	if (!bOverwrite && IFileManager::Get().FileExists(*FilePath))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Tension profile '%s' already exists. Use overwrite: true to replace."), *Name));
	}

	FString Genre = TEXT("custom");
	Params->TryGetStringField(TEXT("genre"), Genre);

	FString Description;
	Params->TryGetStringField(TEXT("description"), Description);

	// Validate factor weights
	static const TSet<FString> KnownFactors = {
		TEXT("sightline_length"), TEXT("ceiling_height"), TEXT("room_volume"), TEXT("exit_count"),
		TEXT("lighting_level"), TEXT("audio_reverb")
	};

	TArray<FString> UnknownFactors;
	auto ValidatedFactors = MakeShared<FJsonObject>();
	float TotalWeight = 0.0f;

	for (const auto& Pair : (*FactorsPtr)->Values)
	{
		if (!KnownFactors.Contains(MonolithKeyToString(Pair.Key)))
		{
			UnknownFactors.Add(MonolithKeyToString(Pair.Key));
		}

		const TSharedPtr<FJsonObject>* FactorObjPtr;
		if (!Pair.Value->TryGetObject(FactorObjPtr) || !FactorObjPtr || !(*FactorObjPtr).IsValid())
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Factor '%s' must be a JSON object with at least a 'weight' field"), *MonolithKeyToString(Pair.Key)));
		}

		double Weight = 0.0;
		if (!(*FactorObjPtr)->TryGetNumberField(TEXT("weight"), Weight))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Factor '%s' missing required field: weight"), *Pair.Key));
		}
		if (Weight < 0.0 || Weight > 1.0)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Factor '%s' weight must be 0-1, got %.3f"), *Pair.Key, Weight));
		}

		TotalWeight += static_cast<float>(Weight);

		auto FactorObj = MakeShared<FJsonObject>();
		FactorObj->SetNumberField(TEXT("weight"), Weight);

		bool bInvert = false;
		(*FactorObjPtr)->TryGetBoolField(TEXT("invert"), bInvert);
		FactorObj->SetBoolField(TEXT("invert"), bInvert);

		ValidatedFactors->SetObjectField(Pair.Key, FactorObj);
	}

	// Build profile
	auto ProfileJson = MakeShared<FJsonObject>();
	ProfileJson->SetStringField(TEXT("name"), Name);
	ProfileJson->SetStringField(TEXT("genre"), Genre);
	ProfileJson->SetStringField(TEXT("source"), TEXT("user"));
	if (!Description.IsEmpty())
	{
		ProfileJson->SetStringField(TEXT("description"), Description);
	}
	ProfileJson->SetObjectField(TEXT("factors"), ValidatedFactors);

	// Thresholds (optional)
	const TSharedPtr<FJsonObject>* ThresholdsPtr;
	if (Params->TryGetObjectField(TEXT("thresholds"), ThresholdsPtr) && ThresholdsPtr && (*ThresholdsPtr).IsValid())
	{
		double Low = 0.3, Medium = 0.5, High = 0.7;
		(*ThresholdsPtr)->TryGetNumberField(TEXT("low"), Low);
		(*ThresholdsPtr)->TryGetNumberField(TEXT("medium"), Medium);
		(*ThresholdsPtr)->TryGetNumberField(TEXT("high"), High);

		if (Low >= Medium || Medium >= High)
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("Thresholds must be ascending: low(%.2f) < medium(%.2f) < high(%.2f)"), Low, Medium, High));
		}

		auto ThresholdsObj = MakeShared<FJsonObject>();
		ThresholdsObj->SetNumberField(TEXT("low"), Low);
		ThresholdsObj->SetNumberField(TEXT("medium"), Medium);
		ThresholdsObj->SetNumberField(TEXT("high"), High);
		ProfileJson->SetObjectField(TEXT("thresholds"), ThresholdsObj);
	}
	else
	{
		// Default thresholds matching current horror implementation (0-100 mapped to 0-1)
		auto ThresholdsObj = MakeShared<FJsonObject>();
		ThresholdsObj->SetNumberField(TEXT("low"), 0.2);
		ThresholdsObj->SetNumberField(TEXT("medium"), 0.4);
		ThresholdsObj->SetNumberField(TEXT("high"), 0.7);
		ProfileJson->SetObjectField(TEXT("thresholds"), ThresholdsObj);
	}

	// Save
	FString SaveError;
	if (!SaveJsonFile(FilePath, ProfileJson, SaveError))
	{
		return FMonolithActionResult::Error(SaveError);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("name"), Name);
	Result->SetStringField(TEXT("genre"), Genre);
	Result->SetStringField(TEXT("file"), FilePath);
	Result->SetNumberField(TEXT("factor_count"), ValidatedFactors->Values.Num());
	Result->SetNumberField(TEXT("total_weight"), TotalWeight);
	Result->SetStringField(TEXT("status"), bOverwrite ? TEXT("overwritten") : TEXT("created"));

	if (UnknownFactors.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> WarningsArr;
		for (const FString& UF : UnknownFactors)
		{
			WarningsArr.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("Unknown factor '%s' — accepted but not used by built-in tension scoring. Known: sightline_length, ceiling_height, room_volume, exit_count, lighting_level, audio_reverb"), *UF)));
		}
		Result->SetArrayField(TEXT("warnings"), WarningsArr);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 6. list_genre_presets
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::ListGenrePresets(const TSharedPtr<FJsonObject>& Params)
{
	FString PresetsDir = GetPresetsDirectory();
	TArray<FString> Files = ListJsonFiles(PresetsDir);

	TArray<TSharedPtr<FJsonValue>> PresetsArr;

	for (const FString& File : Files)
	{
		FString Error;
		TSharedPtr<FJsonObject> PresetJson = LoadJsonFile(PresetsDir / File, Error);
		if (!PresetJson.IsValid())
		{
			continue;
		}

		auto Entry = MakeShared<FJsonObject>();

		FString Name;
		PresetJson->TryGetStringField(TEXT("name"), Name);
		Entry->SetStringField(TEXT("name"), Name);

		FString Genre;
		if (PresetJson->TryGetStringField(TEXT("genre"), Genre))
		{
			Entry->SetStringField(TEXT("genre"), Genre);
		}

		FString Version;
		if (PresetJson->TryGetStringField(TEXT("version"), Version))
		{
			Entry->SetStringField(TEXT("version"), Version);
		}

		FString Description;
		if (PresetJson->TryGetStringField(TEXT("description"), Description))
		{
			Entry->SetStringField(TEXT("description"), Description);
		}

		// Content summary
		auto Summary = MakeShared<FJsonObject>();
		auto CountSection = [&](const FString& Section) -> int32
		{
			const TArray<TSharedPtr<FJsonValue>>* Arr;
			if (PresetJson->TryGetArrayField(Section, Arr))
			{
				return Arr->Num();
			}
			return 0;
		};

		Summary->SetNumberField(TEXT("patterns"), CountSection(TEXT("patterns")));
		Summary->SetNumberField(TEXT("acoustic_profiles"), CountSection(TEXT("acoustic_profiles")));
		Summary->SetNumberField(TEXT("tension_profiles"), CountSection(TEXT("tension_profiles")));
		Summary->SetNumberField(TEXT("templates"), CountSection(TEXT("templates")));
		Summary->SetNumberField(TEXT("prop_kits"), CountSection(TEXT("prop_kits")));
		Entry->SetObjectField(TEXT("content_summary"), Summary);

		Entry->SetStringField(TEXT("file"), File);
		PresetsArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("presets"), PresetsArr);
	Result->SetNumberField(TEXT("total_count"), PresetsArr.Num());
	Result->SetStringField(TEXT("directory"), PresetsDir);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 7. export_genre_preset
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::ExportGenrePreset(const TSharedPtr<FJsonObject>& Params)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name) || Name.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: name"));
	}

	bool bOverwrite = false;
	Params->TryGetBoolField(TEXT("overwrite"), bOverwrite);

	FString PresetsDir = GetPresetsDirectory();
	FString FilePath = PresetsDir / Name + TEXT(".json");
	if (!bOverwrite && IFileManager::Get().FileExists(*FilePath))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Preset '%s' already exists. Use overwrite: true to replace."), *Name));
	}

	FString Genre = TEXT("custom");
	Params->TryGetStringField(TEXT("genre"), Genre);

	FString Description;
	Params->TryGetStringField(TEXT("description"), Description);

	// Helper: get filter list or nullptr (= include all)
	auto GetFilterList = [&](const FString& ParamName) -> TSet<FString>
	{
		TSet<FString> Filter;
		const TArray<TSharedPtr<FJsonValue>>* Arr;
		if (Params->TryGetArrayField(ParamName, Arr))
		{
			for (const auto& Val : *Arr)
			{
				FString S;
				if (Val->TryGetString(S))
				{
					Filter.Add(S);
				}
			}
		}
		return Filter;
	};

	TSet<FString> PatternFilter = GetFilterList(TEXT("include_patterns"));
	TSet<FString> AcousticFilter = GetFilterList(TEXT("include_acoustic_profiles"));
	TSet<FString> TensionFilter = GetFilterList(TEXT("include_tension_profiles"));
	TSet<FString> TemplateFilter = GetFilterList(TEXT("include_templates"));
	TSet<FString> PropKitFilter = GetFilterList(TEXT("include_prop_kits"));

	// Helper: collect JSON files from a directory, optionally filtering by name
	auto CollectFiles = [&](const FString& Dir, const TSet<FString>& Filter) -> TArray<TSharedPtr<FJsonValue>>
	{
		TArray<TSharedPtr<FJsonValue>> Arr;
		TArray<FString> Files = ListJsonFiles(Dir);
		for (const FString& File : Files)
		{
			FString BaseName = FPaths::GetBaseFilename(File);
			if (Filter.Num() > 0 && !Filter.Contains(BaseName))
			{
				continue;
			}

			FString Error;
			TSharedPtr<FJsonObject> Json = LoadJsonFile(Dir / File, Error);
			if (Json.IsValid())
			{
				Arr.Add(MakeShared<FJsonValueObject>(Json));
			}
		}
		return Arr;
	};

	// Collect all sections
	TArray<TSharedPtr<FJsonValue>> Patterns = CollectFiles(GetPatternsDirectory(), PatternFilter);
	TArray<TSharedPtr<FJsonValue>> AcousticProfiles = CollectFiles(GetAcousticProfilesDirectory(), AcousticFilter);
	TArray<TSharedPtr<FJsonValue>> TensionProfiles = CollectFiles(GetTensionProfilesDirectory(), TensionFilter);
	TArray<TSharedPtr<FJsonValue>> Templates = CollectFiles(GetTemplatesDirectory(), TemplateFilter);
	TArray<TSharedPtr<FJsonValue>> PropKits = CollectFiles(GetPropKitsDirectory(), PropKitFilter);

	int32 TotalItems = Patterns.Num() + AcousticProfiles.Num() + TensionProfiles.Num() + Templates.Num() + PropKits.Num();

	// Warn about filtered names that weren't found (likely built-in items which can't be exported)
	TArray<FString> ExportWarnings;
	auto CheckMissing = [&](const TSet<FString>& Filter, const TArray<TSharedPtr<FJsonValue>>& Collected, const FString& Category)
	{
		if (Filter.Num() == 0) return;
		TSet<FString> Found;
		for (const auto& Item : Collected)
		{
			if (const TSharedPtr<FJsonObject>* Obj = nullptr; Item->TryGetObject(Obj) && Obj->IsValid())
			{
				FString ItemName;
				(*Obj)->TryGetStringField(TEXT("name"), ItemName);
				Found.Add(ItemName);
			}
		}
		for (const FString& Requested : Filter)
		{
			if (!Found.Contains(Requested))
			{
				ExportWarnings.Add(FString::Printf(
					TEXT("Requested %s '%s' not found in user files — built-in items cannot be exported (they ship with the plugin)."),
					*Category, *Requested));
			}
		}
	};
	CheckMissing(PatternFilter, Patterns, TEXT("pattern"));
	CheckMissing(AcousticFilter, AcousticProfiles, TEXT("acoustic profile"));
	CheckMissing(TensionFilter, TensionProfiles, TEXT("tension profile"));

	if (TotalItems == 0)
	{
		FString Msg = TEXT("No user-created items found to export.");
		if (ExportWarnings.Num() > 0)
		{
			Msg += TEXT(" ") + FString::Join(ExportWarnings, TEXT(" "));
		}
		return FMonolithActionResult::Error(Msg);
	}

	// Build the preset bundle
	auto PresetJson = MakeShared<FJsonObject>();
	PresetJson->SetStringField(TEXT("name"), Name);
	PresetJson->SetStringField(TEXT("genre"), Genre);
	PresetJson->SetStringField(TEXT("version"), TEXT("1.0"));
	if (!Description.IsEmpty())
	{
		PresetJson->SetStringField(TEXT("description"), Description);
	}
	PresetJson->SetStringField(TEXT("exported_at"), FDateTime::Now().ToString());
	PresetJson->SetArrayField(TEXT("patterns"), Patterns);
	PresetJson->SetArrayField(TEXT("acoustic_profiles"), AcousticProfiles);
	PresetJson->SetArrayField(TEXT("tension_profiles"), TensionProfiles);
	PresetJson->SetArrayField(TEXT("templates"), Templates);
	PresetJson->SetArrayField(TEXT("prop_kits"), PropKits);

	// Save
	FString SaveError;
	if (!SaveJsonFile(FilePath, PresetJson, SaveError))
	{
		return FMonolithActionResult::Error(SaveError);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("name"), Name);
	Result->SetStringField(TEXT("genre"), Genre);
	Result->SetStringField(TEXT("file"), FilePath);

	auto Summary = MakeShared<FJsonObject>();
	Summary->SetNumberField(TEXT("patterns"), Patterns.Num());
	Summary->SetNumberField(TEXT("acoustic_profiles"), AcousticProfiles.Num());
	Summary->SetNumberField(TEXT("tension_profiles"), TensionProfiles.Num());
	Summary->SetNumberField(TEXT("templates"), Templates.Num());
	Summary->SetNumberField(TEXT("prop_kits"), PropKits.Num());
	Summary->SetNumberField(TEXT("total_items"), TotalItems);
	Result->SetObjectField(TEXT("content_summary"), Summary);
	Result->SetStringField(TEXT("status"), bOverwrite ? TEXT("overwritten") : TEXT("created"));

	if (ExportWarnings.Num() > 0)
	{
		TArray<TSharedPtr<FJsonValue>> WarnArr;
		for (const FString& W : ExportWarnings)
		{
			WarnArr.Add(MakeShared<FJsonValueString>(W));
		}
		Result->SetArrayField(TEXT("warnings"), WarnArr);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 8. import_genre_preset
// ============================================================================

FMonolithActionResult FMonolithMeshPresetActions::ImportGenrePreset(const TSharedPtr<FJsonObject>& Params)
{
	FString PresetName;
	if (!Params->TryGetStringField(TEXT("preset_name"), PresetName) || PresetName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: preset_name"));
	}

	FString MergeMode = TEXT("skip_existing");
	Params->TryGetStringField(TEXT("merge_mode"), MergeMode);

	if (MergeMode != TEXT("overwrite") && MergeMode != TEXT("skip_existing") && MergeMode != TEXT("rename_conflicts"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid merge_mode '%s'. Must be: overwrite, skip_existing, rename_conflicts"), *MergeMode));
	}

	// Load the preset file
	FString PresetsDir = GetPresetsDirectory();
	FString FilePath = PresetsDir / PresetName + TEXT(".json");
	FString LoadError;
	TSharedPtr<FJsonObject> PresetJson = LoadJsonFile(FilePath, LoadError);
	if (!PresetJson.IsValid())
	{
		return FMonolithActionResult::Error(LoadError);
	}

	// Validate schema
	FString ValidateError;
	if (!ValidateGenrePresetJson(PresetJson, ValidateError))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid preset JSON: %s"), *ValidateError));
	}

	// Track import results
	int32 Imported = 0;
	int32 Skipped = 0;
	int32 Renamed = 0;
	int32 Overwritten = 0;
	TArray<TSharedPtr<FJsonValue>> Errors;

	// Helper: import a section of the preset into a target directory
	auto ImportSection = [&](const FString& SectionName, const FString& TargetDir)
	{
		const TArray<TSharedPtr<FJsonValue>>* SectionArr;
		if (!PresetJson->TryGetArrayField(SectionName, SectionArr))
		{
			return;
		}

		IFileManager::Get().MakeDirectory(*TargetDir, true);

		for (int32 i = 0; i < SectionArr->Num(); ++i)
		{
			const TSharedPtr<FJsonObject>* ItemObjPtr;
			if (!(*SectionArr)[i]->TryGetObject(ItemObjPtr) || !ItemObjPtr || !(*ItemObjPtr).IsValid())
			{
				Errors.Add(MakeShared<FJsonValueString>(FString::Printf(
					TEXT("%s[%d]: not a valid JSON object"), *SectionName, i)));
				continue;
			}

			FString ItemName;
			if (!(*ItemObjPtr)->TryGetStringField(TEXT("name"), ItemName) || ItemName.IsEmpty())
			{
				Errors.Add(MakeShared<FJsonValueString>(FString::Printf(
					TEXT("%s[%d]: missing 'name' field"), *SectionName, i)));
				continue;
			}

			FString TargetPath = TargetDir / ItemName + TEXT(".json");
			bool bExists = IFileManager::Get().FileExists(*TargetPath);

			if (bExists)
			{
				if (MergeMode == TEXT("skip_existing"))
				{
					Skipped++;
					continue;
				}
				else if (MergeMode == TEXT("rename_conflicts"))
				{
					// Find a unique name
					int32 Suffix = 1;
					FString NewName;
					FString NewPath;
					do
					{
						NewName = FString::Printf(TEXT("%s_%d"), *ItemName, Suffix);
						NewPath = TargetDir / NewName + TEXT(".json");
						Suffix++;
					} while (IFileManager::Get().FileExists(*NewPath) && Suffix < 100);

					if (Suffix >= 100)
					{
						Errors.Add(MakeShared<FJsonValueString>(FString::Printf(
							TEXT("%s '%s': too many conflicts (tried 99 suffixes)"), *SectionName, *ItemName)));
						continue;
					}

					// Update the name in the JSON
					auto ItemCopy = MakeShared<FJsonObject>();
					for (const auto& Pair : (*ItemObjPtr)->Values)
					{
						ItemCopy->SetField(Pair.Key, Pair.Value);
					}
					ItemCopy->SetStringField(TEXT("name"), NewName);

					FString SaveError;
					if (SaveJsonFile(NewPath, ItemCopy, SaveError))
					{
						Renamed++;
						Imported++;
					}
					else
					{
						Errors.Add(MakeShared<FJsonValueString>(FString::Printf(
							TEXT("%s '%s': %s"), *SectionName, *NewName, *SaveError)));
					}
					continue;
				}
				else // overwrite
				{
					Overwritten++;
				}
			}

			FString SaveError;
			if (SaveJsonFile(TargetPath, *ItemObjPtr, SaveError))
			{
				Imported++;
			}
			else
			{
				Errors.Add(MakeShared<FJsonValueString>(FString::Printf(
					TEXT("%s '%s': %s"), *SectionName, *ItemName, *SaveError)));
			}
		}
	};

	// Import all sections
	ImportSection(TEXT("patterns"), GetPatternsDirectory());
	ImportSection(TEXT("acoustic_profiles"), GetAcousticProfilesDirectory());
	ImportSection(TEXT("tension_profiles"), GetTensionProfilesDirectory());
	ImportSection(TEXT("templates"), GetTemplatesDirectory());
	ImportSection(TEXT("prop_kits"), GetPropKitsDirectory());

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("preset_name"), PresetName);
	Result->SetStringField(TEXT("merge_mode"), MergeMode);
	Result->SetNumberField(TEXT("imported"), Imported);
	Result->SetNumberField(TEXT("skipped"), Skipped);
	Result->SetNumberField(TEXT("renamed"), Renamed);
	Result->SetNumberField(TEXT("overwritten"), Overwritten);

	if (Errors.Num() > 0)
	{
		Result->SetArrayField(TEXT("errors"), Errors);
	}

	FString PresetGenre;
	if (PresetJson->TryGetStringField(TEXT("genre"), PresetGenre))
	{
		Result->SetStringField(TEXT("genre"), PresetGenre);
	}

	return FMonolithActionResult::Success(Result);
}
