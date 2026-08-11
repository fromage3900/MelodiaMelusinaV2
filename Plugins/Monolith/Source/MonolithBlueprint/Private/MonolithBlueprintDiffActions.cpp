#include "MonolithBlueprintDiffActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "Components/SceneComponent.h"
#include "Kismet2/BlueprintEditorUtils.h"

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintDiffActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("compare_blueprints"),
		TEXT("Compare two Blueprints and return a structured diff of variables, components, functions, and graphs. "
		     "Useful for reviewing changes between versions or comparing similar Blueprints."),
		FMonolithActionHandler::CreateStatic(&HandleCompareBlueprints),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path_a"), TEXT("First Blueprint asset path"))
			.RequiredAssetPath(TEXT("asset_path_b"), TEXT("Second Blueprint asset path"))
			.Build());
}

// ============================================================
//  Internal helpers
// ============================================================

namespace
{
	// --- Variable serialization (mirrors HandleGetVariables) ---

	struct FVarInfo
	{
		FString Name;
		FString Type;
		FString DefaultValue;
		FString Category;
		bool bInstanceEditable = false;
		bool bBlueprintReadOnly = false;
		bool bReplicated = false;
		bool bTransient = false;
	};

	TArray<FVarInfo> CollectVariables(UBlueprint* BP)
	{
		TArray<FVarInfo> Out;
		UClass* GenClass = BP->GeneratedClass;
		UObject* CDO = GenClass ? GenClass->GetDefaultObject(false) : nullptr;

		for (const FBPVariableDescription& Var : BP->NewVariables)
		{
			FVarInfo Info;
			Info.Name = Var.VarName.ToString();
			Info.Type = MonolithBlueprintInternal::ContainerPrefix(Var.VarType) +
				MonolithBlueprintInternal::PinTypeToString(Var.VarType);
			Info.DefaultValue = Var.DefaultValue;
			if (Info.DefaultValue.IsEmpty() && CDO && GenClass)
			{
				FProperty* Prop = GenClass->FindPropertyByName(Var.VarName);
				if (Prop)
				{
					const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(CDO);
					Prop->ExportTextItem_Direct(Info.DefaultValue, ValuePtr, nullptr, CDO, PPF_None);
				}
			}
			Info.Category = Var.Category.ToString();
			Info.bInstanceEditable = (Var.PropertyFlags & CPF_DisableEditOnInstance) == 0;
			Info.bBlueprintReadOnly = (Var.PropertyFlags & CPF_BlueprintReadOnly) != 0;
			Info.bReplicated = (Var.PropertyFlags & CPF_Net) != 0;
			Info.bTransient = (Var.PropertyFlags & CPF_Transient) != 0;
			Out.Add(MoveTemp(Info));
		}
		return Out;
	}

