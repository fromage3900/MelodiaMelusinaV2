// Copyright (c) 2025-2026 zolnoor. All rights reserved.

#include "Actions/AudioActions.h"
#include "MCPCommonUtils.h"
#include "Editor.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Sound/SoundCue.h"
#include "Sound/SoundWave.h"
#include "Kismet/GameplayStatics.h"

// =============================================================================
// FCreateSoundCueAction
// =============================================================================

bool FCreateSoundCueAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("cue_name")))
	{
		OutError = TEXT("Missing 'cue_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FCreateSoundCueAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString CueName = Params->GetStringField(TEXT("cue_name"));
	FString PackagePath = GetOptionalString(Params, TEXT("path"), TEXT("/Game/Audio/"));
	if (!PackagePath.EndsWith(TEXT("/")))
	{
		PackagePath += TEXT("/");
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("cue_name"), CueName);
	Result->SetStringField(TEXT("asset_path"), PackagePath + CueName);
	Result->SetBoolField(TEXT("success"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddSoundNodeWavePlayerAction
// =============================================================================

bool FAddSoundNodeWavePlayerAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("cue_name")) || !Params->HasField(TEXT("sound_wave_path")))
	{
		OutError = TEXT("Missing 'cue_name' or 'sound_wave_path' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddSoundNodeWavePlayerAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString CueName = Params->GetStringField(TEXT("cue_name"));
	FString WavePath = Params->GetStringField(TEXT("sound_wave_path"));
	bool bLooping = GetOptionalBool(Params, TEXT("looping"), false);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("cue_name"), CueName);
	Result->SetStringField(TEXT("sound_wave_path"), WavePath);
	Result->SetBoolField(TEXT("looping"), bLooping);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddSoundNodeModulatorAction
// =============================================================================

bool FAddSoundNodeModulatorAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("cue_name")))
	{
		OutError = TEXT("Missing 'cue_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddSoundNodeModulatorAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString CueName = Params->GetStringField(TEXT("cue_name"));
	double PitchMin = GetOptionalNumber(Params, TEXT("pitch_min"), 0.9);
	double PitchMax = GetOptionalNumber(Params, TEXT("pitch_max"), 1.1);
	double VolumeMin = GetOptionalNumber(Params, TEXT("volume_min"), 0.8);
	double VolumeMax = GetOptionalNumber(Params, TEXT("volume_max"), 1.0);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("cue_name"), CueName);
	Result->SetNumberField(TEXT("pitch_min"), PitchMin);
	Result->SetNumberField(TEXT("pitch_max"), PitchMax);
	Result->SetNumberField(TEXT("volume_min"), VolumeMin);
	Result->SetNumberField(TEXT("volume_max"), VolumeMax);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddSoundNodeRandomAction
// =============================================================================

bool FAddSoundNodeRandomAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("cue_name")))
	{
		OutError = TEXT("Missing 'cue_name' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddSoundNodeRandomAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString CueName = Params->GetStringField(TEXT("cue_name"));
	bool bNoRep = GetOptionalBool(Params, TEXT("randomize_without_replacement"), true);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("cue_name"), CueName);
	Result->SetBoolField(TEXT("randomize_without_replacement"), bNoRep);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddSoundNodeAttenuationAction
// =============================================================================

bool FAddSoundNodeAttenuationAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("cue_name")))
	{
		OutError = TEXT("Missing 'cue_name' parameter");
		return false;
	}
	if (Params->HasField(TEXT("inner_radius")) && Params->HasField(TEXT("outer_radius")))
	{
		if (Params->GetNumberField(TEXT("inner_radius")) > Params->GetNumberField(TEXT("outer_radius")))
		{
			OutError = TEXT("inner_radius cannot exceed outer_radius");
			return false;
		}
	}
	if (Params->HasField(TEXT("spatialization_algorithm")))
	{
		FString Alg = Params->GetStringField(TEXT("spatialization_algorithm"));
		if (Alg != TEXT("SPATIALIZATION_Default") && Alg != TEXT("SPATIALIZATION_HRTF"))
		{
			OutError = TEXT("Invalid spatialization_algorithm. Must be SPATIALIZATION_Default or SPATIALIZATION_HRTF");
			return false;
		}
	}
	return true;
}

TSharedPtr<FJsonObject> FAddSoundNodeAttenuationAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString CueName = Params->GetStringField(TEXT("cue_name"));
	double Inner = GetOptionalNumber(Params, TEXT("inner_radius"), 400.0);
	double Outer = GetOptionalNumber(Params, TEXT("outer_radius"), 3000.0);
	double Falloff = GetOptionalNumber(Params, TEXT("falloff_distance"), 2600.0);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("cue_name"), CueName);
	Result->SetNumberField(TEXT("inner_radius"), Inner);
	Result->SetNumberField(TEXT("outer_radius"), Outer);
	Result->SetNumberField(TEXT("falloff_distance"), Falloff);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FCreateMetaSoundSourceAction
// =============================================================================

bool FCreateMetaSoundSourceAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("metasound_name")))
	{
		OutError = TEXT("Missing 'metasound_name' parameter");
		return false;
	}
	if (Params->GetStringField(TEXT("metasound_name")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("metasound_name cannot be empty");
		return false;
	}
	if (Params->HasField(TEXT("output_format")))
	{
		FString Fmt = Params->GetStringField(TEXT("output_format"));
		if (Fmt != TEXT("Mono") && Fmt != TEXT("Stereo") && Fmt != TEXT("Quad") && Fmt != TEXT("5.1") && Fmt != TEXT("7.1"))
		{
			OutError = FString::Printf(TEXT("Invalid output_format '%s'. Must be Mono, Stereo, Quad, 5.1, or 7.1"), *Fmt);
			return false;
		}
	}
	return true;
}

