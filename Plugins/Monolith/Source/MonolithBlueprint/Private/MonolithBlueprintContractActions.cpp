#include "MonolithBlueprintContractActions.h"
#include "MonolithBlueprintInternal.h"
#include "MonolithParamSchema.h"

#include "Engine/Blueprint.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "EdGraphSchema_K2.h"
#include "EdGraph/EdGraphPin.h"
#include "UObject/Class.h"
#include "UObject/UnrealType.h"
#include "UObject/EnumProperty.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithBpContract, Log, All);

// ============================================================
//  Variable-contract extraction + diff
//
//  A "variable descriptor" captures everything that matters for BP-pin /
//  PropertyAccess compatibility of a single member variable:
//    - the base type (bool/int/float/name/struct/enum/object/...)
//    - the container kind (scalar/Array/Set/Map)
//    - the enum subtype  (UEnum path)        — for byte/enum properties
//    - the struct subtype (UScriptStruct path) — for struct properties
//
//  Struct/enum identity is compared by *path* because BP pins compare struct
//  types by exact UScriptStruct pointer identity (see investigation notes:
//  FStructUtils::TheSameLayout is layout-equality, NOT pin compatibility).
// ============================================================
namespace MonolithBpContractInternal
{
	struct FVarDescriptor
	{
		FName    Name;
		FString  BaseType;       // e.g. "bool", "float", "name", "struct", "enum", "object"
		FString  Container;      // "scalar" | "Array" | "Set" | "Map"
		FString  EnumSubtype;    // UEnum path, or empty
		FString  StructSubtype;  // UScriptStruct path, or empty
		FString  ObjectClass;    // PropertyClass path for object/class props, or empty
		FString  MapValueType;   // value descriptor summary for Map props, or empty
		bool     bPresent = false;
	};

	// Map an FProperty's container category to a stable string.
	static FString ContractContainerKind(const FProperty* Prop)
	{
		if (CastField<FArrayProperty>(Prop)) return TEXT("Array");
		if (CastField<FSetProperty>(Prop))   return TEXT("Set");
		if (CastField<FMapProperty>(Prop))   return TEXT("Map");
		return TEXT("scalar");
	}

	// Describe a scalar (non-container) property's base type + subtype fields.
	// Container properties forward their inner/element property here.
	static void ContractDescribeScalar(const FProperty* Prop, FVarDescriptor& Out)
	{
		if (!Prop) { Out.BaseType = TEXT("<null>"); return; }

		if (CastField<FBoolProperty>(Prop))                                  { Out.BaseType = TEXT("bool");   return; }
		if (const FByteProperty* P = CastField<FByteProperty>(Prop))
		{
			// A byte property MAY carry an enum (TEnumAsByte<E> / a UserDefinedEnum
			// referenced as a byte). If it does, this is an enum-typed variable.
			if (P->Enum)
			{
				Out.BaseType    = TEXT("enum");
				Out.EnumSubtype = P->Enum->GetPathName();
			}
			else
			{
				Out.BaseType = TEXT("byte");
			}
			return;
		}
		if (const FEnumProperty* P = CastField<FEnumProperty>(Prop))
		{
			Out.BaseType = TEXT("enum");
			if (const UEnum* E = P->GetEnum())
			{
				Out.EnumSubtype = E->GetPathName();
			}
			return;
		}
		if (CastField<FIntProperty>(Prop))                                  { Out.BaseType = TEXT("int");    return; }
		if (CastField<FInt64Property>(Prop))                                { Out.BaseType = TEXT("int64");  return; }
		if (CastField<FFloatProperty>(Prop))                                { Out.BaseType = TEXT("float");  return; }
		if (CastField<FDoubleProperty>(Prop))                               { Out.BaseType = TEXT("double"); return; }
		if (CastField<FStrProperty>(Prop))                                  { Out.BaseType = TEXT("string"); return; }
		if (CastField<FNameProperty>(Prop))                                 { Out.BaseType = TEXT("name");   return; }
		if (CastField<FTextProperty>(Prop))                                 { Out.BaseType = TEXT("text");   return; }
		if (const FStructProperty* P = CastField<FStructProperty>(Prop))
		{
			Out.BaseType = TEXT("struct");
			if (P->Struct)
			{
				Out.StructSubtype = P->Struct->GetPathName();
			}
			return;
		}
		if (const FClassProperty* P = CastField<FClassProperty>(Prop))
		{
			Out.BaseType = TEXT("class");
			if (P->MetaClass) Out.ObjectClass = P->MetaClass->GetPathName();
			return;
		}
		if (const FObjectPropertyBase* P = CastField<FObjectPropertyBase>(Prop))
		{
			Out.BaseType = TEXT("object");
			if (P->PropertyClass) Out.ObjectClass = P->PropertyClass->GetPathName();
			return;
		}

		// Fallback: use the engine's CPP-type string for anything not special-cased.
		Out.BaseType = Prop->GetCPPType(nullptr, 0u);
	}

