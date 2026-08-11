#include "MelodiaQuantumDrawSubsystem.h"

#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "TimerManager.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaIntegrationConfig.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaRhythmSkillDefinition.h"
#include "MelodiaSongDataAsset.h"

namespace
{
	FName ChartIdForIndex(const int32 Index)
	{
		return FName(*FString::Printf(TEXT("chart_%d"), Index));
	}

	int32 ChartIndexFromId(const FName Id)
	{
		const FString Name = Id.ToString();
		if (!Name.StartsWith(TEXT("chart_")))
		{
			return INDEX_NONE;
		}
		return FCString::Atoi(*Name.RightChop(6));
	}
}

void UMelodiaQuantumDrawSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UGameInstance* GI = GetGameInstance())
	{
		NarrativeSubsystem = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		if (NarrativeSubsystem)
		{
			NarrativeSubsystem->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleBattleRequested);
		}
	}

	// Same collection the audio-reactive layer drives; the quantum params live
	// alongside BeatPulse rather than in a second collection nobody binds.
	QuantumParameterCollection = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"));
	if (!QuantumParameterCollection)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_QUANTUM could not load MPC_Melodia_Palette; quantum presentation will not publish."));
	}

	QuantumTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &ThisClass::TickQuantumPulse));
}

void UMelodiaQuantumDrawSubsystem::Deinitialize()
{
	CancelActiveDraw();
	PendingSongDraws.Reset();
	bProcessingSongDrawQueue = false;

	if (NarrativeSubsystem)
	{
		NarrativeSubsystem->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleBattleRequested);
		NarrativeSubsystem = nullptr;
	}

	if (QuantumTickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(QuantumTickerHandle);
		QuantumTickerHandle.Reset();
	}
	QuantumParameterCollection = nullptr;

	Super::Deinitialize();
}

void UMelodiaQuantumDrawSubsystem::RequestDraw(const int32 Seed, const TArray<FMelodiaDrawCandidate>& Candidates, const FString& Provider, FMelodiaDrawCompleted OnCompleted)
{
	if (bDrawInFlight)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_QUANTUM draw rejected while another request is active; callers should use the song queue."));
		if (OnCompleted.IsBound())
		{
			OnCompleted.Execute(NAME_None, TEXT("busy"), false);
		}
		return;
	}

	// Kept so the published QuantumSeed/QuantumChoice describe THIS draw rather
	// than whatever the previous one happened to leave behind.
	LastDrawSeed = Seed;
	LastCandidateCount = Candidates.Num();

	if (Candidates.Num() < 2)
	{
		OnDrawCompleted.Broadcast(NAME_None, TEXT("classical-baseline"), false);
		if (OnCompleted.IsBound())
		{
			OnCompleted.Execute(NAME_None, TEXT("classical-baseline"), false);
		}
		return;
	}

	UMelodiaIntegrationConfig* Config = NarrativeSubsystem ? NarrativeSubsystem->Config : nullptr;
	if (!Config || !Config->bEnableQuantumDraw || Config->QuantumDrawServiceUrl.IsEmpty())
	{
		OnDrawCompleted.Broadcast(NAME_None, TEXT("classical-baseline"), false);
		if (OnCompleted.IsBound())
		{
			OnCompleted.Execute(NAME_None, TEXT("classical-baseline"), false);
		}
		return;
	}

	const TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
	Payload->SetStringField(TEXT("job_type"), TEXT("rank_layouts"));
	Payload->SetNumberField(TEXT("seed"), Seed);
	Payload->SetStringField(TEXT("backend"), Provider.IsEmpty() ? Config->QuantumDrawProvider : Provider);

	TArray<TSharedPtr<FJsonValue>> CandidateArray;
	for (const FMelodiaDrawCandidate& Candidate : Candidates)
	{
		const TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("id"), Candidate.Id.ToString());
		Entry->SetNumberField(TEXT("difficulty"), Candidate.Difficulty);
		Entry->SetNumberField(TEXT("spacing"), Candidate.Spacing);
		CandidateArray.Add(MakeShared<FJsonValueObject>(Entry));
	}
	Payload->SetArrayField(TEXT("candidates"), CandidateArray);

	FString PayloadString;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&PayloadString);
	FJsonSerializer::Serialize(Payload, Writer);
	Writer->Close();

	const TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
	Request->SetVerb(TEXT("POST"));
	Request->SetURL(Config->QuantumDrawServiceUrl);
	Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	Request->SetContentAsString(PayloadString);

	const uint64 RequestGeneration = ++NextRequestGeneration;
	ActiveRequestGeneration = RequestGeneration;
	bDrawInFlight = true;
	PendingCallback = OnCompleted;

	if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
	{
		World->GetTimerManager().ClearTimer(TimeoutHandle);
		const float TimeoutSeconds = static_cast<float>(Config->QuantumDrawTimeoutMs) / 1000.0f;
		FTimerDelegate TimeoutDelegate;
		TimeoutDelegate.BindLambda([this, RequestGeneration]()
		{
			FinalizeDraw(RequestGeneration, NAME_None, TEXT("timeout"), false);
		});
		World->GetTimerManager().SetTimer(
			TimeoutHandle,
			TimeoutDelegate,
			TimeoutSeconds,
			false);
	}

	// The request stays alive because the lambda captures it by value
	// (TSharedRef copy keeps the refcount up until the callback runs).
	ActiveRequest = Request;
	Request->OnProcessRequestComplete().BindLambda(
		[this, Request, RequestGeneration](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bConnectedSuccessfully)
		{
			FName WinnerId = NAME_None;
			FString Backend = TEXT("classical-baseline");
			bool bSuccess = false;

			if (bConnectedSuccessfully && Res.IsValid() && Res->GetResponseCode() == 200)
			{
				const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Res->GetContentAsString());
				TSharedPtr<FJsonObject> ResponseJson;
				if (FJsonSerializer::Deserialize(Reader, ResponseJson) && ResponseJson.IsValid())
				{
					WinnerId = FName(*ResponseJson->GetStringField(TEXT("winner_id")));
					Backend = ResponseJson->GetStringField(TEXT("backend"));
					bSuccess = ResponseJson->GetStringField(TEXT("status")) == TEXT("completed") && !WinnerId.IsNone();
				}
			}

			UE_LOG(LogTemp, Log, TEXT("MELODIA_QUANTUM draw complete winner=%s backend=%s success=%s"),
				*WinnerId.ToString(), *Backend, bSuccess ? TEXT("true") : TEXT("false"));
			FinalizeDraw(RequestGeneration, WinnerId, Backend, bSuccess);
		});

	if (!Request->ProcessRequest())
	{
		FinalizeDraw(RequestGeneration, NAME_None, TEXT("request-failed"), false);
		return;
	}
	UE_LOG(LogTemp, Log, TEXT("MELODIA_QUANTUM draw requested seed=%d candidates=%d backend=%s url=%s"),
		Seed, Candidates.Num(), *Config->QuantumDrawProvider, *Config->QuantumDrawServiceUrl);
}

