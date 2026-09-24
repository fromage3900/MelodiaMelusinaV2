// Copyright UNAmedia. All Rights Reserved.
/*
### LEGAL NOTICE ###
### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

No changes to the code of this file are permitted, including any changes to other code that alter its intended execution.
Individuals and organizations making any modifications and/or users and organizations using unauthorized modifications are deemed to be in violation of the license terms.
For any need to customize this file you can contact UNAmedia.

### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
*/

#pragma once

#if WITH_EDITOR

#include "UNAAuth/AuthManager.h"

#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Input/Reply.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SWindow.h"


class SAuthDialog : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SAuthDialog){}

	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, 
		const TSharedRef<SWindow>& InParentWindow,
		EPluginAuthorizationState AuthorizationState,
		const FUNAPluginInfo& PluginInfo);

private:

	/** Called when the user presses the Cancel button. */
	FReply OnCancel();

	bool IsQuitButtonEnabled() const;
	FText GetQuitButtonText() const;

	void OnWindowClosed(const TSharedRef<SWindow>& InWindow);

	FReply OnOpenStore();

private:
	/** The parent window holding this dialog, for when we need to trigger a close. */
	TWeakPtr<SWindow> ParentWindow;

	const double WaitTime = 5;
	double StartTime = 0;

	FUNAPluginInfo PluginInfo;
};

#endif // WITH_EDITOR
