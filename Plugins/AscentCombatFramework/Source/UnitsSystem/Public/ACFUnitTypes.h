// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "ACFUnitTypes.generated.h"

/**
 *
 */

UENUM(BlueprintType)
enum class EConqueredState : uint8 {
    ENotConquered = 0 UMETA(DisplayName = "Not Conquered"),
/*    EConquerStart = 1 UMETA(DisplayName = "Conquer Setup"),*/
    EConquerInProgress = 2 UMETA(DisplayName = "Conquer In Progress"),
    EConquered = 3 UMETA(DisplayName = "Conquered"),
};

UCLASS()
class UNITSSYSTEM_API UACFUnitTypes : public UObject {
    GENERATED_BODY()

public:
    UACFUnitTypes() {};
};
// class UNITSSYSTEM_API ACFUnitTypes
// {
// public:
// 	ACFUnitTypes();
// 	~ACFUnitTypes();
// };
