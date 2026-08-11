// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/Tools.h"

#include "IImageWrapperModule.h"
#include "TextureResource.h"
#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Base/SettingsFile.h"
#include "Blueprint/WidgetTree.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Core/QuillscriptSettings.h"
#include "Core/QuillscriptSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerState.h"
#include "HAL/PlatformFileManager.h"
#include "Internationalization/Regex.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Math/BasicMathExpressionEvaluator.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Modules/ModuleManager.h"
#include "Slate/WidgetRenderer.h"
#include "Text/SmartTypewriter.h"
#include "UObject/SavePackage.h"
#include "Utils/Lexer.h"


#pragma region Print

void UTools::Log(FString Message, const UObject* Owner, const EPrintType PrintType)
{
	bool bShow{ UQuillscriptSettings::Get()->GetAlwaysPrintLog() };

	#if WITH_EDITOR

		bShow = true;

	#endif

	if (bShow)
	{
		if (const EVerbosityMode VerbosityMode{ UQuillscriptSettings::Get()->GetVerbosity() }; VerbosityMode != EVerbosityMode::None)
		{
			// Get the owner name if there is one.
			if (Owner)
				Message = TEXT(" ❰ ") + UKismetSystemLibrary::GetDisplayName(Owner) + TEXT(" ❱   ") + Message;

			// Set color.
			FColor TextColor;

			switch (PrintType)
			{
			case EPrintType::Success:
				TextColor = FColor(118, 255, 3);
				Message = TEXT("✔ ") + Message;
				UE_LOG(LogTemp, Log, TEXT("%s"), *Message);
				break;

			case EPrintType::Warning:
				TextColor = FColor(255, 241, 118);
				Message = TEXT("✏ ") + Message;
				UE_LOG(LogTemp, Warning, TEXT("%s"), *Message);
				break;

			case EPrintType::Error:
				TextColor = FColor(255, 82, 82);
				Message = TEXT("✖ ") + Message;
				UE_LOG(LogTemp, Error, TEXT("%s"), *Message);
				break;

			default:
				TextColor = FColor::Cyan;
				Message = TEXT("✒ ") + Message;
				UE_LOG(LogTemp, Display, TEXT("%s"), *Message);
			}

			// Print to screen.
			if (VerbosityMode == EVerbosityMode::Full && GEngine)
				GEngine->AddOnScreenDebugMessage(-1, 10.f, TextColor, Message);
		}
	}
}

void UTools::Print(const FString Message, const UObject* Owner)
{
	Log(Message, Owner, EPrintType::Log);
}

void UTools::Success(const FString Message, const UObject* Owner)
{
	Log(Message, Owner, EPrintType::Success);
}

void UTools::Warning(const FString Message, const UObject* Owner)
{
	Log(Message, Owner, EPrintType::Warning);
}

void UTools::Error(const FString Message, const UObject* Owner)
{
	Log(Message, Owner, EPrintType::Error);
}

#pragma endregion Print


#pragma region Utilities

void UTools::RenameObject(UObject* Object, FString NewName)
{
	if (Object && !NewName.IsEmpty())
	{
		NewName.TrimStartAndEndInline();
		NewName.ReplaceInline(TEXT(" "), TEXT(""));

		Object->Rename(*NewName);
	}
}

UClass* UTools::FindClassByPath(FString Path)
{
	if (!Path.StartsWith("/"))
		Path.InsertAt(0, "/");

	FSoftClassPath SoftClassPath{ Path };
	TObjectPtr<UClass> Class{ SoftClassPath.TryLoadClass<UObject>() };

	if (Class)
		return Class;

	// Try to complete a C++ path.
	if (!Path.StartsWith("/Script/"))
		SoftClassPath.SetPath("/Script" + Path);

	Class = SoftClassPath.TryLoadClass<UObject>();

	if (Class)
		return Class;

	// Try to complete a blueprint path.
	if (!Path.EndsWith("_C") && !Path.EndsWith("_C\'"))
	{
		if (Path.RemoveFromEnd("\'"))
			Path.Append("_C\'");
		else
			Path.Append("_C");
	}

	SoftClassPath.SetPath(Path);
	return SoftClassPath.TryLoadClass<UObject>();
}

UObject* UTools::GetClassDefaultObject(const UClass* Class)
{
	if (Class)
		return Class->GetDefaultObject();

	return nullptr;
}

bool UTools::PropertyExists(UObject* Object, const FName PropertyName, FString& Type)
{
	Type = "undefined";

	// Check if the object is valid and the property name is not empty.
	if (!IsValid(Object) || PropertyName.IsNone())
	{ Warning("UTools::GetPropertyByName() -> 'Object' or 'Property Name' is invalid."); return false; }

	// Find the property in the class.
	if (const FProperty* Property{ Object->GetClass()->FindPropertyByName(PropertyName) })
	{
		Type = Property->GetCPPType();
		return true;
	}

	return false;
}

FString UTools::GetPropertyByName(UObject* Object, const FName PropertyName, FString& Type)
{
	Type = "undefined";

	// Check if the object is valid and the property name is not empty.
	if (!IsValid(Object) || PropertyName.IsNone())
	{ Warning("UTools::GetPropertyByName() -> 'Object' or 'Property Name' is invalid."); return ""; }

	// Find the property in the class.
	if (const FProperty* Property{ Object->GetClass()->FindPropertyByName(PropertyName) })
	{
		FString PropertyAsString;
		Type = Property->GetCPPType();

		// Export the property value to a string.
		Property->ExportTextItem_Direct(
			PropertyAsString,
			Property->ContainerPtrToValuePtr<FString*>(Object),
			nullptr,
			Object,
			PPF_None
		);

		// Fix empty values.
		if (PropertyAsString.IsEmpty())
		{
			if (Type == "bool")
				PropertyAsString = "false";
			if (Type == "uint8" || Type == "int32" || Type == "int64" || Type == "float" || Type == "double")
				PropertyAsString = "0";
		}

		return PropertyAsString;
	}

	Warning("UTools::GetPropertyByName() -> 'Object' does not have a property named: " + PropertyName.ToString());
	return "";
}

void UTools::SetPropertyByName(UObject* Object, const FName PropertyName, const FString ValueAsString)
{
	// Check if the object is valid and the property name is not empty.
	if (!IsValid(Object) || PropertyName.IsNone())
	{ Warning("UTools::SetPropertyByName() -> 'Object' or 'Property Name' is invalid."); return; }

	if (const FProperty* Property{ Object->GetClass()->FindPropertyByName(PropertyName) })
	{
		Property->ImportText_Direct(
			*ValueAsString,
			Property->ContainerPtrToValuePtr<FString*>(Object),
			Object,
			PPF_None
		);

		return;
	}

	Warning("UTools::SetPropertyByName() -> 'Object' does not have a property named: " + PropertyName.ToString());
}

