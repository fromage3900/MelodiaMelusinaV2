// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

// Core / test
#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

// JSON / registry
#include "Dom/JsonObject.h"
#include "MonolithToolRegistry.h"

// Texture verification
#include "Engine/Texture2D.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"

/**
 * MonolithUI.ImportTextureFromBytes.BasicPNG
 *
 * Dispatches `ui.import_texture_from_bytes` through the Monolith registry with
 * a 2x2 red PNG (base64). Asserts:
 *  - Action succeeds
 *  - Result payload exposes asset_path / width / height
 *  - Width/Height match the PNG header (2x2)
 *  - The UTexture2D actually materialises in-memory at the reported path
 *
 * Uses save=false so the test does not pollute /Content/ on disk.
 *
 * Test fixture path: /Game/Tests/Monolith/UI/Textures/T_ImportBytesTest
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIImportTextureFromBytesBasicTest,
    "MonolithUI.ImportTextureFromBytes.BasicPNG",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIImportTextureFromBytesBasicTest::RunTest(const FString& Parameters)
{
    // 2x2 red PNG, base64-encoded.
    const FString RedPngB64 = TEXT(
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFUlEQVR4nGP8z8Dwn4GB"
        "gYEJRIAwAB8XAgICR7MUAAAAAElFTkSuQmCC");

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("destination"),
        TEXT("/Game/Tests/Monolith/UI/Textures/T_ImportBytesTest"));
    Params->SetStringField(TEXT("bytes_b64"), RedPngB64);
    Params->SetStringField(TEXT("format_hint"), TEXT("png"));
    Params->SetBoolField(TEXT("save"), false);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("import_texture_from_bytes"), Params);

    TestTrue(TEXT("import_texture_from_bytes bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"),
            *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    if (!Result.Result.IsValid())
    {
        AddError(TEXT("Result payload was null on success"));
        return false;
    }

    FString AssetPath;
    TestTrue(TEXT("asset_path in result"),
        Result.Result->TryGetStringField(TEXT("asset_path"), AssetPath));

    double W = 0.0, H = 0.0, SizeBytes = 0.0;
    Result.Result->TryGetNumberField(TEXT("width"), W);
    Result.Result->TryGetNumberField(TEXT("height"), H);
    Result.Result->TryGetNumberField(TEXT("size_bytes"), SizeBytes);
    TestEqual(TEXT("width 2"), (int32)W, 2);
    TestEqual(TEXT("height 2"), (int32)H, 2);
    TestEqual(TEXT("size_bytes 2*2*4=16"), (int32)SizeBytes, 16);

    if (!AssetPath.IsEmpty())
    {
        FString AssetName;
        {
            int32 SlashIdx = INDEX_NONE;
            if (AssetPath.FindLastChar(TEXT('/'), SlashIdx))
            {
                AssetName = AssetPath.Mid(SlashIdx + 1);
            }
        }
        const FString DottedPath = AssetPath + TEXT(".") + AssetName;

        UTexture2D* Tex = FindObject<UTexture2D>(nullptr, *DottedPath);
        if (!Tex)
        {
            Tex = LoadObject<UTexture2D>(nullptr, *DottedPath);
        }
        TestNotNull(TEXT("UTexture2D exists at returned asset_path"), Tex);
        if (Tex)
        {
            // GetSizeX/Y return LODGroup-mutated platform-data size; assert on
            // Source.GetSizeX/Y instead so TEXTUREGROUP_UI's MinLODSize=32
            // doesn't pad the 2x2 source up to 32x32 at build time.
#if WITH_EDITOR
            TestEqual(TEXT("Tex->Source SizeX == 2"), Tex->Source.GetSizeX(), (int64)2);
            TestEqual(TEXT("Tex->Source SizeY == 2"), Tex->Source.GetSizeY(), (int64)2);
#endif
        }
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
