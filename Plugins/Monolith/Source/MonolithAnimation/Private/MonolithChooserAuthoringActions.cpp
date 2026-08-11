#include "MonolithChooserAuthoringActions.h"
#include "MonolithParamSchema.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#if WITH_CHOOSER
#include "MonolithAssetUtils.h"

// Chooser runtime headers. Chooser.Build.cs adds its Internal/ dir to
// PublicIncludePaths, so the Internal table/column headers are reachable for any
// module taking the "Chooser" dependency (same as MonolithChooserActions.cpp).
#include "Chooser.h"                 // UChooserTable (Internal, on public include path)
#include "ChooserSignature.h"        // UChooserSignature (ResultType/OutputObjectType/ContextData)
#include "ObjectChooser_Asset.h"     // FAssetChooser (Internal, public path) — result rows
#include "OutputObjectColumn.h"      // FOutputObjectColumn / FChooserOutputObjectRowData
#include "BoolColumn.h"              // FBoolColumn / EBoolColumnCellValue
#include "EnumColumn.h"              // FEnumColumn / FChooserEnumRowData / EEnumColumnCellValueComparison
#include "GameplayTagColumn.h"       // FGameplayTagColumn (RowValues: FGameplayTagContainer)
#include "FloatRangeColumn.h"        // FFloatRangeColumn / FChooserFloatRangeRowData
#include "ChooserPropertyAccess.h"   // FChooserPropertyBinding (input binding chain)
#include "IHasContext.h"             // EObjectChooserResultType

#include "StructUtils/InstancedStruct.h"
#include "GameplayTagContainer.h"
#include "GameplayTagsManager.h"
#include "UObject/Class.h"
#include "Editor.h"
#endif // WITH_CHOOSER

// ---------------------------------------------------------------------------
// Registration (always registers; per-handler gating below)
// ---------------------------------------------------------------------------

void FMonolithChooserAuthoringActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// --- create_chooser_table ---
	Registry.RegisterAction(TEXT("chooser"), TEXT("create_chooser_table"),
		TEXT("Create a new UChooserTable asset. Sets the result type (Object/Class/NoPrimaryResult, default Object) and an optional output object class + an optional context object class parameter. Marks the package dirty."),
		FMonolithActionHandler::CreateStatic(&HandleCreateChooserTable),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Asset path for the new UChooserTable"))
			.Optional(TEXT("output_type"), TEXT("string"), TEXT("Result type: ObjectResult (default) / ClassResult / NoPrimaryResult. 'Object' is accepted as an alias for ObjectResult."), TEXT("Object"))
			.Optional(TEXT("output_class"), TEXT("string"), TEXT("Optional output object class (the Result Class), e.g. /Game/.../ABP.ABP_C or PoseSearchDatabase"))
			.Optional(TEXT("context_class"), TEXT("string"), TEXT("Optional context object class added as a FContextObjectTypeClass parameter, e.g. ABP_Humanoid_C"))
			.Build());

	// --- add_chooser_column ---
	Registry.RegisterAction(TEXT("chooser"), TEXT("add_chooser_column"),
		TEXT("Append a column to a UChooserTable. column_kind is Bool / Enum / GameplayTag / FloatRange / OutputObject. For input (filter) columns an optional binding_property dotted path sets the InputValue property-binding chain. CRITICAL: the new column's per-row value array is grown to the table's current row count so all parallel arrays stay aligned. Marks the package dirty."),
		FMonolithActionHandler::CreateStatic(&HandleAddChooserColumn),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("UChooserTable asset path"))
			.Required(TEXT("column_kind"), TEXT("string"), TEXT("Bool | Enum | GameplayTag | FloatRange | OutputObject"))
			.Optional(TEXT("binding_property"), TEXT("string"), TEXT("Optional dotted property path for the input binding chain (e.g. 'bIsCrouching' or 'Movement.Speed'). Input columns only."))
			.Optional(TEXT("enum_class"), TEXT("string"), TEXT("Enum columns only: full path or bare short name of the UEnum this column filters (e.g. '/Script/MyModule.EStance' or 'EStance'). Sets the editor-side enum binding so cell values display/validate against this enum."))
			.Build());

	// --- add_chooser_row ---
	Registry.RegisterAction(TEXT("chooser"), TEXT("add_chooser_row"),
		TEXT("Append a row to a UChooserTable. cells is one entry per INPUT (filter) column, in column order (Bool: true/false/any; Enum: int value; FloatRange: {min,max}; GameplayTag: tag string). output_psd is the asset the row selects (written as an FAssetChooser result). HIGHEST risk: every parallel array (each input column's per-row value array, each OutputObject column's RowValues, ResultsStructs, DisabledRows) grows by EXACTLY 1 atomically. Marks the package dirty."),
		FMonolithActionHandler::CreateStatic(&HandleAddChooserRow),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("UChooserTable asset path"))
			.Required(TEXT("cells"), TEXT("array"), TEXT("One cell per INPUT column in column order. Bool: bool or 'any'; Enum: integer; FloatRange: {min:number,max:number}; GameplayTag: tag string."))
			.RequiredAssetPath(TEXT("output_psd"), TEXT("Asset this row selects (e.g. a PoseSearch database). Written as an FAssetChooser result row."))
			.Build());

	// --- set_chooser_cell ---
	Registry.RegisterAction(TEXT("chooser"), TEXT("set_chooser_cell"),
		TEXT("Set a typed predicate value into a specific (column_index, row_index) cell of a UChooserTable. The accepted value fields depend on the column's concrete kind: Bool -> bool_value (bool) or 'any'; Enum -> enum_value (integer) [+ optional comparison: MatchEqual/MatchNotEqual/MatchAny]; FloatRange -> float_min + float_max (numbers); GameplayTag -> tags (string or array of tag strings). Both indices are validated in range. Marks the package dirty."),
		FMonolithActionHandler::CreateStatic(&HandleSetChooserCell),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("UChooserTable asset path"))
			.Required(TEXT("column_index"), TEXT("number"), TEXT("Zero-based index into ColumnsStructs"))
			.Required(TEXT("row_index"), TEXT("number"), TEXT("Zero-based row index (must be < row count)"))
			.Optional(TEXT("bool_value"), TEXT("bool"), TEXT("Bool column: cell value (true/false). Omit and pass 'any' via this field as a string to match-any."))
			.Optional(TEXT("enum_value"), TEXT("number"), TEXT("Enum column: raw integer enum value"))
			.Optional(TEXT("comparison"), TEXT("string"), TEXT("Enum column: MatchEqual (default) / MatchNotEqual / MatchAny"))
			.Optional(TEXT("float_min"), TEXT("number"), TEXT("FloatRange column: inclusive minimum"))
			.Optional(TEXT("float_max"), TEXT("number"), TEXT("FloatRange column: inclusive maximum"))
			.Optional(TEXT("tags"), TEXT("array"), TEXT("GameplayTag column: a single tag string or an array of tag strings"))
			.Build());
}

