// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "K2Node_SetPCGExEntryMember.h"

#include "BlueprintActionDatabaseRegistrar.h"
#include "BlueprintNodeSpawner.h"
#include "Helpers/PCGExCollectionEntryBlueprintLibrary.h"

#define LOCTEXT_NAMESPACE "K2Node_SetPCGExEntryMember"

void UK2Node_SetPCGExEntryMember::GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const
{
	UClass* ActionKey = GetClass();
	if (ActionRegistrar.IsOpenForRegistration(ActionKey))
	{
		UBlueprintNodeSpawner* NodeSpawner = UBlueprintNodeSpawner::Create(GetClass());
		check(NodeSpawner != nullptr);
		ActionRegistrar.AddBlueprintAction(ActionKey, NodeSpawner);
	}
}

FName UK2Node_SetPCGExEntryMember::GetWildcardFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryMemberValue);
}

FName UK2Node_SetPCGExEntryMember::GetSoftObjectFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryMemberSoftObject);
}

FName UK2Node_SetPCGExEntryMember::GetSoftClassFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetEntryMemberSoftClass);
}

FText UK2Node_SetPCGExEntryMember::GetBaseTitle() const
{
	return LOCTEXT("BaseTitle", "Set Entry Member");
}

#undef LOCTEXT_NAMESPACE
