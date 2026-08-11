// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Elements/PCGExDataHash.h"

#include "PCGContext.h"
#include "PCGGraph.h"
#include "PCGParamData.h"
#include "PCGPin.h"
#include "Data/PCGBasePointData.h"
#include "Data/PCGPolyLineData.h"
#include "Data/PCGSpatialData.h"
#include "Helpers/PCGExMetaHelpers.h"
#include "Metadata/PCGMetadata.h"
#include "Misc/Crc.h"

#define LOCTEXT_NAMESPACE "PCGExDataHashElement"
#define PCGEX_NAMESPACE DataHash

namespace PCGExDataHash
{
	EPCGMetadataTypes ToMetadataType(EPCGExDataHashType InType)
	{
		switch (InType)
		{
		case EPCGExDataHashType::Bool:
			return EPCGMetadataTypes::Boolean;
		case EPCGExDataHashType::Int32:
			return EPCGMetadataTypes::Integer32;
		case EPCGExDataHashType::Int64:
			return EPCGMetadataTypes::Integer64;
		case EPCGExDataHashType::Float:
			return EPCGMetadataTypes::Float;
		case EPCGExDataHashType::Double:
			return EPCGMetadataTypes::Double;
		case EPCGExDataHashType::Vector2:
			return EPCGMetadataTypes::Vector2;
		case EPCGExDataHashType::Vector:
			return EPCGMetadataTypes::Vector;
		case EPCGExDataHashType::Vector4:
			return EPCGMetadataTypes::Vector4;
		case EPCGExDataHashType::Quaternion:
			return EPCGMetadataTypes::Quaternion;
		case EPCGExDataHashType::Rotator:
			return EPCGMetadataTypes::Rotator;
		case EPCGExDataHashType::Transform:
			return EPCGMetadataTypes::Transform;
		default:
			return EPCGMetadataTypes::Unknown;
		}
	}

	uint32 HashBox(const FBox& InBox)
	{
		uint32 H = GetTypeHash(InBox.Min.X);
		H = HashCombine(H, GetTypeHash(InBox.Min.Y));
		H = HashCombine(H, GetTypeHash(InBox.Min.Z));
		H = HashCombine(H, GetTypeHash(InBox.Max.X));
		H = HashCombine(H, GetTypeHash(InBox.Max.Y));
		H = HashCombine(H, GetTypeHash(InBox.Max.Z));
		return H;
	}

	// FCrc::StrCrc32 is deterministic across sessions, platforms, and builds.
	// We use it instead of GetTypeHash(FName) which depends on FName pool insertion order.
	uint32 StableClassHash(const UPCGData* Data)
	{
		if (!Data)
		{
			return 0u;
		}
		// GetClass()->GetName() returns the class's short name (e.g. "PCGBasePointData"),
		// stable as long as the class isn't renamed at the C++ level.
		return FCrc::StrCrc32(*Data->GetClass()->GetName());
	}

	uint32 HashInput(const UPCGData* Data)
	{
		if (!Data)
		{
			return 0u;
		}

		uint32 H = StableClassHash(Data);

		if (const UPCGBasePointData* PointData = Cast<UPCGBasePointData>(Data))
		{
			H = HashCombine(H, GetTypeHash(PointData->GetNumPoints()));
			H = HashCombine(H, HashBox(PointData->GetBounds()));
			return H;
		}

		if (const UPCGPolyLineData* PolyLineData = Cast<UPCGPolyLineData>(Data))
		{
			H = HashCombine(H, GetTypeHash(PolyLineData->GetNumSegments()));
			H = HashCombine(H, HashBox(PolyLineData->GetBounds()));
			return H;
		}

		if (const UPCGParamData* ParamData = Cast<UPCGParamData>(Data))
		{
			const UPCGMetadata* Metadata = ParamData->ConstMetadata();
			H = HashCombine(H, GetTypeHash(Metadata ? Metadata->GetLocalItemCount() : 0));
			return H;
		}

		if (const UPCGSpatialData* SpatialData = Cast<UPCGSpatialData>(Data))
		{
			H = HashCombine(H, HashBox(SpatialData->GetBounds()));
			return H;
		}

		return H;
	}

