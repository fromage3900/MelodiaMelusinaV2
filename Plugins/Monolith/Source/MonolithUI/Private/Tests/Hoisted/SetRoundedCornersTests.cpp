// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

// Core / test
#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

// JSON / registry
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "MonolithToolRegistry.h"

// UMG -- shared test fixture
#include "Tests/Hoisted/MonolithUITestFixtureUtils.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Widget.h"

// Reflection -- the action is reflection-only and so is the readback path.
#include "UObject/Class.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UnrealType.h"
#include "UObject/UObjectGlobals.h"

// Math
#include "Math/Color.h"
#include "Math/Vector4.h"

/**
 * MonolithUI.SetRoundedCorners.Basic
 *
 * Architectural invariant under test: the action is reflection-only and has NO
 * compile-time dep on URoundedBorder.
 *
 * The TEST exercises that action against a real URoundedBorder widget when an
 * optional provider is loaded; if the class isn't found the test SKIPS
 * (returns true with a warning) rather than failing -- provider absence is a
 * valid deployment and must not regress the build.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUISetRoundedCornersBasicTest,
    "MonolithUI.SetRoundedCorners.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace MonolithUI::SetRoundedCornersTests
{
    static constexpr const TCHAR* GTestWidgetName = TEXT("TestBorder");

    static UClass* FindLoadedWidgetClassByName(FName ClassName)
    {
        for (TObjectIterator<UClass> It; It; ++It)
        {
            UClass* Candidate = *It;
            if (Candidate
                && Candidate->GetFName() == ClassName
                && Candidate->IsChildOf(UWidget::StaticClass()))
            {
                return Candidate;
            }
        }

        return nullptr;
    }

    /** Read an FVector4 UPROPERTY by name via reflection. Returns false if absent/incompatible. */
    static bool ReadVector4Property(UWidget* Widget, FName PropName, FVector4& OutValue)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        FStructProperty* StructProp = CastField<FStructProperty>(Prop);
        if (!StructProp || !StructProp->Struct
            || StructProp->Struct->GetFName() != FName(TEXT("Vector4")))
        {
            return false;
        }
        const void* ValuePtr = StructProp->ContainerPtrToValuePtr<void>(Widget);
        FMemory::Memcpy(&OutValue, ValuePtr, sizeof(FVector4));
        return true;
    }

    /** Read an FLinearColor UPROPERTY by name via reflection. Returns false if absent/incompatible. */
    static bool ReadLinearColorProperty(UWidget* Widget, FName PropName, FLinearColor& OutValue)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        FStructProperty* StructProp = CastField<FStructProperty>(Prop);
        if (!StructProp || !StructProp->Struct
            || StructProp->Struct->GetFName() != FName(TEXT("LinearColor")))
        {
            return false;
        }
        const void* ValuePtr = StructProp->ContainerPtrToValuePtr<void>(Widget);
        FMemory::Memcpy(&OutValue, ValuePtr, sizeof(FLinearColor));
        return true;
    }

    /** Read a float UPROPERTY by name via reflection. Returns false if absent/incompatible. */
    static bool ReadFloatProperty(UWidget* Widget, FName PropName, float& OutValue)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop);
        if (!FloatProp)
        {
            return false;
        }
        OutValue = FloatProp->GetPropertyValue_InContainer(Widget);
        return true;
    }
}

