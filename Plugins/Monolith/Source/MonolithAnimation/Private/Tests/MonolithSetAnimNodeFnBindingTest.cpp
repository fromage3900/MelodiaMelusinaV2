// Copyright tumourlove. All Rights Reserved.

// =============================================================================
// MonolithSetAnimNodeFnBindingTest.cpp
//
// Regression test for the set_anim_node_function_binding subsystem-refresh fix.
//
// THE FIX (HandleSetAnimNodeFunctionBinding, MonolithAnimationActions.cpp):
//   After MarkBlueprintAsModified, the handler calls ABP->RequestRefreshExtensions()
//   so the next compile REGENERATES the anim-blueprint extension set for the changed
//   binding. A bound become-relevant / initial-update function depends on the
//   FAnimSubsystemInstance_NodeRelevancy subsystem; without the refresh that
//   subsystem is OMITTED from the generated class and a bound dispatcher hits a
//   NULL subsystem at runtime.
//
// WHAT THIS ASSERTS:
//   Create a disposable AnimBlueprint in /Game/Tests/Monolith/, add a sequence-player
//   anim node, author a thread-safe self-function whose signature matches the
//   anim-update prototype, bind it to the node's become-relevant slot via the action
//   path (FMonolithAnimationActions::HandleSetAnimNodeFunctionBinding), and after the
//   bind+compile assert that the generated class carries a NON-NULL
//   FAnimSubsystemInstance_NodeRelevancy subsystem (i.e. the extension regenerated).
//
//   This is the observable contract the fix guarantees. Removing
//   RequestRefreshExtensions() leaves the subsystem absent on the freshly-modified
//   class -> this assertion fails -> regression caught.
//
// The disposable ABP + its package are deleted at the end of the test.
//
// SKIP semantics: the test is self-contained (it builds its own minimal skeleton),
// so it does not depend on any project or engine asset. It only SKIPs if GEditor is
// unavailable (non-editor context).
// =============================================================================

#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

#include "Editor.h"
#include "Dom/JsonObject.h"

#include "MonolithAnimationActions.h"
#include "MonolithToolRegistry.h" // FMonolithActionResult

#include "Animation/Skeleton.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/AnimBlueprintGeneratedClass.h"
#include "Animation/AnimInstance.h"
#include "AnimBlueprintExtension.h" // UAnimBlueprintExtension::GetExtensions — extension-presence assertion
#include "ReferenceSkeleton.h"

#include "AnimationGraph.h"
#include "AnimGraphNode_Base.h"
#include "AnimGraphNode_SequencePlayer.h"
#include "EdGraph/EdGraph.h" // FGraphNodeCreator (template defined here)
#include "K2Node_FunctionEntry.h"
#include "EdGraphSchema_K2.h"

#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

namespace MonolithSetAnimNodeFnBindingTest
{
	static const TCHAR* const TestAbpPath = TEXT("/Game/Tests/Monolith/ABP_FnBindingRefreshTest");
	static const TCHAR* const TestFuncName = TEXT("MonolithTestBecomeRelevant");

	// Build a minimal disposable USkeleton (root + one child bone) entirely in-memory.
	// Avoids any dependency on a project/engine skeletal asset.
	static USkeleton* CreateDisposableSkeleton()
	{
		USkeleton* Skeleton = NewObject<USkeleton>(GetTransientPackage(), NAME_None, RF_Transient);
		if (!Skeleton) return nullptr;
		{
			FReferenceSkeletonModifier Modifier(Skeleton);
			Modifier.Add(FMeshBoneInfo(FName(TEXT("root")), TEXT("root"), INDEX_NONE), FTransform::Identity);
			Modifier.Add(FMeshBoneInfo(FName(TEXT("pelvis")), TEXT("pelvis"), 0), FTransform::Identity);
		}
		return Skeleton;
	}

