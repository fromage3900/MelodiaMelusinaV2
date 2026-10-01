// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAITypes.h"
#include "ACFBaseAIController.h"
#include "ACFCCTypes.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include "Groups/ACFGroupAgentInterface.h"
#include <BehaviorTree/Blackboard/BlackboardKey.h>
#include <DetourCrowdAIController.h>
#include <GameplayTagContainer.h>
#include <Perception/AIPerceptionTypes.h>

#include "ACFAIController.generated.h"

/**
 *
 */

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAIStateChanged, const FGameplayTag, AIState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAICombatStateChanged, const EAICombatState, AICombatState);

UCLASS()
class AIFRAMEWORK_API AACFAIController : public AACFBaseAIController, public IACFGroupAgentInterface {
    GENERATED_BODY()

protected:
    virtual void BeginPlay() override;

    virtual void OnPossess(APawn* _possPawn) override;

    virtual void OnUnPossess() override;

    virtual void EndPlay(const EEndPlayReason::Type reason) override;

    // The Behavior Tree component that controls the AI decision-making process
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UBehaviorTreeComponent> BehaviorTreeComponent;

    // The Blackboard component used to store and manage AI variables during execution
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UBlackboardComponent> BlackboardComponent;

    // The combat behavior component that defines how the AI fights and reacts in combat
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UACFCombatBehaviourComponent> CombatBehaviorComponent;

    // The commands manager component, responsible for handling AI commands and execution logic
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UACFCommandsManagerComponent> CommandsManagerComp;

    // The targeting component that manages how the AI selects and tracks its targets
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UATSAITargetComponent> TargetingComponent;

    // The threat manager component, responsible for tracking and prioritizing threats
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UACFThreatManagerComponent> ThreatComponent;

    // The default behavior tree assigned to the AI, defining its overall logic
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<class UBehaviorTree> BehaviorTree;

    // The character that owns this AI Controller, providing access to character-specific properties
    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<class AACFCharacter> CharacterOwned;

    /*Default AI state for this agent*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|AI State")
    FGameplayTag DefaultState;

    /*Indicates the default locomotion state of this AI for each AI state*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI State")
    TMap<FGameplayTag, ELocomotionState> LocomotionStateByAIState;

    /*If set to true this AI will try to come back to the Home Position once it is over MaxDistanceFromHome*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Home")
    bool bBoundToHome = true;

    /*If bBoundToHome  is true, once the AI is over this distance from his lead/home position, he will try to come back home*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bBoundToHome), BlueprintReadOnly, Category = "ACF|Home")
    float MaxDistanceFromHome = 8500.f;

    /*If set to true this AI will be teleported back near the Lead Position once it is over TeleportHomeTriggerDistance*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Teleport")
    bool bTeleportToLead = false;

    /*Distance to trigger the teleport*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bTeleportToLead), BlueprintReadOnly, Category = "ACF|Teleport")
    float TeleportToLeadTriggerDistance = 8500.f;

    /*Radius in which the controlled pawn is spawned near the lead*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = bTeleportToLead), BlueprintReadOnly, Category = "ACF|Teleport")
    float TeleportNearLeadRadius = 2500.f;

    /*Distance for which the controlled pawn stop fighting against his target*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Combat")
    float LoseTargetDistance = 3500.f;

    /*Indicates if this agent attacks an enemy on perception*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Combat")
    bool bIsAggressive = true;

    /*Indicates if this agent  should react once he gets hit*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Combat")
    bool bShouldReactOnHit = true;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    int32 GroupIndex;

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void HandleMaxThreatUpdated(AActor* newMax);

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void HandlePerceptionUpdated(AActor* Actor, FAIStimulus Stimulus);

public:
    AACFAIController(const FObjectInitializer& ObjectInitializer);

    /// <summary>
    /// /Groupable Entity Interface
    /// </summary>
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Group")
    class UACFGroupAIComponent* GetOwningGroup();
    virtual class UACFGroupAIComponent* GetOwningGroup_Implementation() override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Group")
    bool IsPartOfGroup();
    virtual bool IsPartOfGroup_Implementation() override;
    /// <summary>
    /// /End Groupable Entity
    /// </summary>
    ///

private:
    void EnableCharacterComponents(bool bEnabled);

    UPROPERTY()
    TObjectPtr<class UACFGroupAIComponent> GroupOwner;

    UPROPERTY()
    TObjectPtr<class UACFAIPatrolComponent> patrolComp;

    TObjectPtr<class UACFAIPatrolComponent> TryGetPatrolComp() const;

    FVector homeLocation;

    struct FBlackboard::FKey commandDurationTimeKey,
        targetActorKey,
        targetActorDistanceKey,
        targetPointLocationKey,
        groupLeaderKey, targetDistanceKey,
        combatStateKey, isPausedKey, groupLeadDistanceKey, homeDistanceKey;

    UFUNCTION()
    void HandleCharacterHit(const FACFDamageEvent& damageReceived);

    UFUNCTION()
    void HandleCharacterDeath();

    UFUNCTION()
    virtual void OnTargetDeathHandle();

    void TryGetPatrolPath();

    UPROPERTY()
    FGameplayTag CurrentAIState;

public:
    friend class AACFGroupAIController;

    // Returns the AI-controlled character
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class AACFCharacter* GetBaseAICharacter() const { return CharacterOwned; }

    // Returns the combat behavior component, which dictates AI fighting behavior
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UACFCombatBehaviourComponent* GetCombatBehavior() const { return CombatBehaviorComponent; }

    // Returns the command manager component, responsible for executing AI commands
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UACFCommandsManagerComponent* GetCommandManager() const { return CommandsManagerComp; }

    /** True while an ACF command is executing (e.g. FollowMe, GoThere). Use as a guard to skip movement updates that would conflict with the command's own MoveTo. */
    UFUNCTION(BlueprintPure, Category = "ACF|Command")
    bool IsExecutingCommand() const;

