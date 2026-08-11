// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "K2Node_SetPCGExCollectionMember.h"

#include "BlueprintActionDatabaseRegistrar.h"
#include "BlueprintNodeSpawner.h"
#include "Helpers/PCGExCollectionEntryBlueprintLibrary.h"

#define LOCTEXT_NAMESPACE "K2Node_SetPCGExCollectionMember"

void UK2Node_SetPCGExCollectionMember::GetMenuActions(FBlueprintActionDatabaseRegistrar& ActionRegistrar) const
{
	UClass* ActionKey = GetClass();
	if (ActionRegistrar.IsOpenForRegistration(ActionKey))
	{
		UBlueprintNodeSpawner* NodeSpawner = UBlueprintNodeSpawner::Create(GetClass());
		check(NodeSpawner != nullptr);
		ActionRegistrar.AddBlueprintAction(ActionKey, NodeSpawner);
	}
}

FName UK2Node_SetPCGExCollectionMember::GetWildcardFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetCollectionMemberValue);
}

FName UK2Node_SetPCGExCollectionMember::GetSoftObjectFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetCollectionMemberSoftObject);
}

FName UK2Node_SetPCGExCollectionMember::GetSoftClassFunctionName() const
{
	return GET_FUNCTION_NAME_CHECKED(UPCGExCollectionEntryBlueprintLibrary, TrySetCollectionMemberSoftClass);
}

FText UK2Node_SetPCGExCollectionMember::GetBaseTitle() const
{
	return LOCTEXT("BaseTitle", "Set Collection Member");
}

#undef LOCTEXT_NAMESPACE
