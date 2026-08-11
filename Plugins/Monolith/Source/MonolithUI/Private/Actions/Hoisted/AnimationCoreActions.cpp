// Copyright tumourlove. All Rights Reserved.
#include "Actions/Hoisted/AnimationCoreActions.h"

// Monolith registry
#include "MonolithToolRegistry.h"

// JSON
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// Core / packaging
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"

// Widget Blueprint (editor-only: Animations, WidgetTree)
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Widget.h"

// UWidgetAnimation + binding
#include "Animation/WidgetAnimation.h"

// MovieScene core
#include "MovieScene.h"

// MovieScene tracks + sections
#include "Tracks/MovieSceneFloatTrack.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "Channels/MovieSceneCurveChannelCommon.h"

// Compile
#include "Kismet2/KismetEditorUtilities.h"

// Frame math
#include "Misc/FrameRate.h"
#include "Misc/FrameTime.h"

namespace MonolithUI::AnimationInternal
{
    /** Resolve a property name to the track property path UMG expects. */
    static FString ResolvePropertyPath(const FString& PropertyName)
    {
        // UMG animation tracks use the direct UPROPERTY name as the path.
        // RenderOpacity maps to UWidget::RenderOpacity. ColorAndOpacity / RenderTransform
        // follow the same pattern.
        return PropertyName;
    }

    /** Find a widget by name in the WBP's widget tree. */
    static UWidget* FindWidgetByName(UWidgetBlueprint* WBP, const FString& WidgetName)
    {
        if (!WBP->WidgetTree)
        {
            return nullptr;
        }
        return WBP->WidgetTree->FindWidget(FName(*WidgetName));
    }

    /** Find an existing UWidgetAnimation by display label, or return nullptr. */
    static UWidgetAnimation* FindAnimationByName(UWidgetBlueprint* WBP, const FString& AnimName)
    {
#if WITH_EDITORONLY_DATA
        for (UWidgetAnimation* Anim : WBP->Animations)
        {
            if (Anim && Anim->GetDisplayLabel() == AnimName)
            {
                return Anim;
            }
        }
#endif
        return nullptr;
    }

    /**
     * Find or create a UWidgetAnimation on the WBP. Returns nullptr if the build
     * lacks WITH_EDITORONLY_DATA (won't happen in an editor-only module).
     */
    static UWidgetAnimation* FindOrCreateAnimation(UWidgetBlueprint* WBP, const FString& AnimName)
    {
#if WITH_EDITORONLY_DATA
        UWidgetAnimation* Existing = FindAnimationByName(WBP, AnimName);
        if (Existing)
        {
            return Existing;
        }

        UWidgetAnimation* NewAnim = NewObject<UWidgetAnimation>(WBP, FName(*AnimName));
        if (!NewAnim)
        {
            return nullptr;
        }

#if WITH_EDITOR
        NewAnim->SetDisplayLabel(AnimName);
#endif

        if (!NewAnim->MovieScene)
        {
            NewAnim->MovieScene = NewObject<UMovieScene>(NewAnim, NewAnim->GetFName(), RF_Transactional);
        }

        WBP->Animations.Add(NewAnim);

        // Register in WidgetVariableNameToGuidMap so the WBP compiler's validation pass
        // (WidgetBlueprintCompiler.cpp:805) finds the entry. Use deterministic GUID
        // matching the compiler's own pattern.
        WBP->WidgetVariableNameToGuidMap.Add(
            NewAnim->GetFName(),
            FGuid::NewDeterministicGuid(NewAnim->GetPathName()));

        return NewAnim;
#else
        return nullptr;
#endif
    }

    /** Ensure a possessable binding exists for the given widget. Returns the binding GUID. */
    static FGuid EnsurePossessableBinding(
        UWidgetAnimation* WidgetAnim,
        UMovieScene* Scene,
        const FString& WidgetName,
        bool bIsRootWidget)
    {
        for (const FWidgetAnimationBinding& Binding : WidgetAnim->AnimationBindings)
        {
            if (Binding.WidgetName == FName(*WidgetName))
            {
                return Binding.AnimationGuid;
            }
        }

        FGuid PossessableGuid = Scene->AddPossessable(WidgetName, UWidget::StaticClass());

        FWidgetAnimationBinding NewBinding;
        NewBinding.WidgetName = FName(*WidgetName);
        NewBinding.SlotWidgetName = NAME_None;
        NewBinding.AnimationGuid = PossessableGuid;
        NewBinding.bIsRootWidget = bIsRootWidget;
        WidgetAnim->AnimationBindings.Add(NewBinding);

        return PossessableGuid;
    }

