// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFGASAttributesComponent.h"
#include "ACFDifficultyManagerComponent.h"
#include "ACFGASDeveloperSettings.h"
#include "ACFGASTypes.h"
#include "ACFRPGFunctionLibrary.h"
#include "AttributeSet.h"
#include "Engine/DataTable.h"
#include <AbilitySystemComponent.h>
#include <Engine/DataTable.h>
#include <GameplayEffect.h>
#include <GameplayEffectTypes.h>

// Sets default values for this component's properties
UACFGASAttributesComponent::UACFGASAttributesComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    bLoaded = false;
}

UAbilitySystemComponent* UACFGASAttributesComponent::GetOwnerAbilityComponent() const
{
    return abilityComp;
}

void UACFGASAttributesComponent::AssignPerkToAttribute_Implementation(FGameplayAttribute attribute, int32 numPerks /*= 1*/)
{
    if (!abilityComp) {
        return;
    }
    if (GetAvailablePerks() >= numPerks) {
        float newValue = abilityComp->GetNumericAttributeBase(attribute);
        newValue += numPerks;
        abilityComp->SetNumericAttributeBase(attribute, newValue);
        ConsumePerks(numPerks);
    }
}

void UACFGASAttributesComponent::SetCharacterRow(FDataTableRowHandle val)
{
    CharacterRow = val;
}

void UACFGASAttributesComponent::InitializeAttributeSet()
{
    InitAttributesValue();
    ApplyPermanentEffects();
}

// Called when the game starts
void UACFGASAttributesComponent::BeginPlay()
{
    Super::BeginPlay();


    UACFDifficultyManagerComponent* DiffComp = UACFRPGFunctionLibrary::GetDifficultyManager(this);
    if (DiffComp) {
        CachedDifficultyManager = DiffComp;
        if (!DiffComp->OnDifficultyChanged.IsAlreadyBound(this, &UACFGASAttributesComponent::OnDifficultyLevelChanged)) {
            DiffComp->OnDifficultyChanged.AddDynamic(this, &UACFGASAttributesComponent::OnDifficultyLevelChanged);
        }
    }

    if (GetOwner()->HasAuthority() && bAutoInitialize) {
        InitializeAttributeSet();
    }
    else {
        abilityComp = GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
    }
}

void UACFGASAttributesComponent::InitAttributesValue()
{
    abilityComp = GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
    allAttributes = GetAttributeToSave();
    if (abilityComp) {
        for (const auto& startData : abilityComp->DefaultStartingData) {
            abilityComp->InitStats(startData.Attributes, startData.DefaultStartingTable);
        }
        if (bLoaded) {
            return;
        }
        if (GetLevelingType() != ELevelingType::EGenerateNewStatsFromCurves) {
            InitAttributesFromDT();

        } else {
            InitAttributesFromLevelCurves();
        }
    }
}

void UACFGASAttributesComponent::InitAttributesFromDT()
{
    if (!abilityComp) {
        return;
    }
    if (!CharacterRow.DataTable) {
        return;
    }
    const FACFAttributeInits* attInits = CharacterRow.DataTable->FindRow<FACFAttributeInits>(CharacterRow.RowName, "");
    if (!attInits) {
        return;
    }

    const FACFDifficultyScaling* DifficultyRow = nullptr;
    if (bAffectedByDifficultyLevel) {
        DifficultyRow = GetCachedDifficultyScaling();
    }

    for (const auto& attribute : attInits->PawnAttributesInit) {
        if (abilityComp->HasAttributeSetForAttribute(attribute.Attribute)) {
            float FinalValue = attribute.InitValue;
            if (DifficultyRow) {
                FinalValue *= GetMultiplierForAttribute(*DifficultyRow, attribute.Attribute);
            }
            abilityComp->SetNumericAttributeBase(attribute.Attribute, FinalValue);
        }
    }
}

void UACFGASAttributesComponent::InitAttributesFromLevelCurves()
{
    if (!abilityComp || !AttributesByLevelCurve) {
        return;
    }

    const UACFGASDeveloperSettings* Settings = GetDefault<UACFGASDeveloperSettings>();

    const UDataTable* AttributesByCurveRow = Settings->GetAttributesByCurveRow();

    if (!AttributesByCurveRow) {
        return;
    }

    const FACFDifficultyScaling* DifficultyRow = nullptr;
    if (bAffectedByDifficultyLevel) {
        DifficultyRow = GetCachedDifficultyScaling();
    }

    for (const TPair<FName, uint8*>& Elem : AttributesByCurveRow->GetRowMap()) {
        const FName& RowName = Elem.Key;
        const FAttributeSerializeKeys* AttributeKey = AttributesByCurveRow->FindRow<FAttributeSerializeKeys>(Elem.Key, TEXT("InitAttributes"));

        if (!AttributeKey) {
            continue;
        }

        const FRealCurve* Curve = AttributesByLevelCurve->FindCurve(RowName, FString());
        if (Curve) {
            float Value = Curve->Eval(static_cast<float>(CharacterLevel));
            if (abilityComp->HasAttributeSetForAttribute(AttributeKey->Attribute)) {
                if (DifficultyRow) {
                    Value *= GetMultiplierForAttribute(*DifficultyRow, AttributeKey->Attribute);
                }
                abilityComp->SetNumericAttributeBase(AttributeKey->Attribute, Value);
            }
        } else {
            UE_LOG(LogTemp, Warning, TEXT("Missing curve row for attribute: %s"), *RowName.ToString());
        }
    }
}

