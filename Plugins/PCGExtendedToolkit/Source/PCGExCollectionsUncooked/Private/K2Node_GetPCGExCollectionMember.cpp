// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "K2Node_GetPCGExCollectionMember.h"

#include "BlueprintActionDatabaseRegistrar.h"
#include "BlueprintNodeSpawner.h"
#include "Helpers/PCGExCollectionEntryBlueprintLibrary.h"

#define LOCTEXT_NAMESPACE "K2Node_GetPCGExCollectionMember"

void UK2Node_GetPCGExCollectionMember::GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const
{
	UClass* ActionKey = GetClass();
	if (ActionRegistrar.IsOpenForRegistration(ActionKey))
	{
		UBlueprintNodeSpawner* NodeSpawner = UBlueprintNodeSpawner::Create(GetClass());
		check(NodeSpawner != nullptr);
		ActionRegistrar.AddBlueprintAction(ActionKey, NodeSpawner);
	}
}

FName UK2Node_GetPCGExCollectionMember::GetWildcardFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetCollectionMemberValue);
}

FName UK2Node_GetPCGExCollectionMember::GetSoftObjectFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetCollectionMemberSoftObject);
}

FName UK2Node_GetPCGExCollectionMember::GetSoftClassFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TryGetCollectionMemberSoftClass);
}

FText UK2Node_GetPCGExCollectionMember::GetBaseTitle() const
{
	return LOCTEXT("BaseTitle", "Get Collection Member");
}

#undef LOCTEXT_NAMESPACE