    /** Find or create a float track + section. Returns the float channel for key insertion. */
    static FMovieSceneFloatChannel* EnsureFloatTrackAndSection(
        UMovieScene* Scene,
        const FGuid& PossessableGuid,
        const FString& PropertyName,
        const TRange<FFrameNumber>& SectionRange)
    {
        UMovieSceneFloatTrack* FloatTrack = Scene->FindTrack<UMovieSceneFloatTrack>(PossessableGuid, FName(*PropertyName));
        if (!FloatTrack)
        {
            FloatTrack = Scene->AddTrack<UMovieSceneFloatTrack>(PossessableGuid);
            if (!FloatTrack)
            {
                return nullptr;
            }
            FloatTrack->SetPropertyNameAndPath(FName(*PropertyName), ResolvePropertyPath(PropertyName));
        }

        UMovieSceneFloatSection* Section = nullptr;
        if (FloatTrack->GetAllSections().Num() > 0)
        {
            Section = Cast<UMovieSceneFloatSection>(FloatTrack->GetAllSections()[0]);
        }
        if (!Section)
        {
            Section = Cast<UMovieSceneFloatSection>(FloatTrack->CreateNewSection());
            if (!Section)
            {
                return nullptr;
            }
            Section->SetRange(SectionRange);
            FloatTrack->AddSection(*Section);
        }
        else
        {
            // Clear existing keys so repeated calls are idempotent.
            Section->GetChannel().Reset();
            TRange<FFrameNumber> CurrentRange = Section->GetRange();
            Section->SetRange(TRange<FFrameNumber>::Hull(CurrentRange, SectionRange));
        }

        return &Section->GetChannel();
    }

    /** Parsed keyframe from JSON. */
    struct FParsedKey
    {
        double Time = 0.0;
        float Value = 0.0f;
        FString Interp = TEXT("cubic"); // "cubic", "linear", "constant"
        float ArriveTangent = 0.0f;
        float LeaveTangent = 0.0f;
        float ArriveTangentWeight = 0.0f;
        float LeaveTangentWeight = 0.0f;
        bool bHasWeights = false;
    };

    /** Insert a single key into a float channel. */
    static void InsertKey(FMovieSceneFloatChannel* Channel, const FFrameRate& TickRes, const FParsedKey& Key)
    {
        const FFrameNumber Frame = TickRes.AsFrameNumber(Key.Time);

        if (Key.Interp == TEXT("linear"))
        {
            Channel->AddLinearKey(Frame, Key.Value);
        }
        else if (Key.Interp == TEXT("constant"))
        {
            Channel->AddConstantKey(Frame, Key.Value);
        }
        else
        {
            FMovieSceneTangentData TangentData;
            TangentData.ArriveTangent = Key.ArriveTangent;
            TangentData.LeaveTangent = Key.LeaveTangent;
            TangentData.ArriveTangentWeight = Key.ArriveTangentWeight;
            TangentData.LeaveTangentWeight = Key.LeaveTangentWeight;
            TangentData.TangentWeightMode = Key.bHasWeights
                ? RCTWM_WeightedBoth
                : RCTWM_WeightedNone;

            Channel->AddCubicKey(Frame, Key.Value, RCTM_User, TangentData);
        }
    }

} // namespace MonolithUI::AnimationInternal


// -----------------------------------------------------------------------------
// Phase I — public-to-MonolithUI helper surface.
//
// The forwarders below expose the same logic the action handlers consume so the
// new `FUIAnimationMovieSceneBuilder` (Public/Animation/) can drive editor
// MovieScene without re-implementing track/binding/key plumbing or the
// CSS-bezier-to-weighted-tangent math.
//
// All forwarders translate FAnimationCoreKey <-> FParsedKey at the boundary so
// the .cpp's anonymous helper namespace stays the single source of truth.
// -----------------------------------------------------------------------------