void UACFGASAttributesComponent::ApplyPermanentEffects()
{
    UAbilitySystemComponent* AbilitySystemComponent = GetOwnerAbilityComponent();
    if (AbilitySystemComponent) {
        permanentEffects.Empty();
        for (const auto& effect : StartingEffects) {
            FGameplayEffectContextHandle EffectContext = AbilitySystemComponent->MakeEffectContext();
            FGameplayEffectSpecHandle SpecHandle = AbilitySystemComponent->MakeOutgoingSpec(effect, 1.0f, EffectContext);
            if (SpecHandle.IsValid()) {
                permanentEffects.Add(AbilitySystemComponent->ApplyGameplayEffectSpecToSelf(*SpecHandle.Data.Get()));
            }
        }
    }
}

void UACFGASAttributesComponent::OnComponentLoaded_Implementation()
{
    if (!abilityComp) {
        abilityComp = GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
    }
    if (!allAttributes) {
        allAttributes = GetAttributeToSave();
    }

    if (allAttributes && abilityComp) {
        for (const auto& attribute : SaveableAttributes) {
            FAttributeSerializeKeys* attName = allAttributes->FindRow<FAttributeSerializeKeys>(attribute.AttributeName, "");
            if (attName) {
                abilityComp->SetNumericAttributeBase(attName->Attribute, attribute.Value);
            }
        }
    }

    bLoaded = true;
    RefreshDifficulty();
}

void UACFGASAttributesComponent::RefreshDifficulty()
{
    if (!bAffectedByDifficultyLevel) {
        return;
    }

    AActor* Owner = GetOwner();
    if (!Owner || !Owner->HasAuthority()) {
        return;
    }

    if (!CachedDifficultyManager.IsValid()) {
        if (UACFDifficultyManagerComponent* DiffComp = UACFRPGFunctionLibrary::GetDifficultyManager(this)) {
            CachedDifficultyManager = DiffComp;
        }
    }

    if (!abilityComp) {
        abilityComp = Owner->FindComponentByClass<UAbilitySystemComponent>();
    }

    if (!abilityComp) {
        return;
    }

    if (GetLevelingType() != ELevelingType::EGenerateNewStatsFromCurves) {
        InitAttributesFromDT();
    } else {
        InitAttributesFromLevelCurves();
    }
}

void UACFGASAttributesComponent::OnComponentSaved_Implementation()
{
    SaveableAttributes.Empty();

    if (abilityComp && allAttributes) {
        const auto allAttStruct = allAttributes->GetRowMap();
        for (const auto& att : allAttStruct) {
            FAttributeSerializeKeys* AttSerialize = (FAttributeSerializeKeys*)att.Value;
            const float baseValue = abilityComp->GetNumericAttributeBase(AttSerialize->Attribute);
            SaveableAttributes.Add(FAttributeSerializeNames(att.Key, baseValue));
        }
    }
}

UDataTable* UACFGASAttributesComponent::GetAttributeToSave() const
{

    UACFGASDeveloperSettings* settings = GetMutableDefault<UACFGASDeveloperSettings>();

    if (settings) {
        return settings->GetAttributeKeys();
    }
    return nullptr;
}

const FACFDifficultyScaling* UACFGASAttributesComponent::GetCachedDifficultyScaling() const
{
    UACFDifficultyManagerComponent* DiffComp = CachedDifficultyManager.IsValid()
        ? CachedDifficultyManager.Get()
        : UACFRPGFunctionLibrary::GetDifficultyManager(this);

    if (!DiffComp) {
        return nullptr;
    }

    const FGameplayTag DifficultyLevel = DiffComp->GetCurrentDifficultyLevel();
    if (!DifficultyLevel.IsValid()) {
        return nullptr;
    }

    UDataTable* DifficultyDT = UACFRPGFunctionLibrary::GetDifficultyScalingTable();
    if (!DifficultyDT) {
        return nullptr;
    }

    TArray<FACFDifficultyScaling*> AllRows;
    DifficultyDT->GetAllRows(TEXT("GetCachedDifficultyScaling"), AllRows);

    for (FACFDifficultyScaling* Row : AllRows) {
        if (Row && Row->DifficultyLevel == DifficultyLevel) {
            return Row;
        }
    }

    return nullptr;
}

float UACFGASAttributesComponent::GetMultiplierForAttribute(const FACFDifficultyScaling& Scaling, const FGameplayAttribute& Attribute)
{
    for (const FACFDifficultyAttributeMultiplier& Entry : Scaling.AttributeMultipliers) {
        if (Entry.Attribute == Attribute) {
            return Entry.Multiplier;
        }
    }
    return 1.0f;
}

void UACFGASAttributesComponent::OnDifficultyLevelChanged(FGameplayTag NewDifficultyLevel)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) {
        return;
    }

    if (bAffectedByDifficultyLevel) {
        RefreshDifficulty();
    } else if (!bLoaded) {
        InitAttributesValue();
    }
}
