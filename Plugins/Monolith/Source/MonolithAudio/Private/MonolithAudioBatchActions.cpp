#include "MonolithAudioBatchActions.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundConcurrency.h"
#include "Sound/SoundSubmix.h"

#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/UnrealType.h"

// LogMonolith declared in MonolithJsonUtils.h (MonolithCore)

// ============================================================================
// Shared helpers
// ============================================================================

namespace AudioBatchHelpers
{
	// Parse a JSON array field that may arrive as a string (Claude Code serialization quirk)
	static bool ParseJsonArrayField(const TSharedPtr<FJsonObject>& Params, const FString& FieldName,
		TArray<TSharedPtr<FJsonValue>>& OutArray, FString& OutError)
	{
		TSharedPtr<FJsonValue> Field = Params->TryGetField(FieldName);
		if (!Field.IsValid())
		{
			OutError = FString::Printf(TEXT("Missing required field '%s'"), *FieldName);
			return false;
		}

		if (Field->Type == EJson::Array)
		{
			OutArray = Field->AsArray();
			return true;
		}

		// Claude Code may serialize arrays as JSON strings
		if (Field->Type == EJson::String)
		{
			TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Field->AsString());
			TSharedPtr<FJsonValue> Parsed;
			if (FJsonSerializer::Deserialize(Reader, Parsed) && Parsed.IsValid() && Parsed->Type == EJson::Array)
			{
				OutArray = Parsed->AsArray();
				return true;
			}
		}

