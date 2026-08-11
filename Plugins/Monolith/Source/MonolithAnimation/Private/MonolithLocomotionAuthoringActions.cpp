#include "MonolithLocomotionAuthoringActions.h"
#include "MonolithAssetUtils.h"
#include "MonolithParamSchema.h"

#include "Animation/AnimSequence.h"                 // UAnimSequence, HasRootMotion, ExtractRootMotionFromRange, FAnimExtractContext
#include "AnimationModifier.h"                       // UAnimationModifier::ApplyToAnimationSequence
#include "AnimationModifiersAssetUserData.h"         // UAnimationModifiersAssetUserData::AddAnimationModifierOfClass / GetAnimationModifierInstances
#include "AnimationBlueprintLibrary.h"               // DoesCurveExist / RemoveCurve, ERawCurveTrackTypes
#include "UObject/UnrealType.h"                      // FProperty reflective set (CurveName / Axis / bStopAtEnd / SampleRate / StopSpeedThreshold)
#include "UObject/EnumProperty.h"
#include "Templates/SubclassOf.h"
#include "Math/UnrealMathUtility.h"
#include "Editor.h"

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

void FMonolithLocomotionAuthoringActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// T1-L2 — get_root_motion_speed
	Registry.RegisterAction(TEXT("animation"), TEXT("get_root_motion_speed"),
		TEXT("Compute the root-motion translation speed (cm/s) of an AnimSequence by extracting root motion over the clip. ")
		TEXT("Returns an explicit 'speed unknowable' signal when root motion is disabled / root-locked / the extracted delta is zero, rather than reporting 0."),
		FMonolithActionHandler::CreateStatic(&HandleGetRootMotionSpeed),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_path"), TEXT("UAnimSequence asset path to measure"))
			.Optional(TEXT("mode"), TEXT("string"), TEXT("average | peak | per_frame — how to summarise speed across the clip (default average)"))
			.Optional(TEXT("sample_rate"), TEXT("integer"), TEXT("Per-frame sampling rate in Hz for peak/per_frame modes (default 30)"))
			.Build());

	// T1-L3 — bake_distance_curve
	Registry.RegisterAction(TEXT("animation"), TEXT("bake_distance_curve"),
		TEXT("Reflectively construct + configure a UDistanceCurveModifier (AnimationLocomotionLibrary plugin), register it into the asset's ")
		TEXT("AnimationModifiers stack so it persists, then apply it to bake a distance curve. Removes any pre-existing curve of the target ")
		TEXT("name first to avoid the engine duplicate-key assert. No typed dependency on the locomotion plugin — resolved by class name."),
		FMonolithActionHandler::CreateStatic(&HandleBakeDistanceCurve),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("anim_path"), TEXT("UAnimSequence asset path to bake the distance curve onto"))
			.Optional(TEXT("curve_name"), TEXT("string"), TEXT("Name of the generated curve (default 'Distance')"))
			.Optional(TEXT("axis"), TEXT("string"), TEXT("Axis/axes to measure distance from: X|Y|Z|XY|XZ|YZ|XYZ (default XY)"))
			.Optional(TEXT("sign"), TEXT("string"), TEXT("from_start (positive distance traveled) | to_end (negative distance remaining, => bStopAtEnd). Default from_start"))
			.Optional(TEXT("sample_rate"), TEXT("integer"), TEXT("Curve sampling rate in Hz (default 30)"))
			.Optional(TEXT("stop_speed_threshold"), TEXT("number"), TEXT("Root-motion speed below this is treated as stopped (default 5.0; only used when sign=from_start)"))
			.Build());
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

namespace
{
	/** EDistanceCurve_Axis enumerator names, in declaration order (DistanceCurveModifier.h:12). */
	const TCHAR* GAxisNames[] = { TEXT("X"), TEXT("Y"), TEXT("Z"), TEXT("XY"), TEXT("XZ"), TEXT("YZ"), TEXT("XYZ") };

