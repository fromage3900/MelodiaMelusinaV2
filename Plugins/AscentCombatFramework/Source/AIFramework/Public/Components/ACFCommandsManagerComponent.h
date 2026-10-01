// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "Containers/Queue.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include "Commands/ACFBaseCommand.h"

#include "ACFCommandsManagerComponent.generated.h"


class AACFAIController;

UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFCommandsManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFCommandsManagerComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;
	UPROPERTY(EditDefaultsOnly, Instanced, meta = (Categories = "AICommand"), BlueprintReadWrite, Category = ACF)
	TMap<FGameplayTag, class UACFBaseCommand*> commands;

	TQueue<class UACFBaseCommand*> commandToExecute;

public:
	/**
	 * Executes the pending command stored in the queue.
	 * This function is called on the server to process any queued commands that have not been executed yet.
	 * Ensures reliable execution with validation.
	 */
	UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = ACF)
	void ExecutePendingCommand();

	/**
	 * Triggers a specific command based on the given GameplayTag.
	 * This function sends a command request to the AI, which may include actions like attacking, dodging, or defending.
	 * Executes on the server to ensure network synchronization and command validation.
	 *
	 * @param command - The GameplayTag representing the command to be executed.
	 */
	UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = ACF)
	void TriggerCommand(const FGameplayTag& command);

	/**
	 * Terminates the currently active command.
	 * This is useful for interrupting an ongoing AI action, such as stopping an attack mid-animation.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TerminateCurrentCommand();

	/**
	 * Checks whether there are any pending commands waiting to be executed.
	 *
	 * @return True if there are commands in the queue, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool HasPendingCommands() const { return !commandToExecute.IsEmpty(); }


	// Checks if a command is currently being executed
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsExecutingCommand() const;

	// Returns the currently executing command
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE UACFBaseCommand* GetCurrentCommand() const { return currentCommand; }

	// Checks if a command with the specified tag exists in the command map
	UFUNCTION(BlueprintPure, Category = ACF)
	bool HasCommandWithTag(const FGameplayTag& CommandTag) const;

	// Adds a new command and optionally triggers it immediately
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool AddCommand(const FGameplayTag& CommandTag, TSubclassOf<UACFBaseCommand> CommandClass, bool bTriggerImmediately = false);

	// Removes a command from the available commands map
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool RemoveCommand(const FGameplayTag& CommandTag);

	/**
	 * Event triggered when a command execution is finished.
	 * Used to notify other systems (such as UI or behavior trees) that the AI has completed an action.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FonCommandFinished OnCommandFinished;

private:
	TObjectPtr<AACFAIController> controllerOwner;

	TObjectPtr<UACFBaseCommand> currentCommand;

	UFUNCTION()
	void HandleCommandFinished(bool bSuccess);
};
