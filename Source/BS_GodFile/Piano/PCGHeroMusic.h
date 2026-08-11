#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include "PCGPoint.h"
#include "MelodiaCoreRulesLibrary.h"
#include "PCGHeroMusic.generated.h"

// Hero music contract: native overlap handlers remain reflected for PCG-spawned nodes.

class UBoxComponent;
class UMelodiaAudioComponent;
class UPCGComponent;
class UPCGGraph;
class UPCGMetadata;
class UMaterialInterface;
class UPrimitiveComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UProceduralMeshComponent;

USTRUCT(BlueprintType)
struct BS_GODFILE_API FPCGHeroMusicNodeDimensions
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Geometry")
	float Width = 110.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Geometry")
	float Depth = 110.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Geometry")
	float Height = 16.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Animation", meta = (ClampMin = "0.0"))
	float PressDepth = 6.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Animation", meta = (ClampMin = "0.0"))
	float SpringStiffness = 1100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Animation", meta = (ClampMin = "0.0"))
	float SpringDamping = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hero Music|Animation", meta = (ClampMin = "0.0"))
	float PressTriggerHeight = 20.0f;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FPCGHeroMusicNoteEvent
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	int32 NodeIndex = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	int32 Lane = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	int32 MidiNote = 60;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	float TimingErrorMs = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	EMelodiaRhythmGrade Grade = EMelodiaRhythmGrade::Miss;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Note")
	TObjectPtr<AActor> InteractingActor = nullptr;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FPCGHeroMusicScoreState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 TotalNotes = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 HitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 PerfectCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 MissCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 Streak = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	int32 Score = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	bool bCompleted = false;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UPCGHeroMusicProfile : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Layout")
	FPCGHeroMusicNodeDimensions NodeDimensions;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music")
	TArray<int32> MidiNotes;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music")
	int32 ExpectedNoteCount = 12;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music", meta = (ClampMin = "0.0"))
	float BeatWindowBeats = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music")
	bool bSequentialProgression = false;

	/** Play the existing hit/miss grade cues in addition to the musical note. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music")
	bool bPlayGradeFeedbackSFX = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Music")
	FMelodiaRhythmWindows RhythmWindows;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UStaticMesh> NodeMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UMaterialInterface> NodeMaterial;

	/** Optional piano-authentic split. A sharp/flat MIDI pitch uses the ebony
	 * references; natural pitches use the ivory references. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UStaticMesh> WhiteNodeMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UStaticMesh> BlackNodeMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UMaterialInterface> WhiteNodeMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Visuals")
	TSoftObjectPtr<UMaterialInterface> BlackNodeMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Render")
	float InstanceEndCullDistance = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Render")
	int32 CustomDepthStencilValue = 3;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Render")
	bool bWriteCustomDepth = true;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FPCGHeroMusicNodeEvent, FPCGHeroMusicNoteEvent, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FPCGHeroMusicStationEvent, int32, StationIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FPCGHeroMusicCompletionEvent);

class APCGHeroMusicGraphHost;

UCLASS(Blueprintable)
class BS_GODFILE_API APCGHeroMusicNode : public AActor
{
	GENERATED_BODY()

public:
	APCGHeroMusicNode();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Called by PCGSpawnActor so the point seed is the gameplay identity. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Hero Music|PCG")
	void InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata);

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	int32 GetNodeIndex() const { return NodeIndex; }

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	int32 GetLane() const { return Lane; }

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	int32 GetMidiNote() const { return MidiNote; }

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	int32 GetSeedIdentity() const { return SeedIdentity; }

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	bool IsPressed() const { return bIsPressed; }

	UFUNCTION(BlueprintCallable, Category = "Hero Music|Node")
	void SetPressedForActor(AActor* SteppingActor, bool bPressedForActor);

	UFUNCTION(BlueprintPure, Category = "Hero Music|Node")
	APCGHeroMusicGraphHost* GetHost() const { return HostOwner.Get(); }

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UStaticMeshComponent> NodeMeshComponent;

	/** Authored at runtime/editor from a chamfered key profile so hero pads are
	 * actual beveled geometry even when an imported preview mesh is only a box. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UProceduralMeshComponent> BeveledKeyMeshComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UBoxComponent> NodeBlocker;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UBoxComponent> StepTrigger;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Events")
	FPCGHeroMusicNodeEvent OnNoteActivated;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Events")
	FPCGHeroMusicNodeEvent OnNoteDeactivated;

	void SetHost(APCGHeroMusicGraphHost* InHost);

private:
	void ResolveHost();

protected:
	virtual void ApplyProfileGeometry();

private:
	void RebuildBeveledKeyGeometry(float Width, float Depth, float Height, UMaterialInterface* Material);
	UFUNCTION()
	void HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
	UFUNCTION()
	void HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
	void BeginNodePress(AActor* SteppingActor);
	void EndNodePress(AActor* SteppingActor);
	bool IsPlayerControlledPawn(AActor* OtherActor) const;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Hero Music|PCG", meta = (AllowPrivateAccess = "true"))
	int32 NodeIndex = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Hero Music|PCG", meta = (AllowPrivateAccess = "true"))
	int32 Lane = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Hero Music|PCG", meta = (AllowPrivateAccess = "true"))
	int32 MidiNote = 60;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Hero Music|PCG", meta = (AllowPrivateAccess = "true"))
	int32 SeedIdentity = 0;

	TWeakObjectPtr<APCGHeroMusicGraphHost> HostOwner;
	TSet<TWeakObjectPtr<AActor>> PressingActors;
	float CurrentPressOffset = 0.0f;
	float PressVelocity = 0.0f;
	bool bIsPressed = false;
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGHeroMusicGraphHost : public AActor
{
	GENERATED_BODY()

public:
	APCGHeroMusicGraphHost();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UPCGComponent> PCGComponent;

	/** Supplies a valid editor/runtime generation bounds for authored point graphs. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UBoxComponent> GenerationBounds;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Hero Music|Components")
	TObjectPtr<UMelodiaAudioComponent> AudioComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Configuration")
	TObjectPtr<UPCGHeroMusicProfile> Profile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Configuration")
	TObjectPtr<UPCGGraph> MusicGraph;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Events")
	FPCGHeroMusicNodeEvent OnNoteJudged;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Events")
	FPCGHeroMusicCompletionEvent OnPatternCompleted;

	UPROPERTY(BlueprintReadOnly, Category = "Hero Music|Score")
	FPCGHeroMusicScoreState ScoreState;

	UFUNCTION(BlueprintPure, Category = "Hero Music|Score")
	FPCGHeroMusicScoreState GetScoreState() const { return ScoreState; }

	UFUNCTION(BlueprintPure, Category = "Hero Music|Score")
	int32 GetRegisteredNodeCount() const { return RegisteredNodes.Num(); }

	void RegisterNode(APCGHeroMusicNode* Node);
	void UnregisterNode(APCGHeroMusicNode* Node);

protected:
	virtual void HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event);
	void RecordProgressionMiss();
	bool TryGetCurrentMusicBeat(double& OutBeat) const;
	void MarkCompleted();

private:
	UFUNCTION()
	void HandleNodeActivated(FPCGHeroMusicNoteEvent Event);

	void ApplyNoteToScore(const FPCGHeroMusicNoteEvent& Event);
	void ApplyCrescendoResponse();

	UPROPERTY()
	TSet<TObjectPtr<APCGHeroMusicNode>> RegisteredNodes;
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGResonanceCathedralHost : public APCGHeroMusicGraphHost
{
	GENERATED_BODY()

public:
	APCGResonanceCathedralHost();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Cathedral")
	int32 StationCount = 4;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Cathedral")
	FPCGHeroMusicStationEvent OnStationCompleted;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Cathedral")
	FPCGHeroMusicCompletionEvent OnCathedralCompleted;

	UFUNCTION(BlueprintPure, Category = "Hero Music|Cathedral")
	int32 GetActiveStation() const { return ActiveStation; }

protected:
	virtual void HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event) override;

private:
	int32 ActiveStation = 0;
	int32 ExpectedDegree = 0;
	double StationStartBeat = 0.0;
	bool bHasStationStartBeat = false;
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGArpeggioBridgeHost : public APCGHeroMusicGraphHost
{
	GENERATED_BODY()

public:
	APCGArpeggioBridgeHost();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Bridge")
	int32 NoteCount = 24;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Bridge")
	FPCGHeroMusicCompletionEvent OnBridgeCompleted;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Bridge")
	TObjectPtr<AActor> CompletionGate;

	UFUNCTION(BlueprintPure, Category = "Hero Music|Bridge")
	int32 GetExpectedNodeIndex() const { return ExpectedNodeIndex; }

protected:
	virtual void HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event) override;

private:
	int32 ExpectedNodeIndex = 0;
};

/**
 * Interactive bell node used by the third hero instrument. It keeps the
 * shared overlap, spring, timing, audio, score, and reactivity contract, but
 * replaces the rectangular presentation mesh with a lathed bell body.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API APCGBellTreeGardenNode : public APCGHeroMusicNode
{
	GENERATED_BODY()

public:
	APCGBellTreeGardenNode();

protected:
	virtual void ApplyProfileGeometry() override;

private:
	void RebuildBellGeometry(float Width, float Depth, float Height, UMaterialInterface* Material);
};

/** Ordered, local-completion host for the BellTreeGarden proof level. */
UCLASS(Blueprintable)
class BS_GODFILE_API APCGBellTreeGardenHost : public APCGHeroMusicGraphHost
{
	GENERATED_BODY()

public:
	APCGBellTreeGardenHost();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Bell Garden")
	int32 BellCount = 18;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Hero Music|Bell Garden")
	int32 BranchCount = 3;

	UPROPERTY(BlueprintAssignable, Category = "Hero Music|Bell Garden")
	FPCGHeroMusicCompletionEvent OnGardenCompleted;

	UFUNCTION(BlueprintPure, Category = "Hero Music|Bell Garden")
	int32 GetExpectedBellIndex() const { return ExpectedBellIndex; }

protected:
	virtual void HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event) override;

private:
	int32 ExpectedBellIndex = 0;
};
