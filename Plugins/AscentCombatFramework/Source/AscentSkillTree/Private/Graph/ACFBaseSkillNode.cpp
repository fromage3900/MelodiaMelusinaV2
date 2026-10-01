// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ACFBaseSkillNode.h"

#if WITH_EDITOR
FText UACFBaseSkillNode::GetNodeTitle() const
{
    if (!Skill || GetUISkillInfo().SkillName.IsEmpty()) {
        return FText::FromString("No Skill Name");
    }
    return GetUISkillInfo().SkillName;
}

FText UACFBaseSkillNode::GetParagraphTitle() const
{
    if (!Skill || GetUISkillInfo().Description.IsEmpty()) {
        return FText::FromString("Configure this Skill in the Details Panel!");
    }
    return GetUISkillInfo().Description;
}

#endif