	/** Magnitude of a root-motion translation restricted to the requested axis/axes.
	 *  Mirrors UDistanceCurveModifier::CalculateMagnitude (DistanceCurveModifier.cpp:88) for the
	 *  speed read path, keyed by the EDistanceCurve_Axis enumerator INDEX (0=X .. 6=XYZ). */
	double AxisMagnitudeByIndex(const FVector& V, int32 AxisIndex)
	{
		switch (AxisIndex)
		{
			case 0:  return FMath::Abs(V.X);                                   // X
			case 1:  return FMath::Abs(V.Y);                                   // Y
			case 2:  return FMath::Abs(V.Z);                                   // Z
			case 3:  return FMath::Sqrt(V.X * V.X + V.Y * V.Y);                // XY
			case 4:  return FMath::Sqrt(V.X * V.X + V.Z * V.Z);                // XZ
			case 5:  return FMath::Sqrt(V.Y * V.Y + V.Z * V.Z);               // YZ
			default: return FMath::Sqrt(V.X * V.X + V.Y * V.Y + V.Z * V.Z);   // XYZ
		}
	}

	/** Parse an axis string -> EDistanceCurve_Axis enumerator index. Returns -1 on unknown. Default handled by caller. */
	int32 ParseAxisIndex(const FString& In)
	{
		for (int32 i = 0; i < UE_ARRAY_COUNT(GAxisNames); ++i)
		{
			if (In.Equals(GAxisNames[i], ESearchCase::IgnoreCase))
			{
				return i;
			}
		}
		return -1;
	}

	/** Resolve the UDistanceCurveModifier UClass reflectively (no typed dependency on AnimationLocomotionLibrary).
	 *  Tries the class path first, then the bare name (NativeFirst), mirroring the existing apply_anim_modifier
	 *  reflective resolution (MonolithAnimationActions.cpp:4300). Returns nullptr if the plugin is not present. */
	UClass* ResolveDistanceCurveModifierClass()
	{
		// Class default object path for a native UCLASS in the AnimationLocomotionLibraryEditor module.
		if (UClass* ByPath = FindObject<UClass>(nullptr, TEXT("/Script/AnimationLocomotionLibraryEditor.DistanceCurveModifier")))
		{
			return ByPath;
		}
		if (UClass* ByName = FindFirstObject<UClass>(TEXT("DistanceCurveModifier"), EFindFirstObjectOptions::NativeFirst))
		{
			return ByName;
		}
		return nullptr;
	}

	/** Set a named FProperty on a UObject from a primitive value, by reflective property lookup.
	 *  Returns false if the property is absent or the type does not match (so the caller can hard-error,
	 *  which is the §13 dep-free regression signal). */
	bool SetNameProp(UObject* Obj, const TCHAR* PropName, FName Value)
	{
		if (FNameProperty* P = CastField<FNameProperty>(Obj->GetClass()->FindPropertyByName(PropName)))
		{
			P->SetPropertyValue_InContainer(Obj, Value);
			return true;
		}
		return false;
	}

	bool SetBoolProp(UObject* Obj, const TCHAR* PropName, bool Value)
	{
		if (FBoolProperty* P = CastField<FBoolProperty>(Obj->GetClass()->FindPropertyByName(PropName)))
		{
			P->SetPropertyValue_InContainer(Obj, Value);
			return true;
		}
		return false;
	}

	bool SetInt32Prop(UObject* Obj, const TCHAR* PropName, int32 Value)
	{
		if (FIntProperty* P = CastField<FIntProperty>(Obj->GetClass()->FindPropertyByName(PropName)))
		{
			P->SetPropertyValue_InContainer(Obj, Value);
			return true;
		}
		return false;
	}

	bool SetFloatProp(UObject* Obj, const TCHAR* PropName, float Value)
	{
		if (FFloatProperty* P = CastField<FFloatProperty>(Obj->GetClass()->FindPropertyByName(PropName)))
		{
			P->SetPropertyValue_InContainer(Obj, Value);
			return true;
		}
		return false;
	}

	/** Set the EDistanceCurve_Axis enum property by enumerator INDEX, reflectively (the underlying type is uint8). */
	bool SetEnumPropByIndex(UObject* Obj, const TCHAR* PropName, int32 EnumIndex)
	{
		FProperty* Raw = Obj->GetClass()->FindPropertyByName(PropName);
		// uint8-backed UENUM(BlueprintType) surfaces as either FEnumProperty (with a byte underlying prop) or
		// FByteProperty (with an Enum* set). Handle both reflectively.
		if (FEnumProperty* EP = CastField<FEnumProperty>(Raw))
		{
			if (FNumericProperty* Underlying = EP->GetUnderlyingProperty())
			{
				Underlying->SetIntPropertyValue(EP->ContainerPtrToValuePtr<void>(Obj), static_cast<int64>(EnumIndex));
				return true;
			}
		}
		if (FByteProperty* BP = CastField<FByteProperty>(Raw))
		{
			BP->SetPropertyValue_InContainer(Obj, static_cast<uint8>(EnumIndex));
			return true;
		}
		return false;
	}
}

