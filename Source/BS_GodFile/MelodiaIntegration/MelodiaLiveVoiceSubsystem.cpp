// Copyright Melodia. Dev-gated live ElevenLabs speech. See header for the contract.

#include "MelodiaLiveVoiceSubsystem.h"

#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Dom/JsonObject.h"
#include "Graph/ADSGraphNode.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundWaveProcedural.h"

DEFINE_LOG_CATEGORY_STATIC(LogMelodiaLiveVoice, Log, All);

namespace
{
	constexpr int32 PCMBytesPerSample = 2; // pcm_* is signed 16-bit mono
}

bool UMelodiaLiveVoiceSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
#if UE_BUILD_SHIPPING
	return false;
#else
	return Super::ShouldCreateSubsystem(Outer)
		&& FParse::Param(FCommandLine::Get(), TEXT("MelodiaLiveVoice"));
#endif
}

void UMelodiaLiveVoiceSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	if (!InWorld.IsGameWorld() || InWorld.GetNetMode() == NM_DedicatedServer)
	{
		return;
	}

	VoiceClass = LoadObject<USoundClass>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Voice.SCL_Voice"));

	// ADS hook: authored SoundToPlay always wins; this fires only for silent nodes.
	UADSGraphNode::OnUnvoicedLine.AddUObject(this, &ThisClass::HandleUnvoicedADSLine);

	// Debug trigger v1: `Melodia.Speak <line...>` in the game console.
	SpeakCommand = IConsoleManager::Get().RegisterConsoleCommand(
		TEXT("Melodia.Speak"),
		TEXT("Melodia.Speak <line...> -- speak a line with Melusina's live voice (dev, -MelodiaLiveVoice)"),
		FConsoleCommandWithArgsDelegate::CreateUObject(this, &ThisClass::ConsoleSpeak),
		ECVF_Cheat);

	if (DefaultVoiceId.IsEmpty())
	{
		UE_LOG(LogMelodiaLiveVoice, Warning,
			TEXT("Live voice active but DefaultVoiceId is empty (Phase 1 audition gate). SpeakLine will no-op until a voice is promoted."));
	}
	UE_LOG(LogMelodiaLiveVoice, Log, TEXT("Melodia live voice ready (model=%s, voice set=%s)"),
		*ModelId, DefaultVoiceId.IsEmpty() ? TEXT("no") : TEXT("yes"));
}

void UMelodiaLiveVoiceSubsystem::ConsoleSpeak(const TArray<FString>& Args)
{
	SpeakLine(FString::Join(Args, TEXT(" ")));
}

void UMelodiaLiveVoiceSubsystem::Deinitialize()
{
	if (SpeakCommand)
	{
		IConsoleManager::Get().UnregisterConsoleObject(SpeakCommand);
		SpeakCommand = nullptr;
	}
	UADSGraphNode::OnUnvoicedLine.RemoveAll(this);
	StopSpeaking();
	Queue.Empty();
	Super::Deinitialize();
}

void UMelodiaLiveVoiceSubsystem::HandleUnvoicedADSLine(const FString& Text, const FString& /*ParticipantTag*/, AActor* Speaker)
{
	SpeakLineAtActor(Text, Speaker);
}

void UMelodiaLiveVoiceSubsystem::SpeakLine(const FString& Text, const FString& VoiceIdOverride)
{
	EnqueueLine(Text, VoiceIdOverride, nullptr);
}

void UMelodiaLiveVoiceSubsystem::SpeakLineAtActor(const FString& Text, AActor* Speaker, const FString& VoiceIdOverride)
{
	EnqueueLine(Text, VoiceIdOverride, Speaker);
}

void UMelodiaLiveVoiceSubsystem::EnqueueLine(const FString& Text, const FString& VoiceIdOverride, AActor* Speaker)
{
	const FString Clean = Text.TrimStartAndEnd();
	if (Clean.IsEmpty())
	{
		return;
	}
	const FString VoiceId = !VoiceIdOverride.IsEmpty() ? VoiceIdOverride : DefaultVoiceId;
	if (VoiceId.IsEmpty())
	{
		UE_LOG(LogMelodiaLiveVoice, Verbose, TEXT("SpeakLine dropped: no voice ID promoted yet"));
		return;
	}
	if (Queue.Num() >= MaxQueuedLines)
	{
		Queue.Pop(EAllowShrinking::No); // newest-wins for barks
	}
	Queue.Add(FPendingLine{Clean, VoiceId, Speaker});
	PumpQueue();
}

void UMelodiaLiveVoiceSubsystem::OnUtteranceFinished()
{
	// Natural end of one line: release the wave/component, keep the queue.
	ActiveAudio = nullptr;
	ActiveWave = nullptr;
	bSpeaking = false;
	PumpQueue();
}

void UMelodiaLiveVoiceSubsystem::StopSpeaking()
{
	Queue.Empty();
	if (IsValid(ActiveAudio))
	{
		ActiveAudio->Stop();
	}
	ActiveAudio = nullptr;
	ActiveWave = nullptr;
	bSpeaking = false;
}

FString UMelodiaLiveVoiceSubsystem::ResolveApiKey() const
{
	return FPlatformMisc::GetEnvironmentVariable(TEXT("ELEVENLABS_API_KEY")).TrimStartAndEnd();
}

FString UMelodiaLiveVoiceSubsystem::CacheKey(const FString& Text, const FString& VoiceId, const FString& Model)
{
	return FString::Printf(TEXT("%s|%s|%s"), *VoiceId, *Model, *Text);
}

