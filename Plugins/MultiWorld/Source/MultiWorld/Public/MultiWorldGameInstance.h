// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"

#include "MultiWorldGameInstance.generated.h"

/**
 * Custom GameInstance class needed to support MultiWorld on your project.
 *
 * To set it on your project just open the "Project Settings" panel, 
 * go to "Maps and Modes", here search for the property "Game Instance Class" and then set it to @c MultiWorldGameInstance.
 *
 * If you can't use this implementation, follow the instructions at #UMultiWorldOverrides.
 */
UCLASS()
class MULTIWORLD_API UMultiWorldGameInstance : public UGameInstance
{
    GENERATED_BODY()

public:

    /** Override of <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameInstance/Exec/index.html">UGameInstance::Exec()</a> */
    virtual bool Exec(UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar) override;

    /** Override of <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameInstance/OnWorldChanged/index.html">UGameInstance::OnWorldChanged()</a> */
    virtual void OnWorldChanged(UWorld* OldWorld, UWorld* NewWorld) override;
};
