// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "K2Node_GetPCGExEntryProperty.h"

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

#define LOCTEXT_NAMESPACE "K2Node_GetPCGExEntryProperty"

// Pin names match the library function's parameter names so ExpandNode can look up
// the spawned UK2Node_CallFunction's pins via FindPinChecked. Display labels are set
// via PinFriendlyName in AllocateDefaultPins.
const FName UK2Node_GetPCGExEntryProperty::CollectionPinName(TEXT("Collection"));
const FName UK2Node_GetPCGExEntryProperty::EntryIndexPinName(TEXT("EntryIndex"));
const FName UK2Node_GetPCGExEntryProperty::PropertyNamePinName(TEXT("PropertyName"));
const FName UK2Node_GetPCGExEntryProperty::ValuePinName(TEXT("OutValue"));
const FName UK2Node_GetPCGExEntryProperty::SuccessPinName(TEXT("Success"));

void UK2Node_GetPCGExEntryProperty::AllocateDefaultPins()
{
	UEdGraphPin* CollectionPin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Object, UPCGExAssetCollection::StaticClass(), CollectionPinName);
	CollectionPin->PinFriendlyName = LOCTEXT("CollectionPinFriendlyName", "Collection");

	UEdGraphPin* EntryIndexPin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Int, EntryIndexPinName);
	EntryIndexPin->PinFriendlyName = LOCTEXT("EntryIndexPinFriendlyName", "Entry Index");
	EntryIndexPin->DefaultValue = TEXT("0");

	UEdGraphPin* NamePin = CreatePin(EGPD_Input, UEdGraphSchema_K2::PC_Name, PropertyNamePinName);
	NamePin->PinFriendlyName = LOCTEXT("PropertyNamePinFriendlyName", "Prop");

	UEdGraphPin* ValuePin = CreatePin(EGPD_Output, UEdGraphSchema_K2::PC_Wildcard, ValuePinName);
	ValuePin->PinFriendlyName = LOCTEXT("ValuePinFriendlyName", "Value");

	// Restore the previously resolved type so the wildcard isn't reset to gray on graph
	// reopen. The engine's pin reconstruction only carries the type across when the pin
	// has live connections; manually-picked types (right-click "Change Type" with no
	// downstream wiring) would otherwise be lost.
	if (ResolvedPinType.PinCategory != NAME_None &&
		ResolvedPinType.PinCategory != UEdGraphSchema_K2::PC_Wildcard)
	{
		ValuePin->PinType = ResolvedPinType;
	}

	UEdGraphPin* SuccessPin = CreatePin(EGPD_Output, UEdGraphSchema_K2::PC_Boolean, SuccessPinName);
	SuccessPin->PinFriendlyName = LOCTEXT("SuccessPinFriendlyName", "Success");

	Super::AllocateDefaultPins();
}

FText UK2Node_GetPCGExEntryProperty::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return LOCTEXT("NodeTitle", "Get Entry Property");
}

FText UK2Node_GetPCGExEntryProperty::GetTooltipText() const
{
	return LOCTEXT("NodeTooltip",
	               "Reads an entry's resolved property from a PCGEx Asset Collection by raw entry index\n"
	               "(enabled per-entry override first, collection default otherwise).\n"
	               "The output pin's type drives how the stored value is converted.\n"
	               "Returns true when the conversion succeeded.");
}

FSlateIcon UK2Node_GetPCGExEntryProperty::GetIconAndTint(FLinearColor& OutColor) const
{
	OutColor = GetNodeTitleColor();
	static FSlateIcon Icon(FAppStyle::GetAppStyleSetName(), "GraphEditor.Function_16x");
	return Icon;
}

FLinearColor UK2Node_GetPCGExEntryProperty::GetNodeTitleColor() const
{
	return FLinearColor(0.0f, 0.5f, 0.8f);
}

FText UK2Node_GetPCGExEntryProperty::GetMenuCategory() const
{
	return LOCTEXT("MenuCategory", "PCGEx|Collection");
}

void UK2Node_GetPCGExEntryProperty::GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const
{
	UClass* ActionKey = GetClass();
	if (ActionRegistrar.IsOpenForRegistration(ActionKey))
	{
		UBlueprintNodeSpawner* NodeSpawner = UBlueprintNodeSpawner::Create(GetClass());
		check(NodeSpawner != nullptr);
		ActionRegistrar.AddBlueprintAction(ActionKey, NodeSpawner);
	}
}

