// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExK2NodeTypeHelpers.h"

#include "EdGraphSchema_K2.h"
#include "Metadata/PCGMetadataAttributeTraits.h"

#define LOCTEXT_NAMESPACE "PCGExK2NodeTypeHelpers"

namespace PCGExK2NodeTypeHelpers
{
	bool MakePinTypeForMetadataType(EPCGMetadataTypes Type, FEdGraphPinType& OutPinType)
	{
		OutPinType = FEdGraphPinType();
		OutPinType.ContainerType = EPinContainerType::None;

		switch (Type)
		{
		case EPCGMetadataTypes::Float:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Real;
			OutPinType.PinSubCategory = UEdGraphSchema_K2::PC_Float;
			return true;
		case EPCGMetadataTypes::Double:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Real;
			OutPinType.PinSubCategory = UEdGraphSchema_K2::PC_Double;
			return true;
		case EPCGMetadataTypes::Integer32:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Int;
			return true;
		case EPCGMetadataTypes::Integer64:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Int64;
			return true;
		case EPCGMetadataTypes::Boolean:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
			return true;
		case EPCGMetadataTypes::Name:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Name;
			return true;
		case EPCGMetadataTypes::String:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_String;
			return true;
		case EPCGMetadataTypes::Vector2:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FVector2D>::Get();
			return true;
		case EPCGMetadataTypes::Vector:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FVector>::Get();
			return true;
		case EPCGMetadataTypes::Vector4:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FVector4>::Get();
			return true;
		case EPCGMetadataTypes::Quaternion:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FQuat>::Get();
			return true;
		case EPCGMetadataTypes::Rotator:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FRotator>::Get();
			return true;
		case EPCGMetadataTypes::Transform:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FTransform>::Get();
			return true;
		case EPCGMetadataTypes::SoftObjectPath:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FSoftObjectPath>::Get();
			return true;
		case EPCGMetadataTypes::SoftClassPath:
			OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
			OutPinType.PinSubCategoryObject = TBaseStructure<FSoftClassPath>::Get();
			return true;
		default:
			return false;
		}
	}

	FText GetDisplayNameForMetadataType(EPCGMetadataTypes Type)
	{
		switch (Type)
		{
		case EPCGMetadataTypes::Float:
			return LOCTEXT("Type_Float", "Float");
		case EPCGMetadataTypes::Double:
			return LOCTEXT("Type_Double", "Double");
		case EPCGMetadataTypes::Integer32:
			return LOCTEXT("Type_Int32", "Integer (32-bit)");
		case EPCGMetadataTypes::Integer64:
			return LOCTEXT("Type_Int64", "Integer (64-bit)");
		case EPCGMetadataTypes::Boolean:
			return LOCTEXT("Type_Bool", "Boolean");
		case EPCGMetadataTypes::Name:
			return LOCTEXT("Type_Name", "Name");
		case EPCGMetadataTypes::String:
			return LOCTEXT("Type_String", "String");
		case EPCGMetadataTypes::Vector2:
			return LOCTEXT("Type_Vector2", "Vector 2D");
		case EPCGMetadataTypes::Vector:
			return LOCTEXT("Type_Vector", "Vector");
		case EPCGMetadataTypes::Vector4:
			return LOCTEXT("Type_Vector4", "Vector 4");
		case EPCGMetadataTypes::Quaternion:
			return LOCTEXT("Type_Quat", "Quaternion");
		case EPCGMetadataTypes::Rotator:
			return LOCTEXT("Type_Rotator", "Rotator");
		case EPCGMetadataTypes::Transform:
			return LOCTEXT("Type_Transform", "Transform");
		case EPCGMetadataTypes::SoftObjectPath:
			return LOCTEXT("Type_SoftObjectPath", "Soft Object Path");
		case EPCGMetadataTypes::SoftClassPath:
			return LOCTEXT("Type_SoftClassPath", "Soft Class Path");
		default:
			return LOCTEXT("Type_Unknown", "Unknown");
		}
	}
}

#undef LOCTEXT_NAMESPACE
