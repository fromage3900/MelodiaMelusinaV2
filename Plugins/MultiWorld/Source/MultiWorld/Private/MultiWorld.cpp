// Copyright UNAmedia. All Rights Reserved.

#include "MultiWorld.h"

//#if WITH_EDITOR
//#	include "UNAAuth/AuthManager.h"
//#endif // WITH_EDITOR

DEFINE_LOG_CATEGORY(LogMultiWorld)

#define LOCTEXT_NAMESPACE "FMultiWorldModule"


void FMultiWorldModule::StartupModule()
{
#if WITH_EDITOR
	/*
	### LEGAL NOTICE ###
	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###

	No changes to the code below are permitted, including any changes to other code that alter its intended execution.
	Individuals and organizations making any modifications and/or users and organizations using unauthorized modifications are deemed to be in violation of the license terms.
	For any need to customize this method you can contact UNAmedia.

	### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ###
	*/
	static const FText PluginFriendlyName = LOCTEXT("FMultiWorldModule_PluginFriendlyName", "MultiWorld");
	static const FString MultiWorldPluginItemID = TEXT("841977869d9f43f99c06f151f05b4722"); // ItemID
	static const FString MultiWorldPluginOfferID = TEXT("483ac00af8284f5683b904219c4e9c45"); // OfferID
	//Authorizer = MakeShared<FUNAAuthManager>(FUNAPluginInfo(PluginFriendlyName, MultiWorldPluginItemID, MultiWorldPluginOfferID));
#endif // WITH_EDITOR
}

void FMultiWorldModule::ShutdownModule()
{
//#if WITH_EDITOR
//	Authorizer.Reset();
//#endif // WITH_EDITOR
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FMultiWorldModule, MultiWorld)