// Copyright UNAmedia. All Rights Reserved.
/*
### LEGAL NOTICE ###
### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

No changes to the code of this file are permitted, including any changes to other code that alter its intended execution.
Individuals and organizations making any modifications and/or users and organizations using unauthorized modifications are deemed to be in violation of the license terms.
For any need to customize this file you can contact UNAmedia.

### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
*/

#if WITH_EDITOR

#include "UNAAuth/SAuthDialog.h"

#include "Misc/MessageDialog.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Input/SButton.h"
//#include "Widgets/Input/SHyperlink.h"
#include "Widgets/Text/SRichTextBlock.h"
#include "Styling/CoreStyle.h"
#include "Styling/AppStyle.h"
#include "Editor.h"
//#include "Widgets/Images/SThrobber.h"

#include "ILauncherPlatform.h"
#include "LauncherPlatformModule.h"

#define LOCTEXT_NAMESPACE "UNAmedia_SAuthDialog"


namespace SAuthDialog_Private
{

struct PluginAuthorizationStateInfo
{
	FString StateId;
	FText Description;

	PluginAuthorizationStateInfo()
	{}

	PluginAuthorizationStateInfo(const FString& id)
		: StateId(id),
		  Description(FText::GetEmpty())
	{
	}

	PluginAuthorizationStateInfo(const FString & id, const FText & desc)
		: StateId(id),
		  Description(desc)
	{}
};


#define PluginAuthorizationStateToString_ENTRY_(STATE)	{ EPluginAuthorizationState::STATE, { TEXT(#STATE) }, }
#define PluginAuthorizationStateToString_ENTRY_WITHDESC_(STATE,DESC)	{ EPluginAuthorizationState::STATE, { TEXT(#STATE), LOCTEXT("UNAmedia_SAuthDialog_PluginAuthorizationState_Description_" #STATE, DESC) }, }

static const TMap<EPluginAuthorizationState, PluginAuthorizationStateInfo> PluginAuthorizationState_To_Info = {
	PluginAuthorizationStateToString_ENTRY_(Initializing),
	PluginAuthorizationStateToString_ENTRY_(StartLauncher),
	PluginAuthorizationStateToString_ENTRY_(StartLauncher_Waiting),
	PluginAuthorizationStateToString_ENTRY_(AuthorizePlugin),
	PluginAuthorizationStateToString_ENTRY_(AuthorizePlugin_Waiting),
	PluginAuthorizationStateToString_ENTRY_(IsUserSignedIn),
	PluginAuthorizationStateToString_ENTRY_(IsUserSignedIn_Waiting),
	PluginAuthorizationStateToString_ENTRY_(SigninRequired),
	PluginAuthorizationStateToString_ENTRY_(SigninRequired_Waiting),
	PluginAuthorizationStateToString_ENTRY_(Signin_Waiting),
	// Starting from Signin_Timout included, they are "final" states.
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(Signin_Timeout, "The sign-in process took too long, likely due to network issues. This can also be caused by the inability to communicate with the Epic Games Launcher. Check your connection and settings, then retry."),
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(SigninFailed, "Sign-in failed due to incorrect credentials or account issues. Verify your username/email and password are correct."),
	PluginAuthorizationStateToString_ENTRY_(Authorized),
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(Unauthorized, "No valid license found for your account. Please ensure your purchase is completed and linked correctly to your account. Visit the Store page to verify your purchase, or contact support for assistance."),
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(LauncherStartFailed, "The Epic Games Launcher could not start successfully. Restart your computer and try launching the application again."),
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(Timeout, "Operation took too long to complete, likely due to network or server issues. This can also be caused by the inability to communicate with the Epic Games Launcher. Check your connection and settings, then retry."),
	PluginAuthorizationStateToString_ENTRY_WITHDESC_(Canceled, "Operation was canceled, possibly by user intervention or error. Restart the process and check for interruptions.")
};

#undef PluginAuthorizationStateToString_ENTRY_WITHDESC_
#undef PluginAuthorizationStateToString_ENTRY_


FString PluginAuthorizationStateToString(EPluginAuthorizationState AuthorizationState)
{
	static const FString Unknown(TEXT("Unknown"));
	const PluginAuthorizationStateInfo* s = PluginAuthorizationState_To_Info.Find(AuthorizationState);
	return s != nullptr ? s->StateId : Unknown;
}


FText PluginAuthorizationStateToDescription(EPluginAuthorizationState AuthorizationState)
{
	const PluginAuthorizationStateInfo* s = PluginAuthorizationState_To_Info.Find(AuthorizationState);
	return s != nullptr ? s->Description : FText::GetEmpty();
}


static void OnBrowserLinkClicked(const FSlateHyperlinkRun::FMetadata& Metadata, TSharedRef<SWidget> ParentWidget)
{
	const FString* UrlPtr = Metadata.Find(TEXT("href"));
	if (UrlPtr)
	{
		FPlatformProcess::LaunchURL(**UrlPtr, nullptr, nullptr);
	}
}

} // namespace SAuthDialog_Private


