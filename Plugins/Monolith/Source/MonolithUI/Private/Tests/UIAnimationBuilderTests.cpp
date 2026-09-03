// Copyright tumourlove. All Rights Reserved.
//
// Phase I — automation tests for FUIAnimationMovieSceneBuilder.
//
// Two tests, both exercising the editor MovieScene builder:
//   I1: MonolithUI.AnimationBuilder.MovieSceneOpacityTrack
//   I7: MonolithUI.AnimationBuilder.PreserveNamedSurvivesRebuild
//
// The original I4 (FUIAnimationRuntimeDriver.FadeInPlays) belongs with the
// optional runtime provider, not MonolithUI.
//
// Test-fixture WBPs land under /Game/Tests/Monolith/UI/ per the throwaway-asset rule.
#if WITH_DEV_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"

// Fixture utilities (Phase D / hoisted-tests baseline).
#include "Tests/Hoisted/MonolithUITestFixtureUtils.h"

// Phase I subjects
#include "Animation/UIAnimationMovieSceneBuilder.h"
#include "Animation/UISpecAnimation.h"
#include "Spec/UISpec.h"

// MovieScene introspection
#include "Animation/WidgetAnimation.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "Channels/MovieSceneCurveChannelCommon.h"

// Widget Blueprint introspection
#include "WidgetBlueprint.h"

namespace MonolithUI::AnimationBuilderTests
{
    static const FString GAssetPath_MovieScene =
        TEXT("/Game/Tests/Monolith/UI/WBP_AnimBuilder_MovieScene");
    static const FString GAssetPath_Preserve   =
        TEXT("/Game/Tests/Monolith/UI/WBP_AnimBuilder_Preserve");

    /**
     * Build a 1-animation FUISpecDocument that ramps RenderOpacity 0 -> 1 over
     * Duration seconds on a child widget named "MyImage".
     */
    static FUISpecDocument MakeFadeInDocument(float Duration, FName AnimName = FName(TEXT("FadeIn")))
    {
        FUISpecDocument Doc;
        Doc.Version = 1;
        Doc.Name = TEXT("Test");

        FUISpecAnimation Anim;
        Anim.Name = AnimName;
        Anim.TargetWidgetId = FName(TEXT("MyImage"));
        Anim.TargetProperty = FName(TEXT("RenderOpacity"));
        Anim.Duration = Duration;
        Anim.Easing = FName(TEXT("Linear"));

        FUISpecKeyframe K0;
        K0.Time = 0.f;
        K0.ScalarValue = 0.f;
        K0.Easing = FName(TEXT("Linear"));

        FUISpecKeyframe K1;
        K1.Time = Duration;
        K1.ScalarValue = 1.f;
        K1.Easing = FName(TEXT("Linear"));

        Anim.Keyframes.Add(K0);
        Anim.Keyframes.Add(K1);

        Doc.Animations.Add(Anim);
        return Doc;
    }

    /** Find a UWidgetAnimation on the WBP by display label. */
    static UWidgetAnimation* FindAnim(UWidgetBlueprint* WBP, const FString& Label)
    {
#if WITH_EDITORONLY_DATA
        if (!WBP)
        {
            return nullptr;
        }
        for (UWidgetAnimation* Anim : WBP->Animations)
        {
            if (Anim && Anim->GetDisplayLabel() == Label)
            {
                return Anim;
            }
        }
#endif
        return nullptr;
    }

    /** Find the first float track on the supplied animation matching PropertyName. */
    static UMovieSceneFloatTrack* FindFloatTrack(UWidgetAnimation* WidgetAnim, FName PropertyName)
    {
        if (!WidgetAnim || !WidgetAnim->MovieScene)
        {
            return nullptr;
        }

        const UMovieScene* Scene = WidgetAnim->MovieScene;
        for (const FMovieSceneBinding& Binding : Scene->GetBindings())
        {
            UMovieSceneFloatTrack* FloatTrack = WidgetAnim->MovieScene->FindTrack<UMovieSceneFloatTrack>(
                Binding.GetObjectGuid(), PropertyName);
            if (FloatTrack)
            {
                return FloatTrack;
            }
        }
        return nullptr;
    }
} // namespace MonolithUI::AnimationBuilderTests