void* UTools::FindPropertyByName(UObject* Object, const FName PropertyName, FString& Type)
{
	void* PropertyValue{ nullptr };
	Type = "undefined";

	// Check if the object is valid and the property name is not empty.
	if (!Object || PropertyName.IsNone())
	{ Warning("UTools::FindPropertyByName() -> 'Object' or 'Property Name' is invalid."); return nullptr; }

	// Find the property in the class.
	if (const TObjectPtr<UClass> ObjectClass{ Object->GetClass() })
	{
		if (const FProperty* Property{ FindFProperty<FProperty>(ObjectClass, PropertyName) })
		{
			// Get the property type.
			Type = Property->GetCPPType();

			// Export the property value to a void pointer.
			PropertyValue = Property->ContainerPtrToValuePtr<void>(Object);
		}
		else
			Warning("UTools::FindPropertyByName() -> 'Object' does not have a property named: " + PropertyName.ToString());
	}

	return PropertyValue;
}

void UTools::InsertPropertyByName(UObject* Object, const FName PropertyName, const void* ValuePtr)
{
	// Check if the object is valid and the property name is not empty.
	if (!Object)
		Warning("UTools::InsertPropertyByName() -> 'Object' is invalid.");

	// Set property.
	if (const TObjectPtr<UClass> ObjectClass{ Object->GetClass() })
	{
		if (const FProperty* Property{ FindFProperty<FProperty>(ObjectClass, PropertyName) })
			Property->SetValue_InContainer(Object, ValuePtr);
		else
			Warning("UTools::SetPropertyByName() -> 'Object' does not have a property named: " + PropertyName.ToString());
	}
}

