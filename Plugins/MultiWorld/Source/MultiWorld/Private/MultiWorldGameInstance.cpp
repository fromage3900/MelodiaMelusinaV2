// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldGameInstance.h"

#include "MultiWorldOverrides.h"

bool UMultiWorldGameInstance::Exec(UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar)
{    
    return UMultiWorldOverrides::GameInstance_Exec(this, InWorld, Cmd, Ar);
}

void UMultiWorldGameInstance::OnWorldChanged(UWorld* OldWorld, UWorld* NewWorld)
{
    UMultiWorldOverrides::GameInstance_OnWorldChanged(this, OldWorld, NewWorld);
}
