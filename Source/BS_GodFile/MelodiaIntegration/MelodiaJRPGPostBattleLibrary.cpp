#include "MelodiaJRPGPostBattleLibrary.h"

#include "StructUtils/UserDefinedStruct.h"
#include "UObject/UnrealType.h"

namespace
{
	/** Resolve a UUserDefinedStruct member's internal (GUID-suffixed) property by authored name. */
	FProperty* FindAuthoredStructMember(const UStruct* Struct, const TCHAR* AuthoredName)
	{
		if (!Struct)
		{
			return nullptr;
		}
		for (FProperty* Prop : TFieldRange<FProperty>(Struct))
		{
			FString Authored = FName::NameToDisplayString(Prop->GetName(), false);
			if (const UUserDefinedStruct* UDS = Cast<UUserDefinedStruct>(Struct))
			{
				Authored = UDS->GetAuthoredNameForField(Prop);
			}
			if (Authored == AuthoredName)
			{
				return Prop;
			}
		}
		return nullptr;
	}
}

void UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(UObject* BattleController)
{
	if (!IsValid(BattleController))
	{
		return;
	}

	// The stock controller names its active battle base through this variable.
	// Mirror the party bootstrap's reflection pattern: read the property, never
	// cast to a generated class that may not be loaded.
	FObjectPropertyBase* BattleProperty = FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("battle"));
	if (!BattleProperty)
	{
		BattleProperty = FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("currentBattle"));
	}
	UObject* BattleBase = BattleProperty ? BattleProperty->GetObjectPropertyValue_InContainer(BattleController) : nullptr;
	if (!IsValid(BattleBase))
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_RECOVERY no battle base on '%s'; party not restored."), *GetNameSafe(BattleController));
		return;
	}

	FArrayProperty* PlayerUnitsProperty = FindFProperty<FArrayProperty>(BattleBase->GetClass(), TEXT("playerUnits"));
	if (!PlayerUnitsProperty)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_RECOVERY battle base '%s' has no playerUnits array; party not restored."), *GetNameSafe(BattleBase));
		return;
	}

	FObjectPropertyBase* ElementProperty = CastField<FObjectPropertyBase>(PlayerUnitsProperty->Inner);
	if (!ElementProperty)
	{
		return;
	}

	FScriptArrayHelper ArrayHelper(PlayerUnitsProperty, PlayerUnitsProperty->ContainerPtrToValuePtr<void>(BattleBase));
	int32 RestoredCount = 0;

	// The controller's persistent per-unit state map (TMap<UClass*, FS_UnitState>).
	// The stock syncs battle state back into it; on defeat there is no sync, so a
	// unit that died mid-battle would respawn dead next encounter. Write the
	// restored values into the map as well, by class key.
	FMapProperty* PartyMapProperty = FindFProperty<FMapProperty>(BattleController->GetClass(), TEXT("playerUnits"));
	const UStruct* UnitStateStruct = nullptr;
	// These must be the concrete numeric type: FProperty has no typed accessor.
	FIntProperty* MapCurrentHP = nullptr;
	FIntProperty* MapCurrentMP = nullptr;
	if (PartyMapProperty)
	{
		if (FStructProperty* StateStructProp = CastField<FStructProperty>(PartyMapProperty->ValueProp))
		{
			UnitStateStruct = StateStructProp->Struct;
			MapCurrentHP = CastField<FIntProperty>(FindAuthoredStructMember(UnitStateStruct, TEXT("currentHP")));
			// Stock FS_UnitState / unit fields use currentMP (catalog + unit
			// instance property). The earlier curentMP lookup was a typo guess
			// that null'd the map write and skipped persistent HP/MP restore.
			MapCurrentMP = CastField<FIntProperty>(FindAuthoredStructMember(UnitStateStruct, TEXT("currentMP")));
		}
	}

	for (int32 Index = 0; Index < ArrayHelper.Num(); ++Index)
	{
		UObject* Unit = ElementProperty->GetObjectPropertyValue(ArrayHelper.GetRawPtr(Index));
		if (!IsValid(Unit))
		{
			continue;
		}

		const FIntProperty* MaxHPProperty = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("maxHP"));
		const FIntProperty* MaxMPProperty = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("maxMP"));
		FIntProperty* CurrentHPProperty = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("currentHP"));
		FIntProperty* CurrentMPProperty = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("currentMP"));

		const int32 MaxHP = (CurrentHPProperty && MaxHPProperty) ? MaxHPProperty->GetPropertyValue_InContainer(Unit) : 0;
		const int32 MaxMP = (CurrentMPProperty && MaxMPProperty) ? MaxMPProperty->GetPropertyValue_InContainer(Unit) : 0;

		if (CurrentHPProperty && MaxHPProperty && CurrentHPProperty->GetPropertyValue_InContainer(Unit) != MaxHP)
		{
			CurrentHPProperty->SetPropertyValue_InContainer(Unit, MaxHP);
		}
		if (CurrentMPProperty && MaxMPProperty && CurrentMPProperty->GetPropertyValue_InContainer(Unit) != MaxMP)
		{
			CurrentMPProperty->SetPropertyValue_InContainer(Unit, MaxMP);
		}

		// Persist the restored values into the controller's map entry for this
		// unit's class, so the next encounter spawns the unit alive.
		if (PartyMapProperty && MapCurrentHP && MapCurrentMP && UnitStateStruct && Unit->GetClass())
		{
			// FindMapIndexWithKey takes the address of the key, so the key must be a
			// named l-value -- GetClass() returns a temporary.
			UClass* UnitClass = Unit->GetClass();
			FScriptMapHelper MapHelper(PartyMapProperty, PartyMapProperty->ContainerPtrToValuePtr<void>(BattleController));
			const int32 MapIndex = MapHelper.FindMapIndexWithKey(&UnitClass);
			if (MapIndex != INDEX_NONE)
			{
				uint8* MapValue = MapHelper.GetValuePtr(MapIndex);
				if (MapValue)
				{
					if (MapCurrentHP->GetPropertyValue_InContainer(MapValue) != MaxHP)
					{
						MapCurrentHP->SetPropertyValue_InContainer(MapValue, MaxHP);
					}
					if (MapCurrentMP->GetPropertyValue_InContainer(MapValue) != MaxMP)
					{
						MapCurrentMP->SetPropertyValue_InContainer(MapValue, MaxMP);
					}
				}
			}
		}

		++RestoredCount;
	}

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RECOVERY restored %d player unit(s) to full HP/MP after battle (instances + persistent map)."), RestoredCount);
}
