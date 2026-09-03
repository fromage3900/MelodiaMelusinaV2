// MonolithUISettingsActions.cpp
#include "MonolithUISettingsActions.h"
#include "MonolithParamSchema.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFileManager.h"

// ============================================================================
// Helpers
// ============================================================================

FString FMonolithUISettingsActions::ResolveSourceDir(const FString& ModuleName, FMonolithActionResult& OutError)
{
    FString ProjectDir = FPaths::ProjectDir();
    FString SourceDir = FPaths::Combine(ProjectDir, TEXT("Source"), ModuleName);

    // Verify the module directory exists
    if (!FPaths::DirectoryExists(SourceDir))
    {
        OutError = FMonolithActionResult::Error(
            FString::Printf(TEXT("Source directory not found: %s — module '%s' must already exist"), *SourceDir, *ModuleName));
        return FString();
    }

    return SourceDir;
}

bool FMonolithUISettingsActions::WriteSourceFiles(const FString& Dir, const FString& ClassName,
    const FString& HeaderContent, const FString& CppContent,
    TSharedPtr<FJsonObject>& OutResult, FMonolithActionResult& OutError)
{
    FString HeaderPath = FPaths::Combine(Dir, ClassName + TEXT(".h"));
    FString CppPath = FPaths::Combine(Dir, ClassName + TEXT(".cpp"));

    // Check for existing files
    if (FPaths::FileExists(HeaderPath))
    {
        OutError = FMonolithActionResult::Error(
            FString::Printf(TEXT("File already exists: %s — delete or rename before scaffolding"), *HeaderPath));
        return false;
    }

    if (!FFileHelper::SaveStringToFile(HeaderContent, *HeaderPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        OutError = FMonolithActionResult::Error(
            FString::Printf(TEXT("Failed to write header: %s"), *HeaderPath));
        return false;
    }

    if (!FFileHelper::SaveStringToFile(CppContent, *CppPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        OutError = FMonolithActionResult::Error(
            FString::Printf(TEXT("Failed to write cpp: %s"), *CppPath));
        return false;
    }

    OutResult = MakeShared<FJsonObject>();
    OutResult->SetStringField(TEXT("header_path"), HeaderPath);
    OutResult->SetStringField(TEXT("cpp_path"), CppPath);
    OutResult->SetStringField(TEXT("class_name"), ClassName);
    return true;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithUISettingsActions::RegisterActions(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"), TEXT("scaffold_game_user_settings"),
        TEXT("Generate a UGameUserSettings subclass .h/.cpp with audio, sensitivity, and accessibility config"),
        FMonolithActionHandler::CreateStatic(&HandleScaffoldGameUserSettings),
        FParamSchemaBuilder()
            .Required(TEXT("class_name"), TEXT("string"), TEXT("Class name, e.g. ULeviathanGameUserSettings"))
            .Required(TEXT("module_name"), TEXT("string"), TEXT("Target module name, e.g. Leviathan"))
            .Optional(TEXT("features"), TEXT("array"), TEXT("Feature flags: audio_volumes, mouse_sensitivity, accessibility_flags, keybinding_support"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("scaffold_save_game"),
        TEXT("Generate a ULocalPlayerSaveGame subclass .h/.cpp with versioned save properties"),
        FMonolithActionHandler::CreateStatic(&HandleScaffoldSaveGame),
        FParamSchemaBuilder()
            .Required(TEXT("class_name"), TEXT("string"), TEXT("Class name, e.g. ULeviathanSaveGame"))
            .Required(TEXT("module_name"), TEXT("string"), TEXT("Target module name"))
            .Optional(TEXT("properties"), TEXT("array"), TEXT("Array of {name, type, default_value} for UPROPERTY(SaveGame) fields"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("scaffold_save_subsystem"),
        TEXT("Generate a UGameInstanceSubsystem for async save/load management"),
        FMonolithActionHandler::CreateStatic(&HandleScaffoldSaveSubsystem),
        FParamSchemaBuilder()
            .Required(TEXT("class_name"), TEXT("string"), TEXT("Subsystem class name, e.g. ULeviathanSaveSubsystem"))
            .Required(TEXT("module_name"), TEXT("string"), TEXT("Target module name"))
            .Required(TEXT("save_game_class"), TEXT("string"), TEXT("Save game class to manage, e.g. ULeviathanSaveGame"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("scaffold_audio_settings"),
        TEXT("Return JSON describing the USoundMix/USoundClass asset hierarchy and wiring code needed for audio settings"),
        FMonolithActionHandler::CreateStatic(&HandleScaffoldAudioSettings),
        FParamSchemaBuilder()
            .Optional(TEXT("categories"), TEXT("array"), TEXT("Audio categories (default: Master, Music, SFX, Voice, Ambient)"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("scaffold_input_remapping"),
        TEXT("Return JSON describing UEnhancedInputUserSettings setup and UInputKeySelector widget wiring for keybinding UI"),
        FMonolithActionHandler::CreateStatic(&HandleScaffoldInputRemapping),
        FParamSchemaBuilder()
            .Optional(TEXT("actions"), TEXT("array"), TEXT("Input action names to expose for remapping"))
            .Build()
    );
}

// ============================================================================
// scaffold_game_user_settings
// ============================================================================

FMonolithActionResult FMonolithUISettingsActions::HandleScaffoldGameUserSettings(const TSharedPtr<FJsonObject>& Params)
{
    FString ClassName = Params->GetStringField(TEXT("class_name"));
    FString ModuleName = Params->GetStringField(TEXT("module_name"));
    if (ClassName.IsEmpty() || ModuleName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required params: class_name, module_name"));
    }

    // Strip leading U if present for file naming
    FString CleanName = ClassName;
    if (CleanName.StartsWith(TEXT("U"))) CleanName = CleanName.RightChop(1);

    // Parse features
    TSet<FString> Features;
    const TArray<TSharedPtr<FJsonValue>>* FeaturesArray = nullptr;
    if (Params->TryGetArrayField(TEXT("features"), FeaturesArray))
    {
        for (const auto& Val : *FeaturesArray)
        {
            Features.Add(Val->AsString());
        }
    }
    else
    {
        // Default: all features
        Features.Add(TEXT("audio_volumes"));
        Features.Add(TEXT("mouse_sensitivity"));
        Features.Add(TEXT("accessibility_flags"));
        Features.Add(TEXT("keybinding_support"));
    }

    FMonolithActionResult Err;
    FString SourceDir = ResolveSourceDir(ModuleName, Err);
    if (SourceDir.IsEmpty()) return Err;

    // Build API macro from module name (uppercase)
    FString ApiMacro = ModuleName.ToUpper() + TEXT("_API");

    // ---- Header ----
    FString Header;
    Header += TEXT("// Auto-generated by Monolith scaffold_game_user_settings\n");
    Header += TEXT("#pragma once\n\n");
    Header += TEXT("#include \"CoreMinimal.h\"\n");
    Header += TEXT("#include \"GameFramework/GameUserSettings.h\"\n");
    Header += FString::Printf(TEXT("#include \"%s.generated.h\"\n\n"), *CleanName);

    if (Features.Contains(TEXT("accessibility_flags")))
    {
        Header += TEXT("UENUM(BlueprintType)\n");
        Header += TEXT("enum class EColorblindMode : uint8\n");
        Header += TEXT("{\n");
        Header += TEXT("\tNormal,\n");
        Header += TEXT("\tDeuteranope,\n");
        Header += TEXT("\tProtanope,\n");
        Header += TEXT("\tTritanope\n");
        Header += TEXT("};\n\n");
    }

    Header += FString::Printf(TEXT("UCLASS(config=Game, defaultconfig)\nclass %s %s : public UGameUserSettings\n{\n\tGENERATED_BODY()\n\npublic:\n"), *ApiMacro, *ClassName);
    Header += FString::Printf(TEXT("\t%s();\n\n"), *ClassName);
    Header += TEXT("\tvirtual void ApplyNonResolutionSettings() override;\n\n");
    Header += FString::Printf(TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Settings\")\n\tstatic %s* Get%s();\n\n"), *ClassName, *CleanName);

    if (Features.Contains(TEXT("audio_volumes")))
    {
        Header += TEXT("\t// --- Audio ---\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Audio\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n");
        Header += TEXT("\tfloat MasterVolume = 1.0f;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Audio\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n");
        Header += TEXT("\tfloat MusicVolume = 1.0f;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Audio\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n");
        Header += TEXT("\tfloat SFXVolume = 1.0f;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Audio\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n");
        Header += TEXT("\tfloat VoiceVolume = 1.0f;\n\n");
    }

    if (Features.Contains(TEXT("mouse_sensitivity")))
    {
        Header += TEXT("\t// --- Input ---\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Input\", meta = (ClampMin = \"0.1\", ClampMax = \"10.0\"))\n");
        Header += TEXT("\tfloat MouseSensitivity = 1.0f;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Input\")\n");
        Header += TEXT("\tbool bInvertMouseY = false;\n\n");
    }

    if (Features.Contains(TEXT("accessibility_flags")))
    {
        Header += TEXT("\t// --- Accessibility ---\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Accessibility\")\n");
        Header += TEXT("\tbool bReducedMotion = false;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Accessibility\")\n");
        Header += TEXT("\tbool bHighContrast = false;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Accessibility\", meta = (ClampMin = \"0.75\", ClampMax = \"1.5\"))\n");
        Header += TEXT("\tfloat FontScale = 1.0f;\n\n");
        Header += TEXT("\tUPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category = \"Accessibility\")\n");
        Header += TEXT("\tEColorblindMode ColorblindMode = EColorblindMode::Normal;\n\n");
    }

    if (Features.Contains(TEXT("keybinding_support")))
    {
        Header += TEXT("\t// --- Keybinding ---\n");
        Header += TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Settings|Input\")\n");
        Header += TEXT("\tvoid SaveKeyBindings();\n\n");
        Header += TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Settings|Input\")\n");
        Header += TEXT("\tvoid LoadKeyBindings();\n\n");
    }

    Header += TEXT("};\n");

    // ---- Cpp ----
    FString Cpp;
    Cpp += TEXT("// Auto-generated by Monolith scaffold_game_user_settings\n");
    Cpp += FString::Printf(TEXT("#include \"%s.h\"\n"), *CleanName);
    if (Features.Contains(TEXT("audio_volumes")))
    {
        Cpp += TEXT("#include \"AudioDevice.h\"\n");
        Cpp += TEXT("#include \"Sound/SoundMix.h\"\n");
        Cpp += TEXT("#include \"Sound/SoundClass.h\"\n");
        Cpp += TEXT("#include \"Kismet/GameplayStatics.h\"\n");
    }
    Cpp += TEXT("\n");

    // Constructor
    Cpp += FString::Printf(TEXT("%s::%s()\n{\n}\n\n"), *ClassName, *ClassName);

    // Static getter
    Cpp += FString::Printf(TEXT("%s* %s::Get%s()\n{\n"), *ClassName, *ClassName, *CleanName);
    Cpp += FString::Printf(TEXT("\treturn Cast<%s>(UGameUserSettings::GetGameUserSettings());\n}\n\n"), *ClassName);

    // ApplyNonResolutionSettings
    Cpp += FString::Printf(TEXT("void %s::ApplyNonResolutionSettings()\n{\n"), *ClassName);
    Cpp += TEXT("\tSuper::ApplyNonResolutionSettings();\n\n");
    if (Features.Contains(TEXT("audio_volumes")))
    {
        Cpp += TEXT("\t// Push audio volumes via SoundMix\n");
        Cpp += TEXT("\t// NOTE: Requires USoundMix and USoundClass assets created in editor.\n");
        Cpp += TEXT("\t// Use scaffold_audio_settings to get the asset setup info.\n");
        Cpp += TEXT("\t// Example wiring (uncomment after creating assets):\n");
        Cpp += TEXT("\t//\n");
        Cpp += TEXT("\t// UWorld* World = GEngine->GetCurrentPlayWorld();\n");
        Cpp += TEXT("\t// if (World)\n");
        Cpp += TEXT("\t// {\n");
        Cpp += TEXT("\t//     USoundMix* Mix = LoadObject<USoundMix>(nullptr, TEXT(\"/Game/Audio/SoundMix_Master\"));\n");
        Cpp += TEXT("\t//     USoundClass* MasterClass = LoadObject<USoundClass>(nullptr, TEXT(\"/Game/Audio/SC_Master\"));\n");
        Cpp += TEXT("\t//     if (Mix && MasterClass)\n");
        Cpp += TEXT("\t//     {\n");
        Cpp += TEXT("\t//         UGameplayStatics::SetSoundMixClassOverride(World, Mix, MasterClass, MasterVolume);\n");
        Cpp += TEXT("\t//         UGameplayStatics::PushSoundMixModifier(World, Mix);\n");
        Cpp += TEXT("\t//     }\n");
        Cpp += TEXT("\t// }\n");
    }
    Cpp += TEXT("}\n\n");

    if (Features.Contains(TEXT("keybinding_support")))
    {
        Cpp += FString::Printf(TEXT("void %s::SaveKeyBindings()\n{\n"), *ClassName);
        Cpp += TEXT("\t// TODO: Persist UEnhancedInputUserSettings mappings\n");
        Cpp += TEXT("\t// See scaffold_input_remapping for the full wiring guide\n");
        Cpp += TEXT("\tSaveSettings();\n");
        Cpp += TEXT("}\n\n");

        Cpp += FString::Printf(TEXT("void %s::LoadKeyBindings()\n{\n"), *ClassName);
        Cpp += TEXT("\tLoadSettings();\n");
        Cpp += TEXT("}\n\n");
    }

    // Write files
    TSharedPtr<FJsonObject> Result;
    if (!WriteSourceFiles(SourceDir, CleanName, Header, Cpp, Result, Err))
    {
        return Err;
    }

    // Add DefaultEngine.ini reminder
    FString IniLine = FString::Printf(
        TEXT("[/Script/Engine.Engine]\nGameUserSettingsClassName=/Script/%s.%s"), *ModuleName, *ClassName);
    Result->SetStringField(TEXT("default_engine_ini"), IniLine);
    Result->SetStringField(TEXT("note"), TEXT("Add the DefaultEngine.ini line to register this as the active GameUserSettings class"));

    TArray<TSharedPtr<FJsonValue>> FeatureList;
    for (const FString& F : Features)
    {
        FeatureList.Add(MakeShared<FJsonValueString>(F));
    }
    Result->SetArrayField(TEXT("features"), FeatureList);

    return FMonolithActionResult::Success(Result);
}

// ============================================================================
// scaffold_save_game
// ============================================================================

FMonolithActionResult FMonolithUISettingsActions::HandleScaffoldSaveGame(const TSharedPtr<FJsonObject>& Params)
{
    FString ClassName = Params->GetStringField(TEXT("class_name"));
    FString ModuleName = Params->GetStringField(TEXT("module_name"));
    if (ClassName.IsEmpty() || ModuleName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required params: class_name, module_name"));
    }

    FString CleanName = ClassName;
    if (CleanName.StartsWith(TEXT("U"))) CleanName = CleanName.RightChop(1);

    FString ApiMacro = ModuleName.ToUpper() + TEXT("_API");

    // Parse properties
    struct FSaveProp
    {
        FString Name;
        FString Type;
        FString Default;
    };
    TArray<FSaveProp> Properties;

    const TArray<TSharedPtr<FJsonValue>>* PropsArray = nullptr;
    if (Params->TryGetArrayField(TEXT("properties"), PropsArray))
    {
        for (const auto& Val : *PropsArray)
        {
            const TSharedPtr<FJsonObject>& PropObj = Val->AsObject();
            if (PropObj.IsValid() && PropObj->Values.Num() > 0)
            {
                FSaveProp P;
                P.Name = PropObj->GetStringField(TEXT("name"));
                P.Type = PropObj->GetStringField(TEXT("type"));
                P.Default = PropObj->GetStringField(TEXT("default_value"));
                if (!P.Name.IsEmpty() && !P.Type.IsEmpty())
                {
                    Properties.Add(P);
                }
            }
        }
    }

    FMonolithActionResult Err;
    FString SourceDir = ResolveSourceDir(ModuleName, Err);
    if (SourceDir.IsEmpty()) return Err;

    // ---- Header ----
    FString Header;
    Header += TEXT("// Auto-generated by Monolith scaffold_save_game\n");
    Header += TEXT("#pragma once\n\n");
    Header += TEXT("#include \"CoreMinimal.h\"\n");
    Header += TEXT("#include \"GameFramework/SaveGame.h\"\n");
    Header += FString::Printf(TEXT("#include \"%s.generated.h\"\n\n"), *CleanName);

    Header += FString::Printf(TEXT("UCLASS()\nclass %s %s : public ULocalPlayerSaveGame\n{\n\tGENERATED_BODY()\n\npublic:\n"), *ApiMacro, *ClassName);

    // Data version
    Header += TEXT("\tstatic constexpr int32 LatestSaveVersion = 1;\n\n");
    Header += TEXT("\tvirtual int32 GetLatestDataVersion() const override { return LatestSaveVersion; }\n\n");

    // Properties
    if (Properties.Num() > 0)
    {
        Header += TEXT("\t// --- Save Data ---\n");
        for (const FSaveProp& P : Properties)
        {
            Header += TEXT("\tUPROPERTY(SaveGame, BlueprintReadWrite, Category = \"SaveData\")\n");
            if (P.Default.IsEmpty())
            {
                Header += FString::Printf(TEXT("\t%s %s;\n\n"), *P.Type, *P.Name);
            }
            else
            {
                Header += FString::Printf(TEXT("\t%s %s = %s;\n\n"), *P.Type, *P.Name, *P.Default);
            }
        }
    }
    else
    {
        Header += TEXT("\t// Add UPROPERTY(SaveGame) fields here\n");
        Header += TEXT("\tUPROPERTY(SaveGame, BlueprintReadWrite, Category = \"SaveData\")\n");
        Header += TEXT("\tint32 TotalPlayTimeSeconds = 0;\n\n");
        Header += TEXT("\tUPROPERTY(SaveGame, BlueprintReadWrite, Category = \"SaveData\")\n");
        Header += TEXT("\tFString LastCheckpoint;\n\n");
    }

    // Overrides
    Header += TEXT("protected:\n");
    Header += TEXT("\tvirtual void HandlePostLoad() override;\n\n");
    Header += TEXT("public:\n");
    Header += TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Save\")\n");
    Header += TEXT("\tvoid ResetToDefault();\n");

    Header += TEXT("};\n");

    // ---- Cpp ----
    FString Cpp;
    Cpp += TEXT("// Auto-generated by Monolith scaffold_save_game\n");
    Cpp += FString::Printf(TEXT("#include \"%s.h\"\n\n"), *CleanName);

    // HandlePostLoad with version migration stub
    Cpp += FString::Printf(TEXT("void %s::HandlePostLoad()\n{\n"), *ClassName);
    Cpp += TEXT("\tSuper::HandlePostLoad();\n\n");
    Cpp += TEXT("\tconst int32 LoadedVersion = GetSavedDataVersion();\n\n");
    Cpp += TEXT("\t// Version migration stub — add cases as save format evolves\n");
    Cpp += TEXT("\tif (LoadedVersion < 1)\n");
    Cpp += TEXT("\t{\n");
    Cpp += TEXT("\t\t// Migrate from version 0 to 1\n");
    Cpp += TEXT("\t\tUE_LOG(LogTemp, Log, TEXT(\"Migrating save data from version %d to %d\"), LoadedVersion, LatestSaveVersion);\n");
    Cpp += TEXT("\t}\n");
    Cpp += TEXT("}\n\n");

    // ResetToDefault
    Cpp += FString::Printf(TEXT("void %s::ResetToDefault()\n{\n"), *ClassName);
    if (Properties.Num() > 0)
    {
        for (const FSaveProp& P : Properties)
        {
            if (!P.Default.IsEmpty())
            {
                Cpp += FString::Printf(TEXT("\t%s = %s;\n"), *P.Name, *P.Default);
            }
            else
            {
                Cpp += FString::Printf(TEXT("\t%s = {};\n"), *P.Name);
            }
        }
    }
    else
    {
        Cpp += TEXT("\tTotalPlayTimeSeconds = 0;\n");
        Cpp += TEXT("\tLastCheckpoint = FString();\n");
    }
    Cpp += TEXT("\n\tUE_LOG(LogTemp, Log, TEXT(\"Save data reset to defaults\"));\n");
    Cpp += TEXT("}\n");

    // Write files
    TSharedPtr<FJsonObject> Result;
    if (!WriteSourceFiles(SourceDir, CleanName, Header, Cpp, Result, Err))
    {
        return Err;
    }

    Result->SetNumberField(TEXT("property_count"), Properties.Num());
    Result->SetNumberField(TEXT("latest_version"), 1);

    return FMonolithActionResult::Success(Result);
}

// ============================================================================
// scaffold_save_subsystem
// ============================================================================

FMonolithActionResult FMonolithUISettingsActions::HandleScaffoldSaveSubsystem(const TSharedPtr<FJsonObject>& Params)
{
    FString ClassName = Params->GetStringField(TEXT("class_name"));
    FString ModuleName = Params->GetStringField(TEXT("module_name"));
    FString SaveGameClass = Params->GetStringField(TEXT("save_game_class"));
    if (ClassName.IsEmpty() || ModuleName.IsEmpty() || SaveGameClass.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required params: class_name, module_name, save_game_class"));
    }

    FString CleanName = ClassName;
    if (CleanName.StartsWith(TEXT("U"))) CleanName = CleanName.RightChop(1);

    FString CleanSaveClass = SaveGameClass;
    if (CleanSaveClass.StartsWith(TEXT("U"))) CleanSaveClass = CleanSaveClass.RightChop(1);

    FString ApiMacro = ModuleName.ToUpper() + TEXT("_API");

    FMonolithActionResult Err;
    FString SourceDir = ResolveSourceDir(ModuleName, Err);
    if (SourceDir.IsEmpty()) return Err;

    // ---- Header ----
    FString Header;
    Header += TEXT("// Auto-generated by Monolith scaffold_save_subsystem\n");
    Header += TEXT("#pragma once\n\n");
    Header += TEXT("#include \"CoreMinimal.h\"\n");
    Header += TEXT("#include \"Subsystems/GameInstanceSubsystem.h\"\n");
    Header += FString::Printf(TEXT("#include \"%s.generated.h\"\n\n"), *CleanName);
    Header += FString::Printf(TEXT("class %s;\n\n"), *SaveGameClass);

    Header += TEXT("DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSaveComplete, bool, bSuccess);\n");
    Header += TEXT("DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLoadComplete, bool, bSuccess);\n\n");

    Header += FString::Printf(TEXT("UCLASS()\nclass %s %s : public UGameInstanceSubsystem\n{\n\tGENERATED_BODY()\n\npublic:\n"), *ApiMacro, *ClassName);

    Header += TEXT("\tvirtual void Initialize(FSubsystemCollectionBase& Collection) override;\n");
    Header += TEXT("\tvirtual void Deinitialize() override;\n\n");

    Header += TEXT("\t/** Save current data asynchronously */\n");
    Header += TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Save\")\n");
    Header += TEXT("\tvoid SaveAsync(int32 SlotIndex = 0);\n\n");

    Header += TEXT("\t/** Load save data asynchronously */\n");
    Header += TEXT("\tUFUNCTION(BlueprintCallable, Category = \"Save\")\n");
    Header += TEXT("\tvoid LoadAsync(int32 SlotIndex = 0);\n\n");

    Header += TEXT("\t/** Get the current save data (creates default if none loaded) */\n");
    Header += TEXT("\tUFUNCTION(BlueprintCallable, BlueprintPure, Category = \"Save\")\n");
    Header += FString::Printf(TEXT("\t%s* GetCurrentSave() const;\n\n"), *SaveGameClass);

    Header += TEXT("\t/** Check if a save exists in the given slot */\n");
    Header += TEXT("\tUFUNCTION(BlueprintCallable, BlueprintPure, Category = \"Save\")\n");
    Header += TEXT("\tbool DoesSaveExist(int32 SlotIndex = 0) const;\n\n");

    Header += TEXT("\tUPROPERTY(BlueprintAssignable, Category = \"Save\")\n");
    Header += TEXT("\tFOnSaveComplete OnSaveComplete;\n\n");

    Header += TEXT("\tUPROPERTY(BlueprintAssignable, Category = \"Save\")\n");
    Header += TEXT("\tFOnLoadComplete OnLoadComplete;\n\n");

    Header += TEXT("private:\n");
    Header += TEXT("\tUPROPERTY()\n");
    Header += FString::Printf(TEXT("\tTObjectPtr<%s> CurrentSave;\n\n"), *SaveGameClass);

    Header += TEXT("\tFString GetSlotName(int32 SlotIndex) const;\n");

    Header += TEXT("};\n");

    // ---- Cpp ----
    FString Cpp;
    Cpp += TEXT("// Auto-generated by Monolith scaffold_save_subsystem\n");
    Cpp += FString::Printf(TEXT("#include \"%s.h\"\n"), *CleanName);
    Cpp += FString::Printf(TEXT("#include \"%s.h\"\n"), *CleanSaveClass);
    Cpp += TEXT("#include \"Kismet/GameplayStatics.h\"\n\n");

    // Initialize
    Cpp += FString::Printf(TEXT("void %s::Initialize(FSubsystemCollectionBase& Collection)\n{\n"), *ClassName);
    Cpp += TEXT("\tSuper::Initialize(Collection);\n");
    Cpp += FString::Printf(TEXT("\tCurrentSave = NewObject<%s>(this);\n"), *SaveGameClass);
    Cpp += TEXT("\tUE_LOG(LogTemp, Log, TEXT(\"Save subsystem initialized\"));\n");
    Cpp += TEXT("}\n\n");

    // Deinitialize
    Cpp += FString::Printf(TEXT("void %s::Deinitialize()\n{\n"), *ClassName);
    Cpp += TEXT("\tCurrentSave = nullptr;\n");
    Cpp += TEXT("\tSuper::Deinitialize();\n");
    Cpp += TEXT("}\n\n");

    // GetSlotName
    Cpp += FString::Printf(TEXT("FString %s::GetSlotName(int32 SlotIndex) const\n{\n"), *ClassName);
    Cpp += TEXT("\treturn FString::Printf(TEXT(\"SaveSlot_%d\"), SlotIndex);\n");
    Cpp += TEXT("}\n\n");

    // DoesSaveExist
    Cpp += FString::Printf(TEXT("bool %s::DoesSaveExist(int32 SlotIndex) const\n{\n"), *ClassName);
    Cpp += TEXT("\treturn UGameplayStatics::DoesSaveGameExist(GetSlotName(SlotIndex), 0);\n");
    Cpp += TEXT("}\n\n");

    // GetCurrentSave
    Cpp += FString::Printf(TEXT("%s* %s::GetCurrentSave() const\n{\n"), *SaveGameClass, *ClassName);
    Cpp += TEXT("\treturn CurrentSave;\n");
    Cpp += TEXT("}\n\n");

    // SaveAsync
    Cpp += FString::Printf(TEXT("void %s::SaveAsync(int32 SlotIndex)\n{\n"), *ClassName);
    Cpp += TEXT("\tif (!CurrentSave)\n");
    Cpp += TEXT("\t{\n");
    Cpp += TEXT("\t\tOnSaveComplete.Broadcast(false);\n");
    Cpp += TEXT("\t\treturn;\n");
    Cpp += TEXT("\t}\n\n");
    Cpp += TEXT("\tFString SlotName = GetSlotName(SlotIndex);\n");
    Cpp += TEXT("\tFAsyncSaveGameToSlotDelegate OnDone;\n");
    Cpp += FString::Printf(TEXT("\tOnDone.BindLambda([this](const FString& Slot, int32 UserIdx, bool bSuccess)\n"));
    Cpp += TEXT("\t{\n");
    Cpp += TEXT("\t\tUE_LOG(LogTemp, Log, TEXT(\"Save %s: slot=%s\"), bSuccess ? TEXT(\"succeeded\") : TEXT(\"failed\"), *Slot);\n");
    Cpp += TEXT("\t\tOnSaveComplete.Broadcast(bSuccess);\n");
    Cpp += TEXT("\t});\n\n");
    Cpp += TEXT("\tUGameplayStatics::AsyncSaveGameToSlot(CurrentSave, SlotName, 0, OnDone);\n");
    Cpp += TEXT("}\n\n");

    // LoadAsync
    Cpp += FString::Printf(TEXT("void %s::LoadAsync(int32 SlotIndex)\n{\n"), *ClassName);
    Cpp += TEXT("\tFString SlotName = GetSlotName(SlotIndex);\n\n");
    Cpp += TEXT("\tif (!UGameplayStatics::DoesSaveGameExist(SlotName, 0))\n");
    Cpp += TEXT("\t{\n");
    Cpp += TEXT("\t\tUE_LOG(LogTemp, Warning, TEXT(\"No save in slot: %s\"), *SlotName);\n");
    Cpp += TEXT("\t\tOnLoadComplete.Broadcast(false);\n");
    Cpp += TEXT("\t\treturn;\n");
    Cpp += TEXT("\t}\n\n");
    Cpp += TEXT("\tFAsyncLoadGameFromSlotDelegate OnDone;\n");
    Cpp += TEXT("\tOnDone.BindLambda([this](const FString& Slot, int32 UserIdx, USaveGame* Loaded)\n");
    Cpp += TEXT("\t{\n");
    Cpp += FString::Printf(TEXT("\t\t%s* TypedSave = Cast<%s>(Loaded);\n"), *SaveGameClass, *SaveGameClass);
    Cpp += TEXT("\t\tif (TypedSave)\n");
    Cpp += TEXT("\t\t{\n");
    Cpp += TEXT("\t\t\tCurrentSave = TypedSave;\n");
    Cpp += TEXT("\t\t\tUE_LOG(LogTemp, Log, TEXT(\"Save loaded from slot: %s\"), *Slot);\n");
    Cpp += TEXT("\t\t\tOnLoadComplete.Broadcast(true);\n");
    Cpp += TEXT("\t\t}\n");
    Cpp += TEXT("\t\telse\n");
    Cpp += TEXT("\t\t{\n");
    Cpp += TEXT("\t\t\tUE_LOG(LogTemp, Warning, TEXT(\"Failed to cast save from slot: %s\"), *Slot);\n");
    Cpp += TEXT("\t\t\tOnLoadComplete.Broadcast(false);\n");
    Cpp += TEXT("\t\t}\n");
    Cpp += TEXT("\t});\n\n");
    Cpp += TEXT("\tUGameplayStatics::AsyncLoadGameFromSlot(SlotName, 0, OnDone);\n");
    Cpp += TEXT("}\n");

    // Write files
    TSharedPtr<FJsonObject> Result;
    if (!WriteSourceFiles(SourceDir, CleanName, Header, Cpp, Result, Err))
    {
        return Err;
    }

    Result->SetStringField(TEXT("save_game_class"), SaveGameClass);
    Result->SetStringField(TEXT("note"), TEXT("Remember to include the save game header in your module's Build.cs dependencies"));

    return FMonolithActionResult::Success(Result);
}

// ============================================================================
// scaffold_audio_settings (INFO ONLY — returns setup guide, no files written)
// ============================================================================

FMonolithActionResult FMonolithUISettingsActions::HandleScaffoldAudioSettings(const TSharedPtr<FJsonObject>& Params)
{
    // Parse categories
    TArray<FString> Categories;
    const TArray<TSharedPtr<FJsonValue>>* CatsArray = nullptr;
    if (Params->TryGetArrayField(TEXT("categories"), CatsArray))
    {
        for (const auto& Val : *CatsArray)
        {
            Categories.Add(Val->AsString());
        }
    }
    else
    {
        Categories = { TEXT("Master"), TEXT("Music"), TEXT("SFX"), TEXT("Voice"), TEXT("Ambient") };
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

    // Sound Classes
    TArray<TSharedPtr<FJsonValue>> ClassArray;
    for (const FString& Cat : Categories)
    {
        TSharedPtr<FJsonObject> SC = MakeShared<FJsonObject>();
        SC->SetStringField(TEXT("asset_name"), FString::Printf(TEXT("SC_%s"), *Cat));
        SC->SetStringField(TEXT("asset_type"), TEXT("SoundClass"));
        SC->SetStringField(TEXT("suggested_path"), FString::Printf(TEXT("/Game/Audio/SC_%s"), *Cat));
        if (Cat != TEXT("Master"))
        {
            SC->SetStringField(TEXT("parent_class"), TEXT("SC_Master"));
        }
        ClassArray.Add(MakeShared<FJsonValueObject>(SC));
    }
    Result->SetArrayField(TEXT("sound_classes"), ClassArray);

    // Sound Mix
    TSharedPtr<FJsonObject> Mix = MakeShared<FJsonObject>();
    Mix->SetStringField(TEXT("asset_name"), TEXT("SoundMix_Master"));
    Mix->SetStringField(TEXT("asset_type"), TEXT("SoundMix"));
    Mix->SetStringField(TEXT("suggested_path"), TEXT("/Game/Audio/SoundMix_Master"));

    TArray<TSharedPtr<FJsonValue>> MixEntries;
    for (const FString& Cat : Categories)
    {
        TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
        Entry->SetStringField(TEXT("sound_class"), FString::Printf(TEXT("SC_%s"), *Cat));
        Entry->SetNumberField(TEXT("volume_adjust"), 1.0);
        Entry->SetNumberField(TEXT("pitch_adjust"), 1.0);
        MixEntries.Add(MakeShared<FJsonValueObject>(Entry));
    }
    Mix->SetArrayField(TEXT("mix_entries"), MixEntries);
    Result->SetObjectField(TEXT("sound_mix"), Mix);

    // Hierarchy
    TSharedPtr<FJsonObject> Hierarchy = MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> Children;
    for (int32 i = 1; i < Categories.Num(); ++i)
    {
        Children.Add(MakeShared<FJsonValueString>(Categories[i]));
    }
    Hierarchy->SetStringField(TEXT("root"), Categories[0]);
    Hierarchy->SetArrayField(TEXT("children"), Children);
    Result->SetObjectField(TEXT("hierarchy"), Hierarchy);

    // Wiring code
    TSharedPtr<FJsonObject> Wiring = MakeShared<FJsonObject>();
    Wiring->SetStringField(TEXT("push_mix"),
        TEXT("UGameplayStatics::PushSoundMixModifier(World, SoundMix_Master)"));
    Wiring->SetStringField(TEXT("set_volume"),
        TEXT("UGameplayStatics::SetSoundMixClassOverride(World, SoundMix_Master, SC_Category, Volume, 1.0f, 0.0f)"));
    Wiring->SetStringField(TEXT("clear_overrides"),
        TEXT("UGameplayStatics::ClearSoundMixClassOverride(World, SoundMix_Master, SC_Category)"));
    Wiring->SetStringField(TEXT("note"),
        TEXT("Call PushSoundMixModifier once on game start. Use SetSoundMixClassOverride per-category when the user changes a volume slider."));
    Result->SetObjectField(TEXT("wiring_code"), Wiring);

    // Setup steps
    TArray<TSharedPtr<FJsonValue>> Steps;
    Steps.Add(MakeShared<FJsonValueString>(TEXT("1. Create SoundClass assets in Content Browser (right-click > Sounds > Sound Class)")));
    Steps.Add(MakeShared<FJsonValueString>(TEXT("2. Set parent-child hierarchy: Master > Music, SFX, Voice, Ambient")));
    Steps.Add(MakeShared<FJsonValueString>(TEXT("3. Create SoundMix_Master (right-click > Sounds > Sound Mix)")));
    Steps.Add(MakeShared<FJsonValueString>(TEXT("4. Assign SoundClasses to your sound cues/waves")));
    Steps.Add(MakeShared<FJsonValueString>(TEXT("5. In GameUserSettings::ApplyNonResolutionSettings, call SetSoundMixClassOverride per category")));
    Steps.Add(MakeShared<FJsonValueString>(TEXT("6. Call PushSoundMixModifier once at game startup (e.g. GameMode::BeginPlay)")));
    Result->SetArrayField(TEXT("setup_steps"), Steps);

    return FMonolithActionResult::Success(Result);
}

// ============================================================================
// scaffold_input_remapping (INFO ONLY — returns setup guide, no files written)
// ============================================================================

FMonolithActionResult FMonolithUISettingsActions::HandleScaffoldInputRemapping(const TSharedPtr<FJsonObject>& Params)
{
    // Parse actions
    TArray<FString> Actions;
    const TArray<TSharedPtr<FJsonValue>>* ActionsArray = nullptr;
    if (Params->TryGetArrayField(TEXT("actions"), ActionsArray))
    {
        for (const auto& Val : *ActionsArray)
        {
            Actions.Add(Val->AsString());
        }
    }
    else
    {
        Actions = { TEXT("IA_Move"), TEXT("IA_Look"), TEXT("IA_Jump"), TEXT("IA_Sprint"), TEXT("IA_Crouch"), TEXT("IA_Interact"), TEXT("IA_Fire"), TEXT("IA_Aim") };
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

    // Enhanced Input User Settings setup
    TSharedPtr<FJsonObject> EISetup = MakeShared<FJsonObject>();
    EISetup->SetStringField(TEXT("class"), TEXT("UEnhancedInputUserSettings"));
    EISetup->SetStringField(TEXT("access"),
        TEXT("UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(LocalPlayer);\n"
             "UEnhancedInputUserSettings* UserSettings = Subsystem->GetUserSettings<UEnhancedInputUserSettings>();"));
    EISetup->SetStringField(TEXT("get_mappings"),
        TEXT("const TArray<FEnhancedActionKeyMapping>& Mappings = UserSettings->GetPlayerMappableActionKeyMappings();"));
    EISetup->SetStringField(TEXT("remap"),
        TEXT("UserSettings->MapPlayerKey(MappingName, NewKey, Slot, /* bDirtyOnly */ false);"));
    EISetup->SetStringField(TEXT("save"),
        TEXT("UserSettings->SaveSettings();"));
    EISetup->SetStringField(TEXT("reset"),
        TEXT("UserSettings->ResetAllPlayerKeysToDefault();"));
    Result->SetObjectField(TEXT("enhanced_input_setup"), EISetup);

    // Widget wiring for UInputKeySelector
    TSharedPtr<FJsonObject> WidgetSetup = MakeShared<FJsonObject>();
    WidgetSetup->SetStringField(TEXT("widget_class"), TEXT("UInputKeySelector"));
    WidgetSetup->SetStringField(TEXT("create_per_action"),
        TEXT("For each remappable action, add a row: [TextBlock (action name)] [UInputKeySelector (current binding)]"));
    WidgetSetup->SetStringField(TEXT("bind_on_key_selected"),
        TEXT("InputKeySelector->OnKeySelected.AddDynamic(this, &UMyWidget::OnKeySelected);\n"
             "// In OnKeySelected: UserSettings->MapPlayerKey(ActionName, SelectedKey, Slot, false);"));
    WidgetSetup->SetStringField(TEXT("set_current_key"),
        TEXT("InputKeySelector->SetSelectedKey(CurrentMapping.Key);"));
    WidgetSetup->SetStringField(TEXT("escape_keys"),
        TEXT("InputKeySelector->SetEscapeKeys({ EKeys::Escape, EKeys::RightMouseButton });"));
    Result->SetObjectField(TEXT("widget_wiring"), WidgetSetup);

    // Actions list
    TArray<TSharedPtr<FJsonValue>> ActionList;
    for (const FString& A : Actions)
    {
        TSharedPtr<FJsonObject> ActionObj = MakeShared<FJsonObject>();
        ActionObj->SetStringField(TEXT("action_name"), A);
        ActionObj->SetStringField(TEXT("display_name"), A.Replace(TEXT("IA_"), TEXT("")));
        ActionObj->SetBoolField(TEXT("remappable"), true);
        ActionList.Add(MakeShared<FJsonValueObject>(ActionObj));
    }
    Result->SetArrayField(TEXT("actions"), ActionList);

    // Save/load flow
    TArray<TSharedPtr<FJsonValue>> Flow;
    Flow.Add(MakeShared<FJsonValueString>(TEXT("1. On settings UI open: read current mappings from UEnhancedInputUserSettings")));
    Flow.Add(MakeShared<FJsonValueString>(TEXT("2. Populate each UInputKeySelector with the current FKey")));
    Flow.Add(MakeShared<FJsonValueString>(TEXT("3. On key selected: call MapPlayerKey() to update mapping")));
    Flow.Add(MakeShared<FJsonValueString>(TEXT("4. On Apply: call SaveSettings() to persist")));
    Flow.Add(MakeShared<FJsonValueString>(TEXT("5. On Cancel: call ResetAllPlayerKeysToDefault() or re-load settings")));
    Flow.Add(MakeShared<FJsonValueString>(TEXT("6. On game start: UEnhancedInputUserSettings auto-loads saved mappings")));
    Result->SetArrayField(TEXT("save_load_flow"), Flow);

    // DefaultInput.ini note
    Result->SetStringField(TEXT("config_note"),
        TEXT("Mark actions as PlayerMappable in your InputMappingContext: set bIsPlayerMappable=true on each mapping. "
             "In DefaultInput.ini, add [/Script/EnhancedInput.EnhancedInputDeveloperSettings] with the IMC asset path."));

    return FMonolithActionResult::Success(Result);
}
