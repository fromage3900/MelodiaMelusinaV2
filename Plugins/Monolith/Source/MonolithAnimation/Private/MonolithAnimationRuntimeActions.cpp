#include "MonolithAnimationRuntimeActions.h"
#include "MonolithParamSchema.h"
#include "MonolithStructFieldResolver.h"

#include "Editor.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimClassInterface.h"
#include "Animation/AnimStateMachineTypes.h"
#include "Animation/AnimNode_StateMachine.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "UObject/UnrealType.h"
#include "UObject/EnumProperty.h"
#include "UObject/Class.h"

DEFINE_LOG_CATEGORY_STATIC(LogMonolithAnimRuntime, Log, All);

namespace
{
	// ── PIE actor + skeletal mesh + anim instance resolution ────────────
	struct FAnimPIELookup
	{
		AActor* Actor = nullptr;
		USkeletalMeshComponent* MeshComp = nullptr;
		UAnimInstance* AnimInstance = nullptr;
		FMonolithActionResult Error;
		bool bSuccess = false;
	};

	FAnimPIELookup FindAnimInstanceInPIE(const TSharedPtr<FJsonObject>& Params)
	{
		FAnimPIELookup Result;

		FString ActorName = Params->GetStringField(TEXT("actor"));
		if (ActorName.IsEmpty())
		{
			Result.Error = FMonolithActionResult::Error(TEXT("Missing required param 'actor'"));
			return Result;
		}

		FString ComponentName;
		if (Params->HasField(TEXT("component_name")))
		{
			ComponentName = Params->GetStringField(TEXT("component_name"));
		}

		FWorldContext* PIEContext = GEditor ? GEditor->GetPIEWorldContext() : nullptr;
		if (!PIEContext || !PIEContext->World())
		{
			Result.Error = FMonolithActionResult::Error(TEXT("PIE not running — start Play-In-Editor first"));
			return Result;
		}
		UWorld* PIEWorld = PIEContext->World();

		for (TActorIterator<AActor> It(PIEWorld); It; ++It)
		{
			if (It->GetActorLabel() == ActorName || It->GetName() == ActorName)
			{
				Result.Actor = *It;
				break;
			}
		}
		if (!Result.Actor)
		{
			Result.Error = FMonolithActionResult::Error(FString::Printf(TEXT("Actor '%s' not found in PIE world"), *ActorName));
			return Result;
		}

		for (UActorComponent* C : Result.Actor->GetComponents())
		{
			USkeletalMeshComponent* MC = Cast<USkeletalMeshComponent>(C);
			if (!MC) continue;
			if (ComponentName.IsEmpty() || MC->GetName() == ComponentName)
			{
				Result.MeshComp = MC;
				break;
			}
		}
		if (!Result.MeshComp)
		{
			Result.Error = FMonolithActionResult::Error(FString::Printf(
				TEXT("No skeletal mesh component%s found on actor '%s'"),
				ComponentName.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" named '%s'"), *ComponentName),
				*ActorName));
			return Result;
		}

		Result.AnimInstance = Result.MeshComp->GetAnimInstance();
		Result.bSuccess = true;
		return Result;
	}

	FString AnimationModeToString(EAnimationMode::Type Mode)
	{
		switch (Mode)
		{
			case EAnimationMode::AnimationBlueprint: return TEXT("AnimationBlueprint");
			case EAnimationMode::AnimationSingleNode: return TEXT("AnimationSingleNode");
			case EAnimationMode::AnimationCustomMode: return TEXT("AnimationCustomMode");
			default: return TEXT("Unknown");
		}
	}

	// Read an already-resolved property value into a JSON value. Handles the common
	// scalar types directly; falls back to ExportText for structs/enums/anything else.
	// ExportTextItem_Direct needs an "owner" object for object-reference export context;
	// the leaf's container object is passed as OwnerForExport.
	TSharedPtr<FJsonValue> ReadResolvedValue(const FProperty* Prop, const void* ValuePtr,
		const UObject* OwnerForExport, FString& OutTypeName)
	{
		if (!Prop || !ValuePtr)
		{
			OutTypeName = TEXT("<not found>");
			return nullptr;
		}
		OutTypeName = Prop->GetCPPType(nullptr, 0u);

		if (const FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
		{
			return MakeShared<FJsonValueBoolean>(BoolProp->GetPropertyValue(ValuePtr));
		}
		if (const FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(FloatProp->GetPropertyValue(ValuePtr));
		}
		if (const FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(DoubleProp->GetPropertyValue(ValuePtr));
		}
		if (const FIntProperty* IntProp = CastField<FIntProperty>(Prop))
		{
			return MakeShared<FJsonValueNumber>(IntProp->GetPropertyValue(ValuePtr));
		}
		if (const FStrProperty* StrProp = CastField<FStrProperty>(Prop))
		{
			return MakeShared<FJsonValueString>(StrProp->GetPropertyValue(ValuePtr));
		}
		if (const FNameProperty* NameProp = CastField<FNameProperty>(Prop))
		{
			return MakeShared<FJsonValueString>(NameProp->GetPropertyValue(ValuePtr).ToString());
		}
		if (const FObjectPropertyBase* ObjProp = CastField<FObjectPropertyBase>(Prop))
		{
			UObject* Val = ObjProp->GetObjectPropertyValue(ValuePtr);
			return MakeShared<FJsonValueString>(Val ? Val->GetPathName() : TEXT("None"));
		}

		// Generic fallback (enums, structs, vectors, etc.)
		FString Exported;
		Prop->ExportTextItem_Direct(Exported, ValuePtr, nullptr, const_cast<UObject*>(OwnerForExport), PPF_None);
		return MakeShared<FJsonValueString>(Exported);
	}

	// Read a single live UPROPERTY value off an object into a JSON value, resolving
	// dotted member paths + UserDefinedStruct friendly names via the shared resolver.
	// Plain (non-dotted) names keep the flat-lookup base case.
	TSharedPtr<FJsonValue> ReadPropertyValue(UObject* Obj, const FString& VarName, FString& OutTypeName)
	{
		if (!Obj)
		{
			OutTypeName = TEXT("<not found>");
			return nullptr;
		}
		const MonolithStructField::FResolved Resolved = MonolithStructField::Resolve(Obj, VarName);
		if (!Resolved.Leaf)
		{
			OutTypeName = TEXT("<not found>");
			return nullptr;
		}
		return ReadResolvedValue(Resolved.Leaf, Resolved.ValuePtr, Obj, OutTypeName);
	}

	// ── Lockstep parity comparison (compare_to_actor) ────────────────────
	struct FParityTolerance
	{
		double Float     = 1e-3;
		double Vector    = 1e-2; // per-component (cm)
		double Rotator   = 1e-2; // per-component (deg)
		double Transform = 1e-2; // per-component (translation cm / rotation deg)
	};

	// Classify a property into a tolerance class string used in the report.
	FString ParityToleranceClass(const FProperty* Prop)
	{
		if (CastField<FBoolProperty>(Prop) || CastField<FNameProperty>(Prop) ||
			CastField<FStrProperty>(Prop)  || CastField<FTextProperty>(Prop) ||
			CastField<FObjectPropertyBase>(Prop))
		{
			return TEXT("exact");
		}
		if (CastField<FEnumProperty>(Prop)) return TEXT("exact");
		if (CastField<FByteProperty>(Prop)) return TEXT("exact");
		if (CastField<FIntProperty>(Prop) || CastField<FInt64Property>(Prop)) return TEXT("exact");
		if (CastField<FFloatProperty>(Prop) || CastField<FDoubleProperty>(Prop)) return TEXT("float");
		if (const FStructProperty* SP = CastField<FStructProperty>(Prop))
		{
			if (SP->Struct == TBaseStructure<FVector>::Get())    return TEXT("vector");
			if (SP->Struct == TBaseStructure<FRotator>::Get())   return TEXT("rotator");
			if (SP->Struct == TBaseStructure<FTransform>::Get()) return TEXT("transform");
			return TEXT("struct-exact");
		}
		return TEXT("exact");
	}

	// Read a double from a numeric property value pointer (float or double).
	double ParityReadNumeric(const FProperty* Prop, const void* Ptr)
	{
		if (const FFloatProperty* P = CastField<FFloatProperty>(Prop))   return (double)P->GetPropertyValue(Ptr);
		if (const FDoubleProperty* P = CastField<FDoubleProperty>(Prop)) return P->GetPropertyValue(Ptr);
		return 0.0;
	}

	// Compare one named property on two instances. Populates OutEntry with the
	// per-variable verdict (delta + pass/fail). Returns the pass flag.
	bool ParityCompareProperty(
		UObject* A, UObject* B, const FString& VarName,
		const FParityTolerance& Tol, const TSharedPtr<FJsonObject>& OutEntry)
	{
		OutEntry->SetStringField(TEXT("name"), VarName);

		// Resolve both sides through the shared dotted-path / UDS friendly-name resolver
		// so parity comparison supports the same addressing as the variables read.
		const MonolithStructField::FResolved ResA = MonolithStructField::Resolve(A, VarName);
		const MonolithStructField::FResolved ResB = MonolithStructField::Resolve(B, VarName);
		const FProperty* PropA = ResA.Leaf;
		const FProperty* PropB = ResB.Leaf;
		if (!PropA || !PropB)
		{
			OutEntry->SetStringField(TEXT("tolerance_class"), TEXT("missing"));
			OutEntry->SetBoolField(TEXT("pass"), false);
			OutEntry->SetStringField(TEXT("note"),
				!PropA ? TEXT("property not found on actor") : TEXT("property not found on compare_to_actor"));
			return false;
		}

		// Differing property layouts can't be component-compared — flag and fail.
		if (PropA->GetClass() != PropB->GetClass())
		{
			OutEntry->SetStringField(TEXT("tolerance_class"), TEXT("type-mismatch"));
			OutEntry->SetBoolField(TEXT("pass"), false);
			OutEntry->SetStringField(TEXT("a_type"), PropA->GetCPPType(nullptr, 0u));
			OutEntry->SetStringField(TEXT("b_type"), PropB->GetCPPType(nullptr, 0u));
			return false;
		}

		const void* PtrA = ResA.ValuePtr;
		const void* PtrB = ResB.ValuePtr;
		const FString Klass = ParityToleranceClass(PropA);
		OutEntry->SetStringField(TEXT("tolerance_class"), Klass);

		if (Klass == TEXT("float"))
		{
			const double VA = ParityReadNumeric(PropA, PtrA);
			const double VB = ParityReadNumeric(PropB, PtrB);
			const double Delta = FMath::Abs(VA - VB);
			const bool bPass = Delta <= Tol.Float;
			OutEntry->SetNumberField(TEXT("a"), VA);
			OutEntry->SetNumberField(TEXT("b"), VB);
			OutEntry->SetNumberField(TEXT("delta"), Delta);
			OutEntry->SetNumberField(TEXT("tolerance"), Tol.Float);
			OutEntry->SetBoolField(TEXT("pass"), bPass);
			return bPass;
		}

		if (Klass == TEXT("vector") || Klass == TEXT("rotator"))
		{
			const FStructProperty* SP = CastField<FStructProperty>(PropA);
			double C0A, C1A, C2A, C0B, C1B, C2B;
			if (Klass == TEXT("vector"))
			{
				const FVector& VA = *static_cast<const FVector*>(PtrA);
				const FVector& VB = *static_cast<const FVector*>(PtrB);
				C0A = VA.X; C1A = VA.Y; C2A = VA.Z; C0B = VB.X; C1B = VB.Y; C2B = VB.Z;
			}
			else
			{
				const FRotator& RA = *static_cast<const FRotator*>(PtrA);
				const FRotator& RB = *static_cast<const FRotator*>(PtrB);
				C0A = RA.Pitch; C1A = RA.Yaw; C2A = RA.Roll; C0B = RB.Pitch; C1B = RB.Yaw; C2B = RB.Roll;
			}
			const double Bound = (Klass == TEXT("vector")) ? Tol.Vector : Tol.Rotator;
			const double MaxDelta = FMath::Max3(FMath::Abs(C0A - C0B), FMath::Abs(C1A - C1B), FMath::Abs(C2A - C2B));
			const bool bPass = MaxDelta <= Bound;
			(void)SP;
			OutEntry->SetNumberField(TEXT("max_component_delta"), MaxDelta);
			OutEntry->SetNumberField(TEXT("tolerance"), Bound);
			OutEntry->SetBoolField(TEXT("pass"), bPass);
			return bPass;
		}

		if (Klass == TEXT("transform"))
		{
			const FTransform& TA = *static_cast<const FTransform*>(PtrA);
			const FTransform& TB = *static_cast<const FTransform*>(PtrB);
			const FVector LocA = TA.GetLocation(), LocB = TB.GetLocation();
			const FRotator RotA = TA.Rotator(), RotB = TB.Rotator();
			const double LocDelta = FMath::Max3(FMath::Abs(LocA.X - LocB.X), FMath::Abs(LocA.Y - LocB.Y), FMath::Abs(LocA.Z - LocB.Z));
			const double RotDelta = FMath::Max3(FMath::Abs(RotA.Pitch - RotB.Pitch), FMath::Abs(RotA.Yaw - RotB.Yaw), FMath::Abs(RotA.Roll - RotB.Roll));
			const bool bScaleEqual = TA.GetScale3D().Equals(TB.GetScale3D(), 0.0);
			const bool bPass = (LocDelta <= Tol.Transform) && (RotDelta <= Tol.Transform) && bScaleEqual;
			OutEntry->SetNumberField(TEXT("translation_delta"), LocDelta);
			OutEntry->SetNumberField(TEXT("rotation_delta"), RotDelta);
			OutEntry->SetBoolField(TEXT("scale_exact"), bScaleEqual);
			OutEntry->SetNumberField(TEXT("tolerance"), Tol.Transform);
			OutEntry->SetBoolField(TEXT("pass"), bPass);
			return bPass;
		}

		// exact / struct-exact — byte-identical comparison via FProperty::Identical.
		const bool bPass = PropA->Identical(PtrA, PtrB, PPF_None);
		FString ExpA, ExpB;
		PropA->ExportTextItem_Direct(ExpA, PtrA, nullptr, A, PPF_None);
		PropB->ExportTextItem_Direct(ExpB, PtrB, nullptr, B, PPF_None);
		OutEntry->SetStringField(TEXT("a"), ExpA);
		OutEntry->SetStringField(TEXT("b"), ExpB);
		OutEntry->SetBoolField(TEXT("pass"), bPass);
		return bPass;
	}
}

