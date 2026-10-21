#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaLiveVoiceSubsystem.generated.h"

class USoundClass;
class USoundWaveProcedural;
class UAudioComponent;

/**
 * Melusina's LIVE spoken voice: runtime ElevenLabs TTS, dev/showcase only.
 *
 * Created only with -MelodiaLiveVoice (never in Shipping). Sentence-level:
 * one async HTTPS POST per line requesting raw PCM (pcm_24000) -- UE has no
 * runtime MP3 decode path, so the ADS editor MP3 flow stays editor-only.
 * Each utterance gets a FRESH USoundWaveProcedural (the 2026-10-16 mixer
 * crash proved a replayed procedural wave starves the AudioMixer), queued
 * once, played on SCL_Voice so UMelodiaAudioBusSubsystem remains the sole
 * bus-gain writer. Results are cached in-memory by hash(text+voice+model).
 *
 * The API key comes ONLY from the ELEVENLABS_API_KEY environment variable.
 * It is never logged, never stored in config, never committed. With no flag,
 * no key, no voice, or no network this is a total no-op: authored
 * SoundToPlay lines always win and gameplay never blocks.
 *
 * Voice identity is owner-gated: DefaultVoiceId ships EMPTY. Set it in
 * DefaultGame.ini [/Script/BS_GodFile.MelodiaLiveVoiceSubsystem] only after
 * the Phase 1 audition promotes a voice (Tools/AIRI/MelusinaVoicebank).
 */
UCLASS(config = Game)
class BS_GODFILE_API UMelodiaLiveVoiceSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

	/** Speak a line now (queued behind the current utterance, max MaxQueuedLines). */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Live Voice")
	void SpeakLine(const FString& Text, const FString& VoiceIdOverride = FString());

	/** Speak a line attached to an actor (spatial voice); falls back to 2D. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Live Voice")
	void SpeakLineAtActor(const FString& Text, AActor* Speaker, const FString& VoiceIdOverride = FString());

	UFUNCTION(BlueprintCallable, Category = "Melodia|Live Voice")
	void StopSpeaking();

	UFUNCTION(BlueprintPure, Category = "Melodia|Live Voice")
	bool IsSpeaking() const { return bSpeaking; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Live Voice")
	int32 GetCacheHits() const { return CacheHits; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Live Voice")
	int32 GetRequestsMade() const { return RequestsMade; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Live Voice")
	FString GetLastError() const { return LastError; }

	/** Config: promoted Melusina voice ID. Empty = inert. Set in DefaultGame.ini, never a key. */
	UPROPERTY(config, EditDefaultsOnly, Category = "Melodia|Live Voice")
	FString DefaultVoiceId;

	UPROPERTY(config, EditDefaultsOnly, Category = "Melodia|Live Voice")
	FString ModelId = TEXT("eleven_multilingual_v2");

	/** PCM sample rate requested from the provider; must match PlayPCM. */
	UPROPERTY(config, EditDefaultsOnly, Category = "Melodia|Live Voice", meta = (ClampMin = "8000", ClampMax = "48000"))
	int32 SampleRate = 24000;

	UPROPERTY(config, EditDefaultsOnly, Category = "Melodia|Live Voice", meta = (ClampMin = "1", ClampMax = "16"))
	int32 MaxQueuedLines = 4;

private:
	struct FPendingLine
	{
		FString Text;
		FString VoiceId;
		TWeakObjectPtr<AActor> Speaker;
	};

	UFUNCTION()
	void OnUtteranceFinished();

	void HandleUnvoicedADSLine(const FString& Text, const FString& ParticipantTag, AActor* Speaker);
	void ConsoleSpeak(const TArray<FString>& Args);
	class IConsoleObject* SpeakCommand = nullptr;
	void EnqueueLine(const FString& Text, const FString& VoiceId, AActor* Speaker);
	void PumpQueue();
	void StartRequest(const FPendingLine& Line);
	void PlayPCM(const TArray<uint8>& PCMBytes, AActor* Speaker);
	FString ResolveApiKey() const;
	static FString CacheKey(const FString& Text, const FString& VoiceId, const FString& Model);

	TArray<FPendingLine> Queue;
	TMap<FString, TArray<uint8>> PCMCache;
	bool bSpeaking = false;
	bool bRequestInFlight = false;
	bool bWarnedNoKey = false;
	int32 CacheHits = 0;
	int32 RequestsMade = 0;
	FString LastError;

	UPROPERTY(Transient)
	TObjectPtr<USoundClass> VoiceClass;

	UPROPERTY(Transient)
	TObjectPtr<USoundWaveProcedural> ActiveWave;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> ActiveAudio;
};