namespace MonolithUI
{
    static AnimationInternal::FParsedKey ToParsedKey(const FAnimationCoreKey& In)
    {
        AnimationInternal::FParsedKey Out;
        Out.Time = In.Time;
        Out.Value = In.Value;
        Out.Interp = In.Interp;
        Out.ArriveTangent = In.ArriveTangent;
        Out.LeaveTangent = In.LeaveTangent;
        Out.ArriveTangentWeight = In.ArriveTangentWeight;
        Out.LeaveTangentWeight = In.LeaveTangentWeight;
        Out.bHasWeights = In.bHasWeights;
        return Out;
    }

    void ComputeBezierWeightedTangents(
        double X1, double Y1, double X2, double Y2,
        double FromValue, double ToValue,
        double StartTime, double EndTime,
        FAnimationCoreKey& OutKey0,
        FAnimationCoreKey& OutKey1)
    {
        const double DeltaValue = ToValue - FromValue;
        const double DurationSec = EndTime - StartTime;
        const double SafeDuration = (DurationSec > 0.0) ? DurationSec : 1e-6;

        OutKey0 = FAnimationCoreKey{};
        OutKey0.Time = StartTime;
        OutKey0.Value = static_cast<float>(FromValue);
        OutKey0.Interp = TEXT("cubic");
        OutKey0.LeaveTangent = (X1 != 0.0)
            ? static_cast<float>((Y1 / X1) * DeltaValue / SafeDuration)
            : 0.0f;
        OutKey0.LeaveTangentWeight = static_cast<float>(FMath::Sqrt(X1 * X1 + Y1 * Y1) / 3.0);
        OutKey0.ArriveTangent = 0.0f;
        OutKey0.ArriveTangentWeight = 0.0f;
        OutKey0.bHasWeights = true;

        OutKey1 = FAnimationCoreKey{};
        OutKey1.Time = EndTime;
        OutKey1.Value = static_cast<float>(ToValue);
        OutKey1.Interp = TEXT("cubic");
        OutKey1.ArriveTangent = (X2 != 1.0)
            ? static_cast<float>(((1.0 - Y2) / (1.0 - X2)) * DeltaValue / SafeDuration)
            : 0.0f;
        OutKey1.ArriveTangentWeight = static_cast<float>(FMath::Sqrt((1.0 - X2) * (1.0 - X2) + (1.0 - Y2) * (1.0 - Y2)) / 3.0);
        OutKey1.LeaveTangent = 0.0f;
        OutKey1.LeaveTangentWeight = 0.0f;
        OutKey1.bHasWeights = true;
    }

    UWidgetAnimation* FindOrCreateWidgetAnimation(
        UWidgetBlueprint* WBP,
        const FString& AnimationName)
    {
        return AnimationInternal::FindOrCreateAnimation(WBP, AnimationName);
    }

    FGuid EnsureWidgetPossessableBinding(
        UWidgetAnimation* WidgetAnim,
        UMovieScene* Scene,
        const FString& WidgetName,
        bool bIsRootWidget)
    {
        return AnimationInternal::EnsurePossessableBinding(WidgetAnim, Scene, WidgetName, bIsRootWidget);
    }

    FMovieSceneFloatChannel* EnsureFloatTrackSectionChannel(
        UMovieScene* Scene,
        const FGuid& PossessableGuid,
        const FString& PropertyName,
        const TRange<FFrameNumber>& SectionRange)
    {
        return AnimationInternal::EnsureFloatTrackAndSection(Scene, PossessableGuid, PropertyName, SectionRange);
    }

    void InsertFloatChannelKey(
        FMovieSceneFloatChannel* Channel,
        const FFrameRate& TickRes,
        const FAnimationCoreKey& Key)
    {
        AnimationInternal::InsertKey(Channel, TickRes, ToParsedKey(Key));
    }
} // namespace MonolithUI


FMonolithActionResult MonolithUI::FAnimationCoreActions::HandleCreateAnimationV2(
    const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::AnimationInternal;

    if (!Params.IsValid())
    {
        return FMonolithActionResult::Error(TEXT("Missing params object"), -32602);
    }

    FString AssetPath;
    if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: asset_path"), -32602);
    }
    FString AnimName;
    if (!Params->TryGetStringField(TEXT("animation_name"), AnimName) || AnimName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: animation_name"), -32602);
    }
    double DurationSec = 0.0;
    if (!Params->TryGetNumberField(TEXT("duration_sec"), DurationSec) || DurationSec <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("duration_sec must be a positive number"), -32602);
    }

    const TArray<TSharedPtr<FJsonValue>>* TracksArr = nullptr;
    if (!Params->TryGetArrayField(TEXT("tracks"), TracksArr) || !TracksArr || TracksArr->Num() == 0)
    {
        return FMonolithActionResult::Error(TEXT("tracks must be a non-empty array"), -32602);
    }

    bool bCompileOnce = true;
    Params->TryGetBoolField(TEXT("compile_once"), bCompileOnce);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' not found"), *AssetPath), -32603);
    }

