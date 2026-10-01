// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFCommandsManagerComponent.h"
#include "ACFAIController.h"
#include "Commands/ACFBaseCommand.h"

// Sets default values for this component's properties
UACFCommandsManagerComponent::UACFCommandsManagerComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

// Called when the game starts
void UACFCommandsManagerComponent::BeginPlay()
{
    Super::BeginPlay();
    controllerOwner = Cast<AACFAIController>(GetOwner());
}

void UACFCommandsManagerComponent::TerminateCurrentCommand()
{
    if (currentCommand) {
        currentCommand->EndCommand(controllerOwner);
    } else {
        UE_LOG(LogTemp, Warning, TEXT("Invalid Command - UACFCommandsManagerComponent::TerminateCurrentCommand"));
    }
}

void UACFCommandsManagerComponent::HandleCommandFinished(bool bSuccess)
{
    if (currentCommand) {
        currentCommand->OnCommandFinished.RemoveDynamic(this, &UACFCommandsManagerComponent::HandleCommandFinished);
        currentCommand = nullptr;
        OnCommandFinished.Broadcast(bSuccess);
    }

}

void UACFCommandsManagerComponent::TriggerCommand_Implementation(const FGameplayTag& command)
{
    if (commands.Contains(command)) {
        UACFBaseCommand** comm = commands.Find(command);

        if (*comm) {
            UACFBaseCommand* commptr = *comm;

            if (commptr && controllerOwner) {
                commandToExecute.Enqueue(commptr);
            }
        }
    }
}

bool UACFCommandsManagerComponent::TriggerCommand_Validate(const FGameplayTag& command)
{
    return true;
}

void UACFCommandsManagerComponent::ExecutePendingCommand_Implementation()
{
    UACFBaseCommand* commptr;
    if (commandToExecute.Dequeue(commptr)) {
        currentCommand = commptr;
        if (controllerOwner) {
            controllerOwner->StopMovement();
        }
        // controllerOwner->SetWaitDurationTimeBK(currentCommand->EstimatedDurationWait);
        currentCommand->OnCommandFinished.AddDynamic(this, &UACFCommandsManagerComponent::HandleCommandFinished);
        currentCommand->InternalExecute(controllerOwner);
    }
}

bool UACFCommandsManagerComponent::ExecutePendingCommand_Validate()
{
    return true;
}

bool UACFCommandsManagerComponent::RemoveCommand(const FGameplayTag& CommandTag)
{
    // Check if command exists before attempting removal
    if (!commands.Contains(CommandTag)) {
        UE_LOG(LogTemp, Warning, TEXT("Command with tag %s not found - UACFCommandsManagerComponent::RemoveCommand"), 
            *CommandTag.ToString());
        return false;
    }

    // Remove the command from the map
    commands.Remove(CommandTag);

    UE_LOG(LogTemp, Log, TEXT("Command with tag %s removed successfully - UACFCommandsManagerComponent::RemoveCommand"), 
        *CommandTag.ToString());

    return true;
}

bool UACFCommandsManagerComponent::HasCommandWithTag(const FGameplayTag& CommandTag) const
{
    // Check if the command map contains the specified tag
    return commands.Contains(CommandTag);
}

bool UACFCommandsManagerComponent::AddCommand(const FGameplayTag& CommandTag, TSubclassOf<UACFBaseCommand> CommandClass, bool bTriggerImmediately /*= false*/)
{
    // Validate input parameters
    if (!CommandTag.IsValid()) {
        UE_LOG(LogTemp, Error, TEXT("Invalid CommandTag - UACFCommandsManagerComponent::AddCommand"));
        return false;
    }

    if (!CommandClass) {
        UE_LOG(LogTemp, Error, TEXT("Invalid CommandClass - UACFCommandsManagerComponent::AddCommand"));
        return false;
    }

    // Check if command with this tag already exists
    if (commands.Contains(CommandTag)) {
        UE_LOG(LogTemp, Warning, TEXT("Command with tag %s already exists, replacing it - UACFCommandsManagerComponent::AddCommand"), 
            *CommandTag.ToString());
    }

    // Create a new instance of the command
    UACFBaseCommand* NewCommand = NewObject<UACFBaseCommand>(this, CommandClass);
    
    if (!NewCommand) {
        UE_LOG(LogTemp, Error, TEXT("Failed to create command instance for tag %s - UACFCommandsManagerComponent::AddCommand"), 
            *CommandTag.ToString());
        return false;
    }

    // Add or replace the command in the map
    commands.Add(CommandTag, NewCommand);

    UE_LOG(LogTemp, Log, TEXT("Command with tag %s added successfully - UACFCommandsManagerComponent::AddCommand"), 
        *CommandTag.ToString());

    // Optionally trigger the command immediately
    if (bTriggerImmediately) {
        TriggerCommand(CommandTag);
    }

    return true;
}

bool UACFCommandsManagerComponent::IsExecutingCommand() const
{
    // Check if there is a command currently being executed
    return currentCommand != nullptr;
}
