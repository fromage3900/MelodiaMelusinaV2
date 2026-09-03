#include "MelodiaWaterNativeSimulationComponent.h"

#include "Engine/World.h"
#include "Components/ChildActorComponent.h"
#include "Components/SceneComponent.h"
#include "Materials/MaterialInterface.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterProfile.h"
#include "MelodiaWaterSimulationZone.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"
#include "WaterBodyComponent.h"
#include "WaterBodyActor.h"

namespace
{
	static FString NormalizeReflectionName(FString Name)
	{
		Name.ReplaceInline(TEXT(" "), TEXT(""));
		Name.ReplaceInline(TEXT("-"), TEXT(""));
		Name.ReplaceInline(TEXT("_"), TEXT(""));
		return Name;
	}

	static FProperty* FindPropertyLoose(UStruct* Struct, const TCHAR* DesiredName)
	{
		if (!Struct)
		{
			return nullptr;
		}

		const FString Wanted = NormalizeReflectionName(DesiredName);
		for (TFieldIterator<FProperty> It(Struct); It; ++It)
		{
			if (NormalizeReflectionName(It->GetName()).Equals(Wanted, ESearchCase::IgnoreCase))
			{
				return *It;
			}
		}

		return nullptr;
	}

	static UFunction* FindFunctionLoose(UObject* Object, const TCHAR* DesiredName)
	{
		if (!Object)
		{
			return nullptr;
		}

		const FString Wanted = NormalizeReflectionName(DesiredName);
		for (TFieldIterator<UFunction> It(Object->GetClass()); It; ++It)
		{
			if (NormalizeReflectionName(It->GetName()).Equals(Wanted, ESearchCase::IgnoreCase))
			{
				return *It;
			}
		}

		return nullptr;
	}

	static bool SetBoolProperty(UObject* Object, const TCHAR* Name, bool Value)
	{
		if (FBoolProperty* Property = CastField<FBoolProperty>(FindPropertyLoose(Object ? Object->GetClass() : nullptr, Name)))
		{
			Property->SetPropertyValue_InContainer(Object, Value);
			return true;
		}
		return false;
	}

	static bool SetIntProperty(UObject* Object, const TCHAR* Name, int32 Value)
	{
		if (FIntProperty* Property = CastField<FIntProperty>(FindPropertyLoose(Object ? Object->GetClass() : nullptr, Name)))
		{
			Property->SetPropertyValue_InContainer(Object, Value);
			return true;
		}
		return false;
	}

	static bool SetFloatProperty(UObject* Object, const TCHAR* Name, float Value)
	{
		FProperty* RawProperty = FindPropertyLoose(Object ? Object->GetClass() : nullptr, Name);
		if (FDoubleProperty* DoubleProperty = CastField<FDoubleProperty>(RawProperty))
		{
			DoubleProperty->SetPropertyValue_InContainer(Object, static_cast<double>(Value));
			return true;
		}
		if (FFloatProperty* FloatProperty = CastField<FFloatProperty>(RawProperty))
		{
			FloatProperty->SetPropertyValue_InContainer(Object, Value);
			return true;
		}
		return false;
	}

	static bool SetStructProperty(UObject* Object, const TCHAR* Name, const FVector2D& Value)
	{
		if (FStructProperty* Property = CastField<FStructProperty>(FindPropertyLoose(Object ? Object->GetClass() : nullptr, Name)))
		{
			if (Property->Struct == TBaseStructure<FVector2D>::Get())
			{
				*Property->ContainerPtrToValuePtr<FVector2D>(Object) = Value;
				return true;
			}
		}
		return false;
	}

	static bool SetStructProperty(UObject* Object, const TCHAR* Name, const FIntPoint& Value)
	{
		if (FStructProperty* Property = CastField<FStructProperty>(FindPropertyLoose(Object ? Object->GetClass() : nullptr, Name)))
		{
			if (Property->Struct == TBaseStructure<FIntPoint>::Get())
			{
				*Property->ContainerPtrToValuePtr<FIntPoint>(Object) = Value;
				return true;
			}
		}
		return false;
	}