TMap<FName, FString> UTools::CallFunctionByName(UObject* WorldContextObject, UObject* Target, const FName FunctionName, const TArray<FString>& Parameters)
{
	TMap<FName, FString> Outers;

	if (IsValid(Target))
	{
		if (const TObjectPtr<UFunction> Function{ Target->FindFunction(FunctionName) })
		{
			// Allocate parameters' memory.
			uint8* Buffer{ StaticCast<uint8*>(FMemory_Alloca(Function->ParmsSize)) };
			FMemory::Memzero(Buffer, Function->ParmsSize);

			// Add parameters to the container.
			uint32 I{ 0 };
			for (TFieldIterator<FProperty> It{ Function }; It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
			{
				const FProperty* FunctionProperty{ *It };
				FString Type{ FunctionProperty->GetCPPType() };

				// World Context Object parameter, if the function has one.
				if (Type == "UObject*" && ( FunctionProperty->GetName() == "__WorldContext" || FunctionProperty->GetName() == "WorldContextObject" ) && IsValid(Target->GetWorld()))
					*FunctionProperty->ContainerPtrToValuePtr<UObject*>(Buffer) = Target->GetWorld();

				// Other parameters.
				else if (Parameters.IsValidIndex(I))
				{
					// Prevent crashing if the parameter was omitted.
					if (FString Parameter{ Parameters[I] }; Parameter.IsEmpty())
						Parameter = "0";

					// All other parameters' types.
					else
					{
						FunctionProperty->ImportText_Direct(
							*Parameter,
							FunctionProperty->ContainerPtrToValuePtr<void>(Buffer),
							Function,
							PPF_None
						);
					}

					I++;
				}
			}

			// Call the function with parameters, on target.
			Target->ProcessEvent(Function, Buffer);

			// Get the return value and outer parameters.
			for (TFieldIterator<FProperty> It(Function, EFieldIteratorFlags::ExcludeSuper); It; ++It)
			{
				if (const FProperty* OutProperty{ *It }; OutProperty->HasAnyPropertyFlags(CPF_OutParm))
				{
					const FString Type{ OutProperty->GetCPPType() };
					FString Value;

					OutProperty->ExportText_Direct(
						Value,
						OutProperty->ContainerPtrToValuePtr<void>(Buffer),
						nullptr,
						Function,
						PPF_None
					);

					// Fix empty values.
					if (Value.IsEmpty())
					{
						if (Type == "bool")
							Value = "false";
						if (Type == "uint8" || Type == "int32" || Type == "int64" || Type == "float" || Type == "double")
							Value = "0";
					}

					if (!Value.IsEmpty())
						Outers.Add(OutProperty->GetFName(), Value);
				}
			}
		}
	}

	return Outers;
}

bool UTools::HasAuthority(const UObject* WorldContextObject)
{
	if (
		WorldContextObject &&
		WorldContextObject->GetWorld() &&
		WorldContextObject->GetWorld()->GetFirstPlayerController()
	)
		return WorldContextObject->GetWorld()->GetFirstPlayerController()->HasAuthority();

	return false;
}

bool UTools::IsModuleLoaded(const FName ModuleName)
{
	if (const FModuleManager* ModuleManager{ &FModuleManager::Get() })
		return ModuleManager->IsModuleLoaded(ModuleName);

	return false;
}

FString UTools::GenerateRandomString(const uint8 Size, const bool bLetters, const bool bNumbers, const bool bSymbols)
{
	FString Id;
	TArray<FString> Chars;

	if (bLetters)
		Chars.Append({ "A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z" });

	if (bNumbers)
		Chars.Append({ "0","1","2","3","4","5","6","7","8","9" });

	if (bSymbols)
		Chars.Append({ "!","@","#","$","%","&","*","-","+","/","?" });

	const int32 Length{ Chars.Num() - 1 };

	for (int32 I{ 0 }; I < Size; I++)
		Id.Append(Chars[FMath::RandRange(0, Length)]);

	return Id;
}

bool UTools::RetrieveOption(const UObject* WorldContextObject, const FString& Key, FString& Value)
{
	if (const TObjectPtr<AGameModeBase> GameMode{ UGameplayStatics::GetGameMode(WorldContextObject) })
	{
		Value = UGameplayStatics::ParseOption(GameMode->OptionsString, Key);

		if (!Value.IsEmpty())
			return true;
	}

	return false;
}

TArray<FString> UTools::SortStringsAlphabetically(TArray<FString> Strings)
{
	Strings.Sort([](const FString& A, const FString& B) {
		return RemoveAccentuation(A).ToLower() < RemoveAccentuation(B).ToLower();
	});

	return Strings;
}

void UTools::RegisterStringTable(const FName StringTablePath)
{
	if (!FStringTableRegistry::Get().FindStringTable(StringTablePath).IsValid())
	{
		const FSoftObjectPath AssetPath{ StringTablePath.ToString() };
		AssetPath.TryLoad();
	}
}

FString UTools::FindStringTableKey(const FText& Text, FName& StringTableId)
{
	if (FTextKey Key; FTextInspector::GetTableIdAndKey(Text, StringTableId, Key))
		return Key.ToString();

	return FString();
}

TArray<FString> UTools::GetVariablesInString(const FString String)
{
	TArray<FString> VariablesNames;

	for (int32 I{ 0 }; I < String.Len(); ++I)
	{
		if (String.Mid(I, 1) == SYMBOL(CurlyOpen))
		{
			FString VariableName{ "" };

			++I;

			while (String.Mid(I, 1) != SYMBOL(CurlyClose))
			{
				VariableName += String.Mid(I, 1);
				++I;
			}

			VariablesNames.Add(VariableName);
		}
	}

	return VariablesNames;
}

bool UTools::StringTableContains(const FName StringTableName, const FString Key, FString& OutSourceString)
{
	if (const FStringTableConstPtr StringTable{ FStringTableRegistry::Get().FindStringTable(StringTableName) }; StringTable.IsValid())
		if (StringTable.Get()->GetSourceString(Key, OutSourceString))
			return true;

	return false;
}

FString UTools::GetWorldTypeAsString()
{
	FString None{ "None" };

	if (const TObjectPtr<UWorld> World{ UQuillscriptSubsystem::World() })
	{
		switch (World->WorldType)
		{
		case EWorldType::None:			return None;
		case EWorldType::Game:			return "Game";
		case EWorldType::Editor:		return "Editor";
		case EWorldType::PIE:			return "PIE";
		case EWorldType::EditorPreview:	return "EditorPreview";
		case EWorldType::GamePreview:	return "GamePreview";
		case EWorldType::GameRPC:		return "GameRPC";
		case EWorldType::Inactive:		return "Inactive";

		default: return None;
		}
	}

	return None;
}

int32 UTools::Length(FString ContainerAsString)
{
	ContainerAsString.RemoveSpacesInline();

	// Maps
	if (ContainerAsString.StartsWith("((") && ContainerAsString.EndsWith("))"))
		return ContainerAsString.ReplaceInline(TEXT("),(\""), TEXT("")) + 1;

	// String Arrays and Sets
	if (ContainerAsString.Contains("\",\""))
		return ContainerAsString.ReplaceInline(TEXT("\",\""), TEXT("")) + 1;

	// Others Arrays and Sets
	return ContainerAsString.ReplaceInline(TEXT(","), TEXT("")) + 1;
}

TArray<FString> UTools::RegexMatch(const FString& SourceString, const FString& Pattern, const bool bCaseInsensitive)
{
	TArray<FString> Matches;
	ERegexPatternFlags Flags{ ERegexPatternFlags::None };

	if (bCaseInsensitive)
		Flags = ERegexPatternFlags::CaseInsensitive;

	FRegexMatcher RegexMatcher{ FRegexPattern(Pattern, Flags), SourceString };

	while (RegexMatcher.FindNext())
		Matches.Add(RegexMatcher.GetCaptureGroup(0));

	return Matches;
}

#pragma endregion Utilities


#pragma region Metadata

FString UTools::GetProjectName()
{
	FString ProjectName;

	GConfig->GetString(
		TEXT("/Script/EngineSettings.GeneralProjectSettings"),
		TEXT("ProjectName"),
		ProjectName,
		GGameIni
	);

	return ProjectName;
}

FString UTools::GetProjectVersion()
{
	FString ProjectVersion;

	GConfig->GetString(
		TEXT("/Script/EngineSettings.GeneralProjectSettings"),
		TEXT("ProjectVersion"),
		ProjectVersion,
		GGameIni
	);

	return ProjectVersion;
}

FString UTools::GetCompanyName()
{
	FString CompanyName;

	GConfig->GetString(
		TEXT("/Script/EngineSettings.GeneralProjectSettings"),
		TEXT("CompanyName"),
		CompanyName,
		GGameIni
	);

	return CompanyName;
}

#pragma endregion Metadata


#pragma region Assets

void UTools::MarkAssetDirty(const UObject* Asset)
{
	if (const TObjectPtr<UPackage> Package = Asset->GetOutermost())
		Package->SetDirtyFlag(true);
}

void UTools::SaveAsset(UObject* Asset)
{
	// Get the package path.
	if (const TObjectPtr<UPackage> Package = Asset->GetOutermost())
	{
		const FString PackageName{ Package->GetName() };

		// Save to disk asset.
		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_NoFlags;
		SaveArgs.SaveFlags = 0U;
		SaveArgs.bForceByteSwapping = false;
		SaveArgs.bWarnOfLongFilename = true;
		SaveArgs.bSlowTask = true;
		SaveArgs.FinalTimeStamp = FDateTime::MinValue();
		SaveArgs.Error = GError;

		if (UPackage::SavePackage(Package, Asset, *FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension()), SaveArgs))
			Success("Asset saved to: " + PackageName, Asset);
	}
}

bool UTools::AssetExists(const FString& AssetPath)
{
	return FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get().GetAssetByObjectPath(FSoftObjectPath(AssetPath)).IsValid();
}

UObject* UTools::LoadAssetByPath(const FString& Path)
{
	return LoadAssetByPath<UObject>(Path);
}

#pragma endregion Assets


#pragma region Files

TArray<FString> UTools::GetAllSaveGameSlotNames()
{
	// Create a class to override the Visit method.
	class FFindSavesVisitor : public IPlatformFile::FDirectoryVisitor
	{
	public:
		TArray<FString> SavesFound;

		virtual bool Visit(const TCHAR* FilenameOrDirectory, bool bIsDirectory) override
		{
			if (!bIsDirectory)
			{
				if (const FString FullFilePath(FilenameOrDirectory); FPaths::GetExtension(FullFilePath) == "sav")
				{
					FString CleanFilename{ FPaths::GetBaseFilename(FullFilePath) };
					CleanFilename = CleanFilename.Replace(TEXT(".sav"), TEXT(""));
					SavesFound.Add(CleanFilename);
				}
			}

			return true;
		}
	};

	// Get all saves files.
	TArray<FString> Saves;

	if (const FString SavesFolder{ FPaths::ProjectSavedDir() + "SaveGames" }; !SavesFolder.IsEmpty())
	{
		FFindSavesVisitor Visitor;
		FPlatformFileManager::Get().GetPlatformFile().IterateDirectory(*SavesFolder, Visitor);
		Saves = Visitor.SavesFound;
	}

	return Saves;
}