#if WITH_EDITORONLY_DATA
    if (!WBP->WidgetTree)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' has no WidgetTree"), *AssetPath), -32603);
    }

    UWidgetAnimation* WidgetAnim = FindOrCreateAnimation(WBP, AnimName);
    if (!WidgetAnim || !WidgetAnim->MovieScene)
    {
        return FMonolithActionResult::Error(TEXT("Failed to create UWidgetAnimation or MovieScene"), -32603);
    }

    UMovieScene* Scene = WidgetAnim->MovieScene;
    const FFrameRate TickRes = Scene->GetTickResolution();

    const FFrameNumber StartFrame(0);
    const FFrameNumber EndFrame = TickRes.AsFrameNumber(DurationSec);
    Scene->SetPlaybackRange(StartFrame, (EndFrame - StartFrame).Value);

    TArray<FString> Warnings;
    int32 TotalKeysInserted = 0;
    int32 TracksCreated = 0;

    for (int32 TrackIdx = 0; TrackIdx < TracksArr->Num(); ++TrackIdx)
    {
        const TSharedPtr<FJsonValue>& TrackVal = (*TracksArr)[TrackIdx];
        const TSharedPtr<FJsonObject>* TrackObjPtr = nullptr;
        if (!TrackVal.IsValid() || !TrackVal->TryGetObject(TrackObjPtr) || !TrackObjPtr || !TrackObjPtr->IsValid())
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("tracks[%d] must be an object"), TrackIdx), -32602);
        }
        const TSharedPtr<FJsonObject>& TrackObj = *TrackObjPtr;

        FString WidgetName;
        if (!TrackObj->TryGetStringField(TEXT("widget_name"), WidgetName) || WidgetName.IsEmpty())
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("tracks[%d].widget_name is required"), TrackIdx), -32602);
        }
        FString PropertyName;
        if (!TrackObj->TryGetStringField(TEXT("property"), PropertyName) || PropertyName.IsEmpty())
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("tracks[%d].property is required"), TrackIdx), -32602);
        }

        const TArray<TSharedPtr<FJsonValue>>* KeysArr = nullptr;
        if (!TrackObj->TryGetArrayField(TEXT("keys"), KeysArr) || !KeysArr || KeysArr->Num() == 0)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("tracks[%d].keys must be a non-empty array"), TrackIdx), -32602);
        }

        UWidget* Widget = FindWidgetByName(WBP, WidgetName);
        if (!Widget)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Widget '%s' not found in WidgetTree of '%s'"), *WidgetName, *AssetPath), -32603);
        }

        const bool bIsRoot = (Widget == WBP->WidgetTree->RootWidget);

        FGuid PossessableGuid = EnsurePossessableBinding(WidgetAnim, Scene, WidgetName, bIsRoot);

        TRange<FFrameNumber> SectionRange(StartFrame, EndFrame);

        FMovieSceneFloatChannel* Channel = EnsureFloatTrackAndSection(
            Scene, PossessableGuid, PropertyName, SectionRange);
        if (!Channel)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Failed to create float track for '%s.%s'"), *WidgetName, *PropertyName), -32603);
        }
        ++TracksCreated;

        for (int32 KeyIdx = 0; KeyIdx < KeysArr->Num(); ++KeyIdx)
        {
            const TSharedPtr<FJsonValue>& KeyVal = (*KeysArr)[KeyIdx];
            const TSharedPtr<FJsonObject>* KeyObjPtr = nullptr;
            if (!KeyVal.IsValid() || !KeyVal->TryGetObject(KeyObjPtr) || !KeyObjPtr || !KeyObjPtr->IsValid())
            {
                return FMonolithActionResult::Error(
                    FString::Printf(TEXT("tracks[%d].keys[%d] must be an object"), TrackIdx, KeyIdx), -32602);
            }
            const TSharedPtr<FJsonObject>& KeyObj = *KeyObjPtr;

            FParsedKey ParsedKey;
            if (!KeyObj->TryGetNumberField(TEXT("time"), ParsedKey.Time))
            {
                return FMonolithActionResult::Error(
                    FString::Printf(TEXT("tracks[%d].keys[%d].time is required"), TrackIdx, KeyIdx), -32602);
            }
            double ValueD = 0.0;
            if (!KeyObj->TryGetNumberField(TEXT("value"), ValueD))
            {
                return FMonolithActionResult::Error(
                    FString::Printf(TEXT("tracks[%d].keys[%d].value is required"), TrackIdx, KeyIdx), -32602);
            }
            ParsedKey.Value = static_cast<float>(ValueD);

            KeyObj->TryGetStringField(TEXT("interp"), ParsedKey.Interp);

            double TempD = 0.0;
            if (KeyObj->TryGetNumberField(TEXT("arrive_tangent"), TempD))
            {
                ParsedKey.ArriveTangent = static_cast<float>(TempD);
            }
            if (KeyObj->TryGetNumberField(TEXT("leave_tangent"), TempD))
            {
                ParsedKey.LeaveTangent = static_cast<float>(TempD);
            }
            if (KeyObj->TryGetNumberField(TEXT("arrive_weight"), TempD))
            {
                ParsedKey.ArriveTangentWeight = static_cast<float>(TempD);
                ParsedKey.bHasWeights = true;
            }
            if (KeyObj->TryGetNumberField(TEXT("leave_weight"), TempD))
            {
                ParsedKey.LeaveTangentWeight = static_cast<float>(TempD);
                ParsedKey.bHasWeights = true;
            }

            InsertKey(Channel, TickRes, ParsedKey);
            ++TotalKeysInserted;
        }
    }

    if (bCompileOnce)
    {
        FKismetEditorUtilities::CompileBlueprint(WBP);
    }

    WBP->MarkPackageDirty();

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimName);
    Result->SetNumberField(TEXT("tracks_created"), static_cast<double>(TracksCreated));
    Result->SetNumberField(TEXT("keys_inserted"), static_cast<double>(TotalKeysInserted));
    Result->SetBoolField(TEXT("compiled"), bCompileOnce);
    if (Warnings.Num() > 0)
    {
        TArray<TSharedPtr<FJsonValue>> Arr;
        for (const FString& W : Warnings)
        {
            Arr.Add(MakeShared<FJsonValueString>(W));
        }
        Result->SetArrayField(TEXT("warnings"), Arr);
    }
    return FMonolithActionResult::Success(Result);
