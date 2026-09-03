// Copyright (c) 2025-2026 zolnoor. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/EditorAction.h"

/**
 * Create a Sound Cue
 */
class UEBLUEPRINTMCP_API FCreateSoundCueAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("CreateSoundCue"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add SoundWave Player node to Sound Cue
 */
class UEBLUEPRINTMCP_API FAddSoundNodeWavePlayerAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddSoundNodeWavePlayer"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add Modulator node to Sound Cue
 */
class UEBLUEPRINTMCP_API FAddSoundNodeModulatorAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddSoundNodeModulator"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add Random node to Sound Cue
 */
class UEBLUEPRINTMCP_API FAddSoundNodeRandomAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddSoundNodeRandom"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Set Attenuation on Sound Cue
 */
class UEBLUEPRINTMCP_API FAddSoundNodeAttenuationAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddSoundNodeAttenuation"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Create MetaSound Source Asset
 */
class UEBLUEPRINTMCP_API FCreateMetaSoundSourceAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("CreateMetaSoundSource"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Add Node / Operator to MetaSound Graph
 */
class UEBLUEPRINTMCP_API FAddMetaSoundNodeAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("AddMetaSoundNode"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Connect pins in MetaSound Graph
 */
class UEBLUEPRINTMCP_API FConnectMetaSoundNodesAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("ConnectMetaSoundNodes"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Set/Declare MetaSound Parameter
 */
class UEBLUEPRINTMCP_API FSetMetaSoundParameterAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("SetMetaSoundParameter"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};

/**
 * Play sound at world location
 */
class UEBLUEPRINTMCP_API FPlaySoundAtLocationAction : public FEditorAction
{
public:
	virtual FString GetActionName() const override { return TEXT("PlaySoundAtLocation"); }

protected:
	virtual bool Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError) override;
	virtual TSharedPtr<FJsonObject> ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context) override;
};
