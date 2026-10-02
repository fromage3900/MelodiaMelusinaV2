// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include <GameplayTagContainer.h>
#include <NativeGameplayTags.h>

#include "ACFItemTypes.generated.h"


/**
 *
 */

UENUM(BlueprintType)
enum class EProjectileHitPolicy : uint8 {
    DestroyOnHit = 0 UMETA(DisplayName = "Destroy On Hit"),
    AttachOnHit = 1 UMETA(DisplayName = "Attach On Hit"),
    DoNothing = 2 UMETA(DisplayName = "Do Nothing"),
};

UENUM(BlueprintType)
enum class EBowState : uint8 {
    EIdle = 0 UMETA(DisplayName = "Idle"),
    EPulling = 1 UMETA(DisplayName = "Pull"),
    ERelease = 2 UMETA(DisplayName = "Release"),
};

UENUM(BlueprintType)
enum class EHandleType : uint8 {
    OneHanded = 0 UMETA(DisplayName = "One Hand"),
    OffHand = 1 UMETA(DisplayName = "Off-Hand Weapon"),
    TwoHanded = 2 UMETA(DisplayName = "Two Handed Weapon"),
};

/** Defines how to the shoot trace is handled */
UENUM(BlueprintType)
enum class EShootTargetType : uint8 {
    // From the player's camera towards camera focus
    CameraTowardsFocus,
    // From the pawn's center, in the pawn's orientation
    PawnForward,
    // From the pawn's center, oriented towards camera focus
    PawnTowardsFocus,
    // From the weapon's muzzle or location, in the pawn's orientation
    WeaponForward,
    // From the weapon's muzzle or location, towards camera focus
    WeaponTowardsFocus,
};

UENUM(BlueprintType)
enum class EItemType : uint8 {
    Armor = 0 UMETA(DisplayName = "Armor"),
    MeleeWeapon = 1 UMETA(DisplayName = "Melee Weapon"),
    RangedWeapon = 2 UMETA(DisplayName = "Ranged Weapon"),
    Consumable = 3 UMETA(DisplayName = "Consumable"),
    Material = 4 UMETA(DisplayName = "Material"),
    Accessory = 5 UMETA(DisplayName = "Accessory"),
    Projectile = 6 UMETA(DisplayName = "Ammo"),
    Quest = 7 UMETA(DisplayName = "Quest Item"),
    Other = 8 UMETA(DisplayName = "Other"),
};


namespace FACFTags
{
	UE_DECLARE_GAMEPLAY_TAG_EXTERN(WeaponShoot);
	UE_DECLARE_GAMEPLAY_TAG_EXTERN(WeaponPull);
	UE_DECLARE_GAMEPLAY_TAG_EXTERN(WeaponReload);

}


UENUM(BlueprintType)
enum class EInventorySource : uint8
{
	Pawn        UMETA(DisplayName = "Pawn"),
	Controller  UMETA(DisplayName = "Controller")
};



USTRUCT(BlueprintType)
struct FModularPart {
    GENERATED_BODY()

public:
    FModularPart()
    {
        meshComp = nullptr;
    };

    FModularPart(const TObjectPtr<class UACFArmorSlotComponent>& inComp);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag ItemSlot;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFArmorSlotComponent> meshComp;

    FORCEINLINE bool operator==(const FModularPart& Other) const
    {
        return this->ItemSlot == Other.ItemSlot;
    }

    FORCEINLINE bool operator!=(const FModularPart& Other) const
    {
        return this->ItemSlot != Other.ItemSlot;
    }

    FORCEINLINE bool operator!=(const FGameplayTag& Other) const
    {
        return this->ItemSlot != Other;
    }

    FORCEINLINE bool operator==(const FGameplayTag& Other) const
    {
        return this->ItemSlot == Other;
    }
};

USTRUCT(BlueprintType)
struct FItemGenerationSlot : public FTableRowBase {
    GENERATED_BODY()

public:
    FItemGenerationSlot() {};

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag Category;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag Rarity;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    TSoftClassPtr<class UACFItem> ItemClass;
};

USTRUCT(BlueprintType)
struct FACFItemGenerationRule {
    GENERATED_BODY()

public:
    FACFItemGenerationRule() {};

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag Category;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag Rarity;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    int32 MinItemCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    int32 MaxItemCount = 1;
};

UENUM(BlueprintType)
enum class EShootingType : uint8 {
    EProjectile UMETA(DisplayName = "Shoot Projectile"),
    ESwipeTrace UMETA(DisplayName = "Shoot Swipe Trace"),
};

UCLASS()
class INVENTORYSYSTEM_API UACFItemTypes : public UObject {
    GENERATED_BODY()
};
