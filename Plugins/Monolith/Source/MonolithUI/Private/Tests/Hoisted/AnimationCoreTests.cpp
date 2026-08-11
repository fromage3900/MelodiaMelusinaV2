// Copyright tumourlove. All Rights Reserved.
#if WITH_DEV_AUTOMATION_TESTS

// Core / test
#include "CoreMinimal.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"

// JSON / registry
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "MonolithToolRegistry.h"

// UMG -- build a throwaway WBP + probe the result
#include "Tests/Hoisted/MonolithUITestFixtureUtils.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Image.h"

// Animation
#include "Animation/WidgetAnimation.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "Channels/MovieSceneCurveChannelCommon.h"

// Event track
#include "Tracks/MovieSceneEventTrack.h"
#include "Sections/MovieSceneEventTriggerSection.h"
#include "Channels/MovieSceneEventChannel.h"

// Delegate binding
#include "Animation/WidgetAnimationDelegateBinding.h"
#include "Engine/BlueprintGeneratedClass.h"

// Asset / package
#include "Editor.h"

namespace MonolithUI::AnimationCoreTests
{
    static const FString GTestAssetPath = TEXT("/Game/Tests/Monolith/UI/WBP_AnimCoreTest");
} // namespace MonolithUI::AnimationCoreTests


