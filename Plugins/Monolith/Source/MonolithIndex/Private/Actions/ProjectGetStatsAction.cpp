#include "Actions/ProjectGetStatsAction.h"
#include "MonolithIndexSubsystem.h"
#include "MonolithParamSchema.h"
#include "Editor.h"

FMonolithActionResult FProjectGetStatsAction::Execute(const TSharedPtr<FJsonObject>& Params)
{
	UMonolithIndexSubsystem* Subsystem = GEditor->GetEditorSubsystem<UMonolithIndexSubsystem>();
	if (!Subsystem)
	{
		return FMonolithActionResult::Error(TEXT("Index subsystem not available"));
	}

	TSharedPtr<FJsonObject> Stats = Subsystem->GetStats();
	if (!Stats.IsValid())
	{
		return FMonolithActionResult::Error(TEXT("Failed to retrieve stats"));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("success"), true);

	bool bIndexing = Subsystem->IsIndexing();
	Result->SetBoolField(TEXT("indexing"), bIndexing);
	if (bIndexing)
	{
		Result->SetNumberField(TEXT("progress"), Subsystem->GetProgress());
		Result->SetStringField(TEXT("status"), Subsystem->GetStatusMessage());
	}
	Result->SetObjectField(TEXT("stats"), Stats);
	return FMonolithActionResult::Success(Result);
}

TSharedPtr<FJsonObject> FProjectGetStatsAction::GetSchema()
{
	return MakeShared<FJsonObject>();
}
