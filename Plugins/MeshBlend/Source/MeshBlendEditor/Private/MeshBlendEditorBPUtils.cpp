// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendEditorBPUtils.h"

#include "Editor.h"
#include "MeshBlendActivatorSubsystem.h"
#include "MeshBlendConfigUtils.h"
#include "Framework/Application/SlateApplication.h"

#define LOCTEXT_NAMESPACE "UMeshBlendEditorBPUtils"

void UMeshBlendEditorBPUtils::SetSlateThrottling(const int Value)
{
	static IConsoleVariable* CVarSlateThrottling = IConsoleManager::Get().FindConsoleVariable(TEXT("Slate.bAllowThrottling"));

	if (CVarSlateThrottling)
	{
		CVarSlateThrottling->Set(Value, ECVF_SetByConsole);
	}
}

int UMeshBlendEditorBPUtils::GetSlateThrottling()
{
	static IConsoleVariable* CVarSlateThrottling = IConsoleManager::Get().FindConsoleVariable(TEXT("Slate.bAllowThrottling"));

	if (CVarSlateThrottling)
	{
		return CVarSlateThrottling->GetInt();
	}

	return 0;
}

void UMeshBlendEditorBPUtils::SetMeshBlendConsoleVariable(const FString Name, const float Value)
{
	if (IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(*Name, false))
	{
		CVar->Set(Value, ECVF_SetByConsole);
	}
}

float UMeshBlendEditorBPUtils::GetMeshBlendConsoleVariable(const FString Name)
{
	if (const IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(*Name, false))
	{
		return CVar->GetFloat();
	}

	return 0.0f;
}

void UMeshBlendEditorBPUtils::ResizeEditorUtilityWidget(UEditorUtilityWidget* Widget, const float X, const float Y)
{
	if (Widget->GetCachedWidget().IsValid())
	{
		const TSharedRef<const SWidget> CachedWidget = Widget->GetCachedWidget().ToSharedRef();
		const TSharedPtr<SWindow> TabWindow = FSlateApplication::Get().FindWidgetWindow(CachedWidget);

		if (TabWindow.IsValid())
		{
			const float ApplicationScale = FSlateApplication::Get().GetApplicationScale() * TabWindow->GetDPIScaleFactor();
			const FVector2f DesiredSize(X * ApplicationScale, Y * ApplicationScale);
			TabWindow->Resize(DesiredSize);
		}
	}
}

bool UMeshBlendEditorBPUtils::HasMeshBlendConsoleVariables()
{
	return FMeshBlendConfigUtils::IsAllowStaticLightingCVarCorrect() && FMeshBlendConfigUtils::IsLumenMaterialAOCVarCorrect();
}

void UMeshBlendEditorBPUtils::TryAddMeshBlendConsoleVariables()
{
	FMeshBlendConfigUtils::FixConsoleSettings();
}

void UMeshBlendEditorBPUtils::ToggleEnabled()
{
	static const auto CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.Enable"));
	CVar->Set(!CVar->GetBool(), ECVF_SetByConsole);
	GEditor->RedrawAllViewports(true);
}

bool UMeshBlendEditorBPUtils::IsEnabled()
{
	static const auto CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.Enable"));
	return CVar->GetBool();
}

void UMeshBlendEditorBPUtils::ToggleDebugVisualization()
{
	static const auto CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.Visualize"));
	CVar->Set(CVar->GetInt() == 0 ? 1 : 0, ECVF_SetByConsole);
	GEditor->RedrawAllViewports(true);
}

bool UMeshBlendEditorBPUtils::GetDebugVisualization()
{
	static const auto CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.Visualize"));
	return CVar->GetInt() == 1;
}


void UMeshBlendEditorBPUtils::TryResetMeshActivator()
{
	static const auto CVarCustomerGBufferChannel = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.CustomerGBufferChannel"));
	const UWorld* World = GWorld;

	if (GEditor && GEditor->PlayWorld != nullptr)
	{
		World = GEditor->PlayWorld;
	}

	if (World)
	{
		if (const UMeshBlendActivatorSubsystem* Subsystem = UMeshBlendActivatorSubsystem::GetInstance(World))
		{
			Subsystem->MeshBlendActivatorLogic->RestartActivator(World, false);
		}
	}

	if (GEditor && GEditor->PlayWorld == nullptr && !GEditor->IsAnyViewportRealtime())
	{
		FMessageLog("MapCheck")
			.Warning()
			->AddToken(FTextToken::Create(LOCTEXT(
				"MapCheck_MeshBlendViewportNotRealtime",
				"MeshBlend will only update blending in the editor when the viewport is realtime.")));

		FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
	}

	if (CVarCustomerGBufferChannel->GetBool())
	{
		return;
	}

	if (!FMeshBlendConfigUtils::IsLumenMaterialAOCVarCorrect())
	{
		FMessageLog("MapCheck")
			.Warning()
			->AddToken(FTextToken::Create(LOCTEXT(
				"MapCheck_MeshBlendScreenProbeGatherMaterialAO",
				"r.Lumen.ScreenProbeGather.MaterialAO needs to be 0 to avoid shadow artifacts with MeshBlend.")))
			->AddToken(FActionToken::Create(
				LOCTEXT("MapCheck_MeshBlendActivatorConsoleAction", "Fix console settings"),
				LOCTEXT("MapCheck_MeshBlendActivatorConsoleToolTip", "Click to fix console settings"),
				FOnActionTokenExecuted::CreateStatic(&FMeshBlendConfigUtils::FixConsoleSettings)
			))
			->AddToken(FURLToken::Create(
				"https://meshblend.lervik.com",
				LOCTEXT("MapCheck_MeshBlendActivatorNotFound_UrlText", "Click to open documentation")));

		FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
	}

	if (!FMeshBlendConfigUtils::IsAllowStaticLightingCVarCorrect())
	{
		FMessageLog("MapCheck")
			.Warning()
			->AddToken(FTextToken::Create(LOCTEXT(
				"MapCheck_MeshBlendAllowStaticLighting",
				"MeshBlend: r.AllowStaticLighting needs to be 0 for MeshBlend to work. Adjust project settings.")))
			->AddToken(FActionToken::Create(
				LOCTEXT("MapCheck_MeshBlendActivatorConsoleAction", "Fix console settings"),
				LOCTEXT("MapCheck_MeshBlendActivatorConsoleToolTip", "Click to fix console settings"),
				FOnActionTokenExecuted::CreateStatic(&FMeshBlendConfigUtils::FixConsoleSettings)
			))
			->AddToken(FURLToken::Create(
				"https://meshblend.lervik.com",
				LOCTEXT("MapCheck_MeshBlendActivatorNotFound_UrlText", "Click to open documentation")));

		FMessageLog("MapCheck").Open(EMessageSeverity::Warning, true);
	}
}

#undef LOCTEXT_NAMESPACE
