// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "K2Node_SetPCGExEntryProperty.h"

#include "BlueprintActionDatabaseRegistrar.h"
#include "BlueprintNodeSpawner.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "KismetCompiler.h"
#include "ToolMenu.h"
#include "ToolMenus.h"
#include "Core/PCGExAssetCollection.h"
#include "Details/PCGExK2NodeTypeHelpers.h"
#include "Helpers/PCGExCollectionEntryBlueprintLibrary.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Metadata/PCGMetadataAttributeTraits.h"
#include "Styling/AppStyle.h"

#define LOCTEXT_NAMESPACE "K2Node_SetPCGExEntryProperty"

// Pin names match the library function's parameter names so ExpandNode can look up
// the spawned UK2Node_CallFunction's pins via FindPinChecked. Display labels are set
// via PinFriendlyName in AllocateDefaultPins.
const FName UK2Node_SetPCGExEntryProperty::CollectionPinName(TEXT("Collection"));
const FName UK2Node_SetPCGExEntryProperty::EntryIndexPinName(TEXT("EntryIndex"));
const FName UK2Node_SetPCGExEntryProperty::PropertyNamePinName(TEXT("PropertyName"));
const FName UK2Node_SetPCGExEntryProperty::NewValuePinName(TEXT("NewValue"));
const FName UK2Node_SetPCGExEntryProperty::ReadbackPinName(TEXT("Readback"));
const FName UK2Node_SetPCGExEntryProperty::SuccessPinName(TEXT("Success"));

void UK2Node_SetPCGExEntryProperty::AllocateDefaultPins()
{
	CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Exec, UEdGraphSchema_K2::PN_Execute);
	CreatePin(EGPD_Output, UEdGraphSchema_K2::PC_Exec, UEdGraphSchema_K2::PN_Then);

	UEdGraphPin* CollectionPin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Object, UPCGExAssetCollection::StaticClass(), CollectionPinName);
	CollectionPin->PinFriendlyName = LOCTEXT("CollectionPinFriendlyName", "Collection");

	UEdGraphPin* EntryIndexPin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Int, EntryIndexPinName);
	EntryIndexPin->PinFriendlyName = LOCTEXT("EntryIndexPinFriendlyName", "Entry Index");
	EntryIndexPin->DefaultValue = TEXT("0");

	UEdGraphPin* NamePin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Name, PropertyNamePinName);
	NamePin->PinFriendlyName = LOCTEXT("PropertyNamePinFriendlyName", "Prop");

	UEdGraphPin* NewValuePin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Wildcard, NewValuePinName);
	NewValuePin->PinFriendlyName = LOCTEXT("NewValuePinFriendlyName", "New Value");

	UEdGraphPin* ReadbackPin = CreatePin(EGPD_Output, UEdGraphSchema_K2::PC_Wildcard, ReadbackPinName);
	ReadbackPin->PinFriendlyName = LOCTEXT("ReadbackPinFriendlyName", "Readback");

	// Restore previously resolved type so manually-picked or previously-connected types
	// survive save/reopen even when no connections exist on either wildcard. Both pins
	// always share the same concrete type.
	if (ResolvedPinType.PinCategory != NAME_None &&
		ResolvedPinType.PinCategory != UEdGraphSchema_K2::PC_Wildcard)
	{
		NewValuePin->PinType = ResolvedPinType;
		ReadbackPin->PinType = ResolvedPinType;
	}

	UEdGraphPin* SuccessPin = CreatePin(EGPD_Output, UEdGraphSchema_K2::PC_Boolean, SuccessPinName);
	SuccessPin->PinFriendlyName = LOCTEXT("SuccessPinFriendlyName", "Success");

	Super::AllocateDefaultPins();
}

FText UK2Node_SetPCGExEntryProperty::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return LOCTEXT("NodeTitle", "Set Entry Property");
}