bool UTools::SaveToTextFile(const FString FileName, const FString FileContent, const EDirectory BaseDirectory)
{
	return FFileHelper::SaveStringToFile(FileContent, *(DirectoryToString(BaseDirectory) + FileName));
}

bool UTools::LoadTextFile(FString& FileContent, const FString FileName, const EDirectory BaseDirectory)
{
	return FFileHelper::LoadFileToString(FileContent, *(DirectoryToString(BaseDirectory) + FileName));
}

UTexture2D* UTools::LoadImage(const FString FileName, const EDirectory BaseDirectory)
{
	TObjectPtr<UTexture2D> Texture{ nullptr };

	IImageWrapperModule& ImageWrapperModule{ FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName("ImageWrapper")) };
	const TSharedPtr ImageWrapper{ ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG) };

	if (TArray64<uint8> RawFileData; FFileHelper::LoadFileToArray(RawFileData, *(DirectoryToString(BaseDirectory) + FileName)))
	{
		if (ImageWrapper.IsValid() && ImageWrapper->SetCompressed(RawFileData.GetData(), RawFileData.Num()))
		{
			if (TArray<uint8> Uncompressed; ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, Uncompressed))
			{
				Texture = UTexture2D::CreateTransient(ImageWrapper->GetWidth(), ImageWrapper->GetHeight(), EPixelFormat::PF_B8G8R8A8);

				// Copy data.
				void* TextureData = Texture->GetPlatformData()->Mips[0].BulkData.Lock(EBulkDataLockFlags::LOCK_READ_WRITE);
				FMemory::Memcpy(TextureData, Uncompressed.GetData(), Uncompressed.Num());
				Texture->GetPlatformData()->Mips[0].BulkData.Unlock();

				// Update the rendering resource from data.
				Texture->UpdateResource();
			}
		}
	}

	return Texture;
}

void UTools::TakeScreenshot(const EDirectory BaseDirectory, const FString FileName, const bool bCaptureUI)
{
	FScreenshotRequest::RequestScreenshot(DirectoryToString(BaseDirectory) + FileName + ".png", bCaptureUI, false);
}

FString UTools::DirectoryToString(const EDirectory Directory)
{
	switch (Directory)
	{
	case EDirectory::Project:			return FPaths::ProjectDir();
	case EDirectory::ProjectContent:	return FPaths::ProjectContentDir();
	case EDirectory::ProjectSaved:		return FPaths::ProjectSavedDir();
	case EDirectory::ProjectConfig:		return FPaths::ProjectConfigDir();
	case EDirectory::ScreenShot:		return FPaths::ScreenShotDir();
	case EDirectory::Launch:			return FPaths::LaunchDir();
	default: return "";
	}
}

TArray<FString> UTools::ListFiles(FString Directory, const TArray<FString> FileExtensionFilter, const EDirectory BaseDirectory, const bool bRecursively)
{
	TArray<FString> FilesList;
	Directory = DirectoryToString(BaseDirectory) + Directory;

	if(IPlatformFile& PlatformFile{ FPlatformFileManager::Get().GetPlatformFile() }; PlatformFile.DirectoryExists(*Directory))
	{
		auto FindFiles = [&FilesList, &PlatformFile, &bRecursively](const FString& InDirectory, const TCHAR* InFileExtensionFilter)
		{
			TArray<FString> Files;

			if (bRecursively)
				PlatformFile.FindFilesRecursively(Files, *InDirectory, InFileExtensionFilter);
			else
				PlatformFile.FindFiles(Files, *InDirectory, InFileExtensionFilter);

			FilesList.Append(Files);
		};

		if (FileExtensionFilter.IsEmpty())
			FindFiles(Directory, nullptr);
		else
		{
			for (const FString& FileExtension : FileExtensionFilter)
				FindFiles(Directory, *FileExtension);
		}
	}
	else
		Error("UTools::ListFilesInDirectory() -> Directory does not exist: " + Directory);

	return FilesList;
}

TArray<FString> UTools::ListDirectories(FString Directory, const EDirectory BaseDirectory, const bool bRecursively)
{
	TArray<FString> FilesList;
	Directory = DirectoryToString(BaseDirectory) + Directory;

	if(IPlatformFile& PlatformFile{ FPlatformFileManager::Get().GetPlatformFile() }; PlatformFile.DirectoryExists(*Directory))
	{
		auto IterateDirectory = [&FilesList](const TCHAR* FilenameOrDirectory, const bool bIsDirectory) -> bool
		{
			if (bIsDirectory)
				FilesList.Add(FString(FilenameOrDirectory));

			return true;
		};

		if (bRecursively)
			PlatformFile.IterateDirectoryRecursively(*Directory, IterateDirectory);
		else
			PlatformFile.IterateDirectory(*Directory, IterateDirectory);
	}
	else
		Error("UTools::ListFilesInDirectory() -> Directory does not exist: " + Directory);

	return FilesList;
}

void UTools::LaunchFile(FString FilePath, const EDirectory BaseDirectory)
{
	FilePath = DirectoryToString(BaseDirectory) + FilePath;

	if (FPaths::FileExists(FilePath))
	{
		if (!FPlatformProcess::LaunchFileInDefaultExternalApplication(*FilePath, nullptr, ELaunchVerb::Open))
			Error("UTools::LaunchFile() -> Failed to open file: " + FilePath);
	}
	else
		Error("UTools::LaunchFile() -> File does not exist: " + FilePath);
}

#pragma endregion Files


#pragma region Settings

bool UTools::GetBoolSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, bool& SettingValue)
{
	return GConfig->GetBool(*Section, *Key, SettingValue, SettingFileToString(SettingFile));
}

void UTools::SetBoolSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const bool Value, const FString CustomFile)
{
	if (GConfig)
	{
		const FString FileName{ SettingFile == ESettingsFile::Custom ? CustomFile : SettingFileToString(SettingFile) };

		// Set value.
		GConfig->SetBool(*Section, *Key, Value, FileName);

		// Sometimes the config file won't save changes if you don't call this function after you've set all your config keys.
		GConfig->Flush(false, FileName);
	}
}

bool UTools::GetStringSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, FString& SettingValue)
{
	return GConfig->GetString(*Section, *Key, SettingValue, SettingFileToString(SettingFile));
}

void UTools::SetStringSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const FString Value, const FString CustomFile)
{
	if (GConfig)
	{
		const FString FileName{ SettingFile == ESettingsFile::Custom ? CustomFile : SettingFileToString(SettingFile) };

		// Set value.
		GConfig->SetString(*Section, *Key, *Value, FileName);

		// Sometimes the config file won't save changes if you don't call this function after you've set all your config keys.
		GConfig->Flush(false, FileName);
	}
}