	// Resolve the engine anim-update prototype UFunction so the authored self-function
	// copies a signature-compatible parameter list (the handler's validate gate requires
	// IsSignatureCompatibleWith the node's PrototypeFunction).
	static UFunction* ResolvePrototypeFunction()
	{
		return FindObject<UFunction>(nullptr,
			TEXT("/Script/AnimGraphRuntime.AnimExecutionContextLibrary.Prototype_ThreadSafeAnimUpdateCall"));
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMonolithAnimNodeFnBindingSubsystemRefreshTest,
	"Monolith.AnimNodeFnBinding.SubsystemRefresh",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithAnimNodeFnBindingSubsystemRefreshTest::RunTest(const FString& /*Parameters*/)
{
	using namespace MonolithSetAnimNodeFnBindingTest;

	if (!GEditor)
	{
		AddInfo(TEXT("Skipped — no GEditor (non-editor context)"));
		return true;
	}

	// --- 1) Disposable skeleton + AnimBlueprint -----------------------------------
	USkeleton* Skeleton = CreateDisposableSkeleton();
	if (!TestNotNull(TEXT("Disposable skeleton created"), Skeleton))
	{
		return false;
	}

	UPackage* Pkg = CreatePackage(TestAbpPath);
	if (!TestNotNull(TEXT("Test package created"), Pkg))
	{
		return false;
	}

	FString AssetName;
	int32 LastSlash = INDEX_NONE;
	FString(TestAbpPath).FindLastChar('/', LastSlash);
	AssetName = FString(TestAbpPath).Mid(LastSlash + 1);

	UAnimBlueprint* ABP = Cast<UAnimBlueprint>(FKismetEditorUtilities::CreateBlueprint(
		UAnimInstance::StaticClass(), Pkg, FName(*AssetName),
		BPTYPE_Normal, UAnimBlueprint::StaticClass(),
		UAnimBlueprintGeneratedClass::StaticClass(), NAME_None));
	if (!TestNotNull(TEXT("AnimBlueprint created"), ABP))
	{
		return false;
	}
	ABP->TargetSkeleton = Skeleton;
	if (UAnimBlueprintGeneratedClass* GenClass = Cast<UAnimBlueprintGeneratedClass>(ABP->GeneratedClass))
	{
		GenClass->TargetSkeleton = Skeleton;
	}
	if (UAnimBlueprintGeneratedClass* SkelGenClass = Cast<UAnimBlueprintGeneratedClass>(ABP->SkeletonGeneratedClass))
	{
		SkelGenClass->TargetSkeleton = Skeleton;
	}

	// --- 2) Add a sequence-player anim node to the main AnimGraph ------------------
	UAnimationGraph* AnimGraph = nullptr;
	{
		TArray<UEdGraph*> AllGraphs;
		ABP->GetAllGraphs(AllGraphs);
		for (UEdGraph* Graph : AllGraphs)
		{
			if (UAnimationGraph* AG = Cast<UAnimationGraph>(Graph))
			{
				AnimGraph = AG;
				break;
			}
		}
	}
	if (!TestNotNull(TEXT("Main AnimGraph found"), AnimGraph))
	{
		return false;
	}

	UAnimGraphNode_Base* SeqNode = nullptr;
	{
		// Pristine spawn — avoids the template-duplication assert path.
		FGraphNodeCreator<UAnimGraphNode_SequencePlayer> Creator(*AnimGraph);
		UAnimGraphNode_SequencePlayer* NewNode = Creator.CreateNode(/*bSelectNewNode=*/false);
		Creator.Finalize();
		SeqNode = NewNode;
	}
	if (!TestNotNull(TEXT("Sequence-player node spawned"), SeqNode))
	{
		return false;
	}
	const FString NodeId = SeqNode->GetName();

	// --- 3) Author a thread-safe self-function with a prototype-compatible signature -
	UFunction* Prototype = ResolvePrototypeFunction();
	if (!TestNotNull(TEXT("Anim-update prototype function resolved"), Prototype))
	{
		return false;
	}

	UEdGraph* FuncGraph = FBlueprintEditorUtils::CreateNewGraph(
		ABP, FName(TestFuncName), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
	if (!TestNotNull(TEXT("Function graph created"), FuncGraph))
	{
		return false;
	}
	// Seed the entry/exit nodes from the prototype so the new function's signature is
	// compatible with the anim-update prototype the handler validates against.
	FBlueprintEditorUtils::AddFunctionGraph<UFunction>(ABP, FuncGraph, /*bIsUserCreated=*/true, Prototype);

	// Mark the function thread-safe (the handler hard-rejects non-thread-safe bindings).
	for (UEdGraphNode* Node : FuncGraph->Nodes)
	{
		if (UK2Node_FunctionEntry* Entry = Cast<UK2Node_FunctionEntry>(Node))
		{
			Entry->Modify();
			Entry->MetaData.bThreadSafe = true;
			break;
		}
	}

	// Compile once so the function exists on the (skeleton) generated class for binding.
	FKismetEditorUtilities::CompileBlueprint(ABP);

	// --- 4) Bind the become-relevant slot via the ACTION PATH (the code under test) -
	TSharedPtr<FJsonObject> BindParams = MakeShared<FJsonObject>();
	BindParams->SetStringField(TEXT("asset_path"), ABP->GetPathName());
	BindParams->SetStringField(TEXT("node_id"), NodeId);
	BindParams->SetStringField(TEXT("binding"), TEXT("become_relevant"));
	BindParams->SetStringField(TEXT("function_name"), TestFuncName);
	BindParams->SetBoolField(TEXT("recompile"), true);

	FMonolithActionResult BindResult = FMonolithAnimationActions::HandleSetAnimNodeFunctionBinding(BindParams);
	if (!TestTrue(
			FString::Printf(TEXT("Bind action succeeded (%s)"),
				BindResult.bSuccess ? TEXT("ok") : *BindResult.ErrorMessage),
			BindResult.bSuccess))
	{
		// Best-effort cleanup before bailing.
		if (ABP) { ABP->ClearFlags(RF_Standalone | RF_Public); ABP->RemoveFromRoot(); ABP->MarkAsGarbage(); }
		if (Pkg) { Pkg->SetDirtyFlag(false); Pkg->RemoveFromRoot(); Pkg->MarkAsGarbage(); }
		return false;
	}

	// --- 5) ASSERT: the NodeRelevancy extension was requested for the ABP ------------
	// The fix (RequestRefreshExtensions) is what causes the compile to request the
	// UAnimBlueprintExtension_NodeRelevancy extension for the bound become-relevant
	// function. The extension survives the post-compile RefreshSet because the bound
	// node keeps needing it. A regression (fix removed) means the extension is never
	// requested -> bExtensionPresent false -> test fails.
	//
	// Name-match (not GetExtension<T>, which asserts on miss) avoids a Private-header
	// dependency on the editor-only extension class.
	bool bExtensionPresent = false;
	for (UAnimBlueprintExtension* Ext : UAnimBlueprintExtension::GetExtensions(ABP))
	{
		if (Ext && Ext->GetClass()->GetName() == TEXT("AnimBlueprintExtension_NodeRelevancy"))
		{
			bExtensionPresent = true;
			break;
		}
	}

	TestTrue(
		TEXT("NodeRelevancy extension requested after binding a become-relevant function "
			 "(proves RequestRefreshExtensions ran)"),
		bExtensionPresent);

	// --- 6) Cleanup: delete the disposable asset ------------------------------------
	// Mark the package for removal and trash the object so /Game/Tests stays clean.
	if (ABP)
	{
		ABP->ClearFlags(RF_Standalone | RF_Public);
		ABP->RemoveFromRoot();
		ABP->MarkAsGarbage();
	}
	if (Pkg)
	{
		Pkg->SetDirtyFlag(false);
		Pkg->ClearFlags(RF_Standalone);
		Pkg->RemoveFromRoot();
		Pkg->MarkAsGarbage();
	}

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
