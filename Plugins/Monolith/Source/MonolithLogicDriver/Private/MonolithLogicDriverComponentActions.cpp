#include "MonolithLogicDriverComponentActions.h"
#include "MonolithParamSchema.h"
#include "MonolithLogicDriverInternal.h"

#include "Engine/Blueprint.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "UObject/UnrealType.h"

#if WITH_LOGICDRIVER

DEFINE_LOG_CATEGORY_STATIC(LogMonolithLDComponent, Log, All);

namespace
{
	/** Check if a component class is an SM component (by name, since LD is precompiled) */
	bool IsSMComponent(UClass* CompClass)
	{
		if (!CompClass) return false;
		const FString ClassName = CompClass->GetName();
		return ClassName.Contains(TEXT("SMStateMachineComponent"))
			|| ClassName.Contains(TEXT("SMBlueprintComponent"));
	}

	/** Read UPROPERTY values from a component via reflection and return as JSON */
	TSharedPtr<FJsonObject> ReadComponentProperties(UActorComponent* Component)
	{
		TSharedPtr<FJsonObject> Props = MakeShared<FJsonObject>();
		if (!Component) return Props;

		UClass* CompClass = Component->GetClass();

		// Read all UPROPERTY values that aren't inherited from UActorComponent
		for (TFieldIterator<FProperty> PropIt(CompClass, EFieldIteratorFlags::IncludeSuper); PropIt; ++PropIt)
		{
			FProperty* Prop = *PropIt;
			if (!Prop || !Prop->HasAnyPropertyFlags(CPF_Edit | CPF_BlueprintVisible))
			{
				continue;
			}

			// Skip base UActorComponent properties — only want SM-specific ones
			if (Prop->GetOwnerClass() == UActorComponent::StaticClass()
				|| Prop->GetOwnerClass() == USceneComponent::StaticClass()
				|| Prop->GetOwnerClass() == UObject::StaticClass())
			{
				continue;
			}

			const FString PropName = Prop->GetName();
			const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(Component);

			if (const FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
			{
				Props->SetBoolField(PropName, BoolProp->GetPropertyValue(ValuePtr));
			}
			else if (const FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
			{
				Props->SetNumberField(PropName, FloatProp->GetPropertyValue(ValuePtr));
			}
			else if (const FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Prop))
			{
				Props->SetNumberField(PropName, DoubleProp->GetPropertyValue(ValuePtr));
			}
			else if (const FIntProperty* IntProp = CastField<FIntProperty>(Prop))
			{
				Props->SetNumberField(PropName, IntProp->GetPropertyValue(ValuePtr));
			}
			else if (const FStrProperty* StrProp = CastField<FStrProperty>(Prop))
			{
				Props->SetStringField(PropName, StrProp->GetPropertyValue(ValuePtr));
			}
			else if (const FNameProperty* NameProp = CastField<FNameProperty>(Prop))
			{
				Props->SetStringField(PropName, NameProp->GetPropertyValue(ValuePtr).ToString());
			}
			else if (const FObjectPropertyBase* ObjProp = CastField<FObjectPropertyBase>(Prop))
			{
				UObject* ObjVal = ObjProp->GetObjectPropertyValue(ValuePtr);
				Props->SetStringField(PropName, ObjVal ? ObjVal->GetPathName() : TEXT("None"));
			}
			else if (const FEnumProperty* EnumProp = CastField<FEnumProperty>(Prop))
			{
				FString EnumVal;
				Prop->ExportTextItem_Direct(EnumVal, ValuePtr, nullptr, nullptr, PPF_None);
				Props->SetStringField(PropName, EnumVal);
			}
			else if (const FByteProperty* ByteProp = CastField<FByteProperty>(Prop))
			{
				if (ByteProp->Enum)
				{
					uint8 Val = ByteProp->GetPropertyValue(ValuePtr);
					Props->SetStringField(PropName, ByteProp->Enum->GetNameStringByValue(Val));
				}
				else
				{
					Props->SetNumberField(PropName, ByteProp->GetPropertyValue(ValuePtr));
				}
			}
			else
			{
				// Fallback: export as text
				FString TextVal;
				Prop->ExportTextItem_Direct(TextVal, ValuePtr, nullptr, nullptr, PPF_None);
				if (!TextVal.IsEmpty())
				{
					Props->SetStringField(PropName, TextVal);
				}
			}
		}
		return Props;
	}
}

void FMonolithLogicDriverComponentActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("logicdriver"), TEXT("get_sm_component_config"),
		TEXT("Read SM component configuration on an actor Blueprint: state machine class, auto-start, tick interval, network config, and all SM-specific properties"),
		FMonolithActionHandler::CreateStatic(&HandleGetSMComponentConfig),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("blueprint_path"), TEXT("Actor Blueprint asset path (e.g. /Game/Enemies/BP_EnemyBase)"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Specific SM component name; if omitted, returns first SM component found"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("add_sm_component"),
		TEXT("Add a Logic Driver SM component to an actor Blueprint via SimpleConstructionScript"),
		FMonolithActionHandler::CreateStatic(&HandleAddSMComponent),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("blueprint_path"), TEXT("Actor Blueprint asset path"))
			.OptionalAssetPath(TEXT("sm_path"), TEXT("SM Blueprint path to assign as StateMachineClass"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("Component variable name (default: StateMachineComponent)"))
			.Build());