bool UTools::GetIntSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, int32& SettingValue)
{
	return GConfig->GetInt(*Section, *Key, SettingValue, SettingFileToString(SettingFile));
}

void UTools::SetIntSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const int32 Value, const FString CustomFile)
{
	if (GConfig)
	{
		const FString FileName{ SettingFile == ESettingsFile::Custom ? CustomFile : SettingFileToString(SettingFile) };

		// Set value.
		GConfig->SetInt(*Section, *Key, Value, FileName);

		// Sometimes the config file won't save changes if you don't call this function after you've set all your config keys.
		GConfig->Flush(false, FileName);
	}
}

bool UTools::GetFloatSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, float& SettingValue)
{
	return GConfig->GetFloat(*Section, *Key, SettingValue, SettingFileToString(SettingFile));
}

void UTools::SetFloatSetting(const ESettingsFile SettingFile, const FString Section, const FString Key, const float Value, const FString CustomFile)
{
	if (GConfig)
	{
		const FString FileName{ SettingFile == ESettingsFile::Custom ? CustomFile : SettingFileToString(SettingFile) };

		// Set value.
		GConfig->SetFloat(*Section, *Key, Value, FileName);

		// Sometimes the config file won't save changes if you don't call this function after you've set all your config keys.
		GConfig->Flush(false, FileName);
	}
}

FString UTools::SettingFileToString(const ESettingsFile SettingFile)
{
	switch (SettingFile)
	{
	case ESettingsFile::Game:				return GGameIni;
	case ESettingsFile::Editor:				return GEditorIni;
	case ESettingsFile::Input:				return GInputIni;
	case ESettingsFile::Hardware:			return GHardwareIni;
	case ESettingsFile::GameUserSettings:	return GGameUserSettingsIni;
	case ESettingsFile::EditorPerProject:	return GEditorPerProjectIni;
	case ESettingsFile::RuntimeOptions:		return GRuntimeOptionsIni;
	case ESettingsFile::DeviceProfiles:		return GDeviceProfilesIni;
	case ESettingsFile::GameplayTags:		return GGameplayTagsIni;
	case ESettingsFile::Compat:				return GCompatIni;
	case ESettingsFile::Lightmass:			return GLightmassIni;
	case ESettingsFile::Scalability:			return GScalabilityIni;
	case ESettingsFile::InstallBundle:		return GInstallBundleIni;
	case ESettingsFile::EditorLayout:		return GEditorLayoutIni;
	case ESettingsFile::EditorKeyBindings:	return GEditorKeyBindingsIni;
	case ESettingsFile::EditorSettings:		return GEditorSettingsIni;
	default: return "";
	}
}

#pragma endregion Settings


#pragma region UI

void UTools::DestroyWidget(UWidget* Widget)
{
	if (Widget)
	{
		Widget->RemoveFromParent();
		Widget->ConditionalBeginDestroy();
		Widget = nullptr;
	}
}

void UTools::AddToConstraintViewport(UUserWidget* Widget, const int32 ZOrder, const FVector2D Ratio)
{
	// Create child widgets.
	const TObjectPtr<UScaleBox> OuterScale{ Widget->WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass(), "Root") };
	const TObjectPtr<USizeBox> SizeBox{ Widget->WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), "Size Box") };
	const TObjectPtr<UScaleBox> InnerScale{ Widget->WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass(), "Inner Scale") };
	const TObjectPtr<UWidget> Content{ Widget->GetRootWidget() };

	// Setup 'Size Box'.
	SizeBox->SetWidthOverride(Ratio.X);
	SizeBox->SetHeightOverride(Ratio.Y);

	// Setup 'Inner Scale'.
	InnerScale->SetStretch(EStretch::Fill);
	InnerScale->SetClipping(EWidgetClipping::ClipToBoundsAlways);

	// Nest widgets.
	InnerScale->AddChild(Content);
	SizeBox->AddChild(InnerScale);
	OuterScale->AddChild(SizeBox);

	// Change Root.
	Widget->WidgetTree->RootWidget = OuterScale;

	// Add to viewport.
	Widget->AddToViewport(ZOrder);
}

UTexture2D* UTools::CaptureWidget(UUserWidget* UserWidget, const FVector2D DrawSize)
{
	// Create a 2D render target.
	const TObjectPtr<UTextureRenderTarget2D> RenderTarget{ NewObject<UTextureRenderTarget2D>() };
	RenderTarget->InitAutoFormat(DrawSize.X, DrawSize.Y);

	// Create a new widget renderer and render the widget to the render target.
	FWidgetRenderer* Renderer{ new FWidgetRenderer() };
	Renderer->DrawWidget(RenderTarget, UserWidget->TakeWidget(), DrawSize, 0.2f, false);

	// Create new UTexture2D object.
	const TObjectPtr<UTexture2D> Texture{ UTexture2D::CreateTransient(RenderTarget->SizeX, RenderTarget->SizeY, PF_B8G8R8A8) };
	if (!Texture) return nullptr; // Make sure creation was successful

	// Get render target's underlying resource.
	const auto RenderTargetResource{ StaticCast<FTextureRenderTarget2DResource*>(RenderTarget->GameThread_GetRenderTargetResource()) };

	TArray<FColor> OutData;
	RenderTargetResource->ReadPixels(OutData);

	// Perform the copy.
	FTexture2DMipMap& Mip{ Texture->GetPlatformData()->Mips[0] };
	FByteBulkData& RawImageData{ Mip.BulkData };
	void* Data{ RawImageData.Lock(LOCK_READ_WRITE) };

	FMemory::Memcpy(Data, OutData.GetData(), RenderTarget->SizeX * RenderTarget->SizeY * 4); // 4 bytes per pixel (RGBA)

	// Clean up.
	RawImageData.Unlock();
	Texture->UpdateResource();


	return Texture;
}

TArray<UWidget*> UTools::GetNestedWidgets(UWidget* RootWidget)
{
	TArray<UWidget*> Widgets;

	if (IsValid(RootWidget))
	{
		Widgets.Add(RootWidget);

		// Is a Panel Widget.
		if (const UPanelWidget* Panel{ Cast<UPanelWidget>(RootWidget) })
			for (auto* Child : Panel->GetAllChildren())
				Widgets.Append(GetNestedWidgets(Child));

		// Is a User Widget.
		else if (const auto* UserWidget{ Cast<UUserWidget>(RootWidget) })
			Widgets.Append(GetNestedWidgets(UserWidget->GetRootWidget()));
	}

	return Widgets;
}

