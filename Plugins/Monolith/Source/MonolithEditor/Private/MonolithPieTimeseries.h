#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

// Gap 9: sample_pie_timeseries registration. The action lives under the "animation"
// namespace string (verification ergonomics match sample_pie_anim_instance) but is
// IMPLEMENTED in MonolithEditor — it consumes the editor's async PIE-smoke session
// machinery (FPieSmokeSessionManager) which MonolithAnimation cannot reach. The registry
// is namespace-string-keyed (not module-keyed), so a cross-namespace registration from
// MonolithEditor is well-formed; cleanup rides on MonolithAnimation's
// UnregisterNamespace("animation") (handlers are static, so a lingering registration is
// not a use-after-free of data). The handler delegates to
// FMonolithEditorActions::StartTimeseriesSession (where the PIE-start helpers are in scope).
class FMonolithPieTimeseries
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleSamplePieTimeseries(const TSharedPtr<FJsonObject>& Params);
};