// ===========================================================================
// WITH_CHOOSER == 0 : clean off-gate stubs (mirrors MonolithChooserActions.cpp:99-105)
// ===========================================================================
#if !WITH_CHOOSER

namespace
{
	FMonolithActionResult ChooserAuthoringUnavailable()
	{
		return FMonolithActionResult::Error(TEXT("Chooser plugin not available"));
	}
}

FMonolithActionResult FMonolithChooserAuthoringActions::HandleCreateChooserTable(const TSharedPtr<FJsonObject>&) { return ChooserAuthoringUnavailable(); }
FMonolithActionResult FMonolithChooserAuthoringActions::HandleAddChooserColumn(const TSharedPtr<FJsonObject>&)  { return ChooserAuthoringUnavailable(); }
FMonolithActionResult FMonolithChooserAuthoringActions::HandleAddChooserRow(const TSharedPtr<FJsonObject>&)     { return ChooserAuthoringUnavailable(); }
FMonolithActionResult FMonolithChooserAuthoringActions::HandleSetChooserCell(const TSharedPtr<FJsonObject>&)   { return ChooserAuthoringUnavailable(); }

#else // WITH_CHOOSER

// ===========================================================================
// Helpers (file-local)
// ===========================================================================

namespace
{
	/** Resolve an output_type string (case-insensitive) to the result-type enum. */
	bool ParseChooserResultType(const FString& Str, EObjectChooserResultType& Out)
	{
		if (Str.Equals(TEXT("Object"),          ESearchCase::IgnoreCase) ||
			Str.Equals(TEXT("ObjectResult"),    ESearchCase::IgnoreCase)) { Out = EObjectChooserResultType::ObjectResult;    return true; }
		if (Str.Equals(TEXT("Class"),           ESearchCase::IgnoreCase) ||
			Str.Equals(TEXT("ClassResult"),     ESearchCase::IgnoreCase)) { Out = EObjectChooserResultType::ClassResult;     return true; }
		if (Str.Equals(TEXT("NoPrimaryResult"), ESearchCase::IgnoreCase) ||
			Str.Equals(TEXT("None"),            ESearchCase::IgnoreCase)) { Out = EObjectChooserResultType::NoPrimaryResult; return true; }
		return false;
	}

	/**
	 * Resolve a UClass from a user string that may be either a full object path
	 * (e.g. "/Script/PoseSearch.PoseSearchDatabase" or "/Game/.../ABP.ABP_C") or a
	 * bare short name (e.g. "PoseSearchDatabase"). Tries, in order:
	 *   1. LoadClass / LoadObject for explicit paths and BP _C generated classes;
	 *   2. FindFirstObject<UClass>(NativeFirst) for a bare native class short name;
	 *   3. the same on the string with a leading 'U'/'A' stripped (callers may pass
	 *      "PoseSearchDatabase" for class UPoseSearchDatabase).
	 * Returns nullptr if nothing resolves (callers leave the type as-is, no error).
	 */
	UClass* ResolveClassByNameOrPath(const FString& InStr)
	{
		if (InStr.IsEmpty())
		{
			return nullptr;
		}

		// 1. Explicit path forms first (full /Script/... or /Game/... _C path).
		if (UClass* Loaded = LoadClass<UObject>(nullptr, *InStr))
		{
			return Loaded;
		}
		if (UClass* Loaded = LoadObject<UClass>(nullptr, *InStr))
		{
			return Loaded;
		}

		// 2. Bare short name — search loaded UClass objects, native first. This is
		//    the engine-canonical short-name->UClass path (NativeFirst avoids
		//    matching a BP skeleton/reinstanced class).
		if (UClass* Found = FindFirstObject<UClass>(*InStr, EFindFirstObjectOptions::NativeFirst))
		{
			return Found;
		}

		return nullptr;
	}

