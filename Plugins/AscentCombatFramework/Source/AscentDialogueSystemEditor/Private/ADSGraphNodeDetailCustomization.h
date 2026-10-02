// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "CoreMinimal.h"
#include "IDetailCustomization.h"

class UADSDialogue;
class UADSGraphNode;
class UADSWorldDialogue; // forward-declared for IsA<> check inside FADSDialogueDetailCustomization

/**
 * Custom detail panel for ADSGraphNode to add  TTS buttons
 */
class FADSGraphNodeDetailCustomization : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance();
    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override;

private:
    TWeakObjectPtr<UADSGraphNode> CachedNode;
};


class FADSAIVoiceGeneratorComponentDetails : public IDetailCustomization
{
public:
    /** Factory method */
    static TSharedRef<IDetailCustomization> MakeInstance();

    /** Called to customize the details panel */
    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override;

private:
    /** Cached component being customized */
    TWeakObjectPtr<class UADSVoiceConfigDataAsset> CachedComponent;
};


/**
 * Custom detail panel for UADSDialogue to add Export/Import screenplay buttons
 */
class FADSDialogueDetailCustomization : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance();
    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override;

private:
    TWeakObjectPtr<UADSDialogue> CachedDialogue;
};