void UMelodiaQuantumDrawSubsystem::DrawSongsForBattle(const FName EncounterId)
{
	if (!NarrativeSubsystem || !NarrativeSubsystem->Config || !NarrativeSubsystem->Config->bEnableQuantumDraw)
	{
		return;
	}

	// Battle boundary: a fresh battle draws fresh songs and drops the previous
	// battle's latches, so a draw that lands late can never apply a stale song.
	CancelActiveDraw();
	PendingSongDraws.Reset();
	bProcessingSongDrawQueue = false;
	DrawnAssetsThisBattle.Reset();

	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	UMelodiaRhythmCombatSubsystem* RhythmCombat = World ? World->GetSubsystem<UMelodiaRhythmCombatSubsystem>() : nullptr;
	if (!RhythmCombat)
	{
		return;
	}
	RhythmCombat->ClearSongSelections();

	// One draw per distinct song asset: every skill pointing at the same asset
	// plays the same drawn chart this battle, so 8 skills never fire 8 draws
	// against one song library.
	TSet<FString> DrawnPatternPaths;
	for (const auto& [SkillId, SkillPtr] : RhythmCombat->GetSkillCatalog())
	{
		const UMelodiaRhythmSkillDefinition* Skill = SkillPtr;
		if (!Skill || DrawnPatternPaths.Contains(Skill->PatternAsset.ToSoftObjectPath().ToString()))
		{
			continue;
		}
		const UMelodiaSongDataAsset* SongAsset = Cast<UMelodiaSongDataAsset>(Skill->PatternAsset.LoadSynchronous());
		if (!SongAsset || SongAsset->Songs.Num() < 2)
		{
			// Single-chart library: nothing to draw; the latch stays empty and
			// the rhythm subsystem plays the first chart (classical default).
			continue;
		}
		DrawnPatternPaths.Add(Skill->PatternAsset.ToSoftObjectPath().ToString());
		RequestSongDraw(Skill);
	}
}

void UMelodiaQuantumDrawSubsystem::HandleBattleRequested(const FName EncounterId)
{
	DrawSongsForBattle(EncounterId);
}

