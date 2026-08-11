// Copyright tumourlove. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * MonolithUI -- font family ingest action.
 *
 * Reads one-or-more TTF files from disk and imports them as a UFont composite
 * asset plus one UFontFace per typeface entry. Mirrors the editor-import flow
 * used by the texture ingest action with UE 5.7-specific deprecation handling
 * for UFont::CompositeFont (public field is UE_DEPRECATED(5.7); the canonical
 * write path is GetMutableInternalCompositeFont()).
 *
 * Editor-only -- UFontFace::InitializeFromBulkData + font-asset save-to-disk
 * are WITH_EDITORONLY_DATA gated; this module is editor-scoped so no extra
 * macro fencing is required.
 */
namespace MonolithUI
{
    struct FFontIngestActions
    {
        static void Register(FMonolithToolRegistry& Registry);

        static FMonolithActionResult HandleImportFontFamily(const TSharedPtr<FJsonObject>& Params);
    };
}