TArray<UWidget*> UTools::GetNestedWidgetsOfClass(UWidget* RootWidget, const TArray<TSubclassOf<UWidget>> Classes)
{
	TArray<UWidget*> Widgets;

	for (auto* Widget : GetNestedWidgets(RootWidget))
		if (Classes.Contains(Widget->GetClass()))
			Widgets.Add(Widget);

	return Widgets;
}

void UTools::AddChildWidgetAt(UWidget* Parent, UWidget* Child, const int32 Index)
{
	if (IsValid(Parent) && IsValid(Child) && Index >= 0)
	{
		if (const TObjectPtr<UPanelWidget> Panel{ Cast<UPanelWidget>(Parent) })
		{
			auto Children{ Panel->GetAllChildren() };
			bool bAdded{ false };

			// Remove the child from the parent.
			Panel->ClearChildren();

			// Add back the children.
			while (!Children.IsEmpty())
			{
				// Add the child at the specified index.
				if (!bAdded && Panel->GetAllChildren().Num() == Index)
				{
					Panel->AddChild(Child);
					bAdded = true;
				}

				// Add the child back.
				if (Children[0])
				{
					Panel->AddChild(Children[0]);
					Children.RemoveAt(0);
				}
			}

			// Add the child at the end if the index is out of bounds.
			if (!bAdded)
				Panel->AddChild(Child);
		}
	}
}

TArray<UWidget*> UTools::RemoveVisibleWidgets(TArray<UWidget*> Widgets)
{
	TArray<UWidget*> HiddenWidgets;

	for (auto* Widget : Widgets)
		if (Widget && !Widget->IsVisible())
			HiddenWidgets.Add(Widget);

	return HiddenWidgets;
}

TArray<UWidget*> UTools::RemoveHiddenWidgets(TArray<UWidget*> Widgets)
{
	TArray<UWidget*> VisibleWidgets;

	for (auto* Widget : Widgets)
		if (Widget && Widget->IsVisible())
			VisibleWidgets.Add(Widget);

	return VisibleWidgets;
}

ASmartTypewriter* UTools::PlayTypewriterEffect(UObject* WorldContextObject, const FText Text, const FTextPrintedDelegate& PrintedDelegate, const FTextCompletedDelegate& CompletedDelegate, const float Interval, USoundBase* Sound, const bool bOverlapSound, const bool bSanitize)
{
	if (WorldContextObject && WorldContextObject->GetWorld())
	{
		if (const TObjectPtr<ASmartTypewriter> Typewriter{ Cast<ASmartTypewriter>(WorldContextObject->GetWorld()->SpawnActor(ASmartTypewriter::StaticClass())) })
		{
			Typewriter->Initialize(Text, PrintedDelegate, CompletedDelegate, Interval, Sound, bOverlapSound, bSanitize);
			return Typewriter;
		}
	}

	return nullptr;
}

#pragma endregion UI


#pragma region Pipes

FString UTools::ReplaceVariables(const UObject* WorldContextObject, const FString String, TMap<FName, FString> VariablesMap, const TArray<UStringTable*> StringTables, FString Escape)
{
	FString ReplacedString;
	TArray<FString> VariablesNames;

	// Get Quillscript Subsystem reference, if available.
	TObjectPtr<UQuillscriptSubsystem> QuillscriptSubsystem{ nullptr };

	if (WorldContextObject && WorldContextObject->GetWorld() && WorldContextObject->GetWorld()->GetGameInstance())
		QuillscriptSubsystem = WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>();

	// Iterate through each char.
	for (int32 I{ 0 }; I < String.Len(); I++)
	{
		// Get current char.
		const FString CurrentChar{ String.Mid(I, 1) };
		FString PreviousChar;

		if (String.Len() > 1)
			PreviousChar = String.Mid(I-1, 1);

		// If char is an opening bracket, add a new variable to the list.
		if (CurrentChar == SYMBOL(CurlyOpen) && PreviousChar != FLexer::EscapeCharacter)
			VariablesNames.Add("");

		// If char is a closing bracket.
		else if (CurrentChar == SYMBOL(CurlyClose) && !VariablesNames.IsEmpty() && PreviousChar != FLexer::EscapeCharacter)
		{
			// Get a variable name and remove if from the list.
			FString VariableName{ VariablesNames.Pop() };

			// Split the variable name for arrays and maps.
			FString Address;
			if (VariableName.Contains(SYMBOL(Map)))
				VariableName.Split(SYMBOL(Map), &VariableName, &Address);

			// FIND VARIABLE VALUE
			FString VariableValue{ "" };

			// 1 - From variables map.
			if (const FString* Entry{ VariablesMap.Find(FName(VariableName)) })
				VariableValue = *Entry;

			// 2 - From string tables.
			else
				for (const UStringTable* StringTable : StringTables)
					if (StringTable && StringTable->GetStringTable()->GetSourceString(VariableName, VariableValue))
						break;

			// 3 - From container value. (Arrays and Maps)
			if (!Address.IsEmpty())
			{
				// Array.
				if (VariableValue.StartsWith("((") && VariableValue.EndsWith("))"))
					VariableValue = FLexer::GetFromMapString(VariableValue, Address);

				// Map.
				else
					VariableValue = FLexer::GetFromArrayString(VariableValue, FCString::Atoi(*Address));
			}

			// 4 - Regular expressions special cases
			{
				// Dice (1d6, 2d3, 20d12, etc.)
				const FRegexPattern Pattern(TEXT("^(\\d+)[dD](\\d+)$"));
				if (FRegexMatcher Matcher(Pattern, VariableName); Matcher.FindNext())
				{
					int32 NumDice{ FCString::Atoi(*Matcher.GetCaptureGroup(1)) };
					int32 NumSides{ FCString::Atoi(*Matcher.GetCaptureGroup(2)) };
					int32 Sum{ 0 };
					FString Verbose{ VariableName + " roll: " };

					for (int32 Roll{ 0 }; Roll < NumDice; ++Roll)
					{
						int32 Value{ UKismetMathLibrary::RandomIntegerInRange(1, NumSides) };
						Verbose += STR(Value) + " + ";
						Sum += Value;
					}

					VariableValue = STR(Sum);

					Verbose.RemoveFromEnd(" + ");
					Print(Verbose + " = " + VariableValue);
				}
			}

			// 5 - Variable not found. Place the variable back.
			if (VariableValue.IsEmpty())
			{
				if (Escape.IsEmpty() || VariableName.StartsWith(SYMBOL(Reference)) || VariableName.StartsWith(SYMBOL(Option)))
					VariableValue = SYMBOL(CurlyOpen) + VariableName + SYMBOL(CurlyClose);
				else
				{
					VariableValue = Escape;
					Warning("Non-existent variable '" + VariableName + "' replaced by '" + VariableValue + "'.");
				}
			}

			// Execute variable modifier.
			if (QuillscriptSubsystem)
				if (const FVariableGetDelegate* VariableGetDelegate{ QuillscriptSubsystem->GetVariablesModifiers().Find(FName(VariableName)) })
					if (VariableGetDelegate->ExecuteIfBound(FName(VariableName), VariableValue))
						if (const FText* UpdatedVariableValue{ QuillscriptSubsystem->GetVariables().Find(FName(VariableName)) })
							VariableValue = UpdatedVariableValue->ToString();

			// Replace.
			if (VariablesNames.IsEmpty())
				ReplacedString.Append(VariableValue);
			else
				VariablesNames.Last().Append(VariableValue);
		}

		// If char is from a variable name, add it to the last variable on the list.
		else if (!VariablesNames.IsEmpty())
			VariablesNames.Last().Append(CurrentChar);

		// If char is a string letter, add it to the replaced string.
		else
			ReplacedString.Append(CurrentChar);
	}

	return ReplacedString;
}