	/** True for the input/filter column kinds (Bool/Enum/GameplayTag/FloatRange). */
	bool IsInputColumnKind(const FString& Kind)
	{
		return Kind.Equals(TEXT("Bool"),       ESearchCase::IgnoreCase)
			|| Kind.Equals(TEXT("Enum"),       ESearchCase::IgnoreCase)
			|| Kind.Equals(TEXT("GameplayTag"),ESearchCase::IgnoreCase)
			|| Kind.Equals(TEXT("FloatRange"), ESearchCase::IgnoreCase);
	}

#if WITH_EDITORONLY_DATA
	/**
	 * Per-row value array length for a column FInstancedStruct, dispatched on the
	 * concrete column struct type. Each chooser column type stores cells in a
	 * DIFFERENTLY-NAMED member (verified against UE 5.7 engine headers):
	 *   FBoolColumn        -> RowValuesWithAny (TArray<EBoolColumnCellValue>)
	 *   FEnumColumn        -> RowValues        (TArray<FChooserEnumRowData>)
	 *   FGameplayTagColumn -> RowValues        (TArray<FGameplayTagContainer>)
	 *   FFloatRangeColumn  -> RowValues        (TArray<FChooserFloatRangeRowData>)
	 *   FOutputObjectColumn-> RowValues        (TArray<FChooserOutputObjectRowData>)
	 * Returns INDEX_NONE for an unrecognized column type.
	 */
	int32 GetColumnRowCount(const FInstancedStruct& Col)
	{
		if (const FBoolColumn* BoolC = Col.GetPtr<FBoolColumn>())              { return BoolC->RowValuesWithAny.Num(); }
		if (const FEnumColumn* EnumC = Col.GetPtr<FEnumColumn>())              { return EnumC->RowValues.Num(); }
		if (const FGameplayTagColumn* TagC = Col.GetPtr<FGameplayTagColumn>()) { return TagC->RowValues.Num(); }
		if (const FFloatRangeColumn* RangeC = Col.GetPtr<FFloatRangeColumn>()) { return RangeC->RowValues.Num(); }
		if (const FOutputObjectColumn* OutC = Col.GetPtr<FOutputObjectColumn>()){ return OutC->RowValues.Num(); }
		return INDEX_NONE;
	}

	/**
	 * Append exactly one DEFAULT cell to a column's per-row value array. Used both
	 * when adding a new column (to back-fill existing rows) and when adding a new
	 * row (to grow every column by one). For OutputObject columns the default cell
	 * is an empty FChooserOutputObjectRowData (Value set later by the row writer).
	 * Returns false only for an unrecognized column struct type.
	 */
	bool AppendDefaultCell(FInstancedStruct& Col)
	{
		if (FBoolColumn* BoolC = Col.GetMutablePtr<FBoolColumn>())
		{
			BoolC->RowValuesWithAny.Add(BoolC->DefaultRowValue);
			return true;
		}
		if (FEnumColumn* EnumC = Col.GetMutablePtr<FEnumColumn>())
		{
			EnumC->RowValues.Add(FChooserEnumRowData());
			return true;
		}
		if (FGameplayTagColumn* TagC = Col.GetMutablePtr<FGameplayTagColumn>())
		{
			TagC->RowValues.Add(FGameplayTagContainer());
			return true;
		}
		if (FFloatRangeColumn* RangeC = Col.GetMutablePtr<FFloatRangeColumn>())
		{
			RangeC->RowValues.Add(FChooserFloatRangeRowData());
			return true;
		}
		if (FOutputObjectColumn* OutC = Col.GetMutablePtr<FOutputObjectColumn>())
		{
			OutC->RowValues.Add(FChooserOutputObjectRowData());
			return true;
		}
		return false;
	}

	/** Grow a column's per-row array (appending defaults) until it reaches DesiredCount cells. */
	void EnsureColumnRowCount(FInstancedStruct& Col, int32 DesiredCount)
	{
		int32 Cur = GetColumnRowCount(Col);
		if (Cur == INDEX_NONE)
		{
			return; // unknown column type — leave untouched
		}
		while (Cur < DesiredCount)
		{
			if (!AppendDefaultCell(Col)) { break; }
			++Cur;
		}
	}