// -----------------------------------------------------------------------------
// I1: FUIAnimationMovieSceneBuilder::Build produces a UWidgetAnimation with a
//     float track on RenderOpacity.
// -----------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAnimationBuilderMovieSceneOpacityTrackTest,
    "MonolithUI.AnimationBuilder.MovieSceneOpacityTrack",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAnimationBuilderMovieSceneOpacityTrackTest::RunTest(const FString& Parameters)
{
    using namespace MonolithUI::AnimationBuilderTests;
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(GAssetPath_MovieScene, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *GAssetPath_MovieScene);
    TestNotNull(TEXT("WBP loaded"), WBP);
    if (!WBP)
    {
        return false;
    }

    const FUISpecDocument Doc = MakeFadeInDocument(0.5f);
    FUIAnimationBuildOptions Options;
    // Compile is a slow step in a test loop; rely on FBlueprintEditorUtils
    // structural-modify happening downstream. Keep the default true to mirror
    // the production path the LLM-driven harness exercises.
    Options.bCompileBlueprint = true;

    const FUIAnimationRebuildResult Result = FUIAnimationMovieSceneBuilder::Build(Doc, WBP, Options);

    TestTrue(TEXT("Build succeeded"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Builder error: %s"), *Result.ErrorMessage));
        return false;
    }
    TestEqual(TEXT("AnimationsCreated == 1"), Result.AnimationsCreated, 1);
    TestEqual(TEXT("AnimationsRecreated == 0"), Result.AnimationsRecreated, 0);
    TestEqual(TEXT("AnimationsPreserved == 0"), Result.AnimationsPreserved, 0);
    TestEqual(TEXT("TracksCreated == 1"), Result.TracksCreated, 1);
    TestEqual(TEXT("KeysInserted == 2"), Result.KeysInserted, 2);

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* Anim = FindAnim(WBP, TEXT("FadeIn"));
    TestNotNull(TEXT("FadeIn animation present on WBP"), Anim);
    if (!Anim)
    {
        return false;
    }
    TestNotNull(TEXT("MovieScene allocated"), Anim->MovieScene.Get());
    if (!Anim->MovieScene)
    {
        return false;
    }

    UMovieSceneFloatTrack* FloatTrack = FindFloatTrack(Anim, FName(TEXT("RenderOpacity")));
    TestNotNull(TEXT("RenderOpacity float track present"), FloatTrack);
    if (!FloatTrack)
    {
        return false;
    }

    TestTrue(TEXT("Track has at least 1 section"), FloatTrack->GetAllSections().Num() > 0);
    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(FloatTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Float section is castable"), Section);
    if (!Section)
    {
        return false;
    }

    const FMovieSceneFloatChannel& Channel = Section->GetChannel();
    TestEqual(TEXT("Channel has 2 keys"), Channel.GetNumKeys(), 2);

    TArrayView<const FMovieSceneFloatValue> Values = Channel.GetValues();
    if (Values.Num() >= 2)
    {
        TestNearlyEqual(TEXT("Key 0 value ~ 0.0"), Values[0].Value, 0.0f, 0.01f);
        TestNearlyEqual(TEXT("Key 1 value ~ 1.0"), Values[1].Value, 1.0f, 0.01f);
    }
#endif

    return true;
}


// -----------------------------------------------------------------------------
// I7: PreserveAnimationsNamed:["X"] on rebuild keeps the existing X animation
//     untouched.
// -----------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAnimationBuilderPreserveNamedSurvivesRebuildTest,
    "MonolithUI.AnimationBuilder.PreserveNamedSurvivesRebuild",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAnimationBuilderPreserveNamedSurvivesRebuildTest::RunTest(const FString& Parameters)
{
    using namespace MonolithUI::AnimationBuilderTests;
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(GAssetPath_Preserve, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *GAssetPath_Preserve);
    TestNotNull(TEXT("WBP loaded"), WBP);
    if (!WBP)
    {
        return false;
    }

    // Pass 1 — author "Preserved" with a 0.5s linear 0->1 ramp.
    {
        const FUISpecDocument Doc1 = MakeFadeInDocument(0.5f, FName(TEXT("Preserved")));
        FUIAnimationBuildOptions Options;
        const FUIAnimationRebuildResult R1 = FUIAnimationMovieSceneBuilder::Build(Doc1, WBP, Options);
        TestTrue(TEXT("Pass 1 succeeded"), R1.bSuccess);
        TestEqual(TEXT("Pass 1: AnimationsCreated == 1"), R1.AnimationsCreated, 1);
        TestEqual(TEXT("Pass 1: AnimationsPreserved == 0"), R1.AnimationsPreserved, 0);
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* OriginalAnim = FindAnim(WBP, TEXT("Preserved"));
    TestNotNull(TEXT("Preserved animation present after pass 1"), OriginalAnim);
    if (!OriginalAnim)
    {
        return false;
    }

    UMovieSceneFloatTrack* OriginalTrack = FindFloatTrack(OriginalAnim, FName(TEXT("RenderOpacity")));
    TestNotNull(TEXT("Original RenderOpacity track present"), OriginalTrack);
    if (!OriginalTrack)
    {
        return false;
    }
    UMovieSceneFloatSection* OriginalSection = Cast<UMovieSceneFloatSection>(OriginalTrack->GetAllSections()[0]);
    const int32 OriginalKeyCount = OriginalSection ? OriginalSection->GetChannel().GetNumKeys() : -1;
    const FName OriginalAnimFName = OriginalAnim->GetFName();
    // Pointer-identity snapshot — RemoveExistingAnimation renames the existing
    // UObject out to the transient package and FindOrCreate constructs a fresh
    // instance, so the raw pointer is the load-bearing recreate detector. (FName
    // alone is not enough — both old and new claim the same FName.)
    const UWidgetAnimation* OriginalAnimPtr = OriginalAnim;
    const TRange<FFrameNumber> OriginalPlaybackRange = OriginalAnim->MovieScene
        ? OriginalAnim->MovieScene->GetPlaybackRange()
        : TRange<FFrameNumber>::Empty();
#endif

    // Pass 2 — same name in the spec, but listed in PreserveAnimationsNamed.
    // Spec carries a 5.0s ramp; if the preserve actually worked, the WBP's
    // animation MUST still hold the 0.5s 0->1 keys (and the same UObject identity).
    {
        const FUISpecDocument Doc2 = MakeFadeInDocument(5.0f, FName(TEXT("Preserved")));
        FUIAnimationBuildOptions Options;
        Options.PreserveAnimationsNamed.Add(FName(TEXT("Preserved")));
        const FUIAnimationRebuildResult R2 = FUIAnimationMovieSceneBuilder::Build(Doc2, WBP, Options);
        TestTrue(TEXT("Pass 2 succeeded"), R2.bSuccess);
        TestEqual(TEXT("Pass 2: AnimationsCreated == 0"), R2.AnimationsCreated, 0);
        TestEqual(TEXT("Pass 2: AnimationsRecreated == 0"), R2.AnimationsRecreated, 0);
        TestEqual(TEXT("Pass 2: AnimationsPreserved == 1"), R2.AnimationsPreserved, 1);
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* SurvivingAnim = FindAnim(WBP, TEXT("Preserved"));
    TestNotNull(TEXT("Preserved animation still present after pass 2"), SurvivingAnim);
    if (!SurvivingAnim)
    {
        return false;
    }

    // Identity check — same UObject pointer means we never destroyed and rebuilt.
    // (Pointer comparison, not FName: both OldAnim and NewAnim would claim the
    // same FName since FindOrCreate uses FName(*AnimName); only the raw pointer
    // proves no rename-out + reconstruct occurred.)
    TestTrue(TEXT("UObject pointer identity preserved across pass 2"),
             SurvivingAnim == OriginalAnimPtr);
    TestEqual(TEXT("FName matches snapshot (sanity)"),
              SurvivingAnim->GetFName(), OriginalAnimFName);

    // Playback range identity — pass 2 spec asked for 5.0s; if preserve worked,
    // the range still matches the pass-1 0.5s value.
    if (SurvivingAnim->MovieScene)
    {
        const TRange<FFrameNumber> SurvivingRange = SurvivingAnim->MovieScene->GetPlaybackRange();
        TestTrue(TEXT("Playback range unchanged across preserve pass"),
                 SurvivingRange == OriginalPlaybackRange);
    }

    UMovieSceneFloatTrack* SurvivingTrack = FindFloatTrack(SurvivingAnim, FName(TEXT("RenderOpacity")));
    TestNotNull(TEXT("Surviving RenderOpacity track present"), SurvivingTrack);
    if (!SurvivingTrack)
    {
        return false;
    }
    UMovieSceneFloatSection* SurvivingSection = Cast<UMovieSceneFloatSection>(SurvivingTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Surviving section present"), SurvivingSection);
    if (!SurvivingSection)
    {
        return false;
    }
    const int32 SurvivingKeyCount = SurvivingSection->GetChannel().GetNumKeys();
    TestEqual(TEXT("Key count unchanged across preserve pass"),
              SurvivingKeyCount, OriginalKeyCount);
#endif

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
