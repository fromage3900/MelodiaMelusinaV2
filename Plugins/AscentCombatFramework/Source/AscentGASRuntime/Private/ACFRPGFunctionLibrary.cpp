// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFRPGFunctionLibrary.h"
#include "ACFDifficultyManagerComponent.h"
#include "ACFGASDeveloperSettings.h"
#include "ACFGASTypes.h"
#include "ACFRPGTypes.h"
#include <AbilitySystemComponent.h>
#include <GameplayEffect.h>
#include <Kismet/GameplayStatics.h>
#include "GameFramework/GameStateBase.h"

namespace
{
float GetAverageDifficultyMultiplier(const FACFDifficultyScaling& Scaling)
{
    if (Scaling.AttributeMultipliers.Num() == 0) {
        return 1.0f;
    }

    float TotalMultiplier = 0.0f;
    for (const FACFDifficultyAttributeMultiplier& Entry : Scaling.AttributeMultipliers) {
        TotalMultiplier += Entry.Multiplier;
    }
    return TotalMultiplier / static_cast<float>(Scaling.AttributeMultipliers.Num());
}

TArray<FACFDifficultyScaling*> GetDifficultyRows(const TCHAR* Context, bool bSortByCoefficient)
{
    TArray<FACFDifficultyScaling*> AllRows;
    UDataTable* DT = UACFRPGFunctionLibrary::GetDifficultyScalingTable();
    if (!DT) {
        return AllRows;
    }

    DT->GetAllRows(Context, AllRows);

    if (!bSortByCoefficient) {
        return AllRows;
    }

    struct FDifficultySortData {
        FACFDifficultyScaling* Row = nullptr;
        float AverageMultiplier = 1.0f;
        int32 OriginalIndex = INDEX_NONE;
    };

    TArray<FDifficultySortData> SortData;
    for (int32 Index = 0; Index < AllRows.Num(); ++Index) {
        FACFDifficultyScaling* Row = AllRows[Index];
        if (Row && Row->DifficultyLevel.IsValid()) {
            SortData.Add({ Row, GetAverageDifficultyMultiplier(*Row), Index });
        }
    }

    SortData.Sort([](const FDifficultySortData& A, const FDifficultySortData& B) {
        if (FMath::IsNearlyEqual(A.AverageMultiplier, B.AverageMultiplier)) {
            return A.OriginalIndex < B.OriginalIndex;
        }
        return A.AverageMultiplier < B.AverageMultiplier;
    });

    TArray<FACFDifficultyScaling*> SortedRows;
    SortedRows.Reserve(SortData.Num());
    for (const FDifficultySortData& Entry : SortData) {
        SortedRows.Add(Entry.Row);
    }
    return SortedRows;
}
}

bool UACFRPGFunctionLibrary::TryGetModifiersFromGameplayEffect(const FGameplayEffectConfig& effectClass, TArray<FGEModifier>& outModifiers)
{
    if (effectClass.Effect) {
        UGameplayEffect* GameplayEffect = effectClass.Effect->GetDefaultObject<UGameplayEffect>();
        bool bFound = false;
        for (const FGameplayModifierInfo& ModifierInfo : GameplayEffect->Modifiers) {
            // Gets the modified attribute
            FGameplayAttribute Attribute = ModifierInfo.Attribute;
            if (!Attribute.IsValid()) {
                continue;
            }

            // Calculate his magnitued
            float ModifierMagnitude;
            if (ModifierInfo.ModifierMagnitude.GetStaticMagnitudeIfPossible(effectClass.Level, ModifierMagnitude)) {
                outModifiers.Add(FGEModifier(Attribute, ModifierMagnitude));
                bFound = true;
            }
        }
        return bFound;
    }
    return false;
}

bool UACFRPGFunctionLibrary::TryGetModifiersFromGameplayEffects(const TArray<FGameplayEffectConfig>& effects, TArray<FGEModifier>& outModifiers)
{
    bool bFound = false;
    for (const auto& effect : effects) {
        TArray<FGEModifier> modifiers;
        if (TryGetModifiersFromGameplayEffect(effect, modifiers)) {
            outModifiers.Append(modifiers);
            bFound = true;
        }
    }
    return bFound;
}