FText UTools::ToSignedNumber(const float Number)
{
	const FString StringNumber{ FString::SanitizeFloat(Number) };

	if (Number > 0)
		return  FText::FromString("+" + StringNumber);

	return  FText::FromString(StringNumber);
}

FText UTools::ToDisplayText(const FString& String, const bool bIsBool)
{
	return FText::FromString(FName::NameToDisplayString(String, bIsBool));
}

FString UTools::UpperFirstLetter(const FString& String)
{
	return String.Mid(0, 1).ToUpper() + String.Mid(1);
}

FText UTools::TextUpperFirstLetter(const FText& Text)
{
	return FText::FromString(UpperFirstLetter(Text.ToString()));
}

FString UTools::RemoveAccentuation(FString String)
{
	// A
	String.ReplaceInline(TEXT("Á"), TEXT("A"));
	String.ReplaceInline(TEXT("À"), TEXT("A"));
	String.ReplaceInline(TEXT("Â"), TEXT("A"));
	String.ReplaceInline(TEXT("Ã"), TEXT("A"));
	String.ReplaceInline(TEXT("Ä"), TEXT("A"));
	String.ReplaceInline(TEXT("Ā"), TEXT("A"));
	String.ReplaceInline(TEXT("Å"), TEXT("A"));
	String.ReplaceInline(TEXT("á"), TEXT("a"));
	String.ReplaceInline(TEXT("à"), TEXT("a"));
	String.ReplaceInline(TEXT("â"), TEXT("a"));
	String.ReplaceInline(TEXT("ã"), TEXT("a"));
	String.ReplaceInline(TEXT("ä"), TEXT("a"));
	String.ReplaceInline(TEXT("ā"), TEXT("a"));
	String.ReplaceInline(TEXT("å"), TEXT("a"));

	String.ReplaceInline(TEXT("Æ"), TEXT("A"));
	String.ReplaceInline(TEXT("æ"), TEXT("a"));

	// E
	String.ReplaceInline(TEXT("É"), TEXT("E"));
	String.ReplaceInline(TEXT("È"), TEXT("E"));
	String.ReplaceInline(TEXT("Ê"), TEXT("E"));
	String.ReplaceInline(TEXT("Ë"), TEXT("E"));
	String.ReplaceInline(TEXT("Ē"), TEXT("E"));
	String.ReplaceInline(TEXT("é"), TEXT("e"));
	String.ReplaceInline(TEXT("è"), TEXT("e"));
	String.ReplaceInline(TEXT("ê"), TEXT("e"));
	String.ReplaceInline(TEXT("ë"), TEXT("e"));
	String.ReplaceInline(TEXT("ē"), TEXT("e"));
	String.ReplaceInline(TEXT("ë"), TEXT("e"));

	// I
	String.ReplaceInline(TEXT("Í"), TEXT("I"));
	String.ReplaceInline(TEXT("Ì"), TEXT("I"));
	String.ReplaceInline(TEXT("Î"), TEXT("I"));
	String.ReplaceInline(TEXT("Ï"), TEXT("I"));
	String.ReplaceInline(TEXT("Ī"), TEXT("I"));
	String.ReplaceInline(TEXT("í"), TEXT("i"));
	String.ReplaceInline(TEXT("ì"), TEXT("i"));
	String.ReplaceInline(TEXT("î"), TEXT("i"));
	String.ReplaceInline(TEXT("ï"), TEXT("i"));
	String.ReplaceInline(TEXT("ī"), TEXT("i"));

	// O
	String.ReplaceInline(TEXT("Ó"), TEXT("O"));
	String.ReplaceInline(TEXT("Ò"), TEXT("O"));
	String.ReplaceInline(TEXT("Ô"), TEXT("O"));
	String.ReplaceInline(TEXT("Õ"), TEXT("O"));
	String.ReplaceInline(TEXT("Ö"), TEXT("O"));
	String.ReplaceInline(TEXT("Ō"), TEXT("O"));
	String.ReplaceInline(TEXT("ó"), TEXT("o"));
	String.ReplaceInline(TEXT("ò"), TEXT("o"));
	String.ReplaceInline(TEXT("ô"), TEXT("o"));
	String.ReplaceInline(TEXT("õ"), TEXT("o"));
	String.ReplaceInline(TEXT("ö"), TEXT("o"));
	String.ReplaceInline(TEXT("ö"), TEXT("o"));
	String.ReplaceInline(TEXT("ō"), TEXT("o"));

	String.ReplaceInline(TEXT("Œ"), TEXT("O"));
	String.ReplaceInline(TEXT("œ"), TEXT("o"));

	String.ReplaceInline(TEXT("Ø"), TEXT("O"));
	String.ReplaceInline(TEXT("ø"), TEXT("o"));

	// U
	String.ReplaceInline(TEXT("Ú"), TEXT("U"));
	String.ReplaceInline(TEXT("Ù"), TEXT("U"));
	String.ReplaceInline(TEXT("Û"), TEXT("U"));
	String.ReplaceInline(TEXT("Ü"), TEXT("U"));
	String.ReplaceInline(TEXT("Ū"), TEXT("U"));
	String.ReplaceInline(TEXT("Ǖ"), TEXT("U"));
	String.ReplaceInline(TEXT("ú"), TEXT("u"));
	String.ReplaceInline(TEXT("ù"), TEXT("u"));
	String.ReplaceInline(TEXT("û"), TEXT("u"));
	String.ReplaceInline(TEXT("ü"), TEXT("u"));
	String.ReplaceInline(TEXT("ū"), TEXT("u"));
	String.ReplaceInline(TEXT("ǖ"), TEXT("u"));

	// C
	String.ReplaceInline(TEXT("Ç"), TEXT("C"));
	String.ReplaceInline(TEXT("ç"), TEXT("c"));

	// D
	String.ReplaceInline(TEXT("Ð"), TEXT("D"));
	String.ReplaceInline(TEXT("ð"), TEXT("d"));

	// N
	String.ReplaceInline(TEXT("Ñ"), TEXT("N"));
	String.ReplaceInline(TEXT("ñ"), TEXT("n"));

	// Y
	String.ReplaceInline(TEXT("Ÿ"), TEXT("Y"));
	String.ReplaceInline(TEXT("Ȳ"), TEXT("Y"));
	String.ReplaceInline(TEXT("ÿ"), TEXT("y"));
	String.ReplaceInline(TEXT("ȳ"), TEXT("y"));

	return String;
}

