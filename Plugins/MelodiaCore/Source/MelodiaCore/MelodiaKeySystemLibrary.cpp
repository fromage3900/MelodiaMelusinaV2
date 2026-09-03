// Element weakness wheel and harmonic key damage rules.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#include "MelodiaKeySystemLibrary.h"

namespace
{
/** Cyclic weakness wheel: Forte > Gale > Stone > Tide > Radiant > Umbral > Arcane > Forte */
EMelodiaSpellElement GetWeaknessOf(EMelodiaSpellElement Element)
{
	switch (Element)
	{
	case EMelodiaSpellElement::Forte:   return EMelodiaSpellElement::Gale;
	case EMelodiaSpellElement::Gale:    return EMelodiaSpellElement::Stone;
	case EMelodiaSpellElement::Stone:   return EMelodiaSpellElement::Tide;
	case EMelodiaSpellElement::Tide:    return EMelodiaSpellElement::Radiant;
	case EMelodiaSpellElement::Radiant: return EMelodiaSpellElement::Umbral;
	case EMelodiaSpellElement::Umbral:  return EMelodiaSpellElement::Arcane;
	case EMelodiaSpellElement::Arcane:
	default:                            return EMelodiaSpellElement::Forte;
	}
}

EMelodiaSpellElement GetStrengthOf(EMelodiaSpellElement Element)
{
	switch (Element)
	{
	case EMelodiaSpellElement::Forte:   return EMelodiaSpellElement::Arcane;
	case EMelodiaSpellElement::Gale:    return EMelodiaSpellElement::Forte;
	case EMelodiaSpellElement::Stone:   return EMelodiaSpellElement::Gale;
	case EMelodiaSpellElement::Tide:    return EMelodiaSpellElement::Stone;
	case EMelodiaSpellElement::Radiant: return EMelodiaSpellElement::Tide;
	case EMelodiaSpellElement::Umbral:  return EMelodiaSpellElement::Radiant;
	case EMelodiaSpellElement::Arcane:
	default:                            return EMelodiaSpellElement::Umbral;
	}
}

FMelodiaElementKeyDefinition MakeKey(const FName KeyId, const TCHAR* Name, const EMelodiaSpellElement Element, const int32 Level, const TCHAR* Blurb)
{
	FMelodiaElementKeyDefinition Key;
	Key.KeyId = KeyId;
	Key.DisplayName = FText::FromString(Name);
	Key.Element = Element;
	Key.MechanicLevelRequired = Level;
	Key.UnlockBlurb = FText::FromString(Blurb);
	return Key;
}
}

TArray<FMelodiaElementKeyDefinition> UMelodiaKeySystemLibrary::BuildDemoElementKeys()
{
	TArray<FMelodiaElementKeyDefinition> Keys;
	Keys.Add(MakeKey(TEXT("Key_Lv03_Forte"), TEXT("Forte Key"), EMelodiaSpellElement::Forte, 3, TEXT("Unlocks at Lv3 ΓÇö +25% on Forte weakness hits.")));
	Keys.Add(MakeKey(TEXT("Key_Lv06_Tide"), TEXT("Tide Key"), EMelodiaSpellElement::Tide, 6, TEXT("Unlocks at Lv6 ΓÇö harmonic tide resonance.")));
	Keys.Add(MakeKey(TEXT("Key_Lv09_Gale"), TEXT("Gale Key"), EMelodiaSpellElement::Gale, 9, TEXT("Unlocks at Lv9 ΓÇö wind-aligned key.")));
	Keys.Add(MakeKey(TEXT("Key_Lv12_Stone"), TEXT("Stone Key"), EMelodiaSpellElement::Stone, 12, TEXT("Unlocks at Lv12 ΓÇö earth anchor.")));
	Keys.Add(MakeKey(TEXT("Key_Lv15_Radiant"), TEXT("Radiant Key"), EMelodiaSpellElement::Radiant, 15, TEXT("Unlocks at Lv15 ΓÇö light harmonic.")));
	Keys.Add(MakeKey(TEXT("Key_Lv18_Umbral"), TEXT("Umbral Key"), EMelodiaSpellElement::Umbral, 18, TEXT("Unlocks at Lv18 ΓÇö shadow resonance.")));
	Keys.Add(MakeKey(TEXT("Key_Lv21_Arcane"), TEXT("Arcane Key"), EMelodiaSpellElement::Arcane, 21, TEXT("Unlocks at Lv21 ΓÇö arcane mastery.")));
	return Keys;
}

bool UMelodiaKeySystemLibrary::FindElementKey(const FName KeyId, FMelodiaElementKeyDefinition& OutKey)
{
	if (KeyId.IsNone())
	{
		return false;
	}

	for (const FMelodiaElementKeyDefinition& Key : BuildDemoElementKeys())
	{
		if (Key.KeyId == KeyId)
		{
			OutKey = Key;
			return true;
		}
	}
	return false;
}

FName UMelodiaKeySystemLibrary::GetKeyIdForMechanicLevel(const int32 MechanicLevel)
{
	for (const FMelodiaElementKeyDefinition& Key : BuildDemoElementKeys())
	{
		if (Key.MechanicLevelRequired == MechanicLevel)
		{
			return Key.KeyId;
		}
	}
	return NAME_None;
}

bool UMelodiaKeySystemLibrary::IsWeaknessHit(const EMelodiaSpellElement AttackElement, const EMelodiaSpellElement DefenseElement)
{
	return GetWeaknessOf(AttackElement) == DefenseElement;
}

bool UMelodiaKeySystemLibrary::IsResistanceHit(const EMelodiaSpellElement AttackElement, const EMelodiaSpellElement DefenseElement)
{
	return GetStrengthOf(AttackElement) == DefenseElement;
}

float UMelodiaKeySystemLibrary::GetElementDamageMultiplier(const EMelodiaSpellElement AttackElement, const EMelodiaSpellElement DefenseElement, const bool bHasMatchingKey)
{
	float Multiplier = 1.0f;
	if (IsWeaknessHit(AttackElement, DefenseElement))
	{
		Multiplier = WeaknessMultiplier;
		if (bHasMatchingKey)
		{
			Multiplier *= MatchingKeyWeaknessBonus;
		}
	}
	else if (IsResistanceHit(AttackElement, DefenseElement))
	{
		Multiplier = ResistanceMultiplier;
	}
	return Multiplier;
}

EMelodiaSpellElement UMelodiaKeySystemLibrary::GetEnemyElementForEncounterLevel(const int32 EncounterLevel)
{
	const int32 Clamped = FMath::Clamp(EncounterLevel, 1, 30);
	return static_cast<EMelodiaSpellElement>((Clamped + 2) % 7);
}