FActiveGameplayEffectHandle UACFRPGFunctionLibrary::AddGameplayEffectToActor(FGameplayEffectConfig effect, AActor* targetActor)
{
    if (targetActor && effect.Effect) {
        UAbilitySystemComponent* abilityComp = targetActor->FindComponentByClass<UAbilitySystemComponent>();
        if (abilityComp) {
            FGameplayEffectContextHandle EffectContext = abilityComp->MakeEffectContext();
            UGameplayEffect* GameplayEffect = effect.Effect->GetDefaultObject<UGameplayEffect>();

            return abilityComp->ApplyGameplayEffectToSelf(GameplayEffect, effect.Level, EffectContext);
        }
    }
    return FActiveGameplayEffectHandle();
}

void UACFRPGFunctionLibrary::RemovesActiveGameplayEffectFromActor(const FActiveGameplayEffectHandle& effect, AActor* targetActor)
{
    if (targetActor) {
        UAbilitySystemComponent* abilityComp = targetActor->FindComponentByClass<UAbilitySystemComponent>();
        if (abilityComp) {
            abilityComp->RemoveActiveGameplayEffect(effect);
        }
    }
}

void UACFRPGFunctionLibrary::AddGameplayTagToActor(AActor* TargetActor, const FGameplayTag& TagToAdd)
{
    if (!TargetActor) {
        UE_LOG(LogTemp, Warning, TEXT("TargetActor is null in AddGameplayTagToASC"));
        return;
    }

    UAbilitySystemComponent* ASC = TargetActor->FindComponentByClass<UAbilitySystemComponent>();
    if (!ASC) {
        UE_LOG(LogTemp, Warning, TEXT("No ASC found on %s"), *TargetActor->GetName());
        return;
    }

    ASC->AddLooseGameplayTag(TagToAdd);
}

void UACFRPGFunctionLibrary::RemoveGameplayTagFromActor(AActor* TargetActor, const FGameplayTag& TagToAdd)
{
    if (!TargetActor) {
        UE_LOG(LogTemp, Warning, TEXT("TargetActor is null in AddGameplayTagToASC"));
        return;
    }

    UAbilitySystemComponent* ASC = TargetActor->FindComponentByClass<UAbilitySystemComponent>();
    if (!ASC) {
        UE_LOG(LogTemp, Warning, TEXT("No ASC found on %s"), *TargetActor->GetName());
        return;
    }

    ASC->RemoveLooseGameplayTag(TagToAdd);
}

// ========== Difficulty Scaling ==========

UACFDifficultyManagerComponent* UACFRPGFunctionLibrary::GetDifficultyManager(const UObject* WorldContextObject)
{
    if (!WorldContextObject) {
        return nullptr;
    }
    AGameStateBase* GameState = UGameplayStatics::GetGameState(WorldContextObject);
    if (GameState) {
        return GameState->FindComponentByClass<UACFDifficultyManagerComponent>();
    }
    return nullptr;
}

FGameplayTag UACFRPGFunctionLibrary::GetCurrentDifficultyLevel(const UObject* WorldContextObject)
{
    UACFDifficultyManagerComponent* DiffComp = GetDifficultyManager(WorldContextObject);
    if (DiffComp) {
        return DiffComp->GetCurrentDifficultyLevel();
    }
    return FGameplayTag();
}

void UACFRPGFunctionLibrary::SetDifficultyLevel(const UObject* WorldContextObject, const FGameplayTag& NewDifficultyLevel)
{
    UACFDifficultyManagerComponent* DiffComp = GetDifficultyManager(WorldContextObject);
    if (DiffComp) {
        DiffComp->SetDifficultyLevel(NewDifficultyLevel);
    }
}

UDataTable* UACFRPGFunctionLibrary::GetDifficultyScalingTable()
{
    const UACFGASDeveloperSettings* Settings = GetDefault<UACFGASDeveloperSettings>();
    if (Settings) {
        return Settings->GetDifficultyScalingTable();
    }
    return nullptr;
}

bool UACFRPGFunctionLibrary::TryGetDifficultyScaling(const FGameplayTag& DifficultyLevel, FACFDifficultyScaling& OutScaling)
{
    UDataTable* DT = GetDifficultyScalingTable();
    if (!DT || !DifficultyLevel.IsValid()) {
        return false;
    }

    TArray<FACFDifficultyScaling*> AllRows;
    DT->GetAllRows(TEXT("TryGetDifficultyScaling"), AllRows);

    for (const FACFDifficultyScaling* Row : AllRows) {
        if (Row && Row->DifficultyLevel == DifficultyLevel) {
            OutScaling = *Row;
            return true;
        }
    }
    return false;
}

