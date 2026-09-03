#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASCueActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 2: Cue CRUD
	static FMonolithActionResult HandleCreateGameplayCueNotify(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleLinkCueToEffect(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleUnlinkCueFromEffect(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Cue Productivity
	static FMonolithActionResult HandleGetCueInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListGameplayCues(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetCueParameters(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindCueTriggers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateCueCoverage(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchCreateCues(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldCueLibrary(const TSharedPtr<FJsonObject>& Params);
};