void UK2Node_GetPCGExEntryProperty::PinConnectionListChanged(UEdGraphPin* Pin)
{
	Super::PinConnectionListChanged(Pin);

	UEdGraphPin* ValuePin = GetValuePin();
	if (!ValuePin || Pin != ValuePin)
	{
		return;
	}

	if (Pin->LinkedTo.Num() > 0)
	{
		// Adopt the connected pin's type onto our wildcard output
		AdoptPinTypeFromOther(Pin->LinkedTo[0]);
		GetGraph()->NotifyGraphChanged();
	}
	else if (ValuePin->PinType.PinCategory != UEdGraphSchema_K2::PC_Wildcard)
	{
		// All connections gone -- revert to wildcard so the node can adapt to the next connection
		ResetValuePinToWildcard();
		GetGraph()->NotifyGraphChanged();
	}
}

void UK2Node_GetPCGExEntryProperty::GetNodeContextMenuActions(UToolMenu* Menu, UGraphNodeContextMenuContext* Context) const
{
	Super::GetNodeContextMenuActions(Menu, Context);

	if (Context->bIsDebugging || !Context->Pin || Context->Pin != GetValuePin())
	{
		return;
	}

	FToolMenuSection& Section = Menu->AddSection(
		"K2NodeGetPCGExEntryProperty",
		LOCTEXT("ChangeOutputType", "Change Output Type"));

	const UK2Node_GetPCGExEntryProperty* ConstThis = this;

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
				if (UK2Node_GetPCGExEntryProperty* MutableThis = const_cast<UK2Node_GetPCGExEntryProperty*>(ConstThis))
				{
					MutableThis->SetValuePinType(PinType);
				}
			})));
	}
}

void UK2Node_GetPCGExEntryProperty::ExpandNode(FKismetCompilerContext& CompilerContext, UEdGraph* SourceGraph)
{
	Super::ExpandNode(CompilerContext, SourceGraph);

	UEdGraphPin* ValuePin = GetValuePin();
	if (!ValuePin || ValuePin->PinType.PinCategory == UEdGraphSchema_K2::PC_Wildcard)
	{
		CompilerContext.MessageLog.Error(
			*LOCTEXT("WildcardUnresolved",
			         "@@ has an unresolved wildcard output. Connect the Value pin to a typed input or pick a type from its right-click menu.")
			.ToString(),
			this);
		BreakAllNodeLinks();
		return;
	}

	// Object/Class pins are dispatched to dedicated well-typed library functions. The
	// generic CustomStructureParam wildcard path is reserved for struct/primitive types
	// where the BP compiler's frame marshalling is known to behave; Object/Class pins
	// would otherwise be stuffed into an `int32&` slot and corrupt the property's payload.
	const FName Category = ValuePin->PinType.PinCategory;
	const bool bIsObjectLike =
		Category == UEdGraphSchema_K2::PC_Object ||
		Category == UEdGraphSchema_K2::PC_Interface ||
		Category == UEdGraphSchema_K2::PC_SoftObject;
	const bool bIsClassLike =
		Category == UEdGraphSchema_K2::PC_Class ||
		Category == UEdGraphSchema_K2::PC_SoftClass;

	if (bIsObjectLike || bIsClassLike)
	{
		UClass* TargetClass = Cast<UClass>(ValuePin->PinType.PinSubCategoryObject.Get());
		if (!TargetClass)
		{
			CompilerContext.MessageLog.Error(
				*LOCTEXT("ObjectPinMissingClass",
				         "@@ has an Object/Class output pin with no resolved class.")
				.ToString(),
				this);
			BreakAllNodeLinks();
			return;
		}

		UK2Node_CallFunction* CallNode = CompilerContext.SpawnIntermediateNode<UK2Node_CallFunction>(this, SourceGraph);
		const FName FuncName = bIsObjectLike
			? GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyObject)
			: GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyClass);
		CallNode->FunctionReference.SetExternalMember(FuncName, UPCGExCollectionEntryBlueprintLibrary::StaticClass());
		CallNode->AllocateDefaultPins();

		UEdGraphPin* CallCollectionPin = CallNode->FindPinChecked(CollectionPinName);
		UEdGraphPin* CallEntryIndexPin = CallNode->FindPinChecked(EntryIndexPinName);
		UEdGraphPin* CallNamePin = CallNode->FindPinChecked(PropertyNamePinName);
		UEdGraphPin* CallExpectedClassPin = CallNode->FindPinChecked(TEXT("ExpectedClass"));
		UEdGraphPin* CallSuccessPin = CallNode->FindPinChecked(TEXT("bSuccess"));
		UEdGraphPin* CallReturnPin = CallNode->GetReturnValuePin();

		// Drive DeterminesOutputType: set the ExpectedClass literal and notify the call node
		// so it re-stamps its return value pin to TargetClass.
		CallExpectedClassPin->DefaultObject = TargetClass;
		CallNode->PinDefaultValueChanged(CallExpectedClassPin);

		CompilerContext.MovePinLinksToIntermediate(*GetCollectionPin(), *CallCollectionPin);
		CompilerContext.MovePinLinksToIntermediate(*GetEntryIndexPin(), *CallEntryIndexPin);
		CompilerContext.MovePinLinksToIntermediate(*GetPropertyNamePin(), *CallNamePin);
		CompilerContext.MovePinLinksToIntermediate(*ValuePin, *CallReturnPin);
		CompilerContext.MovePinLinksToIntermediate(*GetSuccessPin(), *CallSuccessPin);

		BreakAllNodeLinks();
		return;
	}

	UK2Node_CallFunction* CallNode = CompilerContext.SpawnIntermediateNode<UK2Node_CallFunction>(this, SourceGraph);
	CallNode->FunctionReference.SetExternalMember(
		GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetEntryPropertyValue),
		UPCGExCollectionEntryBlueprintLibrary::StaticClass());
	CallNode->AllocateDefaultPins();

	UEdGraphPin* CallCollectionPin = CallNode->FindPinChecked(CollectionPinName);
	UEdGraphPin* CallEntryIndexPin = CallNode->FindPinChecked(EntryIndexPinName);
	UEdGraphPin* CallNamePin = CallNode->FindPinChecked(PropertyNamePinName);
	UEdGraphPin* CallValuePin = CallNode->FindPinChecked(ValuePinName);
	UEdGraphPin* CallReturnPin = CallNode->GetReturnValuePin();

	// Stamp the user's resolved type onto the call's CustomStructureParam output before
	// moving connections, so the BP compiler treats it as the matching concrete type.
	CallValuePin->PinType = ValuePin->PinType;

	CompilerContext.MovePinLinksToIntermediate(*GetCollectionPin(), *CallCollectionPin);
	CompilerContext.MovePinLinksToIntermediate(*GetEntryIndexPin(), *CallEntryIndexPin);
	CompilerContext.MovePinLinksToIntermediate(*GetPropertyNamePin(), *CallNamePin);
	CompilerContext.MovePinLinksToIntermediate(*ValuePin, *CallValuePin);
	CompilerContext.MovePinLinksToIntermediate(*GetSuccessPin(), *CallReturnPin);

	BreakAllNodeLinks();
}