// ---------------------------------------------------------------------------
// T1-L2 — get_root_motion_speed
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithLocomotionAuthoringActions::HandleGetRootMotionSpeed(const TSharedPtr<FJsonObject>& Params)
{
	const FString AnimPath = Params->GetStringField(TEXT("anim_path"));

	UAnimSequence* Seq = FMonolithAssetUtils::LoadAssetByPath<UAnimSequence>(AnimPath);
	if (!Seq)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("AnimSequence not found: %s"), *AnimPath));
	}

	FString Mode = TEXT("average");
	Params->TryGetStringField(TEXT("mode"), Mode);
	Mode = Mode.ToLower();

	const float PlayLength = Seq->GetPlayLength();

	// §8 gotcha 6 — root motion must be enabled, else ExtractRootMotionFromRange yields nothing meaningful.
	// HasRootMotion() returns bEnableRootMotion on UAnimSequence (AnimSequence.h:406). bForceRootLock means
	// the root bone is pinned in place => no translation to measure. Either way: speed is unknowable, not 0.
	const bool bRootMotionEnabled = Seq->HasRootMotion();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_path"), Seq->GetPathName());
	Root->SetStringField(TEXT("mode"), Mode);
	Root->SetNumberField(TEXT("play_length"), PlayLength);
	Root->SetBoolField(TEXT("root_motion_enabled"), bRootMotionEnabled);
	Root->SetBoolField(TEXT("force_root_lock"), Seq->bForceRootLock);

	if (!bRootMotionEnabled || PlayLength <= KINDA_SMALL_NUMBER)
	{
		Root->SetBoolField(TEXT("speed_known"), false);
		Root->SetStringField(TEXT("reason"), !bRootMotionEnabled
			? TEXT("no root motion / root-locked -> speed unknowable: bEnableRootMotion is false on the sequence")
			: TEXT("speed unknowable: clip has zero play length"));
		return FMonolithActionResult::Success(Root);
	}

	// Total translation over the whole clip => average speed. Non-deprecated 3-arg double overload
	// (AnimSequence.h:428): ExtractRootMotionFromRange(double Start, double End, const FAnimExtractContext&).
	const FVector TotalDelta = Seq->ExtractRootMotionFromRange(0.0, static_cast<double>(PlayLength), FAnimExtractContext()).GetTranslation();
	const double TotalDistance = AxisMagnitudeByIndex(TotalDelta, 6 /* XYZ — full planar+vertical for the global read */);
	const double AverageSpeed = TotalDistance / static_cast<double>(PlayLength);

	// Zero-delta guard: root motion enabled but the clip does not actually translate the root
	// (idle / in-place clip). Reporting 0 cm/s would imply "measured stationary"; instead flag unknowable.
	if (TotalDistance <= KINDA_SMALL_NUMBER)
	{
		Root->SetBoolField(TEXT("speed_known"), false);
		Root->SetStringField(TEXT("reason"), TEXT("no root motion / root-locked -> speed unknowable: extracted root-motion delta is zero (in-place clip)"));
		Root->SetNumberField(TEXT("total_distance"), TotalDistance);
		return FMonolithActionResult::Success(Root);
	}

	Root->SetBoolField(TEXT("speed_known"), true);
	Root->SetNumberField(TEXT("total_distance"), TotalDistance);
	Root->SetNumberField(TEXT("average_speed"), AverageSpeed);

	if (Mode == TEXT("peak") || Mode == TEXT("per_frame"))
	{
		int32 SampleRate = 30;
		if (Params->HasField(TEXT("sample_rate")))
		{
			SampleRate = FMath::Max(1, static_cast<int32>(Params->GetNumberField(TEXT("sample_rate"))));
		}

		const double SampleInterval = 1.0 / static_cast<double>(SampleRate);
		const int32 NumSteps = FMath::Max(1, FMath::CeilToInt(static_cast<double>(PlayLength) / SampleInterval));

		double PeakSpeed = 0.0;
		TArray<TSharedPtr<FJsonValue>> PerFrame;
		double PrevTime = 0.0;
		for (int32 Step = 1; Step <= NumSteps; ++Step)
		{
			const double Time = FMath::Min(Step * SampleInterval, static_cast<double>(PlayLength));
			const double Span = Time - PrevTime;
			if (Span <= KINDA_SMALL_NUMBER) { PrevTime = Time; continue; }

			const FVector StepDelta = Seq->ExtractRootMotionFromRange(PrevTime, Time, FAnimExtractContext()).GetTranslation();
			const double StepDistance = AxisMagnitudeByIndex(StepDelta, 6 /* XYZ */);
			const double StepSpeed = StepDistance / Span;
			PeakSpeed = FMath::Max(PeakSpeed, StepSpeed);

			if (Mode == TEXT("per_frame"))
			{
				TSharedPtr<FJsonObject> FrameJson = MakeShared<FJsonObject>();
				FrameJson->SetNumberField(TEXT("time"), Time);
				FrameJson->SetNumberField(TEXT("speed"), StepSpeed);
				PerFrame.Add(MakeShared<FJsonValueObject>(FrameJson));
			}
			PrevTime = Time;
		}

		Root->SetNumberField(TEXT("peak_speed"), PeakSpeed);
		if (Mode == TEXT("per_frame"))
		{
			Root->SetArrayField(TEXT("per_frame"), PerFrame);
		}
	}

	return FMonolithActionResult::Success(Root);
}

