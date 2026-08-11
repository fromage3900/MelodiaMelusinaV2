#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Class/Blueprint variable-contract actions.
 *
 * Two related actions that reconcile the member-variable surface of one class
 * against another by name+type+container+enum/struct subtype:
 *
 *   compare_class_variable_contract — pure read/report diff between two sides
 *       (each a Blueprint asset path or a native class name). Emits a per-variable
 *       diff keyed by name with a mismatch classification. Mutates nothing.
 *
 *   promote_variables_to_parent — reconcile a named set of a Blueprint's local
 *       variables against its native parent class contract. verify mode reports
 *       which the parent already satisfies vs which it does not yet declare
 *       compatibly; remove_shadowed deletes BP-local duplicates that the parent
 *       already satisfies (so graph nodes rebind to the parent). Never authors C++.
 */
class FMonolithBlueprintContractActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleCompareClassVariableContract(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandlePromoteVariablesToParent(const TSharedPtr<FJsonObject>& Params);
};