	/**
	 * Write one JSON cell value into the LAST row of an INPUT column (the row we
	 * just appended via AppendDefaultCell). The JSON shape depends on column kind:
	 *   Bool:        bool, or string "any"/"true"/"false"
	 *   Enum:        integer (the raw uint8 value); comparison defaults to MatchEqual
	 *   FloatRange:  object { "min": number, "max": number }
	 *   GameplayTag: string tag name (e.g. "State.Locomotion.Walk")
	 * Returns false (with OutError) on a type/shape mismatch.
	 */
	bool SetInputCellFromJson(FInstancedStruct& Col, const TSharedPtr<FJsonValue>& Cell, FString& OutError)
	{
		if (FBoolColumn* BoolC = Col.GetMutablePtr<FBoolColumn>())
		{
			const int32 Last = BoolC->RowValuesWithAny.Num() - 1;
			if (!BoolC->RowValuesWithAny.IsValidIndex(Last)) { OutError = TEXT("Bool column has no row to write"); return false; }

			bool bVal = false;
			FString SVal;
			if (Cell.IsValid() && Cell->TryGetBool(bVal))
			{
				BoolC->RowValuesWithAny[Last] = bVal ? EBoolColumnCellValue::MatchTrue : EBoolColumnCellValue::MatchFalse;
				return true;
			}
			if (Cell.IsValid() && Cell->TryGetString(SVal))
			{
				if (SVal.Equals(TEXT("any"),   ESearchCase::IgnoreCase)) { BoolC->RowValuesWithAny[Last] = EBoolColumnCellValue::MatchAny;   return true; }
				if (SVal.Equals(TEXT("true"),  ESearchCase::IgnoreCase)) { BoolC->RowValuesWithAny[Last] = EBoolColumnCellValue::MatchTrue;  return true; }
				if (SVal.Equals(TEXT("false"), ESearchCase::IgnoreCase)) { BoolC->RowValuesWithAny[Last] = EBoolColumnCellValue::MatchFalse; return true; }
			}
			OutError = TEXT("Bool cell must be a bool or 'any'/'true'/'false'");
			return false;
		}
		if (FEnumColumn* EnumC = Col.GetMutablePtr<FEnumColumn>())
		{
			const int32 Last = EnumC->RowValues.Num() - 1;
			if (!EnumC->RowValues.IsValidIndex(Last)) { OutError = TEXT("Enum column has no row to write"); return false; }

			double NumVal = 0.0;
			if (!Cell.IsValid() || !Cell->TryGetNumber(NumVal))
			{
				OutError = TEXT("Enum cell must be an integer value");
				return false;
			}
			EnumC->RowValues[Last].Value = static_cast<uint8>(static_cast<int32>(NumVal));
			EnumC->RowValues[Last].Comparison = EEnumColumnCellValueComparison::MatchEqual;
			return true;
		}
		if (FFloatRangeColumn* RangeC = Col.GetMutablePtr<FFloatRangeColumn>())
		{
			const int32 Last = RangeC->RowValues.Num() - 1;
			if (!RangeC->RowValues.IsValidIndex(Last)) { OutError = TEXT("FloatRange column has no row to write"); return false; }

			const TSharedPtr<FJsonObject>* Obj = nullptr;
			if (!Cell.IsValid() || !Cell->TryGetObject(Obj) || !Obj || !Obj->IsValid())
			{
				OutError = TEXT("FloatRange cell must be an object { min, max }");
				return false;
			}
			double MinV = 0.0, MaxV = 0.0;
			(*Obj)->TryGetNumberField(TEXT("min"), MinV);
			(*Obj)->TryGetNumberField(TEXT("max"), MaxV);
			RangeC->RowValues[Last].Min = static_cast<float>(MinV);
			RangeC->RowValues[Last].Max = static_cast<float>(MaxV);
			return true;
		}
		if (FGameplayTagColumn* TagC = Col.GetMutablePtr<FGameplayTagColumn>())
		{
			const int32 Last = TagC->RowValues.Num() - 1;
			if (!TagC->RowValues.IsValidIndex(Last)) { OutError = TEXT("GameplayTag column has no row to write"); return false; }

			FString TagStr;
			if (!Cell.IsValid() || !Cell->TryGetString(TagStr) || TagStr.IsEmpty())
			{
				OutError = TEXT("GameplayTag cell must be a non-empty tag string");
				return false;
			}
			const FGameplayTag Tag = UGameplayTagsManager::Get().RequestGameplayTag(FName(*TagStr), /*ErrorIfNotFound=*/false);
			if (!Tag.IsValid())
			{
				OutError = FString::Printf(TEXT("GameplayTag '%s' is not registered"), *TagStr);
				return false;
			}
			TagC->RowValues[Last].Reset();
			TagC->RowValues[Last].AddTag(Tag);
			return true;
		}
		OutError = TEXT("column is not a writable input column");
		return false;
	}

	/** Apply an optional dotted property-binding path to an input column's InputValue chain. */
	void ApplyInputBinding(FInstancedStruct& Col, const FString& DottedPath)
	{
		if (DottedPath.IsEmpty())
		{
			return;
		}

		// The column constructor already InitializeAs()'d InputValue with the right
		// context-property struct (FBoolContextProperty / FEnumContextProperty /
		// FFloatContextProperty / FGameplayTagContextProperty), each of which
		// derives FChooserParameterBase and owns a 'Binding' FChooserPropertyBinding.
		// We reach the base binding generically by reflection on the InputValue
		// struct's 'Binding' member to avoid per-type casts.
		FInstancedStruct* InputValue = nullptr;
		if (FBoolColumn* BoolC = Col.GetMutablePtr<FBoolColumn>())                { InputValue = &BoolC->InputValue; }
		else if (FEnumColumn* EnumC = Col.GetMutablePtr<FEnumColumn>())           { InputValue = &EnumC->InputValue; }
		else if (FGameplayTagColumn* TagC = Col.GetMutablePtr<FGameplayTagColumn>()){ InputValue = &TagC->InputValue; }
		else if (FFloatRangeColumn* RangeC = Col.GetMutablePtr<FFloatRangeColumn>()){ InputValue = &RangeC->InputValue; }
		if (!InputValue || !InputValue->IsValid())
		{
			return;
		}

		// Split the dotted path into the FName chain.
		TArray<FString> Parts;
		DottedPath.ParseIntoArray(Parts, TEXT("."), /*CullEmpty=*/true);
		TArray<FName> Chain;
		for (const FString& P : Parts) { Chain.Add(FName(*P)); }

		// Locate the 'Binding' FStructProperty on the context-property struct and
		// write its PropertyBindingChain via reflection (type-agnostic across the
		// four context-property struct types, all of which derive
		// FChooserParameterBase and hold an FChooserPropertyBinding-derived Binding).
		const UScriptStruct* SS = InputValue->GetScriptStruct();
		if (!SS) { return; }
		for (TFieldIterator<FStructProperty> It(SS); It; ++It)
		{
			if (It->GetName() == TEXT("Binding"))
			{
				void* BindingPtr = It->ContainerPtrToValuePtr<void>(InputValue->GetMutableMemory());
				if (BindingPtr && It->Struct && It->Struct->IsChildOf(FChooserPropertyBinding::StaticStruct()))
				{
					FChooserPropertyBinding* Binding = static_cast<FChooserPropertyBinding*>(BindingPtr);
					Binding->PropertyBindingChain = Chain;
				}
				break;
			}
		}
	}

	/**
	 * Set the editor-side enum binding on an Enum column's InputValue so the column
	 * filters/validates against a concrete UEnum. FEnumColumn has no direct Enum
	 * member; the enum is owned by the InputValue's FChooserEnumPropertyBinding
	 * (its `Enum` field, WITH_EDITORONLY_DATA). Returns false if the column is not
	 * an Enum column or the binding chain is unexpected. No-op (returns true) when
	 * not in an editor-only build (the binding field doesn't exist then).
	 */
	bool ApplyEnumClass(FInstancedStruct& Col, const UEnum* EnumType)
	{
		FEnumColumn* EnumC = Col.GetMutablePtr<FEnumColumn>();
		if (!EnumC || !EnumType)
		{
			return false;
		}
		if (FChooserEnumPropertyBinding* EnumBinding = EnumC->InputValue.GetMutablePtr<FChooserEnumPropertyBinding>())
		{
			EnumBinding->Enum = EnumType;
			return true;
		}
		return false;
	}

