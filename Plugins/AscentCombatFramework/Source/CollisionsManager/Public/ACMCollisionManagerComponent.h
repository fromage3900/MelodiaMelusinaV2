// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMTypes.h"
#include "Components/ActorComponent.h"
#include "Components/SphereComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Kismet/KismetSystemLibrary.h"
#include <Engine/EngineTypes.h>
#include <GameFramework/DamageType.h>

#include "ACMCollisionManagerComponent.generated.h"

class AActor;
class UDamageType;


/**
 * Delegate triggered when a trail is activated.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTrailActivated,FName,TrailName);

/**
 * Delegate triggered when a trail is deactivated.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTrailDeactivated,FName,TrailName);

/**
 * Delegate triggered when a collision is detected.
 * @param HitResult The hit result containing collision details.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCollisionDetected, const FHitResult&, HitResult);

/**
 * Delegate triggered when an actor receives damage.
 * @param damageReceiver The actor that received the damage.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActorDamaged, AActor*, damageReceiver);

/**
 * @class UACMCollisionManagerComponent
 * Manages collision detection and damage handling in the ACF framework.
 *
 * This component handles collision traces, detecting hits, and managing actors that should be ignored.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class COLLISIONSMANAGER_API UACMCollisionManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	/**
	 * Default constructor that initializes component properties.
	 */
	UACMCollisionManagerComponent();

	UPROPERTY(BlueprintAssignable, Category = "ACF|Collision|Trail")
	FOnTrailActivated OnTrailActivated;

	UPROPERTY(BlueprintAssignable, Category = "ACF|Collision|Trail")
	FOnTrailDeactivated OnTrailDeactivated;
	
protected:
	/**
	 * Called when the game starts or when the component is spawned.
	 */
	virtual void BeginPlay() override;

	/**
	 * Called when the component is removed or the game ends.
	 * @param EndPlayReason The reason the component is being removed.
	 */
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/**
	 * Defines the level of debug information displayed.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Debug")
	EDebugType ShowDebugInfo;

	/**
	 * Color used for inactive debug visuals.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Debug")
	FLinearColor DebugInactiveColor;

	/**
	 * Color used for active debug visuals.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Debug")
	FLinearColor DebugActiveColor;

	/**
	 * Allows multiple hits per swing if enabled.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM")
	bool bAllowMultipleHitsPerSwing;

	/**
	 * Collision channels to be considered for tracing.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM")
	TArray<TEnumAsByte<ECollisionChannel>> CollisionChannels;

	/**
	 * List of actors that should be ignored during collision detection.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM")
	TArray<class AActor*> IgnoredActors;

	/**
	 * Determines whether to ignore the owner of this component during collisions.
	 * If true, the component's owner will not be considered in hit detection.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM")
	bool bIgnoreOwner = true;

	
	/**
	 * Determines if the hit should call ApplyDamage
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM")
	bool bAutoApplyDamage = true;

	/**
	 * Stores trace configurations for different damage types.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Traces")
	TMap<FName, FTraceInfo> DamageTraces;

	/**
	 * Configuration for swipe-based traces.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Traces")
	FBaseTraceInfo SwipeTraceInfo;

	/**
	 * Configuration for area-based damage traces.
	 */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACM|Traces")
	FBaseTraceInfo AreaDamageTraceInfo;

