#include "MonolithEditorModule.h"
#include "MonolithEditorActions.h"
#include "MonolithEditorMapActions.h"
#include "MonolithPieObjectActions.h"
#include "MonolithPieInputActions.h"
#include "MonolithPieTimeseries.h"
#include "MonolithStatActions.h"
#include "MonolithSettingsCustomization.h"
#include "MonolithToolRegistry.h"
#include "MonolithJsonUtils.h"
#include "MonolithSettings.h"
#include "PropertyEditorModule.h"
#include "Misc/OutputDeviceRedirector.h"

// PART C — passive modal watcher.
#include "Misc/CoreDelegates.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"
#include "Layout/Children.h"

#define LOCTEXT_NAMESPACE "FMonolithEditorModule"

namespace
{
	// Recursively walk a Slate widget subtree, appending the text of every STextBlock
	// found to OutText (newline-joined). Best-effort and depth-bounded so a pathological
	// tree can't stall the broadcast. The broadcasting thread is the game thread; this
	// runs before the modal's nested loop starts.
	void HarvestTextBlocks(const TSharedPtr<SWidget>& Widget, FString& OutText, int32 Depth)
	{
		if (!Widget.IsValid() || Depth > 12)
		{
			return;
		}
		// STextBlock is a SLeafWidget — identify by widget type name (no RTTI dependency).
		if (Widget->GetType() == TEXT("STextBlock"))
		{
			const FText Text = StaticCastSharedPtr<STextBlock>(Widget)->GetText();
			if (!Text.IsEmpty())
			{
				if (!OutText.IsEmpty()) { OutText.Append(TEXT(" | ")); }
				OutText.Append(Text.ToString());
			}
		}
		if (FChildren* Children = Widget->GetChildren())
		{
			const int32 Num = Children->Num();
			for (int32 Index = 0; Index < Num; ++Index)
			{
				HarvestTextBlocks(Children->GetChildAt(Index), OutText, Depth + 1);
			}
		}
	}
}

void FMonolithEditorModule::StartupModule()
{
	if (!GetDefault<UMonolithSettings>()->bEnableEditor) return;

	LogCapture = new FMonolithLogCapture();
	GLog->AddOutputDevice(LogCapture);

	FMonolithEditorActions::RegisterActions(LogCapture);
	FMonolithEditorMapActions::RegisterActions(FMonolithToolRegistry::Get());  // F8: create_empty_map + get_module_status
	// Gap 8: live-PIE object property read + function call (editor namespace).
	FMonolithPieObjectActions::RegisterActions(FMonolithToolRegistry::Get());
	// Gap 9: time-series PIE sampling with scripted provocation. Implemented in
	// MonolithEditor (it owns the async PIE-smoke session machinery) but registered
	// under the "animation" namespace string — the registry is namespace-string-keyed,
	// not module-keyed (see UnregisterNamespace note in ShutdownModule).
	FMonolithPieTimeseries::RegisterActions(FMonolithToolRegistry::Get());
	// Gap 4: deterministic PIE input/control driving (set control rotation with hold,
	// inject Enhanced Input action, free-fly spectator possess). The held-rotation /
	// repeated-input re-apply state is dropped on PIE end via the hook below.
	FMonolithPieInputActions::RegisterActions(FMonolithToolRegistry::Get());
	FMonolithPieInputActions::RegisterPieEndHook();
	// Gap 10: programmatic stat-group counter/cycle readout (#if STATS gated).
	FMonolithStatActions::RegisterActions(FMonolithToolRegistry::Get());

	// Register settings detail customization
	FPropertyEditorModule& PropModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
	PropModule.RegisterCustomClassLayout(
		UMonolithSettings::StaticClass()->GetFName(),
		FOnGetDetailCustomizationInstance::CreateStatic(&FMonolithSettingsCustomization::MakeInstance)
	);

	const int32 EditorActionCount = FMonolithToolRegistry::Get().GetActions(TEXT("editor")).Num();
	UE_LOG(LogMonolith, Log, TEXT("Monolith — Editor module loaded (%d editor actions)"), EditorActionCount);

	// PART C — subscribe to the pre-Slate-modal broadcast so we can log modal context
	// just before the blocking nested loop starves the in-process MCP server.
#if WITH_EDITOR
	PreSlateModalHandle = FCoreDelegates::PreSlateModal.AddRaw(this, &FMonolithEditorModule::OnPreSlateModal);
#endif
}

void FMonolithEditorModule::OnPreSlateModal()
{
	// Always emit at least a timestamped "modal opening" line — text extraction below
	// is best-effort (the window may not yet be on the modal stack at broadcast time).
	FString Title;
	FString Text;

	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication& Slate = FSlateApplication::Get();
		TSharedPtr<SWindow> Window = Slate.GetActiveModalWindow();
		if (!Window.IsValid())
		{
			Window = Slate.GetActiveTopLevelWindow();
		}
		if (Window.IsValid())
		{
			Title = Window->GetTitle().ToString();
			HarvestTextBlocks(Window->GetContent(), Text, 0);
		}
	}

	UE_LOG(LogMonolith, Warning,
		TEXT("MODAL_OPEN ts='%s' title='%s' text='%s' — game thread is about to enter a blocking modal loop; MCP will be unresponsive until dismissed."),
		*FDateTime::Now().ToString(TEXT("%Y-%m-%dT%H:%M:%S")), *Title, *Text);
}

void FMonolithEditorModule::ShutdownModule()
{
#if WITH_EDITOR
	if (PreSlateModalHandle.IsValid())
	{
		FCoreDelegates::PreSlateModal.Remove(PreSlateModalHandle);
		PreSlateModalHandle.Reset();
	}
#endif

	// Gap 4: drop the PIE-end hook + any residual held-rotation / repeated-input / spectator state.
	FMonolithPieInputActions::UnregisterPieEndHook();

	FMonolithToolRegistry::Get().UnregisterNamespace(TEXT("editor"));

	if (FModuleManager::Get().IsModuleLoaded("PropertyEditor"))
	{
		FPropertyEditorModule& PropModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
		PropModule.UnregisterCustomClassLayout(UMonolithSettings::StaticClass()->GetFName());
	}

	if (LogCapture)
	{
		GLog->RemoveOutputDevice(LogCapture);
		delete LogCapture;
		LogCapture = nullptr;
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMonolithEditorModule, MonolithEditor)
