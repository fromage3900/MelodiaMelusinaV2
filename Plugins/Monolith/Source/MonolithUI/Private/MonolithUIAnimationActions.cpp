// MonolithUIAnimationActions.cpp
#include "MonolithUIAnimationActions.h"
#include "MonolithUIInternal.h"
#include "MonolithParamSchema.h"
#include "Animation/WidgetAnimation.h"
#include "MovieScene.h"
#include "MovieScenePossessable.h"
#include "MovieSceneSpawnable.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Channels/MovieSceneFloatChannel.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Channels/MovieSceneChannelProxy.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

namespace
{
    FString ResolveBindingName(UMovieScene* MovieScene, const FMovieSceneBinding& Binding)
    {
        if (!MovieScene)
        {
            return FString();
        }

        const FGuid& BindingGuid = Binding.GetObjectGuid();
        for (int32 PossessableIndex = 0; PossessableIndex < MovieScene->GetPossessableCount(); ++PossessableIndex)
        {
            const FMovieScenePossessable& Possessable = MovieScene->GetPossessable(PossessableIndex);
            if (Possessable.GetGuid() == BindingGuid)
            {
                return Possessable.GetName();
            }
        }

        for (int32 SpawnableIndex = 0; SpawnableIndex < MovieScene->GetSpawnableCount(); ++SpawnableIndex)
        {
            const FMovieSceneSpawnable& Spawnable = MovieScene->GetSpawnable(SpawnableIndex);
            if (Spawnable.GetGuid() == BindingGuid)
            {
                return Spawnable.GetName();
            }
        }

        return BindingGuid.ToString(EGuidFormats::DigitsWithHyphensLower);
    }

    FGuid FindOrCreateWidgetAnimationBinding(UWidgetBlueprint* WBP, UWidgetAnimation* Animation, UMovieScene* MovieScene, UWidget* TargetWidget)
    {
        if (!WBP || !Animation || !MovieScene || !TargetWidget)
        {
            return FGuid();
        }

        const FName WidgetFName = TargetWidget->GetFName();

        for (const FWidgetAnimationBinding& Binding : Animation->AnimationBindings)
        {
            if (Binding.WidgetName == WidgetFName)
            {
                return Binding.AnimationGuid;
            }
        }

        for (int32 PossessableIndex = 0; PossessableIndex < MovieScene->GetPossessableCount(); ++PossessableIndex)
        {
            const FMovieScenePossessable& Possessable = MovieScene->GetPossessable(PossessableIndex);
            if (Possessable.GetName() == WidgetFName.ToString())
            {
                FWidgetAnimationBinding Binding;
                Binding.AnimationGuid = Possessable.GetGuid();
                Binding.WidgetName = WidgetFName;
                Binding.SlotWidgetName = NAME_None;
                Binding.bIsRootWidget = (WBP->WidgetTree && WBP->WidgetTree->RootWidget == TargetWidget);
                Animation->AnimationBindings.Add(Binding);
                return Binding.AnimationGuid;
            }
        }

        const FGuid NewGuid = MovieScene->AddPossessable(WidgetFName.ToString(), TargetWidget->GetClass());

        FWidgetAnimationBinding Binding;
        Binding.AnimationGuid = NewGuid;
        Binding.WidgetName = WidgetFName;
        Binding.SlotWidgetName = NAME_None;
        Binding.bIsRootWidget = (WBP->WidgetTree && WBP->WidgetTree->RootWidget == TargetWidget);
        Animation->AnimationBindings.Add(Binding);
        return NewGuid;
    }

    UMovieSceneFloatTrack* FindOrCreateFloatTrack(
        UMovieScene* MovieScene,
        const FGuid& PossessableGuid,
        const FName& PropertyName,
        const FString& PropertyPath,
        const FFrameNumber& StartFrame,
        const FFrameNumber& EndFrame)
    {
        if (!MovieScene || !PossessableGuid.IsValid())
        {
            return nullptr;
        }

        const FMovieSceneBinding* Binding = static_cast<const UMovieScene*>(MovieScene)->FindBinding(PossessableGuid);
        if (Binding)
        {
            for (UMovieSceneTrack* Track : Binding->GetTracks())
            {
                UMovieSceneFloatTrack* FloatTrack = Cast<UMovieSceneFloatTrack>(Track);
                if (FloatTrack && FloatTrack->GetPropertyPath().ToString() == PropertyPath)
                {
                    return FloatTrack;
                }
            }
        }

        UMovieSceneFloatTrack* FloatTrack = MovieScene->AddTrack<UMovieSceneFloatTrack>(PossessableGuid);
        if (!FloatTrack)
        {
            return nullptr;
        }

        FloatTrack->SetPropertyNameAndPath(PropertyName, *PropertyPath);

        UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(FloatTrack->CreateNewSection());
        if (!Section)
        {
            return nullptr;
        }

        Section->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
        FloatTrack->AddSection(*Section);
        return FloatTrack;
    }