float UACFRPGFunctionLibrary::GetDifficultyMultiplierForAttribute(const FGameplayTag& DifficultyLevel, const FGameplayAttribute& Attribute)
{
    FACFDifficultyScaling Scaling;
    if (!TryGetDifficultyScaling(DifficultyLevel, Scaling)) {
        return 1.0f;
    }

    for (const FACFDifficultyAttributeMultiplier& Entry : Scaling.AttributeMultipliers) {
        if (Entry.Attribute == Attribute) {
            return Entry.Multiplier;
        }
    }

    return 1.0f;
}

// ========== Difficulty UI Conversions ==========

int32 UACFRPGFunctionLibrary::DifficultyTagToIndex(const FGameplayTag& DifficultyTag)
{
    UDataTable* DT = GetDifficultyScalingTable();
    if (!DT || !DifficultyTag.IsValid()) {
        return INDEX_NONE;
    }

    TArray<FACFDifficultyScaling*> AllRows;
    DT->GetAllRows(TEXT("DifficultyTagToIndex"), AllRows);

    for (int32 i = 0; i < AllRows.Num(); ++i) {
        if (AllRows[i] && AllRows[i]->DifficultyLevel == DifficultyTag) {
            return i;
        }
    }
    return INDEX_NONE;
}

FGameplayTag UACFRPGFunctionLibrary::DifficultyTagAtIndex(int32 Index)
{
    UDataTable* DT = GetDifficultyScalingTable();
    if (!DT || Index < 0) {
        return FGameplayTag();
    }

    TArray<FACFDifficultyScaling*> AllRows;
    DT->GetAllRows(TEXT("DifficultyTagAtIndex"), AllRows);

    if (AllRows.IsValidIndex(Index) && AllRows[Index]) {
        return AllRows[Index]->DifficultyLevel;
    }
    return FGameplayTag();
}

FText UACFRPGFunctionLibrary::GetDifficultyDisplayName(const FGameplayTag& DifficultyTag)
{
    FACFDifficultyScaling Scaling;
    if (TryGetDifficultyScaling(DifficultyTag, Scaling) && !Scaling.UIName.IsEmpty()) {
        return Scaling.UIName;
    }

    // Fallback: derive a readable label from the last segment of the tag (e.g. "Normal").
    const FString TagString = DifficultyTag.GetTagName().ToString();
    FString LeafName;
    if (!TagString.Split(TEXT("."), nullptr, &LeafName, ESearchCase::IgnoreCase, ESearchDir::FromEnd)) {
        LeafName = TagString;
    }
    return FText::FromString(LeafName);
}

FText UACFRPGFunctionLibrary::GetDifficultyDescription(const FGameplayTag& DifficultyTag)
{
    FACFDifficultyScaling Scaling;
    if (TryGetDifficultyScaling(DifficultyTag, Scaling)) {
        return Scaling.UIDescription;
    }
    return FText::GetEmpty();
}

TArray<FGameplayTag> UACFRPGFunctionLibrary::GetAllDifficultyTags(bool bSortByCoefficient)
{
    TArray<FGameplayTag> Result;
    const TArray<FACFDifficultyScaling*> AllRows = GetDifficultyRows(TEXT("GetAllDifficultyTags"), bSortByCoefficient);

    for (const FACFDifficultyScaling* Row : AllRows) {
        if (Row && Row->DifficultyLevel.IsValid()) {
            Result.Add(Row->DifficultyLevel);
        }
    }
    return Result;
}

TArray<FText> UACFRPGFunctionLibrary::GetAllDifficultyDisplayNames(bool bSortByCoefficient)
{
    TArray<FText> Result;
    const TArray<FACFDifficultyScaling*> AllRows = GetDifficultyRows(TEXT("GetAllDifficultyDisplayNames"), bSortByCoefficient);

    for (const FACFDifficultyScaling* Row : AllRows) {
        if (Row && Row->DifficultyLevel.IsValid()) {
            Result.Add(!Row->UIName.IsEmpty() ? Row->UIName : GetDifficultyDisplayName(Row->DifficultyLevel));
        }
    }
    return Result;
}

TArray<FText> UACFRPGFunctionLibrary::GetAllDifficultyDescriptions(bool bSortByCoefficient)
{
    TArray<FText> Result;
    const TArray<FACFDifficultyScaling*> AllRows = GetDifficultyRows(TEXT("GetAllDifficultyDescriptions"), bSortByCoefficient);

    for (const FACFDifficultyScaling* Row : AllRows) {
        if (Row && Row->DifficultyLevel.IsValid()) {
            Result.Add(Row->UIDescription);
        }
    }
    return Result;
}