#else
    return FMonolithActionResult::Error(TEXT("Animation authoring requires editor (WITH_EDITORONLY_DATA)"), -32603);
#endif
}


FMonolithActionResult MonolithUI::FAnimationCoreActions::HandleAddBezierEasedSegment(
    const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::AnimationInternal;

    if (!Params.IsValid())
    {
        return FMonolithActionResult::Error(TEXT("Missing params object"), -32602);
    }

    FString AssetPath;
    if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: asset_path"), -32602);
    }
    FString AnimName;
    if (!Params->TryGetStringField(TEXT("animation_name"), AnimName) || AnimName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: animation_name"), -32602);
    }
    FString WidgetName;
    if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName) || WidgetName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: widget_name"), -32602);
    }
    FString PropertyName;
    if (!Params->TryGetStringField(TEXT("property"), PropertyName) || PropertyName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: property"), -32602);
    }

    double FromValue = 0.0, ToValue = 0.0;
    if (!Params->TryGetNumberField(TEXT("from_value"), FromValue))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: from_value"), -32602);
    }
    if (!Params->TryGetNumberField(TEXT("to_value"), ToValue))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: to_value"), -32602);
    }

    double StartTime = 0.0, EndTime = 0.0;
    if (!Params->TryGetNumberField(TEXT("start_time"), StartTime))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: start_time"), -32602);
    }
    if (!Params->TryGetNumberField(TEXT("end_time"), EndTime))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: end_time"), -32602);
    }
    if (EndTime <= StartTime)
    {
        return FMonolithActionResult::Error(TEXT("end_time must be greater than start_time"), -32602);
    }

    const TArray<TSharedPtr<FJsonValue>>* BezierArr = nullptr;
    if (!Params->TryGetArrayField(TEXT("bezier"), BezierArr) || !BezierArr || BezierArr->Num() != 4)
    {
        return FMonolithActionResult::Error(TEXT("bezier must be an array of exactly 4 numbers [x1, y1, x2, y2]"), -32602);
    }
    const double X1 = (*BezierArr)[0]->AsNumber();
    const double Y1 = (*BezierArr)[1]->AsNumber();
    const double X2 = (*BezierArr)[2]->AsNumber();
    const double Y2 = (*BezierArr)[3]->AsNumber();

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' not found"), *AssetPath), -32603);
    }

