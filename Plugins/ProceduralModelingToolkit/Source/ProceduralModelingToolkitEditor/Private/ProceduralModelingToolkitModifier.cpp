#include "ProceduralModelingToolkitModifier.h"

#include "ProceduralModelingToolkitEditorModule.h"
#include "UDynamicMesh.h"

const FProceduralModelingToolkitModifierParameter* FProceduralModelingToolkitModifierParameters::Find(FName Name) const
{
	return Values.FindByPredicate([Name](const FProceduralModelingToolkitModifierParameter& Parameter)
	{
		return Parameter.Name == Name;
	});
}

FProceduralModelingToolkitModifierParameter* FProceduralModelingToolkitModifierParameters::FindMutable(FName Name)
{
	return Values.FindByPredicate([Name](const FProceduralModelingToolkitModifierParameter& Parameter)
	{
		return Parameter.Name == Name;
	});
}

void FProceduralModelingToolkitModifierParameters::AddBool(FName Name, bool Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::Boolean;
	Parameter.BoolValue = Value;
	Values.Add(Parameter);
}

void FProceduralModelingToolkitModifierParameters::AddInt(FName Name, int32 Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::Integer;
	Parameter.IntValue = Value;
	Values.Add(Parameter);
}

void FProceduralModelingToolkitModifierParameters::AddFloat(FName Name, double Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::Float;
	Parameter.FloatValue = Value;
	Values.Add(Parameter);
}

void FProceduralModelingToolkitModifierParameters::AddVector(FName Name, FVector Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::Vector;
	Parameter.VectorValue = Value;
	Values.Add(Parameter);
}

void FProceduralModelingToolkitModifierParameters::AddRotator(FName Name, FRotator Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::Rotator;
	Parameter.RotatorValue = Value;
	Values.Add(Parameter);
}

void FProceduralModelingToolkitModifierParameters::AddString(FName Name, const FString& Value)
{
	FProceduralModelingToolkitModifierParameter Parameter;
	Parameter.Name = Name;
	Parameter.Type = EProceduralModelingToolkitModifierParameterType::String;
	Parameter.StringValue = Value;
	Values.Add(Parameter);
}

bool FProceduralModelingToolkitModifierParameters::GetBool(FName Name, bool DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->BoolValue : DefaultValue;
}

int32 FProceduralModelingToolkitModifierParameters::GetInt(FName Name, int32 DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->IntValue : DefaultValue;
}

double FProceduralModelingToolkitModifierParameters::GetFloat(FName Name, double DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->FloatValue : DefaultValue;
}

FVector FProceduralModelingToolkitModifierParameters::GetVector(FName Name, FVector DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->VectorValue : DefaultValue;
}

FRotator FProceduralModelingToolkitModifierParameters::GetRotator(FName Name, FRotator DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->RotatorValue : DefaultValue;
}

FString FProceduralModelingToolkitModifierParameters::GetString(FName Name, const FString& DefaultValue) const
{
	const FProceduralModelingToolkitModifierParameter* Parameter = Find(Name);
	return Parameter ? Parameter->StringValue : DefaultValue;
}

FProceduralModelingToolkitModifierResult FProceduralModelingToolkitModifierResult::Success(const FString& Message)
{
	FProceduralModelingToolkitModifierResult Result;
	Result.bSuccess = true;
	Result.Message = Message;
	return Result;
}

FProceduralModelingToolkitModifierResult FProceduralModelingToolkitModifierResult::Failure(const FString& Message)
{
	FProceduralModelingToolkitModifierResult Result;
	Result.bSuccess = false;
	Result.Message = Message;
	return Result;
}

UProceduralModelingToolkitModifier::UProceduralModelingToolkitModifier()
{
	ModifierId = GetClass()->GetFName();
	DisplayName = GetClass()->GetDisplayNameText();
}

FProceduralModelingToolkitModifierResult UProceduralModelingToolkitModifier::Execute(
	UDynamicMesh* TargetMesh,
	const FProceduralModelingToolkitModifierExecutionContext& Context
)
{
	if (!TargetMesh)
	{
		return FProceduralModelingToolkitModifierResult::Failure(TEXT("Modifier execution failed: target Dynamic Mesh is null."));
	}

	UE_LOG(
		LogProceduralModelingToolkit,
		Verbose,
		TEXT("Modifier '%s' has no implementation yet. Passing mesh through unchanged. Source='%s' Output='%s'"),
		*ModifierId.ToString(),
		*Context.SourceAssetPath,
		*Context.OutputAssetPath
	);

	return FProceduralModelingToolkitModifierResult::Success(TEXT("Base modifier pass-through."));
}

void UProceduralModelingToolkitModifier::Serialize(FArchive& Ar)
{
	Super::Serialize(Ar);
}

void UProceduralModelingToolkitModifier::SetEnabled(bool bInEnabled)
{
	bEnabled = bInEnabled;
}

bool UProceduralModelingToolkitModifier::IsEnabled() const
{
	return bEnabled;
}
