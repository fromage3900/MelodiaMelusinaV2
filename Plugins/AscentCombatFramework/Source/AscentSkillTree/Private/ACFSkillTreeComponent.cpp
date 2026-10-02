// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFSkillTreeComponent.h"

#include "ACFGASAttributesComponent.h"
#include "ARSLevelingComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Graph/ACFBaseSkillNode.h"
#include "Graph/ACFSkillTreeGraph.h"
#include <ACFRPGFunctionLibrary.h>
#include <GameplayTagContainer.h>
#include <Logging.h>
#include <Net/UnrealNetwork.h>
#include <UObject/CoreNet.h>

// Sets default values for this component's properties
UACFSkillTreeComponent::UACFSkillTreeComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.
    // You can turn these features off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
}

// Called when the game starts
void UACFSkillTreeComponent::BeginPlay()
{
    Super::BeginPlay();
    AttributeComp = GetOwner()->FindComponentByClass<UACFGASAttributesComponent>();
    AbilityComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
}

void UACFSkillTreeComponent::SynchTrees()
{
    // Synchronizes the graph data with the actual one in the component
    for (UACFSkillTreeGraph* Tree : SkillTrees) {
        for (UAGSGraphNode* Node : Tree->GetAllNodes()) {
            UACFBaseSkillNode* SkillNode = Cast<UACFBaseSkillNode>(Node);
            if (!SkillNode) {
                continue;
            }

            const FGuid NodeId = SkillNode->GetNodeId();
            
            if (ActiveSkills.Contains(NodeId) && !SkillNode->IsNodeActivated()) {
                Tree->ActivateNode(SkillNode);
            }
            else if (SkillNode->IsNodeActivated() && !ActiveSkills.Contains(NodeId)) {
                Tree->DeactivateNode(SkillNode);
            }
        }
    }
}

bool UACFSkillTreeComponent::Internal_RemoveSkill(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId)
{
    FAbilityHandlers* Handlers = SkillHandlers.Find(SkillNodeId);
    if (Handlers) {
        // Remove gameplay effect and clear ability
        UACFRPGFunctionLibrary::RemovesActiveGameplayEffectFromActor(Handlers->GEHandle, GetOwner());
        AbilityComp->ClearAbility(Handlers->GAHandle);
        SkillHandlers.Remove(SkillNodeId);

        // Remove from active skills container and level map
        ActiveSkills.RemoveSkillById(SkillNodeId);

        const int32 Index = SkillLevels.IndexOfByPredicate([&SkillNodeId](const FSkillLevelData& Data) {
            return Data.SkillId == SkillNodeId;
            });
        if (Index != INDEX_NONE) {
            SkillLevels.RemoveAt(Index);
        }

        BroadcastActiveSkillsChanged();
        return true;
    }
    return false;
}

void UACFSkillTreeComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFSkillTreeComponent, ActiveSkills);
    DOREPLIFETIME(UACFSkillTreeComponent, SkillLevels);
    DOREPLIFETIME(UACFSkillTreeComponent, SkillPoints);
}

void UACFSkillTreeComponent::UnlockSkillFromTree_Implementation(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId)
{
    ECanUnlockSkillResult UnlockResult;

    if (CanUnlockSkill(SkillTreeTag, SkillNodeId, UnlockResult))
    {
        UACFBaseSkillNode* SkillNode = GetSkillByIds(SkillTreeTag, SkillNodeId);
        if (SkillNode) {
            const int32 CurrentLevel = GetSkillCurrentLevel(SkillNodeId);

            if (CurrentLevel == 0) {
                // First time unlock: Grant ability, apply effect, store handlers
                const FGameplayAbilitySpecHandle AbilitySpec = AbilityComp->GrantAbility(SkillNode->GetSkillToGrant().AbilityToGrant);
                const FActiveGameplayEffectHandle EffectHandle = UACFRPGFunctionLibrary::AddGameplayEffectToActor(SkillNode->GetSkillToGrant().GameplayEffect, GetOwner());

                FAbilityHandlers Handlers(AbilitySpec, EffectHandle);
                SkillHandlers.Add(SkillNodeId, Handlers);

                ActiveSkills.AddSkill(FSkillSaveData(SkillNodeId, SkillTreeTag));
            }
            else {
                // Upgrading: Re-apply gameplay effect (assuming it scales)
                FAbilityHandlers* Handlers = SkillHandlers.Find(SkillNodeId);
                if (Handlers) {
                    UACFRPGFunctionLibrary::RemovesActiveGameplayEffectFromActor(Handlers->GEHandle, GetOwner());
                    const FActiveGameplayEffectHandle EffectHandle = UACFRPGFunctionLibrary::AddGameplayEffectToActor(SkillNode->GetSkillToGrant().GameplayEffect, GetOwner());
                    Handlers->GEHandle = EffectHandle;
                }
            }

            // Update level and deduct points
            FSkillLevelData* LevelData = SkillLevels.FindByPredicate([&SkillNodeId](const FSkillLevelData& Data) {
                return Data.SkillId == SkillNodeId;
                });
            if (LevelData) {
                LevelData->CurrentLevel++;
            }
            else {
                SkillLevels.Emplace(SkillNodeId, 1);
            }

            AddSkillPoints(-SkillNode->GetSkillToGrant().RequiredSkillPoint);

            BroadcastActiveSkillsChanged();
        }
    }
}

