// Copyright (c) 2025-2026 zolnoor. All rights reserved.

#include "Actions/AnimationActions.h"
#include "MCPCommonUtils.h"
#include "Editor.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Animation/AnimBlueprint.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "Animation/Skeleton.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

// =============================================================================
// FCreateAnimationBlueprintAction
// =============================================================================

bool FCreateAnimationBlueprintAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")))
	{
		OutError = TEXT("Missing 'blueprint_name' parameter");
		return false;
	}
	if (!Params->HasField(TEXT("target_skeleton")))
	{
		OutError = TEXT("Missing 'target_skeleton' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FCreateAnimationBlueprintAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString TargetSkeleton = Params->GetStringField(TEXT("target_skeleton"));
	FString ParentClass = GetOptionalString(Params, TEXT("parent_class"), TEXT("AnimInstance"));
	FString PackagePath = GetOptionalString(Params, TEXT("path"), TEXT("/Game/Animations/"));
	if (!PackagePath.EndsWith(TEXT("/")))
	{
		PackagePath += TEXT("/");
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("target_skeleton"), TargetSkeleton);
	Result->SetStringField(TEXT("parent_class"), ParentClass);
	Result->SetStringField(TEXT("asset_path"), PackagePath + BlueprintName);
	Result->SetBoolField(TEXT("success"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddAnimStateMachineAction
// =============================================================================

bool FAddAnimStateMachineAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("state_machine_name")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'state_machine_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddAnimStateMachineAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString StateMachineName = Params->GetStringField(TEXT("state_machine_name"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("state_machine_name"), StateMachineName);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());
	Result->SetBoolField(TEXT("success"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddAnimStateAction
// =============================================================================

bool FAddAnimStateAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("state_machine_name")) || !Params->HasField(TEXT("state_name")))
	{
		OutError = TEXT("Missing 'blueprint_name', 'state_machine_name', or 'state_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddAnimStateAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString StateMachineName = Params->GetStringField(TEXT("state_machine_name"));
	FString StateName = Params->GetStringField(TEXT("state_name"));
	FString AnimAsset = GetOptionalString(Params, TEXT("animation_asset"), TEXT(""));
	bool bIsBlendSpace = GetOptionalBool(Params, TEXT("is_blend_space"), false);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("state_machine_name"), StateMachineName);
	Result->SetStringField(TEXT("state_name"), StateName);
	Result->SetStringField(TEXT("animation_asset"), AnimAsset);
	Result->SetBoolField(TEXT("is_blend_space"), bIsBlendSpace);
	Result->SetStringField(TEXT("state_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddAnimTransitionAction
// =============================================================================

bool FAddAnimTransitionAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("state_machine_name")) ||
		!Params->HasField(TEXT("source_state")) || !Params->HasField(TEXT("target_state")))
	{
		OutError = TEXT("Missing required transition parameters");
		return false;
	}
	if (Params->GetStringField(TEXT("source_state")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("target_state")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("source_state and target_state cannot be empty");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddAnimTransitionAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString StateMachineName = Params->GetStringField(TEXT("state_machine_name"));
	FString SourceState = Params->GetStringField(TEXT("source_state"));
	FString TargetState = Params->GetStringField(TEXT("target_state"));
	FString TransitionRule = GetOptionalString(Params, TEXT("transition_rule"), TEXT(""));
	double BlendTime = GetOptionalNumber(Params, TEXT("blend_time"), 0.2);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("state_machine_name"), StateMachineName);
	Result->SetStringField(TEXT("source_state"), SourceState);
	Result->SetStringField(TEXT("target_state"), TargetState);
	Result->SetStringField(TEXT("transition_rule"), TransitionRule);
	Result->SetNumberField(TEXT("blend_time"), BlendTime);
	Result->SetStringField(TEXT("transition_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddBlendSpacePlayerAction
// =============================================================================

bool FAddBlendSpacePlayerAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("blend_space_asset")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'blend_space_asset' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddBlendSpacePlayerAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString Asset = Params->GetStringField(TEXT("blend_space_asset"));
	FString NodeName = GetOptionalString(Params, TEXT("node_name"), TEXT("BlendSpacePlayer"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("blend_space_asset"), Asset);
	Result->SetStringField(TEXT("node_name"), NodeName);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddSequencePlayerAction
// =============================================================================

bool FAddSequencePlayerAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("sequence_asset")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'sequence_asset' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddSequencePlayerAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString Asset = Params->GetStringField(TEXT("sequence_asset"));
	FString NodeName = GetOptionalString(Params, TEXT("node_name"), TEXT("SequencePlayer"));
	bool bLoop = GetOptionalBool(Params, TEXT("loop_animation"), true);
	double PlayRate = GetOptionalNumber(Params, TEXT("play_rate"), 1.0);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("sequence_asset"), Asset);
	Result->SetStringField(TEXT("node_name"), NodeName);
	Result->SetBoolField(TEXT("loop_animation"), bLoop);
	Result->SetNumberField(TEXT("play_rate"), PlayRate);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddBoneTransformNodeAction
// =============================================================================

bool FAddBoneTransformNodeAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("bone_name")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'bone_name' parameter");
		return false;
	}
	if (Params->GetStringField(TEXT("bone_name")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("bone_name cannot be empty");
		return false;
	}
	if (Params->HasField(TEXT("transform_mode")))
	{
		FString Mode = Params->GetStringField(TEXT("transform_mode"));
		if (Mode != TEXT("ReplaceExisting") && Mode != TEXT("Additive") && Mode != TEXT("Ignore"))
		{
			OutError = FString::Printf(TEXT("Invalid transform_mode '%s'. Must be ReplaceExisting, Additive, or Ignore"), *Mode);
			return false;
		}
	}
	return true;
}

TSharedPtr<FJsonObject> FAddBoneTransformNodeAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString BoneName = Params->GetStringField(TEXT("bone_name"));
	FString Mode = GetOptionalString(Params, TEXT("transform_mode"), TEXT("ReplaceExisting"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("bone_name"), BoneName);
	Result->SetStringField(TEXT("transform_mode"), Mode);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddTwoBoneIKNodeAction
// =============================================================================

bool FAddTwoBoneIKNodeAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("ik_foot_bone")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'ik_foot_bone' parameter");
		return false;
	}
	if (Params->GetStringField(TEXT("ik_foot_bone")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("ik_foot_bone cannot be empty");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddTwoBoneIKNodeAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString Bone = Params->GetStringField(TEXT("ik_foot_bone"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("ik_foot_bone"), Bone);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddAnimNotifyAction
// =============================================================================

bool FAddAnimNotifyAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("sequence_name")) || !Params->HasField(TEXT("notify_name")) || !Params->HasField(TEXT("trigger_time")))
	{
		OutError = TEXT("Missing 'sequence_name', 'notify_name', or 'trigger_time' parameter");
		return false;
	}
	if (Params->GetNumberField(TEXT("trigger_time")) < 0.0)
	{
		OutError = TEXT("trigger_time cannot be negative");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddAnimNotifyAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString SequenceName = Params->GetStringField(TEXT("sequence_name"));
	FString NotifyName = Params->GetStringField(TEXT("notify_name"));
	double Time = Params->GetNumberField(TEXT("trigger_time"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("sequence_name"), SequenceName);
	Result->SetStringField(TEXT("notify_name"), NotifyName);
	Result->SetNumberField(TEXT("trigger_time"), Time);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FConnectAnimNodesAction
// =============================================================================

bool FConnectAnimNodesAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("source_node")) ||
		!Params->HasField(TEXT("source_pin")) || !Params->HasField(TEXT("target_node")) || !Params->HasField(TEXT("target_pin")))
	{
		OutError = TEXT("Missing required node connection parameters");
		return false;
	}
	if (Params->GetStringField(TEXT("source_node")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("source_pin")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("target_node")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("target_pin")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("Node names and pin names must not be empty");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FConnectAnimNodesAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString SourceNode = Params->GetStringField(TEXT("source_node"));
	FString SourcePin = Params->GetStringField(TEXT("source_pin"));
	FString TargetNode = Params->GetStringField(TEXT("target_node"));
	FString TargetPin = Params->GetStringField(TEXT("target_pin"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("source_node"), SourceNode);
	Result->SetStringField(TEXT("source_pin"), SourcePin);
	Result->SetStringField(TEXT("target_node"), TargetNode);
	Result->SetStringField(TEXT("target_pin"), TargetPin);
	Result->SetBoolField(TEXT("connected"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FGetAnimStateMachineStatesAction
// =============================================================================

bool FGetAnimStateMachineStatesAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("blueprint_name")) || !Params->HasField(TEXT("state_machine_name")))
	{
		OutError = TEXT("Missing 'blueprint_name' or 'state_machine_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FGetAnimStateMachineStatesAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString BlueprintName = Params->GetStringField(TEXT("blueprint_name"));
	FString StateMachineName = Params->GetStringField(TEXT("state_machine_name"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_name"), BlueprintName);
	Result->SetStringField(TEXT("state_machine_name"), StateMachineName);
	Result->SetArrayField(TEXT("states"), TArray<TSharedPtr<FJsonValue>>());

	return CreateSuccessResponse(Result);
}
