// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "K2Node.h"
#include "EdGraph/EdGraphPin.h"

#include "K2Node_GetPCGExProperty.generated.h"

class FBlueprintActionDatabaseRegistrar;
class FKismetCompilerContext;
class UEdGraph;
class UEdGraphPin;
class UGraphNodeContextMenuContext;
class UToolMenu;

/**
 * Blueprint node that reads a named property from a UPCGExPropertyCollectionComponent.
 *
 * Single wildcard output pin: the connected pin's type drives how the stored value
 * is converted at runtime (via FPCGExProperty::TryWriteValue). Users can also pick
 * the output type explicitly from the output pin's right-click menu, supporting any
 * concrete EPCGMetadataTypes entry.
 *
 * Pure node -- no exec flow. Compiles down to a single CustomThunk call to
 * UPCGExPropertyBlueprintLibrary::TryGetPCGExPropertyValue with the user's chosen
 * output type stamped onto the call's wildcard parameter.
 */
UCLASS()
class PCGEXPROPERTIESEDITOR_API UK2Node_GetPCGExProperty : public UK2Node
{
	GENERATED_BODY()

public:
	// UEdGraphNode
	virtual void AllocateDefaultPins() override;
	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual FSlateIcon GetIconAndTint(FLinearColor& OutColor) const override;
	virtual FLinearColor GetNodeTitleColor() const override;
	virtual void PinConnectionListChanged(UEdGraphPin* Pin) override;
	virtual void GetNodeContextMenuActions(UToolMenu* Menu, UGraphNodeContextMenuContext* Context) const override;

	// UK2Node
	virtual bool IsNodePure() const override
	{
		return true;
	}

	virtual FText GetMenuCategory() const override;
	virtual void GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const override;
	virtual void ExpandNode(FKismetCompilerContext& CompilerContext, UEdGraph* SourceGraph) override;

private:
	/**
	 * Persisted resolved pin type for the Value output. AllocateDefaultPins re-stamps
	 * this onto the freshly created wildcard pin on graph reload, so manually-picked
	 * types (right-click menu) survive save/reopen even when no connections exist.
	 * Cleared back to PC_Wildcard when the user resets the pin.
	 */
	UPROPERTY()
	FEdGraphPinType ResolvedPinType;

	UEdGraphPin* GetComponentPin() const;
	UEdGraphPin* GetPropertyNamePin() const;
	UEdGraphPin* GetValuePin() const;
	UEdGraphPin* GetSuccessPin() const;

	/** Reset the Value output pin to wildcard (used when no connection is present). */
	void ResetValuePinToWildcard();

	/** Adopt another pin's type onto the Value output pin. */
	void AdoptPinTypeFromOther(const UEdGraphPin* OtherPin);

	/** Set the Value output pin to a specific PinType (used by the right-click menu). */
	void SetValuePinType(const FEdGraphPinType& InType);

	static const FName ComponentPinName;
	static const FName PropertyNamePinName;
	static const FName ValuePinName;
	static const FName SuccessPinName;
};