	// Computes [Min,Max] given the user's range settings and the value type.
	// When bUseRange is OFF, defaults to:
	//   - integer types: full type range
	//   - everything else: [-1, 1]
	// Scale components of Transform get their own [0, 1] default and use the
	// shared resolved range when bUseRange is on (handled inline at the call site).
	void GetResolvedRange(const UPCGExDataHashSettings* Settings, EPCGExDataHashType ForType, double& OutMin, double& OutMax)
	{
		if (Settings->bUseRange)
		{
			OutMin = FMath::Min(Settings->RangeMin, Settings->RangeMax);
			OutMax = FMath::Max(Settings->RangeMin, Settings->RangeMax);
			return;
		}

		switch (ForType)
		{
		case EPCGExDataHashType::Int32:
			OutMin = static_cast<double>(MIN_int32);
			OutMax = static_cast<double>(MAX_int32);
			return;
		case EPCGExDataHashType::Int64:
			// Full int64 range; handled specially in the random path.
			OutMin = static_cast<double>(MIN_int64);
			OutMax = static_cast<double>(MAX_int64);
			return;
		default:
			OutMin = -1.0;
			OutMax = 1.0;
			return;
		}
	}

	// Uniform random unit quaternion (Shoemake).
	FQuat RandomUnitQuat(FRandomStream& Stream)
	{
		const double U1 = static_cast<double>(Stream.GetFraction());
		const double U2 = static_cast<double>(Stream.GetFraction());
		const double U3 = static_cast<double>(Stream.GetFraction());

		const double S1 = FMath::Sqrt(1.0 - U1);
		const double S2 = FMath::Sqrt(U1);
		const double T2 = 2.0 * UE_DOUBLE_PI * U2;
		const double T3 = 2.0 * UE_DOUBLE_PI * U3;

		return FQuat(
			S1 * FMath::Sin(T2),
			S1 * FMath::Cos(T2),
			S2 * FMath::Sin(T3),
			S2 * FMath::Cos(T3));
	}

	// Quaternion from per-axis Euler degrees in [Min,Max] (used when bUseRange is on).
	FQuat RandomEulerQuat(FRandomStream& Stream, double Min, double Max)
	{
		const FRotator R(Stream.FRandRange(Min, Max), Stream.FRandRange(Min, Max), Stream.FRandRange(Min, Max));
		return R.Quaternion();
	}

	// FRandomStream::RandRange(MIN_int32, MAX_int32) overflows when computing
	// (Max - Min + 1), so the full-range case needs its own path.
	int32 RandomInt32(FRandomStream& Stream, int32 Min, int32 Max)
	{
		if (Min == MIN_int32 && Max == MAX_int32)
		{
			return static_cast<int32>(Stream.GetUnsignedInt());
		}
		if (Max <= Min)
		{
			return Min;
		}
		return Stream.RandRange(Min, Max);
	}

	int64 RandomInt64(FRandomStream& Stream, int64 Min, int64 Max)
	{
		const uint64 Raw =
			(static_cast<uint64>(static_cast<uint32>(Stream.GetUnsignedInt())) << 32) |
			static_cast<uint64>(static_cast<uint32>(Stream.GetUnsignedInt()));

		if (Min == MIN_int64 && Max == MAX_int64)
		{
			return static_cast<int64>(Raw);
		}

		if (Max <= Min)
		{
			return Min;
		}

		const uint64 Span = static_cast<uint64>(Max - Min) + 1ULL;
		return Min + static_cast<int64>(Raw % Span);
	}
}

