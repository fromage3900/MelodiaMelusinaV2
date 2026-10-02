// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFGASEditorSubsystem.h"

#include "HAL/PlatformFilemanager.h"
#include "Internationalization/Regex.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include <Misc/App.h>

bool UACFGASEditorSubsystem::CreateAttributesHeaderFile(const FDirectoryPath& headerPath, const FString& attributeSetName, const TArray<FString>& attributes)
{
    const FString ObjectName = "U" + attributeSetName;

    FString ProjectName; // = FApp::GetProjectName(); // Ottiene il nome del progetto in maiuscolo

    const FString FileName = headerPath.Path + "/" + attributeSetName + ".h ";

    if (!GetModuleNameFromPath(FileName, ProjectName)) {
        return false;
    }

    AddDependenciesToBuildCS(ProjectName);
    FString ApiMacro = ProjectName.ToUpper() + "_API";

    FString FileContent = TEXT("#pragma once\n");
    FileContent += TEXT("#include \"CoreMinimal.h\"\n");
    FileContent += TEXT("#include \"ACFBaseAttributeSet.h\"\n\n");
    FileContent += "#include \"" + attributeSetName + ".generated.h\"" + TEXT("\n\n");

    FileContent += TEXT("\n\n");
    FileContent += TEXT("UCLASS()\n");
    FileContent += FString::Printf(TEXT("class %s %s : public UACFBaseAttributeSet\n"), *ApiMacro, *ObjectName);
    FileContent += TEXT("{\n");
    FileContent += TEXT("    GENERATED_BODY()\n\n");
    FileContent += TEXT("public:\n");
    FileContent += "    " + ObjectName + "();";
    FileContent += TEXT("\n");

    for (const auto& attribute : attributes) {
        FileContent += TEXT("    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = ACF)\n");
        FileContent += "    FGameplayAttributeData " + attribute + TEXT(";\n");
        FileContent += "    ATTRIBUTE_ACCESSORS(" + ObjectName + " , " + attribute + TEXT(");\n");
    }

    FileContent += "protected :";
    FileContent += TEXT("\n");
    FileContent += " virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty> & OutLifetimeProps) const override;";
    FileContent += TEXT("\n");
    FileContent += TEXT("};\n");

    if (FFileHelper::SaveStringToFile(FileContent, *FileName)) {
        UE_LOG(LogTemp, Log, TEXT("File %s creato con successo"), *FileName);
        return true;
    } else {
        UE_LOG(LogTemp, Error, TEXT("Impossibile creare il file %s"), *FileName);
    }
    return false;
}

bool UACFGASEditorSubsystem::CreateAttributesCppFile(const FDirectoryPath& headerPath, const FString& attributeSetName, const TArray<FString>& attributes)
{
    const FString ObjectName = "U" + attributeSetName;
    const FString ProjectName = FApp::GetProjectName(); // Ottiene il nome del progetto in maiuscolo

    FString PathName = headerPath.Path;
    PathName.ReplaceInline(TEXT("Public"), TEXT("Private"), ESearchCase::CaseSensitive);

    const FString FileName = PathName + "/" + attributeSetName + ".cpp ";

    FString FileContent = "#include \"" + attributeSetName + ".h\"" + TEXT("\n\n");
    FileContent += TEXT("#include \"Net/UnrealNetwork.h\"\n\n");

    FileContent += ObjectName + "::" + ObjectName + "()";
    FileContent += TEXT("{\n");
    FileContent += TEXT("    // Codice del costruttore\n");
    FileContent += TEXT("}\n");
    FileContent += TEXT("\n");
    FileContent += TEXT("\n");
    FileContent += TEXT("void ") + ObjectName + TEXT("::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const\n");
    FileContent += TEXT("{\n");
    FileContent += TEXT(" Super::GetLifetimeReplicatedProps(OutLifetimeProps);\n");

    for (const auto& attribute : attributes) {
        FileContent += TEXT("        DOREPLIFETIME_CONDITION_NOTIFY(") + ObjectName + ", " + attribute + TEXT(", COND_None, REPNOTIFY_Always);\n");
    }

    FileContent += TEXT("}\n");
    if (FFileHelper::SaveStringToFile(FileContent, *FileName)) {
        UE_LOG(LogTemp, Log, TEXT("File %s creato con successo"), *FileName);
        return true;
    } else {
        UE_LOG(LogTemp, Error, TEXT("Impossibile creare il file %s"), *FileName);
    }
    return false;
}

UACFGASEditorSubsystem::UACFGASEditorSubsystem()
{
}

bool UACFGASEditorSubsystem::CreateAttributeFiles(const FDirectoryPath& headerPath, const FString& attributeSetName, const TArray<FString>& attributes)
{
    return CreateAttributesHeaderFile(headerPath, attributeSetName, attributes) && CreateAttributesCppFile(headerPath, attributeSetName, attributes);
}

