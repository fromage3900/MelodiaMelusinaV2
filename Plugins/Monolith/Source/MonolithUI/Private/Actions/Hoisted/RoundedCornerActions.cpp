// Copyright tumourlove. All Rights Reserved.
#include "Actions/Hoisted/RoundedCornerActions.h"

// Monolith registry
#include "MonolithToolRegistry.h"

// JSON
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// UMG editor + runtime
#include "Blueprint/WidgetTree.h"              // UWidgetTree::FindWidget(FName)
#include "Components/Widget.h"                 // UWidget
#include "WidgetBlueprint.h"                   // UWidgetBlueprint

// Reflection
#include "UObject/Class.h"                     // UStruct::FindPropertyByName -> FProperty*
#include "UObject/UnrealType.h"                // FProperty, FStructProperty, FFloatProperty, CastField
#include "UObject/UObjectGlobals.h"            // LoadObject

// Kismet editor
#include "Kismet2/BlueprintEditorUtils.h"      // FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified
#include "Kismet2/KismetEditorUtilities.h"     // FKismetEditorUtilities::CompileBlueprint

// Math
#include "Math/Color.h"                        // FLinearColor, FColor::FromHex
#include "Math/Vector4.h"                      // FVector4 (LWC double-backed in UE 5.x)

// MonolithUI shared color parser.
#include "MonolithUICommon.h"

namespace MonolithUI::RoundedCornerInternal
{
    /**
     * Reflection-based write helper for an FVector4 UPROPERTY by name.
     * Returns true on successful write; false with OutWarning populated on absence/incompat.
     */
    static bool TryWriteVector4Property(
        UWidget* Widget,
        const FName PropName,
        const FVector4& NewValue,
        FString& OutWarning)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        if (!Prop)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' not found on widget class '%s' -- skipping"),
                *PropName.ToString(), *Widget->GetClass()->GetName());
            return false;
        }

        FStructProperty* StructProp = CastField<FStructProperty>(Prop);
        if (!StructProp || !StructProp->Struct)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' is not a struct property -- skipping"),
                *PropName.ToString());
            return false;
        }

        // FVector4 is LWC -- its UScriptStruct is "Vector4" (double-backed).
        const FName StructName = StructProp->Struct->GetFName();
        if (StructName != FName(TEXT("Vector4")))
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' has struct type '%s', expected 'Vector4' -- skipping"),
                *PropName.ToString(), *StructName.ToString());
            return false;
        }

        void* ValuePtr = StructProp->ContainerPtrToValuePtr<void>(Widget);
        StructProp->CopyCompleteValue(ValuePtr, &NewValue);
        return true;
    }

    /** Reflection-based write helper for an FLinearColor UPROPERTY by name. */
    static bool TryWriteLinearColorProperty(
        UWidget* Widget,
        const FName PropName,
        const FLinearColor& NewValue,
        FString& OutWarning)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        if (!Prop)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' not found on widget class '%s' -- skipping"),
                *PropName.ToString(), *Widget->GetClass()->GetName());
            return false;
        }

        FStructProperty* StructProp = CastField<FStructProperty>(Prop);
        if (!StructProp || !StructProp->Struct)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' is not a struct property -- skipping"),
                *PropName.ToString());
            return false;
        }

        const FName StructName = StructProp->Struct->GetFName();
        if (StructName != FName(TEXT("LinearColor")))
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' has struct type '%s', expected 'LinearColor' -- skipping"),
                *PropName.ToString(), *StructName.ToString());
            return false;
        }

        void* ValuePtr = StructProp->ContainerPtrToValuePtr<void>(Widget);
        StructProp->CopyCompleteValue(ValuePtr, &NewValue);
        return true;
    }

    /** Reflection-based write helper for a float UPROPERTY by name. */
    static bool TryWriteFloatProperty(
        UWidget* Widget,
        const FName PropName,
        const float NewValue,
        FString& OutWarning)
    {
        FProperty* Prop = Widget->GetClass()->FindPropertyByName(PropName);
        if (!Prop)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' not found on widget class '%s' -- skipping"),
                *PropName.ToString(), *Widget->GetClass()->GetName());
            return false;
        }

        FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop);
        if (!FloatProp)
        {
            OutWarning = FString::Printf(
                TEXT("Property '%s' is not a float property -- skipping"),
                *PropName.ToString());
            return false;
        }

        FloatProp->SetPropertyValue_InContainer(Widget, NewValue);
        return true;
    }
} // namespace MonolithUI::RoundedCornerInternal