#if WITH_EDITORONLY_DATA
    if (!WBP->WidgetTree)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' has no WidgetTree"), *AssetPath), -32603);
    }

    UWidget* Widget = FindWidgetByName(WBP, WidgetName);
    if (!Widget)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget '%s' not found in WidgetTree of '%s'"), *WidgetName, *AssetPath), -32603);
    }

    UWidgetAnimation* WidgetAnim = FindOrCreateAnimation(WBP, AnimName);
    if (!WidgetAnim || !WidgetAnim->MovieScene)
    {
        return FMonolithActionResult::Error(TEXT("Failed to create UWidgetAnimation or MovieScene"), -32603);
    }

    UMovieScene* Scene = WidgetAnim->MovieScene;
    const FFrameRate TickRes = Scene->GetTickResolution();

    const FFrameNumber EndFrame = TickRes.AsFrameNumber(EndTime);
    TRange<FFrameNumber> CurrentRange = Scene->GetPlaybackRange();
    if (CurrentRange.IsEmpty() || !CurrentRange.Contains(EndFrame))
    {
        const FFrameNumber StartFrame(0);
        Scene->SetPlaybackRange(TRange<FFrameNumber>(StartFrame, EndFrame + 1));
    }

    const bool bIsRoot = (Widget == WBP->WidgetTree->RootWidget);
    FGuid PossessableGuid = EnsurePossessableBinding(WidgetAnim, Scene, WidgetName, bIsRoot);

    TRange<FFrameNumber> SectionRange(TickRes.AsFrameNumber(StartTime), EndFrame);
    FMovieSceneFloatChannel* Channel = EnsureFloatTrackAndSection(
        Scene, PossessableGuid, PropertyName, SectionRange);
    if (!Channel)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Failed to create float track for '%s.%s'"), *WidgetName, *PropertyName), -32603);
    }

    // -- Bezier-to-tangent conversion --
    const double DeltaValue = ToValue - FromValue;
    const double DurationSec = EndTime - StartTime;

    FParsedKey Key0;
    Key0.Time = StartTime;
    Key0.Value = static_cast<float>(FromValue);
    Key0.Interp = TEXT("cubic");
    Key0.LeaveTangent = (X1 != 0.0) ? static_cast<float>((Y1 / X1) * DeltaValue / DurationSec) : 0.0f;
    Key0.LeaveTangentWeight = static_cast<float>(FMath::Sqrt(X1 * X1 + Y1 * Y1) / 3.0);
    Key0.ArriveTangent = 0.0f;
    Key0.ArriveTangentWeight = 0.0f;
    Key0.bHasWeights = true;

    FParsedKey Key1;
    Key1.Time = EndTime;
    Key1.Value = static_cast<float>(ToValue);
    Key1.Interp = TEXT("cubic");
    Key1.ArriveTangent = (X2 != 1.0) ? static_cast<float>(((1.0 - Y2) / (1.0 - X2)) * DeltaValue / DurationSec) : 0.0f;
    Key1.ArriveTangentWeight = static_cast<float>(FMath::Sqrt((1.0 - X2) * (1.0 - X2) + (1.0 - Y2) * (1.0 - Y2)) / 3.0);
    Key1.LeaveTangent = 0.0f;
    Key1.LeaveTangentWeight = 0.0f;
    Key1.bHasWeights = true;

    InsertKey(Channel, TickRes, Key0);
    InsertKey(Channel, TickRes, Key1);

    WBP->MarkPackageDirty();

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimName);
    Result->SetStringField(TEXT("widget_name"), WidgetName);
    Result->SetStringField(TEXT("property"), PropertyName);
    Result->SetNumberField(TEXT("keys_inserted"), 2.0);

    TSharedPtr<FJsonObject> TangentInfo = MakeShared<FJsonObject>();
    TangentInfo->SetNumberField(TEXT("key0_leave_tangent"), Key0.LeaveTangent);
    TangentInfo->SetNumberField(TEXT("key0_leave_weight"), Key0.LeaveTangentWeight);
    TangentInfo->SetNumberField(TEXT("key1_arrive_tangent"), Key1.ArriveTangent);
    TangentInfo->SetNumberField(TEXT("key1_arrive_weight"), Key1.ArriveTangentWeight);
    Result->SetObjectField(TEXT("tangent_info"), TangentInfo);

    return FMonolithActionResult::Success(Result);