    UMovieSceneFloatTrack* FindOrCreateOpacityTrack(
        UMovieScene* MovieScene,
        const FGuid& PossessableGuid,
        const FFrameNumber& StartFrame,
        const FFrameNumber& EndFrame)
    {
        return FindOrCreateFloatTrack(
            MovieScene,
            PossessableGuid,
            FName(TEXT("RenderOpacity")),
            TEXT("RenderOpacity"),
            StartFrame,
            EndFrame);
    }
}

void FMonolithUIAnimationActions::RegisterActions(FMonolithToolRegistry& Registry)
{
    Registry.RegisterAction(
        TEXT("ui"), TEXT("list_animations"),
        TEXT("List all UWidgetAnimation assets on a Widget Blueprint"),
        FMonolithActionHandler::CreateStatic(&HandleListAnimations),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("get_animation_details"),
        TEXT("Get tracks and keyframes for a specific animation on a Widget Blueprint"),
        FMonolithActionHandler::CreateStatic(&HandleGetAnimationDetails),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("animation_name"), TEXT("string"), TEXT("Name of the UWidgetAnimation"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("create_animation"),
        TEXT("[DEPRECATED -- use ui::create_animation_v2 instead] Create a new UWidgetAnimation with tracks and keyframes on a Widget Blueprint. Scheduled for removal one major release out (Phase L marker, 2026-04-26). Response payload is tagged {deprecated: true, use_action: \"ui::create_animation_v2\"}; the v2 surface supports multi-track + cubic / weighted-tangent interpolation that v1 cannot express."),
        FMonolithActionHandler::CreateStatic(&HandleCreateAnimation),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("animation_name"), TEXT("string"), TEXT("Name for the new animation"))
            .Required(TEXT("duration"), TEXT("number"), TEXT("Animation duration in seconds"))
            .Optional(TEXT("tracks"), TEXT("array"), TEXT("Array of track definitions: [{\"widget_name\": \"MyWidget\", \"property\": \"opacity|transform|color\", \"keyframes\": [{\"time\": 0.0, \"value\": 1.0}]}]"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("add_animation_keyframe"),
        TEXT("[DEPRECATED -- use ui::create_animation_v2 (multi-key authoring) or ui::add_bezier_eased_segment instead] Add a single keyframe to an existing animation track. Scheduled for removal one major release out (Phase L marker, 2026-04-26). Response payload is tagged {deprecated: true, use_action: \"ui::create_animation_v2\"}; the v2 surface authors entire tracks at once and supports the cubic / weighted-tangent shapes that v1 cannot express."),
        FMonolithActionHandler::CreateStatic(&HandleAddAnimationKeyframe),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("animation_name"), TEXT("string"), TEXT("Name of the UWidgetAnimation"))
            .Required(TEXT("widget_name"), TEXT("string"), TEXT("Target widget name"))
            .Required(TEXT("property"), TEXT("string"), TEXT("Property: opacity, transform, color"))
            .Optional(TEXT("component"), TEXT("string"), TEXT("For transform: tx, ty, angle, sx, sy. For color: r, g, b, a"))
            .Required(TEXT("time"), TEXT("number"), TEXT("Keyframe time in seconds"))
            .Required(TEXT("value"), TEXT("number"), TEXT("Keyframe value for the selected property/component"))
            .Build()
    );

    Registry.RegisterAction(
        TEXT("ui"), TEXT("remove_animation"),
        TEXT("Remove a UWidgetAnimation from a Widget Blueprint"),
        FMonolithActionHandler::CreateStatic(&HandleRemoveAnimation),
        FParamSchemaBuilder()
            .RequiredAssetPath(TEXT("asset_path"), TEXT("Widget Blueprint asset path"))
            .Required(TEXT("animation_name"), TEXT("string"), TEXT("Name of the animation to remove"))
            .Build()
    );
}

// --- list_animations ---
FMonolithActionResult FMonolithUIAnimationActions::HandleListAnimations(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    TArray<TSharedPtr<FJsonValue>> AnimArray;

    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (!Anim) continue;

        TSharedPtr<FJsonObject> AnimObj = MakeShared<FJsonObject>();
        AnimObj->SetStringField(TEXT("name"), Anim->GetName());

        UMovieScene* MovieScene = Anim->GetMovieScene();
        if (MovieScene)
        {
            const UMovieScene* ConstMovieScene = MovieScene;
            FFrameRate TickRes = MovieScene->GetTickResolution();
            TRange<FFrameNumber> PlayRange = MovieScene->GetPlaybackRange();

            double StartTime = PlayRange.GetLowerBoundValue().Value / TickRes.AsDecimal();
            double EndTime = PlayRange.GetUpperBoundValue().Value / TickRes.AsDecimal();

            AnimObj->SetNumberField(TEXT("start_time"), StartTime);
            AnimObj->SetNumberField(TEXT("end_time"), EndTime);
            AnimObj->SetNumberField(TEXT("binding_count"), ConstMovieScene->GetBindings().Num());
        }

        AnimArray.Add(MakeShared<FJsonValueObject>(AnimObj));
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetArrayField(TEXT("animations"), AnimArray);
    Result->SetNumberField(TEXT("count"), AnimArray.Num());
    return FMonolithActionResult::Success(Result);
}

// --- get_animation_details ---
FMonolithActionResult FMonolithUIAnimationActions::HandleGetAnimationDetails(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString AnimationName = Params->GetStringField(TEXT("animation_name"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    // Find the animation by name
    UWidgetAnimation* TargetAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetName() == AnimationName)
        {
            TargetAnim = Anim;
            break;
        }
    }

    if (!TargetAnim)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Animation '%s' not found on '%s'"), *AnimationName, *AssetPath));
    }

    UMovieScene* MovieScene = TargetAnim->GetMovieScene();
    if (!MovieScene)
    {
        return FMonolithActionResult::Error(TEXT("Animation has no MovieScene"));
    }

    FFrameRate TickRes = MovieScene->GetTickResolution();

    // Iterate all tracks
    TArray<TSharedPtr<FJsonValue>> TrackArray;
    for (UMovieSceneTrack* Track : MovieScene->GetTracks())
    {
        if (!Track) continue;

        TSharedPtr<FJsonObject> TrackObj = MakeShared<FJsonObject>();
        TrackObj->SetStringField(TEXT("track_type"), Track->GetClass()->GetName());

        // Get sections
        TArray<TSharedPtr<FJsonValue>> SectionArray;
        for (UMovieSceneSection* Section : Track->GetAllSections())
        {
            if (!Section) continue;

            TSharedPtr<FJsonObject> SecObj = MakeShared<FJsonObject>();

            TRange<FFrameNumber> SectionRange = Section->GetRange();
            if (SectionRange.HasLowerBound())
            {
                SecObj->SetNumberField(TEXT("start_time"),
                    SectionRange.GetLowerBoundValue().Value / TickRes.AsDecimal());
            }
            if (SectionRange.HasUpperBound())
            {
                SecObj->SetNumberField(TEXT("end_time"),
                    SectionRange.GetUpperBoundValue().Value / TickRes.AsDecimal());
            }

            // Count keyframes across all channels
            int32 TotalKeys = 0;
            FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
            for (const FMovieSceneChannelEntry& Entry : ChannelProxy.GetAllEntries())
            {
                for (FMovieSceneChannel* Channel : Entry.GetChannels())
                {
                    if (Channel)
                    {
                        TotalKeys += Channel->GetNumKeys();
                    }
                }
            }
            SecObj->SetNumberField(TEXT("keyframe_count"), TotalKeys);

            SectionArray.Add(MakeShared<FJsonValueObject>(SecObj));
        }
        TrackObj->SetArrayField(TEXT("sections"), SectionArray);

        TrackArray.Add(MakeShared<FJsonValueObject>(TrackObj));
    }

    // Also iterate bound object tracks
    const UMovieScene* ConstMovieScene = MovieScene;
    for (const FMovieSceneBinding& Binding : ConstMovieScene->GetBindings())
    {
        for (UMovieSceneTrack* Track : Binding.GetTracks())
        {
            if (!Track) continue;

            TSharedPtr<FJsonObject> TrackObj = MakeShared<FJsonObject>();
            TrackObj->SetStringField(TEXT("binding_name"), ResolveBindingName(MovieScene, Binding));
            TrackObj->SetStringField(TEXT("track_type"), Track->GetClass()->GetName());

            TArray<TSharedPtr<FJsonValue>> SectionArray;
            for (UMovieSceneSection* Section : Track->GetAllSections())
            {
                if (!Section) continue;

                TSharedPtr<FJsonObject> SecObj = MakeShared<FJsonObject>();
                TRange<FFrameNumber> SectionRange = Section->GetRange();
                if (SectionRange.HasLowerBound())
                {
                    SecObj->SetNumberField(TEXT("start_time"),
                        SectionRange.GetLowerBoundValue().Value / TickRes.AsDecimal());
                }
                if (SectionRange.HasUpperBound())
                {
                    SecObj->SetNumberField(TEXT("end_time"),
                        SectionRange.GetUpperBoundValue().Value / TickRes.AsDecimal());
                }

                int32 TotalKeys = 0;
                FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
                for (const FMovieSceneChannelEntry& Entry : ChannelProxy.GetAllEntries())
                {
                    for (FMovieSceneChannel* Channel : Entry.GetChannels())
                    {
                        if (Channel)
                        {
                            TotalKeys += Channel->GetNumKeys();
                        }
                    }
                }
                SecObj->SetNumberField(TEXT("keyframe_count"), TotalKeys);

                SectionArray.Add(MakeShared<FJsonValueObject>(SecObj));
            }
            TrackObj->SetArrayField(TEXT("sections"), SectionArray);

            TrackArray.Add(MakeShared<FJsonValueObject>(TrackObj));
        }
    }

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimationName);
    Result->SetArrayField(TEXT("tracks"), TrackArray);
    Result->SetNumberField(TEXT("track_count"), TrackArray.Num());
    return FMonolithActionResult::Success(Result);
}

