// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaUIWiringComponent.generated.h"

class UUserWidget;
class UWidget;

UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaUIWiringComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaUIWiringComponent();

	// Wire a button to a function
	UFUNCTION(BlueprintCallable, Category="Melodia|UI")
	void WireButton(UUserWidget* Widget, const FString& ButtonName, const FString& FunctionName);

	// Wire a widget to an event
	UFUNCTION(BlueprintCallable, Category="Melodia|UI")
	void WireWidgetEvent(UUserWidget* Widget, const FString& WidgetName, const FString& EventName);

	// Get a widget by name
	UFUNCTION(BlueprintCallable, Category="Melodia|UI")
	UWidget* GetWidgetByName(UUserWidget* Widget, const FString& WidgetName);

protected:
	virtual void BeginPlay() override;

private:
    UPROPERTY(EditAnywhere, Category="Melodia|UI")
    TArray<FString> AutoWireButtons;

    UPROPERTY(EditAnywhere, Category="Melodia|UI")
    TArray<FString> AutoWireEvents;

    UWidget* FindWidgetRecursive(UWidget* ParentWidget, const FString& WidgetName);
};