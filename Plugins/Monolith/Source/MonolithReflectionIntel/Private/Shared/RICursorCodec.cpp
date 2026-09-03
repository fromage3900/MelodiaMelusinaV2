// SPDX-License-Identifier: MIT
//
// RICursorCodec — single definition of the shared pagination-cursor codec.
// See RICursorCodec.h for the rationale (unity-build C2084/C2011 consolidation).
// Bodies are a verbatim lift of the formerly-duplicated anonymous-namespace
// helpers; no behaviour change.

#include "Shared/RICursorCodec.h"

#include "Dom/JsonObject.h"
#include "Misc/Base64.h"
#include "MonolithJsonUtils.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Templates/TypeHash.h"

FString EncodeRICursor(const FRICursorState& S)
{
	TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
	O->SetNumberField(TEXT("qh"), static_cast<double>(S.QueryHash));
	O->SetNumberField(TEXT("p"),  S.Page);
	O->SetNumberField(TEXT("tc"), S.CachedTotalEstimate);
	FString Js;
	TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&Js);
	FJsonSerializer::Serialize(O.ToSharedRef(), W);
	return FBase64::Encode(Js);
}

bool DecodeRICursor(const FString& Enc, FRICursorState& Out)
{
	Out = FRICursorState();
	if (Enc.IsEmpty()) { return false; }
	FString Js;
	if (!FBase64::Decode(Enc, Js)) { return false; }
	TSharedPtr<FJsonObject> O;
	TSharedRef<TJsonReader<>> R = TJsonReaderFactory<>::Create(Js);
	if (!FJsonSerializer::Deserialize(R, O) || !O.IsValid()) { return false; }
	double Qh = 0.0, P = 0.0, Tc = -1.0;
	if (!O->TryGetNumberField(TEXT("qh"), Qh)) { return false; }
	if (!O->TryGetNumberField(TEXT("p"),  P))  { return false; }
	if (!O->TryGetNumberField(TEXT("tc"), Tc)) { return false; }
	if (P < 0.0) { return false; }
	if (Qh < 0.0 || Qh > static_cast<double>(TNumericLimits<uint32>::Max())) { return false; }
	Out.QueryHash = static_cast<uint32>(Qh);
	Out.Page = static_cast<int32>(P);
	Out.CachedTotalEstimate = static_cast<int32>(Tc);
	return true;
}

FMonolithActionResult RIInvalidCursorError(const FString& Reason)
{
	TSharedPtr<FJsonObject> Data = MakeShared<FJsonObject>();
	Data->SetStringField(TEXT("error_code"), TEXT("INVALID_CURSOR"));
	return FMonolithActionResult::Error(Reason, FMonolithJsonUtils::ErrInvalidParams)
		.WithErrorData(Data);
}

uint32 RIComputeFilterHash(std::initializer_list<FString> Parts)
{
	uint32 H = 0;
	for (const FString& P : Parts) { H = HashCombine(H, GetTypeHash(P)); }
	return H;
}