#else
    return FMonolithActionResult::Error(TEXT("Animation authoring requires editor (WITH_EDITORONLY_DATA)"), -32603);
#endif
}


FMonolithActionResult MonolithUI::FAnimationCoreActions::HandleBakeSpringAnimation(
    const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::AnimationInternal;

    if (!Params.IsValid())
    {
        return FMonolithActionResult::Error(TEXT("Missing params object"), -32602);
    }

    FString AssetPath;
    if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath) || AssetPath.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: asset_path"), -32602);
    }
    FString AnimName;
    if (!Params->TryGetStringField(TEXT("animation_name"), AnimName) || AnimName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: animation_name"), -32602);
    }
    FString WidgetName;
    if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName) || WidgetName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: widget_name"), -32602);
    }
    FString PropertyName;
    if (!Params->TryGetStringField(TEXT("property"), PropertyName) || PropertyName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: property"), -32602);
    }

    double FromValue = 0.0, ToValue = 0.0;
    if (!Params->TryGetNumberField(TEXT("from_value"), FromValue))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: from_value"), -32602);
    }
    if (!Params->TryGetNumberField(TEXT("to_value"), ToValue))
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: to_value"), -32602);
    }

    double Stiffness = 100.0, Damping = 10.0, Mass = 1.0;
    if (!Params->TryGetNumberField(TEXT("stiffness"), Stiffness) || Stiffness <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("stiffness must be a positive number"), -32602);
    }
    if (!Params->TryGetNumberField(TEXT("damping"), Damping) || Damping < 0.0)
    {
        return FMonolithActionResult::Error(TEXT("damping must be a non-negative number"), -32602);
    }
    if (!Params->TryGetNumberField(TEXT("mass"), Mass) || Mass <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("mass must be a positive number"), -32602);
    }

    double Fps = 60.0;
    Params->TryGetNumberField(TEXT("fps"), Fps);
    if (Fps <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("fps must be a positive number"), -32602);
    }

    double DurationSec = 2.0;
    Params->TryGetNumberField(TEXT("duration"), DurationSec);
    if (DurationSec <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("duration must be a positive number"), -32602);
    }

    bool bCompileOnce = true;
    Params->TryGetBoolField(TEXT("compile_once"), bCompileOnce);

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' not found"), *AssetPath), -32603);
    }

