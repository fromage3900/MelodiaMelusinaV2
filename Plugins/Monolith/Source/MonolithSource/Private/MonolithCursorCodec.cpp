// SPDX-License-Identifier: MIT
// Survivor E (`source_query("search_source")` cursor pagination) — opaque
// cursor codec implementation.
// Plan: Plugins/Monolith/Docs/plans/2026-05-27-mcp-llm-ergonomics.md §3.E

#include "MonolithCursorCodec.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/Base64.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Templates/TypeHash.h"

namespace MonolithCursorCodec
{

FString Encode(const FCursorState& State)
{
	// Build a minimal JSON object; key names are deliberately short to keep the
	// base64 envelope small (cursors travel in every paginated request).
	TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
	// SetNumberField takes double; uint32 -> double round-trips exactly up to 2^53.
	Obj->SetNumberField(TEXT("qh"), static_cast<double>(State.QueryHash));
	Obj->SetNumberField(TEXT("sp"), State.SymbolPage);
	Obj->SetNumberField(TEXT("rp"), State.SourcePage);
	Obj->SetNumberField(TEXT("tc"), State.CachedTotalEstimate);

	FString JsonStr;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonStr);
	FJsonSerializer::Serialize(Obj.ToSharedRef(), Writer);

	return FBase64::Encode(JsonStr);
}

bool Decode(const FString& EncodedCursor, FCursorState& OutState)
{
	OutState = FCursorState();

	if (EncodedCursor.IsEmpty())
	{
		return false;
	}

	FString JsonStr;
	if (!FBase64::Decode(EncodedCursor, JsonStr))
	{
		return false;
	}

	TSharedPtr<FJsonObject> Obj;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
	if (!FJsonSerializer::Deserialize(Reader, Obj) || !Obj.IsValid())
	{
		return false;
	}

	double QhD = 0.0;
	double SpD = 0.0;
	double RpD = 0.0;
	double TcD = -1.0;

	// All four fields are required for a well-formed cursor.
	if (!Obj->TryGetNumberField(TEXT("qh"), QhD)) { return false; }
	if (!Obj->TryGetNumberField(TEXT("sp"), SpD)) { return false; }
	if (!Obj->TryGetNumberField(TEXT("rp"), RpD)) { return false; }
	if (!Obj->TryGetNumberField(TEXT("tc"), TcD)) { return false; }

	// Defensive: reject negative page indices and oversize hashes.
	if (SpD < 0.0 || RpD < 0.0) { return false; }
	if (QhD < 0.0 || QhD > static_cast<double>(TNumericLimits<uint32>::Max())) { return false; }

	OutState.QueryHash = static_cast<uint32>(QhD);
	OutState.SymbolPage = static_cast<int32>(SpD);
	OutState.SourcePage = static_cast<int32>(RpD);
	OutState.CachedTotalEstimate = static_cast<int32>(TcD);
	return true;
}

uint32 ComputeQueryHash(
	const FString& Query,
	const FString& Scope,
	const FString& Mode,
	const FString& Module,
	const FString& PathFilter,
	const FString& SymbolKind)
{
	uint32 Hash = GetTypeHash(Query);
	Hash = HashCombine(Hash, GetTypeHash(Scope));
	Hash = HashCombine(Hash, GetTypeHash(Mode));
	Hash = HashCombine(Hash, GetTypeHash(Module));
	Hash = HashCombine(Hash, GetTypeHash(PathFilter));
	Hash = HashCombine(Hash, GetTypeHash(SymbolKind));
	return Hash;
}

} // namespace MonolithCursorCodec
