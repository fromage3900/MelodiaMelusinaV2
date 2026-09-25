// Copyright Melodia. Transport authority for the Listening Field phrase bus.
//
// Receives melodia.phrase/v1 state over OSC/UDP 127.0.0.1:9002 (see
// Tools/phrase_bridge/ and Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md)
// and republishes it on the game thread. TRANSPORT ONLY: this subsystem
// never writes MPCs, never drives Niagara, never moves sheep, never compiles
// World Compiler recipes, never interprets melodia.directive/v1. for_bar = N+1
// latency is Jev's job (Tools/listening_field/directive_schema.py). Consumers
// subscribe to the delegates and stay single-writer on their own surfaces.
//
// OSC subset — exactly Tools/phrase_bridge/bridge.py _send_state / boundary:
//   /melodia/phrase/state    ",isifsfi"  [idx:i, SECTION:s, bar:i, energy:f,
//                                         TREND:s, conf:f, pulse:i 0|1]
//   /melodia/phrase/boundary ",ii"       [phrase_index, bar]
// beat_in_bar exists on the JSON schema but is not on this wire; BeatInBar
// stays 0. Unknown addresses are ignored.
//
// Choral Sheep consumer: existing TryBeginHarmonize (PIE 2026-09-20).
// Bind OnPhraseBoundary from BP after closed-editor UBT of RecvFrom ingest.
// HOLD / TURN_TO_PLAYER / SPIRAL_FORMATION are not C++ motion. layout_seed
// is a WC key pick only (see LAYOUT_SEEDS in directive_schema.py).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Containers/Ticker.h"
#include "MelodiaPhraseBusSubsystem.generated.h"

class FSocket;

UENUM(BlueprintType)
enum class EMelodiaPhraseSection : uint8
{
	SPARSE	UMETA(DisplayName = "Sparse"),
	VOICE	UMETA(DisplayName = "Voice"),
	BUILD	UMETA(DisplayName = "Build"),
	CLIMAX	UMETA(DisplayName = "Climax"),
	RELEASE	UMETA(DisplayName = "Release")
};

UENUM(BlueprintType)
enum class EMelodiaEnergyTrend : uint8
{
	FALLING	UMETA(DisplayName = "Falling"),
	FLAT	UMETA(DisplayName = "Flat"),
	RISING	UMETA(DisplayName = "Rising")
};

/** One melodia.phrase/v1 sample. Fields mirror Tools/phrase_bridge/phrase_schema.py. */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaPhraseState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	int32 PhraseIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	EMelodiaPhraseSection Section = EMelodiaPhraseSection::SPARSE;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	int32 Bar = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	float BeatInBar = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	float Energy = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	EMelodiaEnergyTrend EnergyTrend = EMelodiaEnergyTrend::FLAT;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	float Confidence = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Phrase Bus")
	bool bBoundaryPulse = false;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMelodiaPhraseState, const FMelodiaPhraseState&, State);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMelodiaPhraseBoundary, int32, PhraseIndex, int32, Bar);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMelodiaPhraseTimeout);

/**
 * Single-writer transport for live musical phrase state.
 *
 * Polls a non-blocking UDP socket on the game thread via FTSTicker — no
 * receiver thread, no locking, safe for all delegates. If no state arrives
 * for TimeoutSeconds (default 6 s = two bars at the 80 BPM trace authority),
 * the bus fires OnPhraseTimeout exactly once; deterministic settle is the
 * conductor's job, this only reports the silence.
 */
UCLASS()
class BS_GODFILE_API UMelodiaPhraseBusSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Phrase Bus")
	void StartListening(int32 Port = 9002);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Phrase Bus")
	void StopListening();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Phrase Bus")
	bool IsListening() const { return Socket != nullptr; }

	UFUNCTION(BlueprintCallable, Category = "Melodia|Phrase Bus")
	const FMelodiaPhraseState& GetCurrentState() const { return CurrentState; }

	/** Seconds of silence before OnPhraseTimeout fires. Default 6 s (2 bars @ 80 BPM). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Phrase Bus")
	float TimeoutSeconds = 6.0f;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Phrase Bus")
	FOnMelodiaPhraseState OnPhraseState;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Phrase Bus")
	FOnMelodiaPhraseBoundary OnPhraseBoundary;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Phrase Bus")
	FOnMelodiaPhraseTimeout OnPhraseTimeout;

private:
	bool PollSocket(float DeltaSeconds);
	bool ParseOscPacket(const uint8* Data, int32 Size);
	bool ParseStateMessage(const uint8* Payload, int32 Size);

	FSocket* Socket = nullptr;
	FTSTicker::FDelegateHandle TickerHandle;
	FMelodiaPhraseState CurrentState;
	double LastPacketTime = 0.0;
	bool bTimeoutFired = false;
};