// ── Registration ────────────────────────────────────────────────────

void FMonolithAnimationRuntimeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("animation"), TEXT("sample_pie_anim_instance"),
		TEXT("Sample a live PIE actor's animation state: active AnimInstance/AnimClass, animation mode, active state-machine states, active montage, requested anim-instance variables, and requested bone/socket transforms. "
		     "When 'compare_to_actor' is set, samples a SECOND actor's AnimInstance in lockstep and emits per-variable deltas with per-type tolerance pass/fail classification + an overall roll-up."),
		FMonolithActionHandler::CreateStatic(&HandleSamplePIEAnimInstance),
		FParamSchemaBuilder()
			.Required(TEXT("actor"), TEXT("string"), TEXT("Actor label or name in the PIE world"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Skeletal mesh component name (if the actor has multiple)"))
			.Optional(TEXT("variables"), TEXT("array"), TEXT("Anim-instance variable names to read live via reflection. Supports dotted member paths (e.g. 'Movement.Speed') that descend nested structs, matching UserDefinedStruct members by their friendly (authored) name. Struct-member traversal only; array/map indexing is not supported."))
			.Optional(TEXT("bones"), TEXT("array"), TEXT("Bone names (strings) to report world-space transforms for"))
			.Optional(TEXT("sockets"), TEXT("array"), TEXT("Socket names (strings) to report world-space transforms for"))
			.Optional(TEXT("state_machines"), TEXT("array"), TEXT("State machine names to report active state for. If omitted, all baked state machines are enumerated"))
			.Optional(TEXT("compare_to_actor"), TEXT("string"), TEXT("Second actor label/name to sample in lockstep and compare the 'variables' set against (parity check)"))
			.Optional(TEXT("compare_component_name"), TEXT("string"), TEXT("Skeletal mesh component name on the compare_to_actor (if it has multiple)"))
			.Optional(TEXT("tolerance"), TEXT("object"), TEXT("Per-type tolerance overrides: {float, vector, rotator, transform}. Exact for bool/enum/int. Defaults: float 1e-3, vector/rotator 1e-2, transform 1e-2"))
			.Build());

	UE_LOG(LogMonolithAnimRuntime, Log, TEXT("MonolithAnimation Runtime: registered 1 action"));
}

