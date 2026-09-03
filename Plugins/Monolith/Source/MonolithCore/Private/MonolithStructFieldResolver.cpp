#include "MonolithStructFieldResolver.h"

#include "UObject/UnrealType.h"
#include "UObject/Class.h"
#include "StructUtils/UserDefinedStruct.h"

namespace MonolithStructField
{
	namespace
	{
		// Match a single segment to a property within a struct/class. Direct
		// FindPropertyByName covers native structs and exact internal names; for a
		// UserDefinedStruct we additionally match each field by its authored
		// (friendly) name, since UDS fields carry a "_<index>_<GUID>" internal suffix.
		const FProperty* FindFieldBySegment(const UStruct* Owner, const FString& Segment)
		{
			if (!Owner)
			{
				return nullptr;
			}

			if (const FProperty* Direct = Owner->FindPropertyByName(FName(*Segment)))
			{
				return Direct;
			}

			if (const UUserDefinedStruct* UserStruct = Cast<UUserDefinedStruct>(Owner))
			{
				for (TFieldIterator<FProperty> It(UserStruct); It; ++It)
				{
					if (UserStruct->GetAuthoredNameForField(*It) == Segment)
					{
						return *It;
					}
				}
			}

			return nullptr;
		}
	}

	FResolved Resolve(const UObject* Container, const FString& Path)
	{
		FResolved Out;
		if (!Container)
		{
			Out.FailedSegment = Path;
			return Out;
		}

		// Non-dotted: flat lookup on the object's class (back-compat base case).
		if (!Path.Contains(TEXT(".")))
		{
			const FProperty* Prop = FindFieldBySegment(Container->GetClass(), Path);
			if (!Prop)
			{
				Out.FailedSegment = Path;
				return Out;
			}
			Out.Leaf = Prop;
			Out.ValuePtr = Prop->ContainerPtrToValuePtr<void>(Container);
			return Out;
		}

		TArray<FString> Segments;
		Path.ParseIntoArray(Segments, TEXT("."), /*CullEmpty=*/true);
		if (Segments.Num() == 0)
		{
			Out.FailedSegment = Path;
			return Out;
		}

		const UStruct* CurrentOwner = Container->GetClass();
		const void* CurrentBase = Container;

		for (int32 i = 0; i < Segments.Num(); ++i)
		{
			const FProperty* Prop = FindFieldBySegment(CurrentOwner, Segments[i]);
			if (!Prop)
			{
				Out.FailedSegment = Segments[i];
				return Out;
			}

			const void* ValuePtr = Prop->ContainerPtrToValuePtr<void>(CurrentBase);

			const bool bLeaf = (i == Segments.Num() - 1);
			if (bLeaf)
			{
				Out.Leaf = Prop;
				Out.ValuePtr = ValuePtr;
				return Out;
			}

			// Non-leaf segments must be structs to descend further.
			const FStructProperty* StructProp = CastField<FStructProperty>(Prop);
			if (!StructProp || !StructProp->Struct)
			{
				Out.FailedSegment = Segments[i];
				return Out;
			}
			CurrentOwner = StructProp->Struct;
			CurrentBase = ValuePtr;
		}

		Out.FailedSegment = Path;
		return Out;
	}
}
