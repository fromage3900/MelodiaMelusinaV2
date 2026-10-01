// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "InputAction.h"
#include "InputCoreTypes.h"
#include "UITag.h"
#include <Styling/SlateTypes.h>

#include "ANSUITypes.generated.h"

/**
 *
 */
// UENUM(BlueprintType)
// enum class EANSInputType : uint8 {
//     EMouseOrKeyboard UMETA(DisplayName = "Keyboard or Mouse"),
//     EGamepad UMETA(DisplayName = "Gamepad")
// };

USTRUCT(BlueprintType)
struct FANSTutorialSettings {

    GENERATED_BODY()

    FANSTutorialSettings()
    {
        InputAction = nullptr;
    }

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ANS)
    UInputAction* InputAction;

    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ANS)
    FText InputDescription;
};

USTRUCT(BlueprintType)
struct FANSActionConfig {
    GENERATED_BODY()

public:
    FANSActionConfig()
    {
        KeyIcon = nullptr;
    }

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    FText UIName;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    UTexture2D* KeyIcon;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    FUIActionTag Action;
};

// USTRUCT(BlueprintType)
// struct FANSActions : public FTableRowBase {
//     GENERATED_BODY()
// 
// public:
//     UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
//     FUIActionTag UIAction;
// 
//     UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
//     FText UIText;
// 
//     UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
//     TMap<EANSInputType, FKey> TriggeringKeys;
// 
//     FORCEINLINE bool operator!=(const FGameplayTag& Other) const
//     {
//         return UIAction != Other;
//     }
// 
//     FORCEINLINE bool operator==(const FGameplayTag& Other) const
//     {
//         return UIAction == Other;
//     }
// 
//     FORCEINLINE bool operator!=(const FANSActions& Other) const
//     {
//         return UIAction != Other.UIAction;
//     }
// 
//     FORCEINLINE bool operator==(const FANSActions& Other) const
//     {
//         return UIAction == Other.UIAction;
//     }
// };

USTRUCT(BlueprintType)
struct FANSKeysIconConfig : public FTableRowBase {
    GENERATED_BODY()

public:
    FANSKeysIconConfig()
    {
        KeyIcon = nullptr;
    }

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    FKey Key;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    class UTexture2D* KeyIcon;
};

USTRUCT(BlueprintType)
struct FANSIcons : public FTableRowBase {
    GENERATED_BODY()

public:
    FANSIcons()
    {
        Icon = nullptr;
    }

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    FGameplayTag IconTag;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ANS)
    class UTexture2D* Icon;
};

USTRUCT(BlueprintType)
struct FFocusedWidget {
    GENERATED_BODY()

public:
    FFocusedWidget()
    {
        parentNavWidget = nullptr;
        focusedWidget = nullptr;
    }

    FFocusedWidget(class UWidget* inWidget, class UANSNavWidget* inNavWidget)
    {
        focusedWidget = inWidget;
        parentNavWidget = inNavWidget;
    }

    UPROPERTY(BlueprintReadOnly, Category = ANS)
    TObjectPtr<class UANSNavWidget> parentNavWidget;

    UPROPERTY(BlueprintReadOnly, Category = ANS)
    TObjectPtr<class UWidget> focusedWidget;

    FButtonStyle initStyle;
};

UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSUITypes : public UObject {
    GENERATED_BODY()
};
