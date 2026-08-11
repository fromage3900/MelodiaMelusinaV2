#include "MelodiaJRPGPresentationRhythmComponent.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "MelodiaAudioComponent.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaUIBridgeSubsystem.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Engine/GameInstance.h"
#include "HarmonixMetasound/Components/MusicClockComponent.h"

void UMelodiaJRPGPresentationRhythmComponent::BeginPlay()
{
	Super::BeginPlay();

	// Bind before the Quartz early-out below, or the session-complete fan-out is
	// silently skipped on every actor that has the fallback turned off.
	if (UMelodiaRhythmCombatSubsystem* RhythmCombat = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaRhythmCombatSubsystem>() : nullptr)
	{
		RhythmCombat->OnRhythmComplete.AddDynamic(this, &UMelodiaJRPGPresentationRhythmComponent::HandleRhythmSessionCompleted);
	}

	UMelodiaMusicClockSubsystem* MusicClock = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr;

	// Register the authored Harmonix clock first. It is preferred whenever it
	// is running; Quartz is only the fallback.
	if (MusicClock && HarmonixClock)
	{
		MusicClock->RegisterMusicClock(HarmonixClock);
		RegisteredHarmonixClock = HarmonixClock;
	}

	AActor* Owner = GetOwner();
	UMelodiaAudioComponent* Audio = Owner ? Owner->FindComponentByClass<UMelodiaAudioComponent>() : nullptr;

	// Live audio binds regardless of which clock authority is active, so the
	// battle BGM, metronome and grade tones keep working under Harmonix too.
	if (Audio && MusicClock)
	{
		MusicClock->RegisterQuartzAudioComponent(Audio);
		RegisteredQuartzAudio = Audio;
		MusicClock->OnMelodiaBeat.AddUniqueDynamic(this, &UMelodiaJRPGPresentationRhythmComponent::HandleMelodiaBeat);
		if (bPlayBattleBGM)
		{
			Audio->PlayBGMQuantized();
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia stock rhythm presentation has no Quartz audio component to register."));
	}

	if (!bEnableQuartzFallback)
	{
		return;
	}

	if (Audio && MusicClock)
	{
		// Harmonix remains preferred. Starting Quartz here merely guarantees an
		// honest sample-accurate fallback if the authored clock is absent or stops.
		Audio->StartBattleClock(QuartzFallbackBPM);
	}
}

void UMelodiaJRPGPresentationRhythmComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UMelodiaRhythmCombatSubsystem* RhythmCombat = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaRhythmCombatSubsystem>() : nullptr)
	{
		RhythmCombat->OnRhythmComplete.RemoveDynamic(this, &UMelodiaJRPGPresentationRhythmComponent::HandleRhythmSessionCompleted);
	}

	if (UMelodiaMusicClockSubsystem* MusicClock = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr)
	{
		MusicClock->OnMelodiaBeat.RemoveDynamic(this, &UMelodiaJRPGPresentationRhythmComponent::HandleMelodiaBeat);
		MusicClock->UnregisterQuartzAudioComponent(RegisteredQuartzAudio.Get());
		MusicClock->UnregisterMusicClock(RegisteredHarmonixClock.Get());
	}
	if (UMelodiaAudioComponent* Audio = RegisteredQuartzAudio.Get())
	{
		Audio->StopBGM();
	}
	RegisteredQuartzAudio.Reset();
	RegisteredHarmonixClock.Reset();

	Super::EndPlay(EndPlayReason);
}

FJRPGPresentationRhythmResult UMelodiaJRPGPresentationRhythmComponent::EvaluateTimingError(const float TimingErrorMs) const
{
	const FMelodiaRhythmGradeResult GradeResult =
		UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(FMath::Abs(TimingErrorMs), RhythmWindows);

	FJRPGPresentationRhythmResult Result;
	Result.Grade = GradeResult.Grade;
	Result.PresentationScalar = GetPresentationScalar(GradeResult.Grade);
	Result.HitCount = GradeResult.bCountsAsHit ? 1 : 0;
	Result.MissCount = GradeResult.bCountsAsHit ? 0 : 1;
	return Result;
}

FJRPGPresentationRhythmResult UMelodiaJRPGPresentationRhythmComponent::RecordTimingError(const float TimingErrorMs)
{
	const FJRPGPresentationRhythmResult Result = EvaluateTimingError(TimingErrorMs);

	// Live audio: per-hit grade tone (Perfect 880 / Great 660 / Good 440 / Miss 220 Hz).
	if (UMelodiaAudioComponent* Audio = RegisteredQuartzAudio.Get())
	{
		Audio->PlayHitSFX(Result.Grade);
	}

	OnPresentationRhythmResult.Broadcast(Result);
	return Result;
}

