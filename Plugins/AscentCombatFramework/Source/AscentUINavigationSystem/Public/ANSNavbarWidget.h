// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSUITypes.h"
#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "UITag.h"
#include <GameplayTagContainer.h>
#include <Input/Events.h>
#include <Layout/Geometry.h>
#include <CommonActivatableWidget.h>

#include "ANSNavbarWidget.generated.h"

class UCommonInputSubsystem;

/** Delegate broadcast when a navbar action is triggered (e.g. button press). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FANSOnActionTriggered, const FUIActionTag&, actionName);

/**
 * Navigation bar widget that shows a list of actions (UIActions) and broadcasts when one is triggered.
 * Implement FillNavbar and OnButtonPressed in Blueprint to build the bar and handle input.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSNavbarWidget : public UCommonActivatableWidget {
    GENERATED_BODY()

protected:
    virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;


	UCommonInputSubsystem* GetInputSubsystem() const;

    /** Rebuilds the navbar from UIActions; calls FillNavbar. */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void BuildNavbar();

    /** Broadcasts OnActionTriggered locally and globally through the subsystem. */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void DispatchOnActionTriggered(const FUIActionTag& action);


    /** Called to populate the bar with buttons from action configs; implement in Blueprint. */
    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void FillNavbar(const TArray<FANSActionConfig>& actionConfigs);

    /** Called when a navbar button is pressed; implement in Blueprint. */
    UFUNCTION(BlueprintImplementableEvent, Category = ANS)
    void OnButtonPressed(const FUIActionTag& action);

public:

    UANSNavbarWidget(const FObjectInitializer& ObjectInitializer);

    /** List of action tags shown in the navbar (e.g. Back, Confirm). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ANS)
    TArray<FUIActionTag> UIActions;

    UPROPERTY(BlueprintAssignable, Category = ANS)
    FANSOnActionTriggered OnActionTriggered;

    UFUNCTION(BlueprintPure, Category = ANS)
    ECommonInputType GetCurrentInputType() const;

    UFUNCTION(BlueprintCallable, Category = ANS)
    void ProcessOnKeyDown(const FKeyEvent& InKeyEvent);

    void ProcessOnNavigation(const FGeometry& MyGeometry, const FNavigationEvent& InNavigationEvent);

    UFUNCTION(BlueprintCallable, Category = ANS)
    void AddNavbarAction(FUIActionTag action);

    UFUNCTION(BlueprintCallable, Category = ANS)
    void RemoveNavbarAction(FUIActionTag action);

    /** Replaces the current list of navbar actions. */
    UFUNCTION(BlueprintCallable, Category = ANS)
    void SetNavbarActions(const TArray<FUIActionTag>& action);

private:
    ECommonInputType InputType;

    UFUNCTION()
    void HandleInputChanged(ECommonInputType bNewInputType);

    UFUNCTION()
    void HandleGlobalAddAction(const FUIActionTag& ActionTag);

    UFUNCTION()
    void HandleGlobalRemoveAction(const FUIActionTag& ActionTag);

    UFUNCTION()
    void HandleGlobalSetActions(const TArray<FUIActionTag>& ActionTags);
};
