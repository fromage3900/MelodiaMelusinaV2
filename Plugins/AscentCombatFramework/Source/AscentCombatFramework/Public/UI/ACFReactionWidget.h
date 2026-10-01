// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Blueprint/UserWidget.h"
#include "ACFReactionWidget.generated.h"

/**
 * Widget used to display a short reaction message (e.g. hit, block, parry) based on a gameplay tag.
 * Implement SetupReactionWidget in Blueprint to show the message mapped to the given tag.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFReactionWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Called to set up the widget with the event tag; implement in Blueprint to show the matching message. */
	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = ACF)
	void SetupReactionWidget(const FGameplayTag& tagEvent);

protected:
	/** Maps gameplay tags (e.g. Hit, Block) to the text to display. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	TMap<FGameplayTag, FText> TagEventToMessage;
};
