// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/**
 * Quillscript plugin runtime module.
 */
class FQuillscriptModule final : public IModuleInterface
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;


private:
	/// Console Commands (Cheat Codes)

	static void Cmd_Next();
	static void Cmd_Rollback();
	static void Cmd_End();
	static void Cmd_Stop();
	static void Cmd_Restore();
	static void Cmd_Play(const TArray<FString>& Args);
	static void Cmd_PlayByLabel(const TArray<FString>& Args);

	static void Cmd_Var(const TArray<FString>& Args);
	static void Cmd_Del(const TArray<FString>& Args);
	static void Cmd_Eval(const TArray<FString>& Args);

	static void Cmd_Bypass();
	static void Cmd_NotBypass();

	static void Cmd_ToggleDebugger();
};