FString UTools::RemoveRichTextTags(FString String)
{
	FString Buffer;

	// Remove rich text close tags.
	String.ReplaceInline(TEXT("</>"), TEXT(""));

	// Remove rich text open tags.
	for (int32 I{ 0 }; I < String.Len(); ++I)
	{
		// Skip tags.
		if (String.Mid(I, 1) == "<")
		{
			while (String.Mid(I, 1) != ">")
				++I;

			++I;
		}

		// Skip delays.
		if (String.Mid(I, 2) == "((")
		{
			while (String.Mid(I, 2) != "))")
				I += 2;

			I += 2;
		}

		Buffer.Append(String.Mid(I, 1));
	}

	return Buffer;
}

FString UTools::ToHash(const FString String)
{
	FString HashString{ FString::SanitizeFloat(GetTypeHash(String)) };
	HashString.RemoveFromEnd(".0");

	return HashString;
}

FString UTools::ToHex(int64 Decimal)
{
	FString Hash;
	int32 Product{ 1 };

	while (Decimal != 0)
	{
		const int64 Remainder{ Decimal % 16 };
		char Char;

		if (Remainder >= 10)
			Char = Remainder + 55;
		else
			Char = Remainder + 48;

		Hash += Char;
		Decimal /= 16;
		Product *= 10;
	}

	return Hash.Reverse();
}

FString UTools::Encrypt(FString InputString, FString Key)
{
	// Check inputs.
	if (InputString.IsEmpty())
		return "";
	if (Key.IsEmpty())
		return "";

	// To split the correctly final result of decryption from trash symbols
	FString SplitSymbol{ "EL@$@!" };
	InputString.Append(SplitSymbol);

	// We need at least 32 symbols key
	Key = FMD5::HashAnsiString(*Key);

	uint32 Size = InputString.Len();
	Size = Size + ( FAES::AESBlockSize - Size % FAES::AESBlockSize );

	uint8* Blob{ new uint8[Size] };

	// Convert string to bytes and encrypt
	if(StringToBytes(InputString, Blob, Size)) {
		FAES::EncryptData(Blob, Size, TCHAR_TO_ANSI(Key.GetCharArray().GetData()));
		InputString = FString::FromHexBlob(Blob, Size);

		delete[] Blob;
		return InputString;
	}

	delete[] Blob;
	return "";
}

FString UTools::Decrypt(FString InputString, FString Key)
{
	// Check inputs
	if (InputString.IsEmpty())
		return "";
	if (Key.IsEmpty())
		return "";

	// To split the correctly final result of decryption from trash symbols
	const FString SplitSymbol{ "EL@$@!" };

	// We need at least 32 symbols key
	Key = FMD5::HashAnsiString(*Key);

	uint32 Size = InputString.Len();
	Size = Size + ( FAES::AESBlockSize - Size % FAES::AESBlockSize );

	uint8* Blob{ new uint8[Size] };

	// Convert string to bytes and decrypt
	if (FString::ToHexBlob(InputString, Blob, Size)) {
		FAES::DecryptData(Blob, Size, TCHAR_TO_ANSI(Key.GetCharArray().GetData()));
		InputString = BytesToString(Blob, Size);

		// Split required data from trash
		FString LeftData;
		FString RightData;
		InputString.Split(SplitSymbol, &LeftData, &RightData, ESearchCase::CaseSensitive, ESearchDir::FromStart);
		InputString = LeftData;

		delete[] Blob;
		return InputString;
	}

	delete[] Blob;
	return "";
}

bool UTools::IsKeyValuePair(const FString& Pair)
{
	return Pair.Contains(SYMBOL(Splitter));
}

void UTools::ToKeyValuePair(const FString& Pair, FString& Key, FString& Value)
{
	if (Pair.Contains(SYMBOL(Splitter)))
	{
		Pair.Split(SYMBOL(Splitter), &Key, &Value);
		return;
	}

	Key = Pair;
}

bool UTools::HasKeyValueTag(const TArray<FString>& Tags, const FString& Key, FString& Value)
{
	for (auto Tag : Tags)
	{
		if (Tag.RemoveFromStart(Key + SYMBOL(Splitter)))
		{
			Value = Tag;
			return true;
		}
	}

	return false;
}

#pragma endregion Pipes


#pragma region Operators

UObject* UTools::NullCoalescingOperator(UObject* A, UObject* B)
{
	return A ? A : B;
}

double UTools::SolveMathExpression(const FString Expression)
{
	const FBasicMathExpressionEvaluator Evaluator;
	TValueOrError Result{ Evaluator.Evaluate(*Expression, 0.0) };

	// Return value.
	if (Result.HasValue())
		return Result.GetValue();

	Warning("UTools::SolveMathExpression() -> " + Result.GetError().Text.ToString() + " [ " + Expression + " ]");
	return 0;
}

bool UTools::IsSameUniqueNetId(const FUniqueNetIdRepl& UniqueIdA, const FUniqueNetIdRepl& UniqueIdB)
{
	if (UniqueIdA.IsValid() && UniqueIdB.IsValid())
		return UniqueIdA == UniqueIdB;

	return false;
}

bool UTools::IsHost(const APlayerState* PlayerState)
{
	if (PlayerState)
		if (const TObjectPtr<APlayerController> PlayerController{ PlayerState->GetPlayerController() })
			return PlayerController->GetRemoteRole() == ROLE_SimulatedProxy;

	return false;
}

#pragma endregion Operators
