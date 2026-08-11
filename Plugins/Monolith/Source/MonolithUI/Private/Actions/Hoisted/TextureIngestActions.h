// Copyright tumourlove. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * MonolithUI -- texture ingest action.
 *
 * Decodes a base64-encoded compressed image (PNG / JPEG / BMP / EXR / TGA /
 * HDR / TIFF / DDS) and imports it as a UTexture2D asset at a /Game/... path.
 * Mirrors the editor-import flow used elsewhere in MonolithUI: NewObject +
 * AssetRegistry::AssetCreated + SavePackage with CreateUniqueAssetName for
 * collision-safe naming.
 *
 * Editor-only -- FTextureSource is WITH_EDITOR-gated.
 */
namespace MonolithUI
{
    struct FTextureIngestActions
    {
        static void Register(FMonolithToolRegistry& Registry);

        static FMonolithActionResult HandleImportTextureFromBytes(const TSharedPtr<FJsonObject>& Params);
    };
}