	TSharedPtr<FJsonObject> VarInfoToJson(const FVarInfo& V)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("name"), V.Name);
		Obj->SetStringField(TEXT("type"), V.Type);
		Obj->SetStringField(TEXT("default_value"), V.DefaultValue);
		Obj->SetStringField(TEXT("category"), V.Category);
		Obj->SetBoolField(TEXT("instance_editable"), V.bInstanceEditable);
		Obj->SetBoolField(TEXT("blueprint_read_only"), V.bBlueprintReadOnly);
		Obj->SetBoolField(TEXT("replicated"), V.bReplicated);
		Obj->SetBoolField(TEXT("transient"), V.bTransient);
		return Obj;
	}

	// --- Component serialization (flat list by name + class) ---

	struct FCompInfo
	{
		FString Name;
		FString Class;
		bool bIsSceneComponent = false;
		bool bIsRoot = false;
	};

	TArray<FCompInfo> CollectComponents(UBlueprint* BP)
	{
		TArray<FCompInfo> Out;
		USimpleConstructionScript* SCS = BP->SimpleConstructionScript;
		if (!SCS) return Out;

		for (USCS_Node* Node : SCS->GetAllNodes())
		{
			if (!Node) continue;
			FCompInfo Info;
			Info.Name = Node->GetVariableName().ToString();
			Info.Class = Node->ComponentClass ? Node->ComponentClass->GetName() : TEXT("unknown");
			Info.bIsSceneComponent = Node->ComponentClass ? Node->ComponentClass->IsChildOf(USceneComponent::StaticClass()) : false;
			Info.bIsRoot = Node->IsRootNode();
			Out.Add(MoveTemp(Info));
		}
		return Out;
	}

	// --- Function serialization ---

	struct FFuncInfo
	{
		FString Name;
		bool bIsPure = false;
		bool bIsConst = false;
		bool bIsStatic = false;
		FString AccessSpecifier;
		int32 InputCount = 0;
		int32 OutputCount = 0;
	};

	TArray<FFuncInfo> CollectFunctions(UBlueprint* BP)
	{
		TArray<FFuncInfo> Out;
		for (UEdGraph* Graph : BP->FunctionGraphs)
		{
			if (!Graph) continue;
			FFuncInfo Info;
			Info.Name = Graph->GetName();

			UK2Node_FunctionEntry* EntryNode = nullptr;
			UK2Node_FunctionResult* ResultNode = nullptr;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (!EntryNode) EntryNode = Cast<UK2Node_FunctionEntry>(Node);
				if (!ResultNode) ResultNode = Cast<UK2Node_FunctionResult>(Node);
				if (EntryNode && ResultNode) break;
			}

			if (EntryNode)
			{
				const uint32 ExtraFlags = EntryNode->GetFunctionFlags();
				Info.bIsPure = (ExtraFlags & FUNC_BlueprintPure) != 0;
				Info.bIsConst = (ExtraFlags & FUNC_Const) != 0;
				Info.bIsStatic = (ExtraFlags & FUNC_Static) != 0;
				Info.AccessSpecifier =
					(ExtraFlags & FUNC_Protected) ? TEXT("Protected") :
					(ExtraFlags & FUNC_Private)   ? TEXT("Private")   : TEXT("Public");

				for (const UEdGraphPin* Pin : EntryNode->Pins)
				{
					if (!Pin || Pin->bHidden) continue;
					if (Pin->Direction != EGPD_Output) continue;
					if (Pin->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec) continue;
					Info.InputCount++;
				}
			}
			if (ResultNode)
			{
				for (const UEdGraphPin* Pin : ResultNode->Pins)
				{
					if (!Pin || Pin->bHidden) continue;
					if (Pin->Direction != EGPD_Input) continue;
					if (Pin->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec) continue;
					Info.OutputCount++;
				}
			}
			Out.Add(MoveTemp(Info));
		}
		return Out;
	}

	// --- Graph info ---

	struct FGraphInfo
	{
		FString Name;
		FString Type;
		int32 NodeCount = 0;
	};

	TArray<FGraphInfo> CollectGraphs(UBlueprint* BP)
	{
		TArray<FGraphInfo> Out;

		auto AddGraphs = [&](const TArray<TObjectPtr<UEdGraph>>& Graphs, const FString& Type)
		{
			for (const auto& Graph : Graphs)
			{
				if (!Graph) continue;
				FGraphInfo Info;
				Info.Name = Graph->GetName();
				Info.Type = Type;
				Info.NodeCount = Graph->Nodes.Num();
				Out.Add(MoveTemp(Info));
			}
		};

		AddGraphs(BP->UbergraphPages, TEXT("event_graph"));
		AddGraphs(BP->FunctionGraphs, TEXT("function"));
		AddGraphs(BP->MacroGraphs, TEXT("macro"));
		AddGraphs(BP->DelegateSignatureGraphs, TEXT("delegate"));
		return Out;
	}

	// --- Diff helpers ---

	TSharedPtr<FJsonObject> DiffVariables(const TArray<FVarInfo>& A, const TArray<FVarInfo>& B)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

		TMap<FString, const FVarInfo*> MapA, MapB;
		for (const FVarInfo& V : A) MapA.Add(V.Name, &V);
		for (const FVarInfo& V : B) MapB.Add(V.Name, &V);

		TArray<TSharedPtr<FJsonValue>> Added, Removed, Modified;

		// Added in B, not in A
		for (const FVarInfo& V : B)
		{
			if (!MapA.Contains(V.Name))
			{
				Added.Add(MakeShared<FJsonValueObject>(VarInfoToJson(V)));
			}
		}

		// Removed from A, not in B
		for (const FVarInfo& V : A)
		{
			if (!MapB.Contains(V.Name))
			{
				Removed.Add(MakeShared<FJsonValueObject>(VarInfoToJson(V)));
			}
		}

		// Modified: same name, different properties
		for (const FVarInfo& VA : A)
		{
			const FVarInfo** PtrB = MapB.Find(VA.Name);
			if (!PtrB) continue;
			const FVarInfo& VB = **PtrB;

			TArray<TSharedPtr<FJsonValue>> Changes;
			if (VA.Type != VB.Type)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("field"), TEXT("type"));
				C->SetStringField(TEXT("a"), VA.Type);
				C->SetStringField(TEXT("b"), VB.Type);
				Changes.Add(MakeShared<FJsonValueObject>(C));
			}
			if (VA.DefaultValue != VB.DefaultValue)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("field"), TEXT("default_value"));
				C->SetStringField(TEXT("a"), VA.DefaultValue);
				C->SetStringField(TEXT("b"), VB.DefaultValue);
				Changes.Add(MakeShared<FJsonValueObject>(C));
			}
			if (VA.Category != VB.Category)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("field"), TEXT("category"));
				C->SetStringField(TEXT("a"), VA.Category);
				C->SetStringField(TEXT("b"), VB.Category);
				Changes.Add(MakeShared<FJsonValueObject>(C));
			}
			if (VA.bInstanceEditable != VB.bInstanceEditable)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("field"), TEXT("instance_editable"));
				C->SetBoolField(TEXT("a"), VA.bInstanceEditable);
				C->SetBoolField(TEXT("b"), VB.bInstanceEditable);
				Changes.Add(MakeShared<FJsonValueObject>(C));
			}
			if (VA.bReplicated != VB.bReplicated)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("field"), TEXT("replicated"));
				C->SetBoolField(TEXT("a"), VA.bReplicated);
				C->SetBoolField(TEXT("b"), VB.bReplicated);
				Changes.Add(MakeShared<FJsonValueObject>(C));
			}

			if (Changes.Num() > 0)
			{
				TSharedPtr<FJsonObject> Mod = MakeShared<FJsonObject>();
				Mod->SetStringField(TEXT("name"), VA.Name);
				Mod->SetArrayField(TEXT("changes"), Changes);
				Modified.Add(MakeShared<FJsonValueObject>(Mod));
			}
		}

		Result->SetArrayField(TEXT("added"), Added);
		Result->SetArrayField(TEXT("removed"), Removed);
		Result->SetArrayField(TEXT("modified"), Modified);
		return Result;
	}

	TSharedPtr<FJsonObject> DiffComponents(const TArray<FCompInfo>& A, const TArray<FCompInfo>& B)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

		TMap<FString, const FCompInfo*> MapA, MapB;
		for (const FCompInfo& C : A) MapA.Add(C.Name, &C);
		for (const FCompInfo& C : B) MapB.Add(C.Name, &C);

		TArray<TSharedPtr<FJsonValue>> Added, Removed, Modified;

		for (const FCompInfo& C : B)
		{
			if (!MapA.Contains(C.Name))
			{
				TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
				Obj->SetStringField(TEXT("name"), C.Name);
				Obj->SetStringField(TEXT("class"), C.Class);
				Added.Add(MakeShared<FJsonValueObject>(Obj));
			}
		}

		for (const FCompInfo& C : A)
		{
			if (!MapB.Contains(C.Name))
			{
				TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
				Obj->SetStringField(TEXT("name"), C.Name);
				Obj->SetStringField(TEXT("class"), C.Class);
				Removed.Add(MakeShared<FJsonValueObject>(Obj));
			}
		}

		for (const FCompInfo& CA : A)
		{
			const FCompInfo** PtrB = MapB.Find(CA.Name);
			if (!PtrB) continue;
			const FCompInfo& CB = **PtrB;

			if (CA.Class != CB.Class)
			{
				TSharedPtr<FJsonObject> Mod = MakeShared<FJsonObject>();
				Mod->SetStringField(TEXT("name"), CA.Name);
				Mod->SetStringField(TEXT("class_a"), CA.Class);
				Mod->SetStringField(TEXT("class_b"), CB.Class);
				Modified.Add(MakeShared<FJsonValueObject>(Mod));
			}
		}

		Result->SetArrayField(TEXT("added"), Added);
		Result->SetArrayField(TEXT("removed"), Removed);
		Result->SetArrayField(TEXT("modified"), Modified);
		return Result;
	}

	TSharedPtr<FJsonObject> DiffFunctions(const TArray<FFuncInfo>& A, const TArray<FFuncInfo>& B)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

		TSet<FString> NamesA, NamesB;
		for (const FFuncInfo& F : A) NamesA.Add(F.Name);
		for (const FFuncInfo& F : B) NamesB.Add(F.Name);

		TArray<TSharedPtr<FJsonValue>> Added, Removed;

		for (const FString& Name : NamesB)
		{
			if (!NamesA.Contains(Name))
			{
				Added.Add(MakeShared<FJsonValueString>(Name));
			}
		}
		for (const FString& Name : NamesA)
		{
			if (!NamesB.Contains(Name))
			{
				Removed.Add(MakeShared<FJsonValueString>(Name));
			}
		}

		Result->SetArrayField(TEXT("added"), Added);
		Result->SetArrayField(TEXT("removed"), Removed);
		return Result;
	}

	TSharedPtr<FJsonObject> DiffGraphs(const TArray<FGraphInfo>& A, const TArray<FGraphInfo>& B)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

		TMap<FString, const FGraphInfo*> MapA, MapB;
		for (const FGraphInfo& G : A) MapA.Add(G.Name, &G);
		for (const FGraphInfo& G : B) MapB.Add(G.Name, &G);

		TArray<TSharedPtr<FJsonValue>> Added, Removed;
		TSharedPtr<FJsonObject> Shared = MakeShared<FJsonObject>();

		for (const FGraphInfo& G : B)
		{
			if (!MapA.Contains(G.Name))
			{
				TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
				Obj->SetStringField(TEXT("name"), G.Name);
				Obj->SetStringField(TEXT("type"), G.Type);
				Obj->SetNumberField(TEXT("node_count"), G.NodeCount);
				Added.Add(MakeShared<FJsonValueObject>(Obj));
			}
		}
		for (const FGraphInfo& G : A)
		{
			if (!MapB.Contains(G.Name))
			{
				TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
				Obj->SetStringField(TEXT("name"), G.Name);
				Obj->SetStringField(TEXT("type"), G.Type);
				Obj->SetNumberField(TEXT("node_count"), G.NodeCount);
				Removed.Add(MakeShared<FJsonValueObject>(Obj));
			}
		}

		// Shared graphs: compare node counts
		for (const FGraphInfo& GA : A)
		{
			const FGraphInfo** PtrB = MapB.Find(GA.Name);
			if (!PtrB) continue;
			const FGraphInfo& GB = **PtrB;

			TSharedPtr<FJsonObject> GDiff = MakeShared<FJsonObject>();
			GDiff->SetStringField(TEXT("type"), GA.Type);
			GDiff->SetNumberField(TEXT("node_count_a"), GA.NodeCount);
			GDiff->SetNumberField(TEXT("node_count_b"), GB.NodeCount);
			GDiff->SetNumberField(TEXT("node_count_delta"), GB.NodeCount - GA.NodeCount);
			Shared->SetObjectField(GA.Name, GDiff);
		}

		Result->SetArrayField(TEXT("added"), Added);
		Result->SetArrayField(TEXT("removed"), Removed);
		Result->SetObjectField(TEXT("shared"), Shared);
		return Result;
	}
} // anonymous namespace