UEdGraphPin* UK2Node_GetPCGExEntryProperty::GetCollectionPin() const
{
	return FindPin(CollectionPinName);
}

UEdGraphPin* UK2Node_GetPCGExEntryProperty::GetEntryIndexPin() const
{
	return FindPin(EntryIndexPinName);
}

UEdGraphPin* UK2Node_GetPCGExEntryProperty::GetPropertyNamePin() const
{
	return FindPin(PropertyNamePinName);
}

UEdGraphPin* UK2Node_GetPCGExEntryProperty::GetValuePin() const
{
	return FindPin(ValuePinName);
}

UEdGraphPin* UK2Node_GetPCGExEntryProperty::GetSuccessPin() const
{
	return FindPin(SuccessPinName);
}

void UK2Node_GetPCGExEntryProperty::ResetValuePinToWildcard()
{
	UEdGraphPin* ValuePin = GetValuePin();
	if (!ValuePin)
	{
		return;
	}
	ValuePin->PinType = FEdGraphPinType();
	ValuePin->PinType.PinCategory = UEdGraphSchema_K2::PC_Wildcard;
	ValuePin->BreakAllPinLinks();
	ResolvedPinType = ValuePin->PinType;
}

void UK2Node_GetPCGExEntryProperty::AdoptPinTypeFromOther(const UEdGraphPin* OtherPin)
{
	if (!OtherPin)
	{
		return;
	}
	UEdGraphPin* ValuePin = GetValuePin();
	if (!ValuePin)
	{
		return;
	}
	ValuePin->PinType = OtherPin->PinType;
	ValuePin->PinType.ContainerType = EPinContainerType::None;
	ResolvedPinType = ValuePin->PinType;
}

void UK2Node_GetPCGExEntryProperty::SetValuePinType(const FEdGraphPinType& InType)
{
	UEdGraphPin* ValuePin = GetValuePin();
	if (!ValuePin)
	{
		return;
	}

	// Break existing links if the new type is incompatible with what's connected
	for (int32 i = ValuePin->LinkedTo.Num() - 1; i >= 0; --i)
	{
		const UEdGraphPin* Linked = ValuePin->LinkedTo[i];
		if (!Linked || Linked->PinType != InType)
		{
			ValuePin->BreakLinkTo(ValuePin->LinkedTo[i]);
		}
	}

	ValuePin->PinType = InType;
	ResolvedPinType = InType;
	GetGraph()->NotifyGraphChanged();

	if (UBlueprint* BP = GetBlueprint())
	{
		FBlueprintEditorUtils::MarkBlueprintAsModified(BP);
	}
}

#undef LOCTEXT_NAMESPACE