bool UACFGASEditorSubsystem::IsValidAttributeFile(const FFilePath& filePath)
{
    FString FilePath = filePath.FilePath;
    if (!FPlatformFileManager::Get().GetPlatformFile().FileExists(*FilePath)) {
        UE_LOG(LogTemp, Warning, TEXT("File %s does not exists"), *FilePath);
        return false;
    }

    // FPaths::GetPath(FilePath)
    // FPaths::GetBaseFilename(FilePath)
    // Verifica l'estensione del file
    FString FileExtension = FPaths::GetExtension(FilePath);
    if (!FileExtension.Equals(TEXT("h"), ESearchCase::IgnoreCase)) {
        UE_LOG(LogTemp, Warning, TEXT("Il file %s non ha unestensione .h"), *FilePath);
        return false;
    }

    FString FileContent;
    if (!FFileHelper::LoadFileToString(FileContent, *FilePath)) {
        UE_LOG(LogTemp, Log, TEXT("Il file e stato caricato con successo ed e un valido .h"));
        return false;
    }

    return FileContent.Contains("FGameplayAttributeData ");
}

bool UACFGASEditorSubsystem::ExtractAttributesFromAttributeFile(const FFilePath& filePath, FString& outattributeSetName, TArray<FString>& outAttributes)
{

    if (!IsValidAttributeFile(filePath)) {
        return false;
    }
    // Carica il contenuto del file
    FString FilePath = filePath.FilePath;

    FString FileContent;
    if (FFileHelper::LoadFileToString(FileContent, *FilePath)) {
        // Espressione regolare per trovare gli attributi definiti come "FGameplayAttributeData attribute;"
        FRegexPattern Pattern(TEXT("FGameplayAttributeData\\s+(\\w+)\\s*;"));

        FRegexMatcher Matcher(Pattern, FileContent);
        outattributeSetName = FPaths::GetBaseFilename(FilePath);

        // Trova tutte le occorrenze e aggiungile all'array
        while (Matcher.FindNext()) {
            FString AttributeName = Matcher.GetCaptureGroup(1);
            outAttributes.Add(AttributeName);
        }

        return true;
    }
    return false;
}

FDirectoryPath UACFGASEditorSubsystem::GetDefaultHeaderPath() const
{
    const FString ProjectName = FApp::GetProjectName();

    const FString FileName = FPaths::ProjectDir() + "Source/" + ProjectName + "/Public/"; //+ attributeSetName + ".h ";

    FDirectoryPath newPath(FileName);

    return newPath;
}

bool UACFGASEditorSubsystem::GetModuleNameFromPath(const FString& FilePath, FString& outModuleName)
{
    FString ModuleName;
    FModuleManager& ModuleManager = FModuleManager::Get();

    TArray<FName> ModuleNames;
    ModuleManager.FindModules(TEXT("*"), ModuleNames);

    for (const FName& Name : ModuleNames) {

        FString ModuleFilePath = Name.ToString();
        if (FilePath.Contains(ModuleFilePath)) {
            outModuleName = ModuleFilePath;
            return true;
        }
    }

    return false;
}

void UACFGASEditorSubsystem::AddDependenciesToBuildCS(const FString& moduleName)
{
    // FString ProjectName = FApp::GetProjectName();
    FString BuildFilePath = FPaths::ProjectDir() + TEXT("Source/") + moduleName + TEXT("/") + moduleName + TEXT(".Build.cs");

    FString FileContent;
    if (FFileHelper::LoadFileToString(FileContent, *BuildFilePath)) {
        FString PublicDependencyMarker = TEXT("PublicDependencyModuleNames.AddRange(new string[] {");
        int32 MarkerIndex = FileContent.Find(PublicDependencyMarker);

        if (MarkerIndex != INDEX_NONE) {
            int32 InsertIndex = MarkerIndex + PublicDependencyMarker.Len();
            FString dependency = TEXT("\"GameplayAbilities\"");
            AddDependency(FileContent, dependency, InsertIndex, BuildFilePath);
            dependency = TEXT("\"AscentGASRuntime\"");
            AddDependency(FileContent, dependency, InsertIndex, BuildFilePath);
        } else {
            UE_LOG(LogTemp, Warning, TEXT("Impossibile trovare la sezione PublicDependencyModuleNames in %s"), *BuildFilePath);
        }
    } else {
        UE_LOG(LogTemp, Error, TEXT("Impossibile caricare il contenuto del file %s"), *BuildFilePath);
    }

    if (FFileHelper::SaveStringToFile(FileContent, *BuildFilePath)) {
        UE_LOG(LogTemp, Log, TEXT("File %s aggiornato con successo aggiungendo GameplayAbilities"), *BuildFilePath);
    } else {
        UE_LOG(LogTemp, Error, TEXT("Impossibile salvare il file %s dopo la modifica"), *BuildFilePath);
    }
}

void UACFGASEditorSubsystem::AddDependency(FString& FileContent, FString dependency, int32 InsertIndex, FString BuildFilePath)
{
    if (!FileContent.Contains(dependency)) {
        const FString DependencyToAdd = dependency + TEXT(",");
        FileContent.InsertAt(InsertIndex, DependencyToAdd);

    } else {
        UE_LOG(LogTemp, Log, TEXT("GameplayAbilities gia presente in %s"), *BuildFilePath);
    }
}