bool UACFSkillTreeComponent::CanUnlockSkill(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId, ECanUnlockSkillResult& OutResult)
{
    if (!AttributeComp) {
        OutResult = ECanUnlockSkillResult::InvalidAttributeComponent;
        return false;
    }

    if (!SkillTreeTag.IsValid() || !SkillNodeId.IsValid()) {
        OutResult = ECanUnlockSkillResult::InvalidInputParameters;
        return false;
    }

    const UACFSkillTreeGraph* SkillTree = GetSkillTreeByTag(SkillTreeTag);
    if (!SkillTree) {
        OutResult = ECanUnlockSkillResult::SkillTreeNotFound;
        return false;
    }

    const UACFBaseSkillNode* SkillNode = SkillTree->GetSkillNodeById(SkillNodeId);
    if (!SkillNode) {
        OutResult = ECanUnlockSkillResult::SkillNodeNotFound;
        return false;
    }

    const FString SkillName = SkillNode->GetUISkillInfo().SkillName.ToString();
    const int32 CurrentLevel = GetSkillCurrentLevel(SkillNodeId);
    const int32 MaxLevel = SkillNode->GetMaxLevel();
    const int32 RequiredPoints = SkillNode->GetSkillToGrant().RequiredSkillPoint;
    const int32 RequiredLevel = SkillNode->GetSkillToGrant().RequiredLevel;
    const int32 CurrentActorLevel = AttributeComp->GetCurrentLevel();

    if (CurrentLevel >= MaxLevel) {
        OutResult = ECanUnlockSkillResult::AlreadyAtMaxLevel;
        return false;
    }
    if (GetSkillPoints() < RequiredPoints) {
        OutResult = ECanUnlockSkillResult::InsufficientSkillPoints;
        return false;
    }

    if (CurrentLevel == 0)
    {
        if (CurrentActorLevel < RequiredLevel) {
            OutResult = ECanUnlockSkillResult::InsufficientCharacterLevel;
            return false;
        }

        // Check parent nodes against component's ActiveSkills instead of graph node activation state
        for (const UAGSGraphNode* ParentNode : SkillNode->ParentNodes)
        {
            const UACFBaseSkillNode* ParentSkillNode = Cast<UACFBaseSkillNode>(ParentNode);
            if (ParentSkillNode && !IsSkillActive(ParentSkillNode->GetNodeId()))
            {
                OutResult = ECanUnlockSkillResult::ParentNodesNotActive;
                return false;
            }
        }
    }

    if (CurrentLevel == 0)
    {
        OutResult = ECanUnlockSkillResult::SkillUnlocked;
        return true;
    }
    else
    {
        OutResult = ECanUnlockSkillResult::SkillUpgraded;
        return true;
    }
}

void UACFSkillTreeComponent::AddSkillPoints_Implementation(int32 SkillPointsToAdd)
{
    SetSkillPoints(GetSkillPoints() + SkillPointsToAdd);
    BroadcastSkillPointsChanged();
}

UACFBaseSkillNode* UACFSkillTreeComponent::GetSkillByIds(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId) const
{
    const UACFSkillTreeGraph* SkillTree = GetSkillTreeByTag(SkillTreeTag);
    if (SkillTree) {
        return SkillTree->GetSkillNodeById(SkillNodeId);
    }
    return nullptr;
}

UACFSkillTreeGraph* UACFSkillTreeComponent::GetSkillTreeByTag(const FGameplayTag& SkillTreeTag) const
{
    for (UACFSkillTreeGraph* Tree : SkillTrees) {
        if (Tree && Tree->GetSkillTreeTag() == SkillTreeTag) {
            return Tree;
        }
    }
    return nullptr;
}

bool UACFSkillTreeComponent::IsSkillActive(const FGuid& SkillNodeId) const
{
    return ActiveSkills.Contains(SkillNodeId);
}

int32 UACFSkillTreeComponent::GetSkillCurrentLevel(const FGuid& SkillNodeId) const
{
    const FSkillLevelData* LevelData = SkillLevels.FindByPredicate([&SkillNodeId](const FSkillLevelData& Data) {
        return Data.SkillId == SkillNodeId;
        });

    if (LevelData) {
        return LevelData->CurrentLevel;
    }
    return 0;
}

void UACFSkillTreeComponent::RemoveSkill_Implementation(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId)
{
    Internal_RemoveSkill(SkillTreeTag, SkillNodeId);
}

void UACFSkillTreeComponent::Respec_Implementation()
{
    TArray<FSkillSaveData> SkillsToRemove = ActiveSkills.Skills;
    int32 TotalSkillPoints = 0;
    
    // Calculate total skill points to refund and remove all skills
    for (const FSkillSaveData& SkillData : SkillsToRemove) {
        const UACFBaseSkillNode* SkillNode = GetSkillByIds(SkillData.SkillTreeTag, SkillData.SkillId);
        const int32 CurrentLevel = GetSkillCurrentLevel(SkillData.SkillId);

        if (SkillNode && CurrentLevel > 0) {
            TotalSkillPoints += (SkillNode->GetSkillToGrant().RequiredSkillPoint * CurrentLevel);
        }
        Internal_RemoveSkill(SkillData.SkillTreeTag, SkillData.SkillId);
    }
    
    // Refund all skill points and clear containers
    AddSkillPoints(TotalSkillPoints);
    ActiveSkills.ClearAllSkills();
    SkillHandlers.Empty();
    SkillLevels.Empty();

    BroadcastActiveSkillsChanged();
    BroadcastSkillPointsChanged();
}