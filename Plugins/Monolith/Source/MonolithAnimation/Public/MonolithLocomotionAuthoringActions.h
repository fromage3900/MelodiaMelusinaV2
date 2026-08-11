#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Locomotion AUTHORING actions for Monolith — registered under the existing
 * `animation` namespace (alongside the other MonolithAnimation action classes).
 *
 * 2 actions:
 *   - get_root_motion_speed : Tier-1 L2. Read the root-motion translation speed
 *                             (cm/s) of a UAnimSequence by extracting root motion
 *                             over the clip. Detects root-locked / root-motion-
 *                             disabled / zero-delta clips and returns an explicit
 *                             "speed unknowable" signal rather than reporting 0.
 *   - bake_distance_curve   : Tier-1 L3. Reflectively construct + configure a
 *                             UDistanceCurveModifier (CurveName / Axis / bStopAtEnd
 *                             / SampleRate / StopSpeedThreshold), register it into
 *                             the asset's AnimationModifiersAssetUserData stack so
 *                             it persists across save/reload, then apply it.
 *
 * Public-release safety (issue-#71 class): UDistanceCurveModifier lives in the
 * AnimationLocomotionLibrary plugin, which is EnabledByDefault:false. To avoid a
 * typed module dependency that would hard-link AnimationLocomotionLibraryEditor,
 * this class resolves the modifier UClass and its EDistanceCurve_Axis enum
 * REFLECTIVELY (FindObject / StaticClass-by-path + FProperty-by-name). No typed
 * reference to UDistanceCurveModifier / EDistanceCurve_Axis / UAnimDistanceMatching-
 * Library appears anywhere in this class, so MonolithAnimation.Build.cs needs no
 * new dependency. If the AnimationLocomotionLibrary plugin is not present, the
 * bake handler returns a clean "AnimationLocomotionLibrary not available" error.
 */
class MONOLITHANIMATION_API FMonolithLocomotionAuthoringActions
{
public:
	/** Register all locomotion-authoring actions with the tool registry. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleGetRootMotionSpeed(const TSharedPtr<FJsonObject>& Params);   // T1-L2
	static FMonolithActionResult HandleBakeDistanceCurve(const TSharedPtr<FJsonObject>& Params);     // T1-L3
};