void UMelodiaJRPGPresentationRhythmComponent::HandleMelodiaBeat(int32 BeatNumber, int32 BeatInBar)
{
	if (bPlayMetronomeClick)
	{
		if (UMelodiaAudioComponent* Audio = RegisteredQuartzAudio.Get())
		{
			Audio->PlayMetronomeClick();
		}
	}
}

FJRPGPresentationRhythmResult UMelodiaJRPGPresentationRhythmComponent::RecordInputNow()
{
	const UWorld* World = GetWorld();
	const UMelodiaMusicClockSubsystem* MusicClock = World ? World->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr;

	if (!MusicClock || !MusicClock->HasMusicalTime())
	{
		// No musical time means nothing to decorate.  The stock command that
		// triggered this still resolves normally; it just gets no flourish.
		FJRPGPresentationRhythmResult Silent;
		Silent.PresentationScalar = 0.0f;
		return Silent;
	}

	return RecordTimingError(MusicClock->GetTimingErrorMsToNearestBeat());
}

void UMelodiaJRPGPresentationRhythmComponent::HandleRhythmSessionCompleted(const EMelodiaSkillGrade Grade, const int32 HitCount, const int32 MissCount)
{
	// EMelodiaSkillGrade and EMelodiaRhythmGrade declare the same four members in
	// the same order; map explicitly rather than casting so a future divergence in
	// either enum becomes a compile error instead of a silent mis-grade.
	FJRPGPresentationRhythmResult Result;
	switch (Grade)
	{
	case EMelodiaSkillGrade::Perfect:	Result.Grade = EMelodiaRhythmGrade::Perfect;	break;
	case EMelodiaSkillGrade::Great:		Result.Grade = EMelodiaRhythmGrade::Great;		break;
	case EMelodiaSkillGrade::Good:		Result.Grade = EMelodiaRhythmGrade::Good;		break;
	case EMelodiaSkillGrade::Miss:		Result.Grade = EMelodiaRhythmGrade::Miss;		break;
	}

	Result.PresentationScalar = GetPresentationScalar(Result.Grade);
	Result.HitCount = HitCount;
	Result.MissCount = MissCount;

	// Presentation fan-out only. Nothing here may touch the authoritative session:
	// ClearPendingDamageMultiplier would wipe the scalar FinishSession just
	// latched, and the damage notify that reads it is an async callback this
	// fan-out cannot observe.
	OnPresentationRhythmResult.Broadcast(Result);

	// Drive the Melodia battle overlay's own grade readout. Fetched per call rather
	// than cached at BeginPlay: the bridge is GameInstance-scoped and outlives this
	// world, and the overlay widget itself only exists for the duration of a battle.
	// A false return is normal outside battle and is not an error here.
	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			if (UMelodiaUIBridgeSubsystem* UIBridge = GameInstance->GetSubsystem<UMelodiaUIBridgeSubsystem>())
			{
				UIBridge->ShowRhythmGradeOnBattleUI(
					UMelodiaRhythmCombatSubsystem::GradeToText(Grade).ToString(), HitCount, MissCount);
			}
		}
	}

	// Reactivity fan-out: the only edge from the LIVE rhythm stack into
	// UMelodiaRhythmReactivitySubsystem, which owns the MPC drive and the OSC
	// stream to TouchDesigner on 127.0.0.1:9000.
	//
	// Every other caller of Notify*() lives in UMelodiaBattleSession /
	// AMelodiaBattleArena -- quarantined MelodiaCore classes that nothing
	// instantiates (AMelodiaEncounterTrigger routes exclusively to the stock JRPG
	// bridge). So the transport, encoder and TD-side receiver were all correct and
	// simply never fed. This is presentation-only and respects the constraint
	// above: it reads the already-computed Result and touches no session state.
	if (UMelodiaRhythmReactivitySubsystem* Reactivity =
			UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		const int32 Total = HitCount + MissCount;
		const float Accuracy = Total > 0 ? static_cast<float>(HitCount) / static_cast<float>(Total) : 0.0f;

		// CommandEnergy is clamped 0-2 subsystem-side; PresentationScalar is the
		// per-grade weight this component already publishes to the rest of the UI,
		// so the OSC stream and the on-screen flourish agree by construction.
		Reactivity->NotifyCommandResolved(
			Result.Grade,
			Result.PresentationScalar,
			Accuracy,
			Accuracy,
			/*InRhythmElement*/ 0);
	}
}

float UMelodiaJRPGPresentationRhythmComponent::GetPresentationScalar(const EMelodiaRhythmGrade Grade)
{
	switch (Grade)
	{
	case EMelodiaRhythmGrade::Perfect:
		return 1.0f;
	case EMelodiaRhythmGrade::Great:
		return 0.8f;
	case EMelodiaRhythmGrade::Good:
		return 0.6f;
	case EMelodiaRhythmGrade::Miss:
	default:
		return 0.25f;
	}
}
