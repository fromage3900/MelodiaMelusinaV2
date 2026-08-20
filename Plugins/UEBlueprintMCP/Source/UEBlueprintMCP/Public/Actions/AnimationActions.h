// Copyright (c) 2025-2026 zolnoor. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/EditorAction.h"

/**
 * Create an Animation Blueprint
 */
class UEBLUEPRINTMCP_API FCreateAnimationBlueprintAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("CreateAnimationBlueprint"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add a State Machine node to AnimGraph
 */
class UEBLUEPRINTMCP_API FAddAnimStateMachineAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddAnimStateMachine"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add an Animation State inside a State Machine
 */
class UEBLUEPRINTMCP_API FAddAnimStateAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddAnimState"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add a transition rule between two states in a State Machine
 */
class UEBLUEPRINTMCP_API FAddAnimTransitionAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddAnimTransition"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add a BlendSpace Player node
 */
class UEBLUEPRINTMCP_API FAddBlendSpacePlayerAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddBlendSpacePlayer"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add an Animation Sequence Player node
 */
class UEBLUEPRINTMCP_API FAddSequencePlayerAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddSequencePlayer"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add a Modify Bone / Skeletal Control node for secondary motion physics
 */
class UEBLUEPRINTMCP_API FAddBoneTransformNodeAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddBoneTransformNode"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add a Two-Bone IK skeletal control node
 */
class UEBLUEPRINTMCP_API FAddTwoBoneIKNodeAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddTwoBoneIKNode"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add an Animation Notify to an Animation Sequence
 */
class UEBLUEPRINTMCP_API FAddAnimNotifyAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddAnimNotify"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Connect animation pose/sync pins
 */
class UEBLUEPRINTMCP_API FConnectAnimNodesAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("ConnectAnimNodes"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Query State Machine states and transitions
 */
class UEBLUEPRINTMCP_API FGetAnimStateMachineStatesAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("GetAnimStateMachineStates"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};
