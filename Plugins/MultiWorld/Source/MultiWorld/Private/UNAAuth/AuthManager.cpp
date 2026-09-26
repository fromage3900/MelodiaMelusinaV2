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

#include "UNAAuth/AuthManager.h"

#include "UNAAuth/SAuthDialog.h"

#include "PluginWardenModule.h"
#ifdef UNA_AUTHMANAGER_FPluginWardenAuthorizer_StartLauncher_Waiting_FIX_
#	include "Application/IPortalApplicationWindow.h"
#endif
#include "Account/IPortalUser.h" // for EEntitlementCacheLevelRequest

#define UI UI_ST
THIRD_PARTY_INCLUDES_START
#include "openssl/evp.h"
#include "openssl/hmac.h"
#include "openssl/x509.h"
//#include "openssl/err.h"
THIRD_PARTY_INCLUDES_END
#undef UI



#define LOCTEXT_NAMESPACE "FUNAAuthManager"

static const FString StoreId(TEXT("UNAAuth"));
static const FString SectionName(TEXT("Cache"));


namespace FUNAAuthManager_Private
{

static const FString HMAC_TAG(TEXT("hmac"));
static const FString PKC_TAG(TEXT("pkc"));

#include "./public-key.h"

FString HMACSignString(const FString& key, const FString& msg)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/

	unsigned int hash_len = 32;
	unsigned char hash[32] = {};

	typedef TStringConversion< TStringConvert<FString::ElementType, UTF8CHAR> > FStringUtf8;
	const FStringUtf8 Utf8Key = StringCast<UTF8CHAR>(*key);
	const FStringUtf8 Utf8Msg = StringCast<UTF8CHAR>(*msg);

	HMAC_CTX* hmac = HMAC_CTX_new();
	HMAC_Init_ex(hmac, Utf8Key.Get(), Utf8Key.Length(), EVP_sha256(), nullptr);
	HMAC_Update(hmac, reinterpret_cast<const unsigned char*>(Utf8Msg.Get()), Utf8Msg.Length());
	HMAC_Final(hmac, hash, &hash_len);
	HMAC_CTX_free(hmac);

	return FBase64::Encode(hash, hash_len);
}


FString GetNamesKey(int flag)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/

	FString ComputerName = flag & 2 ? TEXT("*") : FString(FPlatformProcess::ComputerName()).Replace(TEXT(" "), TEXT(""), ESearchCase::CaseSensitive);
	if (ComputerName.IsEmpty())
	{
		ComputerName = "-";
	}
	FString UserName = flag & 1 ? TEXT("*") : FString(FPlatformProcess::UserName()).Replace(TEXT(" "), TEXT(""), ESearchCase::CaseSensitive);
	if (UserName.IsEmpty())
	{
		UserName = "-";
	}
	return FString::Printf(TEXT("%s %s"), *ComputerName, *UserName);
}



FString GetHMACKey(const FUNAPluginInfo & PluginInfo, int flag)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	return FString::Printf(TEXT("%s %s"), *PluginInfo.ItemId, *GetNamesKey(flag));
}

} // namespace FUNAAuthManager_Private


FUNAAuthManager::FUNAAuthManager(const FUNAPluginInfo & InPluginInfo, bool bAutoMode)
	: PluginInfo(InPluginInfo),
	AuthorizationState(EPluginAuthorizationState::Initializing)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	FEditorDelegates::OnEditorInitialized.AddRaw(this, &FUNAAuthManager::OnEditorInitialized);
	FTickerDelegate TickDelegate = FTickerDelegate::CreateRaw(this, &FUNAAuthManager::OnTick);
	TickerDelegateHandle = FTSTicker::GetCoreTicker().AddTicker(TickDelegate);
	if (bAutoMode)
	{
		FEditorDelegates::PreBeginPIE.AddRaw(this, &FUNAAuthManager::OnPreBeginPIE);
	}

	UE_SET_LOG_VERBOSITY(PluginWarden, Warning);
}



FUNAAuthManager::~FUNAAuthManager()
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	FTSTicker::GetCoreTicker().RemoveTicker(TickerDelegateHandle);
	FEditorDelegates::OnEditorInitialized.RemoveAll(this);
	FEditorDelegates::EndPIE.RemoveAll(this);
}