	Registry.RegisterAction(TEXT("logicdriver"), TEXT("configure_sm_component"),
		TEXT("Set SM component properties on an actor Blueprint: auto_start, tick_interval, network_config via reflection"),
		FMonolithActionHandler::CreateStatic(&HandleConfigureSMComponent),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("blueprint_path"), TEXT("Actor Blueprint asset path"))
			.Optional(TEXT("component_name"), TEXT("string"), TEXT("SM component name (if multiple)"))
			.Optional(TEXT("auto_start"), TEXT("boolean"), TEXT("Enable/disable auto-start"))
			.Optional(TEXT("tick_interval"), TEXT("number"), TEXT("Tick interval in seconds"))
			.Optional(TEXT("network_config"), TEXT("string"), TEXT("Network tick configuration enum value"))
			.Build());

	UE_LOG(LogMonolithLDComponent, Log, TEXT("MonolithLogicDriver Component: registered 3 actions"));
}

FMonolithActionResult FMonolithLogicDriverComponentActions::HandleGetSMComponentConfig(const TSharedPtr<FJsonObject>& Params)
{
	if (!Params.IsValid() || !Params->HasField(TEXT("blueprint_path")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: blueprint_path"));
	}

	const FString BPPath = Params->GetStringField(TEXT("blueprint_path"));
	FString ComponentName;
	if (Params->HasField(TEXT("component_name")))
	{
		ComponentName = Params->GetStringField(TEXT("component_name"));
	}

	// Load the Blueprint
	UBlueprint* BP = Cast<UBlueprint>(StaticLoadObject(UBlueprint::StaticClass(), nullptr, *BPPath));
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load Blueprint at '%s'"), *BPPath));
	}

	if (!BP->SimpleConstructionScript)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint '%s' has no SimpleConstructionScript (not an Actor BP?)"), *BPPath));
	}

	// Scan SCS nodes for SM component
	UActorComponent* FoundComponent = nullptr;
	FString FoundNodeName;

	for (USCS_Node* Node : BP->SimpleConstructionScript->GetAllNodes())
	{
		if (!Node || !Node->ComponentTemplate)
		{
			continue;
		}

		UClass* CompClass = Node->ComponentTemplate->GetClass();
		if (!IsSMComponent(CompClass))
		{
			continue;
		}

		// If a specific name was requested, match it
		if (!ComponentName.IsEmpty())
		{
			if (Node->GetVariableName().ToString() != ComponentName
				&& Node->ComponentTemplate->GetName() != ComponentName)
			{
				continue;
			}
		}

		FoundComponent = Node->ComponentTemplate;
		FoundNodeName = Node->GetVariableName().ToString();
		break;
	}

	if (!FoundComponent)
	{
		if (!ComponentName.IsEmpty())
		{
			return FMonolithActionResult::Error(FString::Printf(
				TEXT("No SM component named '%s' found in Blueprint '%s'"), *ComponentName, *BPPath));
		}
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No SM component found in Blueprint '%s'"), *BPPath));
	}

	// Read well-known properties via reflection
	UClass* CompClass = FoundComponent->GetClass();

	// StateMachineClass — typically a UObject* or TSubclassOf<USMInstance>
	FString StateMachineClass = TEXT("None");
	if (FProperty* SMClassProp = CompClass->FindPropertyByName(TEXT("StateMachineClass")))
	{
		SMClassProp->ExportTextItem_Direct(StateMachineClass, SMClassProp->ContainerPtrToValuePtr<void>(FoundComponent), nullptr, nullptr, PPF_None);
	}

	// bAutoStart
	bool bAutoStart = false;
	if (const FBoolProperty* AutoStartProp = CastField<FBoolProperty>(CompClass->FindPropertyByName(TEXT("bAutoStart"))))
	{
		bAutoStart = AutoStartProp->GetPropertyValue(AutoStartProp->ContainerPtrToValuePtr<void>(FoundComponent));
	}

	// TickInterval
	float TickInterval = 0.f;
	if (const FFloatProperty* TickProp = CastField<FFloatProperty>(CompClass->FindPropertyByName(TEXT("TickInterval"))))
	{
		TickInterval = TickProp->GetPropertyValue(TickProp->ContainerPtrToValuePtr<void>(FoundComponent));
	}

	// NetworkConfig — likely an enum
	FString NetworkConfig = TEXT("Unknown");
	if (FProperty* NetProp = CompClass->FindPropertyByName(TEXT("NetworkTickConfiguration")))
	{
		NetProp->ExportTextItem_Direct(NetworkConfig, NetProp->ContainerPtrToValuePtr<void>(FoundComponent), nullptr, nullptr, PPF_None);
	}
	else if (FProperty* NetProp2 = CompClass->FindPropertyByName(TEXT("ServerNetworkTickConfiguration")))
	{
		NetProp2->ExportTextItem_Direct(NetworkConfig, NetProp2->ContainerPtrToValuePtr<void>(FoundComponent), nullptr, nullptr, PPF_None);
	}

	// All SM-specific properties
	TSharedPtr<FJsonObject> AllProps = ReadComponentProperties(FoundComponent);

	// Build result
	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_path"), BPPath);
	Result->SetStringField(TEXT("component_name"), FoundNodeName);
	Result->SetStringField(TEXT("component_class"), CompClass->GetName());
	Result->SetStringField(TEXT("state_machine_class"), StateMachineClass);
	Result->SetBoolField(TEXT("auto_start"), bAutoStart);
	Result->SetNumberField(TEXT("tick_interval"), TickInterval);
	Result->SetStringField(TEXT("network_config"), NetworkConfig);
	Result->SetObjectField(TEXT("properties"), AllProps);

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverComponentActions::HandleAddSMComponent(const TSharedPtr<FJsonObject>& Params)
{
	if (!Params.IsValid() || !Params->HasField(TEXT("blueprint_path")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: blueprint_path"));
	}

	const FString BPPath = Params->GetStringField(TEXT("blueprint_path"));
	FString CompName = TEXT("StateMachineComponent");
	if (Params->HasField(TEXT("component_name")) && !Params->GetStringField(TEXT("component_name")).IsEmpty())
	{
		CompName = Params->GetStringField(TEXT("component_name"));
	}

	// Load actor Blueprint
	UBlueprint* BP = Cast<UBlueprint>(StaticLoadObject(UBlueprint::StaticClass(), nullptr, *BPPath));
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load Blueprint at '%s'"), *BPPath));
	}
	if (!BP->SimpleConstructionScript)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Blueprint '%s' has no SimpleConstructionScript (not an Actor BP?)"), *BPPath));
	}

	// Get SM component class
	UClass* SMCompClass = MonolithLD::GetSMComponentClass();
	if (!SMCompClass)
	{
		return FMonolithActionResult::Error(TEXT("SMStateMachineComponent class not found. Is Logic Driver Pro loaded?"));
	}

	// Check if a component with this name already exists
	for (USCS_Node* ExistingNode : BP->SimpleConstructionScript->GetAllNodes())
	{
		if (ExistingNode && ExistingNode->GetVariableName().ToString() == CompName)
		{
			return FMonolithActionResult::Error(
				FString::Printf(TEXT("Component named '%s' already exists in Blueprint '%s'"), *CompName, *BPPath));
		}
	}

	// Create SCS node
	USCS_Node* NewNode = BP->SimpleConstructionScript->CreateNode(SMCompClass, FName(*CompName));
	if (!NewNode)
	{
		return FMonolithActionResult::Error(TEXT("Failed to create SCS node for SM component"));
	}
	BP->SimpleConstructionScript->AddNode(NewNode);

	// If sm_path provided, set StateMachineClass on the component template
	FString SMPath;
	if (Params->HasField(TEXT("sm_path")))
	{
		SMPath = Params->GetStringField(TEXT("sm_path"));
	}

	if (!SMPath.IsEmpty() && NewNode->ComponentTemplate)
	{
		// Load the SM Blueprint to get its GeneratedClass
		FString LoadError;
		UBlueprint* SMBP = MonolithLD::LoadSMBlueprint(SMPath, LoadError);
		if (SMBP && SMBP->GeneratedClass)
		{
			// Set StateMachineClass property via reflection
			UClass* CompClass = NewNode->ComponentTemplate->GetClass();
			FProperty* SMClassProp = CompClass->FindPropertyByName(TEXT("StateMachineClass"));
			if (SMClassProp)
			{
				// For TSubclassOf, we need to use FClassProperty
				if (FClassProperty* ClassProp = CastField<FClassProperty>(SMClassProp))
				{
					ClassProp->SetObjectPropertyValue(
						ClassProp->ContainerPtrToValuePtr<void>(NewNode->ComponentTemplate),
						SMBP->GeneratedClass);
				}
				else
				{
					// Fallback: try ImportText
					FString ClassPath = SMBP->GeneratedClass->GetPathName();
					void* ValuePtr = SMClassProp->ContainerPtrToValuePtr<void>(NewNode->ComponentTemplate);
					SMClassProp->ImportText_Direct(*ClassPath, ValuePtr, NewNode->ComponentTemplate, PPF_None);
				}
			}
		}
		else
		{
			UE_LOG(LogMonolithLDComponent, Warning, TEXT("Could not load SM Blueprint at '%s' to set StateMachineClass: %s"), *SMPath, *LoadError);
		}
	}

	// Mark dirty
	BP->Modify();
	BP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_path"), BPPath);
	Result->SetStringField(TEXT("component_name"), CompName);
	Result->SetStringField(TEXT("component_class"), SMCompClass->GetName());
	if (!SMPath.IsEmpty())
	{
		Result->SetStringField(TEXT("state_machine_class"), SMPath);
	}
	Result->SetStringField(TEXT("message"),
		FString::Printf(TEXT("Added SM component '%s' to '%s'"), *CompName, *BPPath));

	return FMonolithActionResult::Success(Result);
}