bool FMonolithUISetRoundedCornersBasicTest::RunTest(const FString& Parameters)
{
    using namespace MonolithUI::SetRoundedCornersTests;

    UClass* RoundedBorderClass = FindLoadedWidgetClassByName(FName(TEXT("RoundedBorder")));
    if (!RoundedBorderClass)
    {
        AddWarning(TEXT("Skipping: URoundedBorder class not found (optional provider not loaded)."));
        return true;
    }

    const FString TestWBPPath = TEXT("/Game/Tests/Monolith/UI/WBP_SetRoundedCornersTest");

    FString FixtureError;
    if (!MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint(
        TestWBPPath, FName(GTestWidgetName), RoundedBorderClass, FixtureError))
    {
        AddError(FString::Printf(TEXT("Failed to build test fixture WBP: %s"), *FixtureError));
        return false;
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), TestWBPPath);
    Params->SetStringField(TEXT("widget_name"), GTestWidgetName);
    {
        TArray<TSharedPtr<FJsonValue>> Radii;
        Radii.Add(MakeShared<FJsonValueNumber>(8.0));   // TL
        Radii.Add(MakeShared<FJsonValueNumber>(12.0));  // TR
        Radii.Add(MakeShared<FJsonValueNumber>(16.0));  // BR
        Radii.Add(MakeShared<FJsonValueNumber>(20.0));  // BL
        Params->SetArrayField(TEXT("corner_radii"), Radii);
    }
    Params->SetStringField(TEXT("outline_color"), TEXT("#FF0000FF")); // opaque red
    Params->SetNumberField(TEXT("outline_width"), 3.5);
    Params->SetStringField(TEXT("fill_color"), TEXT("#40404080"));    // ~25% alpha gray
    Params->SetBoolField(TEXT("compile"), true);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("set_rounded_corners"), Params);

    TestTrue(TEXT("set_rounded_corners bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    if (Result.Result.IsValid())
    {
        const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
        if (Result.Result->TryGetArrayField(TEXT("properties_set"), Arr) && Arr)
        {
            TestEqual(TEXT("properties_set count"), Arr->Num(), 4);
        }
        else
        {
            AddError(TEXT("Result payload missing 'properties_set' array"));
        }
    }
    else
    {
        AddError(TEXT("Result payload was null on success"));
    }

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *TestWBPPath);
    if (!WBP || !WBP->WidgetTree)
    {
        AddError(TEXT("Failed to reload test WBP for read-back"));
        return false;
    }
    UWidget* TestWidget = WBP->WidgetTree->FindWidget(FName(GTestWidgetName));
    if (!TestWidget)
    {
        AddError(TEXT("TestBorder not found after write"));
        return false;
    }

    FVector4 RadiiRead(0, 0, 0, 0);
    TestTrue(TEXT("Read CornerRadii"), ReadVector4Property(TestWidget, FName(TEXT("CornerRadii")), RadiiRead));
    TestEqual(TEXT("CornerRadii.X (TL)"), RadiiRead.X, 8.0);
    TestEqual(TEXT("CornerRadii.Y (TR)"), RadiiRead.Y, 12.0);
    TestEqual(TEXT("CornerRadii.Z (BR)"), RadiiRead.Z, 16.0);
    TestEqual(TEXT("CornerRadii.W (BL)"), RadiiRead.W, 20.0);

    FLinearColor OutlineRead = FLinearColor::Transparent;
    TestTrue(TEXT("Read OutlineColor"), ReadLinearColorProperty(TestWidget, FName(TEXT("OutlineColor")), OutlineRead));
    TestTrue(TEXT("OutlineColor is red-dominant"), OutlineRead.R > OutlineRead.G && OutlineRead.R > OutlineRead.B);
    TestEqual(TEXT("OutlineColor.A opaque"), OutlineRead.A, 1.0f);

    float WidthRead = 0.0f;
    TestTrue(TEXT("Read OutlineWidth"), ReadFloatProperty(TestWidget, FName(TEXT("OutlineWidth")), WidthRead));
    TestEqual(TEXT("OutlineWidth"), WidthRead, 3.5f);

    FLinearColor FillRead = FLinearColor::Transparent;
    TestTrue(TEXT("Read FillColor"), ReadLinearColorProperty(TestWidget, FName(TEXT("FillColor")), FillRead));
    TestTrue(TEXT("FillColor is gray (R == G == B)"), FMath::IsNearlyEqual(FillRead.R, FillRead.G) && FMath::IsNearlyEqual(FillRead.G, FillRead.B));
    TestTrue(TEXT("FillColor alpha is ~0.5"), FMath::IsNearlyEqual(FillRead.A, 128.0f / 255.0f, 0.01f));

    return true;
}

/**
 * MonolithUI.SetRoundedCorners.InvalidParams
 *
 * Validates the -32602 error path. No fixture needed.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUISetRoundedCornersInvalidParamsTest,
    "MonolithUI.SetRoundedCorners.InvalidParams",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUISetRoundedCornersInvalidParamsTest::RunTest(const FString& Parameters)
{
    {
        TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
        const FMonolithActionResult R = FMonolithToolRegistry::Get().ExecuteAction(
            TEXT("ui"), TEXT("set_rounded_corners"), P);
        TestFalse(TEXT("missing asset_path -> failure"), R.bSuccess);
        TestEqual(TEXT("missing asset_path -> -32602"), R.ErrorCode, -32602);
    }

    {
        TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
        P->SetStringField(TEXT("asset_path"), TEXT("/Game/Foo/Bar"));
        const FMonolithActionResult R = FMonolithToolRegistry::Get().ExecuteAction(
            TEXT("ui"), TEXT("set_rounded_corners"), P);
        TestFalse(TEXT("missing widget_name -> failure"), R.bSuccess);
        TestEqual(TEXT("missing widget_name -> -32602"), R.ErrorCode, -32602);
    }

    {
        TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
        P->SetStringField(TEXT("asset_path"), TEXT("/Game/Foo/Bar"));
        P->SetStringField(TEXT("widget_name"), TEXT("Anything"));
        const FMonolithActionResult R = FMonolithToolRegistry::Get().ExecuteAction(
            TEXT("ui"), TEXT("set_rounded_corners"), P);
        TestFalse(TEXT("no optional fields -> failure"), R.bSuccess);
        TestEqual(TEXT("no optional fields -> -32602"), R.ErrorCode, -32602);
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