// --- create_animation ---
FMonolithActionResult FMonolithUIAnimationActions::HandleCreateAnimation(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString AnimationName = Params->GetStringField(TEXT("animation_name"));
    double Duration = Params->GetNumberField(TEXT("duration"));

    if (AnimationName.IsEmpty())
    {
        return FMonolithActionResult::Error(TEXT("Missing required param: animation_name"));
    }
    if (Duration <= 0.0)
    {
        return FMonolithActionResult::Error(TEXT("Duration must be > 0"));
    }

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    // Check for duplicate name
    for (UWidgetAnimation* Existing : WBP->Animations)
    {
        if (Existing && Existing->GetName() == AnimationName)
        {
            return FMonolithActionResult::Error(
                FString::Printf(TEXT("Animation '%s' already exists"), *AnimationName));
        }
    }

    // Create the UWidgetAnimation as a subobject of the WBP
    UWidgetAnimation* NewAnim = NewObject<UWidgetAnimation>(
        WBP, FName(*AnimationName), RF_Transactional);

    // Create the UMovieScene
    UMovieScene* MovieScene = NewObject<UMovieScene>(
        NewAnim, NewAnim->GetFName(), RF_Transactional);
    NewAnim->MovieScene = MovieScene;

    // Configure tick resolution and display rate
    // UE 5.7 standard: 60000 tick resolution, 30fps display
    FFrameRate TickResolution(60000, 1);
    FFrameRate DisplayRate(30, 1);
    MovieScene->SetTickResolutionDirectly(TickResolution);
    MovieScene->SetDisplayRate(DisplayRate);

    // Set playback range
    FFrameNumber StartFrame(0);
    FFrameNumber EndFrame(FMath::RoundToInt32(Duration * TickResolution.AsDecimal()));
    MovieScene->SetPlaybackRange(
        TRange<FFrameNumber>(StartFrame, EndFrame));

    int32 TrackCount = 0;
    int32 KeyframeCount = 0;

    // Process tracks array if provided
    const TArray<TSharedPtr<FJsonValue>>* TracksArray = nullptr;
    if (Params->TryGetArrayField(TEXT("tracks"), TracksArray) && TracksArray)
    {
        for (const TSharedPtr<FJsonValue>& TrackVal : *TracksArray)
        {
            const TSharedPtr<FJsonObject>* TrackObjPtr = nullptr;
            if (!TrackVal->TryGetObject(TrackObjPtr) || !TrackObjPtr || !(*TrackObjPtr).IsValid())
            {
                continue;
            }
            const TSharedPtr<FJsonObject>& TrackObj = *TrackObjPtr;

            FString WidgetName = TrackObj->GetStringField(TEXT("widget_name"));
            FString Property = TrackObj->GetStringField(TEXT("property"));

            if (WidgetName.IsEmpty() || Property.IsEmpty()) continue;

            // Find the widget in the tree
            UWidget* TargetWidget = WBP->WidgetTree
                ? WBP->WidgetTree->FindWidget(FName(*WidgetName))
                : nullptr;
            if (!TargetWidget)
            {
                continue; // Skip tracks for widgets that don't exist
            }

            // Find or create possessable for this widget
            const FGuid PossessableGuid = FindOrCreateWidgetAnimationBinding(WBP, NewAnim, MovieScene, TargetWidget);
            if (!PossessableGuid.IsValid())
            {
                continue;
            }

            // Create a float track for the property
            if (Property == TEXT("opacity"))
            {
                // Create a float track bound to RenderOpacity
                UMovieSceneFloatTrack* FloatTrack = FindOrCreateOpacityTrack(MovieScene, PossessableGuid, StartFrame, EndFrame);
                if (!FloatTrack) continue;

                // Get the float channel and add keyframes
                UMovieSceneSection* Section = FloatTrack->GetAllSections().Num() > 0 ? FloatTrack->GetAllSections()[0] : nullptr;
                if (!Section) continue;

                FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
                FMovieSceneFloatChannel* Channel = ChannelProxy.GetChannel<FMovieSceneFloatChannel>(0);
                if (!Channel) continue;

                const TArray<TSharedPtr<FJsonValue>>* KeyframesArray = nullptr;
                if (TrackObj->TryGetArrayField(TEXT("keyframes"), KeyframesArray) && KeyframesArray)
                {
                    for (const TSharedPtr<FJsonValue>& KfVal : *KeyframesArray)
                    {
                        const TSharedPtr<FJsonObject>* KfObjPtr = nullptr;
                        if (!KfVal->TryGetObject(KfObjPtr) || !KfObjPtr || !(*KfObjPtr).IsValid())
                        {
                            continue;
                        }
                        const TSharedPtr<FJsonObject>& KfObj = *KfObjPtr;

                        double Time = KfObj->GetNumberField(TEXT("time"));
                        double Value = KfObj->GetNumberField(TEXT("value"));

                        FFrameNumber KeyFrame(
                            FMath::RoundToInt32(Time * TickResolution.AsDecimal()));
                        Channel->AddLinearKey(KeyFrame, static_cast<float>(Value));
                        KeyframeCount++;
                    }
                }

                TrackCount++;
            }
            else if (Property == TEXT("transform"))
            {
                // Transform tracks use MovieScene3DTransformTrack for translation/rotation/scale
                // For UMG we use float tracks on RenderTransform sub-properties
                // Create separate float tracks for TranslationX, TranslationY, Angle, ScaleX, ScaleY

                FString SubProperties[] = {
                    TEXT("RenderTransform.Translation.X"),
                    TEXT("RenderTransform.Translation.Y"),
                    TEXT("RenderTransform.Angle"),
                    TEXT("RenderTransform.Scale.X"),
                    TEXT("RenderTransform.Scale.Y")
                };
                FString SubPropertyNames[] = {
                    TEXT("Translation X"), TEXT("Translation Y"),
                    TEXT("Angle"),
                    TEXT("Scale X"), TEXT("Scale Y")
                };

                // For transform, keyframes contain {time, tx, ty, angle, sx, sy}
                // Create one float track per sub-property, each with matching keyframes
                for (int32 SubIdx = 0; SubIdx < 5; ++SubIdx)
                {
                    UMovieSceneFloatTrack* FloatTrack = MovieScene->AddTrack<UMovieSceneFloatTrack>(PossessableGuid);
                    if (!FloatTrack) continue;

                    FloatTrack->SetPropertyNameAndPath(
                        FName(*SubPropertyNames[SubIdx]), *SubProperties[SubIdx]);

                    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(
                        FloatTrack->CreateNewSection());
                    if (!Section) continue;

                    Section->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
                    FloatTrack->AddSection(*Section);

                    FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
                    FMovieSceneFloatChannel* Channel = ChannelProxy.GetChannel<FMovieSceneFloatChannel>(0);
                    if (!Channel) continue;

                    const TArray<TSharedPtr<FJsonValue>>* KeyframesArray = nullptr;
                    if (TrackObj->TryGetArrayField(TEXT("keyframes"), KeyframesArray) && KeyframesArray)
                    {
                        FString FieldNames[] = {
                            TEXT("tx"), TEXT("ty"), TEXT("angle"), TEXT("sx"), TEXT("sy")
                        };
                        double Defaults[] = { 0.0, 0.0, 0.0, 1.0, 1.0 };

                        for (const TSharedPtr<FJsonValue>& KfVal : *KeyframesArray)
                        {
                            const TSharedPtr<FJsonObject>* KfObjPtr = nullptr;
                            if (!KfVal->TryGetObject(KfObjPtr) || !KfObjPtr || !(*KfObjPtr).IsValid())
                            {
                                continue;
                            }
                            const TSharedPtr<FJsonObject>& KfObj = *KfObjPtr;

                            double Time = KfObj->GetNumberField(TEXT("time"));
                            double Value = Defaults[SubIdx];
                            if (KfObj->HasField(FieldNames[SubIdx]))
                            {
                                Value = KfObj->GetNumberField(FieldNames[SubIdx]);
                            }

                            FFrameNumber KeyFrame(
                                FMath::RoundToInt32(Time * TickResolution.AsDecimal()));
                            Channel->AddLinearKey(KeyFrame, static_cast<float>(Value));
                            KeyframeCount++;
                        }
                    }

                    TrackCount++;
                }
            }
            else if (Property == TEXT("color"))
            {
                // Color tracks: R, G, B, A float channels on ColorAndOpacity
                FString SubProperties[] = {
                    TEXT("ColorAndOpacity.R"),
                    TEXT("ColorAndOpacity.G"),
                    TEXT("ColorAndOpacity.B"),
                    TEXT("ColorAndOpacity.A")
                };
                FString SubPropertyNames[] = {
                    TEXT("Color R"), TEXT("Color G"), TEXT("Color B"), TEXT("Color A")
                };

                for (int32 SubIdx = 0; SubIdx < 4; ++SubIdx)
                {
                    UMovieSceneFloatTrack* FloatTrack = MovieScene->AddTrack<UMovieSceneFloatTrack>(PossessableGuid);
                    if (!FloatTrack) continue;

                    FloatTrack->SetPropertyNameAndPath(
                        FName(*SubPropertyNames[SubIdx]), *SubProperties[SubIdx]);

                    UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(
                        FloatTrack->CreateNewSection());
                    if (!Section) continue;

                    Section->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
                    FloatTrack->AddSection(*Section);

                    FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
                    FMovieSceneFloatChannel* Channel = ChannelProxy.GetChannel<FMovieSceneFloatChannel>(0);
                    if (!Channel) continue;

                    const TArray<TSharedPtr<FJsonValue>>* KeyframesArray = nullptr;
                    if (TrackObj->TryGetArrayField(TEXT("keyframes"), KeyframesArray) && KeyframesArray)
                    {
                        FString FieldNames[] = {
                            TEXT("r"), TEXT("g"), TEXT("b"), TEXT("a")
                        };
                        double Defaults[] = { 1.0, 1.0, 1.0, 1.0 };

                        for (const TSharedPtr<FJsonValue>& KfVal : *KeyframesArray)
                        {
                            const TSharedPtr<FJsonObject>* KfObjPtr = nullptr;
                            if (!KfVal->TryGetObject(KfObjPtr) || !KfObjPtr || !(*KfObjPtr).IsValid())
                            {
                                continue;
                            }
                            const TSharedPtr<FJsonObject>& KfObj = *KfObjPtr;

                            double Time = KfObj->GetNumberField(TEXT("time"));
                            double Value = Defaults[SubIdx];
                            if (KfObj->HasField(FieldNames[SubIdx]))
                            {
                                Value = KfObj->GetNumberField(FieldNames[SubIdx]);
                            }

                            FFrameNumber KeyFrame(
                                FMath::RoundToInt32(Time * TickResolution.AsDecimal()));
                            Channel->AddLinearKey(KeyFrame, static_cast<float>(Value));
                            KeyframeCount++;
                        }
                    }

                    TrackCount++;
                }
            }
            else
            {
                // Unknown property — skip with no error (lenient)
                continue;
            }
        }
    }

    // Add the animation to the widget blueprint
    WBP->Animations.Add(NewAnim);

    // Mirror editor bookkeeping so the compiler sees a GUID for the final animation name.
    MonolithUIInternal::RegisterVariableName(WBP, NewAnim->GetFName());

    // Mark modified and compile
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
    FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimationName);
    Result->SetNumberField(TEXT("duration"), Duration);
    Result->SetNumberField(TEXT("tracks_created"), TrackCount);
    Result->SetNumberField(TEXT("keyframes_created"), KeyframeCount);
    Result->SetBoolField(TEXT("compiled"), true);
    // Phase L deprecation hint -- v1 surface scheduled for removal one major release out.
    // Same {deprecated, use_action} payload shape used elsewhere in the registry for
    // cross-namespace alias deprecation, so callers can branch on a single tag.
    Result->SetBoolField(TEXT("deprecated"), true);
    Result->SetStringField(TEXT("use_action"), TEXT("ui::create_animation_v2"));
    return FMonolithActionResult::Success(Result);
}

