// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ANSNavPageWidget.h"
#include "CoreMinimal.h"

#include "ANSNavPopUpWidget.generated.h"


/**
 * Modal pop-up page that inherits from ANSNavPageWidget.
 *
 * Push this widget onto a separate UI layer (e.g. UI.Layer.Modal) so the page
 * underneath stays visible. Common UI automatically routes input to the topmost
 * active widget and restores focus when this pop-up is deactivated.
 */
UCLASS()
class ASCENTUINAVIGATIONSYSTEM_API UANSNavPopUpWidget : public UANSNavPageWidget {
	GENERATED_BODY()

public:
	UANSNavPopUpWidget();

protected:
	virtual void NativeOnDeactivated() override;

	/** The page that spawned this pop-up. Available for Blueprint logic that needs a reference back to the owner. */
	UPROPERTY(BlueprintReadWrite, Category = ANS, Meta = (ExposeOnSpawn = true))
	UANSNavPageWidget* pageOwner;

	/** Restores navigation on the owning page and returns focus to its last focused widget. */
	UFUNCTION(BlueprintCallable, Category = ANS)
	void ResetFocusOnOwner();
};