// ── sample_pie_anim_instance ────────────────────────────────────────

FMonolithActionResult FMonolithAnimationRuntimeActions::HandleSamplePIEAnimInstance(const TSharedPtr<FJsonObject>& Params)
{
	FAnimPIELookup Lookup = FindAnimInstanceInPIE(Params);
	if (!Lookup.bSuccess) return Lookup.Error;

	USkeletalMeshComponent* MeshComp = Lookup.MeshComp;
	UAnimInstance* AnimInstance = Lookup.AnimInstance;

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("actor"), Lookup.Actor->GetActorLabel());
	Root->SetStringField(TEXT("component"), MeshComp->GetName());

	// Animation mode + class info.
	Root->SetStringField(TEXT("animation_mode"), AnimationModeToString(MeshComp->GetAnimationMode()));
	if (UClass* AnimClass = MeshComp->GetAnimClass())
	{
		Root->SetStringField(TEXT("mesh_anim_class"), AnimClass->GetPathName());
	}
	if (USkeletalMesh* SkelMesh = MeshComp->GetSkeletalMeshAsset())
	{
		Root->SetStringField(TEXT("skeletal_mesh"), SkelMesh->GetPathName());
	}

	if (!AnimInstance)
	{
		Root->SetStringField(TEXT("note"), TEXT("No active AnimInstance on this component (animation mode may not be AnimationBlueprint)"));
		return FMonolithActionResult::Success(Root);
	}
	Root->SetStringField(TEXT("anim_instance_class"), AnimInstance->GetClass()->GetPathName());

	// ── Active state-machine state(s) ────────────────────────────────
	TArray<TSharedPtr<FJsonValue>> StateMachinesArr;
	TArray<FName> MachineNames;

	const TArray<TSharedPtr<FJsonValue>>* RequestedSMs = nullptr;
	if (Params->TryGetArrayField(TEXT("state_machines"), RequestedSMs) && RequestedSMs)
	{
		for (const TSharedPtr<FJsonValue>& V : *RequestedSMs)
		{
			FString Name;
			if (V.IsValid() && V->TryGetString(Name) && !Name.IsEmpty())
			{
				MachineNames.Add(FName(*Name));
			}
		}
	}
	else
	{
		// Enumerate all baked state machines from the generated anim class.
		if (IAnimClassInterface* AnimClassInterface = IAnimClassInterface::GetFromClass(AnimInstance->GetClass()))
		{
			for (const FBakedAnimationStateMachine& Baked : AnimClassInterface->GetBakedStateMachines())
			{
				MachineNames.Add(Baked.MachineName);
			}
		}
	}

	for (const FName& MachineName : MachineNames)
	{
		const int32 MachineIndex = AnimInstance->GetStateMachineIndex(MachineName);
		TSharedPtr<FJsonObject> SMObj = MakeShared<FJsonObject>();
		SMObj->SetStringField(TEXT("machine_name"), MachineName.ToString());
		SMObj->SetNumberField(TEXT("machine_index"), MachineIndex);
		if (MachineIndex != INDEX_NONE)
		{
			SMObj->SetStringField(TEXT("active_state"), AnimInstance->GetCurrentStateName(MachineIndex).ToString());
			SMObj->SetNumberField(TEXT("machine_weight"), AnimInstance->GetInstanceMachineWeight(MachineIndex));
		}
		else
		{
			SMObj->SetStringField(TEXT("note"), TEXT("machine name not found on this anim instance"));
		}
		StateMachinesArr.Add(MakeShared<FJsonValueObject>(SMObj));
	}
	Root->SetArrayField(TEXT("state_machines"), StateMachinesArr);

	// ── Active montage ───────────────────────────────────────────────
	if (UAnimMontage* ActiveMontage = AnimInstance->GetCurrentActiveMontage())
	{
		TSharedPtr<FJsonObject> MontageObj = MakeShared<FJsonObject>();
		MontageObj->SetStringField(TEXT("montage"), ActiveMontage->GetPathName());
		MontageObj->SetBoolField(TEXT("is_playing"), AnimInstance->Montage_IsPlaying(ActiveMontage));
		MontageObj->SetStringField(TEXT("current_section"), AnimInstance->Montage_GetCurrentSection(ActiveMontage).ToString());
		Root->SetObjectField(TEXT("active_montage"), MontageObj);
	}
	else
	{
		Root->SetField(TEXT("active_montage"), MakeShared<FJsonValueNull>());
	}

	// ── Requested anim-instance variables (live reflection) ──────────
	const TArray<TSharedPtr<FJsonValue>>* RequestedVars = nullptr;
	if (Params->TryGetArrayField(TEXT("variables"), RequestedVars) && RequestedVars)
	{
		TSharedPtr<FJsonObject> VarsObj = MakeShared<FJsonObject>();
		for (const TSharedPtr<FJsonValue>& V : *RequestedVars)
		{
			FString VarName;
			if (!V.IsValid() || !V->TryGetString(VarName) || VarName.IsEmpty()) continue;
			FString TypeName;
			TSharedPtr<FJsonValue> Val = ReadPropertyValue(AnimInstance, VarName, TypeName);
			if (Val.IsValid())
			{
				VarsObj->SetField(VarName, Val);
			}
			else
			{
				VarsObj->SetStringField(VarName, FString::Printf(TEXT("<%s>"), *TypeName));
			}
		}
		Root->SetObjectField(TEXT("variables"), VarsObj);
	}

	// ── Bone transforms (resolve name -> index, then world transform) ─
	const TArray<TSharedPtr<FJsonValue>>* RequestedBones = nullptr;
	if (Params->TryGetArrayField(TEXT("bones"), RequestedBones) && RequestedBones)
	{
		TArray<TSharedPtr<FJsonValue>> BonesArr;
		for (const TSharedPtr<FJsonValue>& V : *RequestedBones)
		{
			FString BoneName;
			if (!V.IsValid() || !V->TryGetString(BoneName) || BoneName.IsEmpty()) continue;

			TSharedPtr<FJsonObject> BoneObj = MakeShared<FJsonObject>();
			BoneObj->SetStringField(TEXT("bone"), BoneName);

			// CRITICAL: resolve the bone NAME to an index before GetBoneTransform(index).
			const int32 BoneIndex = MeshComp->GetBoneIndex(FName(*BoneName));
			if (BoneIndex == INDEX_NONE)
			{
				BoneObj->SetStringField(TEXT("error"), TEXT("bone not found on skeleton"));
				BonesArr.Add(MakeShared<FJsonValueObject>(BoneObj));
				continue;
			}
			BoneObj->SetNumberField(TEXT("index"), BoneIndex);

			const FTransform XForm = MeshComp->GetBoneTransform(BoneIndex);
			const FVector Loc = XForm.GetLocation();
			const FRotator Rot = XForm.Rotator();
			const FVector Scale = XForm.GetScale3D();
			TSharedPtr<FJsonObject> LocObj = MakeShared<FJsonObject>();
			LocObj->SetNumberField(TEXT("x"), Loc.X); LocObj->SetNumberField(TEXT("y"), Loc.Y); LocObj->SetNumberField(TEXT("z"), Loc.Z);
			TSharedPtr<FJsonObject> RotObj = MakeShared<FJsonObject>();
			RotObj->SetNumberField(TEXT("pitch"), Rot.Pitch); RotObj->SetNumberField(TEXT("yaw"), Rot.Yaw); RotObj->SetNumberField(TEXT("roll"), Rot.Roll);
			TSharedPtr<FJsonObject> ScaleObj = MakeShared<FJsonObject>();
			ScaleObj->SetNumberField(TEXT("x"), Scale.X); ScaleObj->SetNumberField(TEXT("y"), Scale.Y); ScaleObj->SetNumberField(TEXT("z"), Scale.Z);
			BoneObj->SetObjectField(TEXT("location"), LocObj);
			BoneObj->SetObjectField(TEXT("rotation"), RotObj);
			BoneObj->SetObjectField(TEXT("scale"), ScaleObj);
			BoneObj->SetStringField(TEXT("space"), TEXT("world"));
			BonesArr.Add(MakeShared<FJsonValueObject>(BoneObj));
		}
		Root->SetArrayField(TEXT("bones"), BonesArr);
	}

	// ── Socket transforms ────────────────────────────────────────────
	const TArray<TSharedPtr<FJsonValue>>* RequestedSockets = nullptr;
	if (Params->TryGetArrayField(TEXT("sockets"), RequestedSockets) && RequestedSockets)
	{
		TArray<TSharedPtr<FJsonValue>> SocketsArr;
		for (const TSharedPtr<FJsonValue>& V : *RequestedSockets)
		{
			FString SocketName;
			if (!V.IsValid() || !V->TryGetString(SocketName) || SocketName.IsEmpty()) continue;

			TSharedPtr<FJsonObject> SockObj = MakeShared<FJsonObject>();
			SockObj->SetStringField(TEXT("socket"), SocketName);
			if (!MeshComp->DoesSocketExist(FName(*SocketName)))
			{
				SockObj->SetStringField(TEXT("error"), TEXT("socket not found"));
				SocketsArr.Add(MakeShared<FJsonValueObject>(SockObj));
				continue;
			}

			const FTransform XForm = MeshComp->GetSocketTransform(FName(*SocketName), RTS_World);
			const FVector Loc = XForm.GetLocation();
			const FRotator Rot = XForm.Rotator();
			TSharedPtr<FJsonObject> LocObj = MakeShared<FJsonObject>();
			LocObj->SetNumberField(TEXT("x"), Loc.X); LocObj->SetNumberField(TEXT("y"), Loc.Y); LocObj->SetNumberField(TEXT("z"), Loc.Z);
			TSharedPtr<FJsonObject> RotObj = MakeShared<FJsonObject>();
			RotObj->SetNumberField(TEXT("pitch"), Rot.Pitch); RotObj->SetNumberField(TEXT("yaw"), Rot.Yaw); RotObj->SetNumberField(TEXT("roll"), Rot.Roll);
			SockObj->SetObjectField(TEXT("location"), LocObj);
			SockObj->SetObjectField(TEXT("rotation"), RotObj);
			SockObj->SetStringField(TEXT("space"), TEXT("world"));
			SocketsArr.Add(MakeShared<FJsonValueObject>(SockObj));
		}
		Root->SetArrayField(TEXT("sockets"), SocketsArr);
	}

	// ── Lockstep parity comparison (compare_to_actor) ────────────────────
	FString CompareActor;
	if (Params->TryGetStringField(TEXT("compare_to_actor"), CompareActor) && !CompareActor.IsEmpty())
	{
		// Resolve the second actor's AnimInstance by reusing FindAnimInstanceInPIE
		// with a synthetic params blob (actor + optional component name).
		TSharedPtr<FJsonObject> CmpParams = MakeShared<FJsonObject>();
		CmpParams->SetStringField(TEXT("actor"), CompareActor);
		FString CmpComponent;
		if (Params->TryGetStringField(TEXT("compare_component_name"), CmpComponent) && !CmpComponent.IsEmpty())
		{
			CmpParams->SetStringField(TEXT("component_name"), CmpComponent);
		}

		FAnimPIELookup CmpLookup = FindAnimInstanceInPIE(CmpParams);
		if (!CmpLookup.bSuccess)
		{
			TSharedPtr<FJsonObject> Err = MakeShared<FJsonObject>();
			Err->SetStringField(TEXT("error"), CmpLookup.Error.ErrorMessage);
			Root->SetObjectField(TEXT("comparison"), Err);
		}
		else if (!CmpLookup.AnimInstance)
		{
			TSharedPtr<FJsonObject> Cmp = MakeShared<FJsonObject>();
			Cmp->SetStringField(TEXT("error"), TEXT("compare_to_actor has no active AnimInstance"));
			Root->SetObjectField(TEXT("comparison"), Cmp);
		}
		else
		{
			// Parse tolerance overrides.
			FParityTolerance Tol;
			const TSharedPtr<FJsonObject>* TolObj = nullptr;
			if (Params->TryGetObjectField(TEXT("tolerance"), TolObj) && TolObj)
			{
				double V;
				if ((*TolObj)->TryGetNumberField(TEXT("float"), V))     Tol.Float = V;
				if ((*TolObj)->TryGetNumberField(TEXT("vector"), V))    Tol.Vector = V;
				if ((*TolObj)->TryGetNumberField(TEXT("rotator"), V))   Tol.Rotator = V;
				if ((*TolObj)->TryGetNumberField(TEXT("transform"), V)) Tol.Transform = V;
			}

			TSharedPtr<FJsonObject> Cmp = MakeShared<FJsonObject>();
			Cmp->SetStringField(TEXT("compare_actor"), CmpLookup.Actor->GetActorLabel());
			Cmp->SetStringField(TEXT("compare_anim_instance_class"), CmpLookup.AnimInstance->GetClass()->GetPathName());

			TArray<TSharedPtr<FJsonValue>> CmpArr;
			int32 PassCount = 0, FailCount = 0;
			const TArray<TSharedPtr<FJsonValue>>* CmpVars = nullptr;
			if (Params->TryGetArrayField(TEXT("variables"), CmpVars) && CmpVars)
			{
				for (const TSharedPtr<FJsonValue>& V : *CmpVars)
				{
					FString VarName;
					if (!V.IsValid() || !V->TryGetString(VarName) || VarName.IsEmpty()) continue;
					TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
					const bool bPass = ParityCompareProperty(AnimInstance, CmpLookup.AnimInstance, VarName, Tol, Entry);
					if (bPass) ++PassCount; else ++FailCount;
					CmpArr.Add(MakeShared<FJsonValueObject>(Entry));
				}
			}
			Cmp->SetArrayField(TEXT("variables"), CmpArr);

			TSharedPtr<FJsonObject> Roll = MakeShared<FJsonObject>();
			Roll->SetNumberField(TEXT("compared"), PassCount + FailCount);
			Roll->SetNumberField(TEXT("pass"), PassCount);
			Roll->SetNumberField(TEXT("fail"), FailCount);
			Roll->SetBoolField(TEXT("overall_pass"), FailCount == 0 && (PassCount + FailCount) > 0);
			Cmp->SetObjectField(TEXT("summary"), Roll);

			Root->SetObjectField(TEXT("comparison"), Cmp);
		}
	}

	// Asset-player weight note: direct per-asset-player weight getters require a
	// node index (GetInstanceAssetPlayerTime etc. are time-only). State/machine
	// weights ARE reachable via GetInstanceStateWeight / GetInstanceMachineWeight
	// (machine weight reported above). Full per-node weight walk deferred this pass.
	Root->SetStringField(TEXT("asset_player_weight_note"),
		TEXT("Per-asset-player blend weights have no direct public getter; state-machine weights are reported under state_machines[].machine_weight. Full node-graph weight walk deferred."));

	return FMonolithActionResult::Success(Root);
}