void UMelodiaQuantumDrawSubsystem::RequestSongDraw(const UMelodiaRhythmSkillDefinition* Skill)
{
	const UMelodiaSongDataAsset* SongAsset = Cast<UMelodiaSongDataAsset>(Skill->PatternAsset.LoadSynchronous());
	if (!SongAsset || SongAsset->Songs.Num() < 2)
	{
		return;
	}

	const float WindowBeats = static_cast<float>(FMath::Max(1, Skill->IntroBeats) + FMath::Max(1, Skill->ActiveBeats));

	TArray<FMelodiaDrawCandidate> Candidates;
	Candidates.Reserve(SongAsset->Songs.Num());
	for (int32 i = 0; i < SongAsset->Songs.Num(); ++i)
	{
		const FMelodiaSongChart& Chart = SongAsset->Songs[i];

		// Chart-derived weights, so authoring a chart is authoring its draw
		// odds: difficulty from note density (notes per beat), spacing from
		// tempo. Deterministic, documented, no extra authored fields.
		int32 NotesInWindow = 0;
		for (const FMelodiaChartNote& Note : Chart.BasicChartNotes)
		{
			if (Note.TargetBeat <= WindowBeats)
			{
				++NotesInWindow;
			}
		}
		const float Density = NotesInWindow / FMath::Max(1.0f, WindowBeats);
		const float Difficulty = FMath::Clamp(0.1f + 0.8f * (Density / 2.0f), 0.05f, 0.95f);
		const float Spacing = FMath::Clamp(Chart.BPM / 170.0f, 0.1f, 0.95f);

		FMelodiaDrawCandidate Candidate;
		Candidate.Id = ChartIdForIndex(i);
		Candidate.Difficulty = Difficulty;
		Candidate.Spacing = Spacing;
		Candidates.Add(Candidate);

		UE_LOG(LogTemp, Log, TEXT("MELODIA_QUANTUM candidate %s difficulty=%.2f spacing=%.2f (density=%.2f bpm=%.0f)"),
			*Candidate.Id.ToString(), Difficulty, Spacing, Density, Chart.BPM);
	}

	FQueuedSongDraw QueuedDraw;
	QueuedDraw.SkillId = Skill->SkillId;
	QueuedDraw.Seed = static_cast<int32>(FMath::RandRange(0, 100000));
	QueuedDraw.Candidates = MoveTemp(Candidates);
	PendingSongDraws.Add(MoveTemp(QueuedDraw));
	StartNextSongDraw();
}

void UMelodiaQuantumDrawSubsystem::StartNextSongDraw()
{
	if (bDrawInFlight || PendingSongDraws.Num() == 0)
	{
		return;
	}

	FQueuedSongDraw NextDraw = MoveTemp(PendingSongDraws[0]);
	PendingSongDraws.RemoveAt(0);
	PendingSkillId = NextDraw.SkillId;
	bProcessingSongDrawQueue = true;

	FMelodiaDrawCompleted Completion;
	Completion.BindDynamic(this, &ThisClass::HandleSongDrawCompleted);
	RequestDraw(NextDraw.Seed, NextDraw.Candidates, NextDraw.Provider, Completion);
}

void UMelodiaQuantumDrawSubsystem::HandleSongDrawCompleted(const FName WinnerId, const FString Backend, const bool bSuccess)
{
	const FName SkillIdForDraw = PendingSkillId;
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	UMelodiaRhythmCombatSubsystem* RhythmCombat = World ? World->GetSubsystem<UMelodiaRhythmCombatSubsystem>() : nullptr;
	if (RhythmCombat && bSuccess)
	{
		const int32 ChartIndex = ChartIndexFromId(WinnerId);
		if (ChartIndex != INDEX_NONE)
		{
			RhythmCombat->SetSongSelectionIndex(SkillIdForDraw, ChartIndex);
			UE_LOG(LogTemp, Log, TEXT("MELODIA_QUANTUM latched skill=%s song chart index=%d (backend=%s)"),
				*SkillIdForDraw.ToString(), ChartIndex, *Backend);
		}
	}

	PendingSkillId = NAME_None;
	bProcessingSongDrawQueue = false;
	StartNextSongDraw();
}

