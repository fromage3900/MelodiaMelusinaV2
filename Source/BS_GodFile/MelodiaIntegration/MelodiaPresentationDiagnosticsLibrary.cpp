#include "MelodiaPresentationDiagnosticsLibrary.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "MelodiaPrototypeCaptureSubsystem.h"
#include "MelodiaAudioReactivePresentationSubsystem.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaPersonaSubsystem.h"
#include "Kismet/GameplayStatics.h"

void UMelodiaPresentationDiagnosticsLibrary::LogPrototypePresentationState(const UObject* WorldContextObject)
{
	UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	if (!World)
	{
		return;
	}

	APlayerController* Controller = World->GetFirstPlayerController();
	AGameModeBase* GameMode = World->GetAuthGameMode();
	UMelodiaPrototypeCaptureSubsystem* Capture = World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaPrototypeCaptureSubsystem>() : nullptr;
	UE_LOG(LogTemp, Log, TEXT("Melodia presentation: map=%s gameMode=%s controller=%s pawn=%s capture=%s"),
		*World->GetMapName(),
		*GetNameSafe(GameMode),
		*GetNameSafe(Controller),
		*GetNameSafe(Controller ? Controller->GetPawn() : nullptr),
		Capture ? *Capture->GetCaptureSurfaceLabel().ToString() : TEXT("Unavailable"));
}

void UMelodiaPresentationDiagnosticsLibrary::LogGameplayFoundationState(const UObject* WorldContextObject)
{
	UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr;
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (!World || !GameInstance)
	{
		return;
	}

	const UMelodiaExternalJRPGBridgeSubsystem* Bridge = GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();
	const UMelodiaAudioReactivePresentationSubsystem* AudioPresentation = GameInstance->GetSubsystem<UMelodiaAudioReactivePresentationSubsystem>();
	const UMelodiaPersonaSubsystem* Persona = GameInstance->GetSubsystem<UMelodiaPersonaSubsystem>();
	const APlayerController* Controller = World->GetFirstPlayerController();
	// MelodiaJRPGSlot0 is the canonical slot (OrreryMainMenuGameMode::CanonicalSaveSlot,
	// BP_MelodiaJRPGGameInstance::slotName_0, BP_SavePointBase). This check previously read
	// MelusinaSlot0 — the quarantined MelodiaCore lane's slot — so the log reported
	// canonical_slot=false whenever the real canonical save existed.
	const bool bCanonicalSlotExists = UGameplayStatics::DoesSaveGameExist(TEXT("MelodiaJRPGSlot0"), 0);

	UE_LOG(LogTemp, Log,
		TEXT("MELODIA_FOUNDATION_STATE map=%s controller=%s jrpg_bridge_active=%s encounter=%s harmonic_presentation_active=%s available_quests=%d canonical_slot=%s"),
		*World->GetMapName(),
		*GetNameSafe(Controller),
		Bridge && Bridge->IsJRPGBattleActive() ? TEXT("true") : TEXT("false"),
		Bridge ? *Bridge->GetActiveEncounterId().ToString() : TEXT("None"),
		AudioPresentation && AudioPresentation->IsPresentationBattleActive() ? TEXT("true") : TEXT("false"),
		Persona ? Persona->GetAvailableQuests().Num() : 0,
		bCanonicalSlotExists ? TEXT("true") : TEXT("false"));
}
