// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapsEditorSubsystem.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "Misc/PackageName.h"
#include "PackageTools.h"
#include "UObject/SavePackage.h"

bool UAMSMapsEditorSubsystem::FromRenderTargetToTexture(UTextureRenderTarget2D* renderTarget, const FString& pathToSave, const FString& textureName)
{
    if (!renderTarget) {
        return false;
    }
    const FString AssetPath = FPaths::ProjectContentDir();
    const FString PackagePath = FString("/Game/") + pathToSave + textureName;

    FString FixedPackageName;
    FString FailMessage;

    if (!FPackageName::TryConvertFilenameToLongPackageName(PackagePath, FixedPackageName, &FailMessage)) {
        return false;
    }

    if (FPackageName::DoesPackageExist(FixedPackageName)) {
        FixedPackageName += "_New";
    }

    UPackage* Package = CreatePackage(*FixedPackageName);
    Package->FullyLoad();

    UTexture2D* NewTexture = NewObject<UTexture2D>(Package, *textureName, RF_Public | RF_Standalone | RF_MarkAsRootSet);
    NewTexture->AddToRoot();

    UKismetRenderingLibrary::ConvertRenderTargetToTexture2DEditorOnly(this, renderTarget, NewTexture);

    Package->MarkPackageDirty();
    Package->FullyLoad();

    FAssetRegistryModule::AssetCreated(NewTexture);

    const FString PackageFileName = FPackageName::LongPackageNameToFilename(FixedPackageName, FPackageName::GetAssetPackageExtension());

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    return UPackage::SavePackage(Package, NewTexture, *PackageFileName, SaveArgs);
}