    // Returns the threat manager component, which tracks and prioritizes threats
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UACFThreatManagerComponent* GetThreatManager() const { return ThreatComponent; }

    // Returns the maximum allowed distance from the AI's home location before it returns
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE float GetMaxDistanceFromHome() const { return MaxDistanceFromHome; }

    // Returns the distance threshold at which the AI teleports near its leader
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE float GetTeleportLeadDistanceTrigger() const { return TeleportToLeadTriggerDistance; }

    // Returns the distance threshold at which the AI loses its current target
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE float GetLoseTargetDistance() const { return LoseTargetDistance; }

    // Returns the blackboard key used for tracking the command duration time
    struct FBlackboard::FKey GetCommandDurationTimeKey() const { return commandDurationTimeKey; }

    // Returns the AI's index in the group (useful for AI formations)
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE int32 GetIndexInGroup() const { return GroupIndex; }

    // Returns the behavior tree component managing the AI logic
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UBehaviorTreeComponent* GetBehaviorThreeComponent() const { return BehaviorTreeComponent; }

    // Returns the behavior tree asset assigned to the AI
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UBehaviorTree* GetBehaviorTree() const { return BehaviorTree; }

    // Returns the AI's group component, if it belongs to a group
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE class UACFGroupAIComponent* GetGroup() const { return GroupOwner; }

    // Checks if the AI should return to its home location when idle
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE bool ShouldReturnHome() const { return bBoundToHome; }

    // Checks if the AI should teleport near its leader when too far away
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE bool ShouldTeleportNearLead() const { return bTeleportToLead; }

    // Returns the AI's default state (e.g., Idle, Patrol, Combat)
    UFUNCTION(BlueprintPure, Category = "ACF|Getter")
    FORCEINLINE FGameplayTag GetDefaultAIState() const { return DefaultState; }

    // Sets the default state of the AI
    UFUNCTION(BlueprintCallable, Category = "ACF|State")
    void SetDefaultState(FGameplayTag inDefaultState)
    {
        DefaultState = inDefaultState;
    }

    // Overrides the locomotion state map used to resolve movement mode per AI state
    UFUNCTION(BlueprintCallable, Category = "ACF|State")
    void SetLocomotionStateByAIState(const TMap<FGameplayTag, ELocomotionState>& InMap)
    {
        LocomotionStateByAIState = InMap;
    }

