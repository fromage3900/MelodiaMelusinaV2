// Copyright Melodia. Optional local AIRI bridge transport.

#include "MelodiaAiriBridgeSubsystem.h"

#include "Dom/JsonObject.h"
#include "HAL/PlatformTime.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UObject/Package.h"

DEFINE_LOG_CATEGORY_STATIC(LogMelodiaAiriBridge, Log, All);

namespace
{
	const TCHAR* RelayRoot = TEXT("http://127.0.0.1:8765");

	bool TryGetKnownLocation(const UWorld& World, FString& OutLocation)
	{
		const FString MapName = World.GetMapName();
		if (MapName.Contains(TEXT("LV_SeaAbove_Prototype")))
		{
			OutLocation = TEXT("Sea Above");
			return true;
		}
		if (MapName.Contains(TEXT("L_MelusinaMorning")))
		{
			OutLocation = TEXT("Melusina's Morning");
			return true;
		}
		if (MapName.Contains(TEXT("L_KaleidoNave")))
		{
			OutLocation = TEXT("Kaleido Nave");
			return true;
		}
		if (MapName.Contains(TEXT("MelodiaIntegrationMap")))
		{
			OutLocation = TEXT("Melodia Integration Field");
			return true;
		}
		return false;
	}

	FString SerializeJson(const TSharedRef<FJsonObject>& Object)
	{
		FString Output;
		const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Output);
		FJsonSerializer::Serialize(Object, Writer);
		return Output;
	}

	bool IsValidTimestamp(const FString& Value)
	{
		FDateTime Parsed;
		return Value.Len() <= 40 && FDateTime::ParseIso8601(*Value, Parsed);
	}
}

bool UMelodiaAiriBridgeSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	#if UE_BUILD_SHIPPING
	return false;
	#else
	return Super::ShouldCreateSubsystem(Outer)
		&& FParse::Param(FCommandLine::Get(), TEXT("MelodiaAiriBridge"));
	#endif
}

void UMelodiaAiriBridgeSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);

	if (!InWorld.IsGameWorld() || InWorld.GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	PublishWorldLocation(InWorld);
	IntentPollTicker = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &ThisClass::PollIntents),
		2.0f);
}

void UMelodiaAiriBridgeSubsystem::Deinitialize()
{
	if (IntentPollTicker.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(IntentPollTicker);
		IntentPollTicker.Reset();
	}
	bIntentPollInFlight = false;
	Super::Deinitialize();
}

void UMelodiaAiriBridgeSubsystem::PublishWorldLocation(const UWorld& World)
{
	FString Location;
	if (!TryGetKnownLocation(World, Location))
	{
		UE_LOG(LogMelodiaAiriBridge, Verbose, TEXT("No semantic location mapping for this world; event skipped"));
		return;
	}

	const TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
	Payload->SetStringField(TEXT("location"), Location);

	const TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>();
	Event->SetStringField(TEXT("id"), FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens));
	Event->SetStringField(TEXT("type"), TEXT("melodia.world.location"));
	Event->SetNumberField(TEXT("version"), 1);
	Event->SetStringField(TEXT("timestamp"), FDateTime::UtcNow().ToIso8601());
	Event->SetObjectField(TEXT("payload"), Payload);

	LastTransmittedType = TEXT("melodia.world.location");
	TWeakObjectPtr<UMelodiaAiriBridgeSubsystem> WeakThis(this);
	const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(FString(RelayRoot) + TEXT("/v1/events"));
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->SetTimeout(1.0f);
	Request->SetContentAsString(SerializeJson(Event));
	Request->OnProcessRequestComplete().BindLambda(
		[WeakThis](FHttpRequestPtr, FHttpResponsePtr Response, const bool bSucceeded)
		{
			if (!WeakThis.IsValid())
			{
				return;
			}
			UMelodiaAiriBridgeSubsystem* Self = WeakThis.Get();
			Self->bRelayConnected = bSucceeded && Response.IsValid() && Response->GetResponseCode() < 500;
			if (!Self->bRelayConnected)
			{
				UE_LOG(LogMelodiaAiriBridge, Verbose, TEXT("Local AIRI relay is offline; gameplay continues"));
			}
		});
	Request->ProcessRequest();
}

bool UMelodiaAiriBridgeSubsystem::PollIntents(float DeltaSeconds)
{
	if (bIntentPollInFlight)
	{
		return true;
	}

	bIntentPollInFlight = true;
	const double RequestStartedAt = FPlatformTime::Seconds();
	TWeakObjectPtr<UMelodiaAiriBridgeSubsystem> WeakThis(this);
	const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(FString(RelayRoot) + TEXT("/v1/intents"));
	Request->SetVerb(TEXT("GET"));
	Request->SetTimeout(1.0f);
	Request->OnProcessRequestComplete().BindLambda(
		[WeakThis, RequestStartedAt](FHttpRequestPtr, FHttpResponsePtr Response, const bool bSucceeded)
		{
			if (!WeakThis.IsValid())
			{
				return;
			}
			UMelodiaAiriBridgeSubsystem* Self = WeakThis.Get();
			Self->bIntentPollInFlight = false;
			Self->LastRoundTripMs = static_cast<float>((FPlatformTime::Seconds() - RequestStartedAt) * 1000.0);
			Self->bRelayConnected = bSucceeded && Response.IsValid() && Response->GetResponseCode() == 200;
			if (Self->bRelayConnected)
			{
				Self->HandlePollResponse(Response->GetContentAsString());
			}
		});
	if (!Request->ProcessRequest())
	{
		bIntentPollInFlight = false;
		bRelayConnected = false;
	}
	return true;
}

