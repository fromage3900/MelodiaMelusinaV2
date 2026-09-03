#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include "PCGPoint.h"
#include "PCGMusicSequencer.generated.h"

class UPCGComponent;
class UPCGGraph;
class UPCGMetadata;
class UBoxComponent;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;
class USceneComponent;

USTRUCT(BlueprintType)
struct BS_GODFILE_API FPCGMusicStepGridDimensions
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	int32 Steps = 16;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	int32 Lanes = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	float StepSpacing = 86.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	float LaneSpacing = 96.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	float PadWidth = 68.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	float PadDepth = 68.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Layout")
	float PadHeight = 12.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Animation", meta = (ClampMin = "0.0"))
	float PressDepth = 5.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Animation", meta = (ClampMin = "0.0"))
	float SpringStiffness = 1100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Animation", meta = (ClampMin = "0.0"))
	float SpringDamping = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Music Grid|Animation", meta = (ClampMin = "0.0"))
	float PressTriggerHeight = 10.0f;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UPCGMusicStepGridProfile : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Layout")
	FPCGMusicStepGridDimensions Dimensions;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Music")
	int32 FirstMidiNote = 60;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Music")
	TArray<int32> LaneMidiNotes = {60, 62, 64, 67};

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Visuals")
	TSoftObjectPtr<UStaticMesh> PadMesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Visuals")
	TSoftObjectPtr<UMaterialInterface> PadMaterial;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FPCGMusicStepEvent, int32, StepIndex, int32, Lane, int32, MidiNote, AActor*, SteppingActor);

UCLASS(Blueprintable)
class BS_GODFILE_API APCGMusicStepPad : public AActor
{
	GENERATED_BODY()

public:
	APCGMusicStepPad();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Called by PCGSpawnActor after this pad is created from a deterministic point. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Music Grid|PCG")
	void InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata);

	UFUNCTION(BlueprintPure, Category = "Music Grid")
	int32 GetStepIndex() const { return StepIndex; }

	UFUNCTION(BlueprintPure, Category = "Music Grid")
	int32 GetLane() const { return Lane; }

	UFUNCTION(BlueprintPure, Category = "Music Grid")
	int32 GetMidiNote() const { return MidiNote; }

	UFUNCTION(BlueprintPure, Category = "Music Grid")
	bool IsPressed() const { return bIsPressed; }

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Music Grid|Components")
	TObjectPtr<UStaticMeshComponent> PadMeshComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Music Grid|Components")
	TObjectPtr<UBoxComponent> PadBlocker;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Music Grid|Components")
	TObjectPtr<UBoxComponent> StepTrigger;

	UPROPERTY(BlueprintAssignable, Category = "Music Grid|Events")
	FPCGMusicStepEvent OnStepActivated;

	UPROPERTY(BlueprintAssignable, Category = "Music Grid|Events")
	FPCGMusicStepEvent OnStepDeactivated;

	FBox GetWorldFootprint() const;
	void SetGrid(class APCGMusicStepGrid* InGrid);
	void SetPressedForActor(AActor* SteppingActor, bool bPressedForActor);

private:
	void ResolveGrid();
	void ApplyProfileGeometry();
	UFUNCTION()
	void HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
	UFUNCTION()
	void HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
	void BeginPadPress(AActor* SteppingActor);
	void EndPadPress(AActor* SteppingActor);
	bool IsPlayerControlledPawn(AActor* OtherActor) const;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Music Grid|PCG", meta = (AllowPrivateAccess = "true"))
	int32 StepIndex = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Music Grid|PCG", meta = (AllowPrivateAccess = "true"))
	int32 Lane = INDEX_NONE;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Music Grid|PCG", meta = (AllowPrivateAccess = "true"))
	int32 MidiNote = INDEX_NONE;

	TWeakObjectPtr<class APCGMusicStepGrid> GridOwner;
	TSet<TWeakObjectPtr<AActor>> PressingActors;
	float CurrentPressOffset = 0.0f;
	float PressVelocity = 0.0f;
	bool bIsPressed = false;
};

UCLASS(Blueprintable)
class BS_GODFILE_API APCGMusicStepGrid : public AActor
{
	GENERATED_BODY()

public:
	APCGMusicStepGrid();

	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Music Grid|Components")
	TObjectPtr<UPCGComponent> PCGComponent;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Configuration")
	TObjectPtr<UPCGMusicStepGridProfile> Profile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Music Grid|Configuration")
	TObjectPtr<UPCGGraph> MusicGraph;

	UPROPERTY(BlueprintAssignable, Category = "Music Grid|Events")
	FPCGMusicStepEvent OnStepActivated;

	UPROPERTY(BlueprintAssignable, Category = "Music Grid|Events")
	FPCGMusicStepEvent OnStepDeactivated;

	UPROPERTY(BlueprintReadOnly, Category = "Music Grid|State")
	int32 ActivePadCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Music Grid|State")
	int32 RegisteredPadCount = 0;

	UFUNCTION(BlueprintPure, Category = "Music Grid")
	UPCGMusicStepGridProfile* GetProfile() const { return Profile; }

	void RegisterPad(APCGMusicStepPad* Pad);
	void UnregisterPad(APCGMusicStepPad* Pad);
	void NotifyPadActivated(APCGMusicStepPad* Pad, AActor* SteppingActor);
	void NotifyPadDeactivated(APCGMusicStepPad* Pad, AActor* SteppingActor);

private:
	void UpdateActivePadCount();

	UPROPERTY()
	TSet<TObjectPtr<APCGMusicStepPad>> RegisteredPads;
};