// --- add_animation_keyframe ---
FMonolithActionResult FMonolithUIAnimationActions::HandleAddAnimationKeyframe(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString AnimationName = Params->GetStringField(TEXT("animation_name"));
    FString WidgetName = Params->GetStringField(TEXT("widget_name"));
    FString Property = Params->GetStringField(TEXT("property"));
    FString Component = Params->HasField(TEXT("component")) ? Params->GetStringField(TEXT("component")) : FString();
    double Time = Params->GetNumberField(TEXT("time"));
    double Value = Params->GetNumberField(TEXT("value"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    // Find the animation
    UWidgetAnimation* TargetAnim = nullptr;
    for (UWidgetAnimation* Anim : WBP->Animations)
    {
        if (Anim && Anim->GetName() == AnimationName)
        {
            TargetAnim = Anim;
            break;
        }
    }
    if (!TargetAnim)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Animation '%s' not found"), *AnimationName));
    }

    UMovieScene* MovieScene = TargetAnim->GetMovieScene();
    if (!MovieScene)
    {
        return FMonolithActionResult::Error(TEXT("Animation has no MovieScene"));
    }

    FFrameRate TickRes = MovieScene->GetTickResolution();
    FFrameNumber KeyFrame(FMath::RoundToInt32(Time * TickRes.AsDecimal()));

    // Determine the property path to match
    FString PropertyPath;
    FName TrackPropertyName = NAME_None;
    if (Property == TEXT("opacity"))
    {
        PropertyPath = TEXT("RenderOpacity");
        TrackPropertyName = FName(TEXT("RenderOpacity"));
    }
    else if (Property == TEXT("transform"))
    {
        if (Component == TEXT("tx"))
        {
            PropertyPath = TEXT("RenderTransform.Translation.X");
            TrackPropertyName = FName(TEXT("Translation X"));
        }
        else if (Component == TEXT("ty"))
        {
            PropertyPath = TEXT("RenderTransform.Translation.Y");
            TrackPropertyName = FName(TEXT("Translation Y"));
        }
        else if (Component == TEXT("angle"))
        {
            PropertyPath = TEXT("RenderTransform.Angle");
            TrackPropertyName = FName(TEXT("Angle"));
        }
        else if (Component == TEXT("sx"))
        {
            PropertyPath = TEXT("RenderTransform.Scale.X");
            TrackPropertyName = FName(TEXT("Scale X"));
        }
        else if (Component == TEXT("sy"))
        {
            PropertyPath = TEXT("RenderTransform.Scale.Y");
            TrackPropertyName = FName(TEXT("Scale Y"));
        }
        else
        {
            return FMonolithActionResult::Error(
                TEXT("For property 'transform', component must be one of: tx, ty, angle, sx, sy"));
        }
    }
    else if (Property == TEXT("color"))
    {
        if (Component == TEXT("r"))
        {
            PropertyPath = TEXT("ColorAndOpacity.R");
            TrackPropertyName = FName(TEXT("Color R"));
        }
        else if (Component == TEXT("g"))
        {
            PropertyPath = TEXT("ColorAndOpacity.G");
            TrackPropertyName = FName(TEXT("Color G"));
        }
        else if (Component == TEXT("b"))
        {
            PropertyPath = TEXT("ColorAndOpacity.B");
            TrackPropertyName = FName(TEXT("Color B"));
        }
        else if (Component == TEXT("a"))
        {
            PropertyPath = TEXT("ColorAndOpacity.A");
            TrackPropertyName = FName(TEXT("Color A"));
        }
        else
        {
            return FMonolithActionResult::Error(
                TEXT("For property 'color', component must be one of: r, g, b, a"));
        }
    }
    else
    {
        return FMonolithActionResult::Error(
            TEXT("add_animation_keyframe supports properties: opacity, transform, color"));
    }

    UWidget* TargetWidget = WBP->WidgetTree ? WBP->WidgetTree->FindWidget(FName(*WidgetName)) : nullptr;
    if (!TargetWidget)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Widget '%s' not found"), *WidgetName));
    }

    const TRange<FFrameNumber> PlaybackRange = MovieScene->GetPlaybackRange();
    const FFrameNumber StartFrame = PlaybackRange.GetLowerBoundValue();
    const FFrameNumber EndFrame = PlaybackRange.GetUpperBoundValue();
    const FGuid PossessableGuid = FindOrCreateWidgetAnimationBinding(WBP, TargetAnim, MovieScene, TargetWidget);
    if (!PossessableGuid.IsValid())
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Unable to create animation binding for widget '%s'"), *WidgetName));
    }

    UMovieSceneFloatTrack* FloatTrack = FindOrCreateFloatTrack(
        MovieScene,
        PossessableGuid,
        TrackPropertyName,
        PropertyPath,
        StartFrame,
        EndFrame);
    if (!FloatTrack)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Unable to create %s track for widget '%s'"), *PropertyPath, *WidgetName));
    }

    for (UMovieSceneSection* Section : FloatTrack->GetAllSections())
    {
        FMovieSceneChannelProxy& ChannelProxy = Section->GetChannelProxy();
        FMovieSceneFloatChannel* Channel = ChannelProxy.GetChannel<FMovieSceneFloatChannel>(0);
        if (!Channel)
        {
            continue;
        }

        Channel->AddLinearKey(KeyFrame, static_cast<float>(Value));

        FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
        FKismetEditorUtilities::CompileBlueprint(WBP);

        TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
        Result->SetStringField(TEXT("asset_path"), AssetPath);
        Result->SetStringField(TEXT("animation_name"), AnimationName);
        Result->SetStringField(TEXT("widget_name"), WidgetName);
        Result->SetStringField(TEXT("property"), Property);
        if (!Component.IsEmpty())
        {
            Result->SetStringField(TEXT("component"), Component);
        }
        Result->SetNumberField(TEXT("time"), Time);
        Result->SetNumberField(TEXT("value"), Value);
        Result->SetBoolField(TEXT("binding_created"), true);
        Result->SetBoolField(TEXT("track_created"), true);
        Result->SetBoolField(TEXT("added"), true);
        // Phase L deprecation hint -- v1 surface scheduled for removal one major release out.
        Result->SetBoolField(TEXT("deprecated"), true);
        Result->SetStringField(TEXT("use_action"), TEXT("ui::create_animation_v2"));
        return FMonolithActionResult::Success(Result);
    }

    return FMonolithActionResult::Error(
        FString::Printf(TEXT("No section channel found for property '%s' on widget '%s'"), *Property, *WidgetName));
}