void UMelodiaQuantumDrawSubsystem::PublishQuantumPresentation(const FName WinnerId, const FString& Backend, const bool bSuccess)
{
	// A failed or timed-out draw is not a quantum moment. Leave the latched
	// values alone and let the pulse keep decaying; publishing a pulse here
	// would fire the exotic overlay on precisely the runs where nothing was
	// actually decided.
	if (!bSuccess)
	{
		return;
	}

	const int32 ChartIndex = ChartIndexFromId(WinnerId);
	if (ChartIndex != INDEX_NONE && LastCandidateCount > 1)
	{
		// The bridge computes 1 - Choice, so Choice must be 0..1.
		LastQuantumChoice = FMath::Clamp(static_cast<float>(ChartIndex) / static_cast<float>(LastCandidateCount - 1), 0.0f, 1.0f);
	}
	else
	{
		LastQuantumChoice = 0.0f;
	}

	LastQuantumSeedNormalized = FMath::Frac(static_cast<float>(LastDrawSeed) / 100000.0f);

	// "classical-baseline" and "timeout" are the two locally-produced backends;
	// anything else came from the service actually answering.
	const bool bQuantumBackend = !Backend.IsEmpty()
		&& !Backend.StartsWith(TEXT("classical"))
		&& !Backend.Equals(TEXT("timeout"), ESearchCase::IgnoreCase);
	LastQuantumBackend = bQuantumBackend ? 1.0f : 0.0f;

	// Colour comes from the winning skill's authored LaneColor rather than a
	// palette invented here.
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (const UMelodiaRhythmCombatSubsystem* RhythmCombat = World ? World->GetSubsystem<UMelodiaRhythmCombatSubsystem>() : nullptr)
	{
		if (const UMelodiaRhythmSkillDefinition* Skill = RhythmCombat->FindSkill(PendingSkillId))
		{
			LastQuantumReactionColor = Skill->LaneColor;
		}
	}

	QuantumPulse = 1.0f;
	WriteQuantumParameters();

	UE_LOG(LogTemp, Log, TEXT("MELODIA_QUANTUM published choice=%.3f seed=%.3f backend=%.0f (%s) colour=%s"),
		LastQuantumChoice, LastQuantumSeedNormalized, LastQuantumBackend, *Backend, *LastQuantumReactionColor.ToString());
}

void UMelodiaQuantumDrawSubsystem::WriteQuantumParameters()
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World || !QuantumParameterCollection)
	{
		return;
	}

	UMaterialParameterCollectionInstance* Instance = World->GetParameterCollectionInstance(QuantumParameterCollection);
	if (!Instance)
	{
		return;
	}

	Instance->SetScalarParameterValue(TEXT("QuantumChoice"), LastQuantumChoice);
	Instance->SetScalarParameterValue(TEXT("QuantumSeed"), LastQuantumSeedNormalized);
	Instance->SetScalarParameterValue(TEXT("QuantumBackend"), LastQuantumBackend);
	Instance->SetScalarParameterValue(TEXT("QuantumPulse"), QuantumPulse);
	Instance->SetVectorParameterValue(TEXT("QuantumReactionColor"), LastQuantumReactionColor);
}

bool UMelodiaQuantumDrawSubsystem::TickQuantumPulse(const float DeltaTime)
{
	if (QuantumPulse <= 0.0f)
	{
		return true;
	}

	QuantumPulse = FMath::Max(0.0f, QuantumPulse - DeltaTime * 3.5f);
	WriteQuantumParameters();
	return true;
}

void UMelodiaQuantumDrawSubsystem::CancelActiveDraw()
{
	if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
	{
		World->GetTimerManager().ClearTimer(TimeoutHandle);
	}

	if (ActiveRequest.IsValid())
	{
		ActiveRequest->CancelRequest();
		ActiveRequest.Reset();
	}

	++NextRequestGeneration;
	ActiveRequestGeneration = NextRequestGeneration;
	bDrawInFlight = false;
	PendingCallback = FMelodiaDrawCompleted();
	PendingSkillId = NAME_None;
}

void UMelodiaQuantumDrawSubsystem::FinalizeDraw(const uint64 RequestGeneration, FName WinnerId, const FString& Backend, bool bSuccess)
{
	if (!bDrawInFlight || RequestGeneration != ActiveRequestGeneration)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MELODIA_QUANTUM ignored stale completion generation=%llu active=%llu"),
			static_cast<unsigned long long>(RequestGeneration),
			static_cast<unsigned long long>(ActiveRequestGeneration));
		return;
	}

	if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
	{
		World->GetTimerManager().ClearTimer(TimeoutHandle);
	}
	ActiveRequest.Reset();

	PublishQuantumPresentation(WinnerId, Backend, bSuccess);
	bDrawInFlight = false;
	OnDrawCompleted.Broadcast(WinnerId, Backend, bSuccess);
	const FMelodiaDrawCompleted Pending = PendingCallback;
	PendingCallback = FMelodiaDrawCompleted();
	if (Pending.IsBound())
	{
		Pending.Execute(WinnerId, Backend, bSuccess);
	}
}
