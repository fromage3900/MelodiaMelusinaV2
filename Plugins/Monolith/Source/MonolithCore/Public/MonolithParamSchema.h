#pragma once
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include <initializer_list>

/**
 * Survivor D — schema-tag opt-in for dispatch-time \→/ rewrite.
 *
 * Phase 1 of plan §3.D (Docs/plans/2026-05-27-mcp-llm-ergonomics.md).
 * Default is `Other` for back-compat — every existing `.Required` / `.Optional`
 * call stays `Other` and opts OUT of any path normalisation. Only the new
 * `RequiredAssetPath` / `OptionalAssetPath` sugar tags `AssetPath`.
 *
 *  - Other        — no path semantics; never rewritten.
 *  - AssetPath    — `/Game/...` style. `\` rewritten to `/` at dispatch with warning.
 *  - DiskPath     — native OS path. Explicit opt-OUT for clarity. Never rewritten.
 *  - GameplayTag  — `A.B.C` tag string. Reserved; never rewritten in Phase 1.
 *
 * Stored on the per-param JSON schema object as a string field "kind"
 * (KindToString below) so the wire-format remains plain JSON.
 */
enum class EMonolithParamKind : uint8
{
	Other = 0,
	AssetPath,
	DiskPath,
	GameplayTag,
};

namespace MonolithParamKind
{
	inline const TCHAR* ToString(EMonolithParamKind Kind)
	{
		switch (Kind)
		{
			case EMonolithParamKind::AssetPath:   return TEXT("AssetPath");
			case EMonolithParamKind::DiskPath:    return TEXT("DiskPath");
			case EMonolithParamKind::GameplayTag: return TEXT("GameplayTag");
			default:                              return TEXT("Other");
		}
	}

	inline EMonolithParamKind FromString(const FString& S)
	{
		if (S == TEXT("AssetPath"))   return EMonolithParamKind::AssetPath;
		if (S == TEXT("DiskPath"))    return EMonolithParamKind::DiskPath;
		if (S == TEXT("GameplayTag")) return EMonolithParamKind::GameplayTag;
		return EMonolithParamKind::Other;
	}
}

class FParamSchemaBuilder
{
public:
	// --- Required (no aliases) ---
	FParamSchemaBuilder& Required(const FString& Name, const FString& Type, const FString& Desc)
	{
		AddParam(Name, Type, Desc, /*bRequired=*/true, /*Default=*/TEXT(""), /*bHasDefault=*/false, {}, EMonolithParamKind::Other);
		return *this;
	}

