// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSSaveTypes.h"

// Serialize() implementations are in ALSSaveTypes.h as inline to fix LNK2001
// when other modules (e.g. AIFramework) use FALSActorData in UPROPERTY(SaveGame).

FALSObjectData::FALSObjectData(const UObject* Object) : Super()
{
	alsName = Object->GetFName();
	Class = Object->GetClass();
}