void UMelodiaLiveVoiceSubsystem::PumpQueue()
{
	if (bSpeaking || bRequestInFlight || Queue.IsEmpty())
	{
		return;
	}
	const FPendingLine Line = Queue[0];
	Queue.RemoveAt(0);

	const FString Key = CacheKey(Line.Text, Line.VoiceId, ModelId);
	if (const TArray<uint8>* Cached = PCMCache.Find(Key))
	{
		++CacheHits;
		UE_LOG(LogMelodiaLiveVoice, Log, TEXT("Live voice cache hit (%d bytes), no API call"), Cached->Num());
		PlayPCM(*Cached, Line.Speaker.Get());
		return;
	}
	StartRequest(Line);
}

void UMelodiaLiveVoiceSubsystem::StartRequest(const FPendingLine& Line)
{
	const FString ApiKey = ResolveApiKey();
	if (ApiKey.IsEmpty())
	{
		LastError = TEXT("ELEVENLABS_API_KEY not set");
		if (!bWarnedNoKey)
		{
			bWarnedNoKey = true;
			UE_LOG(LogMelodiaLiveVoice, Warning,
				TEXT("Live voice inert: ELEVENLABS_API_KEY environment variable is not set. Lines are dropped, gameplay continues."));
		}
		PumpQueue();
		return;
	}

	const TSharedRef<FJsonObject> Body = MakeShared<FJsonObject>();
	Body->SetStringField(TEXT("text"), Line.Text);
	Body->SetStringField(TEXT("model_id"), ModelId);
	FString BodyString;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyString);
	FJsonSerializer::Serialize(Body, Writer);

	const FString Url = FString::Printf(
		TEXT("https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=pcm_%d"),
		*FGenericPlatformHttp::UrlEncode(Line.VoiceId), SampleRate);

	bRequestInFlight = true;
	++RequestsMade;
	TWeakObjectPtr<UMelodiaLiveVoiceSubsystem> WeakThis(this);
	const FString Key = CacheKey(Line.Text, Line.VoiceId, ModelId);
	TWeakObjectPtr<AActor> WeakSpeaker = Line.Speaker;

	const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
	Request->SetURL(Url);
	Request->SetVerb(TEXT("POST"));
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->SetHeader(TEXT("xi-api-key"), ApiKey); // never logged
	Request->SetTimeout(30.0f);
	Request->SetContentAsString(BodyString);
	Request->OnProcessRequestComplete().BindLambda(
		[WeakThis, Key, WeakSpeaker](FHttpRequestPtr, FHttpResponsePtr Response, const bool bSucceeded)
		{
			if (!WeakThis.IsValid())
			{
				return;
			}
			UMelodiaLiveVoiceSubsystem* Self = WeakThis.Get();
			Self->bRequestInFlight = false;

			const int32 Code = Response.IsValid() ? Response->GetResponseCode() : 0;
			if (!bSucceeded || Code != 200 || !Response.IsValid())
			{
				Self->LastError = FString::Printf(TEXT("ElevenLabs HTTP %d"), Code);
				UE_LOG(LogMelodiaLiveVoice, Warning, TEXT("Live voice request failed (HTTP %d); line dropped"), Code);
				Self->PumpQueue();
				return;
			}
			const TArray<uint8>& Bytes = Response->GetContent();
			if (Bytes.Num() < PCMBytesPerSample)
			{
				Self->LastError = TEXT("Empty PCM response");
				Self->PumpQueue();
				return;
			}
			Self->PCMCache.Add(Key, Bytes);
			Self->PlayPCM(Bytes, WeakSpeaker.Get());
		});
	if (!Request->ProcessRequest())
	{
		bRequestInFlight = false;
		LastError = TEXT("HTTP request failed to start");
		PumpQueue();
	}
}

void UMelodiaLiveVoiceSubsystem::PlayPCM(const TArray<uint8>& PCMBytes, AActor* Speaker)
{
	// Fresh wave per utterance: a replayed procedural wave has a spent queue
	// and starved the AudioMixer on 2026-10-16. Never reuse ActiveWave.
	USoundWaveProcedural* Wave = NewObject<USoundWaveProcedural>(this);
	Wave->SetSampleRate(SampleRate);
	Wave->NumChannels = 1;
	Wave->Duration = static_cast<float>(PCMBytes.Num() / PCMBytesPerSample) / static_cast<float>(SampleRate);
	Wave->bLooping = false;
	if (VoiceClass)
	{
		Wave->SoundClassObject = VoiceClass; // SCL_Voice: AudioBus subsystem owns the gain
	}
	Wave->QueueAudio(PCMBytes.GetData(), PCMBytes.Num());
	ActiveWave = Wave;

	UAudioComponent* Audio = nullptr;
	if (IsValid(Speaker))
	{
		if (USceneComponent* Root = Speaker->GetRootComponent())
		{
			Audio = UGameplayStatics::SpawnSoundAttached(Wave, Root);
		}
	}
	if (!Audio)
	{
		Audio = UGameplayStatics::SpawnSound2D(this, Wave);
	}
	if (!Audio)
	{
		LastError = TEXT("Failed to spawn voice audio");
		ActiveWave = nullptr;
		PumpQueue();
		return;
	}

	ActiveAudio = Audio;
	bSpeaking = true;
	Audio->OnAudioFinished.AddDynamic(this, &ThisClass::OnUtteranceFinished);
	UE_LOG(LogMelodiaLiveVoice, Log, TEXT("Speaking live line (%.2fs PCM, speaker=%s)"),
		Wave->Duration, Speaker ? *Speaker->GetName() : TEXT("2D"));
}