    // Returns the full locomotion state map (AI state tag → locomotion state)
    UFUNCTION(BlueprintPure, Category = "ACF|State")
    TMap<FGameplayTag, ELocomotionState> GetLocomotionStateByAIState() const
    {
        return LocomotionStateByAIState;
    }

    // Adds or updates a single entry in the locomotion state map without replacing the whole map
    UFUNCTION(BlueprintCallable, Category = "ACF|State")
    void SetLocomotionStateForAIState(UPARAM(meta = (Categories = "AIState")) FGameplayTag AIStateTag, ELocomotionState InLocomotionState)
    {
        LocomotionStateByAIState.Add(AIStateTag, InLocomotionState);
    }

    // Resets the AI to its default state
    UFUNCTION(BlueprintCallable, Category = "ACF|State")
    void ResetToDefaultState();

    // Replaces the behavior tree asset and restarts the tree if the AI is already active
    UFUNCTION(BlueprintCallable, Category = "ACF|BehaviorTree")
    void SetBehaviorTree(class UBehaviorTree* NewBehaviorTree);

    // Sets the maximum distance from home before the AI returns
    UFUNCTION(BlueprintCallable, Category = "ACF|Home")
    void SetMaxDistanceFromHome(float NewDistance) { MaxDistanceFromHome = NewDistance; }

    // Enables or disables teleport-to-lead behaviour
    UFUNCTION(BlueprintCallable, Category = "ACF|Teleport")
    void SetTeleportToLead(bool bEnable) { bTeleportToLead = bEnable; }

    // Sets the distance that triggers a teleport near the lead
    UFUNCTION(BlueprintCallable, Category = "ACF|Teleport")
    void SetTeleportTriggerDistance(float NewDistance) { TeleportToLeadTriggerDistance = NewDistance; }

    // Sets the spawn radius used when teleporting near the lead
    UFUNCTION(BlueprintCallable, Category = "ACF|Teleport")
    void SetTeleportNearLeadRadius(float NewRadius) { TeleportNearLeadRadius = NewRadius; }

    // Sets the distance at which the AI drops its current target
    UFUNCTION(BlueprintCallable, Category = "ACF|Combat")
    void SetLoseTargetDistance(float NewDistance) { LoseTargetDistance = NewDistance; }

    // Sets whether this AI attacks enemies on perception
    UFUNCTION(BlueprintCallable, Category = "ACF|Combat")
    void SetIsAggressive(bool bAggressive) { bIsAggressive = bAggressive; }

    // Sets whether this AI reacts when hit
    UFUNCTION(BlueprintCallable, Category = "ACF|Combat")
    void SetShouldReactOnHit(bool bReact) { bShouldReactOnHit = bReact; }

    // BLACKBOARD (BK) FUNCTIONS - These interact with the Behavior Tree's blackboard keys

    // Sets the waiting duration in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetWaitDurationTimeBK(float time);

    // Retrieves the command duration time stored in the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    float GetCommandDurationTimeBK() const;

    // Retrieves the AI's combat state from the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    EAICombatState GetCombatStateBK() const;

    // Returns current AI state
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    FGameplayTag GetAIState() const
    {
        return CurrentAIState;
    }

    // Retrieves the AI's target actor from the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    AActor* GetTargetActorBK() const;

    // Retrieves the target point location stored in the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    FVector GetTargetPointLocationBK() const;

    // Checks if the AI is paused (blackboard variable)
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    bool GetIsPausedBK() const;

    // Retrieves the AI's lead actor from the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    class AActor* GetLeadActorBK() const;

    // Retrieves the distance to the target actor stored in the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    float GetTargetActorDistanceBK() const;

    // Retrieves the distance to the target point stored in the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    float GetTargetPointDistanceBK() const;

    // Retrieves the distance to the AI's leader stored in the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    float GetLeadActorDistanceBK() const;

    // Retrieves the distance to the AI's home location from the blackboard
    UFUNCTION(BlueprintPure, Category = "ACF|Blackboard")
    float GetHomeDistanceBK() const;

    // Sets the AI's target location in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetTargetLocationBK(const FVector& targetLocation);