	// Describe the *base type* of a pin (category + sub-category-object) into the
	// descriptor's BaseType/EnumSubtype/StructSubtype/ObjectClass fields. Used for
	// both the scalar case and the inner type of a container pin. Normalizes to the
	// SAME base-type vocabulary as ContractDescribeScalar (the FProperty path) so a
	// Blueprint side and a native side compare apples-to-apples.
	static void ContractDescribePinBase(
		const FName& Category, const FString& SubCategory, UObject* SubObject, FVarDescriptor& Out)
	{
		if (Category == UEdGraphSchema_K2::PC_Boolean)      { Out.BaseType = TEXT("bool");   return; }
		if (Category == UEdGraphSchema_K2::PC_Int)          { Out.BaseType = TEXT("int");    return; }
		if (Category == UEdGraphSchema_K2::PC_Int64)        { Out.BaseType = TEXT("int64");  return; }
		if (Category == UEdGraphSchema_K2::PC_Real)
		{
			Out.BaseType = (SubCategory == TEXT("double")) ? TEXT("double") : TEXT("float");
			return;
		}
		if (Category == UEdGraphSchema_K2::PC_String)       { Out.BaseType = TEXT("string"); return; }
		if (Category == UEdGraphSchema_K2::PC_Name)         { Out.BaseType = TEXT("name");   return; }
		if (Category == UEdGraphSchema_K2::PC_Text)         { Out.BaseType = TEXT("text");   return; }
		if (Category == UEdGraphSchema_K2::PC_Byte || Category == UEdGraphSchema_K2::PC_Enum)
		{
			// A byte pin MAY carry an enum sub-object; an enum pin always does. Either
			// way, an enum-typed variable is reported as "enum" with the UEnum path so
			// it matches the FEnumProperty / FByteProperty(with Enum) native paths.
			if (UEnum* E = Cast<UEnum>(SubObject))
			{
				Out.BaseType    = TEXT("enum");
				Out.EnumSubtype = E->GetPathName();
			}
			else
			{
				Out.BaseType = TEXT("byte");
			}
			return;
		}
		if (Category == UEdGraphSchema_K2::PC_Struct)
		{
			Out.BaseType = TEXT("struct");
			if (UScriptStruct* S = Cast<UScriptStruct>(SubObject)) Out.StructSubtype = S->GetPathName();
			return;
		}
		if (Category == UEdGraphSchema_K2::PC_Class || Category == UEdGraphSchema_K2::PC_SoftClass)
		{
			Out.BaseType = TEXT("class");
			if (UClass* C = Cast<UClass>(SubObject)) Out.ObjectClass = C->GetPathName();
			return;
		}
		if (Category == UEdGraphSchema_K2::PC_Object || Category == UEdGraphSchema_K2::PC_SoftObject ||
			Category == UEdGraphSchema_K2::PC_Interface)
		{
			Out.BaseType = TEXT("object");
			if (UClass* C = Cast<UClass>(SubObject)) Out.ObjectClass = C->GetPathName();
			return;
		}
		Out.BaseType = Category.ToString();
	}

