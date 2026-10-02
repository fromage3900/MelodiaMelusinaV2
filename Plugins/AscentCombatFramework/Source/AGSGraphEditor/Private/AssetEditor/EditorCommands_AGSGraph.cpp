#include "EditorCommands_AGSGraph.h"
#include "Framework/Commands/Commands.h"
#include "Framework/Commands/UICommandInfo.h"
#include "Framework/Commands/InputChord.h"

#define LOCTEXT_NAMESPACE "EditorCommands_AGSGraph"

void FEditorCommands_AGSGraph::RegisterCommands()
{
	UI_COMMAND(GraphSettings, "Graph Settings", "Graph Settings", EUserInterfaceActionType::Button, FInputChord());

}

#undef LOCTEXT_NAMESPACE