// ============================================================
//  compare_blueprints
// ============================================================

FMonolithActionResult FMonolithBlueprintDiffActions::HandleCompareBlueprints(const TSharedPtr<FJsonObject>& Params)
{
	FString PathA = Params->GetStringField(TEXT("asset_path_a"));
	FString PathB = Params->GetStringField(TEXT("asset_path_b"));

	if (PathA.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: asset_path_a"));
	}
	if (PathB.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: asset_path_b"));
	}

	UBlueprint* BPA = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(PathA);
	if (!BPA)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint A not found: %s"), *PathA));
	}

	UBlueprint* BPB = FMonolithAssetUtils::LoadAssetByPath<UBlueprint>(PathB);
	if (!BPB)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint B not found: %s"), *PathB));
	}

	// Collect data from both BPs
	TArray<FVarInfo> VarsA = CollectVariables(BPA);
	TArray<FVarInfo> VarsB = CollectVariables(BPB);

	TArray<FCompInfo> CompsA = CollectComponents(BPA);
	TArray<FCompInfo> CompsB = CollectComponents(BPB);

	TArray<FFuncInfo> FuncsA = CollectFunctions(BPA);
	TArray<FFuncInfo> FuncsB = CollectFunctions(BPB);

	TArray<FGraphInfo> GraphsA = CollectGraphs(BPA);
	TArray<FGraphInfo> GraphsB = CollectGraphs(BPB);

	// Diff each section
	TSharedPtr<FJsonObject> VarDiff = DiffVariables(VarsA, VarsB);
	TSharedPtr<FJsonObject> CompDiff = DiffComponents(CompsA, CompsB);
	TSharedPtr<FJsonObject> FuncDiff = DiffFunctions(FuncsA, FuncsB);
	TSharedPtr<FJsonObject> GraphDiff = DiffGraphs(GraphsA, GraphsB);

	// Build summary
	int32 Additions = 0, Removals = 0, Modifications = 0;

	Additions += VarDiff->GetArrayField(TEXT("added")).Num();
	Additions += CompDiff->GetArrayField(TEXT("added")).Num();
	Additions += FuncDiff->GetArrayField(TEXT("added")).Num();
	Additions += GraphDiff->GetArrayField(TEXT("added")).Num();

	Removals += VarDiff->GetArrayField(TEXT("removed")).Num();
	Removals += CompDiff->GetArrayField(TEXT("removed")).Num();
	Removals += FuncDiff->GetArrayField(TEXT("removed")).Num();
	Removals += GraphDiff->GetArrayField(TEXT("removed")).Num();

	Modifications += VarDiff->GetArrayField(TEXT("modified")).Num();
	Modifications += CompDiff->GetArrayField(TEXT("modified")).Num();

	TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
	Summary->SetNumberField(TEXT("total_diffs"), Additions + Removals + Modifications);
	Summary->SetNumberField(TEXT("additions"), Additions);
	Summary->SetNumberField(TEXT("removals"), Removals);
	Summary->SetNumberField(TEXT("modifications"), Modifications);

	// Build result
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path_a"), PathA);
	Root->SetStringField(TEXT("asset_path_b"), PathB);
	Root->SetStringField(TEXT("parent_class_a"), BPA->ParentClass ? BPA->ParentClass->GetName() : TEXT("None"));
	Root->SetStringField(TEXT("parent_class_b"), BPB->ParentClass ? BPB->ParentClass->GetName() : TEXT("None"));
	Root->SetObjectField(TEXT("variables"), VarDiff);
	Root->SetObjectField(TEXT("components"), CompDiff);
	Root->SetObjectField(TEXT("functions"), FuncDiff);
	Root->SetObjectField(TEXT("graphs"), GraphDiff);
	Root->SetObjectField(TEXT("summary"), Summary);

	return FMonolithActionResult::Success(Root);
}