void SAuthDialog::Construct(
	const FArguments& InArgs, 
	const TSharedRef<SWindow>& InParentWindow, 
	EPluginAuthorizationState AuthorizationState, 
	const FUNAPluginInfo& InPluginInfo)
{
	ParentWindow = InParentWindow;
	PluginInfo = InPluginInfo;

	InParentWindow->SetOnWindowClosed(FOnWindowClosed::CreateSP(this, &SAuthDialog::OnWindowClosed));

	StartTime = FSlateApplication::Get().GetCurrentTime();

	const FText ErrorMessage = FText::Format(
		LOCTEXT("UNAmedia_SAuthDialog_AuthFailedErrorCode_Generic", "Error code \"{0}\" ({1})."),
		FText::FromString(FString::FromInt(static_cast<int32>(AuthorizationState))),
		FText::FromString(SAuthDialog_Private::PluginAuthorizationStateToString(AuthorizationState))
	);
	const FString ReadMoreURL = TEXT("https://docs.unamedia.com/ue-plugin-per-user-license");
	const FText RichBodyText = FText::Format(
		LOCTEXT("UNAmedia_SAuthDialog_AuthFailedMessage_Generic",
R"(<LargeText>We can't find a valid License for {0} linked to your account.</>

<RichTextBlock.TextHighlight>Error</>: <RichTextBlock.Italic>{1} ({2})</>
<RichTextBlock.TextHighlight>Description</>: <RichTextBlock.Italic>{3}</>

<RichTextBlock.Bold>As {0} is licensed on a "per-user" basis, obtaining a valid License is essential for legal use.</>
If you see this message, it means that {0} is running and a valid per-user License is required.

You can visit the <a id="store" style="Common.GotoBlueprintHyperlink">Store page</> to verify that a valid purchase is linked to your account. If your purchase from the Store is valid, please restart the Epic Games Launcher and ensure you are signed in with the correct account. If the issue continues, our <a id="browser" href="{4}" style="Common.GotoBlueprintHyperlink">support team</> is available to assist you.

<RichTextBlock.Bold>We kindly remind you that using {0} without a valid per-user License is not permitted.</>
You can read more about the <RichTextBlock.Italic>License Terms</> and <RichTextBlock.Italic>Troubleshooting</> on <a id="browser" href="{4}" style="Common.GotoBlueprintHyperlink">our website</>.
)"),
		InPluginInfo.FriendlyName,
		FText::FromString(SAuthDialog_Private::PluginAuthorizationStateToString(AuthorizationState)),
		FText::FromString(FString::FromInt(static_cast<int32>(AuthorizationState))),
		SAuthDialog_Private::PluginAuthorizationStateToDescription(AuthorizationState),
		FText::FromString(ReadMoreURL)
	);

	ChildSlot
	[
		SNew(SBox)
		.MaxDesiredWidth(700)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
			[
				SNew(SVerticalBox)

				+ SVerticalBox::Slot()
				.FillHeight(1.0f)
				.Padding(10, 30, 10, 20)
				[
					SNew(SRichTextBlock)
						.Text(RichBodyText)
						.AutoWrapText(true)
						.Margin(10)
						.DecoratorStyleSet(&FAppStyle::Get())
						+ SRichTextBlock::HyperlinkDecorator(TEXT("browser"), FSlateHyperlinkRun::FOnClick::CreateStatic(&SAuthDialog_Private::OnBrowserLinkClicked, AsShared()))
						+ SRichTextBlock::HyperlinkDecorator(TEXT("store"), FSlateHyperlinkRun::FOnClick::CreateLambda([this](const FSlateHyperlinkRun::FMetadata& /*Metadata*/) { OnOpenStore(); }))
				]

				// Dialog buttons
				+ SVerticalBox::Slot()
				.AutoHeight()
				.HAlign(HAlign_Fill)
				.Padding(10)
				[
					SNew(SHorizontalBox)

					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(10)
					[
						SNew(STextBlock)
						.Text(ErrorMessage)
						.WrapTextAt(600)
					]

					+ SHorizontalBox::Slot()
					.FillWidth(1)
					[
						SNew(SSpacer)
					]

					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(10)
					[
						SNew(SButton)
						.Text(LOCTEXT("OpenStoreText", "Open Store"))
						.OnClicked(this, &SAuthDialog::OnOpenStore)
					]

					+ SHorizontalBox::Slot()
					.AutoWidth()
					.Padding(10)
					[
						SNew(SButton)
						.Text(this, &SAuthDialog::GetQuitButtonText)
						.IsEnabled(this, &SAuthDialog::IsQuitButtonEnabled)
						.OnClicked(this, &SAuthDialog::OnCancel)
					]
				]
			]
		]
	];
}

FReply SAuthDialog::OnCancel()
{
	ParentWindow.Pin()->RequestDestroyWindow();

	return FReply::Handled();
}

bool SAuthDialog::IsQuitButtonEnabled() const
{
	double ElapsedTime = FSlateApplication::Get().GetCurrentTime() - StartTime;
	return ElapsedTime > WaitTime;
}

FText SAuthDialog::GetQuitButtonText() const
{
	double ElapsedTime = FSlateApplication::Get().GetCurrentTime() - StartTime;

	int MissingSeconds = FMath::RoundToInt(WaitTime - ElapsedTime);
	if (MissingSeconds > 0)
	{
		return FText::Format(LOCTEXT("CloseText", "Continue ({0} sec)"), MissingSeconds);
	}
	
	return LOCTEXT("CloseTextSimple", "Continue");
}

void SAuthDialog::OnWindowClosed(const TSharedRef<SWindow>& InWindow)
{
	
}

FReply SAuthDialog::OnOpenStore()
{
	ILauncherPlatform* LauncherPlatform = FLauncherPlatformModule::Get();

	if (LauncherPlatform != nullptr )
	{
		FOpenLauncherOptions StorePageOpen(FString(TEXT("/ue/marketplace/content/")) + PluginInfo.OfferId);
		LauncherPlatform->OpenLauncher(StorePageOpen);
	}

	return FReply::Handled();
}


#undef LOCTEXT_NAMESPACE

#endif // WITH_EDITOR