	/**
	 * Write a typed predicate value into a SPECIFIC (already-existing) cell of an
	 * input column, dispatched on the column's concrete kind. Unlike
	 * SetInputCellFromJson (which targets the last appended row from a single JSON
	 * cell value), this addresses an arbitrary RowIdx and reads the per-kind value
	 * fields directly off the action params:
	 *   Bool        -> bool_value (bool) OR bool_value=="any" string
	 *   Enum        -> enum_value (int) [+ comparison string]
	 *   FloatRange  -> float_min / float_max
	 *   GameplayTag -> tags (string or array of strings)
	 *   OutputObject-> (not handled here; outputs are authored via add_chooser_row)
	 * RowIdx is assumed already validated against GetColumnRowCount by the caller.
	 * Returns false + OutError on a kind/shape mismatch.
	 */
	bool SetCellAtRowFromParams(FInstancedStruct& Col, int32 RowIdx,
		const TSharedPtr<FJsonObject>& Params, FString& OutError)
	{
		if (FBoolColumn* BoolC = Col.GetMutablePtr<FBoolColumn>())
		{
			if (!BoolC->RowValuesWithAny.IsValidIndex(RowIdx)) { OutError = TEXT("row index out of range for Bool column"); return false; }

			bool bVal = false;
			FString SVal;
			if (Params->TryGetBoolField(TEXT("bool_value"), bVal))
			{
				BoolC->RowValuesWithAny[RowIdx] = bVal ? EBoolColumnCellValue::MatchTrue : EBoolColumnCellValue::MatchFalse;
				return true;
			}
			if (Params->TryGetStringField(TEXT("bool_value"), SVal) && SVal.Equals(TEXT("any"), ESearchCase::IgnoreCase))
			{
				BoolC->RowValuesWithAny[RowIdx] = EBoolColumnCellValue::MatchAny;
				return true;
			}
			OutError = TEXT("Bool cell requires bool_value (bool) or 'any'");
			return false;
		}
		if (FEnumColumn* EnumC = Col.GetMutablePtr<FEnumColumn>())
		{
			if (!EnumC->RowValues.IsValidIndex(RowIdx)) { OutError = TEXT("row index out of range for Enum column"); return false; }

			double NumVal = 0.0;
			if (!Params->TryGetNumberField(TEXT("enum_value"), NumVal))
			{
				OutError = TEXT("Enum cell requires enum_value (integer)");
				return false;
			}
			EnumC->RowValues[RowIdx].Value = static_cast<uint8>(static_cast<int32>(NumVal));

			EEnumColumnCellValueComparison Cmp = EEnumColumnCellValueComparison::MatchEqual;
			FString CmpStr;
			if (Params->TryGetStringField(TEXT("comparison"), CmpStr))
			{
				if      (CmpStr.Equals(TEXT("MatchEqual"),    ESearchCase::IgnoreCase)) { Cmp = EEnumColumnCellValueComparison::MatchEqual; }
				else if (CmpStr.Equals(TEXT("MatchNotEqual"), ESearchCase::IgnoreCase)) { Cmp = EEnumColumnCellValueComparison::MatchNotEqual; }
				else if (CmpStr.Equals(TEXT("MatchAny"),      ESearchCase::IgnoreCase)) { Cmp = EEnumColumnCellValueComparison::MatchAny; }
				else { OutError = FString::Printf(TEXT("Unrecognized comparison '%s'"), *CmpStr); return false; }
			}
			EnumC->RowValues[RowIdx].Comparison = Cmp;
			return true;
		}
		if (FFloatRangeColumn* RangeC = Col.GetMutablePtr<FFloatRangeColumn>())
		{
			if (!RangeC->RowValues.IsValidIndex(RowIdx)) { OutError = TEXT("row index out of range for FloatRange column"); return false; }

			double MinV = 0.0, MaxV = 0.0;
			const bool bHasMin = Params->TryGetNumberField(TEXT("float_min"), MinV);
			const bool bHasMax = Params->TryGetNumberField(TEXT("float_max"), MaxV);
			if (!bHasMin && !bHasMax)
			{
				OutError = TEXT("FloatRange cell requires float_min and/or float_max");
				return false;
			}
			if (bHasMin) { RangeC->RowValues[RowIdx].Min = static_cast<float>(MinV); }
			if (bHasMax) { RangeC->RowValues[RowIdx].Max = static_cast<float>(MaxV); }
			return true;
		}
		if (FGameplayTagColumn* TagC = Col.GetMutablePtr<FGameplayTagColumn>())
		{
			if (!TagC->RowValues.IsValidIndex(RowIdx)) { OutError = TEXT("row index out of range for GameplayTag column"); return false; }

			// Accept either a single tag string or an array of tag strings.
			TArray<FString> TagStrings;
			const TArray<TSharedPtr<FJsonValue>>* ArrPtr = nullptr;
			FString SingleTag;
			if (Params->TryGetArrayField(TEXT("tags"), ArrPtr) && ArrPtr)
			{
				for (const TSharedPtr<FJsonValue>& V : *ArrPtr)
				{
					FString T;
					if (V.IsValid() && V->TryGetString(T) && !T.IsEmpty()) { TagStrings.Add(T); }
				}
			}
			else if (Params->TryGetStringField(TEXT("tags"), SingleTag) && !SingleTag.IsEmpty())
			{
				TagStrings.Add(SingleTag);
			}
			if (TagStrings.Num() == 0)
			{
				OutError = TEXT("GameplayTag cell requires tags (a tag string or array of tag strings)");
				return false;
			}

			FGameplayTagContainer Container;
			for (const FString& T : TagStrings)
			{
				const FGameplayTag Tag = UGameplayTagsManager::Get().RequestGameplayTag(FName(*T), /*ErrorIfNotFound=*/false);
				if (!Tag.IsValid())
				{
					OutError = FString::Printf(TEXT("GameplayTag '%s' is not registered"), *T);
					return false;
				}
				Container.AddTag(Tag);
			}
			TagC->RowValues[RowIdx] = MoveTemp(Container);
			return true;
		}
		OutError = TEXT("column is not a writable input column (Bool/Enum/FloatRange/GameplayTag)");
		return false;
	}
#endif // WITH_EDITORONLY_DATA
}

