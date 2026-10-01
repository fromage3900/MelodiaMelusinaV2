// Copyright Epic Games, Inc. All Rights Reserved.

#include "ACFEditorStyle.h"
#include "Framework/Application/SlateApplication.h"
#include "Slate/SlateGameResources.h"
#include "Styling/SlateStyleMacros.h"
#include "Styling/SlateStyleRegistry.h"
#include <Interfaces/IPluginManager.h>

#define RootToContentDir Style->RootToContentDir

TSharedPtr<FSlateStyleSet> FACFEditorStyle::StyleInstance = nullptr;

void FACFEditorStyle::Initialize()
{
	if (!StyleInstance.IsValid()) {
		StyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
	}
}

void FACFEditorStyle::Shutdown()
{
	FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
	ensure(StyleInstance.IsUnique());
	StyleInstance.Reset();
}

FName FACFEditorStyle::GetStyleSetName()
{
	return StyleSetName;
}

const FVector2D Icon32x32(28.0f, 28.0f);
const FVector2D Icon20x20(20.0f, 20.0f);
const FVector2D Icon8(8.f, 8.f);
const FVector2D Icon16(16.f, 16.f);

TSharedRef<FSlateStyleSet> FACFEditorStyle::Create()
{
	TSharedRef<FSlateStyleSet> Style = MakeShareable(new FSlateStyleSet(StyleSetName));
	const FString ResourceDir = IPluginManager::Get().FindPlugin(PluginName)->GetBaseDir() / TEXT("Resources");
	Style->SetContentRoot(ResourceDir);

	Style->Set("ACFEditor.SmallIcon", new IMAGE_BRUSH(TEXT("ACF32"), Icon20x20));

	Style->Set("ClassIcon.AGSAction", new FSlateImageBrush(ResourceDir / TEXT("Event.png"), Icon16));
	Style->Set("ClassThumbnail.AGSAction", new FSlateImageBrush(ResourceDir / TEXT("Event.png"), Icon32x32));
	Style->Set("ClassIcon.ADSDialogue", new FSlateImageBrush(ResourceDir / TEXT("dialogue.png"), Icon16));
	Style->Set("ClassThumbnail.ADSDialogue", new FSlateImageBrush(ResourceDir / TEXT("dialogue.png"), Icon32x32));
	Style->Set("ClassIcon.AQSQuest", new FSlateImageBrush(ResourceDir / TEXT("quest.png"), Icon16));
	Style->Set("ClassThumbnail.AQSQuest", new FSlateImageBrush(ResourceDir / TEXT("quest.png"), Icon32x32));
	Style->Set("ClassIcon.ACFCraftRecipeDataAsset", new FSlateImageBrush(ResourceDir / TEXT("Craft.png"), Icon16));
	Style->Set("ClassThumbnail.ACFCraftRecipeDataAsset", new FSlateImageBrush(ResourceDir / TEXT("Craft.png"), Icon32x32));
	Style->Set("ClassIcon.ACFBuildRecipe", new FSlateImageBrush(ResourceDir / TEXT("Build.png"), Icon16));
	Style->Set("ClassThumbnail.ACFCrafACFBuildRecipetRecipeDataAsset", new FSlateImageBrush(ResourceDir / TEXT("Build.png"), Icon32x32));
	Style->Set("ClassIcon.ACFActionAbility", new FSlateImageBrush(ResourceDir / TEXT("technical-skills.png"), Icon16));
	Style->Set("ClassThumbnail.ACFActionAbility", new FSlateImageBrush(ResourceDir / TEXT("technical-skills.png"), Icon32x32));
	Style->Set("ClassIcon.AQSQuestObjective", new FSlateImageBrush(ResourceDir / TEXT("Objective.png"), Icon16));
	Style->Set("ClassThumbnail.AQSQuestObjective", new FSlateImageBrush(ResourceDir / TEXT("Objective.png"), Icon32x32));
	Style->Set("ClassIcon.ACFItem", new FSlateImageBrush(ResourceDir / TEXT("Bag.png"), Icon16));
	Style->Set("ClassThumbnail.ACFItem", new FSlateImageBrush(ResourceDir / TEXT("Bag.png"), Icon32x32));
	Style->Set("ClassIcon.AGSCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon16));
	Style->Set("ClassThumbnail.AGSCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon32x32));
	Style->Set("ClassIcon.ACFActionCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon16));
	Style->Set("ClassThumbnail.ACFActionCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon32x32));
	Style->Set("ClassIcon.CASAnimCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon16));
	Style->Set("ClassThumbnail.CASAnimCondition", new FSlateImageBrush(ResourceDir / TEXT("Condition.png"), Icon32x32));
	Style->Set("ClassIcon.ACFAbilitySet", new FSlateImageBrush(ResourceDir / TEXT("Ability.png"), Icon16));
	Style->Set("ClassThumbnail.ACFAbilitySet", new FSlateImageBrush(ResourceDir / TEXT("Ability.png"), Icon32x32));

	Style->Set("ClassIcon.ACFStorage", new FSlateImageBrush(ResourceDir / TEXT("Chest.png"), Icon16));
	Style->Set("ClassThumbnail.ACFStorage", new FSlateImageBrush(ResourceDir / TEXT("Chest.png"), Icon32x32));


	Style->Set("ClassIcon.ACFWorldItem", new FSlateImageBrush(ResourceDir / TEXT("Pouch.png"), Icon16));
	Style->Set("ClassThumbnail.ACFWorldItem", new FSlateImageBrush(ResourceDir / TEXT("Pouch.png"), Icon32x32));

	Style->Set("ClassIcon.ACFAIGroupSpawner", new FSlateImageBrush(ResourceDir / TEXT("Group.png"), Icon16));
	Style->Set("ClassThumbnail.ACFAIGroupSpawner", new FSlateImageBrush(ResourceDir / TEXT("Group.png"), Icon32x32));

	Style->Set("ClassIcon.ACFLadder", new FSlateImageBrush(ResourceDir / TEXT("ladder.png"), Icon16));
	Style->Set("ClassThumbnail.ACFLadder", new FSlateImageBrush(ResourceDir / TEXT("ladder.png"), Icon32x32));


	Style->Set("ClassIcon.AMSMapLocation", new FSlateImageBrush(ResourceDir / TEXT("Location.png"), Icon16));
	Style->Set("ClassThumbnail.AMSMapLocation", new FSlateImageBrush(ResourceDir / TEXT("Location.png"), Icon32x32));
	Style->Set("ClassIcon.AMSMapArea", new FSlateImageBrush(ResourceDir / TEXT("maparea.png"), Icon16));
	Style->Set("ClassThumbnail.AMSMapArea", new FSlateImageBrush(ResourceDir / TEXT("maparea.png"), Icon32x32));
	Style->Set("ClassIcon.ACFSplinePath", new FSlateImageBrush(ResourceDir / TEXT("Spline.png"), Icon16));
	Style->Set("ClassThumbnail.ACFSplinePath", new FSlateImageBrush(ResourceDir / TEXT("Spline.png"), Icon32x32));


	Style->Set("ClassIcon.ACFCharacter", new FSlateImageBrush(ResourceDir / TEXT("warrior.png"), Icon16));
	Style->Set("ClassThumbnail.ACFCharacter", new FSlateImageBrush(ResourceDir / TEXT("warrior.png"), Icon32x32));


	Style->Set("ClassIcon.ACFCharacterDataAsset", new FSlateImageBrush(ResourceDir / TEXT("warrior.png"), Icon16));
	Style->Set("ClassThumbnail.ACFCharacterDataAsset", new FSlateImageBrush(ResourceDir / TEXT("warrior.png"), Icon32x32));
	Style->Set("ClassIcon.ACFEncounterDataAsset", new FSlateImageBrush(ResourceDir / TEXT("monster.png"), Icon16));
	Style->Set("ClassThumbnail.ACFEncounterDataAsset", new FSlateImageBrush(ResourceDir / TEXT("monster.png"), Icon32x32));

	Style->Set("ClassIcon.ACFMusicVolume", new FSlateImageBrush(ResourceDir / TEXT("music.png"), Icon16));
	Style->Set("ClassThumbnail.ACFMusicVolume", new FSlateImageBrush(ResourceDir / TEXT("music.png"), Icon32x32));

	Style->Set("ClassIcon.ACFBaseInteractableActor", new FSlateImageBrush(ResourceDir / TEXT("interactivity.png"), Icon16));
	Style->Set("ClassThumbnail.ACFBaseInteractableActor", new FSlateImageBrush(ResourceDir / TEXT("interactivity.png"), Icon32x32));

	Style->Set("ClassIcon.AQSQuestTrigger", new FSlateImageBrush(ResourceDir / TEXT("Objective.png"), Icon16));
	Style->Set("ClassThumbnail.AQSQuestTrigger", new FSlateImageBrush(ResourceDir / TEXT("Objective.png"), Icon32x32));

	
	Style->Set("ClassIcon.ACFAIRoutineDataAsset", new FSlateImageBrush(ResourceDir / TEXT("routine.png"), Icon16));
	Style->Set("ClassThumbnail.ACFAIRoutineDataAsset", new FSlateImageBrush(ResourceDir / TEXT("routine.png"), Icon32x32));

	Style->Set("ClassIcon.ACFGatherableSpawner", new FSlateImageBrush(ResourceDir / TEXT("plant.png"), Icon16));
	Style->Set("ClassThumbnail.ACFGatherableSpawner", new FSlateImageBrush(ResourceDir / TEXT("plant.png"), Icon32x32));

	Style->Set("ClassIcon.ACFGatherableDataAsset", new FSlateImageBrush(ResourceDir / TEXT("plant.png"), Icon16));
	Style->Set("ClassThumbnail.ACFGatherableDataAsset", new FSlateImageBrush(ResourceDir / TEXT("plant.png"), Icon32x32));

	return Style;
}

void FACFEditorStyle::ReloadTextures()
{
	if (FSlateApplication::IsInitialized()) {
		FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
	}
}

const ISlateStyle& FACFEditorStyle::Get()
{
	return *StyleInstance;
}
