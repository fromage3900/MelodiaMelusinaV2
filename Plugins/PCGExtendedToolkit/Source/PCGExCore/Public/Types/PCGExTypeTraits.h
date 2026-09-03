// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "PCGExCommon.h"
#include "Helpers/PCGExMetaHelpers.h" // FText shims + MetadataTraits<FText> specialization
#include "UObject/SoftObjectPath.h"

namespace PCGExTypes
{
	constexpr int TypesAllocations = 256; // Full uint8 range for EPCGMetadataTypes

	// Type Traits - Compile time type classification

	template <typename T>
	struct TTraits
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Unknown;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		// Euclidean-style numeric distance: |a-b|, length(a-b), or angular for FQuat.
		// Mutually exclusive with bSupportsMatchScore.
		static constexpr bool bSupportsDistance = false;
		// Categorical 0/1 equality distance (for types with no continuous ordering).
		static constexpr bool bSupportsMatchScore = false;
		// Per-side remap to [0, 1] before distance is meaningful (excludes ints, bool, FQuat, categoricals).
		static constexpr bool bSupportsNormalization = false;
	};

	// Numeric types
	template <>
	struct TTraits<bool>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Boolean;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = true;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE bool Min()
		{
			return false;
		}

		static FORCEINLINE bool Max()
		{
			return true;
		}
	};

	template <>
	struct TTraits<int32>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Integer32;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = true;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = false; // integer remap loses precision

		static FORCEINLINE int32 Min()
		{
			return TNumericLimits<int32>::Lowest();
		}

		static FORCEINLINE int32 Max()
		{
			return TNumericLimits<int32>::Max();
		}
	};

	template <>
	struct TTraits<int64>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Integer64;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = true;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = false; // integer remap loses precision

		static FORCEINLINE int64 Min()
		{
			return TNumericLimits<int64>::Lowest();
		}

		static FORCEINLINE int64 Max()
		{
			return TNumericLimits<int64>::Max();
		}
	};

	template <>
	struct TTraits<float>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Float;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = true;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		// "Smallest possible value" -- the most-negative finite float. NOT TNumericLimits<float>::Min(),
		// which returns the smallest *positive* normal value and would break Max-accumulator sentinels.
		static FORCEINLINE float Min()
		{
			return TNumericLimits<float>::Lowest();
		}

		static FORCEINLINE float Max()
		{
			return TNumericLimits<float>::Max();
		}
	};

	template <>
	struct TTraits<double>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Double;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = true;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		// "Smallest possible value" -- the most-negative finite double. NOT TNumericLimits<double>::Min(),
		// which returns the smallest *positive* normal value and would break Max-accumulator sentinels.
		static FORCEINLINE double Min()
		{
			return TNumericLimits<double>::Lowest();
		}

		static FORCEINLINE double Max()
		{
			return TNumericLimits<double>::Max();
		}
	};

	// Vector types
	template <>
	struct TTraits<FVector2D>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Vector2;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = true;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		static FORCEINLINE FVector2D Min()
		{
			return FVector2D(TNumericLimits<double>::Lowest());
		}

		static FORCEINLINE FVector2D Max()
		{
			return FVector2D(TNumericLimits<double>::Max());
		}
	};

	template <>
	struct TTraits<FVector>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Vector;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = true;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		static FORCEINLINE FVector Min()
		{
			return FVector(TNumericLimits<double>::Lowest());
		}

		static FORCEINLINE FVector Max()
		{
			return FVector(TNumericLimits<double>::Max());
		}
	};

	template <>
	struct TTraits<FVector4>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Vector4;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = true;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		static FORCEINLINE FVector4 Min()
		{
			return FVector4(TNumericLimits<double>::Lowest(), TNumericLimits<double>::Lowest(), TNumericLimits<double>::Lowest(), TNumericLimits<double>::Lowest());
		}

		static FORCEINLINE FVector4 Max()
		{
			return FVector4(TNumericLimits<double>::Max(), TNumericLimits<double>::Max(), TNumericLimits<double>::Max(), TNumericLimits<double>::Max());
		}
	};

	// Rotation types

	template <>
	struct TTraits<FRotator>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Rotator;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = true;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = true;
		static constexpr bool bSupportsArithmetic = true;

		static constexpr bool bSupportsDistance = true;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = true;

		static FORCEINLINE FRotator Min()
		{
			return FRotator(TNumericLimits<double>::Lowest(), TNumericLimits<double>::Lowest(), TNumericLimits<double>::Lowest());
		}

		static FORCEINLINE FRotator Max()
		{
			return FRotator(TNumericLimits<double>::Max(), TNumericLimits<double>::Max(), TNumericLimits<double>::Max());
		}
	};


	template <>
	struct TTraits<FQuat>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Quaternion;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = true;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = true; // angular: 1 - |dot|
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = false; // angular distance already in [0, 1]

		static FORCEINLINE FQuat Min()
		{
			return TTraits<FRotator>::Min().Quaternion();
		}

		static FORCEINLINE FQuat Max()
		{
			return TTraits<FRotator>::Max().Quaternion();
		}
	};

	template <>
	struct TTraits<FTransform>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Transform;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = false;
		static constexpr bool bSupportsLerp = true;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		// FTransform has no meaningful single-scalar distance -- composite of pos+rot+scale.
		static constexpr bool bSupportsDistance = false;
		static constexpr bool bSupportsMatchScore = false;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE FTransform Min()
		{
			return FTransform(TTraits<FQuat>::Min(), TTraits<FVector>::Min(), TTraits<FVector>::Min());
		}

		static FORCEINLINE FTransform Max()
		{
			return FTransform(TTraits<FQuat>::Max(), TTraits<FVector>::Max(), TTraits<FVector>::Max());
		}
	};

	// String types
	template <>
	struct TTraits<FString>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::String;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = true;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = false;
		static constexpr bool bSupportsMatchScore = true;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE FString Min()
		{
			return FString();
		}

		static FORCEINLINE FString Max()
		{
			return FString();
		}
	};

	template <>
	struct TTraits<FName>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::Name;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = true;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = false;
		static constexpr bool bSupportsMatchScore = true;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE FName Min()
		{
			return NAME_None;
		}

		static FORCEINLINE FName Max()
		{
			return NAME_None;
		}
	};

	template <>
	struct TTraits<FSoftObjectPath>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::SoftObjectPath;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = true;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = false;
		static constexpr bool bSupportsMatchScore = true;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE FSoftObjectPath Min()
		{
			return FSoftObjectPath();
		}

		static FORCEINLINE FSoftObjectPath Max()
		{
			return FSoftObjectPath();
		}
	};

	template <>
	struct TTraits<FSoftClassPath>
	{
		static constexpr EPCGMetadataTypes Type = EPCGMetadataTypes::SoftClassPath;
		static constexpr int16 TypeId = static_cast<int16>(Type);

		static constexpr bool bIsNumeric = false;
		static constexpr bool bIsVector = false;
		static constexpr bool bIsRotation = false;
		static constexpr bool bIsString = true;
		static constexpr bool bSupportsLerp = false;
		static constexpr bool bSupportsMinMax = false;
		static constexpr bool bSupportsArithmetic = false;

		static constexpr bool bSupportsDistance = false;
		static constexpr bool bSupportsMatchScore = true;
		static constexpr bool bSupportsNormalization = false;

		static FORCEINLINE FSoftClassPath Min()
		{
			return FSoftClassPath();
		}

		static FORCEINLINE FSoftClassPath Max()
		{
			return FSoftClassPath();
		}
	};

}
