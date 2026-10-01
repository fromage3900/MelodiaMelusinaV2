// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <Input/Events.h>

#include "ANSNavbarFunctionLibrary.generated.h"

/**
 *
 */
/*enum class ECommonInputType : uint8;*/

UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSNavbarFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    /*Returns the type of input (gamepad, keyboard, mouse) for this event*/
    UFUNCTION(BlueprintCallable, Category = ANS)
    static ECommonInputType GetInputTypeByKeyEvent(const FKeyEvent& InKeyEvent);

    UFUNCTION(BlueprintCallable, Category = ANS)
    static ECommonInputType GetCommonInputTypeByKey(const FKey& InKey);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ANSLibrary)
    static class UTexture2D* GetIconByTag(const class UObject* WorldContextObject, const FGameplayTag& IconTag);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ANSLibrary)
    static class UTexture2D* GetIconByKey(const class UObject* WorldContextObject, const FKey& key);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ANSLibrary)
    static TArray<FKey> GetKeysForAction(const class UObject* WorldContextObject, const UInputAction* action);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ANSLibrary)
    static class UTexture2D* GetKeyIconForActionAndInputType(const class UObject* WorldContextObject, const UInputAction* action, ECommonInputType inputType);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ANSLibrary)
    static class UTexture2D* GetKeyIconForUIAction(const class UObject* WorldContextObject, const FUIActionTag& action);

};