	static void SetStructVector(UScriptStruct* Struct, void* StructMemory, const TCHAR* Name, const FVector& Value)
	{
		if (FStructProperty* Property = CastField<FStructProperty>(FindPropertyLoose(Struct, Name)))
		{
			if (Property->Struct == TBaseStructure<FVector>::Get())
			{
				*Property->ContainerPtrToValuePtr<FVector>(StructMemory) = Value;
			}
		}
	}

	static void SetStructFloat(UScriptStruct* Struct, void* StructMemory, const TCHAR* Name, float Value)
	{
		FProperty* RawProperty = FindPropertyLoose(Struct, Name);
		if (FDoubleProperty* DoubleProperty = CastField<FDoubleProperty>(RawProperty))
		{
			DoubleProperty->SetPropertyValue_InContainer(StructMemory, static_cast<double>(Value));
		}
		else if (FFloatProperty* FloatProperty = CastField<FFloatProperty>(RawProperty))
		{
			FloatProperty->SetPropertyValue_InContainer(StructMemory, Value);
		}
	}

	static void SetStructObject(UScriptStruct* Struct, void* StructMemory, const TCHAR* Name, UObject* Value)
	{
		if (FObjectPropertyBase* Property = CastField<FObjectPropertyBase>(FindPropertyLoose(Struct, Name)))
		{
			Property->SetObjectPropertyValue_InContainer(StructMemory, Value);
		}
	}

	/** Owning, aligned Blueprint ProcessEvent parameter pack. */
	struct FScopedFunctionParameters
	{
		explicit FScopedFunctionParameters(UFunction* InFunction)
			: Function(InFunction)
		{
			if (!Function || Function->ParmsSize <= 0)
			{
				return;
			}

			Data = static_cast<uint8*>(FMemory::Malloc(Function->ParmsSize, Function->MinAlignment));
			FMemory::Memzero(Data, Function->ParmsSize);
			for (TFieldIterator<FProperty> It(Function); It; ++It)
			{
				FProperty* Property = *It;
				if (Property && Property->HasAnyPropertyFlags(CPF_Parm)
					&& !Property->HasAnyPropertyFlags(CPF_ZeroConstructor))
				{
					Property->InitializeValue_InContainer(Data);
				}
			}
		}

		~FScopedFunctionParameters()
		{
			if (Data)
			{
				for (TFieldIterator<FProperty> It(Function); It; ++It)
				{
					FProperty* Property = *It;
					if (Property && Property->HasAnyPropertyFlags(CPF_Parm)
						&& !Property->HasAnyPropertyFlags(CPF_ZeroConstructor))
					{
						Property->DestroyValue_InContainer(Data);
					}
				}
				FMemory::Free(Data);
			}
		}

		uint8* GetData() const { return Data; }

		UFunction* Function = nullptr;
		uint8* Data = nullptr;
	};

	static FStructProperty* FindParameterStruct(UFunction* Function, UScriptStruct* ExpectedStruct)
	{
		if (!Function || !ExpectedStruct)
		{
			return nullptr;
		}

		for (TFieldIterator<FProperty> It(Function); It; ++It)
		{
			if (FStructProperty* StructParameter = CastField<FStructProperty>(*It))
			{
				if (StructParameter->HasAnyPropertyFlags(CPF_Parm)
					&& !StructParameter->HasAnyPropertyFlags(CPF_ReturnParm)
					&& StructParameter->Struct == ExpectedStruct)
				{
					return StructParameter;
				}
			}
		}

		return nullptr;
	}

	static UScriptStruct* LoadFluidStruct(const TCHAR* StructName)
	{
		const FString ObjectPath = FString::Printf(TEXT("/Water/FluidSimulation/Blueprints/Structs/%s.%s"), StructName, StructName);
		return LoadObject<UScriptStruct>(nullptr, *ObjectPath);
	}

	static UMaterialInterface* LoadFluidMaterial(const TCHAR* MaterialName)
	{
		const FString ObjectPath = FString::Printf(TEXT("/Water/FluidSimulation/Materials/Forces/%s.%s"), MaterialName, MaterialName);
		return LoadObject<UMaterialInterface>(nullptr, *ObjectPath);
	}
}