// ===========================================================================
// create_chooser_table
// ===========================================================================

FMonolithActionResult FMonolithChooserAuthoringActions::HandleCreateChooserTable(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	const FString OutputType = Params->HasField(TEXT("output_type"))
		? Params->GetStringField(TEXT("output_type")) : TEXT("Object");
	const FString OutputClassPath = Params->HasField(TEXT("output_class"))
		? Params->GetStringField(TEXT("output_class")) : FString();
	const FString ContextClassPath = Params->HasField(TEXT("context_class"))
		? Params->GetStringField(TEXT("context_class")) : FString();

	EObjectChooserResultType ResultType;
	if (!ParseChooserResultType(OutputType, ResultType))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unrecognized output_type '%s' (expected ObjectResult/ClassResult/NoPrimaryResult)"), *OutputType));
	}

	// CreatePackage reuse semantics (project gotcha): guard against an existing asset first.
	if (FMonolithAssetUtils::LoadAssetByPath<UObject>(AssetPath))
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Asset already exists at '%s'"), *AssetPath));
	}

	FString AssetName;
	int32 LastSlash = INDEX_NONE;
	if (!AssetPath.FindLastChar('/', LastSlash) || LastSlash == AssetPath.Len() - 1)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Invalid asset path: %s"), *AssetPath));
	}
	AssetName = AssetPath.Mid(LastSlash + 1);

	UPackage* Pkg = CreatePackage(*AssetPath);
	if (!Pkg)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to create package at '%s'"), *AssetPath));
	}

	UChooserTable* Table = NewObject<UChooserTable>(Pkg, FName(*AssetName), RF_Public | RF_Standalone);
	if (!Table)
	{
		return FMonolithActionResult::Error(TEXT("Failed to create UChooserTable object"));
	}

	// ResultType / OutputObjectType live on the UChooserSignature base.
	Table->ResultType = ResultType;

	if (!OutputClassPath.IsEmpty() && ResultType != EObjectChooserResultType::NoPrimaryResult)
	{
		// Resolve full path OR bare short name ("PoseSearchDatabase"). On failure
		// leave OutputObjectType unset (no error) per the action contract.
		if (UClass* OutClass = ResolveClassByNameOrPath(OutputClassPath))
		{
			Table->OutputObjectType = OutClass;
		}
	}

	// Optional context object class — appended as a FContextObjectTypeClass parameter
	// on the context owner (this table is its own root at creation).
	if (!ContextClassPath.IsEmpty())
	{
		if (UClass* CtxClass = ResolveClassByNameOrPath(ContextClassPath))
		{
			FInstancedStruct CtxEntry;
			CtxEntry.InitializeAs<FContextObjectTypeClass>();
			CtxEntry.GetMutable<FContextObjectTypeClass>().Class = CtxClass;
			Table->ContextData.Add(MoveTemp(CtxEntry));
		}
	}

	Table->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), Table->GetPathName());
	Root->SetStringField(TEXT("result_type"),
		ResultType == EObjectChooserResultType::ObjectResult ? TEXT("ObjectResult") :
		ResultType == EObjectChooserResultType::ClassResult  ? TEXT("ClassResult")  : TEXT("NoPrimaryResult"));
	Root->SetStringField(TEXT("output_class"), Table->OutputObjectType ? Table->OutputObjectType->GetPathName() : TEXT(""));
	Root->SetNumberField(TEXT("context_count"), Table->ContextData.Num());
	return FMonolithActionResult::Success(Root);
}

// ===========================================================================
// add_chooser_column
// ===========================================================================

FMonolithActionResult FMonolithChooserAuthoringActions::HandleAddChooserColumn(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath  = Params->GetStringField(TEXT("asset_path"));
	const FString ColumnKind = Params->GetStringField(TEXT("column_kind"));
	const FString BindingProp = Params->HasField(TEXT("binding_property"))
		? Params->GetStringField(TEXT("binding_property")) : FString();
	const FString EnumClassStr = Params->HasField(TEXT("enum_class"))
		? Params->GetStringField(TEXT("enum_class")) : FString();

	UChooserTable* Table = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(AssetPath);
	if (!Table)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("ChooserTable not found: %s"), *AssetPath));
	}