		OutError = FString::Printf(TEXT("'%s' must be a JSON array"), *FieldName);
		return false;
	}

	// Extract string array from parsed JSON values
	static TArray<FString> JsonArrayToStringArray(const TArray<TSharedPtr<FJsonValue>>& JsonArray)
	{
		TArray<FString> Result;
		Result.Reserve(JsonArray.Num());
		for (const TSharedPtr<FJsonValue>& Val : JsonArray)
		{
			if (Val.IsValid())
			{
				Result.Add(Val->AsString());
			}
		}
		return Result;
	}

	// Parse asset_paths from params — common to all batch actions
	static bool ParseAssetPaths(const TSharedPtr<FJsonObject>& Params, TArray<FString>& OutPaths, FString& OutError)
	{
		TArray<TSharedPtr<FJsonValue>> PathsJsonArray;
		if (!ParseJsonArrayField(Params, TEXT("asset_paths"), PathsJsonArray, OutError))
		{
			return false;
		}
		OutPaths = JsonArrayToStringArray(PathsJsonArray);
		if (OutPaths.Num() == 0)
		{
			OutError = TEXT("asset_paths array is empty");
			return false;
		}
		return true;
	}

	// Load a USoundBase (or subclass) by asset path
	template<typename T>
	static T* LoadAudioAsset(const FString& AssetPath)
	{
		// Registry-first per CLAUDE.md lessons
		IAssetRegistry& AssetRegistry = IAssetRegistry::GetChecked();
		FAssetData AssetData = AssetRegistry.GetAssetByObjectPath(FSoftObjectPath(AssetPath));
		if (AssetData.IsValid())
		{
			UObject* Loaded = AssetData.GetAsset();
			if (Loaded)
			{
				return Cast<T>(Loaded);
			}
		}
		// Fallback to StaticLoadObject
		return Cast<T>(StaticLoadObject(T::StaticClass(), nullptr, *AssetPath));
	}

	// Add a failure entry to the failed array
	static void AddFailure(TArray<TSharedPtr<FJsonValue>>& FailedArray, const FString& Path, const FString& Error)
	{
		auto FailObj = MakeShared<FJsonObject>();
		FailObj->SetStringField(TEXT("path"), Path);
		FailObj->SetStringField(TEXT("error"), Error);
		FailedArray.Add(MakeShared<FJsonValueObject>(FailObj));
	}

	// Build standard batch result: { "modified": N, "failed": [...] }
	static TSharedPtr<FJsonObject> MakeBatchResult(int32 Modified, const TArray<TSharedPtr<FJsonValue>>& Failed)
	{
		auto ResultJson = MakeShared<FJsonObject>();
		ResultJson->SetNumberField(TEXT("modified"), Modified);
		ResultJson->SetArrayField(TEXT("failed"), Failed);
		return ResultJson;
	}

	// Parse EVirtualizationMode from string
	static bool ParseVirtualizationMode(const FString& ModeStr, EVirtualizationMode& OutMode, FString& OutError)
	{
		if (ModeStr.Equals(TEXT("Restart"), ESearchCase::IgnoreCase))
		{
			OutMode = EVirtualizationMode::Restart;
			return true;
		}
		if (ModeStr.Equals(TEXT("PlayWhenSilent"), ESearchCase::IgnoreCase))
		{
			OutMode = EVirtualizationMode::PlayWhenSilent;
			return true;
		}
		if (ModeStr.Equals(TEXT("Disabled"), ESearchCase::IgnoreCase))
		{
			OutMode = EVirtualizationMode::Disabled;
			return true;
		}
		OutError = FString::Printf(TEXT("Invalid VirtualizationMode '%s'. Valid: Restart, PlayWhenSilent, Disabled"), *ModeStr);
		return false;
	}

	// Parse ESoundAssetCompressionType from string
	static bool ParseCompressionType(const FString& TypeStr, ESoundAssetCompressionType& OutType, FString& OutError)
	{
		static const TMap<FString, ESoundAssetCompressionType> Map = {
			{TEXT("BinkAudio"), ESoundAssetCompressionType::BinkAudio},
			{TEXT("ADPCM"), ESoundAssetCompressionType::ADPCM},
			{TEXT("PCM"), ESoundAssetCompressionType::PCM},
			{TEXT("Opus"), ESoundAssetCompressionType::Opus},
			{TEXT("RADAudio"), ESoundAssetCompressionType::RADAudio},
			{TEXT("PlatformSpecific"), ESoundAssetCompressionType::PlatformSpecific},
			{TEXT("ProjectDefined"), ESoundAssetCompressionType::ProjectDefined},
		};

		for (const auto& Pair : Map)
		{
			if (Pair.Key.Equals(TypeStr, ESearchCase::IgnoreCase))
			{
				OutType = Pair.Value;
				return true;
			}
		}
		OutError = FString::Printf(TEXT("Invalid ESoundAssetCompressionType '%s'. Valid: BinkAudio, ADPCM, PCM, Opus, RADAudio, PlatformSpecific, ProjectDefined"), *TypeStr);
		return false;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithAudioBatchActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("audio"), TEXT("batch_assign_sound_class"),
		TEXT("Assign a SoundClass to multiple USoundBase assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchAssignSoundClass),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase asset paths"))
			.Required(TEXT("sound_class"), TEXT("string"), TEXT("SoundClass asset path to assign"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_assign_attenuation"),
		TEXT("Assign an attenuation settings asset to multiple USoundBase assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchAssignAttenuation),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase asset paths"))
			.Required(TEXT("attenuation"), TEXT("string"), TEXT("SoundAttenuation asset path to assign"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_compression"),
		TEXT("Set compression quality and/or type on multiple USoundWave assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetCompression),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundWave asset paths"))
			.Optional(TEXT("quality"), TEXT("number"), TEXT("Compression quality 1-100"))
			.Optional(TEXT("type"), TEXT("string"), TEXT("ESoundAssetCompressionType: BinkAudio, ADPCM, PCM, Opus, RADAudio, PlatformSpecific, ProjectDefined"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_submix"),
		TEXT("Set SoundSubmixObject on multiple USoundBase assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetSubmix),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase asset paths"))
			.Required(TEXT("submix"), TEXT("string"), TEXT("SoundSubmix asset path to assign"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_concurrency"),
		TEXT("Add a SoundConcurrency to the ConcurrencySet on multiple USoundBase assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetConcurrency),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase asset paths"))
			.Required(TEXT("concurrency"), TEXT("string"), TEXT("SoundConcurrency asset path to add"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_looping"),
		TEXT("Set bLooping on multiple USoundWave assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetLooping),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundWave asset paths"))
			.Required(TEXT("looping"), TEXT("bool"), TEXT("Whether to loop"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_virtualization"),
		TEXT("Set VirtualizationMode on multiple USoundBase assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetVirtualization),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase asset paths"))
			.Required(TEXT("mode"), TEXT("string"), TEXT("EVirtualizationMode: Restart, PlayWhenSilent, Pause"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_rename_audio"),
		TEXT("Rename multiple audio assets with prefix/suffix/find-replace operations"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchRenameAudio),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of audio asset paths to rename"))
			.Optional(TEXT("prefix"), TEXT("string"), TEXT("Prefix to add to asset name"))
			.Optional(TEXT("suffix"), TEXT("string"), TEXT("Suffix to add to asset name"))
			.Optional(TEXT("find"), TEXT("string"), TEXT("Substring to find in asset name"))
			.Optional(TEXT("replace"), TEXT("string"), TEXT("Replacement string for find"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("batch_set_sound_wave_properties"),
		TEXT("Reflection-based multi-property set on multiple USoundWave assets"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::BatchSetSoundWaveProperties),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundWave asset paths"))
			.Required(TEXT("properties"), TEXT("object"), TEXT("Key-value pairs of UPROPERTY names and values to set"))
			.Build());

	Registry.RegisterAction(TEXT("audio"), TEXT("apply_audio_template"),
		TEXT("Apply a template config to multiple audio assets in one pass"),
		FMonolithActionHandler::CreateStatic(&FMonolithAudioBatchActions::ApplyAudioTemplate),
		FParamSchemaBuilder()
			.Required(TEXT("asset_paths"), TEXT("array"), TEXT("Array of USoundBase/USoundWave asset paths"))
			.Required(TEXT("template"), TEXT("object"), TEXT("Template with optional keys: sound_class, attenuation, compression, submix, concurrency, looping, virtualization"))
			.Build());
}

// ============================================================================
// Action: batch_assign_sound_class
// Set SoundClassObject on N USoundBase assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchAssignSoundClass(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString SoundClassPath = Params->GetStringField(TEXT("sound_class"));
	if (SoundClassPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'sound_class'"));
	}

	USoundClass* SoundClass = LoadAudioAsset<USoundClass>(SoundClassPath);
	if (!SoundClass)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundClass at '%s'"), *SoundClassPath));
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();
		Sound->SoundClassObject = SoundClass;
		Sound->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_assign_attenuation
// Set AttenuationSettings on N USoundBase assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchAssignAttenuation(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString AttenuationPath = Params->GetStringField(TEXT("attenuation"));
	if (AttenuationPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'attenuation'"));
	}

	USoundAttenuation* Attenuation = LoadAudioAsset<USoundAttenuation>(AttenuationPath);
	if (!Attenuation)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundAttenuation at '%s'"), *AttenuationPath));
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();
		Sound->AttenuationSettings = Attenuation;
		Sound->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_set_compression
// Set CompressionQuality and/or SoundAssetCompressionType on N USoundWave assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetCompression(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	bool bHasQuality = Params->HasField(TEXT("quality"));
	bool bHasType = Params->HasField(TEXT("type"));

	if (!bHasQuality && !bHasType)
	{
		return FMonolithActionResult::Error(TEXT("At least one of 'quality' or 'type' must be specified"));
	}

	int32 Quality = 0;
	if (bHasQuality)
	{
		Quality = FMath::Clamp(static_cast<int32>(Params->GetNumberField(TEXT("quality"))), 1, 100);
	}

	ESoundAssetCompressionType CompressionType = ESoundAssetCompressionType::BinkAudio;
	if (bHasType)
	{
		FString TypeStr = Params->GetStringField(TEXT("type"));
		FString TypeError;
		if (!ParseCompressionType(TypeStr, CompressionType, TypeError))
		{
			return FMonolithActionResult::Error(TypeError);
		}
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundWave* Wave = LoadAudioAsset<USoundWave>(Path);
		if (!Wave)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundWave"));
			continue;
		}

		Wave->Modify();
		if (bHasQuality)
		{
			FIntProperty* QualityProp = FindFProperty<FIntProperty>(USoundWave::StaticClass(), TEXT("CompressionQuality"));
			if (QualityProp) { QualityProp->SetPropertyValue_InContainer(Wave, Quality); }
		}
		if (bHasType)
		{
			FEnumProperty* TypeProp = FindFProperty<FEnumProperty>(USoundWave::StaticClass(), TEXT("SoundAssetCompressionType"));
			if (TypeProp)
			{
				FNumericProperty* UnderlyingProp = TypeProp->GetUnderlyingProperty();
				if (UnderlyingProp) { UnderlyingProp->SetIntPropertyValue(TypeProp->ContainerPtrToValuePtr<void>(Wave), (int64)CompressionType); }
			}
		}
		Wave->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_set_submix
// Set SoundSubmixObject on N USoundBase assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetSubmix(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString SubmixPath = Params->GetStringField(TEXT("submix"));
	if (SubmixPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'submix'"));
	}

	USoundSubmix* Submix = LoadAudioAsset<USoundSubmix>(SubmixPath);
	if (!Submix)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundSubmix at '%s'"), *SubmixPath));
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();
		Sound->SoundSubmixObject = Submix;
		Sound->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_set_concurrency
// Add to ConcurrencySet on N USoundBase assets (TSet::Add, not assignment)
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetConcurrency(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString ConcurrencyPath = Params->GetStringField(TEXT("concurrency"));
	if (ConcurrencyPath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'concurrency'"));
	}

	USoundConcurrency* Concurrency = LoadAudioAsset<USoundConcurrency>(ConcurrencyPath);
	if (!Concurrency)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundConcurrency at '%s'"), *ConcurrencyPath));
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();
		Sound->ConcurrencySet.Add(Concurrency);
		Sound->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_set_looping
// Set bLooping on N USoundWave assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetLooping(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	if (!Params->HasField(TEXT("looping")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'looping'"));
	}
	bool bLooping = Params->GetBoolField(TEXT("looping"));

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundWave* Wave = LoadAudioAsset<USoundWave>(Path);
		if (!Wave)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundWave"));
			continue;
		}

		Wave->Modify();
		Wave->bLooping = bLooping;
		Wave->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_set_virtualization
// Set VirtualizationMode on N USoundBase assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetVirtualization(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString ModeStr = Params->GetStringField(TEXT("mode"));
	if (ModeStr.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required field 'mode'"));
	}

	EVirtualizationMode VirtMode;
	FString ModeError;
	if (!ParseVirtualizationMode(ModeStr, VirtMode, ModeError))
	{
		return FMonolithActionResult::Error(ModeError);
	}

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();
		Sound->VirtualizationMode = VirtMode;
		Sound->MarkPackageDirty();
		Modified++;
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: batch_rename_audio
// Rename multiple audio assets using prefix/suffix/find-replace
// Uses IAssetTools::RenameAssets(TArray<FAssetRenameData>&)
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchRenameAudio(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	FString Prefix = Params->GetStringField(TEXT("prefix"));
	FString Suffix = Params->GetStringField(TEXT("suffix"));
	FString Find = Params->GetStringField(TEXT("find"));
	FString Replace = Params->GetStringField(TEXT("replace"));

	if (Prefix.IsEmpty() && Suffix.IsEmpty() && Find.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("At least one of 'prefix', 'suffix', or 'find' must be specified"));
	}

	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
	IAssetTools& AssetTools = AssetToolsModule.Get();

	TArray<FAssetRenameData> RenameList;
	TArray<TSharedPtr<FJsonValue>> Failed;
	// Track new paths for the result
	TArray<TSharedPtr<FJsonValue>> NewPathsArray;

	for (const FString& Path : AssetPaths)
	{
		UObject* Asset = LoadAudioAsset<UObject>(Path);
		if (!Asset)
		{
			AddFailure(Failed, Path, TEXT("Failed to load asset"));
			continue;
		}

		FString OldName = Asset->GetName();
		FString NewName = OldName;

		// Apply find-replace first
		if (!Find.IsEmpty())
		{
			NewName = NewName.Replace(*Find, *Replace);
		}

		// Apply prefix/suffix
		if (!Prefix.IsEmpty())
		{
			NewName = Prefix + NewName;
		}
		if (!Suffix.IsEmpty())
		{
			NewName = NewName + Suffix;
		}

		if (NewName == OldName)
		{
			AddFailure(Failed, Path, TEXT("Rename would produce identical name"));
			continue;
		}

		FString PackagePath = FPackageName::GetLongPackagePath(Asset->GetOutermost()->GetName());
		RenameList.Add(FAssetRenameData(Asset, PackagePath, NewName));
		NewPathsArray.Add(MakeShared<FJsonValueString>(PackagePath / NewName));
	}

	int32 Renamed = 0;
	if (RenameList.Num() > 0)
	{
		bool bSuccess = AssetTools.RenameAssets(RenameList);
		if (bSuccess)
		{
			Renamed = RenameList.Num();
		}
		else
		{
			// RenameAssets is all-or-nothing — if it fails, report all as failed
			for (const FAssetRenameData& Data : RenameList)
			{
				AddFailure(Failed, Data.Asset->GetPathName(), TEXT("RenameAssets returned false"));
			}
			NewPathsArray.Empty();
		}
	}

	auto ResultJson = MakeShared<FJsonObject>();
	ResultJson->SetNumberField(TEXT("renamed"), Renamed);
	ResultJson->SetArrayField(TEXT("new_paths"), NewPathsArray);
	ResultJson->SetArrayField(TEXT("failed"), Failed);
	return FMonolithActionResult::Success(ResultJson);
}

// ============================================================================
// Action: batch_set_sound_wave_properties
// Reflection-based multi-property set on N USoundWave assets
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::BatchSetSoundWaveProperties(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	const TSharedPtr<FJsonObject>* PropertiesPtr = nullptr;
	if (!Params->TryGetObjectField(TEXT("properties"), PropertiesPtr) || !PropertiesPtr || !(*PropertiesPtr).IsValid())
	{
		// Claude Code may serialize the object as a string
		FString PropsStr = Params->GetStringField(TEXT("properties"));
		if (!PropsStr.IsEmpty())
		{
			TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(PropsStr);
			TSharedPtr<FJsonObject> ParsedObj;
			if (FJsonSerializer::Deserialize(Reader, ParsedObj) && ParsedObj.IsValid() && ParsedObj->Values.Num() > 0)
			{
				// Store as a local that survives the loop
				Params->SetObjectField(TEXT("_parsed_properties"), ParsedObj);
				PropertiesPtr = Params->Values.Find(TEXT("_parsed_properties")) ?
					&(*Params->Values.Find(TEXT("_parsed_properties")))->AsObject() : nullptr;
			}
		}
		if (!PropertiesPtr || !(*PropertiesPtr).IsValid())
		{
			return FMonolithActionResult::Error(TEXT("Missing or invalid 'properties' object"));
		}
	}

	const TSharedPtr<FJsonObject>& Properties = *PropertiesPtr;

	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundWave* Wave = LoadAudioAsset<USoundWave>(Path);
		if (!Wave)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundWave"));
			continue;
		}

		Wave->Modify();
		bool bAnySet = false;
		TArray<FString> PropertyErrors;

		for (const auto& PropPair : Properties->Values)
		{
			const FString PropName = MonolithKeyToString(PropPair.Key);
			const TSharedPtr<FJsonValue>& PropValue = PropPair.Value;

			// Find the UPROPERTY via reflection — check USoundWave and parent classes
			FProperty* Prop = Wave->GetClass()->FindPropertyByName(FName(*PropName));
			if (!Prop)
			{
				PropertyErrors.Add(FString::Printf(TEXT("Property '%s' not found on USoundWave"), *PropName));
				continue;
			}

			void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Wave);

			// Handle common property types
			if (FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
			{
				BoolProp->SetPropertyValue(ValuePtr, PropValue->AsBool());
				bAnySet = true;
			}
			else if (FIntProperty* IntProp = CastField<FIntProperty>(Prop))
			{
				IntProp->SetPropertyValue(ValuePtr, static_cast<int32>(PropValue->AsNumber()));
				bAnySet = true;
			}
			else if (FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
			{
				FloatProp->SetPropertyValue(ValuePtr, static_cast<float>(PropValue->AsNumber()));
				bAnySet = true;
			}
			else if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Prop))
			{
				DoubleProp->SetPropertyValue(ValuePtr, PropValue->AsNumber());
				bAnySet = true;
			}
			else if (FStrProperty* StrProp = CastField<FStrProperty>(Prop))
			{
				StrProp->SetPropertyValue(ValuePtr, PropValue->AsString());
				bAnySet = true;
			}
			else if (FNameProperty* NameProp = CastField<FNameProperty>(Prop))
			{
				NameProp->SetPropertyValue(ValuePtr, FName(*PropValue->AsString()));
				bAnySet = true;
			}
			else if (FEnumProperty* EnumProp = CastField<FEnumProperty>(Prop))
			{
				// Try to set enum by name string
				UEnum* Enum = EnumProp->GetEnum();
				int64 EnumValue = Enum->GetValueByNameString(PropValue->AsString());
				if (EnumValue != INDEX_NONE)
				{
					EnumProp->GetUnderlyingProperty()->SetIntPropertyValue(ValuePtr, EnumValue);
					bAnySet = true;
				}
				else
				{
					PropertyErrors.Add(FString::Printf(TEXT("Invalid enum value '%s' for '%s'"), *PropValue->AsString(), *PropName));
				}
			}
			else if (FByteProperty* ByteProp = CastField<FByteProperty>(Prop))
			{
				if (ByteProp->Enum)
				{
					int64 EnumValue = ByteProp->Enum->GetValueByNameString(PropValue->AsString());
					if (EnumValue != INDEX_NONE)
					{
						ByteProp->SetPropertyValue(ValuePtr, static_cast<uint8>(EnumValue));
						bAnySet = true;
					}
					else
					{
						PropertyErrors.Add(FString::Printf(TEXT("Invalid enum value '%s' for '%s'"), *PropValue->AsString(), *PropName));
					}
				}
				else
				{
					ByteProp->SetPropertyValue(ValuePtr, static_cast<uint8>(PropValue->AsNumber()));
					bAnySet = true;
				}
			}
			else if (FObjectPropertyBase* ObjProp = CastField<FObjectPropertyBase>(Prop))
			{
				// Load object by path
				FString ObjPath = PropValue->AsString();
				UObject* LoadedObj = StaticLoadObject(ObjProp->PropertyClass, nullptr, *ObjPath);
				if (LoadedObj)
				{
					ObjProp->SetObjectPropertyValue(ValuePtr, LoadedObj);
					bAnySet = true;
				}
				else
				{
					PropertyErrors.Add(FString::Printf(TEXT("Failed to load object '%s' for '%s'"), *ObjPath, *PropName));
				}
			}
			else
			{
				// Attempt ImportText as last resort
				FString TextValue = PropValue->AsString();
				if (Prop->ImportText_Direct(*TextValue, ValuePtr, Wave, PPF_None))
				{
					bAnySet = true;
				}
				else
				{
					PropertyErrors.Add(FString::Printf(TEXT("Unsupported property type for '%s'"), *PropName));
				}
			}
		}

		if (bAnySet)
		{
			Wave->MarkPackageDirty();
			Modified++;
		}

		if (PropertyErrors.Num() > 0)
		{
			AddFailure(Failed, Path, FString::Join(PropertyErrors, TEXT("; ")));
		}
	}

	return FMonolithActionResult::Success(MakeBatchResult(Modified, Failed));
}

// ============================================================================
// Action: apply_audio_template
// Apply a template config to N assets in one pass
// Template: { sound_class?, attenuation?, compression?, submix?, concurrency?,
//             looping?, virtualization? }
// ============================================================================

FMonolithActionResult FMonolithAudioBatchActions::ApplyAudioTemplate(const TSharedPtr<FJsonObject>& Params)
{
	using namespace AudioBatchHelpers;

	TArray<FString> AssetPaths;
	FString ParseError;
	if (!ParseAssetPaths(Params, AssetPaths, ParseError))
	{
		return FMonolithActionResult::Error(ParseError);
	}

	// Parse template — may arrive as object or string
	TSharedPtr<FJsonObject> Template;
	{
		const TSharedPtr<FJsonObject>* TemplatePtr = nullptr;
		if (Params->TryGetObjectField(TEXT("template"), TemplatePtr) && TemplatePtr && (*TemplatePtr).IsValid())
		{
			Template = *TemplatePtr;
		}
		else
		{
			FString TemplateStr = Params->GetStringField(TEXT("template"));
			if (!TemplateStr.IsEmpty())
			{
				TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(TemplateStr);
				FJsonSerializer::Deserialize(Reader, Template);
			}
		}
	}

	if (!Template.IsValid() || Template->Values.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty 'template' object"));
	}

	// Pre-resolve template assets so we fail fast before iterating
	TArray<FString> AppliedFields;

	USoundClass* SoundClass = nullptr;
	if (Template->HasField(TEXT("sound_class")))
	{
		FString ClassPath = Template->GetStringField(TEXT("sound_class"));
		SoundClass = LoadAudioAsset<USoundClass>(ClassPath);
		if (!SoundClass)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundClass '%s'"), *ClassPath));
		}
		AppliedFields.Add(TEXT("sound_class"));
	}

	USoundAttenuation* Attenuation = nullptr;
	if (Template->HasField(TEXT("attenuation")))
	{
		FString AttenPath = Template->GetStringField(TEXT("attenuation"));
		Attenuation = LoadAudioAsset<USoundAttenuation>(AttenPath);
		if (!Attenuation)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundAttenuation '%s'"), *AttenPath));
		}
		AppliedFields.Add(TEXT("attenuation"));
	}

	bool bHasCompression = false;
	int32 CompressionQuality = 0;
	bool bHasCompressionQuality = false;
	ESoundAssetCompressionType CompressionType = ESoundAssetCompressionType::BinkAudio;
	bool bHasCompressionType = false;
	if (Template->HasField(TEXT("compression")))
	{
		bHasCompression = true;
		const TSharedPtr<FJsonObject>* CompPtr = nullptr;
		TSharedPtr<FJsonObject> CompObj;
		if (Template->TryGetObjectField(TEXT("compression"), CompPtr) && CompPtr)
		{
			CompObj = *CompPtr;
		}
		else
		{
			// Might be a string-encoded object
			FString CompStr = Template->GetStringField(TEXT("compression"));
			TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(CompStr);
			FJsonSerializer::Deserialize(Reader, CompObj);
		}

		if (CompObj.IsValid())
		{
			if (CompObj->HasField(TEXT("quality")))
			{
				CompressionQuality = FMath::Clamp(static_cast<int32>(CompObj->GetNumberField(TEXT("quality"))), 1, 100);
				bHasCompressionQuality = true;
			}
			if (CompObj->HasField(TEXT("type")))
			{
				FString TypeStr = CompObj->GetStringField(TEXT("type"));
				FString TypeError;
				if (!ParseCompressionType(TypeStr, CompressionType, TypeError))
				{
					return FMonolithActionResult::Error(TypeError);
				}
				bHasCompressionType = true;
			}
		}
		else
		{
			// compression might be a plain number (quality only)
			TSharedPtr<FJsonValue> CompVal = Template->TryGetField(TEXT("compression"));
			if (CompVal.IsValid() && CompVal->Type == EJson::Number)
			{
				CompressionQuality = FMath::Clamp(static_cast<int32>(CompVal->AsNumber()), 1, 100);
				bHasCompressionQuality = true;
			}
		}

		if (bHasCompressionQuality || bHasCompressionType)
		{
			AppliedFields.Add(TEXT("compression"));
		}
		else
		{
			bHasCompression = false;
		}
	}

	USoundSubmix* Submix = nullptr;
	if (Template->HasField(TEXT("submix")))
	{
		FString SubmixPath = Template->GetStringField(TEXT("submix"));
		Submix = LoadAudioAsset<USoundSubmix>(SubmixPath);
		if (!Submix)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundSubmix '%s'"), *SubmixPath));
		}
		AppliedFields.Add(TEXT("submix"));
	}

	USoundConcurrency* Concurrency = nullptr;
	if (Template->HasField(TEXT("concurrency")))
	{
		FString ConcPath = Template->GetStringField(TEXT("concurrency"));
		Concurrency = LoadAudioAsset<USoundConcurrency>(ConcPath);
		if (!Concurrency)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load SoundConcurrency '%s'"), *ConcPath));
		}
		AppliedFields.Add(TEXT("concurrency"));
	}

	bool bHasLooping = Template->HasField(TEXT("looping"));
	bool bLooping = bHasLooping ? Template->GetBoolField(TEXT("looping")) : false;
	if (bHasLooping)
	{
		AppliedFields.Add(TEXT("looping"));
	}

	bool bHasVirtualization = Template->HasField(TEXT("virtualization"));
	EVirtualizationMode VirtMode = EVirtualizationMode::Restart;
	if (bHasVirtualization)
	{
		FString ModeStr = Template->GetStringField(TEXT("virtualization"));
		FString ModeError;
		if (!ParseVirtualizationMode(ModeStr, VirtMode, ModeError))
		{
			return FMonolithActionResult::Error(ModeError);
		}
		AppliedFields.Add(TEXT("virtualization"));
	}

	if (AppliedFields.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Template has no recognized fields"));
	}

	// Apply to all assets
	int32 Modified = 0;
	TArray<TSharedPtr<FJsonValue>> Failed;

	for (const FString& Path : AssetPaths)
	{
		USoundBase* Sound = LoadAudioAsset<USoundBase>(Path);
		if (!Sound)
		{
			AddFailure(Failed, Path, TEXT("Failed to load as USoundBase"));
			continue;
		}

		Sound->Modify();

		if (SoundClass)
		{
			Sound->SoundClassObject = SoundClass;
		}
		if (Attenuation)
		{
			Sound->AttenuationSettings = Attenuation;
		}
		if (Submix)
		{
			Sound->SoundSubmixObject = Submix;
		}
		if (Concurrency)
		{
			Sound->ConcurrencySet.Add(Concurrency);
		}
		if (bHasVirtualization)
		{
			Sound->VirtualizationMode = VirtMode;
		}

		// SoundWave-specific properties (looping, compression) — only apply if asset is a SoundWave
		USoundWave* Wave = Cast<USoundWave>(Sound);
		if (Wave)
		{
			if (bHasLooping)
			{
				Wave->bLooping = bLooping;
			}
			if (bHasCompression)
			{
				if (bHasCompressionQuality)
				{
					FIntProperty* QualityProp = FindFProperty<FIntProperty>(USoundWave::StaticClass(), TEXT("CompressionQuality"));
					if (QualityProp) { QualityProp->SetPropertyValue_InContainer(Wave, CompressionQuality); }
				}
				if (bHasCompressionType)
				{
					FEnumProperty* TypeProp = FindFProperty<FEnumProperty>(USoundWave::StaticClass(), TEXT("SoundAssetCompressionType"));
					if (TypeProp)
					{
						FNumericProperty* UnderlyingProp = TypeProp->GetUnderlyingProperty();
						if (UnderlyingProp) { UnderlyingProp->SetIntPropertyValue(TypeProp->ContainerPtrToValuePtr<void>(Wave), (int64)CompressionType); }
					}
				}
			}
		}
		else if (bHasLooping || bHasCompression)
		{
			// Not a SoundWave but template has wave-only fields — warn but still apply other fields
			FString Warning = TEXT("Not a USoundWave — skipped looping/compression fields");
			// Only add to failed if ONLY wave-specific fields were requested
			if (!SoundClass && !Attenuation && !Submix && !Concurrency && !bHasVirtualization)
			{
				AddFailure(Failed, Path, Warning);
				continue;
			}
			// Otherwise partial success — log but don't add to failed
			UE_LOG(LogMonolith, Warning, TEXT("[apply_audio_template] %s: %s"), *Path, *Warning);
		}

		Sound->MarkPackageDirty();
		Modified++;
	}

	auto ResultJson = MakeShared<FJsonObject>();
	ResultJson->SetNumberField(TEXT("modified"), Modified);
	TArray<TSharedPtr<FJsonValue>> AppliedFieldsJson;
	for (const FString& Field : AppliedFields)
	{
		AppliedFieldsJson.Add(MakeShared<FJsonValueString>(Field));
	}
	ResultJson->SetArrayField(TEXT("applied_fields"), AppliedFieldsJson);
	ResultJson->SetArrayField(TEXT("failed"), Failed);
	return FMonolithActionResult::Success(ResultJson);
}
