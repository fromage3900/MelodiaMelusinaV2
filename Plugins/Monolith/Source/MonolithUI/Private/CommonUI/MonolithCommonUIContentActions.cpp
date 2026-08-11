// Category F: Numeric, Rotator, Lazy, LoadGuard — 4 actions
// 4.F.1 configure_numeric_text
// 4.F.2 configure_rotator
// 4.F.3 create_lazy_image
// 4.F.4 create_load_guard
#include "MonolithCommonUIHelpers.h"

#if WITH_COMMONUI

#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "CommonNumericTextBlock.h"
#include "CommonRotator.h"
#include "CommonLazyImage.h"
#include "CommonLoadGuard.h"

#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/PanelWidget.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

namespace MonolithCommonUIContent
{
	// ----- 4.F.1 configure_numeric_text ----------------------------------------

	static FMonolithActionResult HandleConfigureNumericText(const TSharedPtr<FJsonObject>& Params)
	{
		FString WidgetName;
		if (!Params.IsValid() ||
			!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
			return FMonolithActionResult::Error(TEXT("wbp_path and widget_name required"));
		FString WbpPath = MonolithCommonUI::GetWbpPath(Params);
		if (WbpPath.IsEmpty())
			return FMonolithActionResult::Error(TEXT("wbp_path (or asset_path) required"));

		UWidgetBlueprint* Wbp = nullptr;
		UWidget* Target = nullptr;
		FMonolithActionResult Loaded = MonolithCommonUI::LoadWidgetForMutation(WbpPath, FName(*WidgetName), Wbp, Target);
		if (!Loaded.bSuccess) return Loaded;

		UCommonNumericTextBlock* N = Cast<UCommonNumericTextBlock>(Target);
		if (!N) return FMonolithActionResult::Error(TEXT("target is not a UCommonNumericTextBlock"));

		TArray<FString> Applied;

		FString NumericTypeStr;
		if (Params->TryGetStringField(TEXT("numeric_type"), NumericTypeStr))
		{
			if (FEnumProperty* P = FindFProperty<FEnumProperty>(UCommonNumericTextBlock::StaticClass(), TEXT("NumericType")))
			{
				P->ImportText_Direct(*NumericTypeStr, P->ContainerPtrToValuePtr<void>(N), nullptr, PPF_None);
				Applied.Add(TEXT("numeric_type"));
			}
		}

		double CurrentVal;
		if (Params->TryGetNumberField(TEXT("current_value"), CurrentVal))
		{
			N->SetCurrentValue(static_cast<float>(CurrentVal));
			Applied.Add(TEXT("current_value"));
		}

		FString FormatSpecText;
		if (Params->TryGetStringField(TEXT("formatting_specification"), FormatSpecText))
		{
			if (FStructProperty* P = FindFProperty<FStructProperty>(UCommonNumericTextBlock::StaticClass(), TEXT("FormattingSpecification")))
			{
				P->ImportText_Direct(*FormatSpecText, P->ContainerPtrToValuePtr<void>(N), nullptr, PPF_None);
				Applied.Add(TEXT("formatting_specification"));
			}
		}

		double EaseExp;
		if (Params->TryGetNumberField(TEXT("ease_out_exponent"), EaseExp))
		{
			if (FFloatProperty* P = FindFProperty<FFloatProperty>(UCommonNumericTextBlock::StaticClass(), TEXT("EaseOutInterpolationExponent")))
			{
				P->SetPropertyValue_InContainer(N, static_cast<float>(EaseExp));
				Applied.Add(TEXT("ease_out_exponent"));
			}
		}

		double ShrinkDuration;
		if (Params->TryGetNumberField(TEXT("post_interpolation_shrink_duration"), ShrinkDuration))
		{
			if (FFloatProperty* P = FindFProperty<FFloatProperty>(UCommonNumericTextBlock::StaticClass(), TEXT("PostInterpolationShrinkDuration")))
			{
				P->SetPropertyValue_InContainer(N, static_cast<float>(ShrinkDuration));
				Applied.Add(TEXT("post_interpolation_shrink_duration"));
			}
		}

		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Wbp);
		FKismetEditorUtilities::CompileBlueprint(Wbp);
		Wbp->GetOutermost()->MarkPackageDirty();

		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("wbp_path"), WbpPath);
		Result->SetStringField(TEXT("widget_name"), WidgetName);
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FString& A : Applied) Arr.Add(MakeShared<FJsonValueString>(A));
		Result->SetArrayField(TEXT("applied"), Arr);
		return FMonolithActionResult::Success(Result);
	}

	// ----- 4.F.2 configure_rotator ---------------------------------------------

	static FMonolithActionResult HandleConfigureRotator(const TSharedPtr<FJsonObject>& Params)
	{
		FString WidgetName;
		if (!Params.IsValid() ||
			!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
			return FMonolithActionResult::Error(TEXT("wbp_path and widget_name required"));
		FString WbpPath = MonolithCommonUI::GetWbpPath(Params);
		if (WbpPath.IsEmpty())
			return FMonolithActionResult::Error(TEXT("wbp_path (or asset_path) required"));

		UWidgetBlueprint* Wbp = nullptr;
		UWidget* Target = nullptr;
		FMonolithActionResult Loaded = MonolithCommonUI::LoadWidgetForMutation(WbpPath, FName(*WidgetName), Wbp, Target);
		if (!Loaded.bSuccess) return Loaded;

		UCommonRotator* R = Cast<UCommonRotator>(Target);
		if (!R) return FMonolithActionResult::Error(TEXT("target is not a UCommonRotator"));

		const TArray<TSharedPtr<FJsonValue>>* LabelsArr = nullptr;
		TArray<FText> Labels;
		if (Params->TryGetArrayField(TEXT("labels"), LabelsArr))
		{
			for (const TSharedPtr<FJsonValue>& V : *LabelsArr)
			{
				FString S;
				if (V->TryGetString(S)) Labels.Add(FText::FromString(S));
			}
		}

		// TextLabels and SelectedIndex are non-UPROPERTY protected members of
		// UCommonRotator, so reflection (FindFProperty) cannot reach them.
		// The runtime methods PopulateTextLabels() and SetSelectedItem() fire
		// BlueprintImplementableEvents and touch BindWidget children (MyText)
		// that may be null or partially initialized on the design-time template.
		// Calling them and then MarkBlueprintAsStructurallyModified() causes a
		// null-deref crash inside CommonUI during widget reconstruction.
		//
		// Safe approach: access the raw members through a layout-compatible
		// accessor derived from UCommonRotator.  The two fields sit at the tail
		// of the class and their layout has been stable across CommonUI's
		// lifetime.  We set them directly, bypassing BP events and MyText access,
		// then use the non-structural MarkBlueprintAsModified (no reconstruction).

		struct FCommonRotatorAccessor : public UCommonRotator
		{
			static void SetTextLabelsRaw(UCommonRotator* Target, const TArray<FText>& InLabels)
			{
				static_cast<FCommonRotatorAccessor*>(Target)->TextLabels = InLabels;
			}
			static void SetSelectedIndexRaw(UCommonRotator* Target, int32 InIndex)
			{
				static_cast<FCommonRotatorAccessor*>(Target)->SelectedIndex = InIndex;
			}
		};

		if (Labels.Num() > 0)
		{
			FCommonRotatorAccessor::SetTextLabelsRaw(R, Labels);
			// Reset selected index to 0 (matches PopulateTextLabels behavior)
			FCommonRotatorAccessor::SetSelectedIndexRaw(R, 0);
		}

		int32 Selected;
		if (Params->TryGetNumberField(TEXT("selected_index"), Selected))
		{
			FCommonRotatorAccessor::SetSelectedIndexRaw(R, Selected);
		}

		// Non-structural modification: we only changed data fields, not the
		// widget tree structure.  MarkBlueprintAsStructurallyModified would
		// trigger full widget reconstruction and crash on the partially-
		// initialized template.  MarkBlueprintAsModified just marks dirty.
		FBlueprintEditorUtils::MarkBlueprintAsModified(Wbp);
		Wbp->GetOutermost()->MarkPackageDirty();

		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("wbp_path"), WbpPath);
		Result->SetStringField(TEXT("widget_name"), WidgetName);
		Result->SetNumberField(TEXT("labels_set"), Labels.Num());
		return FMonolithActionResult::Success(Result);
	}

	// ----- Shared: add a widget to an existing WBP tree ------------------------

	static FMonolithActionResult AddWidgetToWbp(UClass* Cls, const TSharedPtr<FJsonObject>& Params)
	{
		FString WidgetName, ParentName;
		if (!Params.IsValid() ||
			!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
			return FMonolithActionResult::Error(TEXT("wbp_path and widget_name required"));
		FString WbpPath = MonolithCommonUI::GetWbpPath(Params);
		if (WbpPath.IsEmpty())
			return FMonolithActionResult::Error(TEXT("wbp_path (or asset_path) required"));
		Params->TryGetStringField(TEXT("parent_widget"), ParentName);

		UWidgetBlueprint* Wbp = LoadObject<UWidgetBlueprint>(nullptr, *WbpPath);
		if (!Wbp || !Wbp->WidgetTree)
			return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load WBP '%s'"), *WbpPath));

		UPanelWidget* Parent = nullptr;
		if (ParentName.IsEmpty())
			Parent = Cast<UPanelWidget>(Wbp->WidgetTree->RootWidget);
		else
		{
			Wbp->WidgetTree->ForEachWidget([&](UWidget* W)
			{
				if (!Parent && W && W->GetFName() == FName(*ParentName))
					Parent = Cast<UPanelWidget>(W);
			});
		}
		if (!Parent) return FMonolithActionResult::Error(TEXT("parent panel not found"));

		UWidget* New = Wbp->WidgetTree->ConstructWidget<UWidget>(Cls, FName(*WidgetName));
		Parent->AddChild(New);

		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Wbp);
		FKismetEditorUtilities::CompileBlueprint(Wbp);
		Wbp->GetOutermost()->MarkPackageDirty();

		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("wbp_path"), WbpPath);
		Result->SetStringField(TEXT("widget_name"), WidgetName);
		Result->SetStringField(TEXT("widget_class"), Cls->GetName());
		return FMonolithActionResult::Success(Result);
	}

	// ----- 4.F.3 create_lazy_image ---------------------------------------------

	static FMonolithActionResult HandleCreateLazyImage(const TSharedPtr<FJsonObject>& Params)
	{
		return AddWidgetToWbp(UCommonLazyImage::StaticClass(), Params);
	}

	// ----- 4.F.4 create_load_guard ---------------------------------------------

	static FMonolithActionResult HandleCreateLoadGuard(const TSharedPtr<FJsonObject>& Params)
	{
		return AddWidgetToWbp(UCommonLoadGuard::StaticClass(), Params);
	}

	// ----- Registration --------------------------------------------------------

	void Register(FMonolithToolRegistry& Registry)
	{
		const FString Cat(TEXT("CommonUI"));

		Registry.RegisterAction(
			TEXT("ui"), TEXT("configure_numeric_text"),
			TEXT("Configure UCommonNumericTextBlock: numeric type, current value, formatting, interpolation"),
			FMonolithActionHandler::CreateStatic(&HandleConfigureNumericText),
			FParamSchemaBuilder()
				.RequiredAssetPath(TEXT("wbp_path"), TEXT("Widget Blueprint path"))
				.Required(TEXT("widget_name"), TEXT("string"), TEXT("Name of UCommonNumericTextBlock"))
				.Optional(TEXT("numeric_type"), TEXT("string"), TEXT("ECommonNumericType: Number|Percentage|Seconds|Distance"))
				.Optional(TEXT("current_value"), TEXT("number"), TEXT("Initial value"))
				.Optional(TEXT("formatting_specification"), TEXT("string"), TEXT("FCommonNumberFormattingOptions text"))
				.Optional(TEXT("ease_out_exponent"), TEXT("number"), TEXT("Interpolation easing exponent"))
				.Optional(TEXT("post_interpolation_shrink_duration"), TEXT("number"), TEXT("Shrink animation duration after interpolation"))
				.Build(),
			Cat);

		Registry.RegisterAction(
			TEXT("ui"), TEXT("configure_rotator"),
			TEXT("Configure UCommonRotator: populate labels, set selected index"),
			FMonolithActionHandler::CreateStatic(&HandleConfigureRotator),
			FParamSchemaBuilder()
				.RequiredAssetPath(TEXT("wbp_path"), TEXT("Widget Blueprint path"))
				.Required(TEXT("widget_name"), TEXT("string"), TEXT("Name of UCommonRotator"))
				.Optional(TEXT("labels"), TEXT("array"), TEXT("Array of text labels to populate"))
				.Optional(TEXT("selected_index"), TEXT("integer"), TEXT("Initial selected index"))
				.Build(),
			Cat);

		Registry.RegisterAction(
			TEXT("ui"), TEXT("create_lazy_image"),
			TEXT("Add a UCommonLazyImage (async texture load with loading throbber) to an existing WBP"),
			FMonolithActionHandler::CreateStatic(&HandleCreateLazyImage),
			FParamSchemaBuilder()
				.RequiredAssetPath(TEXT("wbp_path"), TEXT("Target WBP path"))
				.Required(TEXT("widget_name"), TEXT("string"), TEXT("Name for the lazy image"))
				.Optional(TEXT("parent_widget"), TEXT("string"), TEXT("Parent panel (default: root)"))
				.Build(),
			Cat);

		Registry.RegisterAction(
			TEXT("ui"), TEXT("create_load_guard"),
			TEXT("Add a UCommonLoadGuard (loading-overlay wrapper) to an existing WBP"),
			FMonolithActionHandler::CreateStatic(&HandleCreateLoadGuard),
			FParamSchemaBuilder()
				.RequiredAssetPath(TEXT("wbp_path"), TEXT("Target WBP path"))
				.Required(TEXT("widget_name"), TEXT("string"), TEXT("Name for the load guard"))
				.Optional(TEXT("parent_widget"), TEXT("string"), TEXT("Parent panel (default: root)"))
				.Build(),
			Cat);
	}
}

#endif // WITH_COMMONUI
