// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "ACFBaseCommand.generated.h"

class AACFAIController;

/**
 * * Delegate used to notify when the command execution is completed.
 *
 * This delegate is fired with a boolean parameter indicating whether the command execution
 * was successful (`true`) or failed (`false`).
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FonCommandFinished, bool, success);

/**
 * @class UACFBaseCommand
 * * Base class for AI commands in the Ascent Combat Framework (ACF).
 *
 * This class represents a base AI command that can be executed by AI-controlled characters.
 * Commands derived from this class define specific behaviors such reaching places, using abilites, moving to a target etc.
 *
 * Commands are managed by the UACFCommandsManagerComponent and executed by the AI controller.
 * Each command notifies when it has finished execution using the OnCommandFinished delegate.
 */
UCLASS(Blueprintable, BlueprintType, abstract, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("Default"))
class AIFRAMEWORK_API UACFBaseCommand : public UObject {
    GENERATED_BODY()

public:
    friend class UACFCommandsManagerComponent;

    /**
     * * Marks the command execution as finished.
     *
     * This function is called when the command has completed its execution.
     * It triggers the `OnCommandFinished` event to notify the system.
     *
     * @param bSuccess Indicates whether the command was successfully executed.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void FinishExecution(bool bSuccess);

    /**
     * * Event triggered when the command finishes execution.
     *
     * This can be used to notify other systems or components that the command has completed.
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FonCommandFinished OnCommandFinished;

protected:
    /**
     * * Internally executes the command on the specified AI controller.
     *
     * This function is used by the command manager to start the command execution.
     *
     * @param controller The AI controller that will execute this command.
     */
    void InternalExecute(class AACFAIController* controller);

    /**
     * * Executes the command on the AI controller.
     *
     * This function is meant to be overridden in child classes to define custom command behavior.
     * It is marked as `BlueprintNativeEvent`, allowing it to be implemented in Blueprints if needed.
     *
     * @param controller The AI controller executing the command.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void ExecuteCommand(class AACFAIController* controller);
    virtual void ExecuteCommand_Implementation(class AACFAIController* controller);

    /**
     * * Ends the command execution.
     *
     * This function provides cleanup or final actions that need to happen when the command ends.
     * It is a `BlueprintNativeEvent`, allowing for Blueprint implementation.
     *
     * @param controller The AI controller that executed the command.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void EndCommand(class AACFAIController* controller);
    virtual void EndCommand_Implementation(class AACFAIController* controller);

    /**
     * * Retrieves the world context for this command.
     *
     * Allows the command to interact with the game world (e.g., spawning effects or interacting with objects).
     *
     * @return A pointer to the current game world.
     */
    UWorld* GetWorld() const override;

    /**
     * * Gets the AI controller associated with this command.
     *
     * @return A pointer to the AI controller executing this command.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    AACFAIController* GetAIController() const
    {
        return aiController;
    }

private:
    /**
     * * The AI controller that is executing this command.
     */
    TObjectPtr<AACFAIController> aiController;
};
