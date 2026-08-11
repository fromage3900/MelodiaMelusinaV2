// Copyright tumourlove. All Rights Reserved.
#include "Actions/Hoisted/AnimationEventActions.h"

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

// UWidgetAnimation
#include "Animation/WidgetAnimation.h"

// MovieScene core
#include "MovieScene.h"

// Event track + section + channel
#include "Tracks/MovieSceneEventTrack.h"
#include "Sections/MovieSceneEventTriggerSection.h"
#include "Channels/MovieSceneEventChannel.h"
#include "Channels/MovieSceneEvent.h"

// Delegate bindings
#include "Animation/WidgetAnimationDelegateBinding.h"
#include "Blueprint/UserWidget.h"
#include "Engine/BlueprintGeneratedClass.h"

// Compile
#include "Kismet2/KismetEditorUtilities.h"

// Frame math
#include "Misc/FrameRate.h"
#include "Misc/FrameTime.h"


namespace MonolithUI::AnimationEventInternal
{
    /** Find an existing UWidgetAnimation by display label. */
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
} // namespace MonolithUI::AnimationEventInternal


FMonolithActionResult MonolithUI::FAnimationEventActions::HandleAddAnimationEventTrack(
    const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::AnimationEventInternal;

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

    const TArray<TSharedPtr<FJsonValue>>* EventsArr = nullptr;
    if (!Params->TryGetArrayField(TEXT("events"), EventsArr) || !EventsArr || EventsArr->Num() == 0)
    {
        return FMonolithActionResult::Error(TEXT("events must be a non-empty array"), -32602);
    }

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' not found"), *AssetPath), -32603);
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* WidgetAnim = FindAnimationByName(WBP, AnimName);
    if (!WidgetAnim)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Animation '%s' not found on '%s'"), *AnimName, *AssetPath), -32603);
    }

    UMovieScene* Scene = WidgetAnim->MovieScene;
    if (!Scene)
    {
        return FMonolithActionResult::Error(TEXT("Animation has no MovieScene"), -32603);
    }

    const FFrameRate TickRes = Scene->GetTickResolution();

    UMovieSceneEventTrack* EventTrack = Scene->FindTrack<UMovieSceneEventTrack>();
    if (!EventTrack)
    {
        EventTrack = Scene->AddTrack<UMovieSceneEventTrack>();
        if (!EventTrack)
        {
            return FMonolithActionResult::Error(TEXT("Failed to create UMovieSceneEventTrack"), -32603);
        }
    }

    UMovieSceneSection* NewSection = EventTrack->CreateNewSection();
    UMovieSceneEventTriggerSection* TriggerSection = Cast<UMovieSceneEventTriggerSection>(NewSection);
    if (!TriggerSection)
    {
        return FMonolithActionResult::Error(TEXT("Failed to create UMovieSceneEventTriggerSection"), -32603);
    }

    FFrameNumber MinFrame(0);
    FFrameNumber MaxFrame(0);
    bool bFirstEvent = true;

    int32 KeysInserted = 0;
    for (int32 i = 0; i < EventsArr->Num(); ++i)
    {
        const TSharedPtr<FJsonValue>& EventVal = (*EventsArr)[i];
        const TSharedPtr<FJsonObject>* EventObjPtr = nullptr;
        if (!EventVal.IsValid() || !EventVal->TryGetObject(EventObjPtr) || !EventObjPtr || !EventObjPtr->IsValid())
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("events[%d] must be an object"), i), -32602);
        }
        const TSharedPtr<FJsonObject>& EventObj = *EventObjPtr;

        double TimeSec = 0.0;
        if (!EventObj->TryGetNumberField(TEXT("time"), TimeSec))
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("events[%d].time is required"), i), -32602);
        }
        FString EventName;
        if (!EventObj->TryGetStringField(TEXT("event_name"), EventName) || EventName.IsEmpty())
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("events[%d].event_name is required"), i), -32602);
        }

        const FFrameNumber Frame = TickRes.AsFrameNumber(TimeSec);

        if (bFirstEvent)
        {
            MinFrame = Frame;
            MaxFrame = Frame;
            bFirstEvent = false;
        }
        else
        {
            if (Frame < MinFrame) MinFrame = Frame;
            if (Frame > MaxFrame) MaxFrame = Frame;
        }

        // FMovieSceneEvent is complex (compiled function pointers); we populate
        // the CompiledFunctionName for editor display + binding.
        FMovieSceneEvent EventKey;
#if WITH_EDITORONLY_DATA
        EventKey.CompiledFunctionName = FName(*EventName);
#endif

        TriggerSection->EventChannel.GetData().AddKey(Frame, EventKey);
        ++KeysInserted;
    }

    TriggerSection->SetRange(TRange<FFrameNumber>(MinFrame, MaxFrame + 1));
    EventTrack->AddSection(*TriggerSection);

    WBP->MarkPackageDirty();

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimName);
    Result->SetNumberField(TEXT("events_inserted"), static_cast<double>(KeysInserted));
    Result->SetBoolField(TEXT("track_created"), true);
    return FMonolithActionResult::Success(Result);
#else
    return FMonolithActionResult::Error(TEXT("Animation event authoring requires editor (WITH_EDITORONLY_DATA)"), -32603);
#endif
}