FMonolithActionResult MonolithUI::FRoundedCornerActions::HandleSetRoundedCorners(const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::RoundedCornerInternal;

    if (!Params.IsValid())
    {
        return FMonolithActionResult::Error(TEXT("Missing params object"), -32602);
    }

    FString AssetPath;
    FString WidgetName;
    if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: asset_path"), -32602);
    }
    if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName) || WidgetName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: widget_name"), -32602);
    }

    const TArray<TSharedPtr<FJsonValue>>* CornerRadiiArr = nullptr;
    const bool bHasCornerRadii = Params->TryGetArrayField(TEXT("corner_radii"), CornerRadiiArr)
        && CornerRadiiArr && CornerRadiiArr->Num() >= 4;

    FString OutlineColorStr;
    const bool bHasOutlineColor = Params->TryGetStringField(TEXT("outline_color"), OutlineColorStr)
        && !OutlineColorStr.IsEmpty();

    double OutlineWidthD = 0.0;
    const bool bHasOutlineWidth = Params->TryGetNumberField(TEXT("outline_width"), OutlineWidthD);

    FString FillColorStr;
    const bool bHasFillColor = Params->TryGetStringField(TEXT("fill_color"), FillColorStr)
        && !FillColorStr.IsEmpty();

    if (!bHasCornerRadii && !bHasOutlineColor && !bHasOutlineWidth && !bHasFillColor)
    {
        return FMonolithActionResult::Error(
            TEXT("At least one of corner_radii, outline_color, outline_width, fill_color must be provided"),
            -32602);
    }

    // Pre-parse colors so we fail fast on bad input before touching the WBP.
    FLinearColor OutlineColor = FLinearColor::White;
    if (bHasOutlineColor && !MonolithUI::TryParseColor(OutlineColorStr, OutlineColor))
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Cannot parse outline_color '%s' (expected #RGB/#RRGGBB/#RRGGBBAA or 'R,G,B[,A]')"), *OutlineColorStr),
            -32602);
    }
    FLinearColor FillColor = FLinearColor::White;
    if (bHasFillColor && !MonolithUI::TryParseColor(FillColorStr, FillColor))
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Cannot parse fill_color '%s' (expected #RGB/#RRGGBB/#RRGGBBAA or 'R,G,B[,A]')"), *FillColorStr),
            -32602);
    }

    FVector4 CornerRadii(0.0, 0.0, 0.0, 0.0);
    if (bHasCornerRadii)
    {
        CornerRadii.X = (*CornerRadiiArr)[0]->AsNumber(); // TL
        CornerRadii.Y = (*CornerRadiiArr)[1]->AsNumber(); // TR
        CornerRadii.Z = (*CornerRadiiArr)[2]->AsNumber(); // BR
        CornerRadii.W = (*CornerRadiiArr)[3]->AsNumber(); // BL
    }

    bool bCompile = true;
    Params->TryGetBoolField(TEXT("compile"), bCompile);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint not found at asset_path '%s'"), *AssetPath),
            -32602);
    }

    if (!WBP->WidgetTree)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' has no WidgetTree"), *AssetPath),
            -32603);
    }

    UWidget* TargetWidget = WBP->WidgetTree->FindWidget(FName(*WidgetName));
    if (!TargetWidget)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget named '%s' not found in Widget Blueprint '%s'"),
                *WidgetName, *AssetPath),
            -32602);
    }

    // Reflection writes -- partial success is OK; we accumulate warnings for any
    // missing/incompatible properties and report which ones actually wrote.
    TArray<FString> PropertiesSet;
    TArray<FString> Warnings;
    FString Warning;

    if (bHasCornerRadii)
    {
        if (TryWriteVector4Property(TargetWidget, FName(TEXT("CornerRadii")), CornerRadii, Warning))
        {
            PropertiesSet.Add(TEXT("CornerRadii"));
        }
        else
        {
            Warnings.Add(Warning);
        }
    }
    if (bHasOutlineColor)
    {
        if (TryWriteLinearColorProperty(TargetWidget, FName(TEXT("OutlineColor")), OutlineColor, Warning))
        {
            PropertiesSet.Add(TEXT("OutlineColor"));
        }
        else
        {
            Warnings.Add(Warning);
        }
    }
    if (bHasOutlineWidth)
    {
        if (TryWriteFloatProperty(TargetWidget, FName(TEXT("OutlineWidth")), (float)OutlineWidthD, Warning))
        {
            PropertiesSet.Add(TEXT("OutlineWidth"));
        }
        else
        {
            Warnings.Add(Warning);
        }
    }
    if (bHasFillColor)
    {
        if (TryWriteLinearColorProperty(TargetWidget, FName(TEXT("FillColor")), FillColor, Warning))
        {
            PropertiesSet.Add(TEXT("FillColor"));
        }
        else
        {
            Warnings.Add(Warning);
        }
    }

    if (PropertiesSet.Num() == 0)
    {
        FString Combined = FString::Join(Warnings, TEXT("; "));
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("No properties written on widget '%s' of class '%s': %s"),
                *WidgetName, *TargetWidget->GetClass()->GetName(), *Combined),
            -32603);
    }

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
    if (bCompile)
    {
        FKismetEditorUtilities::CompileBlueprint(WBP);
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("widget_name"), WidgetName);
    {
        TArray<TSharedPtr<FJsonValue>> Arr;
        for (const FString& P : PropertiesSet)
        {
            Arr.Add(MakeShared<FJsonValueString>(P));
        }
        Result->SetArrayField(TEXT("properties_set"), Arr);
    }
    if (Warnings.Num() > 0)
    {
        TArray<TSharedPtr<FJsonValue>> Arr;
        for (const FString& W : Warnings)
        {
            Arr.Add(MakeShared<FJsonValueString>(W));
        }
        Result->SetArrayField(TEXT("warnings"), Arr);
    }
    Result->SetBoolField(TEXT("compiled"), bCompile);
    return FMonolithActionResult::Success(Result);
}

void MonolithUI::FRoundedCornerActions::Register(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("set_rounded_corners"),
        TEXT("Reflection-based writer for CornerRadii / OutlineColor / OutlineWidth / FillColor "
             "UPROPERTY fields on a named widget inside a Widget Blueprint. Works on any widget "
             "exposing compatible UPROPERTY names. "
             "Params: asset_path (string, required), widget_name (string, required), "
             "corner_radii (array [TL,TR,BR,BL], optional), outline_color (hex or 'R,G,B[,A]', optional), "
             "outline_width (number, optional), fill_color (hex or 'R,G,B[,A]', optional), "
             "compile (bool, optional, default true). At least one optional field is required."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FRoundedCornerActions::HandleSetRoundedCorners));
}