UMelodiaWaterNativeSimulationComponent::UMelodiaWaterNativeSimulationComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UMelodiaWaterProfile> ProfileFinder(
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default"));
	if (ProfileFinder.Succeeded())
	{
		Profile = ProfileFinder.Object;
	}
}

void UMelodiaWaterNativeSimulationComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
		if (WaterSubsystem)
		{
			WaterSubsystem->OnFluidImpulse.AddUniqueDynamic(this, &ThisClass::HandleFluidImpulse);
		}
	}

	RefreshNativeWaterBinding();
	if (AMelodiaWaterSimulationZone* Zone = Cast<AMelodiaWaterSimulationZone>(GetOwner()))
	{
		Zone->ConfigureEngineWaterComponents(Profile);
	}
	else
	{
		ConfigureEngineWaterComponents(Profile);
	}
}

void UMelodiaWaterNativeSimulationComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (WaterSubsystem)
	{
		WaterSubsystem->OnFluidImpulse.RemoveDynamic(this, &ThisClass::HandleFluidImpulse);
		WaterSubsystem = nullptr;
	}

	bNativeWaterReady = false;
	DynamicForcesThisWindow = 0;
	ImpulseForcesThisWindow = 0;
	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterNativeSimulationComponent::ConfigureAssignedEngineWaterComponents(UMelodiaWaterProfile* ProfileAsset)
{
	if (ProfileAsset)
	{
		Profile = ProfileAsset;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	TArray<UActorComponent*> Components;
	Owner->GetComponents(Components);
	EngineSimulationComponents.Reset();

	for (UActorComponent* Component : Components)
	{
		if (!Component)
		{
			continue;
		}

		const FString ClassName = Component->GetClass()->GetName();
		const bool bIsShallowWater = ClassName.Contains(TEXT("ShallowWaterSimComponent"));
		const bool bIsWaveFoam = ClassName.Contains(TEXT("WaveFoamSimComponent"));
		if (!bIsShallowWater && !bIsWaveFoam)
		{
			continue;
		}

		EngineSimulationComponents.Add(Component);
		SetBoolProperty(Component, TEXT("Enabled"), true);
		SetBoolProperty(Component, TEXT("bEnabled"), true);

		if (bIsShallowWater)
		{
			SetStructProperty(Component, TEXT("SimResolution"), FIntPoint(256, 256));
			SetStructProperty(Component, TEXT("SimWorldSize"), FVector2D(2048.0, 2048.0));
			SetFloatProperty(Component, TEXT("DeltaT"), 1.0f / 60.0f);
			SetIntProperty(Component, TEXT("SubSteps"), 1);
		}
		else
		{
			SetFloatProperty(Component, TEXT("SimulationWorldSize"), 2048.0f);
			SetFloatProperty(Component, TEXT("WaveSimWorldSize"), 2048.0f);
			SetFloatProperty(Component, TEXT("Fading"), 0.1f);
			SetIntProperty(Component, TEXT("WaveFoamResolution"), 512);
			SetIntProperty(Component, TEXT("Wave Foam Resolution"), 512);
		}
	}

	RefreshNativeWaterBinding();
}

void UMelodiaWaterNativeSimulationComponent::RouteImpulseToAssignedEngineWater(const FMelodiaWaterFluidImpulse& Impulse)
{
	if (!bNativeWaterReady || Impulse.ForceMode == EMelodiaWaterForceMode::Contact || !Impulse.bRouteToNativeWater)
	{
		return;
	}

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : Impulse.Timestamp;
	if (ForceBudgetWindowStart <= 0.0f || Now - ForceBudgetWindowStart >= 1.0f)
	{
		ForceBudgetWindowStart = Now;
		DynamicForcesThisWindow = 0;
		ImpulseForcesThisWindow = 0;
	}

	const int32 DynamicBudget = Profile ? FMath::Min(Profile->MaxNativeDynamicForces, NativeLimits.MaxDynamicForces) : NativeLimits.MaxDynamicForces;
	const int32 ImpulseBudget = Profile ? FMath::Min(Profile->MaxNativeImpulseForces, NativeLimits.MaxImpulseForces) : NativeLimits.MaxImpulseForces;
	if (Impulse.ForceMode == EMelodiaWaterForceMode::Dynamic && DynamicForcesThisWindow >= DynamicBudget)
	{
		return;
	}
	if (Impulse.ForceMode == EMelodiaWaterForceMode::Impulse && ImpulseForcesThisWindow >= ImpulseBudget)
	{
		return;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	TArray<UActorComponent*> Components;
	Owner->GetComponents(Components);
	for (UActorComponent* Component : Components)
	{
		UChildActorComponent* ChildComponent = Cast<UChildActorComponent>(Component);
		AActor* FluidActor = ChildComponent ? ChildComponent->GetChildActor() : nullptr;
		if (!FluidActor || !FluidActor->GetClass()->GetName().Contains(TEXT("FluidSim")))
		{
			continue;
		}

		const float ForceRadius = FMath::Clamp(Impulse.Radius, 8.0f, 512.0f);
		const float ForceStrength = -FMath::Clamp(Impulse.Strength * 1000.0f, 1.0f, 1000.0f);
		if (Impulse.ForceMode == EMelodiaWaterForceMode::Impulse)
		{
			UFunction* Function = FindFunctionLoose(FluidActor, TEXT("ApplyFluidForceImpulse"));
			UScriptStruct* ForceStruct = LoadFluidStruct(TEXT("FluidForceImpulse"));
			if (!Function || !ForceStruct)
			{
				continue;
			}

			FStructOnScope Scope(ForceStruct);
			SetStructVector(ForceStruct, Scope.GetStructMemory(), TEXT("WorldPosition"), Impulse.Location);
			SetStructFloat(ForceStruct, Scope.GetStructMemory(), TEXT("ForceRadius"), ForceRadius);
			SetStructFloat(ForceStruct, Scope.GetStructMemory(), TEXT("ForceStrength"), ForceStrength);
			SetStructObject(ForceStruct, Scope.GetStructMemory(), TEXT("MaterialOverride"), LoadFluidMaterial(TEXT("M_Fluid_Sim_Force_Impulse")));

			FStructProperty* StructParameter = FindParameterStruct(Function, ForceStruct);
			FScopedFunctionParameters ParameterScope(Function);
			uint8* Parameters = ParameterScope.GetData();
			if (!StructParameter || !Parameters)
			{
				continue;
			}

			StructParameter->CopyCompleteValue(
				StructParameter->ContainerPtrToValuePtr<void>(Parameters),
				Scope.GetStructMemory());
			FluidActor->ProcessEvent(Function, Parameters);
			++ImpulseForcesThisWindow;
		}
		else if (Impulse.ForceMode == EMelodiaWaterForceMode::Dynamic)
		{
			UFunction* Function = FindFunctionLoose(FluidActor, TEXT("RegisterDynamicForce"));
			UScriptStruct* ForceStruct = LoadFluidStruct(TEXT("FluidForceDynamic"));
			if (!Function || !ForceStruct)
			{
				continue;
			}

			FStructOnScope Scope(ForceStruct);
			SetStructFloat(ForceStruct, Scope.GetStructMemory(), TEXT("ForceRadius"), ForceRadius);
			SetStructFloat(ForceStruct, Scope.GetStructMemory(), TEXT("ForceStrength"), ForceStrength);
			SetStructObject(ForceStruct, Scope.GetStructMemory(), TEXT("MaterialOverride"), LoadFluidMaterial(TEXT("M_Fluid_Sim_Force_Component")));

			FScopedFunctionParameters ParameterScope(Function);
			uint8* Parameters = ParameterScope.GetData();
			if (!Parameters)
			{
				continue;
			}

			bool bFoundForceStruct = false;
			bool bFoundTrackedComponent = false;
			bool bFoundWaterLevel = false;
			for (TFieldIterator<FProperty> It(Function); It; ++It)
			{
				FProperty* Property = *It;
				if (!Property || !Property->HasAnyPropertyFlags(CPF_Parm)
					|| Property->HasAnyPropertyFlags(CPF_ReturnParm))
				{
					continue;
				}
				if (FStructProperty* StructParameter = CastField<FStructProperty>(Property))
				{
					if (StructParameter->Struct == ForceStruct)
					{
						StructParameter->CopyCompleteValue(
							StructParameter->ContainerPtrToValuePtr<void>(Parameters),
							Scope.GetStructMemory());
						bFoundForceStruct = true;
					}
				}
				else if (FObjectPropertyBase* ObjectParameter = CastField<FObjectPropertyBase>(Property))
				{
					if (ObjectParameter->PropertyClass && Component->IsA(ObjectParameter->PropertyClass))
					{
						ObjectParameter->SetObjectPropertyValue_InContainer(Parameters, Component);
						bFoundTrackedComponent = true;
					}
				}
				else if (FDoubleProperty* DoubleParameter = CastField<FDoubleProperty>(Property))
				{
					DoubleParameter->SetPropertyValue_InContainer(Parameters, static_cast<double>(Impulse.Location.Z));
					bFoundWaterLevel = true;
				}
				else if (FFloatProperty* FloatParameter = CastField<FFloatProperty>(Property))
				{
					FloatParameter->SetPropertyValue_InContainer(Parameters, Impulse.Location.Z);
					bFoundWaterLevel = true;
				}
			}

			if (!bFoundForceStruct || !bFoundTrackedComponent || !bFoundWaterLevel)
			{
				continue;
			}

			FluidActor->ProcessEvent(Function, Parameters);
			++DynamicForcesThisWindow;
		}

		return;
	}
}

void UMelodiaWaterNativeSimulationComponent::RefreshNativeWaterBinding()
{
	NativeLimits = FMelodiaWaterNativeLimits();
	bNativeWaterReady = false;

	if (!bEnabled || !WaterSubsystem)
	{
		return;
	}

	WaterSubsystem->GetNativeWaterLimits(NativeLimits);
	bNativeWaterReady = NativeLimits.bWaterAvailable && IsValid(WaterZone);
	if (Profile && Profile->SimulationTier >= EMelodiaWaterSimulationTier::ShallowWater2D)
	{
		bNativeWaterReady = bNativeWaterReady && NativeLimits.bShallowWaterSimulationEnabled;
	}
}

bool UMelodiaWaterNativeSimulationComponent::IsWaterBodyBound(FName WaterBodyId) const
{
	if (WaterBodyId.IsNone())
	{
		return true;
	}

	if (Profile && !Profile->WaterBodyId.IsNone() && Profile->WaterBodyId != WaterBodyId)
	{
		return false;
	}

	for (const UWaterBodyComponent* WaterBody : WaterBodies)
	{
		if (IsValid(WaterBody) && IsValid(WaterBody->GetWaterBodyActor()) && WaterBody->GetWaterBodyActor()->GetFName() == WaterBodyId)
		{
			return true;
		}
	}

	return WaterBodies.Num() == 0;
}

void UMelodiaWaterNativeSimulationComponent::HandleFluidImpulse(FMelodiaWaterFluidImpulse Impulse)
{
	if (!bNativeWaterReady || !Impulse.bRouteToNativeWater || !IsWaterBodyBound(Impulse.WaterBodyId))
	{
		return;
	}

	if (Profile)
	{
		if (Impulse.RequestedTier < Profile->SimulationTier || !Profile->bUseNativeWater || !Profile->bRouteContactsToNativeWater)
		{
			return;
		}
		if (!Profile->EffectProfileId.IsNone() && !Impulse.EffectProfileId.IsNone() && Profile->EffectProfileId != Impulse.EffectProfileId)
		{
			return;
		}
	}

	if (Impulse.ForceMode == EMelodiaWaterForceMode::Dynamic && NativeLimits.MaxDynamicForces <= 0)
	{
		return;
	}
	if (Impulse.ForceMode == EMelodiaWaterForceMode::Impulse && NativeLimits.MaxImpulseForces <= 0)
	{
		return;
	}

	if (AMelodiaWaterSimulationZone* Zone = Cast<AMelodiaWaterSimulationZone>(GetOwner()))
	{
		Zone->RouteImpulseToNativeWater(Impulse);
	}
	else
	{
		RouteImpulseToAssignedEngineWater(Impulse);
		RouteImpulseToNativeWater(Impulse);
	}
}