FMonolithActionResult MonolithUI::FAnimationEventActions::HandleBindAnimationToEvent(
    const TSharedPtr<FJsonObject>& Params)
{
    using namespace MonolithUI::AnimationEventInternal;

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
    FString WidgetEvent;
    if (!Params->TryGetStringField(TEXT("widget_event"), WidgetEvent) || WidgetEvent.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing or empty required param: widget_event"), -32602);
    }

    static const TArray<FString> ValidWidgetEvents = {
        TEXT("OnHovered"), TEXT("OnUnhovered"),
        TEXT("OnPressed"), TEXT("OnReleased"),
        TEXT("OnFocusReceived"), TEXT("OnFocusLost")
    };
    if (!ValidWidgetEvents.Contains(WidgetEvent))
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("widget_event '%s' is not valid. Must be one of: OnHovered, OnUnhovered, OnPressed, OnReleased, OnFocusReceived, OnFocusLost"), *WidgetEvent),
            -32602);
    }

    FString AnimationEvent = TEXT("Started");
    Params->TryGetStringField(TEXT("animation_event"), AnimationEvent);

    EWidgetAnimationEvent AnimEventEnum;
    if (AnimationEvent == TEXT("Finished"))
    {
        AnimEventEnum = EWidgetAnimationEvent::Finished;
    }
    else if (AnimationEvent == TEXT("Started"))
    {
        AnimEventEnum = EWidgetAnimationEvent::Started;
    }
    else
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("animation_event '%s' must be 'Started' or 'Finished'"), *AnimationEvent),
            -32602);
    }

    UWidgetBlueprint* WBP = LoadObject<UWidgetBlueprint>(nullptr, *AssetPath);
    if (!WBP)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget Blueprint '%s' not found"), *AssetPath), -32603);
    }

#if WITH_EDITORONLY_DATA
    UWidgetAnimation* WidgetAnim = FindAnimationByName(WBP, AnimName);
    if (!WidgetAnim)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Animation '%s' not found on '%s'"), *AnimName, *AssetPath), -32603);
    }

    if (!WBP->GeneratedClass)
    {
        FKismetEditorUtilities::CompileBlueprint(WBP);
    }

    UClass* GenClass = WBP->GeneratedClass;
    if (!GenClass)
    {
        return FMonolithActionResult::Error(TEXT("Widget Blueprint has no GeneratedClass after compilation"), -32603);
    }

    UBlueprintGeneratedClass* BPGC = Cast<UBlueprintGeneratedClass>(GenClass);
    if (!BPGC)
    {
        return FMonolithActionResult::Error(TEXT("GeneratedClass is not a UBlueprintGeneratedClass"), -32603);
    }

    // Pattern from KismetCompiler.cpp:3287-3291.
    UDynamicBlueprintBinding* ExistingBinding = UBlueprintGeneratedClass::GetDynamicBindingObject(
        BPGC, UWidgetAnimationDelegateBinding::StaticClass());

    UWidgetAnimationDelegateBinding* DelegateBinding = nullptr;
    if (ExistingBinding)
    {
        DelegateBinding = CastChecked<UWidgetAnimationDelegateBinding>(ExistingBinding);
    }
    else
    {
        DelegateBinding = NewObject<UWidgetAnimationDelegateBinding>(BPGC, UWidgetAnimationDelegateBinding::StaticClass());
        BPGC->DynamicBindingObjects.Add(DelegateBinding);
    }

    const FString FuncName = FString::Printf(TEXT("%s_Play%s"), *WidgetEvent, *AnimName);

    FBlueprintWidgetAnimationDelegateBinding NewEntry;
    NewEntry.Action = AnimEventEnum;
    NewEntry.AnimationToBind = FName(*AnimName);
    NewEntry.FunctionNameToBind = FName(*FuncName);
    NewEntry.UserTag = NAME_None;

    DelegateBinding->WidgetAnimationDelegateBindings.Add(NewEntry);

    WBP->MarkPackageDirty();

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimName);
    Result->SetStringField(TEXT("widget_event"), WidgetEvent);
    Result->SetStringField(TEXT("animation_event"), AnimationEvent);
    Result->SetStringField(TEXT("function_name_bound"), FuncName);
    Result->SetBoolField(TEXT("binding_created"), true);
    return FMonolithActionResult::Success(Result);
#else
    return FMonolithActionResult::Error(TEXT("Animation delegate binding requires editor (WITH_EDITORONLY_DATA)"), -32603);
#endif
}


void MonolithUI::FAnimationEventActions::Register(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("add_animation_event_track"),
        TEXT("Adds a UMovieSceneEventTrack (master track, not bound to a widget) to an existing "
             "UWidgetAnimation on a WBP. Inserts timed FMovieSceneEvent keys for animation lifecycle events. "
             "Params: asset_path (string, /Game/... WBP path), animation_name (string, must exist), "
             "events (array of { time: number (seconds), event_name: string })."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FAnimationEventActions::HandleAddAnimationEventTrack));

    Registry.RegisterAction(
        TEXT("ui"),
        TEXT("bind_animation_to_event"),
        TEXT("Creates a UWidgetAnimationDelegateBinding entry that wires a widget interaction event "
             "to trigger a named animation. The binding is stored on the WBP's generated class. "
             "Params: asset_path (string), animation_name (string, must exist), "
             "widget_event (string, one of: OnHovered, OnUnhovered, OnPressed, OnReleased, OnFocusReceived, OnFocusLost), "
             "animation_event (string, optional, 'Started' or 'Finished', default 'Started')."),
        FMonolithActionHandler::CreateStatic(&MonolithUI::FAnimationEventActions::HandleBindAnimationToEvent));
}