FText UK2Node_SetPCGExEntryProperty::GetTooltipText() const
{
	return LOCTEXT("NodeTooltip",
	               "Writes a value to an entry's property override slot on a PCGEx Asset Collection "
	               "(by raw entry index), enables the override, and reads back the resolved value.\n"
	               "The property must be part of the collection's schema.\n"
	               "New Value and Readback share the same type at compile time; connecting either to "
	               "a typed pin retypes both.\n"
	               "Returns true when the write (and conversion) succeeded.");
}

FSlateIcon UK2Node_SetPCGExEntryProperty::GetIconAndTint(FLinearColor& OutColor) const
{
	OutColor = GetNodeTitleColor();
	static FSlateIcon Icon(FAppStyle::GetAppStyleSetName(), "GraphEditor.Function_16x");
	return Icon;
}

FLinearColor UK2Node_SetPCGExEntryProperty::GetNodeTitleColor() const
{
	return FLinearColor(0.0f, 0.5f, 0.8f);
}

FText UK2Node_SetPCGExEntryProperty::GetMenuCategory() const
{
	return LOCTEXT("MenuCategory", "PCGEx|Collection");
}

void UK2Node_SetPCGExEntryProperty::GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const
{
	UClass* ActionKey = GetClass();
	if (ActionRegistrar.IsOpenForRegistration(ActionKey))
	{
		UBlueprintNodeSpawner* NodeSpawner = UBlueprintNodeSpawner::Create(GetClass());
		check(NodeSpawner != nullptr);
		ActionRegistrar.AddBlueprintAction(ActionKey, NodeSpawner);
	}
}

void UK2Node_SetPCGExEntryProperty::PinConnectionListChanged(UEdGraphPin* Pin)
{
	Super::PinConnectionListChanged(Pin);

	UEdGraphPin* NewValuePin = GetNewValuePin();
	UEdGraphPin* ReadbackPin = GetReadbackPin();
	if (!NewValuePin || !ReadbackPin)
	{
		return;
	}

	if (Pin != NewValuePin && Pin != ReadbackPin)
	{
		return;
	}

	if (Pin->LinkedTo.Num() > 0)
	{
		AdoptTypeFromOther(Pin->LinkedTo[0]);
		GetGraph()->NotifyGraphChanged();
	}
	else if (NewValuePin->LinkedTo.Num() == 0 && ReadbackPin->LinkedTo.Num() == 0)
	{
		// Both wildcards fully disconnected -- revert to wildcard so the node can adapt next time
		if (NewValuePin->PinType.PinCategory != UEdGraphSchema_K2::PC_Wildcard ||
			ReadbackPin->PinType.PinCategory != UEdGraphSchema_K2::PC_Wildcard)
		{
			ResetWildcardPinsToWildcard();
			GetGraph()->NotifyGraphChanged();
		}
	}
}

void UK2Node_SetPCGExEntryProperty::GetNodeContextMenuActions(UToolMenu* Menu, UGraphNodeContextMenuContext* Context) const
{
	Super::GetNodeContextMenuActions(Menu, Context);

	if (Context->bIsDebugging || !Context->Pin)
	{
		return;
	}
	if (Context->Pin != GetNewValuePin() && Context->Pin != GetReadbackPin())
	{
		return;
	}

	FToolMenuSection& Section = Menu->AddSection(
		"K2NodeSetPCGExEntryProperty",
		LOCTEXT("ChangeOutputType", "Change Value Type"));

	const UK2Node_SetPCGExEntryProperty* ConstThis = this;

	for (uint8 i = 0; i < static_cast<uint8>(EPCGMetadataTypes::Count); ++i)
	{
		const EPCGMetadataTypes MetadataType = static_cast<EPCGMetadataTypes>(i);

		FEdGraphPinType PinType;
		if (!PCGExK2NodeTypeHelpers::MakePinTypeForMetadataType(MetadataType, PinType))
		{
			continue;
		}

		Section.AddMenuEntry(
			NAME_None,
			PCGExK2NodeTypeHelpers::GetDisplayNameForMetadataType(MetadataType),
			FText::GetEmpty(),
			FSlateIcon(),
			FUIAction(FExecuteAction::CreateLambda([ConstThis, PinType]()
			{
				if (UK2Node_SetPCGExEntryProperty* MutableThis = const_cast<UK2Node_SetPCGExEntryProperty*>(ConstThis))
				{
					MutableThis->SetWildcardPinsType(PinType);
				}
			})));
	}
}

