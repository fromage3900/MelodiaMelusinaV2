#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * AnimBlueprint graph-surgery actions for Monolith (animation namespace).
 *
 * Higher-risk graph repair kept separate from the stable MonolithAbpWriteActions
 * wiring surface so the reflective-K2Node and slice-removal work can be rolled
 * back as a unit.
 *
 * 5 actions:
 *   - rebuild_evaluate_chooser_node   (WITH_CHOOSER)
 *   - replace_evaluate_chooser_nodes  (WITH_CHOOSER)
 *   - duplicate_reparent_and_sanitize
 *   - find_node_slice
 *   - remove_node_slice
 *
 * The two Evaluate-Chooser actions spawn UK2Node_EvaluateChooser2 reflectively
 * (its header lives in a non-exported ChooserUncooked/Private path and cannot be
 * included). They are gated behind WITH_CHOOSER; off-gate the handlers return a
 * clean "Chooser plugin not available" error rather than failing to link.
 */
class MONOLITHANIMATION_API FMonolithAbpGraphSurgeryActions
{
public:
	/** Register all graph-surgery actions with the tool registry. Always registers; chooser handlers gate internally. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// F10 — reflective Evaluate-Chooser node surgery (WITH_CHOOSER)
	static FMonolithActionResult HandleRebuildEvaluateChooserNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleReplaceEvaluateChooserNodes(const TSharedPtr<FJsonObject>& Params);

	// Pack B — chooser-into-AnimGraph (WITH_CHOOSER)
	// add_evaluate_chooser_node      : spawn a FRESH UK2Node_EvaluateChooser2 (reflective) bound to a chooser table.
	// wire_chooser_to_motion_matching: connect the chooser 'Result' output to a Motion Matching node 'Database' input.
	static FMonolithActionResult HandleAddEvaluateChooserNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleWireChooserToMotionMatching(const TSharedPtr<FJsonObject>& Params);

	// bind_chooser_database_via_threadsafe (WITH_CHOOSER): place the (exec-driven)
	// EvaluateChooser2 inside a thread-safe FUNCTION graph with execute wired + context=self,
	// store its Result into a SelectedDatabase var, and feed the MM node Database pin from a
	// VariableGet of that var. This is the WORKING exec-driven pattern (a bare chooser dropped
	// in the AnimGraph with execute unconnected is pruned by the compiler -> null database -> A-pose).
	static FMonolithActionResult HandleBindChooserDatabaseViaThreadSafe(const TSharedPtr<FJsonObject>& Params);

	// bind_threadsafe_update_function (T1-L1): GENERALIZES the thread-safe function-graph surgery
	// proven by HandleBindChooserDatabaseViaThreadSafe, swapping the reflective EvaluateChooser2 node
	// for a UK2Node_CallFunction bound (SetFromFunction) to a resolved UFunction*. Creates/reuses a
	// thread-safe FUNCTION graph (BlueprintThreadSafeUpdateAnimation context), wires FunctionEntry
	// exec -> call node exec, optional Self -> object/self context pin, supplies a small fixed input
	// arg set (literal pin defaults + self), stores the call's single result into a named var via a
	// VariableSet, and (optionally) feeds an AnimGraph target node pin from a VariableGet of that var.
	//
	// v1a SCOPE: known-signature BP-library / member static call. The target UFunction is resolved via
	// UClass::FindFunctionByName and MUST be a non-pure, thread-safe (BlueprintThreadSafe), Kismet-callable
	// function with NO return-parameter properties (anim-graph rule) and a single non-exec result output.
	// Unsupported signatures (pure, non-thread-safe, internal-use-only, return-param, multi-result, or an
	// arg binding referencing a pin/type we cannot set) are REJECTED with a clear error rather than
	// silently mis-wired. Arbitrary-signature generic arg binding (v1b) is a gated follow-on. This handler
	// does NOT depend on the Chooser plugin and compiles regardless of WITH_CHOOSER.
	static FMonolithActionResult HandleBindThreadsafeUpdateFunction(const TSharedPtr<FJsonObject>& Params);

	// F11 — duplicate + reparent + dependency classification
	static FMonolithActionResult HandleDuplicateReparentAndSanitize(const TSharedPtr<FJsonObject>& Params);

	// F12 — directional node-slice compute / removal
	static FMonolithActionResult HandleFindNodeSlice(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveNodeSlice(const TSharedPtr<FJsonObject>& Params);
};
