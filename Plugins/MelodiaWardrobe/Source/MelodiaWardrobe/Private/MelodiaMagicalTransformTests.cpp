// Automation coverage for the Magical Transform reveal.
//
// These target the two places this feature can break WITHOUT SAYING ANYTHING.
// A material parameter write to a name the material does not expose is not an
// error, and neither is a transition that never advances -- both look like "the
// artist has not authored it yet". So the curve evaluator and the phase machine
// are asserted directly rather than inferred from a rendered result.
//
// Deliberately world-free. The evaluator is a static pure function and the phase
// machine needs no owner, so these run without a level, a pawn, or a material.
// That keeps them fast and keeps them from failing for reasons unrelated to the
// logic under test.

#if WITH_DEV_AUTOMATION_TESTS

#include "MelodiaMagicalTransformComponent.h"
#include "MelodiaMagicalTransformTypes.h"
#include "MelodiaTraversalComponent.h"
#include "Misc/AutomationTest.h"
#include "UObject/Package.h"

// ── Keyframe evaluator ───────────────────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaMagicalTransformCurveTest,
	"Melodia.Wardrobe.MagicalTransform.Curve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaMagicalTransformCurveTest::RunTest(const FString& Parameters)
{
	using FTrack = FMelodiaMagicalTransformTrack;
	using FKey = FMelodiaMagicalTransformKey;

	// An unauthored track must still reveal. Failing to nothing here would mean a
	// forgotten curve silently costs the whole feature.
	{
		const TArray<FKey> Empty;
		TestEqual(TEXT("Empty track is a linear ramp at t=0"),
			FTrack::Evaluate(Empty, 0.0f).Progress, 0.0f);
		TestEqual(TEXT("Empty track is a linear ramp at t=0.5"),
			FTrack::Evaluate(Empty, 0.5f).Progress, 0.5f);
		TestEqual(TEXT("Empty track is a linear ramp at t=1"),
			FTrack::Evaluate(Empty, 1.0f).Progress, 1.0f);
	}

	// Out-of-range time clamps instead of extrapolating. Extrapolation would push
	// Progress past 1 and hard-clip the silhouette edge.
	{
		TArray<FKey> Keys;
		FKey A; A.Time = 0.0f; A.Progress = 0.0f; Keys.Add(A);
		FKey B; B.Time = 1.0f; B.Progress = 1.0f; Keys.Add(B);

		TestEqual(TEXT("Negative time clamps to the first key"),
			FTrack::Evaluate(Keys, -5.0f).Progress, 0.0f);
		TestEqual(TEXT("Time above 1 clamps to the last key"),
			FTrack::Evaluate(Keys, 9.0f).Progress, 1.0f);
		TestTrue(TEXT("Midpoint interpolates linearly"),
			FMath::IsNearlyEqual(FTrack::Evaluate(Keys, 0.25f).Progress, 0.25f, 1e-4f));
	}

	// A single key is a constant hold, not a divide by zero.
	{
		TArray<FKey> Keys;
		FKey Only; Only.Time = 0.5f; Only.Progress = 0.7f; Only.Bloom = 2.0f; Keys.Add(Only);
		TestEqual(TEXT("Single key holds its progress at t=0"),
			FTrack::Evaluate(Keys, 0.0f).Progress, 0.7f);
		TestEqual(TEXT("Single key holds its bloom at t=1"),
			FTrack::Evaluate(Keys, 1.0f).Bloom, 2.0f);
	}

	// Keys authored out of order are an authoring slip, not a reason to produce
	// garbage: reordering array rows in the details panel is genuinely awkward.
	{
		TArray<FKey> Keys;
		FKey Late; Late.Time = 1.0f; Late.Progress = 1.0f; Keys.Add(Late);
		FKey Early; Early.Time = 0.0f; Early.Progress = 0.0f; Keys.Add(Early);

		TestEqual(TEXT("Unsorted keys still evaluate the start correctly"),
			FTrack::Evaluate(Keys, 0.0f).Progress, 0.0f);
		TestTrue(TEXT("Unsorted keys still interpolate correctly"),
			FMath::IsNearlyEqual(FTrack::Evaluate(Keys, 0.5f).Progress, 0.5f, 1e-4f));
	}

	// Two keys at the same time is a legal instant step. The zero span must not
	// divide: a NaN here propagates into the opacity mask and corrupts the slot.
	{
		TArray<FKey> Keys;
		FKey A; A.Time = 0.0f; A.Progress = 0.0f; Keys.Add(A);
		FKey B; B.Time = 0.5f; B.Progress = 0.2f; Keys.Add(B);
		FKey C; C.Time = 0.5f; C.Progress = 0.9f; Keys.Add(C);
		FKey D; D.Time = 1.0f; D.Progress = 1.0f; Keys.Add(D);

		const FMelodiaMagicalTransformPose Pose = FTrack::Evaluate(Keys, 0.5f);
		TestFalse(TEXT("Coincident keys do not produce NaN"), FMath::IsNaN(Pose.Progress));
		TestTrue(TEXT("Coincident keys step to the later value"),
			FMath::IsNearlyEqual(Pose.Progress, 0.9f, 1e-4f));
	}

	// The shipped default shape has to actually start concealed and end revealed,
	// or the reveal is visible before the unlock and never completes after it.
	{
		const FTrack Default = FTrack::MakeDefaultRevealTrack();
		TestTrue(TEXT("Default track has authored keys"), Default.Keys.Num() > 1);

		const FMelodiaMagicalTransformPose Start = Default.Evaluate(0.0f);
		const FMelodiaMagicalTransformPose End = Default.Evaluate(1.0f);

		TestEqual(TEXT("Default track starts fully concealed"), Start.Progress, 0.0f);
		TestEqual(TEXT("Default track ends fully revealed"), End.Progress, 1.0f);

		// The settled pose must have no flourish left. A residual bloom or
		// dissolve band would leave the wings permanently shimmering.
		TestEqual(TEXT("Default track settles with no dissolve band"), End.Dissolve, 0.0f);
		TestEqual(TEXT("Default track settles with no bloom"), End.Bloom, 0.0f);
		TestEqual(TEXT("Default track settles with no sparkle"), End.Sparkle, 0.0f);

		// Bloom leads progress: the wavefront should ignite before any silhouette
		// appears, so the flare reads as the cause of the wing rather than a
		// highlight on one that is already there.
		const FMelodiaMagicalTransformPose Early = Default.Evaluate(0.18f);
		TestTrue(TEXT("Bloom leads progress early in the reveal"),
			Early.Bloom > Early.Progress);

		// Progress must never regress, or the wing would flicker mid-reveal.
		float Previous = -1.0f;
		bool bMonotonic = true;
		for (int32 Step = 0; Step <= 20; ++Step)
		{
			const float Sample = Default.Evaluate(Step / 20.0f).Progress;
			bMonotonic &= (Sample >= Previous - 1e-4f);
			Previous = Sample;
		}
		TestTrue(TEXT("Default track progress is monotonic non-decreasing"), bMonotonic);
	}

	return true;
}

