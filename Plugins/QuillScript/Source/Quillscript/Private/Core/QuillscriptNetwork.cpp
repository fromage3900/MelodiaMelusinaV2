// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptNetwork.h"

#include "Utils/Quill.h"
#include "Utils/Tools.h"


AQuillscriptNetwork::AQuillscriptNetwork()
{
	// Settings.
	this->PrimaryActorTick.bCanEverTick = false;
	this->bReplicates = true;
	this->bAlwaysRelevant = true;
}


#pragma region RPC

#pragma region Server

#pragma region Data

void AQuillscriptNetwork::Server_Join_Implementation(const APlayerState* CallerPlayerState)
{
	// Find what script is playing in the caller.

	WARNING("Server");

	this->Multi_Join(CallerPlayerState);
}

#pragma endregion Data

#pragma endregion Server


#pragma region Clients

#pragma region Data

void AQuillscriptNetwork::Multi_Join_Implementation(const APlayerState* CallerPlayerState)
{
	ERROR("Client");

	//UQuill::ResumeScript();
}

#pragma endregion Data

#pragma endregion Clients

#pragma endregion RPC