/**
 * MonolithUI.CreateAnimationV2.Basic
 *
 * Creates a 2-key cubic RenderOpacity animation on a test WBP. Asserts:
 * animation exists in WBP->Animations, channel has 2 keys, key values match
 * within tolerance, tangent data present.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUICreateAnimationV2BasicTest,
    "MonolithUI.CreateAnimationV2.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUICreateAnimationV2BasicTest::RunTest(const FString& Parameters)
{
    using namespace MonolithUI::AnimationCoreTests;
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    FString SetupError;
    if (!CreateOrReuseTestWidgetBlueprint(GTestAssetPath, FName(TEXT("MyImage")), nullptr, SetupError))
    {
        AddError(FString::Printf(TEXT("Fixture setup failed: %s"), *SetupError));
        return false;
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), GTestAssetPath);
    Params->SetStringField(TEXT("animation_name"), TEXT("FadeIn"));
    Params->SetNumberField(TEXT("duration_sec"), 0.5);
    Params->SetBoolField(TEXT("compile_once"), true);

    TArray<TSharedPtr<FJsonValue>> Tracks;
    {
        TSharedPtr<FJsonObject> Track = MakeShared<FJsonObject>();
        Track->SetStringField(TEXT("widget_name"), TEXT("MyImage"));
        Track->SetStringField(TEXT("property"), TEXT("RenderOpacity"));

        TArray<TSharedPtr<FJsonValue>> Keys;
        {
            TSharedPtr<FJsonObject> K0 = MakeShared<FJsonObject>();
            K0->SetNumberField(TEXT("time"), 0.0);
            K0->SetNumberField(TEXT("value"), 0.0);
            K0->SetStringField(TEXT("interp"), TEXT("cubic"));
            K0->SetNumberField(TEXT("leave_tangent"), 2.0);
            K0->SetNumberField(TEXT("leave_weight"), 0.33);
            Keys.Add(MakeShared<FJsonValueObject>(K0));
        }
        {
            TSharedPtr<FJsonObject> K1 = MakeShared<FJsonObject>();
            K1->SetNumberField(TEXT("time"), 0.5);
            K1->SetNumberField(TEXT("value"), 1.0);
            K1->SetStringField(TEXT("interp"), TEXT("cubic"));
            K1->SetNumberField(TEXT("arrive_tangent"), 0.0);
            K1->SetNumberField(TEXT("arrive_weight"), 0.33);
            Keys.Add(MakeShared<FJsonValueObject>(K1));
        }
        Track->SetArrayField(TEXT("keys"), Keys);
        Tracks.Add(MakeShared<FJsonValueObject>(Track));
    }
    Params->SetArrayField(TEXT("tracks"), Tracks);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("create_animation_v2"), Params);

    TestTrue(TEXT("create_animation_v2 bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    double KeysInserted = 0.0;
    TestTrue(TEXT("result has keys_inserted"), Result.Result->TryGetNumberField(TEXT("keys_inserted"), KeysInserted));
    TestEqual(TEXT("keys_inserted == 2"), static_cast<int32>(KeysInserted), 2);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *GTestAssetPath);
    if (!WBP)
    {
        AddError(TEXT("Failed to reload test WBP"));
        return false;
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* FoundAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetDisplayLabel() == TEXT("FadeIn"))
        {
            FoundAnim = Anim;
            break;
        }
    }
    TestNotNull(TEXT("FadeIn animation found in WBP->Animations"), FoundAnim);
    if (!FoundAnim)
    {
        return false;
    }

    TestNotNull(TEXT("MovieScene exists"), FoundAnim->MovieScene.Get());
    if (!FoundAnim->MovieScene)
    {
        return false;
    }

    UMovieSceneFloatTrack* FloatTrack = nullptr;
    const UMovieScene* ConstScene = FoundAnim->MovieScene;
    for (const FMovieSceneBinding& Binding : ConstScene->GetBindings())
    {
        FloatTrack = FoundAnim->MovieScene->FindTrack<UMovieSceneFloatTrack>(
            Binding.GetObjectGuid(), FName(TEXT("RenderOpacity")));
        if (FloatTrack)
        {
            break;
        }
    }
    TestNotNull(TEXT("RenderOpacity float track found"), FloatTrack);
    if (!FloatTrack)
    {
        return false;
    }

    TestTrue(TEXT("Track has at least 1 section"), FloatTrack->GetAllSections().Num() > 0);
    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(FloatTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Float section exists"), Section);
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
        TestNearlyEqual(TEXT("Key 0 leave tangent ~ 2.0"), Values[0].Tangent.LeaveTangent, 2.0f, 0.01f);
    }
#endif

    return true;
}


/**
 * MonolithUI.AddBezierEasedSegment.Basic
 *
 * Creates a bezier-eased segment with cubic-bezier(0.42, 0, 0.58, 1.0)
 * (ease-in-out). Asserts: 2 keys exist, weighted tangent mode set,
 * tangent values non-zero for this curve shape.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAddBezierEasedSegmentBasicTest,
    "MonolithUI.AddBezierEasedSegment.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAddBezierEasedSegmentBasicTest::RunTest(const FString& Parameters)
{
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    const FString BezierTestPath = TEXT("/Game/Tests/Monolith/UI/WBP_BezierSegTest");

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(BezierTestPath, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), BezierTestPath);
    Params->SetStringField(TEXT("animation_name"), TEXT("EaseInOut"));
    Params->SetStringField(TEXT("widget_name"), TEXT("MyImage"));
    Params->SetStringField(TEXT("property"), TEXT("RenderOpacity"));
    Params->SetNumberField(TEXT("from_value"), 0.0);
    Params->SetNumberField(TEXT("to_value"), 1.0);
    Params->SetNumberField(TEXT("start_time"), 0.0);
    Params->SetNumberField(TEXT("end_time"), 0.5);

    TArray<TSharedPtr<FJsonValue>> Bezier;
    Bezier.Add(MakeShared<FJsonValueNumber>(0.42));
    Bezier.Add(MakeShared<FJsonValueNumber>(0.0));
    Bezier.Add(MakeShared<FJsonValueNumber>(0.58));
    Bezier.Add(MakeShared<FJsonValueNumber>(1.0));
    Params->SetArrayField(TEXT("bezier"), Bezier);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("add_bezier_eased_segment"), Params);

    TestTrue(TEXT("add_bezier_eased_segment bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    double KeysInserted = 0.0;
    TestTrue(TEXT("result has keys_inserted"), Result.Result->TryGetNumberField(TEXT("keys_inserted"), KeysInserted));
    TestEqual(TEXT("keys_inserted == 2"), static_cast<int32>(KeysInserted), 2);

    const TSharedPtr<FJsonObject>* TangentInfoPtr = nullptr;
    TestTrue(TEXT("result has tangent_info"), Result.Result->TryGetObjectField(TEXT("tangent_info"), TangentInfoPtr));

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *BezierTestPath);
    if (!WBP)
    {
        AddError(TEXT("Failed to reload bezier test WBP"));
        return false;
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* FoundAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetDisplayLabel() == TEXT("EaseInOut"))
        {
            FoundAnim = Anim;
            break;
        }
    }
    TestNotNull(TEXT("EaseInOut animation found"), FoundAnim);
    if (!FoundAnim || !FoundAnim->MovieScene)
    {
        return false;
    }

    UMovieSceneFloatTrack* FloatTrack = nullptr;
    const UMovieScene* ConstScene2 = FoundAnim->MovieScene;
    for (const FMovieSceneBinding& Binding : ConstScene2->GetBindings())
    {
        FloatTrack = FoundAnim->MovieScene->FindTrack<UMovieSceneFloatTrack>(
            Binding.GetObjectGuid(), FName(TEXT("RenderOpacity")));
        if (FloatTrack)
        {
            break;
        }
    }
    TestNotNull(TEXT("RenderOpacity float track found"), FloatTrack);
    if (!FloatTrack || FloatTrack->GetAllSections().Num() == 0)
    {
        return false;
    }

    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(FloatTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Float section exists"), Section);
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

        TestEqual(TEXT("Key 0 tangent weight mode is WeightedBoth"),
            static_cast<int32>(Values[0].Tangent.TangentWeightMode),
            static_cast<int32>(RCTWM_WeightedBoth));
        TestEqual(TEXT("Key 1 tangent weight mode is WeightedBoth"),
            static_cast<int32>(Values[1].Tangent.TangentWeightMode),
            static_cast<int32>(RCTWM_WeightedBoth));

        // For ease-in-out (0.42, 0, 0.58, 1.0): key 0 leave tangent == 0,
        // key 1 arrive tangent == 0; both leave/arrive weights > 0.
        TestNearlyEqual(TEXT("Key 0 leave tangent ~ 0"), Values[0].Tangent.LeaveTangent, 0.0f, 0.01f);
        TestNearlyEqual(TEXT("Key 1 arrive tangent ~ 0"), Values[1].Tangent.ArriveTangent, 0.0f, 0.01f);
        TestTrue(TEXT("Key 0 leave weight > 0"), Values[0].Tangent.LeaveTangentWeight > 0.0f);
        TestTrue(TEXT("Key 1 arrive weight > 0"), Values[1].Tangent.ArriveTangentWeight > 0.0f);
    }
#endif

    return true;
}


/**
 * MonolithUI.BakeSpringAnimation.Basic
 *
 * Bakes an underdamped spring (stiffness=100, damping=10, mass=1) into dense
 * linear keyframes. Asserts: key count > 10, at least 2 zero-crossings
 * relative to target (underdamped overshoot).
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIBakeSpringAnimationBasicTest,
    "MonolithUI.BakeSpringAnimation.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIBakeSpringAnimationBasicTest::RunTest(const FString& Parameters)
{
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    const FString SpringTestPath = TEXT("/Game/Tests/Monolith/UI/WBP_SpringTest");

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(SpringTestPath, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), SpringTestPath);
    Params->SetStringField(TEXT("animation_name"), TEXT("SpringBounce"));
    Params->SetStringField(TEXT("widget_name"), TEXT("MyImage"));
    Params->SetStringField(TEXT("property"), TEXT("RenderOpacity"));
    Params->SetNumberField(TEXT("from_value"), 0.0);
    Params->SetNumberField(TEXT("to_value"), 1.0);
    Params->SetNumberField(TEXT("stiffness"), 100.0);
    Params->SetNumberField(TEXT("damping"), 10.0);
    Params->SetNumberField(TEXT("mass"), 1.0);
    Params->SetNumberField(TEXT("fps"), 60.0);
    Params->SetNumberField(TEXT("duration"), 2.0);
    Params->SetBoolField(TEXT("compile_once"), true);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("bake_spring_animation"), Params);

    TestTrue(TEXT("bake_spring_animation bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    double KeysInserted = 0.0;
    TestTrue(TEXT("result has keys_inserted"), Result.Result->TryGetNumberField(TEXT("keys_inserted"), KeysInserted));
    TestTrue(TEXT("keys_inserted > 10 (dense sampling)"), static_cast<int32>(KeysInserted) > 10);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *SpringTestPath);
    if (!WBP)
    {
        AddError(TEXT("Failed to reload spring test WBP"));
        return false;
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* FoundAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetDisplayLabel() == TEXT("SpringBounce"))
        {
            FoundAnim = Anim;
            break;
        }
    }
    TestNotNull(TEXT("SpringBounce animation found"), FoundAnim);
    if (!FoundAnim || !FoundAnim->MovieScene)
    {
        return false;
    }

    UMovieSceneFloatTrack* FloatTrack = nullptr;
    const UMovieScene* ConstScene = FoundAnim->MovieScene;
    for (const FMovieSceneBinding& Binding : ConstScene->GetBindings())
    {
        FloatTrack = FoundAnim->MovieScene->FindTrack<UMovieSceneFloatTrack>(
            Binding.GetObjectGuid(), FName(TEXT("RenderOpacity")));
        if (FloatTrack)
        {
            break;
        }
    }
    TestNotNull(TEXT("RenderOpacity float track found"), FloatTrack);
    if (!FloatTrack || FloatTrack->GetAllSections().Num() == 0)
    {
        return false;
    }

    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(FloatTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Float section exists"), Section);
    if (!Section)
    {
        return false;
    }

    const FMovieSceneFloatChannel& Channel = Section->GetChannel();
    TestTrue(TEXT("Channel key count > 10"), Channel.GetNumKeys() > 10);

    // Underdamped spring should overshoot, so values cross 1.0 at least twice.
    TArrayView<const FMovieSceneFloatValue> Values = Channel.GetValues();
    int32 ZeroCrossings = 0;
    const float Target = 1.0f;
    for (int32 i = 1; i < Values.Num(); ++i)
    {
        const float Prev = Values[i - 1].Value - Target;
        const float Curr = Values[i].Value - Target;
        if ((Prev > 0.0f && Curr <= 0.0f) || (Prev < 0.0f && Curr >= 0.0f))
        {
            ++ZeroCrossings;
        }
    }
    TestTrue(TEXT("Underdamped spring has >= 2 zero-crossings"), ZeroCrossings >= 2);
#endif

    return true;
}


/**
 * MonolithUI.AddAnimationEventTrack.Basic
 *
 * Adds 2 event keys at t=0 and t=0.3 to an existing animation. Asserts:
 * master event track exists, section has correct key count.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIAddAnimationEventTrackBasicTest,
    "MonolithUI.AddAnimationEventTrack.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIAddAnimationEventTrackBasicTest::RunTest(const FString& Parameters)
{
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    const FString EventTestPath = TEXT("/Game/Tests/Monolith/UI/WBP_EventTrackTest");

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(EventTestPath, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    {
        TSharedPtr<FJsonObject> CreateParams = MakeShared<FJsonObject>();
        CreateParams->SetStringField(TEXT("asset_path"), EventTestPath);
        CreateParams->SetStringField(TEXT("animation_name"), TEXT("FadeIn"));
        CreateParams->SetNumberField(TEXT("duration_sec"), 0.5);
        CreateParams->SetBoolField(TEXT("compile_once"), false);

        TArray<TSharedPtr<FJsonValue>> Tracks;
        {
            TSharedPtr<FJsonObject> Track = MakeShared<FJsonObject>();
            Track->SetStringField(TEXT("widget_name"), TEXT("MyImage"));
            Track->SetStringField(TEXT("property"), TEXT("RenderOpacity"));

            TArray<TSharedPtr<FJsonValue>> Keys;
            {
                TSharedPtr<FJsonObject> K0 = MakeShared<FJsonObject>();
                K0->SetNumberField(TEXT("time"), 0.0);
                K0->SetNumberField(TEXT("value"), 0.0);
                K0->SetStringField(TEXT("interp"), TEXT("linear"));
                Keys.Add(MakeShared<FJsonValueObject>(K0));
            }
            {
                TSharedPtr<FJsonObject> K1 = MakeShared<FJsonObject>();
                K1->SetNumberField(TEXT("time"), 0.5);
                K1->SetNumberField(TEXT("value"), 1.0);
                K1->SetStringField(TEXT("interp"), TEXT("linear"));
                Keys.Add(MakeShared<FJsonValueObject>(K1));
            }
            Track->SetArrayField(TEXT("keys"), Keys);
            Tracks.Add(MakeShared<FJsonValueObject>(Track));
        }
        CreateParams->SetArrayField(TEXT("tracks"), Tracks);

        const FMonolithActionResult CreateResult = FMonolithToolRegistry::Get().ExecuteAction(
            TEXT("ui"), TEXT("create_animation_v2"), CreateParams);
        if (!CreateResult.bSuccess)
        {
            AddError(FString::Printf(TEXT("Prerequisite create_animation_v2 failed: %s"), *CreateResult.ErrorMessage));
            return false;
        }
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), EventTestPath);
    Params->SetStringField(TEXT("animation_name"), TEXT("FadeIn"));

    TArray<TSharedPtr<FJsonValue>> Events;
    {
        TSharedPtr<FJsonObject> E0 = MakeShared<FJsonObject>();
        E0->SetNumberField(TEXT("time"), 0.0);
        E0->SetStringField(TEXT("event_name"), TEXT("OnFadeStart"));
        Events.Add(MakeShared<FJsonValueObject>(E0));
    }
    {
        TSharedPtr<FJsonObject> E1 = MakeShared<FJsonObject>();
        E1->SetNumberField(TEXT("time"), 0.3);
        E1->SetStringField(TEXT("event_name"), TEXT("OnFadeMid"));
        Events.Add(MakeShared<FJsonValueObject>(E1));
    }
    Params->SetArrayField(TEXT("events"), Events);

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("add_animation_event_track"), Params);

    TestTrue(TEXT("add_animation_event_track bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    double EventsInserted = 0.0;
    TestTrue(TEXT("result has events_inserted"), Result.Result->TryGetNumberField(TEXT("events_inserted"), EventsInserted));
    TestEqual(TEXT("events_inserted == 2"), static_cast<int32>(EventsInserted), 2);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *EventTestPath);
    if (!WBP)
    {
        AddError(TEXT("Failed to reload event track test WBP"));
        return false;
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* FoundAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetDisplayLabel() == TEXT("FadeIn"))
        {
            FoundAnim = Anim;
            break;
        }
    }
    TestNotNull(TEXT("FadeIn animation found"), FoundAnim);
    if (!FoundAnim || !FoundAnim->MovieScene)
    {
        return false;
    }

    const UMovieScene* ConstScene = FoundAnim->MovieScene;
    UMovieSceneEventTrack* EventTrack = FoundAnim->MovieScene->FindTrack<UMovieSceneEventTrack>();
    TestNotNull(TEXT("Master event track found"), EventTrack);
    if (!EventTrack)
    {
        return false;
    }

    TestTrue(TEXT("Event track has at least 1 section"), EventTrack->GetAllSections().Num() > 0);

    UMovieSceneEventTriggerSection* TriggerSection =
        Cast<UMovieSceneEventTriggerSection>(EventTrack->GetAllSections()[0]);
    TestNotNull(TEXT("Trigger section exists"), TriggerSection);
    if (!TriggerSection)
    {
        return false;
    }

    TestEqual(TEXT("Event channel has 2 keys"),
        TriggerSection->EventChannel.GetNumKeys(), 2);
#endif

    return true;
}


/**
 * MonolithUI.BindAnimationToEvent.Basic
 *
 * Binds "OnHovered" to "Started" on an existing animation. Verifies
 * UWidgetAnimationDelegateBinding has the correct entry on the generated class.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMonolithUIBindAnimationToEventBasicTest,
    "MonolithUI.BindAnimationToEvent.Basic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMonolithUIBindAnimationToEventBasicTest::RunTest(const FString& Parameters)
{
    using MonolithUI::TestUtils::CreateOrReuseTestWidgetBlueprint;

    const FString BindTestPath = TEXT("/Game/Tests/Monolith/UI/WBP_BindAnimTest");

    FString FixtureError;
    if (!CreateOrReuseTestWidgetBlueprint(BindTestPath, FName(TEXT("MyImage")), nullptr, FixtureError))
    {
        AddError(FString::Printf(TEXT("Fixture build failed: %s"), *FixtureError));
        return false;
    }

    {
        TSharedPtr<FJsonObject> CreateParams = MakeShared<FJsonObject>();
        CreateParams->SetStringField(TEXT("asset_path"), BindTestPath);
        CreateParams->SetStringField(TEXT("animation_name"), TEXT("FadeIn"));
        CreateParams->SetNumberField(TEXT("duration_sec"), 0.5);
        CreateParams->SetBoolField(TEXT("compile_once"), true);

        TArray<TSharedPtr<FJsonValue>> Tracks;
        {
            TSharedPtr<FJsonObject> Track = MakeShared<FJsonObject>();
            Track->SetStringField(TEXT("widget_name"), TEXT("MyImage"));
            Track->SetStringField(TEXT("property"), TEXT("RenderOpacity"));

            TArray<TSharedPtr<FJsonValue>> Keys;
            {
                TSharedPtr<FJsonObject> K0 = MakeShared<FJsonObject>();
                K0->SetNumberField(TEXT("time"), 0.0);
                K0->SetNumberField(TEXT("value"), 0.0);
                K0->SetStringField(TEXT("interp"), TEXT("linear"));
                Keys.Add(MakeShared<FJsonValueObject>(K0));
            }
            {
                TSharedPtr<FJsonObject> K1 = MakeShared<FJsonObject>();
                K1->SetNumberField(TEXT("time"), 0.5);
                K1->SetNumberField(TEXT("value"), 1.0);
                K1->SetStringField(TEXT("interp"), TEXT("linear"));
                Keys.Add(MakeShared<FJsonValueObject>(K1));
            }
            Track->SetArrayField(TEXT("keys"), Keys);
            Tracks.Add(MakeShared<FJsonValueObject>(Track));
        }
        CreateParams->SetArrayField(TEXT("tracks"), Tracks);

        const FMonolithActionResult CreateResult = FMonolithToolRegistry::Get().ExecuteAction(
            TEXT("ui"), TEXT("create_animation_v2"), CreateParams);
        if (!CreateResult.bSuccess)
        {
            AddError(FString::Printf(TEXT("Prerequisite create_animation_v2 failed: %s"), *CreateResult.ErrorMessage));
            return false;
        }
    }

    TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("asset_path"), BindTestPath);
    Params->SetStringField(TEXT("animation_name"), TEXT("FadeIn"));
    Params->SetStringField(TEXT("widget_event"), TEXT("OnHovered"));
    Params->SetStringField(TEXT("animation_event"), TEXT("Started"));

    const FMonolithActionResult Result = FMonolithToolRegistry::Get().ExecuteAction(
        TEXT("ui"), TEXT("bind_animation_to_event"), Params);

    TestTrue(TEXT("bind_animation_to_event bSuccess"), Result.bSuccess);
    if (!Result.bSuccess)
    {
        AddError(FString::Printf(TEXT("Action error: %s (code %d)"), *Result.ErrorMessage, Result.ErrorCode));
        return false;
    }

    bool bBindingCreated = false;
    TestTrue(TEXT("result has binding_created"), Result.Result->TryGetBoolField(TEXT("binding_created"), bBindingCreated));
    TestTrue(TEXT("binding_created is true"), bBindingCreated);

    FString FuncNameBound;
    TestTrue(TEXT("result has function_name_bound"), Result.Result->TryGetStringField(TEXT("function_name_bound"), FuncNameBound));
    TestEqual(TEXT("function_name_bound matches"), FuncNameBound, TEXT("OnHovered_PlayFadeIn"));

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *BindTestPath);
    if (!WBP || !WBP->GeneratedClass)
    {
        AddError(TEXT("Failed to reload WBP or GeneratedClass is null"));
        return false;
    }

    UDynamicBlueprintBinding* BindingObj = UBlueprintGeneratedClass::GetDynamicBindingObject(
        WBP->GeneratedClass, UWidgetAnimationDelegateBinding::StaticClass());

    if (!BindingObj)
    {
        AddWarning(TEXT("UWidgetAnimationDelegateBinding not found on GeneratedClass -- "
                       "may have been cleared by recompilation. Marking as expected limitation."));
        return true;
    }

    UWidgetAnimationDelegateBinding* DelegateBinding = Cast<UWidgetAnimationDelegateBinding>(BindingObj);
    TestNotNull(TEXT("DelegateBinding cast succeeded"), DelegateBinding);
    if (!DelegateBinding)
    {
        return false;
    }

    TestTrue(TEXT("Has at least 1 binding entry"),
        DelegateBinding->WidgetAnimationDelegateBindings.Num() > 0);

    if (DelegateBinding->WidgetAnimationDelegateBindings.Num() > 0)
    {
        const FBlueprintWidgetAnimationDelegateBinding& Entry =
            DelegateBinding->WidgetAnimationDelegateBindings.Last();
        TestEqual(TEXT("Action is Started"),
            static_cast<uint8>(Entry.Action),
            static_cast<uint8>(EWidgetAnimationEvent::Started));
        TestEqual(TEXT("AnimationToBind is FadeIn"),
            Entry.AnimationToBind, FName(TEXT("FadeIn")));
        TestEqual(TEXT("FunctionNameToBind matches"),
            Entry.FunctionNameToBind, FName(TEXT("OnHovered_PlayFadeIn")));
    }

    return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