	// Build a descriptor from a Blueprint variable's authoritative FEdGraphPinType.
	// Preferred over the compiled-FProperty path for Blueprint-local variables: the
	// KismetCompiler can lower a UserDefinedEnum (PC_Enum) pin to a plain FIntProperty
	// on the generated class, which would hide enum-subtype mismatches the AnimGraph /
	// chooser pins actually see. The pin type is what BP bindings compare against.
	static FVarDescriptor ContractDescribeFromPinType(const FName& Name, const FEdGraphPinType& PinType)
	{
		FVarDescriptor D;
		D.bPresent = true;
		D.Name = Name;

		switch (PinType.ContainerType)
		{
		case EPinContainerType::Array: D.Container = TEXT("Array"); break;
		case EPinContainerType::Set:   D.Container = TEXT("Set");   break;
		case EPinContainerType::Map:   D.Container = TEXT("Map");   break;
		default:                       D.Container = TEXT("scalar"); break;
		}

		ContractDescribePinBase(PinType.PinCategory, PinType.PinSubCategory.ToString(),
			PinType.PinSubCategoryObject.Get(), D);

		// Map value type → summary string (mirrors the FProperty map path).
		if (PinType.ContainerType == EPinContainerType::Map)
		{
			FVarDescriptor ValDesc;
			ContractDescribePinBase(PinType.PinValueType.TerminalCategory,
				PinType.PinValueType.TerminalSubCategory.ToString(),
				PinType.PinValueType.TerminalSubCategoryObject.Get(), ValDesc);
			D.MapValueType = ValDesc.BaseType;
			if (!ValDesc.StructSubtype.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.StructSubtype;
			else if (!ValDesc.EnumSubtype.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.EnumSubtype;
			else if (!ValDesc.ObjectClass.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.ObjectClass;
		}
		return D;
	}

	// Build a full descriptor (base + container + subtype) for a member property.
	static FVarDescriptor ContractDescribeProperty(const FProperty* Prop)
	{
		FVarDescriptor D;
		D.bPresent = true;
		D.Name      = Prop->GetFName();
		D.Container = ContractContainerKind(Prop);

		if (const FArrayProperty* Arr = CastField<FArrayProperty>(Prop))
		{
			ContractDescribeScalar(Arr->Inner, D);
		}
		else if (const FSetProperty* Set = CastField<FSetProperty>(Prop))
		{
			ContractDescribeScalar(Set->ElementProp, D);
		}
		else if (const FMapProperty* Map = CastField<FMapProperty>(Prop))
		{
			// Key type drives the primary descriptor; value type captured separately.
			ContractDescribeScalar(Map->KeyProp, D);
			FVarDescriptor ValDesc;
			ContractDescribeScalar(Map->ValueProp, ValDesc);
			D.MapValueType = ValDesc.BaseType;
			if (!ValDesc.StructSubtype.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.StructSubtype;
			else if (!ValDesc.EnumSubtype.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.EnumSubtype;
			else if (!ValDesc.ObjectClass.IsEmpty()) D.MapValueType += TEXT(":") + ValDesc.ObjectClass;
		}
		else
		{
			ContractDescribeScalar(Prop, D);
		}
		return D;
	}

	// Resolve a "side" string into a UStruct* to iterate properties over.
	// Accepts a Blueprint asset path (→ GeneratedClass) or a native class name
	// (as-is, then with U/A prefixes, then a full /Script/... path).
	// OutKind describes what resolved ("blueprint" | "native_class").
	static UStruct* ContractResolveSide(const FString& Side, UClass*& OutClass, UBlueprint*& OutBP, FString& OutKind, FString& OutError)
	{
		OutClass = nullptr;
		OutBP = nullptr;
		OutKind.Reset();

		// Blueprint asset path first (paths contain '/').
		if (Side.Contains(TEXT("/")))
		{
			TSharedPtr<FJsonObject> Synthetic = MakeShared<FJsonObject>();
			Synthetic->SetStringField(TEXT("asset_path"), Side);
			FString Resolved;
			if (UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Synthetic, Resolved))
			{
				if (!BP->GeneratedClass)
				{
					OutError = FString::Printf(TEXT("Blueprint '%s' has no GeneratedClass (needs compile)."), *Side);
					return nullptr;
				}
				OutBP = BP;
				OutClass = BP->GeneratedClass;
				OutKind = TEXT("blueprint");
				return OutClass;
			}
		}

		// Native class name resolution (mirrors MonolithBlueprintStructActions resolver).
		UClass* Resolved = FindFirstObject<UClass>(*Side, EFindFirstObjectOptions::NativeFirst);
		if (!Resolved && !Side.StartsWith(TEXT("U")))
		{
			Resolved = FindFirstObject<UClass>(*(TEXT("U") + Side), EFindFirstObjectOptions::NativeFirst);
		}
		if (!Resolved && !Side.StartsWith(TEXT("A")))
		{
			Resolved = FindFirstObject<UClass>(*(TEXT("A") + Side), EFindFirstObjectOptions::NativeFirst);
		}
		if (!Resolved && Side.Len() > 1 && (Side.StartsWith(TEXT("U")) || Side.StartsWith(TEXT("A"))))
		{
			Resolved = FindFirstObject<UClass>(*Side.Mid(1), EFindFirstObjectOptions::NativeFirst);
		}
		if (!Resolved)
		{
			OutError = FString::Printf(
				TEXT("Could not resolve '%s' as a Blueprint asset path or a native class name "
				     "(tried as-is, with U/A prefix added/stripped). Use a full path for disambiguation."),
				*Side);
			return nullptr;
		}
		OutClass = Resolved;
		OutKind = TEXT("native_class");
		return Resolved;
	}

	// Collect descriptors for all member properties on a UStruct, keyed by name.
	// bIncludeInherited=false restricts to properties declared directly on Struct
	// (TFieldIterator with EFieldIteratorFlags::ExcludeSuper).
	//
	// When OptionalBP is non-null, the Blueprint's NewVariables[].VarType (the
	// authoritative pin type) OVERRIDES the compiled-FProperty descriptor for each
	// BP-local variable. This is essential for enum-typed vars: the KismetCompiler
	// can lower a UserDefinedEnum pin to a plain FIntProperty on the generated class,
	// which would otherwise mask enum-subtype mismatches that BP bindings see.
	static void ContractCollect(UStruct* Struct, bool bIncludeInherited, UBlueprint* OptionalBP, TMap<FName, FVarDescriptor>& Out)
	{
		if (!Struct) return;
		const EFieldIteratorFlags::SuperClassFlags SuperFlags = bIncludeInherited
			? EFieldIteratorFlags::IncludeSuper
			: EFieldIteratorFlags::ExcludeSuper;
		for (TFieldIterator<FProperty> It(Struct, SuperFlags); It; ++It)
		{
			FProperty* Prop = *It;
			if (!Prop) continue;
			FVarDescriptor D = ContractDescribeProperty(Prop);
			Out.Add(D.Name, D);
		}

		// Overlay authoritative pin types for BP-local member variables.
		if (OptionalBP)
		{
			for (const FBPVariableDescription& Var : OptionalBP->NewVariables)
			{
				Out.Add(Var.VarName, ContractDescribeFromPinType(Var.VarName, Var.VarType));
			}
		}
	}

	// Serialize a descriptor into a JSON object (presence + type fields).
	static TSharedPtr<FJsonObject> ContractDescriptorToJson(const FVarDescriptor& D)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetBoolField(TEXT("present"), D.bPresent);
		if (D.bPresent)
		{
			Obj->SetStringField(TEXT("base_type"), D.BaseType);
			Obj->SetStringField(TEXT("container"), D.Container);
			if (!D.EnumSubtype.IsEmpty())   Obj->SetStringField(TEXT("enum_subtype"), D.EnumSubtype);
			if (!D.StructSubtype.IsEmpty()) Obj->SetStringField(TEXT("struct_subtype"), D.StructSubtype);
			if (!D.ObjectClass.IsEmpty())   Obj->SetStringField(TEXT("object_class"), D.ObjectClass);
			if (!D.MapValueType.IsEmpty())  Obj->SetStringField(TEXT("map_value_type"), D.MapValueType);
		}
		return Obj;
	}

	// Classify the mismatch between a left and right descriptor for the same name.
	// "left" is the first side; "right" the second. Returns one of:
	//   ok | missing-on-left | missing-on-right | type-mismatch |
	//   container-mismatch | enum-subtype-mismatch | struct-subtype-mismatch
	static FString ContractClassify(const FVarDescriptor& L, const FVarDescriptor& R)
	{
		if (!L.bPresent && !R.bPresent) return TEXT("ok"); // unreachable in practice
		if (!L.bPresent) return TEXT("missing-on-left");
		if (!R.bPresent) return TEXT("missing-on-right");

		// Container kind first — scalar-vs-array was a Phase-2a bug class.
		if (L.Container != R.Container) return TEXT("container-mismatch");

		// Base type next.
		if (L.BaseType != R.BaseType) return TEXT("type-mismatch");

		// Subtype identity (path equality). Struct/enum identity is what BP pins
		// actually compare against, so a base-type match is insufficient.
		if (L.BaseType == TEXT("enum") && L.EnumSubtype != R.EnumSubtype)
			return TEXT("enum-subtype-mismatch");
		if (L.BaseType == TEXT("struct") && L.StructSubtype != R.StructSubtype)
			return TEXT("struct-subtype-mismatch");
		if ((L.BaseType == TEXT("object") || L.BaseType == TEXT("class")) && L.ObjectClass != R.ObjectClass)
			return TEXT("type-mismatch");
		if (L.Container == TEXT("Map") && L.MapValueType != R.MapValueType)
			return TEXT("type-mismatch");

		return TEXT("ok");
	}

	// Build the structured diff between two descriptor maps. Emits one entry per
	// variable present on either side, plus a summary roll-up.
	static void ContractBuildDiff(
		const TMap<FName, FVarDescriptor>& Left,
		const TMap<FName, FVarDescriptor>& Right,
		const FString& LeftLabel,
		const FString& RightLabel,
		TSharedPtr<FJsonObject>& OutRoot)
	{
		TSet<FName> AllNames;
		for (const auto& KV : Left)  AllNames.Add(KV.Key);
		for (const auto& KV : Right) AllNames.Add(KV.Key);

		TArray<FName> Sorted = AllNames.Array();
		Sorted.Sort([](const FName& A, const FName& B) { return A.LexicalLess(B); });

		TArray<TSharedPtr<FJsonValue>> VarsArr;
		int32 OkCount = 0, MismatchCount = 0;
		for (const FName& Name : Sorted)
		{
			const FVarDescriptor* L = Left.Find(Name);
			const FVarDescriptor* R = Right.Find(Name);
			FVarDescriptor LD = L ? *L : FVarDescriptor{};
			FVarDescriptor RD = R ? *R : FVarDescriptor{};

			const FString Mismatch = ContractClassify(LD, RD);
			if (Mismatch == TEXT("ok")) ++OkCount; else ++MismatchCount;

			TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
			Entry->SetStringField(TEXT("name"), Name.ToString());
			Entry->SetStringField(TEXT("mismatch"), Mismatch);
			Entry->SetObjectField(TEXT("left"), ContractDescriptorToJson(LD));
			Entry->SetObjectField(TEXT("right"), ContractDescriptorToJson(RD));
			VarsArr.Add(MakeShared<FJsonValueObject>(Entry));
		}

		OutRoot->SetStringField(TEXT("left_label"), LeftLabel);
		OutRoot->SetStringField(TEXT("right_label"), RightLabel);
		OutRoot->SetArrayField(TEXT("variables"), VarsArr);

		TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
		Summary->SetNumberField(TEXT("total"), Sorted.Num());
		Summary->SetNumberField(TEXT("ok"), OkCount);
		Summary->SetNumberField(TEXT("mismatch"), MismatchCount);
		OutRoot->SetObjectField(TEXT("summary"), Summary);
	}
} // namespace MonolithBpContractInternal

// ============================================================
//  Registration
// ============================================================

void FMonolithBlueprintContractActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("blueprint"), TEXT("compare_class_variable_contract"),
		TEXT("Diff the member-variable contract of two classes/Blueprints by name+type+container(scalar/Array/Set/Map)"
		     "+enum-subtype+struct-subtype. Each side is a Blueprint asset path or a native class name. Emits a per-variable "
		     "mismatch classification (ok, missing-on-left, missing-on-right, type-mismatch, container-mismatch, "
		     "enum-subtype-mismatch, struct-subtype-mismatch). Pure read/report — mutates nothing."),
		FMonolithActionHandler::CreateStatic(&HandleCompareClassVariableContract),
		FParamSchemaBuilder()
			.Required(TEXT("left"),  TEXT("string"), TEXT("First side: Blueprint asset path (/Game/...) or native class name"), {TEXT("blueprint"), TEXT("left_class")})
			.Required(TEXT("right"), TEXT("string"), TEXT("Second side: Blueprint asset path (/Game/...) or native class name"), {TEXT("parent"), TEXT("right_class")})
			.Optional(TEXT("include_inherited"), TEXT("boolean"), TEXT("Include inherited (super-class) properties on each side (default: false — direct members only)"), TEXT("false"))
			.Optional(TEXT("variables"), TEXT("array"), TEXT("Restrict the diff to this set of variable names (default: all)"))
			.Build());

	Registry.RegisterAction(TEXT("blueprint"), TEXT("promote_variables_to_parent"),
		TEXT("Reconcile a Blueprint's named local variables against its NATIVE parent class contract. "
		     "verify (default): report which variables the native parent already satisfies (name+type+container+enum/struct parity) "
		     "vs which it does not yet declare compatibly. remove_shadowed: delete the now-shadowed BP-local duplicate ONLY for "
		     "variables the native parent already satisfies (so graph nodes rebind to the parent). Never authors C++."),
		FMonolithActionHandler::CreateStatic(&HandlePromoteVariablesToParent),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Blueprint asset path"))
			.Required(TEXT("variables"), TEXT("array"), TEXT("Variable names to reconcile against the native parent contract"))
			.Optional(TEXT("mode"), TEXT("string"), TEXT("verify (default) | remove_shadowed"), TEXT("verify"))
			.Build());

	UE_LOG(LogMonolithBpContract, Log, TEXT("MonolithBlueprint Contract: registered 2 actions"));
}

// ============================================================
//  compare_class_variable_contract  (#2 — the diff engine)
// ============================================================

FMonolithActionResult FMonolithBlueprintContractActions::HandleCompareClassVariableContract(const TSharedPtr<FJsonObject>& Params)
{
	using namespace MonolithBpContractInternal;

	const FString LeftSide  = Params->GetStringField(TEXT("left"));
	const FString RightSide = Params->GetStringField(TEXT("right"));
	if (LeftSide.IsEmpty())  return FMonolithActionResult::Error(TEXT("Missing required parameter: left"));
	if (RightSide.IsEmpty()) return FMonolithActionResult::Error(TEXT("Missing required parameter: right"));

	bool bIncludeInherited = false;
	Params->TryGetBoolField(TEXT("include_inherited"), bIncludeInherited);

	UClass* LeftClass = nullptr; UBlueprint* LeftBP = nullptr; FString LeftKind, LeftErr;
	UStruct* LeftStruct = ContractResolveSide(LeftSide, LeftClass, LeftBP, LeftKind, LeftErr);
	if (!LeftStruct) return FMonolithActionResult::Error(LeftErr);

	UClass* RightClass = nullptr; UBlueprint* RightBP = nullptr; FString RightKind, RightErr;
	UStruct* RightStruct = ContractResolveSide(RightSide, RightClass, RightBP, RightKind, RightErr);
	if (!RightStruct) return FMonolithActionResult::Error(RightErr);

	TMap<FName, FVarDescriptor> LeftMap, RightMap;
	ContractCollect(LeftStruct, bIncludeInherited, LeftBP, LeftMap);
	ContractCollect(RightStruct, bIncludeInherited, RightBP, RightMap);

	// Optional restriction to a named subset.
	const TArray<TSharedPtr<FJsonValue>>* RequestedVars = nullptr;
	if (Params->TryGetArrayField(TEXT("variables"), RequestedVars) && RequestedVars && RequestedVars->Num() > 0)
	{
		TSet<FName> Keep;
		for (const TSharedPtr<FJsonValue>& V : *RequestedVars)
		{
			FString N;
			if (V.IsValid() && V->TryGetString(N) && !N.IsEmpty()) Keep.Add(FName(*N));
		}
		for (auto It = LeftMap.CreateIterator();  It; ++It) { if (!Keep.Contains(It.Key())) It.RemoveCurrent(); }
		for (auto It = RightMap.CreateIterator(); It; ++It) { if (!Keep.Contains(It.Key())) It.RemoveCurrent(); }
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("left_kind"), LeftKind);
	Root->SetStringField(TEXT("right_kind"), RightKind);
	Root->SetStringField(TEXT("left_resolved"), LeftStruct->GetPathName());
	Root->SetStringField(TEXT("right_resolved"), RightStruct->GetPathName());
	ContractBuildDiff(LeftMap, RightMap, LeftSide, RightSide, Root);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}

// ============================================================
//  promote_variables_to_parent  (#1 — reuses the #2 diff engine)
// ============================================================

FMonolithActionResult FMonolithBlueprintContractActions::HandlePromoteVariablesToParent(const TSharedPtr<FJsonObject>& Params)
{
	using namespace MonolithBpContractInternal;

	FString AssetPath;
	UBlueprint* BP = MonolithBlueprintInternal::LoadBlueprintFromParams(Params, AssetPath);
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint not found: %s"), *AssetPath));
	}
	if (!BP->GeneratedClass)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint '%s' has no GeneratedClass (needs compile)."), *AssetPath));
	}

	// Resolve the NATIVE parent class. ParentClass is the immediate parent; walk
	// up until we hit a native (non-BP-generated) class — that is the contract the
	// promoted variables must be authored onto.
	UClass* NativeParent = BP->ParentClass;
	while (NativeParent && NativeParent->ClassGeneratedBy != nullptr)
	{
		NativeParent = NativeParent->GetSuperClass();
	}
	if (!NativeParent)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Blueprint '%s' has no resolvable native parent class."), *AssetPath));
	}

	// Collect the requested variable names.
	const TArray<TSharedPtr<FJsonValue>>* RequestedVars = nullptr;
	if (!Params->TryGetArrayField(TEXT("variables"), RequestedVars) || !RequestedVars || RequestedVars->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: variables (non-empty array of names)"));
	}
	TArray<FName> WantNames;
	for (const TSharedPtr<FJsonValue>& V : *RequestedVars)
	{
		FString N;
		if (V.IsValid() && V->TryGetString(N) && !N.IsEmpty()) WantNames.Add(FName(*N));
	}

	FString Mode = Params->GetStringField(TEXT("mode"));
	if (Mode.IsEmpty()) Mode = TEXT("verify");
	if (Mode != TEXT("verify") && Mode != TEXT("remove_shadowed"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unknown mode '%s'. Valid: verify, remove_shadowed."), *Mode));
	}

	// Build descriptor maps. BP side = the BP-local member variables (direct).
	// Parent side = the full native-parent contract (include inherited so a var
	// satisfied on a grandparent still counts).
	TMap<FName, FVarDescriptor> BpMap, ParentMap;
	ContractCollect(BP->GeneratedClass, /*bIncludeInherited=*/false, /*OptionalBP=*/BP, BpMap);
	ContractCollect(NativeParent, /*bIncludeInherited=*/true, /*OptionalBP=*/nullptr, ParentMap);

	TArray<TSharedPtr<FJsonValue>> ResultsArr;
	int32 SatisfiedCount = 0, UnsatisfiedCount = 0, RemovedCount = 0;
	TArray<FName> ToRemove;

	for (const FName& Name : WantNames)
	{
		const FVarDescriptor* BpDesc     = BpMap.Find(Name);
		const FVarDescriptor* ParentDesc = ParentMap.Find(Name);

		FVarDescriptor LD = BpDesc ? *BpDesc : FVarDescriptor{};
		FVarDescriptor RD = ParentDesc ? *ParentDesc : FVarDescriptor{};
		const FString Mismatch = ContractClassify(LD, RD);

		// Parity = the BP var exists AND the parent declares a compatible counterpart.
		const bool bParentDeclares = ParentDesc != nullptr;
		const bool bParity = BpDesc && ParentDesc && (Mismatch == TEXT("ok"));

		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("name"), Name.ToString());
		Entry->SetBoolField(TEXT("on_blueprint"), BpDesc != nullptr);
		Entry->SetBoolField(TEXT("parent_declares"), bParentDeclares);
		Entry->SetStringField(TEXT("mismatch"), Mismatch);
		Entry->SetObjectField(TEXT("blueprint"), ContractDescriptorToJson(LD));
		Entry->SetObjectField(TEXT("parent"), ContractDescriptorToJson(RD));

		if (bParity)
		{
			++SatisfiedCount;
			Entry->SetStringField(TEXT("status"), TEXT("parent-satisfies"));
			if (Mode == TEXT("remove_shadowed") && BpDesc)
			{
				// Removal-safety gate: only delete vars that are genuinely BP-local
				// member variables (present in NewVariables). A var that resolved as a
				// direct GeneratedClass property but is NOT in NewVariables is not a
				// hand-authored member var and must not be touched.
				const bool bIsLocalMemberVar = BP->NewVariables.ContainsByPredicate(
					[&Name](const FBPVariableDescription& Desc) { return Desc.VarName == Name; });
				if (bIsLocalMemberVar)
				{
					ToRemove.Add(Name);
					Entry->SetBoolField(TEXT("will_remove"), true);
				}
				else
				{
					Entry->SetBoolField(TEXT("will_remove"), false);
					Entry->SetStringField(TEXT("remove_skipped_reason"),
						TEXT("not a BP-local member variable (NewVariables)"));
				}
			}
		}
		else
		{
			++UnsatisfiedCount;
			Entry->SetStringField(TEXT("status"),
				bParentDeclares ? TEXT("parent-declares-but-mismatch") : TEXT("parent-missing"));
		}
		ResultsArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	// remove_shadowed: delete the now-redundant BP-local duplicates. Only the
	// parity-passing variables reach ToRemove — never a var the parent lacks or
	// declares incompatibly (which would orphan graph bindings).
	if (Mode == TEXT("remove_shadowed") && ToRemove.Num() > 0)
	{
		for (const FName& Name : ToRemove)
		{
			FBlueprintEditorUtils::RemoveMemberVariable(BP, Name);
			++RemovedCount;
		}
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), AssetPath);
	Root->SetStringField(TEXT("native_parent"), NativeParent->GetPathName());
	Root->SetStringField(TEXT("mode"), Mode);
	Root->SetArrayField(TEXT("variables"), ResultsArr);

	TSharedPtr<FJsonObject> Summary = MakeShared<FJsonObject>();
	Summary->SetNumberField(TEXT("requested"), WantNames.Num());
	Summary->SetNumberField(TEXT("parent_satisfies"), SatisfiedCount);
	Summary->SetNumberField(TEXT("not_satisfied"), UnsatisfiedCount);
	Summary->SetNumberField(TEXT("removed_shadowed"), RemovedCount);
	Root->SetObjectField(TEXT("summary"), Summary);
	Root->SetBoolField(TEXT("success"), true);
	return FMonolithActionResult::Success(Root);
}