#if WITH_EDITORONLY_DATA
	// Build the new column FInstancedStruct of the requested kind. Each Make<>()
	// runs the column's default constructor, which InitializeAs()'s InputValue
	// with the matching context-property struct.
	FInstancedStruct NewColumn;
	const bool bIsInput = IsInputColumnKind(ColumnKind);

	if      (ColumnKind.Equals(TEXT("Bool"),        ESearchCase::IgnoreCase)) { NewColumn = FInstancedStruct::Make<FBoolColumn>(); }
	else if (ColumnKind.Equals(TEXT("Enum"),        ESearchCase::IgnoreCase)) { NewColumn = FInstancedStruct::Make<FEnumColumn>(); }
	else if (ColumnKind.Equals(TEXT("GameplayTag"), ESearchCase::IgnoreCase)) { NewColumn = FInstancedStruct::Make<FGameplayTagColumn>(); }
	else if (ColumnKind.Equals(TEXT("FloatRange"),  ESearchCase::IgnoreCase)) { NewColumn = FInstancedStruct::Make<FFloatRangeColumn>(); }
	else if (ColumnKind.Equals(TEXT("OutputObject"),ESearchCase::IgnoreCase)) { NewColumn = FInstancedStruct::Make<FOutputObjectColumn>(); }
	else
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Unrecognized column_kind '%s' (expected Bool/Enum/GameplayTag/FloatRange/OutputObject)"), *ColumnKind));
	}

	// Optional input binding (filter columns only).
	if (bIsInput && !BindingProp.IsEmpty())
	{
		ApplyInputBinding(NewColumn, BindingProp);
	}

	// Optional explicit enum class for Enum columns — sets the editor-side enum
	// binding so the column filters/validates against a concrete UEnum. FEnumColumn
	// has no direct Enum member; the enum lives on the InputValue binding.
	bool bEnumClassApplied = false;
	if (ColumnKind.Equals(TEXT("Enum"), ESearchCase::IgnoreCase) && !EnumClassStr.IsEmpty())
	{
		const UEnum* EnumType = LoadObject<UEnum>(nullptr, *EnumClassStr);
		if (!EnumType)
		{
			EnumType = FindFirstObject<UEnum>(*EnumClassStr, EFindFirstObjectOptions::NativeFirst);
		}
		if (EnumType)
		{
			bEnumClassApplied = ApplyEnumClass(NewColumn, EnumType);
		}
		else
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("enum_class '%s' could not be resolved to a UEnum"), *EnumClassStr));
		}
	}

	// CRITICAL alignment step: back-fill the new column's per-row array to the
	// CURRENT row count so every parallel array stays equal-length. Row count is
	// the authoritative ResultsStructs length.
	const int32 CurrentRowCount = Table->ResultsStructs.Num();
	EnsureColumnRowCount(NewColumn, CurrentRowCount);

	Table->ColumnsStructs.Add(MoveTemp(NewColumn));
	Table->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), Table->GetPathName());
	Root->SetNumberField(TEXT("column_count"), Table->ColumnsStructs.Num());
	Root->SetNumberField(TEXT("column_index"), Table->ColumnsStructs.Num() - 1);
	Root->SetStringField(TEXT("column_kind"), ColumnKind);
	Root->SetBoolField(TEXT("is_input"), bIsInput);
	Root->SetNumberField(TEXT("back_filled_rows"), CurrentRowCount);
	Root->SetBoolField(TEXT("enum_class_applied"), bEnumClassApplied);
	return FMonolithActionResult::Success(Root);
#else
	return FMonolithActionResult::Error(TEXT("ColumnsStructs is editor-only data; not available in this build"));
#endif
}

// ===========================================================================
// add_chooser_row  (HIGHEST risk — every parallel array grows by exactly 1)
// ===========================================================================

FMonolithActionResult FMonolithChooserAuthoringActions::HandleAddChooserRow(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	const FString OutputPsd = Params->GetStringField(TEXT("output_psd"));

	const TArray<TSharedPtr<FJsonValue>>* CellsPtr = nullptr;
	if (!Params->TryGetArrayField(TEXT("cells"), CellsPtr) || !CellsPtr)
	{
		return FMonolithActionResult::Error(TEXT("Missing required array parameter: cells"));
	}

	UChooserTable* Table = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(AssetPath);
	if (!Table)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("ChooserTable not found: %s"), *AssetPath));
	}