// --- remove_animation ---
FMonolithActionResult FMonolithUIAnimationActions::HandleRemoveAnimation(const TSharedPtr<FJsonObject>& Params)
{
    FString AssetPath = Params->GetStringField(TEXT("asset_path"));
    FString AnimationName = Params->GetStringField(TEXT("animation_name"));

    FMonolithActionResult Err;
    UWidgetBlueprint* WBP = MonolithUIInternal::LoadWidgetBlueprint(AssetPath, Err);
    if (!WBP) return Err;

    // Find and remove the animation
    int32 FoundIndex = INDEX_NONE;
    FGuid AnimGuid;
    for (int32 i = 0; i < WBP->Animations.Num(); ++i)
    {
        if (WBP->Animations[i] && WBP->Animations[i]->GetName() == AnimationName)
        {
            FoundIndex = i;

            // Find the GUID from animation bindings to clean up
            UMovieScene* MovieScene = WBP->Animations[i]->GetMovieScene();
            if (MovieScene)
            {
                for (int32 p = 0; p < MovieScene->GetPossessableCount(); ++p)
                {
                    AnimGuid = MovieScene->GetPossessable(p).GetGuid();
                    break; // We just need one to identify bindings
                }
            }
            break;
        }
    }

    if (FoundIndex == INDEX_NONE)
    {
        return FMonolithActionResult::Error(
            FString::Printf(TEXT("Animation '%s' not found"), *AnimationName));
    }

    // AnimationBindings live on the UWidgetAnimation itself, not the WBP.
    // Since we're removing the animation entirely, its bindings go with it.

    if (WBP->WidgetVariableNameToGuidMap.Contains(FName(*AnimationName)))
    {
        WBP->OnVariableRemoved(FName(*AnimationName));
    }

    // Remove the animation object
    WBP->Animations.RemoveAt(FoundIndex);

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
    FKismetEditorUtilities::CompileBlueprint(WBP);

    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("asset_path"), AssetPath);
    Result->SetStringField(TEXT("animation_name"), AnimationName);
    Result->SetBoolField(TEXT("removed"), true);
    Result->SetBoolField(TEXT("compiled"), true);
    return FMonolithActionResult::Success(Result);
}
