// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Commands/ACFBaseCommand.h"
#include "ACFAIController.h"
#include "Actors/ACFCharacter.h"



void UACFBaseCommand::FinishExecution(bool bSuccess)
{
    OnCommandFinished.Broadcast(bSuccess);
}

void UACFBaseCommand::InternalExecute(class AACFAIController* controller)
{
    aiController = controller;
    ExecuteCommand(aiController);
}

void UACFBaseCommand::ExecuteCommand_Implementation(class AACFAIController* controller)
{

}

void UACFBaseCommand::EndCommand_Implementation(class AACFAIController* controller)
{

}

UWorld* UACFBaseCommand::GetWorld() const
{
    if (aiController) {
        return aiController->GetWorld();
    }
    return nullptr;
}