#if WITH_EDITOR
FString UPCGExDataHashSettings::GetEnumDisplayName() const
{
	const UEnum* EnumPtr = StaticEnum<EPCGExDataHashType>();
	if (!EnumPtr)
	{
		return FString();
	}
	return EnumPtr->GetDisplayNameTextByValue(static_cast<int64>(OutputType)).ToString();
}
#endif

#if PCGEX_ENGINE_VERSION >= 507
FPCGDataTypeIdentifier UPCGExDataHashSettings::GetCurrentPinTypesID(const UPCGPin* InPin) const
{
	if (!InPin->IsOutputPin() || InPin->Properties.Label != PCGExDataHash::OutputValueLabel)
	{
		return Super::GetCurrentPinTypesID(InPin);
	}

	FPCGDataTypeIdentifier Id = FPCGDataTypeInfoParam::AsId();
	Id.CustomSubtype = static_cast<int32>(PCGExDataHash::ToMetadataType(OutputType));
	return Id;
}
#endif

TArray<FPCGPinProperties> UPCGExDataHashSettings::InputPinProperties() const
{
	TArray<FPCGPinProperties> PinProperties;
	PCGEX_PIN_ANY(PCGPinConstants::DefaultInputLabel, "Any combination of data. The output value is a deterministic function of the inputs' class, element count, spatial bounds, plus the Salt.", Normal)
	return PinProperties;
}

TArray<FPCGPinProperties> UPCGExDataHashSettings::OutputPinProperties() const
{
	TArray<FPCGPinProperties> PinProperties;
	PCGEX_PIN_PARAM(PCGExDataHash::OutputValueLabel, "Single random value derived from the input data.", Required)
	return PinProperties;
}

FPCGElementPtr UPCGExDataHashSettings::CreateElement() const
{
	return MakeShared<FPCGExDataHashElement>();
}

