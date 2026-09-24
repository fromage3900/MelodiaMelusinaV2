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

#include "CoreMinimal.h"

#include <Misc/EngineVersionComparison.h>
#if PLATFORM_MAC && UE_VERSION_NEWER_THAN(4, 20, 0) /* && UE_VERSION_OLDER_THAN(5, 6, 0) */
#	define UNA_AUTHMANAGER_FPluginWardenAuthorizer_StartLauncher_Waiting_FIX_
#endif

#ifdef UNA_AUTHMANAGER_FPluginWardenAuthorizer_StartLauncher_Waiting_FIX_
	#define private public
#endif
#include "PluginWardenAuthorizer.h"	// for EPluginAuthorizationState (and forward decl of FPluginWardenAuthorizer)
									// Needed also by AuthManager.cpp to ensure the same declarations are imported when the "FIX_" is enabled
#ifdef UNA_AUTHMANAGER_FPluginWardenAuthorizer_StartLauncher_Waiting_FIX_
	#undef private
#endif



struct FUNAPluginInfo
{
	FUNAPluginInfo() = default;
	FUNAPluginInfo( const FText& InFriendlyName, const FString& InItemId, const FString& InOfferId )
		: FriendlyName( InFriendlyName )
		, ItemId( InItemId )
		, OfferId( InOfferId )
	{
	}

	FText FriendlyName;
	FString ItemId;
	FString OfferId;
};



class FUNAAuthManager
{
public:
	FUNAAuthManager(const FUNAPluginInfo & InPluginInfo, bool bAutoMode = true);
	~FUNAAuthManager();

public:

	void ExecuteChecked(TFunction<void()> AuthorizedCallback, TFunction<void()> UnauthorizedCallback) const;

private:
	const FUNAPluginInfo PluginInfo;

	FTSTicker::FDelegateHandle TickerDelegateHandle;
	TSharedPtr<FPluginWardenAuthorizer> Authorizer;
	EPluginAuthorizationState AuthorizationState;
	FString CachedAuthMethod;

private:
	void ResetCachedAuthMethod();
	bool HasValidAuthInCache() const;
	void ShowNotEntitledMessage() const;
	void OnEditorInitialized(double Duration);
	bool OnTick(float DeltaTime);
	void OnPreBeginPIE(bool);
};

#endif // WITH_EDITOR