TSharedPtr<FJsonObject> FCreateMetaSoundSourceAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString MetaSoundName = Params->GetStringField(TEXT("metasound_name"));
	FString OutputFormat = GetOptionalString(Params, TEXT("output_format"), TEXT("Stereo"));
	FString PackagePath = GetOptionalString(Params, TEXT("path"), TEXT("/Game/Audio/MetaSounds/"));
	if (!PackagePath.EndsWith(TEXT("/")))
	{
		PackagePath += TEXT("/");
	}

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("metasound_name"), MetaSoundName);
	Result->SetStringField(TEXT("output_format"), OutputFormat);
	Result->SetStringField(TEXT("asset_path"), PackagePath + MetaSoundName);
	Result->SetBoolField(TEXT("success"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FAddMetaSoundNodeAction
// =============================================================================

bool FAddMetaSoundNodeAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("metasound_name")) || !Params->HasField(TEXT("node_type")) || !Params->HasField(TEXT("node_name")))
	{
		OutError = TEXT("Missing 'metasound_name', 'node_type', or 'node_name' parameter");
		return false;
	}
	if (Params->GetStringField(TEXT("node_name")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("node_name cannot be empty");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FAddMetaSoundNodeAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString MetaSoundName = Params->GetStringField(TEXT("metasound_name"));
	FString NodeType = Params->GetStringField(TEXT("node_type"));
	FString NodeName = Params->GetStringField(TEXT("node_name"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("metasound_name"), MetaSoundName);
	Result->SetStringField(TEXT("node_type"), NodeType);
	Result->SetStringField(TEXT("node_name"), NodeName);
	Result->SetStringField(TEXT("node_id"), FGuid::NewGuid().ToString());

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FConnectMetaSoundNodesAction
// =============================================================================

bool FConnectMetaSoundNodesAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("metasound_name")) || !Params->HasField(TEXT("source_node")) ||
		!Params->HasField(TEXT("source_pin")) || !Params->HasField(TEXT("target_node")) || !Params->HasField(TEXT("target_pin")))
	{
		OutError = TEXT("Missing required MetaSound node connection parameters");
		return false;
	}
	if (Params->GetStringField(TEXT("source_node")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("source_pin")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("target_node")).TrimStartAndEnd().IsEmpty() ||
		Params->GetStringField(TEXT("target_pin")).TrimStartAndEnd().IsEmpty())
	{
		OutError = TEXT("MetaSound node names and pin names must not be empty");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FConnectMetaSoundNodesAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString MetaSoundName = Params->GetStringField(TEXT("metasound_name"));
	FString SourceNode = Params->GetStringField(TEXT("source_node"));
	FString SourcePin = Params->GetStringField(TEXT("source_pin"));
	FString TargetNode = Params->GetStringField(TEXT("target_node"));
	FString TargetPin = Params->GetStringField(TEXT("target_pin"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("metasound_name"), MetaSoundName);
	Result->SetStringField(TEXT("source_node"), SourceNode);
	Result->SetStringField(TEXT("source_pin"), SourcePin);
	Result->SetStringField(TEXT("target_node"), TargetNode);
	Result->SetStringField(TEXT("target_pin"), TargetPin);
	Result->SetBoolField(TEXT("connected"), true);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FSetMetaSoundParameterAction
// =============================================================================

bool FSetMetaSoundParameterAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("metasound_name")) || !Params->HasField(TEXT("parameter_name")) || !Params->HasField(TEXT("parameter_type")))
	{
		OutError = TEXT("Missing required parameter fields");
		return false;
	}
	FString ParamType = Params->GetStringField(TEXT("parameter_type"));
	if (ParamType != TEXT("Float") && ParamType != TEXT("Int32") && ParamType != TEXT("Boolean") &&
		ParamType != TEXT("Audio") && ParamType != TEXT("Trigger") && ParamType != TEXT("String"))
	{
		OutError = FString::Printf(TEXT("Invalid parameter_type '%s'. Must be Float, Int32, Boolean, Audio, Trigger, or String"), *ParamType);
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FSetMetaSoundParameterAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString MetaSoundName = Params->GetStringField(TEXT("metasound_name"));
	FString ParamName = Params->GetStringField(TEXT("parameter_name"));
	FString ParamType = Params->GetStringField(TEXT("parameter_type"));

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("metasound_name"), MetaSoundName);
	Result->SetStringField(TEXT("parameter_name"), ParamName);
	Result->SetStringField(TEXT("parameter_type"), ParamType);

	return CreateSuccessResponse(Result);
}

// =============================================================================
// FPlaySoundAtLocationAction
// =============================================================================

bool FPlaySoundAtLocationAction::Validate(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context, FString& OutError)
{
	if (!Params->HasField(TEXT("sound_asset")) || !Params->HasField(TEXT("location")))
	{
		OutError = TEXT("Missing 'sound_asset' or 'location' parameter");
		return false;
	}
	return true;
}

TSharedPtr<FJsonObject> FPlaySoundAtLocationAction::ExecuteInternal(const TSharedPtr<FJsonObject>& Params, FMCPEditorContext& Context)
{
	FString SoundAsset = Params->GetStringField(TEXT("sound_asset"));
	double Volume = GetOptionalNumber(Params, TEXT("volume_multiplier"), 1.0);
	double Pitch = GetOptionalNumber(Params, TEXT("pitch_multiplier"), 1.0);

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("sound_asset"), SoundAsset);
	Result->SetNumberField(TEXT("volume_multiplier"), Volume);
	Result->SetNumberField(TEXT("pitch_multiplier"), Pitch);
	Result->SetBoolField(TEXT("played"), true);

	return CreateSuccessResponse(Result);
}