void FUNAAuthManager::ExecuteChecked(TFunction<void()> AuthorizedCallback, TFunction<void()> UnauthorizedCallback) const
{	
	check(AuthorizedCallback);

	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	if (HasValidAuthInCache())
	{
		AuthorizedCallback();
		return;
	}

	{
		const int AmountOfWork = static_cast<int>(EPluginAuthorizationState::Signin_Waiting) + 1;
		FScopedSlowTask ProgressDialog(AmountOfWork,
			LOCTEXT("EntitlementWaitingDialogTitle", "Checking entitlement..."));
		ProgressDialog.MakeDialog(true);

		while (AuthorizationState < EPluginAuthorizationState::Signin_Timeout)
		{
			if (ProgressDialog.ShouldCancel())
			{
				break;
			}

			// Engine tick isn't running when the modal window is open, so we need to tick any core tickers
			// to as that's what the RPC system uses to update the current state of RPC calls.
			FTaskGraphInterface::Get().ProcessThreadUntilIdle(ENamedThreads::GameThread);
			FTSTicker::GetCoreTicker().Tick(0.01f);

			//ProgressDialog.EnterProgressFrame(FMath::Min(static_cast<int>(AuthorizationState), AmountOfWork));
			ProgressDialog.TickProgress();

			FPlatformProcess::Sleep(0.01f);
		}
	}

	if(AuthorizationState == EPluginAuthorizationState::Authorized)
	{
		AuthorizedCallback();
	}
	else
	{
		ShowNotEntitledMessage();
		// A modal is shown, so code execution here is interrupted until the modal is closed,
		// then the UnauthorizedCallback callback is called (if any).
		// Note that currently the "Continue" button is ignored, since the AuthorizedCallback is not called.

		if (UnauthorizedCallback) 
		{
			UnauthorizedCallback();
		}
	}
}



bool FUNAAuthManager::HasValidAuthInCache() const
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	return !CachedAuthMethod.IsEmpty();
}



void FUNAAuthManager::ResetCachedAuthMethod()
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	CachedAuthMethod.Empty();

	FString SignedStr;
	if (FPlatformMisc::GetStoredValue(StoreId, SectionName, PluginInfo.ItemId, SignedStr))
	{
		TArray<FString> Tokens;
		SignedStr.ParseIntoArrayWS(Tokens);
		if (Tokens.Num() >= 1)
		{
			const FString& Format = Tokens[0];
			if (Format == FUNAAuthManager_Private::HMAC_TAG && Tokens.Num() == 4)
			{
				const FString& FlagStr = Tokens[1];
				const int32 Flag = FCString::Atoi(*FlagStr);
				const FString& DateStr = Tokens[2];
				const FString& Sign = Tokens[3];
				const FString Content = FString::Printf(TEXT("%s %s %s"), *Format, *FlagStr, *DateStr);
				if (Sign == FUNAAuthManager_Private::HMACSignString(FUNAAuthManager_Private::GetHMACKey(PluginInfo, Flag), Content))
				{
					FDateTime Date;
					if (FDateTime::ParseIso8601(*DateStr, Date))
					{
						const FTimespan tdiff = FDateTime::Now() - Date;
						if (tdiff >= -FTimespan::FromHours(2) && tdiff <= FTimespan::FromHours(72))
						{
							CachedAuthMethod = FUNAAuthManager_Private::HMAC_TAG;
							return;
						}
					}
				}
			}
			else if (Format == FUNAAuthManager_Private::PKC_TAG && Tokens.Num() == 5)
			{
				const FString& FlagStr = Tokens[1];
				const int32 Flag = FCString::Atoi(*FlagStr);
				const FString& DateFromStr = Tokens[2];
				const FString& DateToStr = Tokens[3];
				const FString& Sign = Tokens[4];
				TArray<uint8_t> SignBinary;
				FBase64::Decode(Sign, SignBinary);

				const FString ContentToSign = FString::Printf(TEXT("%s %s %s %s %s"), *Format, *FlagStr, *DateFromStr, *DateToStr, *FUNAAuthManager_Private::GetNamesKey(Flag));
				
				typedef TStringConversion< TStringConvert<FString::ElementType, UTF8CHAR> > FStringUtf8;
				const FStringUtf8 Utf8ContentToSign = StringCast<UTF8CHAR>(*ContentToSign);

				// Create an EVP_PKEY structure from the public key
				const unsigned char* p = FUNAAuthManager_Private::publicKey;
				EVP_PKEY* evp_pubkey = d2i_PUBKEY(NULL, &p, FUNAAuthManager_Private::publicKey_len);
				if (!evp_pubkey) {
					//UE_LOG(LogTemp, Error, TEXT("Error loading public key: %s"), ERR_error_string(ERR_get_error(), NULL));
					return;
				}

				// Create an EVP_MD_CTX to hold the message digest context
				EVP_MD_CTX* mdctx = EVP_MD_CTX_new();
				if (!mdctx) {
					//UE_LOG(LogTemp, Error, TEXT("Error allocating memory for EVP_MD_CTX: %s"), ERR_error_string(ERR_get_error(), NULL));
					EVP_PKEY_free(evp_pubkey);
					return;
				}

				// Initialize the signature verification context for SHA-256
				if (EVP_VerifyInit(mdctx, EVP_sha256()) != 1) {
					//UE_LOG(LogTemp, Error, TEXT("Error initializing verification: %s"), ERR_error_string(ERR_get_error(), NULL));
					EVP_MD_CTX_free(mdctx);
					EVP_PKEY_free(evp_pubkey);
					return;
				}

				// Provide the data to be verified
				if (EVP_VerifyUpdate(mdctx, Utf8ContentToSign.Get(), Utf8ContentToSign.Length()) != 1) {
					//UE_LOG(LogTemp, Error, TEXT("Error updating verification: %s"), ERR_error_string(ERR_get_error(), NULL));
					EVP_MD_CTX_free(mdctx);
					EVP_PKEY_free(evp_pubkey);
					return;
				}

				// Verify the signature
				const int result = EVP_VerifyFinal(mdctx, SignBinary.GetData(), SignBinary.Num(), evp_pubkey);
				
				// Clean up
				EVP_MD_CTX_free(mdctx);
				EVP_PKEY_free(evp_pubkey);

				if (result != 1)
				{
					//UE_LOG(LogTemp, Error, TEXT("Signature verification failed: %s"), ERR_error_string(ERR_get_error(), NULL));
					return;
				}

				FDateTime DateFrom, DateTo;
				if (FDateTime::ParseIso8601(*DateFromStr, DateFrom) && FDateTime::ParseIso8601(*DateToStr, DateTo))
				{
					const FDateTime Now = FDateTime::Now();
					if (DateFrom <= Now && Now <= DateTo)
					{
						CachedAuthMethod = FUNAAuthManager_Private::PKC_TAG;
						return;
					}
				}
			}
		}
	}
}