bool FPCGExDataHashElement::ExecuteInternal(FPCGContext* Context) const
{
	check(Context);
	const UPCGExDataHashSettings* Settings = Context->GetInputSettings<UPCGExDataHashSettings>();
	check(Settings);

	if (!PCGExMetaHelpers::IsWritableAttributeName(Settings->OutputAttributeName))
	{
		PCGE_LOG_C(Error, GraphAndLog, Context, FText::Format(FTEXT("\"{0}\" is not a valid attribute name."), FText::FromName(Settings->OutputAttributeName)));
		return true;
	}

	// Hash all inputs on the default pin. Order matters: changing connection order
	// changes the value, consistent with how PCG iterates pin inputs.
	uint32 Hash = GetTypeHash(Settings->Salt);

	const TArray<FPCGTaggedData> Inputs = Context->InputData.GetInputsByPin(PCGPinConstants::DefaultInputLabel);
	Hash = HashCombine(Hash, GetTypeHash(Inputs.Num()));

	for (const FPCGTaggedData& Tagged : Inputs)
	{
		Hash = HashCombine(Hash, PCGExDataHash::HashInput(Tagged.Data));
	}

	FRandomStream Stream(static_cast<int32>(Hash));

	UPCGParamData* OutputData = FPCGContext::NewObject_AnyThread<UPCGParamData>(Context);
	check(OutputData && OutputData->Metadata);

	const FName AttrName = Settings->OutputAttributeName;
	const PCGMetadataEntryKey Entry = OutputData->Metadata->AddEntry();

	double RMin = 0.0;
	double RMax = 0.0;
	PCGExDataHash::GetResolvedRange(Settings, Settings->OutputType, RMin, RMax);

	switch (Settings->OutputType)
	{
	case EPCGExDataHashType::Bool:
	{
		const bool Value = Stream.RandRange(0, 1) != 0;
		FPCGMetadataAttribute<bool>* Attr = OutputData->Metadata->CreateAttribute<bool>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Int32:
	{
		const int32 Min32 = Settings->bUseRange ? static_cast<int32>(FMath::Clamp(RMin, static_cast<double>(MIN_int32), static_cast<double>(MAX_int32))) : MIN_int32;
		const int32 Max32 = Settings->bUseRange ? static_cast<int32>(FMath::Clamp(RMax, static_cast<double>(MIN_int32), static_cast<double>(MAX_int32))) : MAX_int32;
		const int32 Value = PCGExDataHash::RandomInt32(Stream, Min32, Max32);
		FPCGMetadataAttribute<int32>* Attr = OutputData->Metadata->CreateAttribute<int32>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Int64:
	{
		const int64 Min64 = Settings->bUseRange ? static_cast<int64>(FMath::Clamp(RMin, static_cast<double>(MIN_int64), static_cast<double>(MAX_int64))) : MIN_int64;
		const int64 Max64 = Settings->bUseRange ? static_cast<int64>(FMath::Clamp(RMax, static_cast<double>(MIN_int64), static_cast<double>(MAX_int64))) : MAX_int64;
		const int64 Value = PCGExDataHash::RandomInt64(Stream, Min64, Max64);
		FPCGMetadataAttribute<int64>* Attr = OutputData->Metadata->CreateAttribute<int64>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Float:
	{
		const float Value = static_cast<float>(Stream.FRandRange(RMin, RMax));
		FPCGMetadataAttribute<float>* Attr = OutputData->Metadata->CreateAttribute<float>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Double:
	{
		const double Value = Stream.FRandRange(RMin, RMax);
		FPCGMetadataAttribute<double>* Attr = OutputData->Metadata->CreateAttribute<double>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Vector2:
	{
		const FVector2D Value(Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax));
		FPCGMetadataAttribute<FVector2D>* Attr = OutputData->Metadata->CreateAttribute<FVector2D>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Vector:
	{
		const FVector Value(Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax));
		FPCGMetadataAttribute<FVector>* Attr = OutputData->Metadata->CreateAttribute<FVector>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Vector4:
	{
		const FVector4 Value(Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax));
		FPCGMetadataAttribute<FVector4>* Attr = OutputData->Metadata->CreateAttribute<FVector4>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Quaternion:
	{
		const FQuat Value = Settings->bUseRange
			? PCGExDataHash::RandomEulerQuat(Stream, RMin, RMax)
			: PCGExDataHash::RandomUnitQuat(Stream);
		FPCGMetadataAttribute<FQuat>* Attr = OutputData->Metadata->CreateAttribute<FQuat>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Rotator:
	{
		const FRotator Value(Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax));
		FPCGMetadataAttribute<FRotator>* Attr = OutputData->Metadata->CreateAttribute<FRotator>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	case EPCGExDataHashType::Transform:
	{
		const FVector Location(Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax), Stream.FRandRange(RMin, RMax));
		const FQuat Rotation = Settings->bUseRange
			? PCGExDataHash::RandomEulerQuat(Stream, RMin, RMax)
			: PCGExDataHash::RandomUnitQuat(Stream);
		// Scale: special case [0,1] when range is off, otherwise share the user's range.
		const double ScaleMin = Settings->bUseRange ? RMin : 0.0;
		const double ScaleMax = Settings->bUseRange ? RMax : 1.0;
		const FVector Scale(Stream.FRandRange(ScaleMin, ScaleMax), Stream.FRandRange(ScaleMin, ScaleMax), Stream.FRandRange(ScaleMin, ScaleMax));
		const FTransform Value(Rotation, Location, Scale);
		FPCGMetadataAttribute<FTransform>* Attr = OutputData->Metadata->CreateAttribute<FTransform>(AttrName, Value, true, true);
		Attr->SetValue(Entry, Value);
		break;
	}
	}

	FPCGTaggedData& Staged = Context->OutputData.TaggedData.Emplace_GetRef();
	Staged.Pin = PCGExDataHash::OutputValueLabel;
	Staged.Data = OutputData;

	return true;
}

#undef LOCTEXT_NAMESPACE
#undef PCGEX_NAMESPACE