void UK2Node_SetPCGExEntryProperty::ExpandNode(FKismetCompilerContext& CompilerContext, UEdGraph* SourceGraph)
{
	Super::ExpandNode(CompilerContext, SourceGraph);

	UEdGraphPin* NewValuePin = GetNewValuePin();
	UEdGraphPin* ReadbackPin = GetReadbackPin();
	if (!NewValuePin || !ReadbackPin ||
		NewValuePin->PinType.PinCategory == UEdGraphSchema_K2::PC_Wildcard ||
		ReadbackPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Wildcard)
	{
		CompilerContext.MessageLog.Error(
			*LOCTEXT("WildcardUnresolved",
			         "@@ has unresolved wildcard pins. Connect either New Value or Readback to a typed pin, or pick a type from either pin's right-click menu.")
			.ToString(),
			this);
		BreakAllNodeLinks();
		return;
	}

	// Object/Class pins are dispatched to dedicated well-typed library functions to avoid
	// the wildcard CustomStructureParam marshalling bug (the BP compiler stuffs UObject*
	// into an `int32&` slot and corrupts the property's FSoftObjectPath payload). Struct
	// and primitive pins continue to use the wildcard path where the marshalling is sound.
	const FName Category = NewValuePin->PinType.PinCategory;
	const bool bIsObjectLike =
		Category == UEdGraphSchema_K2::PC_Object ||
		Category == UEdGraphSchema_K2::PC_Interface ||
		Category == UEdGraphSchema_K2::PC_SoftObject;
	const bool bIsClassLike =
		Category == UEdGraphSchema_K2::PC_Class ||
		Category == UEdGraphSchema_K2::PC_SoftClass;
	const bool bUseTypedPath = bIsObjectLike || bIsClassLike;

	UClass* TargetClass = nullptr;
	if (bUseTypedPath)
	{
		TargetClass = Cast<UClass>(NewValuePin->PinType.PinSubCategoryObject.Get());
		if (!TargetClass)
		{
			CompilerContext.MessageLog.Error(
				*LOCTEXT("ObjectPinMissingClass",
				         "@@ has an Object/Class pin with no resolved class.")
				.ToString(),
				this);
			BreakAllNodeLinks();
			return;
		}
	}

	UEdGraphPin* OurCollection = GetCollectionPin();
	UEdGraphPin* OurEntryIndex = GetEntryIndexPin();
	UEdGraphPin* OurName = GetPropertyNamePin();

	// Set call (impure). Carries the user's exec flow and Success bool. Choose the
	// function based on the resolved pin category.
	UK2Node_CallFunction* SetCall = CompilerContext.SpawnIntermediateNode<UK2Node_CallFunction>(this, SourceGraph);
	{
		FName SetFunc;
		if (bIsObjectLike)
		{
			SetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryPropertyObject);
		}
		else if (bIsClassLike)
		{
			SetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryPropertyClass);
		}
		else
		{
			SetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryPropertyOverride);
		}
		SetCall->FunctionReference.SetExternalMember(SetFunc, UPCGExCollectionEntryBlueprintLibrary::StaticClass());
		SetCall->AllocateDefaultPins();
	}

	UEdGraphPin* SetCallExec = SetCall->GetExecPin();
	UEdGraphPin* SetCallThen = SetCall->GetThenPin();
	UEdGraphPin* SetCallCollection = SetCall->FindPinChecked(CollectionPinName);
	UEdGraphPin* SetCallEntryIndex = SetCall->FindPinChecked(EntryIndexPinName);
	UEdGraphPin* SetCallName = SetCall->FindPinChecked(PropertyNamePinName);
	UEdGraphPin* SetCallReturn = SetCall->GetReturnValuePin();

	// Resolve the NewValue input pin: the wildcard path needs type stamping; the typed
	// paths have a concrete UObject*/UClass* pin that accepts the user's connection via
	// the schema's standard upcast.
	UEdGraphPin* SetCallNewValue = nullptr;
	if (bIsObjectLike)
	{
		SetCallNewValue = SetCall->FindPinChecked(TEXT("NewObject"));
	}
	else if (bIsClassLike)
	{
		SetCallNewValue = SetCall->FindPinChecked(TEXT("NewClass"));
	}
	else
	{
		SetCallNewValue = SetCall->FindPinChecked(NewValuePinName);
		SetCallNewValue->PinType = NewValuePin->PinType;
	}

	CompilerContext.MovePinLinksToIntermediate(*GetExecPin(), *SetCallExec);
	CompilerContext.MovePinLinksToIntermediate(*GetThenPin(), *SetCallThen);
	CompilerContext.MovePinLinksToIntermediate(*NewValuePin, *SetCallNewValue);
	CompilerContext.MovePinLinksToIntermediate(*GetSuccessPin(), *SetCallReturn);

	// Get call (pure). Pure nodes evaluate on demand when their output is consumed
	// downstream -- which lands after the Set's exec has fired -- so the readback reflects
	// post-write state. Single-wildcard (or fully-typed) calls only, since multi-wildcard
	// CustomStructureParam doesn't reliably construct non-trivially-copyable output buffers.
	UK2Node_CallFunction* GetCall = CompilerContext.SpawnIntermediateNode<UK2Node_CallFunction>(this, SourceGraph);
	{
		FName GetFunc;
		if (bIsObjectLike)
		{
			GetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyObject);
		}
		else if (bIsClassLike)
		{
			GetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyClass);
		}
		else
		{
			GetFunc = GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyValue);
		}
		GetCall->FunctionReference.SetExternalMember(GetFunc, UPCGExCollectionEntryBlueprintLibrary::StaticClass());
		GetCall->AllocateDefaultPins();
	}

	UEdGraphPin* GetCallCollection = GetCall->FindPinChecked(CollectionPinName);
	UEdGraphPin* GetCallEntryIndex = GetCall->FindPinChecked(EntryIndexPinName);
	UEdGraphPin* GetCallName = GetCall->FindPinChecked(PropertyNamePinName);

	// Resolve the readback output pin. Typed paths use DeterminesOutputType on the
	// function's return value -- set ExpectedClass to TargetClass and trigger the call
	// node's dynamic-output retyping. Wildcard path stamps the output pin's type.
	UEdGraphPin* GetCallReadbackSource = nullptr;
	if (bUseTypedPath)
	{
		UEdGraphPin* GetCallExpectedClass = GetCall->FindPinChecked(TEXT("ExpectedClass"));
		GetCallExpectedClass->DefaultObject = TargetClass;
		GetCall->PinDefaultValueChanged(GetCallExpectedClass);
		GetCallReadbackSource = GetCall->GetReturnValuePin();
	}
	else
	{
		GetCallReadbackSource = GetCall->FindPinChecked(TEXT("OutValue"));
		GetCallReadbackSource->PinType = ReadbackPin->PinType;
	}

	// Fan Collection, EntryIndex and PropertyName into both intermediate calls. Linked-to
	// sources get connected to both; otherwise the literal default value is forwarded to both.
	const UEdGraphSchema_K2* K2 = GetDefault<UEdGraphSchema_K2>();
	if (OurCollection)
	{
		if (OurCollection->LinkedTo.Num() > 0)
		{
			for (UEdGraphPin* Source : OurCollection->LinkedTo)
			{
				K2->TryCreateConnection(Source, SetCallCollection);
				K2->TryCreateConnection(Source, GetCallCollection);
			}
		}
		else
		{
			SetCallCollection->DefaultObject = OurCollection->DefaultObject;
			GetCallCollection->DefaultObject = OurCollection->DefaultObject;
			SetCallCollection->DefaultValue = OurCollection->DefaultValue;
			GetCallCollection->DefaultValue = OurCollection->DefaultValue;
		}
	}
	if (OurEntryIndex)
	{
		if (OurEntryIndex->LinkedTo.Num() > 0)
		{
			for (UEdGraphPin* Source : OurEntryIndex->LinkedTo)
			{
				K2->TryCreateConnection(Source, SetCallEntryIndex);
				K2->TryCreateConnection(Source, GetCallEntryIndex);
			}
		}
		else
		{
			SetCallEntryIndex->DefaultValue = OurEntryIndex->DefaultValue;
			GetCallEntryIndex->DefaultValue = OurEntryIndex->DefaultValue;
		}
	}
	if (OurName)
	{
		if (OurName->LinkedTo.Num() > 0)
		{
			for (UEdGraphPin* Source : OurName->LinkedTo)
			{
				K2->TryCreateConnection(Source, SetCallName);
				K2->TryCreateConnection(Source, GetCallName);
			}
		}
		else
		{
			SetCallName->DefaultValue = OurName->DefaultValue;
			GetCallName->DefaultValue = OurName->DefaultValue;
		}
	}

	CompilerContext.MovePinLinksToIntermediate(*ReadbackPin, *GetCallReadbackSource);

	BreakAllNodeLinks();
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetExecPin() const
{
	return FindPin(UEdGraphSchema_K2::PN_Execute);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetThenPin() const
{
	return FindPin(UEdGraphSchema_K2::PN_Then);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetCollectionPin() const
{
	return FindPin(CollectionPinName);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetEntryIndexPin() const
{
	return FindPin(EntryIndexPinName);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetPropertyNamePin() const
{
	return FindPin(PropertyNamePinName);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetNewValuePin() const
{
	return FindPin(NewValuePinName);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetReadbackPin() const
{
	return FindPin(ReadbackPinName);
}

UEdGraphPin* UK2Node_SetPCGExEntryProperty::GetSuccessPin() const
{
	return FindPin(SuccessPinName);
}

void UK2Node_SetPCGExEntryProperty::ResetWildcardPinsToWildcard()
{
	auto ResetOne = [](UEdGraphPin* Pin)
	{
		if (!Pin)
		{
			return;
		}
		Pin->PinType = FEdGraphPinType();
		Pin->PinType.PinCategory = UEdGraphSchema_K2::PC_Wildcard;
		Pin->BreakAllPinLinks();
	};

	ResetOne(GetNewValuePin());
	ResetOne(GetReadbackPin());

	ResolvedPinType = FEdGraphPinType();
	ResolvedPinType.PinCategory = UEdGraphSchema_K2::PC_Wildcard;
}

void UK2Node_SetPCGExEntryProperty::AdoptTypeFromOther(const UEdGraphPin* OtherPin)
{
	if (!OtherPin)
	{
		return;
	}
	FEdGraphPinType InType = OtherPin->PinType;
	InType.ContainerType = EPinContainerType::None;

	if (UEdGraphPin* NewValuePin = GetNewValuePin())
	{
		NewValuePin->PinType = InType;
	}
	if (UEdGraphPin* ReadbackPin = GetReadbackPin())
	{
		ReadbackPin->PinType = InType;
	}
	ResolvedPinType = InType;
}

void UK2Node_SetPCGExEntryProperty::SetWildcardPinsType(const FEdGraphPinType& InType)
{
	auto Apply = [&InType](UEdGraphPin* Pin)
	{
		if (!Pin)
		{
			return;
		}
		for (int32 i = Pin->LinkedTo.Num() - 1; i >= 0; --i)
		{
			const UEdGraphPin* Linked = Pin->LinkedTo[i];
			if (!Linked || Linked->PinType != InType)
			{
				Pin->BreakLinkTo(Pin->LinkedTo[i]);
			}
		}
		Pin->PinType = InType;
	};

	Apply(GetNewValuePin());
	Apply(GetReadbackPin());
	ResolvedPinType = InType;

	GetGraph()->NotifyGraphChanged();

	if (UBlueprint* BP = GetBlueprint())
	{
		FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	}
}

#undef LOCTEXT_NAMESPACE