void FUNAAuthManager::ShowNotEntitledMessage() const
{
	TSharedRef<SWindow> AuthWindow = SNew(SWindow)
		.SupportsMaximize(false)
		.SupportsMinimize(false)
		.HasCloseButton(false)
		.SizingRule(ESizingRule::Autosized)
		.Title(FText::Format(LOCTEXT("EntitlementCheckFormat", "{0} - Entitlement Check"), PluginInfo.FriendlyName));

	TSharedRef<SAuthDialog> PluginAuthPanel = SNew(SAuthDialog, AuthWindow, AuthorizationState, PluginInfo);

	AuthWindow->SetContent(PluginAuthPanel);

	FSlateApplication::Get().AddModalWindow(AuthWindow, nullptr);
}



void FUNAAuthManager::OnEditorInitialized(double)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	ResetCachedAuthMethod();
	Authorizer = MakeShared<FPluginWardenAuthorizer>(PluginInfo.FriendlyName, PluginInfo.ItemId, PluginInfo.OfferId, EEntitlementCacheLevelRequest::Disk);
}



bool FUNAAuthManager::OnTick(float DeltaTime)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	if (!Authorizer.IsValid())
	{
		return true;
	}

	AuthorizationState = Authorizer->UpdateAuthorizationState(DeltaTime);

	static_assert(UE_VERSION_OLDER_THAN(5, 9, 0), "Verify the FPluginWardenAuthorizer implementation for the latest version of Unreal Engine, and the condition for when to apply the fix");
#ifdef UNA_AUTHMANAGER_FPluginWardenAuthorizer_StartLauncher_Waiting_FIX_
	// Keep in sync with "<UE_ROOT>\Engine\Source\Editor\PluginWarden\Private\PluginWardenAuthorizer.cpp", method FPluginWardenAuthorizer::UpdateAuthorizationState(),
	// "StartLauncher_Waiting" state, replicating the code to also include the EGL macOS process (see also "StartLauncher" state).
	if (Authorizer->CurrentState == EPluginAuthorizationState::StartLauncher_Waiting)
	{
		if (FPlatformProcess::IsApplicationRunning(TEXT("EpicGamesLauncher-Mac-Shipping")) && Authorizer->PortalWindowService->IsAvailable() && Authorizer->PortalUserService->IsAvailable())
		{
			Authorizer->CurrentState = EPluginAuthorizationState::AuthorizePlugin;
		}
	}
#endif

#if 0
#	pragma message("WARNING: simulating failed authorization")
	AuthorizationState = EPluginAuthorizationState::Signin_Timeout;
#endif

	// Temporarily cache authorization (if PKC_TAG is valid, it's preserved).
	if (AuthorizationState == EPluginAuthorizationState::Authorized && CachedAuthMethod != FUNAAuthManager_Private::PKC_TAG)
	{
		// TODO: do not write this if a valid FUNAAuthManager_Private::PKC_TAG is available
		constexpr int flag = 0;
		const FString Key = FUNAAuthManager_Private::GetHMACKey(PluginInfo, flag);
		const FString Content = FString::Printf(TEXT("%s %d %s"), *FUNAAuthManager_Private::HMAC_TAG, flag, *FDateTime::Now().ToIso8601());
		const FString ContentSign = FUNAAuthManager_Private::HMACSignString(Key, Content);
		const FString Token = FString::Printf(TEXT("%s %s"), *Content, *ContentSign);
		FPlatformMisc::SetStoredValue(StoreId, SectionName, PluginInfo.ItemId, Token);
	}

	return AuthorizationState < EPluginAuthorizationState::Signin_Timeout;
}



void FUNAAuthManager::OnPreBeginPIE(bool)
{
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	See file comment.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	if (HasValidAuthInCache())
	{
		return;
	}

	if (
		AuthorizationState >= EPluginAuthorizationState::Signin_Timeout
		&& AuthorizationState != EPluginAuthorizationState::Authorized
	)
	{
		ShowNotEntitledMessage();
	}
}



#undef LOCTEXT_NAMESPACE

#endif // WITH_EDITOR