// ── Phase state machine ──────────────────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaMagicalTransformPhaseTest,
	"Melodia.Wardrobe.MagicalTransform.Phase",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaMagicalTransformPhaseTest::RunTest(const FString& Parameters)
{
	UMelodiaMagicalTransformComponent* Transform =
		NewObject<UMelodiaMagicalTransformComponent>(GetTransientPackage());
	if (!Transform)
	{
		TestFalse(TEXT("Could not construct the transform component"), true);
		return false;
	}

	// No owner and no claimed materials: every write is a no-op, which is exactly
	// the state the phase machine has to survive without crashing.
	TestEqual(TEXT("Starts dormant"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Dormant);
	TestEqual(TEXT("Starts with zero progress (zero-safe default)"),
		Transform->GetProgress(), 0.0f);
	TestEqual(TEXT("Claims nothing without an owner"),
		Transform->GetClaimedMaterialCount(), 0);

	Transform->RevealDurationSeconds = 1.0f;
	Transform->ConcealDurationSeconds = 1.0f;

	// Reveal enters the animating phase but must not jump to the end.
	Transform->PlayReveal();
	TestEqual(TEXT("PlayReveal enters Revealing"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Revealing);
	TestTrue(TEXT("Revealing reports as transitioning"), Transform->IsTransitioning());

	// Re-entrancy: a second call must not restart the transition.
	Transform->TickComponent(0.5f, LEVELTICK_All, nullptr);
	const float MidProgress = Transform->GetProgress();
	Transform->PlayReveal();
	TestEqual(TEXT("PlayReveal while revealing does not restart"),
		Transform->GetProgress(), MidProgress);
	TestTrue(TEXT("Progress advanced past zero by mid-transition"), MidProgress > 0.0f);
	TestTrue(TEXT("Progress has not completed at the halfway tick"), MidProgress < 1.0f);

	// Completion is exact, not asymptotic.
	Transform->TickComponent(0.6f, LEVELTICK_All, nullptr);
	TestEqual(TEXT("Reveal completes into Revealed"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Revealed);
	TestEqual(TEXT("Revealed holds full progress"), Transform->GetProgress(), 1.0f);
	TestTrue(TEXT("Revealed reports IsRevealed"), Transform->IsRevealed());
	TestFalse(TEXT("Revealed is not transitioning"), Transform->IsTransitioning());

	// Overshooting ticks must not push progress past 1.
	Transform->TickComponent(10.0f, LEVELTICK_All, nullptr);
	TestEqual(TEXT("Extra ticks do not overshoot progress"), Transform->GetProgress(), 1.0f);

	// Conceal runs the clock back down.
	Transform->PlayConceal();
	TestEqual(TEXT("PlayConceal enters Concealing"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Concealing);
	Transform->TickComponent(0.4f, LEVELTICK_All, nullptr);
	const float ConcealProgress = Transform->GetProgress();
	TestTrue(TEXT("Conceal reduces progress"), ConcealProgress < 1.0f);

	// Reversal resumes from where it was rather than snapping back to the end.
	// A fast unequip/re-equip has to look continuous.
	Transform->PlayReveal();
	TestEqual(TEXT("Reversal re-enters Revealing"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Revealing);
	TestTrue(TEXT("Reversal resumes from the interrupted progress, not from 1"),
		FMath::IsNearlyEqual(Transform->GetProgress(), ConcealProgress, 1e-3f));

	// Conceal all the way down returns to the zero-safe dormant state.
	Transform->PlayConceal();
	Transform->TickComponent(5.0f, LEVELTICK_All, nullptr);
	TestEqual(TEXT("Conceal completes into Dormant"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Dormant);
	TestEqual(TEXT("Dormant holds zero progress"), Transform->GetProgress(), 0.0f);

	// Snap is the save-restore path: no animation, immediate steady state.
	Transform->SnapToPhase(EMelodiaMagicalTransformPhase::Revealed);
	TestEqual(TEXT("SnapToPhase(Revealed) is immediate"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Revealed);
	TestEqual(TEXT("SnapToPhase(Revealed) holds full progress"),
		Transform->GetProgress(), 1.0f);
	TestFalse(TEXT("SnapToPhase does not leave the component transitioning"),
		Transform->IsTransitioning());

	Transform->SnapToPhase(EMelodiaMagicalTransformPhase::Dormant);
	TestEqual(TEXT("SnapToPhase(Dormant) is immediate"),
		Transform->GetPhase(), EMelodiaMagicalTransformPhase::Dormant);
	TestEqual(TEXT("SnapToPhase(Dormant) holds zero progress"),
		Transform->GetProgress(), 0.0f);

	return true;
}

// ── Wing-opacity ownership handshake ─────────────────────────────────────────

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaMagicalTransformWingOwnershipTest,
	"Melodia.Wardrobe.MagicalTransform.WingOwnership",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMelodiaMagicalTransformWingOwnershipTest::RunTest(const FString& Parameters)
{
	// The handshake is what stops UMelodiaTraversalComponent's binary 0/1 write to
	// the same `Opacity` scalar from erasing an in-flight reveal on the first
	// landing. It is a one-line early return, so the thing worth locking down is
	// the contract: default unclaimed, claimable, releasable.
	UMelodiaTraversalComponent* Traversal =
		NewObject<UMelodiaTraversalComponent>(GetTransientPackage());
	if (!Traversal)
	{
		TestFalse(TEXT("Could not construct the traversal component"), true);
		return false;
	}

	TestFalse(TEXT("Wing presentation is self-owned by default"),
		Traversal->IsWingPresentationOwnedExternally());

	Traversal->SetWingPresentationOwnedExternally(true);
	TestTrue(TEXT("Wing presentation can be claimed"),
		Traversal->IsWingPresentationOwnedExternally());

	// Idempotent: a second claim is not an error and must not toggle state.
	Traversal->SetWingPresentationOwnedExternally(true);
	TestTrue(TEXT("Claiming twice stays claimed"),
		Traversal->IsWingPresentationOwnedExternally());

	// Release must return control, or tearing the transform component off a pawn
	// leaves nothing driving the wings at all.
	Traversal->SetWingPresentationOwnedExternally(false);
	TestFalse(TEXT("Wing presentation can be released"),
		Traversal->IsWingPresentationOwnedExternally());

	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
