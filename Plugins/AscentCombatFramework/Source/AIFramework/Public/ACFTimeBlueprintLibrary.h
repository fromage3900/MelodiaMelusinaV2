// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2025.
// All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ACFTimeBlueprintLibrary.generated.h"

class UDaySequenceSubsystem;

/**
 * 
 */
UCLASS()
class AIFRAMEWORK_API UACFTimeBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

	UFUNCTION(BlueprintCallable, Category="ACF|Time")
	static void GetTimeOfTheDayText(const UObject* WorldContextObject,
									FText& OutHoursText,
									FText& OutMinutesText);
};