public:
	/**
	 * Sets up the collision manager with a given damage mesh.
	 * @param inDamageMesh The mesh component to use for collision detection.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACM", meta = (AutoCreateRefTerm = "defaultChannels"))
	void SetupCollisionManager(class UMeshComponent* inDamageMesh,
		const TArray<TEnumAsByte<ECollisionChannel>>& defaultChannels);

	/**
	 * Starts applying area damage over time in a specific region.
	 * @param damageCenter The center of the area where damage is applied.
	 * @param damageRadius The radius of the area.
	 * @param damageInterval The time interval between damage applications.
	 * @param damageTypeOverride Optional override for the damage type.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACM)
	void StartAreaDamage(const FVector& damageCenter, float damageRadius, float damageInterval = 1.f, TSubclassOf<UDamageType> damageTypeOverride = nullptr);

	/**
	 * Stops any currently applied area damage effects.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACM)
	void StopCurrentAreaDamage();

	/**
	 * Performs a single instance of area damage at a given location.
	 * @param damageCenter The center of the damage effect.
	 * @param damageRadius The radius of the effect.
	 * @param damageTypeOverride Optional override for the damage type.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACM)
	void PerformAreaDamage_Single(const FVector& damageCenter, float damageRadius, TSubclassOf<UDamageType> damageTypeOverride = nullptr);

	/**
	 * Locally performs area damage and returns the hit results.
	 * @param damageCenter The center of the effect.
	 * @param damageRadius The radius of the effect.
	 * @param outHits Array to store the resulting hit data.
	 * @param damageTypeOverride Optional override for the damage type.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void PerformAreaDamage_Single_Local(const FVector& damageCenter, float damageRadius, TArray<FHitResult>& outHits, TSubclassOf<UDamageType> damageTypeOverride = nullptr);

	/**
	 * Starts a timed area damage effect for a set duration.
	 * @param damageCenter The center of the damage area.
	 * @param damageRadius The radius of the effect.
	 * @param duration The total duration of the effect.
	 * @param damageInterval Time between each damage application.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACM)
	void PerformAreaDamageForDuration(const FVector& damageCenter, float damageRadius, float duration, float damageInterval = 1.f);

	/**
	 * Adds an actor to the ignore list for collision detection.
	 * @param ignoredActor The actor to ignore.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void AddActorToIgnore(class AActor* ignoredActor);

	/**
	 * Adds a collision channel to the detection list.
	 * @param inTraceChannel The collision channel to add.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void AddCollisionChannel(TEnumAsByte<ECollisionChannel> inTraceChannel);

	/**
	 * Adds multiple collision channels at once.
	 * @param inTraceChannels The array of collision channels to add.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void AddCollisionChannels(TArray<TEnumAsByte<ECollisionChannel>> inTraceChannels);

	/**
	 * Clears all active collision channels.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void ClearCollisionChannels();

	/**
	 * Performs a swipe trace shot between two points.
	 * @param start The starting point of the trace.
	 * @param end The ending point of the trace.
	 * @param radius The radius of the trace (default is 0.f).
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACM)
	void PerformSwipeTraceShot(const FVector& start, const FVector& end, float radius = 0.f);

	/**
	 * Performs a local swipe trace shot and returns the hit result.
	 * @param start The starting point of the trace.
	 * @param end The ending point of the trace.
	 * @param radius The radius of the trace.
	 * @param outHit The resulting hit data.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	bool PerformSwipeTraceShot_Local(const FVector& start, const FVector& end, float radius, FHitResult& outHit);

	/**
	 * Starts all trace systems.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StartAllTraces();

	/**
	 * Stops all currently active traces.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StopAllTraces();

	/**
	 * Starts a single trace by name.
	 * @param Name The name of the trace to start.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StartSingleTrace(const FName& Name);

	/**
	 * Stops a single trace by name.
	 * @param Name The name of the trace to stop.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StopSingleTrace(const FName& Name);

	/**
	 * Starts a single trace for a specified duration.
	 * @param TraceName The name of the trace to start.
	 * @param Duration The duration for which the trace should remain active.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StartTimedSingleTrace(const FName& TraceName, float Duration);

	/**
	 * Starts all traces for a specified duration.
	 * @param Duration The duration for which all traces should remain active.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void StartAllTimedTraces(float Duration);

	/**
	 * Plays a specified trail effect.
	 * @param trail The name of the trail to play.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void PlayTrails(const FName& trail);

	/**
	 * Stops a specified trail effect.
	 * @param trail The name of the trail to stop.
	 */
	UFUNCTION(BlueprintCallable,Category = ACM)
	void StopTrails(const FName& trail);

	/**
	 * Retrieves the map of damage traces.
	 * @return A map containing trace names and their corresponding configurations.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	TMap<FName, FTraceInfo> GetDamageTraces() const
	{
		return DamageTraces;
	};

	/**
	 * Checks if a specific trace is active.
	 * @param traceName The name of the trace to check.
	 * @return True if the trace is active, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = ACM)
	bool IsTraceActive(const FName& traceName);

	/**
	 * Sets the owner of this component, useful when the component is on a weapon but the damage dealer should be the character.
	 * @param newOwner The actor that should be considered as the damage dealer.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void SetActorOwner(AActor* newOwner);

	/**
	 * Gets the current owner of this component.
	 * @return The actor that is set as the owner.
	 */
	UFUNCTION(BlueprintPure, Category = ACM)
	AActor* GetActorOwner() const;

	/**
	 * Configures a specific trace.
	 * @param traceName The name of the trace to configure.
	 * @param traceInfo The configuration settings for the trace.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	void SetTraceConfig(const FName& traceName, const FTraceInfo& traceInfo);

	/**
	 * Attempts to retrieve the configuration for a specified trace.
	 * @param traceName The name of the trace.
	 * @param outTraceInfo The output variable where the trace configuration will be stored.
	 * @return True if the trace configuration was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACM)
	bool TryGetTraceConfig(const FName& traceName, FTraceInfo& outTraceInfo) const
	{
		if (DamageTraces.Contains(traceName)) {
			outTraceInfo = *DamageTraces.Find(traceName);
			return true;
		}
		return false;
	};

	/**
	 * Event triggered when a collision is detected.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACM)
	FOnCollisionDetected OnCollisionDetected;

	/**
	 * Event triggered when an actor takes damage.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACM)
	FOnActorDamaged OnActorDamaged;

	/**
	 * Calculates the rotation of a line from start to end point.
	 * @param start The starting point.
	 * @param end The ending point.
	 * @return The calculated rotation.
	 */
	FRotator GetLineRotation(FVector start, FVector end);

	/**
	 * Updates collision detections and relevant logic.
	 */
	void UpdateCollisions();

	/**
	 * Retrieves the first trace configuration available.
	 * @return The first trace configuration.
	 */
	FTraceInfo GetFirstTrace() const;

