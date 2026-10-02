// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "AGSGraphEditorSettings.generated.h"

UENUM()
enum class EAGSGraphNodeStyle : uint8
{
	ModernHeader UMETA(DisplayName = "Modern (Colored Header)"),
	Filled UMETA(DisplayName = "Filled (Fully Tinted)"),
	Minimal UMETA(DisplayName = "Minimal (Accent Bar)"),
	Classic UMETA(DisplayName = "Classic (Legacy Frame)")
};

/** Visual settings for all AGS-based graph editors (dialogues, quests, combos, AI). */
UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Graph Editor Settings"))
class AGSGRAPHEDITOR_API UAGSGraphEditorSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:

	/** Visual style used to render graph nodes. Reopen the graph editor tab to apply. */
	UPROPERTY(EditAnywhere, config, Category = "Nodes")
	EAGSGraphNodeStyle NodeStyle = EAGSGraphNodeStyle::ModernHeader;

	/** Minimum width of graph nodes. Reopen the graph editor tab to apply. */
	UPROPERTY(EditAnywhere, config, Category = "Nodes", meta = (ClampMin = "60", ClampMax = "400"))
	float NodeMinWidth = 140.0f;

	/** Thickness of connection wires between nodes. */
	UPROPERTY(EditAnywhere, config, Category = "Wires", meta = (ClampMin = "0.5", ClampMax = "8.0"))
	float WireThickness = 2.5f;
};
