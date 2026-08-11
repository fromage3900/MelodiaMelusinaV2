// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendEditor.h"

#include "Editor.h"
#include "EditorToolbar.h"
#include "EditorUtilitySubsystem.h"
#include "EditorUtilityWidgetBlueprint.h"
#include "MeshBlendActivator.h"
#include "MeshBlendEditorBPUtils.h"
#include "MeshBlendLevelProcessor.h"
#include "MeshBlendProcessor.h"
#include "MeshBlendShaderPatcher.h"
#include "MeshBlendSubSystem.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Interfaces/IPluginManager.h"
#include "Logging/MessageLog.h"
#include "Misc/Paths.h"
#include "Styling/SlateStyleRegistry.h"
#include "UObject/ObjectSaveContext.h"

#define LOCTEXT_NAMESPACE "FMeshBlendEditorModule"

const FString PluginName = FString(TEXT("MeshBlend"));

FString InPluginContent(const FString& RelativePath, const ANSICHAR* Extension)
{
	static FString ContentDir = IPluginManager::Get().FindPlugin(PluginName)->GetContentDir();
	return (ContentDir / RelativePath) + Extension;
}

#define IMAGE_PLUGIN_BRUSH( RelativePath, ... ) FSlateImageBrush( InPluginContent( RelativePath, ".png" ), __VA_ARGS__ )

TSharedPtr<FSlateStyleSet> FMeshBlendEditorModule::StyleSet;

TSharedPtr<ISlateStyle> FMeshBlendEditorModule::GetStyleSet()
{
	return StyleSet;
}

void FMeshBlendEditorModule::TryResetMeshActivator()
{
	CheckShaderPatchStatus();
	UMeshBlendEditorBPUtils::TryResetMeshActivator();
}

void FMeshBlendEditorModule::StartupModule()
{
	OnPreSaveWorldHandle = FEditorDelegates::PreSaveWorldWithContext.AddRaw(this, &FMeshBlendEditorModule::OnPreSaveWorld);
	OnEndPIEHandle = FEditorDelegates::EndPIE.AddRaw(this, &FMeshBlendEditorModule::OnEndPIE);

	FEditorToolbar::Startup(this);

	StyleSet = MakeShared<FSlateStyleSet>(FName("MeshBlendStyle"));
	const FVector2D Icon_40(40.0f, 40.0f);
	StyleSet->SetContentRoot(FPaths::EngineContentDir() / TEXT("Editor/Slate"));
	StyleSet->SetCoreContentRoot(FPaths::EngineContentDir() / TEXT("Slate"));
	StyleSet->Set("MeshBlend.Icon", new IMAGE_PLUGIN_BRUSH(TEXT("MeshBlend_40x"), Icon_40));
	FSlateStyleRegistry::RegisterSlateStyle(*StyleSet.Get());
}

void FMeshBlendEditorModule::ShutdownModule()
{
	if (OnPreSaveWorldHandle.IsValid())
	{
		FEditorDelegates::PreSaveWorldWithContext.Remove(OnPreSaveWorldHandle);
	}

	if (OnEndPIEHandle.IsValid())
	{
		FEditorDelegates::EndPIE.Remove(OnEndPIEHandle);
	}

	FEditorToolbar::Shutdown(this);
}

void FMeshBlendEditorModule::OnPreSaveWorld(UWorld* World, FObjectPreSaveContext ObjectPreSaveContext)
{
	if (!ObjectPreSaveContext.IsCooking())
	{
		return;
	}

	if (Processor == nullptr)
	{
		// We create a global processor so that World Partition chunks gets the same bucket values
		Processor = NewObject<UMeshBlendProcessor>();
		Processor->AddToRoot();
	}

	ULevel* Level = World->GetCurrentLevel();
	FMeshBlendLevelProcessor::Transform(Level, Processor, false);
}

void FMeshBlendEditorModule::OnEndPIE(bool bArg)
{
	CheckShaderPatchStatus();
}

void FMeshBlendEditorModule::CheckShaderPatchStatus()
{
	if (!FApp::IsEngineInstalled())
	{
		// Only check shader patch status if the engine is a launcher version installed with the Epic Games Launcher.
		return;
	}

	static const auto CVarMaterialAO = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.CustomerGBufferChannel"));

	if (CVarMaterialAO && CVarMaterialAO->GetInt() == 1)
	{
		return;
	}

	if (!UMeshBlendShaderPatcher::NeedsToPatchShaders())
	{
		return;
	}

	FMessageLog("MapCheck").Warning()
	                       ->AddToken(FTextToken::Create(LOCTEXT("MapCheck_SetShaderPatcher",
	                                                             "Engine shader files are not patched for MeshBlend.")))
	                       ->AddToken(FActionToken::Create(LOCTEXT("MapCheck_FixShaderPatcher", "Open MeshBlend Shader Patcher"),
	                                                       LOCTEXT("MapCheck_FixShaderPatcher_Desc", "Click to open the MeshBlend Shader Patcher."),
	                                                       FOnActionTokenExecuted::CreateStatic(FMeshBlendEditorModule::ShowShaderPatcher),
	                                                       true));
	FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
}

void FMeshBlendEditorModule::ShowShaderPatcher()
{
	const FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(FName("AssetRegistry"));
	const IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();

	UEditorUtilitySubsystem* EditorUtilitySubsystem = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
	const FAssetData AssetData = AssetRegistry.GetAssetByObjectPath(FSoftObjectPath(TEXT("/MeshBlend/Editor/ShaderPatcher.ShaderPatcher")));

	if (!AssetData.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("MeshBlend: ShaderPatcher asset not found!"));
		return;
	}

	UObject* Asset = AssetData.GetAsset();

	if (UEditorUtilityWidgetBlueprint* EditorUtilityWidgetBlueprint = Cast<UEditorUtilityWidgetBlueprint>(Asset))
	{
		EditorUtilitySubsystem->SpawnAndRegisterTab(EditorUtilityWidgetBlueprint);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("MeshBlend: ShaderPatcher asset is not a valid UEditorUtilityWidgetBlueprint!"));
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMeshBlendEditorModule, MeshBlendEditor)
