// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2025.
// All Rights Reserved.


#include "ACFTimeBlueprintLibrary.h"
#include "DaySequenceActor.h"
#include "DaySequenceSubsystem.h"
#include <Engine/Engine.h>

void UACFTimeBlueprintLibrary::GetTimeOfTheDayText(const UObject* WorldContextObject,
									FText& OutHoursText,
									FText& OutMinutesText)
{
	int32 Hours = 0;
	int32 Minutes = 0;
	
	if (const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UDaySequenceSubsystem* DaySequenceSubsystem =World->GetSubsystem<UDaySequenceSubsystem>())
		{
			if (ADaySequenceActor* DayActor = DaySequenceSubsystem->GetDaySequenceActor(/*bFindFallback*/ true))
			{
				int TimeToInt =FMath::RoundToInt(DayActor->GetTimeOfDay()*3600);
				int32 SecondsInDay = TimeToInt % 86400;
				Hours = SecondsInDay / 3600;
				Minutes = (SecondsInDay % 3600)/60;
			}
		}
	}	

	// Hours: no padding, Minutes: 2 digits (00..59) — no locale grouping
	OutHoursText   = FText::FromString(FString::Printf(TEXT("%d"),   Hours));
	OutMinutesText = FText::FromString(FString::Printf(TEXT("%02d"), Minutes));


}
