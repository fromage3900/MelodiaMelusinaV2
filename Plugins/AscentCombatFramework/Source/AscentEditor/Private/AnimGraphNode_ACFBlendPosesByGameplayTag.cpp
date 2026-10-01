// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AnimGraphNode_ACFBlendPosesByGameplayTag.h"
#include "ToolMenus.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "ScopedTransaction.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(AnimGraphNode_ACFBlendPosesByGameplayTag)

#define LOCTEXT_NAMESPACE "AnimGraphNode_ACFBlendPosesByGameplayTag"

UAnimGraphNode_ACFBlendPosesByGameplayTag::UAnimGraphNode_ACFBlendPosesByGameplayTag(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	Node.AddPose();
	Node.AddPose();
	TagEntries.AddDefaulted();
}

FText UAnimGraphNode_ACFBlendPosesByGameplayTag::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
	return LOCTEXT("NodeTitle", "ACF Blend Poses by Gameplay Tag");
}

FText UAnimGraphNode_ACFBlendPosesByGameplayTag::GetTooltipText() const
{
	return LOCTEXT("NodeTooltip",
		"Blends between multiple poses based on active Gameplay Tags.\n"
		"The first matching tag (by list order) wins, so order tags by priority.\n"
		"Falls back to the Default pose when no tag matches.");
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::CustomizePinData(UEdGraphPin* Pin, FName SourcePropertyName, int32 ArrayIndex) const
{
	int32 RawArrayIndex = 0;
	bool bIsPosePin = false;
	bool bIsTimePin = false;
	GetPinInformation(Pin->PinName.ToString(), RawArrayIndex, bIsPosePin, bIsTimePin);

	if (bIsPosePin || bIsTimePin)
	{
		if (RawArrayIndex > 0)
		{
			const int32 TagIndex = RawArrayIndex - 1;
			if (TagEntries.IsValidIndex(TagIndex))
			{
				const FGameplayTag& CurrentTag = TagEntries[TagIndex];
				if (CurrentTag.IsValid())
				{
					Pin->PinFriendlyName = FText::FromString(CurrentTag.ToString());
				}
				else
				{
					Pin->PinFriendlyName = FText::Format(
						LOCTEXT("UnsetTag", "Tag {0} (Not Set)"), FText::AsNumber(RawArrayIndex));
				}
			}
			else
			{
				Pin->PinFriendlyName = LOCTEXT("InvalidIndex", "Invalid index");
			}
		}
		else if (ensure(RawArrayIndex == 0))
		{
			Pin->PinFriendlyName = LOCTEXT("Default", "Default");
		}

		if (bIsPosePin)
		{
			FFormatNamedArguments Args;
			Args.Add(TEXT("PinFriendlyName"), Pin->PinFriendlyName);
			Pin->PinFriendlyName = FText::Format(LOCTEXT("PoseName", "{PinFriendlyName} Pose"), Args);
		}

		if (bIsTimePin)
		{
			FFormatNamedArguments Args;
			Args.Add(TEXT("PinFriendlyName"), Pin->PinFriendlyName);
			Pin->PinFriendlyName = FText::Format(LOCTEXT("BlendTimeName", "{PinFriendlyName} Blend Time"), Args);
		}
	}
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	const FName PropertyName = (PropertyChangedEvent.Property ? PropertyChangedEvent.Property->GetFName() : NAME_None);

	if (PropertyName == GET_MEMBER_NAME_CHECKED(UAnimGraphNode_ACFBlendPosesByGameplayTag, TagEntries))
	{
		ReconstructNode();
	}

	Super::PostEditChangeProperty(PropertyChangedEvent);
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::BakeDataDuringCompilation(FCompilerResultsLog& MessageLog)
{
	Node.SetGameplayTags(TagEntries);
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::GetNodeContextMenuActions(UToolMenu* Menu, UGraphNodeContextMenuContext* Context) const
{
	if (!Context->bIsDebugging)
	{
		{
			FToolMenuSection& Section = Menu->AddSection("ACFAnimGraphNodeAddPose",
				LOCTEXT("AddPoseHeader", "Add Pose Pin"));

			Section.AddMenuEntry(
				"AddPose",
				LOCTEXT("AddPose", "Add Pose Pin"),
				LOCTEXT("AddPoseTooltip", "Add a new pose pin with an associated Gameplay Tag"),
				FSlateIcon(),
				FUIAction(FExecuteAction::CreateUObject(
					const_cast<UAnimGraphNode_ACFBlendPosesByGameplayTag*>(this),
					&UAnimGraphNode_ACFBlendPosesByGameplayTag::AddPosePin))
			);
		}

		if (Context->Pin && (Context->Pin->Direction == EGPD_Input))
		{
			int32 RawArrayIndex = 0;
			bool bIsPosePin = false;
			bool bIsTimePin = false;
			GetPinInformation(Context->Pin->PinName.ToString(), RawArrayIndex, bIsPosePin, bIsTimePin);

			if ((bIsPosePin || bIsTimePin) && RawArrayIndex > 0)
			{
				FToolMenuSection& Section = Menu->AddSection("ACFAnimGraphNodeRemovePose");
				Section.AddMenuEntry(
					"RemovePose",
					LOCTEXT("RemovePose", "Remove Pose Pin"),
					LOCTEXT("RemovePoseTooltip", "Remove this pose pin and its associated Gameplay Tag"),
					FSlateIcon(),
					FUIAction(FExecuteAction::CreateUObject(
						const_cast<UAnimGraphNode_ACFBlendPosesByGameplayTag*>(this),
						&UAnimGraphNode_ACFBlendPosesByGameplayTag::RemovePosePin,
						const_cast<UEdGraphPin*>(Context->Pin)))
				);
			}
		}
	}
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::AddPosePin()
{
	FScopedTransaction Transaction(LOCTEXT("AddPosePinTransaction", "Add Pose Pin"));
	Modify();

	TagEntries.AddDefaulted();
	Node.AddPose();

	ReconstructNode();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(GetBlueprint());
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::RemovePosePin(UEdGraphPin* Pin)
{
	int32 RawArrayIndex = 0;
	bool bIsPosePin = false;
	bool bIsTimePin = false;
	GetPinInformation(Pin->PinName.ToString(), RawArrayIndex, bIsPosePin, bIsTimePin);

	const int32 TagIndex = (bIsPosePin || bIsTimePin) ? (RawArrayIndex - 1) : INDEX_NONE;

	if (TagIndex != INDEX_NONE && TagEntries.IsValidIndex(TagIndex))
	{
		FScopedTransaction Transaction(LOCTEXT("RemovePosePinTransaction", "Remove Pose Pin"));
		Modify();

		TagEntries.RemoveAt(TagIndex);

		RemovedPinArrayIndex = RawArrayIndex;
		Node.RemovePose(RawArrayIndex);
		Pin->SetSavePinIfOrphaned(false);

		ReconstructNode();
		FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(GetBlueprint());
	}
}

void UAnimGraphNode_ACFBlendPosesByGameplayTag::GetPinInformation(const FString& InPinName, int32& Out_PinIndex, bool& Out_bIsPosePin, bool& Out_bIsTimePin)
{
	const int32 UnderscoreIndex = InPinName.Find(TEXT("_"), ESearchCase::CaseSensitive);
	if (UnderscoreIndex != INDEX_NONE)
	{
		const FString ArrayName = InPinName.Left(UnderscoreIndex);
		Out_PinIndex = FCString::Atoi(*(InPinName.Mid(UnderscoreIndex + 1)));
		Out_bIsPosePin = (ArrayName == TEXT("BlendPose"));
		Out_bIsTimePin = (ArrayName == TEXT("BlendTime"));
	}
	else
	{
		Out_bIsPosePin = false;
		Out_bIsTimePin = false;
		Out_PinIndex = INDEX_NONE;
	}
}

#undef LOCTEXT_NAMESPACE
