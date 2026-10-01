// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Game/ACFDamageType.h"
#include "ACFMountSystemFunctionLibrary.generated.h"

/**
 * 
 */
UCLASS()
class MOUNTSYSTEM_API UACFMountSystemFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:	
    /*Returns the local player OR his rider if locally controlled player is a rided mount*/
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
    static class AACFCharacter* GetLocalRiderPlayerCharacter(const UObject* WorldContextObject);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
    static class AActor* GetLocalBestInteractable(const UObject* WorldContextObject);

    /** Returns the actor the local player is currently actively interacting with (null when no interaction is in progress). */
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
    static class AActor* GetLocalCurrentInteractingActor(const UObject* WorldContextObject);


    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static bool DoesDamageInvolveLocalPlayer(const FACFDamageEvent& damageEvent, bool& bIsVictim);
	
};
