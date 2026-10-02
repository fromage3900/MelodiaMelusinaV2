// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/HorizontalBox.h"
#include "UITag.h"
#include "ANSNavWidget.h"
#include "UANSHorizontalNavBox.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnHorizontalIndexChanged, int32, CurrentIndex);

UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSHorizontalNavBox : public UHorizontalBox
{
	GENERATED_BODY()

public:
	UANSHorizontalNavBox();

	UFUNCTION(BlueprintCallable, Category = "ANS Navigation")
	void ProcessOnKeyDown(const FKeyEvent& InKeyEvent);

	UFUNCTION(BlueprintCallable, Category = "ANS Navigation")
	void NavigateToNext();

	UFUNCTION(BlueprintCallable, Category = "ANS Navigation")
	void NavigateToPrevious();

	UFUNCTION(BlueprintCallable, Category = "ANS Navigation")
	void SetSelectedIndex(int32 NewIndex);

	UFUNCTION(BlueprintPure, Category = "ANS Navigation")
	int32 GetSelectedIndex() const { return SelectedIndex; }

	UFUNCTION(BlueprintPure, Category = "ANS Navigation")
	UWidget* GetSelectedWidget() const;

protected:
	virtual void OnSlotAdded(UPanelSlot* InSlot) override;
	virtual void OnSlotRemoved(UPanelSlot* InSlot) override;

private:
	void UpdateChildrenVisuals();

	class UANSUIPlayerSubsystem* GetUISubsystem() const;

public:
	UPROPERTY(BlueprintAssignable, Category = "ANS Navigation")
	FOnHorizontalIndexChanged OnIndexChanged;

protected:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ANS Navigation")
	FUIActionTag NextAction;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ANS Navigation")
	FUIActionTag PreviousAction;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ANS Navigation")
	bool bAllowCircularNavigation = true;

private:
	int32 SelectedIndex = 0;
};