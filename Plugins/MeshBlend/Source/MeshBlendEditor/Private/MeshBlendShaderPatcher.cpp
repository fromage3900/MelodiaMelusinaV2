// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendShaderPatcher.h"

#include "ISourceControlModule.h"
#include "ISourceControlProvider.h"
#include "SourceControlOperations.h"
#include "UnrealEdMisc.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/EngineVersionComparison.h"
#include "Misc/FileHelper.h"

UMeshBlendShaderPatcher::UMeshBlendShaderPatcher(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

int32 UMeshBlendShaderPatcher::GetLinesInFile(const FString& FilePath, const FString& SearchLine)
{
	const FString FullPath = GetFullShaderPath(FilePath);
	int32 LinesFound = 0;
	TArray<FString> Lines;

	if (FFileHelper::LoadFileToStringArray(Lines, *FullPath))
	{
		for (FString& Line : Lines)
		{
			if (Line.Contains(SearchLine, ESearchCase::CaseSensitive) && Line.TrimStartAndEnd().Equals(SearchLine))
			{
				LinesFound++;
			}
		}
	}

	return LinesFound;
}

bool UMeshBlendShaderPatcher::ReplaceContentInFile(const FString& FilePath, const FString& SearchLine, const FString& ReplaceLine, FString& OutErrorMessage)
{
	const FString FullPath = GetFullShaderPath(FilePath);
	TArray<FString> Lines;
	OutErrorMessage = TEXT("");

	if (!EnsureFileIsWriteable(FullPath, OutErrorMessage))
	{
		return false;
	};

	if (FFileHelper::LoadFileToStringArray(Lines, *FullPath))
	{
		int32 LinesFound = 0;

		for (FString& Line : Lines)
		{
			if (Line.Contains(SearchLine, ESearchCase::CaseSensitive) && Line.TrimStartAndEnd().Equals(SearchLine))
			{
				Line.ReplaceInline(*SearchLine, *ReplaceLine, ESearchCase::CaseSensitive);
				LinesFound++;
			}
		}

		if (LinesFound == 0)
		{
			OutErrorMessage = TEXT("Text not found in file");
			return false;
		}

		return FFileHelper::SaveStringArrayToFile(Lines, *FullPath, FFileHelper::EEncodingOptions::ForceUTF8);
	}

	OutErrorMessage = TEXT("Unknown error reading file");
	return false;
}

bool UMeshBlendShaderPatcher::EnsureFileIsWriteable(const FString& FullPath, FString& OutErrorMessage)
{
	if (!IFileManager::Get().FileExists(*FullPath))
	{
		OutErrorMessage = TEXT("File does not exist");
		return false;
	}

	if (IFileManager::Get().IsReadOnly(*FullPath))
	{
		ISourceControlProvider& Provider = ISourceControlModule::Get().GetProvider();

		if (Provider.IsEnabled())
		{
			const TSharedPtr<ISourceControlState> NewState = Provider.GetState(*FullPath, EStateCacheUsage::ForceUpdate);

			if (NewState && NewState->IsSourceControlled() && !NewState->IsCheckedOut())
			{
				if (!NewState->CanCheckout())
				{
					OutErrorMessage = FString::Printf(TEXT("File '%s' is readonly but file cannot be checked out"), *FullPath);
					return false;
				}

				TArray<FString> FilesToBeCheckedOut;
				FilesToBeCheckedOut.Add(FullPath);

				if (Provider.Execute(ISourceControlOperation::Create<FCheckOut>(), FilesToBeCheckedOut) == ECommandResult::Succeeded)
				{
					OutErrorMessage = FString::Printf(TEXT("File '%s' is readonly but file failed to be checked out"), *FullPath);
					return false;
				}
			}
		}

		if (!ensure(FPlatformFileManager::Get().GetPlatformFile().SetReadOnly(*FullPath, false)))
		{
			OutErrorMessage = TEXT("Failed to clear readonly flag on file");
			return false;
		}
	}

	return true;
}

void UMeshBlendShaderPatcher::RestartEditor()
{
	FUnrealEdMisc::Get().RestartEditor(true);
}

TArray<UShaderPatchItem*> UMeshBlendShaderPatcher::GetShaderPatchItems()
{
	TArray<UShaderPatchItem*> Result = TArray<UShaderPatchItem*>();

	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/BasePassPixelShader.usf"),
		TEXT("Fix Specular/Metalic - BasePassPixelShader"),
		TEXT("GBuffer.GBufferAO = AOMultiBounce( Luminance( GBuffer.SpecularColor ), ShadingOcclusion.SpecOcclusion ).g;"),
		TEXT("// GBuffer.GBufferAO = AOMultiBounce( Luminance( GBuffer.SpecularColor ), ShadingOcclusion.SpecOcclusion ).g;")
	));

	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/MobileBasePassPixelShader.usf"),
		TEXT("Fix Specular/Metalic - MobileBasePassPixelShader"),
		TEXT("GBuffer.GBufferAO = AOMultiBounce(Luminance(GBuffer.SpecularColor), ShadingOcclusion.SpecOcclusion).g;"),
		TEXT("// GBuffer.GBufferAO = AOMultiBounce(Luminance(GBuffer.SpecularColor), ShadingOcclusion.SpecOcclusion).g;")
	));

	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/ShadingModels.ush"),
		TEXT("Fix SubSurfaceScattering"),
		TEXT("const half BackScatter = GBuffer.GBufferAO * NormalContribution / (PI * 2);"),
		TEXT("const half BackScatter = NormalContribution / (PI * 2);")
	));

	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/ReflectionEnvironmentPixelShader.usf"),
		TEXT("Fix non-lumen lighting #1"),
		TEXT("float AO = GBuffer.GBufferAO * AmbientOcclusion;"),
		TEXT("float AO = AmbientOcclusion;")
	));

	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/SkyLightingDiffuseShared.ush"),
		TEXT("Fix non-lumen lighting #2"),
		TEXT("FSkyLightVisibilityData SkyVisData = GetSkyLightVisibilityData(SkyLightingNormal, GBuffer.WorldNormal, GBuffer.GBufferAO, AmbientOcclusion, BentNormal);"),
		TEXT("FSkyLightVisibilityData SkyVisData = GetSkyLightVisibilityData(SkyLightingNormal, GBuffer.WorldNormal, 1, AmbientOcclusion, BentNormal);")
	));

#if UE_VERSION_OLDER_THAN(5, 5, 0)
#else
	Result.Add(UShaderPatchItem::Create(
		TEXT("Private/Substrate/Substrate.ush"),
		TEXT("Fix Substrate deferred lighting"),
		TEXT("return SubstrateUnpackIrradianceAndOcclusion(HEADER_GETIRRADIANCE_AO(Header.State)).MaterialAO;"),
		TEXT("return 1.0; // return SubstrateUnpackIrradianceAndOcclusion(HEADER_GETIRRADIANCE_AO(Header.State)).MaterialAO;")
	));
#endif

	return Result;
}

bool UMeshBlendShaderPatcher::NeedsToPatchShaders()
{
	TArray<UShaderPatchItem*> ShaderPatchItems = GetShaderPatchItems();

	for (const UShaderPatchItem* Item : ShaderPatchItems)
	{
		const int32 LinesFound = GetLinesInFile(Item->FilePath, Item->ReplaceLine);

		if (LinesFound != 0)
		{
			return false;
		}
	}

	return true;
}

FString UMeshBlendShaderPatcher::GetFullShaderPath(const FString& FilePath)
{
	return FPaths::EngineDir() / "Shaders" / FilePath;
}