#if WITH_EDITORONLY_DATA
    if (!WBP->WidgetTree)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' has no WidgetTree"), *AssetPath), -32603);
    }

    UWidget* Widget = FindWidgetByName(WBP, WidgetName);
    if (!Widget)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget '%s' not found in WidgetTree of '%s'"), *WidgetName, *AssetPath), -32603);
    }

    UWidgetAnimation* WidgetAnim = FindOrCreateAnimation(WBP, AnimName);
    if (!WidgetAnim || !WidgetAnim->MovieScene)
    {
        return FMonolithActionResult::Error(TEXT("Failed to create UWidgetAnimation or MovieScene"), -32603);
    }

    UMovieScene* Scene = WidgetAnim->MovieScene;
    const FFrameRate TickRes = Scene->GetTickResolution();

    // -- Spring sim (semi-implicit Euler) --
    const double Dt = 1.0 / Fps;
    const int32 MaxFrames = FMath::CeilToInt32(DurationSec * Fps);
    const double To = ToValue;

    double X = FromValue;
    double V = 0.0;
    int32 SettledFrames = 0;
    constexpr double PositionEpsilon = 1e-4;
    constexpr double VelocityEpsilon = 1e-4;
    constexpr int32 SettledThreshold = 5;

    TArray<FParsedKey> SpringKeys;
    SpringKeys.Reserve(MaxFrames + 1);

    for (int32 FrameIdx = 0; FrameIdx <= MaxFrames; ++FrameIdx)
    {
        const double TimeSec = FrameIdx * Dt;

        FParsedKey Key;
        Key.Time = TimeSec;
        Key.Value = static_cast<float>(X);
        Key.Interp = TEXT("linear");
        SpringKeys.Add(Key);

        if (FMath::Abs(X - To) < PositionEpsilon && FMath::Abs(V) < VelocityEpsilon)
        {
            ++SettledFrames;
            if (SettledFrames >= SettledThreshold)
            {
                break;
            }
        }
        else
        {
            SettledFrames = 0;
        }

        const double Accel = (-Stiffness * (X - To) - Damping * V) / Mass;
        V += Accel * Dt;
        X += V * Dt;
    }

    const double FinalTime = SpringKeys.Last().Time;
    const FFrameNumber StartFrame(0);
    const FFrameNumber EndFrame = TickRes.AsFrameNumber(FinalTime);
    Scene->SetPlaybackRange(StartFrame, (EndFrame - StartFrame).Value);

    const bool bIsRoot = (Widget == WBP->WidgetTree->RootWidget);
    FGuid PossessableGuid = EnsurePossessableBinding(WidgetAnim, Scene, WidgetName, bIsRoot);

    TRange<FFrameNumber> SectionRange(StartFrame, EndFrame);
    FMovieSceneFloatChannel* Channel = EnsureFloatTrackAndSection(
        Scene, PossessableGuid, PropertyName, SectionRange);
    if (!Channel)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Failed to create float track for '%s.%s'"), *WidgetName, *PropertyName), -32603);
    }

    for (const FParsedKey& Key : SpringKeys)
    {
        InsertKey(Channel, TickRes, Key);
    }

    if (bCompileOnce)
    {
        FKismetEditorUtilities::CompileBlueprint(WBP);
    }

    WBP->MarkPackageDirty();

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimName);
    Result->SetStringField(TEXT("widget_name"), WidgetName);
    Result->SetStringField(TEXT("property"), PropertyName);
    Result->SetNumberField(TEXT("keys_inserted"), static_cast<double>(SpringKeys.Num()));
    Result->SetNumberField(TEXT("duration_actual"), FinalTime);
    Result->SetBoolField(TEXT("early_settled"), SettledFrames >= SettledThreshold);
    Result->SetBoolField(TEXT("compiled"), bCompileOnce);
    return FMonolithActionResult::Success(Result);
#else
    return FMonolithActionResult::Error(TEXT("Animation authoring requires editor (WITH_EDITORONLY_DATA)"), -32603);
#endif
}


void MonolithUI::FAnimationCoreActions::Register(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("create_animation_v2"),
        TEXT("Creates a UWidgetAnimation on a Widget Blueprint with multi-track, multi-key support. "
             "Supports cubic (with tangent weights for CSS bezier easing), linear, and constant interpolation. "
             "Params: asset_path (string, /Game/... WBP path), animation_name (string), duration_sec (number), "
             "tracks (array of { widget_name, property, keys: [{ time, value, interp?: 'cubic'|'linear'|'constant', "
             "arrive_tangent?, leave_tangent?, arrive_weight?, leave_weight? }] }), "
             "compile_once (bool, optional, default true)."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FAnimationCoreActions::HandleCreateAnimationV2));

    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("add_bezier_eased_segment"),
        TEXT("Convenience wrapper: inserts a 2-key cubic-bezier eased segment into a WBP animation. "
             "Converts CSS cubic-bezier(x1,y1,x2,y2) control points into UE weighted tangents. "
             "Params: asset_path (string), animation_name (string), widget_name (string), property (string), "
             "from_value (number), to_value (number), start_time (number), end_time (number), "
             "bezier (array of 4 numbers [x1, y1, x2, y2])."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FAnimationCoreActions::HandleAddBezierEasedSegment));

    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("bake_spring_animation"),
        TEXT("Bakes a damped harmonic spring simulation into dense linear keyframes on a WBP animation. "
             "Semi-implicit Euler integrator with convergence early-out. "
             "Params: asset_path (string), animation_name (string), widget_name (string), property (string), "
             "from_value (number), to_value (number), stiffness (number, default 100), damping (number, default 10), "
             "mass (number, default 1), fps (number, optional, default 60), duration (number, optional, default 2.0), "
             "compile_once (bool, optional, default true)."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FAnimationCoreActions::HandleBakeSpringAnimation));
}
