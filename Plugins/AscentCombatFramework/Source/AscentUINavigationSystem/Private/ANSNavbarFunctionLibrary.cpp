// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSNavbarFunctionLibrary.h"
#include "ANSUIPlayerSubsystem.h"
#include "CommonInputTypeEnum.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputSubsystems.h"
#include <GameFramework/PlayerController.h>
#include <Input/Events.h>
#include <InputCoreTypes.h>
#include <Kismet/GameplayStatics.h>

#include "ANSUITypes.h"
#include "CommonInputSubsystem.h"
#include "UITag.h"
#include <Engine/GameInstance.h>
#include <Engine/World.h>

ECommonInputType UANSNavbarFunctionLibrary::GetInputTypeByKeyEvent(const FKeyEvent& InKeyEvent)
{
    return UANSNavbarFunctionLibrary::GetCommonInputTypeByKey(InKeyEvent.GetKey());
}

ECommonInputType UANSNavbarFunctionLibrary::GetCommonInputTypeByKey(const FKey& InKey)
{
    if (InKey.IsGamepadKey()) {
        return ECommonInputType::Gamepad;
    }
    return ECommonInputType::MouseAndKeyboard;
}

class UTexture2D* UANSNavbarFunctionLibrary::GetIconByTag(const class UObject* WorldContextObject, const FGameplayTag& IconTag)
{
    const UGameInstance* gameInst = UGameplayStatics::GetGameInstance(WorldContextObject);

    UANSUIPlayerSubsystem* UISub = gameInst->GetSubsystem<UANSUIPlayerSubsystem>();

    if (UISub) {
      return UISub->GetIconByTag(IconTag);
    }

    return nullptr;
}

class UTexture2D* UANSNavbarFunctionLibrary::GetIconByKey(const class UObject* WorldContextObject, const FKey& key)
{
    const UGameInstance* gameInst = UGameplayStatics::GetGameInstance(WorldContextObject);
    UANSUIPlayerSubsystem* UISub = gameInst->GetSubsystem<UANSUIPlayerSubsystem>();

    return UISub->GetCurrentPlatformIconForKey(key);
}

TArray<FKey> UANSNavbarFunctionLibrary::GetKeysForAction(const class UObject* WorldContextObject, const UInputAction* action)
{
    ULocalPlayer* localPlayer;
    if (WorldContextObject && WorldContextObject->GetWorld()) {
        localPlayer = WorldContextObject->GetWorld()->GetFirstLocalPlayerFromController();
        if (localPlayer) {

            UEnhancedInputLocalPlayerSubsystem* enhancedSub = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(localPlayer);
            if (enhancedSub) {
                return enhancedSub->QueryKeysMappedToAction(action);
            }
        }
    }
    UE_LOG(LogTemp, Warning, TEXT("Impossible to find Keys for action!- UANSNavbarFunctionLibrary::GetKeysForAction"));

    return TArray<FKey>();
}

class UTexture2D* UANSNavbarFunctionLibrary::GetKeyIconForActionAndInputType(const class UObject* WorldContextObject, const UInputAction* action, ECommonInputType inputType)
{
    TArray<FKey> keys = UANSNavbarFunctionLibrary::GetKeysForAction(WorldContextObject, action);
    for (const auto& key : keys) {
        if ((key.IsGamepadKey() && inputType == ECommonInputType::Gamepad) || (!key.IsGamepadKey() && inputType == ECommonInputType::MouseAndKeyboard)) {
            return GetIconByKey(WorldContextObject, key);
        }
    }
    UE_LOG(LogTemp, Warning, TEXT("Impossible to find Key Texture for action!- UANSNavbarFunctionLibrary::GetKeysForAction"));
    return nullptr;
}

class UTexture2D* UANSNavbarFunctionLibrary::GetKeyIconForUIAction(const class UObject* WorldContextObject, const FUIActionTag& action)
{
    ULocalPlayer* localPlayer;
    if (WorldContextObject && WorldContextObject->GetWorld()) {
        localPlayer = WorldContextObject->GetWorld()->GetFirstLocalPlayerFromController();
        UCommonInputSubsystem* inputSub = ULocalPlayer::GetSubsystem<UCommonInputSubsystem>(localPlayer);

        ECommonInputType inputType = inputSub->GetCurrentInputType();
        const UGameInstance* gameInst = UGameplayStatics::GetGameInstance(WorldContextObject);
        UANSUIPlayerSubsystem* UISub = gameInst->GetSubsystem<UANSUIPlayerSubsystem>();

        TArray<FKey> outMapping;

        if (UISub->TryGetKeysForAction(action, outMapping)) {
            for (const auto& Key : outMapping) {
                if ((Key.IsGamepadKey() && inputType == ECommonInputType::Gamepad) || (!Key.IsGamepadKey() && inputType == ECommonInputType::MouseAndKeyboard)) {
                    return GetIconByKey(WorldContextObject, Key);
                }
            }
        }

        UE_LOG(LogTemp, Warning, TEXT("Impossible to find Key Texture for action!- UANSNavbarFunctionLibrary::GetKeysForAction"));
        
    }
    return nullptr;
}
