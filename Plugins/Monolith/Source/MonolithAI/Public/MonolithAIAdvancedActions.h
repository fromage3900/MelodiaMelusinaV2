#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIAdvancedActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

#if WITH_MASSENTITY
private:
	static FMonolithActionResult HandleListMassEntityConfigs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMassEntityConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateMassEntityConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddMassTrait(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveMassTrait(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListMassTraits(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListMassProcessors(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateMassEntityConfig(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMassEntityStats(const TSharedPtr<FJsonObject>& Params);

#if WITH_ZONEGRAPH
	static FMonolithActionResult HandleListZoneGraphs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleQueryZoneLanes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetZoneLaneInfo(const TSharedPtr<FJsonObject>& Params);
#endif // WITH_ZONEGRAPH

#endif // WITH_MASSENTITY
};
