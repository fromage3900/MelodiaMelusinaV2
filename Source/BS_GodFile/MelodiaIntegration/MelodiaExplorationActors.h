#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaExplorationActors.generated.h"

class UBoxComponent;
class UPrimitiveComponent;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaExplorationActorEvent, AActor*, MelusinaActor);

/**
 * A presentation-only overlap and interaction anchor for exploration scenes.
 * It contains no input, quest, save, or battle authority: level Blueprints can
 * bind its events now, and a future interaction system can call TryInteract.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaExplorationInteractionVolume : public AActor
{
    GENERATED_BODY()

public:
    AMelodiaExplorationInteractionVolume();

    UFUNCTION(BlueprintCallable, Category="Melodia|Exploration")
    bool TryInteract(AActor* InteractingActor);

    UFUNCTION(BlueprintCallable, Category="Melodia|Exploration")
    void SetInteractionActive(bool bNewActive) { bInteractionActive = bNewActive; }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Exploration")
    TObjectPtr<UBoxComponent> InteractionVolume;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Exploration")
    FName InteractionId = TEXT("ExplorationInteraction");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Exploration", meta=(MultiLine=true))
    FText PromptText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Exploration")
    bool bRequireMelusina = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Exploration")
    bool bOneShot = false;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Exploration")
    FMelodiaExplorationActorEvent OnMelusinaEntered;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Exploration")
    FMelodiaExplorationActorEvent OnMelusinaExited;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Exploration")
    FMelodiaExplorationActorEvent OnInteractionRequested;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex);

    bool IsEligibleExplorer(const AActor* Actor) const;

    bool bInteractionActive = true;
    bool bConsumed = false;
};

/** A one-shot or repeatable spatial-puzzle trigger with no quest authority. */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaPuzzleRelayVolume : public AActor
{
    GENERATED_BODY()

public:
    AMelodiaPuzzleRelayVolume();

    UFUNCTION(BlueprintCallable, Category="Melodia|Puzzle")
    bool ActivateRelay(AActor* ActivatingActor);

    UFUNCTION(BlueprintCallable, Category="Melodia|Puzzle")
    void ResetRelay();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Puzzle")
    TObjectPtr<UBoxComponent> TriggerVolume;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Puzzle")
    FName PuzzleId = TEXT("SpatialPuzzle");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Puzzle")
    bool bRequireMelusina = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Puzzle")
    bool bOneShot = true;

    UPROPERTY(BlueprintAssignable, Category="Melodia|Puzzle")
    FMelodiaExplorationActorEvent OnPuzzleActivated;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    bool IsEligibleExplorer(const AActor* Actor) const;
    bool bActivated = false;
};

/**
 * Basic moving collision geometry.  It is self-contained and starts only when
 * a level designer enables Auto Start or calls StartMotion from a Blueprint.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaMovingPlatform : public AActor
{
    GENERATED_BODY()

public:
    AMelodiaMovingPlatform();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Melodia|Platform")
    void StartMotion();

    UFUNCTION(BlueprintCallable, Category="Melodia|Platform")
    void StopMotion();

    UFUNCTION(BlueprintCallable, Category="Melodia|Platform")
    void ResetPlatform();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Platform")
    TObjectPtr<UStaticMeshComponent> PlatformMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Platform")
    FVector LocalEndOffset = FVector(0.0, 0.0, 300.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Platform", meta=(ClampMin="0.1"))
    float TravelDuration = 2.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Platform")
    bool bAutoStart = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Platform")
    bool bPingPong = true;

private:
    virtual void BeginPlay() override;

    FVector StartLocation = FVector::ZeroVector;
    float ElapsedTime = 0.0f;
    float ResolvedTravelDuration = 2.0f;
    bool bMoving = false;
};