    // Sets the AI's lead actor in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetLeadActorBK(AActor* leadActor);

    // Sets the AI's target actor in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetTargetActorBK(AActor* target);

    // Sets the AI's current state in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetCurrentAIState(UPARAM(meta = (Categories = "AIState")) FGameplayTag aiState);

    // Sets the AI's combat state in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetCombatStateBK(EAICombatState combatState);

    // Sets the target point distance in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetTargetPointDistanceBK(float distance);

    // Sets the target actor distance in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetTargetActorDistanceBK(float distance);

    // Sets the AI's paused state in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetIsPausedBK(bool isPaused);

    // Sets the AI's distance to the lead actor in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetLeadActorDistanceBK(float distance);

    // Sets the AI's distance to its home location in the blackboard
    UFUNCTION(BlueprintCallable, Category = "ACF|Blackboard")
    void SetHomeDistanceBK(float distance);

    // AI LEAD MANAGEMENT FUNCTIONS

    // Teleports the AI near its leader if it's too far away
    UFUNCTION(BlueprintCallable, Category = "ACF|Lead")
    bool TeleportNearLead();

    // Attempts to update the AI's leader reference
    UFUNCTION(BlueprintCallable, Category = "ACF|Lead")
    bool TryUpdateLeadRef();

    // AI HOME MANAGEMENT FUNCTIONS

    // Sets the AI's home location
    UFUNCTION(BlueprintCallable, Category = "ACF|Home")
    void SetHomeLocation(const FVector& newHomeLocation);

    // Enables or disables the return-to-home distance check at runtime.
    UFUNCTION(BlueprintCallable, Category = "ACF|Home")
    void SetReturnHomeCheckEnabled(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "ACF|Home")
    void EnableReturnHomeCheck();

    UFUNCTION(BlueprintCallable, Category = "ACF|Home")
    void DisableReturnHomeCheck();

    // Retrieves the AI's home location
    UFUNCTION(BlueprintPure, Category = "ACF|Home")
    FVector GetHomeLocation() const { return homeLocation; }

    // AI PATROL MANAGEMENT FUNCTIONS

    // Moves the AI to the next waypoint in its patrol path
    UFUNCTION(BlueprintCallable, Category = "ACF|Patrol")
    bool TryGoToNextWaypoint();

    // Retrieves the path distance between the AI and its target
    UFUNCTION(BlueprintCallable, Category = "ACF|Patrol")
    float GetPathDistanceFromTarget();

    // Sets the AI's patrol path, optionally forcing path following
    UFUNCTION(BlueprintCallable, Category = "ACF|Patrol")
    void SetPatrolPath(class AACFSplinePath* inPatrol, bool forcePathFollowing = false);

    /*Forces the AI to target the provided actor*/
    UFUNCTION(BlueprintCallable, Category = "ACF|Target")
    void SetTarget(AActor* target);

    /*Returns the actor targeted by this AI as set in the ATSTargetComponent*/
    UFUNCTION(BlueprintPure, Category = "ACF|Target")
    AActor* GetTarget() const;

    /*Trues if this AI has a valid target*/
    UFUNCTION(BlueprintPure, Category = "ACF|Target")
    bool HasTarget() const;

    /*Tries to request another target, returns true if a new target is found*/
    UFUNCTION(BlueprintCallable, Category = "ACF|Target")
    bool RequestAnotherTarget();

    /*Executes the provided command from the ACFCommandMenagerComponent*/
    UFUNCTION(BlueprintCallable, Category = "ACF|Command")
    void TriggerCommand(const FGameplayTag& command);

    /*Trues if this AI in battle state*/
    UFUNCTION(BlueprintPure, Category = "ACF|Target")
    bool IsInBattle() const;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnAIStateChanged OnAIStateChanged;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnAICombatStateChanged OnAICombatStateChanged;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnDamageReceived OnDamageReceived;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnDeathEvent OnPawnDeath;

    void SetGroupOwner(class UACFGroupAIComponent* group, int32 groupIndex, bool disablePerception, bool bOverrideTeam);

    void UpdateLocomotionState();
    void UpdateCombatLocomotion();
};