	// --- Required (with aliases) ---
	FParamSchemaBuilder& Required(const FString& Name, const FString& Type, const FString& Desc,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, Type, Desc, /*bRequired=*/true, /*Default=*/TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::Other);
		return *this;
	}

	// --- Optional (with default, no aliases) ---
	FParamSchemaBuilder& Optional(const FString& Name, const FString& Type, const FString& Desc,
		const FString& Default = TEXT(""))
	{
		AddParam(Name, Type, Desc, /*bRequired=*/false, Default, /*bHasDefault=*/!Default.IsEmpty(), {}, EMonolithParamKind::Other);
		return *this;
	}

	// --- Optional (with default + aliases) ---
	FParamSchemaBuilder& Optional(const FString& Name, const FString& Type, const FString& Desc,
		const FString& Default, std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, Type, Desc, /*bRequired=*/false, Default, /*bHasDefault=*/!Default.IsEmpty(), Aliases, EMonolithParamKind::Other);
		return *this;
	}

	// --- Optional (no default, with aliases) ---
	FParamSchemaBuilder& Optional(const FString& Name, const FString& Type, const FString& Desc,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, Type, Desc, /*bRequired=*/false, /*Default=*/TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::Other);
		return *this;
	}

	// --- Survivor D sugar overloads — opt-in to path-kind tagging.
	// These wrap Required/Optional + set Kind on the resulting entry.
	// Type is always "string"; default is always empty. Use the non-sugar
	// overloads above if you need a non-string type or a default value.
	FParamSchemaBuilder& RequiredAssetPath(const TCHAR* Name, const TCHAR* Description)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/true, TEXT(""), /*bHasDefault=*/false, {}, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalAssetPath(const TCHAR* Name, const TCHAR* Description)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, TEXT(""), /*bHasDefault=*/false, {}, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& RequiredDiskPath(const TCHAR* Name, const TCHAR* Description)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/true, TEXT(""), /*bHasDefault=*/false, {}, EMonolithParamKind::DiskPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalDiskPath(const TCHAR* Name, const TCHAR* Description)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, TEXT(""), /*bHasDefault=*/false, {}, EMonolithParamKind::DiskPath);
		return *this;
	}

	// --- Path-kind sugar WITH aliases (no default). For path params that also
	// declare K2 alias keys. Type forced "string"; default empty.
	FParamSchemaBuilder& RequiredAssetPath(const TCHAR* Name, const TCHAR* Description,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/true, TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalAssetPath(const TCHAR* Name, const TCHAR* Description,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& RequiredDiskPath(const TCHAR* Name, const TCHAR* Description,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/true, TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::DiskPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalDiskPath(const TCHAR* Name, const TCHAR* Description,
		std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, TEXT(""), /*bHasDefault=*/false, Aliases, EMonolithParamKind::DiskPath);
		return *this;
	}

	// --- Path-kind sugar WITH a non-empty default value. For Optional path
	// params that carry a default (e.g. a default /Game/... save location).
	// Type forced "string". The plain Optional overloads stay Other.
	FParamSchemaBuilder& OptionalAssetPathWithDefault(const TCHAR* Name, const TCHAR* Description,
		const TCHAR* Default)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, Default, /*bHasDefault=*/true, {}, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalAssetPathWithDefault(const TCHAR* Name, const TCHAR* Description,
		const TCHAR* Default, std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, Default, /*bHasDefault=*/true, Aliases, EMonolithParamKind::AssetPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalDiskPathWithDefault(const TCHAR* Name, const TCHAR* Description,
		const TCHAR* Default)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, Default, /*bHasDefault=*/true, {}, EMonolithParamKind::DiskPath);
		return *this;
	}

	FParamSchemaBuilder& OptionalDiskPathWithDefault(const TCHAR* Name, const TCHAR* Description,
		const TCHAR* Default, std::initializer_list<const TCHAR*> Aliases)
	{
		AddParam(Name, TEXT("string"), Description, /*bRequired=*/false, Default, /*bHasDefault=*/true, Aliases, EMonolithParamKind::DiskPath);
		return *this;
	}

	TSharedPtr<FJsonObject> Build()
	{
		return Schema;
	}

private:
	TSharedPtr<FJsonObject> Schema = MakeShared<FJsonObject>();

	void AddParam(const FString& Name, const FString& Type, const FString& Desc, bool bRequired,
		const FString& Default, bool bHasDefault, std::initializer_list<const TCHAR*> Aliases,
		EMonolithParamKind Kind)
	{
		TSharedPtr<FJsonObject> Param = MakeShared<FJsonObject>();
		Param->SetStringField(TEXT("type"), Type);
		Param->SetStringField(TEXT("description"), Desc);
		Param->SetBoolField(TEXT("required"), bRequired);
		if (bHasDefault)
		{
			Param->SetStringField(TEXT("default"), Default);
		}
		if (Aliases.size() > 0)
		{
			TArray<TSharedPtr<FJsonValue>> AliasArr;
			for (const TCHAR* A : Aliases)
			{
				AliasArr.Add(MakeShared<FJsonValueString>(FString(A)));
			}
			Param->SetArrayField(TEXT("aliases"), AliasArr);
		}
		// Survivor D: only emit "kind" when non-default, to keep tools/list bytes lean
		// and back-compat with any consumers that introspect the schema JSON shape.
		if (Kind != EMonolithParamKind::Other)
		{
			Param->SetStringField(TEXT("kind"), MonolithParamKind::ToString(Kind));
		}
		Schema->SetObjectField(Name, Param);
	}
};

/**
 * Param-schema utilities for the tool registry.
 *
 * - ApplyAliases: rewrites alias keys in Params -> canonical schema keys before dispatch.
 *   Returns false if both alias and canonical are supplied (caller treats as ErrInvalidParams).
 * - FindUnknownKeys: returns Params keys that are neither canonical nor declared aliases.
 *   Used by K3 unknown-param warnings.
 * - IsStrictParamsEnabled: env-var STRICT_PARAMS=1 promotes K3 warnings to hard errors.
 */
class MONOLITHCORE_API FMonolithParamSchema
{
public:
	static bool ApplyAliases(const TSharedPtr<FJsonObject>& Schema, const TSharedPtr<FJsonObject>& Params, FString& OutCollision);
	static TArray<FString> FindUnknownKeys(const TSharedPtr<FJsonObject>& Schema, const TSharedPtr<FJsonObject>& Params);
	static bool IsStrictParamsEnabled();
};