void UMelodiaAiriBridgeSubsystem::HandlePollResponse(const FString& ResponseBody)
{
	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseBody);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		RejectIntent(TEXT("malformed-poll-envelope"));
		return;
	}

	if (Root->Values.Num() != 4)
	{
		RejectIntent(TEXT("unexpected-poll-envelope-fields"));
		return;
	}

	FString EnvelopeType;
	FString EnvelopeTimestamp;
	double Version = 0.0;
	if (!Root->TryGetStringField(TEXT("type"), EnvelopeType)
		|| EnvelopeType != TEXT("melodia.bridge.intent_poll")
		|| !Root->TryGetNumberField(TEXT("version"), Version)
		|| Version != 1.0
		|| !Root->TryGetStringField(TEXT("timestamp"), EnvelopeTimestamp)
		|| !IsValidTimestamp(EnvelopeTimestamp))
	{
		RejectIntent(TEXT("unsupported-poll-envelope"));
		return;
	}

	const TSharedPtr<FJsonObject>* Payload = nullptr;
	if (!Root->TryGetObjectField(TEXT("payload"), Payload) || !Payload || !Payload->IsValid())
	{
		RejectIntent(TEXT("malformed-poll-payload"));
		return;
	}
	if ((*Payload)->Values.Num() != 4)
	{
		RejectIntent(TEXT("unexpected-poll-payload-fields"));
		return;
	}

	double QueueDepth = 0.0;
	double RejectedCount = 0.0;
	bool bAiriConnected = false;
	if (!(*Payload)->TryGetNumberField(TEXT("queueDepth"), QueueDepth)
		|| QueueDepth < 0.0 || QueueDepth > 8.0 || FMath::FloorToDouble(QueueDepth) != QueueDepth
		|| !(*Payload)->TryGetNumberField(TEXT("rejected"), RejectedCount)
		|| RejectedCount < 0.0 || FMath::FloorToDouble(RejectedCount) != RejectedCount
		|| !(*Payload)->TryGetBoolField(TEXT("airiConnected"), bAiriConnected))
	{
		RejectIntent(TEXT("malformed-poll-status"));
		return;
	}

	const TSharedPtr<FJsonValue> IntentValue = (*Payload)->TryGetField(TEXT("intent"));
	if (!IntentValue.IsValid())
	{
		RejectIntent(TEXT("missing-intent-field"));
		return;
	}
	if (IntentValue->Type == EJson::Null)
	{
		return;
	}
	if (IntentValue->Type != EJson::Object)
	{
		RejectIntent(TEXT("intent-not-object"));
		return;
	}

	ApplyDebugIntent(IntentValue->AsObject());
}

bool UMelodiaAiriBridgeSubsystem::ApplyDebugIntent(const TSharedPtr<FJsonObject>& Intent)
{
	if (!Intent.IsValid() || Intent->Values.Num() != 5)
	{
		RejectIntent(TEXT("malformed-intent-envelope"));
		return false;
	}

	FString Id;
	FString Type;
	FString Timestamp;
	FGuid ParsedIntentId;
	double Version = 0.0;
	if (!Intent->TryGetStringField(TEXT("id"), Id)
		|| !FGuid::Parse(Id, ParsedIntentId)
		|| !Intent->TryGetStringField(TEXT("type"), Type)
		|| Type != TEXT("melusina.emote")
		|| !Intent->TryGetNumberField(TEXT("version"), Version)
		|| Version != 1.0
		|| !Intent->TryGetStringField(TEXT("timestamp"), Timestamp)
		|| !IsValidTimestamp(Timestamp))
	{
		RejectIntent(TEXT("unsupported-or-malformed-intent"));
		return false;
	}

	const TSharedPtr<FJsonObject>* Payload = nullptr;
	if (!Intent->TryGetObjectField(TEXT("payload"), Payload) || !Payload || !Payload->IsValid() || (*Payload)->Values.Num() != 1)
	{
		RejectIntent(TEXT("malformed-intent-payload"));
		return false;
	}

	FString Emotion;
	if (!(*Payload)->TryGetStringField(TEXT("emotion"), Emotion)
		|| !(Emotion == TEXT("neutral")
			|| Emotion == TEXT("happy")
			|| Emotion == TEXT("curious")
			|| Emotion == TEXT("sad")
			|| Emotion == TEXT("surprised")
			|| Emotion == TEXT("determined")))
	{
		RejectIntent(TEXT("unsupported-emotion"));
		return false;
	}

	const double Now = FPlatformTime::Seconds();
	RecentIntentTimes.RemoveAll([Now](const double AcceptedAt)
	{
		return Now - AcceptedAt >= 60.0;
	});
	if (RecentIntentTimes.Num() >= 5)
	{
		RejectIntent(TEXT("rate-limited"));
		return false;
	}

	RecentIntentTimes.Add(Now);
	LastReceivedType = Type;
	LastAcceptedDebugIntent = FString::Printf(TEXT("melusina.emote(%s)"), *Emotion);
	UE_LOG(LogMelodiaAiriBridge, Log, TEXT("Accepted AIRI intent into debug state: %s"), *LastAcceptedDebugIntent);
	return true;
}

void UMelodiaAiriBridgeSubsystem::RejectIntent(const FString& Reason)
{
	++RejectedIntentCount;
	UE_LOG(LogMelodiaAiriBridge, Warning, TEXT("AIRI intent rejected: %s"), *Reason);
}
