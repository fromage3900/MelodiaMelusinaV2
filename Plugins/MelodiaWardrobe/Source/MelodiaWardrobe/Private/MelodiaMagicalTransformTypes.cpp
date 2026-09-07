#include "MelodiaMagicalTransformTypes.h"

namespace
{
	/**
	 * Linear blend between two keys.
	 *
	 * Linear, not cubic: the keys ARE the authored easing. A spline through them
	 * would overshoot Progress past 1 between keys, and Progress drives an
	 * opacity mask -- an overshoot there is a visible hard clip on the silhouette
	 * edge rather than a soft one. Bloom is allowed to exceed 1 because it is an
	 * emissive gain, so it is the one channel where overshoot is the point, and
	 * the designer gets it by authoring a key above 1 rather than by accident.
	 */
	FMelodiaMagicalTransformPose BlendKeys(
		const FMelodiaMagicalTransformKey& A,
		const FMelodiaMagicalTransformKey& B,
		const float Alpha)
	{
		FMelodiaMagicalTransformPose Pose;
		Pose.Progress = FMath::Lerp(A.Progress, B.Progress, Alpha);
		Pose.Dissolve = FMath::Lerp(A.Dissolve, B.Dissolve, Alpha);
		Pose.Bloom = FMath::Lerp(A.Bloom, B.Bloom, Alpha);
		Pose.Sparkle = FMath::Lerp(A.Sparkle, B.Sparkle, Alpha);
		return Pose;
	}

	FMelodiaMagicalTransformPose PoseFromKey(const FMelodiaMagicalTransformKey& Key)
	{
		FMelodiaMagicalTransformPose Pose;
		Pose.Progress = Key.Progress;
		Pose.Dissolve = Key.Dissolve;
		Pose.Bloom = Key.Bloom;
		Pose.Sparkle = Key.Sparkle;
		return Pose;
	}
}

FMelodiaMagicalTransformPose FMelodiaMagicalTransformTrack::Evaluate(
	const TArray<FMelodiaMagicalTransformKey>& InKeys, const float NormalizedTime)
{
	const float Time = FMath::Clamp(NormalizedTime, 0.0f, 1.0f);

	// Unauthored track degrades to a plain linear reveal with no flourish, never
	// to nothing. A component someone forgot to author still shows the wing.
	if (InKeys.IsEmpty())
	{
		FMelodiaMagicalTransformPose Pose;
		Pose.Progress = Time;
		return Pose;
	}

	if (InKeys.Num() == 1)
	{
		return PoseFromKey(InKeys[0]);
	}

	// Sort a copy. Keys are hand-authored in the details panel, where reordering
	// an array element is fiddly, so an out-of-order key is an authoring slip and
	// not a reason to produce garbage. Sorting the caller's array instead would
	// mutate a const-by-contract input and would show up as rows jumping around
	// under the designer's cursor.
	TArray<FMelodiaMagicalTransformKey> Sorted = InKeys;
	Sorted.Sort([](const FMelodiaMagicalTransformKey& A, const FMelodiaMagicalTransformKey& B)
	{
		return A.Time < B.Time;
	});

	// Clamp outside the authored range rather than extrapolating: a track that
	// starts at 0.2 holds its first key from 0 to 0.2, which is what "the reveal
	// has not started yet" should look like.
	if (Time <= Sorted[0].Time)
	{
		return PoseFromKey(Sorted[0]);
	}
	if (Time >= Sorted.Last().Time)
	{
		return PoseFromKey(Sorted.Last());
	}

	for (int32 Index = 0; Index < Sorted.Num() - 1; ++Index)
	{
		const FMelodiaMagicalTransformKey& A = Sorted[Index];
		const FMelodiaMagicalTransformKey& B = Sorted[Index + 1];
		if (Time < A.Time || Time > B.Time)
		{
			continue;
		}

		const float Span = B.Time - A.Time;

		// Two keys authored at the same time is a legal way to express an instant
		// step. Dividing by the zero span would produce a NaN that propagates
		// straight into SetScalarParameterValue and corrupts the material for the
		// rest of the frame, so the step is taken explicitly.
		if (Span <= UE_SMALL_NUMBER)
		{
			return PoseFromKey(B);
		}

		return BlendKeys(A, B, (Time - A.Time) / Span);
	}

	return PoseFromKey(Sorted.Last());
}

FMelodiaMagicalTransformTrack FMelodiaMagicalTransformTrack::MakeDefaultRevealTrack()
{
	// Authored shape, five keys:
	//   0.00  nothing
	//   0.18  the wavefront ignites before any silhouette appears -- bloom leads,
	//         progress is still near zero, so the flare reads as the CAUSE of the
	//         wing rather than a highlight on an already-visible one
	//   0.45  widest erosion band and peak sparkle: the middle of the dissolve is
	//         where the mask edge is longest, so it is where the effect belongs
	//   0.78  progress nearly complete, flare decaying
	//   1.00  settled: full opacity, no dissolve band, no bloom, no sparkle
	FMelodiaMagicalTransformTrack Track;
	Track.Keys.Reserve(5);

	auto AddKey = [&Track](float Time, float Progress, float Dissolve, float Bloom, float Sparkle)
	{
		FMelodiaMagicalTransformKey Key;
		Key.Time = Time;
		Key.Progress = Progress;
		Key.Dissolve = Dissolve;
		Key.Bloom = Bloom;
		Key.Sparkle = Sparkle;
		Track.Keys.Add(Key);
	};

	AddKey(0.00f, 0.00f, 0.00f, 0.00f, 0.00f);
	AddKey(0.18f, 0.06f, 0.55f, 2.60f, 0.35f);
	AddKey(0.45f, 0.42f, 1.00f, 3.40f, 1.00f);
	AddKey(0.78f, 0.88f, 0.42f, 1.30f, 0.45f);
	AddKey(1.00f, 1.00f, 0.00f, 0.00f, 0.00f);

	return Track;
}