// ---------------------------------------------------------------------------
// T1-L3 — bake_distance_curve
// ---------------------------------------------------------------------------

FMonolithActionResult FMonolithLocomotionAuthoringActions::HandleBakeDistanceCurve(const TSharedPtr<FJsonObject>& Params)
{
	const FString AnimPath = Params->GetStringField(TEXT("anim_path"));

	UAnimSequence* Seq = FMonolithAssetUtils::LoadAssetByPath<UAnimSequence>(AnimPath);
	if (!Seq)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("AnimSequence not found: %s"), *AnimPath));
	}

	// The DistanceCurveModifier early-returns (and logs an error) when the clip has no root motion
	// (DistanceCurveModifier.cpp:22) — fail loudly here instead of baking an empty/garbage curve.
	if (!Seq->HasRootMotion())
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Cannot bake distance curve on '%s': root motion is disabled (bEnableRootMotion=false). The DistanceCurveModifier requires root motion."),
			*AnimPath));
	}

	// --- Resolve UDistanceCurveModifier reflectively (no typed AnimationLocomotionLibrary dep). ---
	UClass* ModifierClass = ResolveDistanceCurveModifierClass();
	if (!ModifierClass)
	{
		return FMonolithActionResult::Error(
			TEXT("AnimationLocomotionLibrary not available: UDistanceCurveModifier class could not be resolved. ")
			TEXT("Enable the AnimationLocomotionLibrary plugin (it is EnabledByDefault:false) to use bake_distance_curve."));
	}

	// --- Parse params -> modifier property values. ---
	FString CurveNameStr = TEXT("Distance");
	Params->TryGetStringField(TEXT("curve_name"), CurveNameStr);
	if (CurveNameStr.IsEmpty()) { CurveNameStr = TEXT("Distance"); }
	const FName CurveName(*CurveNameStr);

	FString AxisStr = TEXT("XY");
	Params->TryGetStringField(TEXT("axis"), AxisStr);
	int32 AxisIndex = ParseAxisIndex(AxisStr);
	if (AxisIndex < 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid axis '%s'. Expected one of X|Y|Z|XY|XZ|YZ|XYZ."), *AxisStr));
	}

	// sign: from_start => positive distance traveled (bStopAtEnd=false);
	//       to_end     => negative distance remaining to clip end (bStopAtEnd=true).
	FString SignStr = TEXT("from_start");
	Params->TryGetStringField(TEXT("sign"), SignStr);
	const bool bStopAtEnd = SignStr.Equals(TEXT("to_end"), ESearchCase::IgnoreCase);

	int32 SampleRate = 30;
	if (Params->HasField(TEXT("sample_rate")))
	{
		SampleRate = FMath::Max(1, static_cast<int32>(Params->GetNumberField(TEXT("sample_rate"))));
	}

	float StopSpeedThreshold = 5.0f;
	if (Params->HasField(TEXT("stop_speed_threshold")))
	{
		StopSpeedThreshold = static_cast<float>(Params->GetNumberField(TEXT("stop_speed_threshold")));
	}

	GEditor->BeginTransaction(FText::FromString(TEXT("Bake Distance Curve")));
	Seq->Modify();

	// --- CRITICAL remove-first guard (spike finding §314). The DistanceCurveModifier OnApply path
	// calls AddCurve + AddFloatCurveKey; if a curve of this name ALREADY exists, the engine hard-asserts
	// on a duplicate key (AnimSequencerController.cpp:3534) and crashes the editor (not catchable).
	// Remove any pre-existing curve of the target name BEFORE applying the modifier. ---
	if (UAnimationBlueprintLibrary::DoesCurveExist(Seq, CurveName, ERawCurveTrackTypes::RCT_Float))
	{
		const bool bRemoveNameFromSkeleton = false;
		UAnimationBlueprintLibrary::RemoveCurve(Seq, CurveName, bRemoveNameFromSkeleton);
	}

	// --- Register the modifier in the asset's AnimationModifiers stack so it PERSISTS (§8 gotcha 7).
	// AddAnimationModifierOfClass retrieves-or-creates the UAnimationModifiersAssetUserData, instantiates
	// the modifier with class defaults, and adds it to AnimationModifierInstances. It does NOT auto-apply,
	// so we fetch the freshly-added instance, set its props reflectively, then apply explicitly. ---
	if (!UAnimationModifiersAssetUserData::AddAnimationModifierOfClass(Seq, ModifierClass))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("Failed to register DistanceCurveModifier into the AnimationModifiers stack"));
	}

	UAnimationModifiersAssetUserData* UserData = Seq->GetAssetUserData<UAnimationModifiersAssetUserData>();
	if (!UserData)
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("AnimationModifiersAssetUserData missing after AddAnimationModifierOfClass"));
	}

	const TArray<UAnimationModifier*>& Instances = UserData->GetAnimationModifierInstances();
	if (Instances.Num() == 0 || !Instances.Last())
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(TEXT("DistanceCurveModifier instance not found in stack after registration"));
	}
	UAnimationModifier* Modifier = Instances.Last();

	// --- Configure the registered instance reflectively. Property-set failures are the §13 dep-free
	// regression signal (the modifier struct shape changed) — fail loudly rather than baking with defaults. ---
	const bool bSetCurve   = SetNameProp(Modifier, TEXT("CurveName"), CurveName);
	const bool bSetAxis    = SetEnumPropByIndex(Modifier, TEXT("Axis"), AxisIndex);
	const bool bSetStop    = SetBoolProp(Modifier, TEXT("bStopAtEnd"), bStopAtEnd);
	const bool bSetSample  = SetInt32Prop(Modifier, TEXT("SampleRate"), SampleRate);
	const bool bSetThresh  = SetFloatProp(Modifier, TEXT("StopSpeedThreshold"), StopSpeedThreshold);

	if (!(bSetCurve && bSetAxis && bSetStop && bSetSample && bSetThresh))
	{
		GEditor->EndTransaction();
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Failed to set one or more DistanceCurveModifier properties reflectively (CurveName=%d Axis=%d bStopAtEnd=%d SampleRate=%d StopSpeedThreshold=%d). ")
			TEXT("The modifier struct shape may have changed — review the reflective bake path."),
			bSetCurve, bSetAxis, bSetStop, bSetSample, bSetThresh));
	}

	// --- Apply: OnApply bakes the curve. The instance is already in the persistent stack. ---
	Modifier->ApplyToAnimationSequence(Seq);

	GEditor->EndTransaction();
	Seq->MarkPackageDirty();

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("anim_path"), Seq->GetPathName());
	Root->SetStringField(TEXT("modifier_class"), ModifierClass->GetName());
	Root->SetStringField(TEXT("curve_name"), CurveNameStr);
	Root->SetStringField(TEXT("axis"), GAxisNames[AxisIndex]);
	Root->SetBoolField(TEXT("stop_at_end"), bStopAtEnd);
	Root->SetNumberField(TEXT("sample_rate"), SampleRate);
	Root->SetNumberField(TEXT("stop_speed_threshold"), StopSpeedThreshold);
	Root->SetNumberField(TEXT("modifier_stack_count"), Instances.Num());
	Root->SetBoolField(TEXT("curve_exists"), UAnimationBlueprintLibrary::DoesCurveExist(Seq, CurveName, ERawCurveTrackTypes::RCT_Float));
	Root->SetStringField(TEXT("status"), TEXT("baked"));
	return FMonolithActionResult::Success(Root);
}