private:
	TObjectPtr<AActor> actorOwner;

	TObjectPtr<UMeshComponent> damageMesh;

	UPROPERTY()
	TMap<FName, FTraceInfo> activatedTraces;

	UPROPERTY()
	TArray<FName> pendingDelete;

	UPROPERTY()
	TMap<FName, FHitActors> alreadyHitActors;

	TArray<TObjectPtr<AActor>> alreadyHitActorsBySphere;
	TArray<TObjectPtr<AActor>> alreadyHitActorsBySweep;
	bool bIsStarted = false;

	void DisplayDebugTraces();

	void ShowDebugTrace(const FVector& StartPos, const FVector& EndPos, const float radius, EDrawDebugTrace::Type DrawDebugType, float duration, FLinearColor DebugColor = FLinearColor::Red);

	UFUNCTION()
	void HandleTimedSingleTraceFinished(const FName& traceEnded);

	UFUNCTION()
	void HandleAllTimedTraceFinished();

	UPROPERTY()
	TMap<FName, class UParticleSystemComponent*> ParticleSystemComponents;

	UPROPERTY()
	TMap<FName, class UNiagaraComponent*> NiagaraSystemComponents;

	void ApplyDamage(const FHitResult& HitResult, const FBaseTraceInfo& currentTrace);

	bool CanActorDamageActor(const AActor* Attacker, const AActor* Victim) const;
	void ApplyPointDamage(const FHitResult& HitResult, const FBaseTraceInfo& currentTrace);

	void ApplyAreaDamage(const FHitResult& HitResult, const FBaseTraceInfo& currentTrace);

	UPROPERTY()
	FTimerHandle AllTraceTimer;

	UPROPERTY()
	FTimerHandle AreaDamageTimer;

	UPROPERTY()
	FTimerHandle AreaDamageLoopTimer;

	UFUNCTION()
	void HandleAreaDamageFinished();

	UFUNCTION()
	void HandleAreaDamageLooping();

	UPROPERTY()
	FAreaDamageInfo currentAreaDamage;

	UPROPERTY()
	TMap<FName, FTimerHandle> TraceTimers;

	UPROPERTY()
	bool bSingleTimedTraceStarted = false;

	UPROPERTY()
	bool bAllTimedTraceStarted = false;

	void SetStarted(bool inStarted);
};