#if WITH_EDITORONLY_DATA
	// --- Step 1: validate cells.Num() == INPUT-column count BEFORE mutating anything. ---
	TArray<int32> InputColumnIndices;
	for (int32 i = 0; i < Table->ColumnsStructs.Num(); ++i)
	{
		const FInstancedStruct& Col = Table->ColumnsStructs[i];
		// Input columns are the filter kinds (Bool/Enum/GameplayTag/FloatRange).
		// OutputObject columns are NOT addressed by cells — they receive the row's output.
		if (Col.GetPtr<FBoolColumn>() || Col.GetPtr<FEnumColumn>()
			|| Col.GetPtr<FGameplayTagColumn>() || Col.GetPtr<FFloatRangeColumn>())
		{
			InputColumnIndices.Add(i);
		}
	}

	if (CellsPtr->Num() != InputColumnIndices.Num())
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("cells count (%d) must equal input-column count (%d)"),
			CellsPtr->Num(), InputColumnIndices.Num()));
	}

	// --- Step 1b: resolve the output asset BEFORE mutating (fail clean if missing). ---
	UObject* OutputAsset = FMonolithAssetUtils::LoadAssetByPath(OutputPsd);
	if (!OutputAsset)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("output_psd asset not found: %s"), *OutputPsd));
	}

	// Snapshot the current authoritative row count so we can detect/repair drift.
	const int32 RowCountBefore = Table->ResultsStructs.Num();

	// --- Step 2: grow EVERY parallel array by exactly 1, default-initialized. ---
	// First grow each column's per-row array to RowCountBefore+1. (EnsureColumnRowCount
	// also repairs any pre-existing under-length column as a safety net.)
	const int32 TargetRowCount = RowCountBefore + 1;
	for (FInstancedStruct& Col : Table->ColumnsStructs)
	{
		EnsureColumnRowCount(Col, TargetRowCount);
	}

	// ResultsStructs: append the FAssetChooser result for this row.
	{
		FInstancedStruct ResultStruct = FInstancedStruct::Make<FAssetChooser>();
		ResultStruct.GetMutable<FAssetChooser>().Asset = OutputAsset;
		Table->ResultsStructs.Add(MoveTemp(ResultStruct));
	}

	// DisabledRows is a parallel TArray<bool>; grow by one (new row enabled).
	Table->DisabledRows.Add(false);

	// --- Step 3: write the input cells into the freshly-appended last cell of each input column. ---
	FString CellError;
	for (int32 c = 0; c < InputColumnIndices.Num(); ++c)
	{
		const int32 ColIdx = InputColumnIndices[c];
		FInstancedStruct& Col = Table->ColumnsStructs[ColIdx];
		if (!SetInputCellFromJson(Col, (*CellsPtr)[c], CellError))
		{
			// Best-effort rollback so we never leave arrays mismatched on a cell error.
			for (FInstancedStruct& RbCol : Table->ColumnsStructs)
			{
				const int32 N = GetColumnRowCount(RbCol);
				if (N == TargetRowCount)
				{
					// Trim the cell we appended in Step 2. RemoveAt avoids the
					// [[nodiscard]] return of Pop() (C4834 under warnings-as-errors).
					if (FBoolColumn* RbBoolC = RbCol.GetMutablePtr<FBoolColumn>())              { RbBoolC->RowValuesWithAny.RemoveAt(RbBoolC->RowValuesWithAny.Num() - 1, EAllowShrinking::No); }
					else if (FEnumColumn* RbEnumC = RbCol.GetMutablePtr<FEnumColumn>())         { RbEnumC->RowValues.RemoveAt(RbEnumC->RowValues.Num() - 1, EAllowShrinking::No); }
					else if (FGameplayTagColumn* RbTagC = RbCol.GetMutablePtr<FGameplayTagColumn>()){ RbTagC->RowValues.RemoveAt(RbTagC->RowValues.Num() - 1, EAllowShrinking::No); }
					else if (FFloatRangeColumn* RbRangeC = RbCol.GetMutablePtr<FFloatRangeColumn>()){ RbRangeC->RowValues.RemoveAt(RbRangeC->RowValues.Num() - 1, EAllowShrinking::No); }
					else if (FOutputObjectColumn* RbOutC = RbCol.GetMutablePtr<FOutputObjectColumn>()){ RbOutC->RowValues.RemoveAt(RbOutC->RowValues.Num() - 1, EAllowShrinking::No); }
				}
			}
			Table->ResultsStructs.RemoveAt(Table->ResultsStructs.Num() - 1, EAllowShrinking::No);
			Table->DisabledRows.RemoveAt(Table->DisabledRows.Num() - 1, EAllowShrinking::No);

			return FMonolithActionResult::Error(FString::Printf(
				TEXT("cell %d (column %d): %s — row append rolled back"), c, ColIdx, *CellError));
		}
	}

	Table->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), Table->GetPathName());
	Root->SetNumberField(TEXT("row_count"), Table->ResultsStructs.Num());
	Root->SetNumberField(TEXT("row_index"), Table->ResultsStructs.Num() - 1);
	Root->SetNumberField(TEXT("column_count"), Table->ColumnsStructs.Num());
	Root->SetNumberField(TEXT("input_column_count"), InputColumnIndices.Num());
	Root->SetNumberField(TEXT("disabled_rows_count"), Table->DisabledRows.Num());
	Root->SetStringField(TEXT("output_asset"), OutputAsset->GetPathName());
	return FMonolithActionResult::Success(Root);
#else
	return FMonolithActionResult::Error(TEXT("ResultsStructs/ColumnsStructs are editor-only data; not available in this build"));
#endif
}

// ===========================================================================
// set_chooser_cell  (set a typed predicate value into a specific cell)
// ===========================================================================

FMonolithActionResult FMonolithChooserAuthoringActions::HandleSetChooserCell(const TSharedPtr<FJsonObject>& Params)
{
	const FString AssetPath = Params->GetStringField(TEXT("asset_path"));

	double ColIdxD = 0.0, RowIdxD = 0.0;
	if (!Params->TryGetNumberField(TEXT("column_index"), ColIdxD))
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: column_index"));
	}
	if (!Params->TryGetNumberField(TEXT("row_index"), RowIdxD))
	{
		return FMonolithActionResult::Error(TEXT("Missing required parameter: row_index"));
	}
	const int32 ColIdx = static_cast<int32>(ColIdxD);
	const int32 RowIdx = static_cast<int32>(RowIdxD);

	UChooserTable* Table = FMonolithAssetUtils::LoadAssetByPath<UChooserTable>(AssetPath);
	if (!Table)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("ChooserTable not found: %s"), *AssetPath));
	}

#if WITH_EDITORONLY_DATA
	if (!Table->ColumnsStructs.IsValidIndex(ColIdx))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("column_index %d out of range (column count %d)"), ColIdx, Table->ColumnsStructs.Num()));
	}

	FInstancedStruct& Col = Table->ColumnsStructs[ColIdx];

	// Validate the row index against THIS column's per-row array (which the row
	// authoring keeps aligned with ResultsStructs).
	const int32 ColRowCount = GetColumnRowCount(Col);
	if (ColRowCount == INDEX_NONE)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("column %d is not a recognized chooser column type"), ColIdx));
	}
	if (RowIdx < 0 || RowIdx >= ColRowCount)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("row_index %d out of range (row count %d)"), RowIdx, ColRowCount));
	}

	FString CellError;
	if (!SetCellAtRowFromParams(Col, RowIdx, Params, CellError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("set_chooser_cell (column %d, row %d): %s"), ColIdx, RowIdx, *CellError));
	}

	Table->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("asset_path"), Table->GetPathName());
	Root->SetNumberField(TEXT("column_index"), ColIdx);
	Root->SetNumberField(TEXT("row_index"), RowIdx);
	return FMonolithActionResult::Success(Root);
#else
	return FMonolithActionResult::Error(TEXT("ColumnsStructs are editor-only data; not available in this build"));
#endif
}

#endif // WITH_CHOOSER