FMonolithActionResult FMonolithLogicDriverComponentActions::HandleConfigureSMComponent(const TSharedPtr<FJsonObject>& Params)
{
	if (!Params.IsValid() || !Params->HasField(TEXT("blueprint_path")))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: blueprint_path"));
	}

	const FString BPPath = Params->GetStringField(TEXT("blueprint_path"));
	FString ComponentName;
	if (Params->HasField(TEXT("component_name")))
	{
		ComponentName = Params->GetStringField(TEXT("component_name"));
	}

	UBlueprint* BP = Cast<UBlueprint>(StaticLoadObject(UBlueprint::StaticClass(), nullptr, *BPPath));
	if (!BP)
	{
		return FMonolithActionResult::Error(FString::Printf(TEXT("Failed to load Blueprint at '%s'"), *BPPath));
	}
	if (!BP->SimpleConstructionScript)
	{
		return FMonolithActionResult::Error(TEXT("Blueprint has no SimpleConstructionScript (not an Actor BP?)"));
	}

	// Find SM component template
	UActorComponent* FoundComponent = nullptr;
	FString FoundNodeName;
	for (USCS_Node* Node : BP->SimpleConstructionScript->GetAllNodes())
	{
		if (!Node || !Node->ComponentTemplate) continue;
		if (!IsSMComponent(Node->ComponentTemplate->GetClass())) continue;

		if (!ComponentName.IsEmpty())
		{
			if (Node->GetVariableName().ToString() != ComponentName
				&& Node->ComponentTemplate->GetName() != ComponentName)
			{
				continue;
			}
		}

		FoundComponent = Node->ComponentTemplate;
		FoundNodeName = Node->GetVariableName().ToString();
		break;
	}

	if (!FoundComponent)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No SM component%s found in Blueprint '%s'"),
			ComponentName.IsEmpty() ? TEXT("") : *FString::Printf(TEXT(" named '%s'"), *ComponentName),
			*BPPath));
	}

	TArray<FString> Applied;

	// auto_start
	if (Params->HasField(TEXT("auto_start")))
	{
		bool bVal = Params->GetBoolField(TEXT("auto_start"));
		FBoolProperty* Prop = CastField<FBoolProperty>(FoundComponent->GetClass()->FindPropertyByName(TEXT("bAutoStart")));
		if (Prop)
		{
			FoundComponent->Modify();
			Prop->SetPropertyValue(Prop->ContainerPtrToValuePtr<void>(FoundComponent), bVal);
			Applied.Add(FString::Printf(TEXT("bAutoStart=%s"), bVal ? TEXT("true") : TEXT("false")));
		}
	}

	// tick_interval
	if (Params->HasField(TEXT("tick_interval")))
	{
		float Val = static_cast<float>(Params->GetNumberField(TEXT("tick_interval")));
		FFloatProperty* Prop = CastField<FFloatProperty>(FoundComponent->GetClass()->FindPropertyByName(TEXT("TickInterval")));
		if (Prop)
		{
			FoundComponent->Modify();
			Prop->SetPropertyValue(Prop->ContainerPtrToValuePtr<void>(FoundComponent), Val);
			Applied.Add(FString::Printf(TEXT("TickInterval=%.4f"), Val));
		}
	}

	// network_config
	if (Params->HasField(TEXT("network_config")))
	{
		FString NetConfig = Params->GetStringField(TEXT("network_config"));
		FProperty* NetProp = FoundComponent->GetClass()->FindPropertyByName(TEXT("NetworkTickConfiguration"));
		if (!NetProp)
		{
			NetProp = FoundComponent->GetClass()->FindPropertyByName(TEXT("ServerNetworkTickConfiguration"));
		}
		if (NetProp)
		{
			FoundComponent->Modify();
			void* ValuePtr = NetProp->ContainerPtrToValuePtr<void>(FoundComponent);
			if (NetProp->ImportText_Direct(*NetConfig, ValuePtr, FoundComponent, PPF_None))
			{
				Applied.Add(FString::Printf(TEXT("%s=%s"), *NetProp->GetName(), *NetConfig));
			}
		}
	}

	if (Applied.Num() == 0)
	{
		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("message"), TEXT("No properties were set (none provided or none matched)"));
		return FMonolithActionResult::Success(R);
	}

	BP->Modify();
	BP->MarkPackageDirty();

	TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("blueprint_path"), BPPath);
	Result->SetStringField(TEXT("component_name"), FoundNodeName);

	TArray<TSharedPtr<FJsonValue>> AppliedArr;
	for (const FString& S : Applied)
		AppliedArr.Add(MakeShared<FJsonValueString>(S));
	Result->SetArrayField(TEXT("properties_set"), AppliedArr);

	return FMonolithActionResult::Success(Result);
}

#else

void FMonolithLogicDriverComponentActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// Logic Driver not available
}

#endif // WITH_LOGICDRIVER
