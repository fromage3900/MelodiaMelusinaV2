// OrreryMainMenuGameMode.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "Blueprint/UserWidget.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundBase.h"
#include "OrreryMainMenuGameMode.generated.h"

class UMelodiaStorySequenceData;
class UMelodiaStorySequenceWidget;
class UTextBlock;

/**
 * Dedicated front-end GameMode. It spawns the configured main-menu widget,
 * switches the first local player to UI-only input, and never creates a
 * gameplay pawn or performs level travel by itself.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AOrreryMainMenuGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    AOrreryMainMenuGameMode();

    virtual void BeginPlay() override;

protected:
    /** Creates the stock JRPG save object, then begins the opening map. */
    UFUNCTION()
    void HandleNewGameClicked();

    /** Restores the stock JRPG save object, then enters the opening map. */
    UFUNCTION()
    void HandleContinueClicked();

    /** Opens the existing canonical-slot panel; it never owns a second save format. */
    UFUNCTION()
    void HandleLoadGameClicked();

    UFUNCTION()
    void HandleSettingsClicked();

    UFUNCTION()
    void HandleSettingsBackClicked();

    /** Lightweight front-end feedback, intentionally optional so authored menus remain compatible. */
    void SetSaveStateFeedback(const FText& Message);

    /** Plays the authored project click cue before dispatching a menu action. */
    void PlayMenuClickSound();

    /** Opens the authored presentation sequence after canonical New Game creation. */
    void BeginOpeningSequence();

    /**
     * Routes the authored opening-map travel through the cross-module authority
     * locator (Decision 030), falling back to a direct OpenLevel only if no
     * travel provider has registered. MelodiaCore-native code cannot reach
     * UMelodiaTravelSubsystem directly -- see MelodiaSharedAuthorityInterfaces.h.
     */
    void TravelToOpeningMap();

    UFUNCTION()
    void HandleOpeningSequenceFinished(UMelodiaStorySequenceData* FinishedSequence);

    /** Widget class shown by the dedicated front-end map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "MainMenu")
    TSubclassOf<UUserWidget> MainMenuWidgetClass;

    /**
     * Native fallback kept soft so editor GameMode construction never forces a
     * UMG package load/compile. It is resolved only when the menu map begins.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "MainMenu")
    TSoftClassPtr<UUserWidget> MainMenuWidgetFallbackClass;

    /** Existing authored panel whose Load Slot action calls the stock JRPG load route. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "MainMenu|Save")
    TSoftClassPtr<UUserWidget> SaveLoadPanelClass;

    /** Player-preference panel. This is presentation-only and never touches canonical save data. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "MainMenu|Settings")
    TSoftClassPtr<UUserWidget> SettingsPanelClass;

    /** Reusable presentation-only story sequence shown after a new canonical save. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="MainMenu|Opening")
    TSoftClassPtr<UMelodiaStorySequenceWidget> OpeningSequenceWidgetFallbackClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="MainMenu|Opening")
    TSoftObjectPtr<UMelodiaStorySequenceData> OpeningSequenceAsset;
    /** Ambient sound to play on the main menu */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Audio")
    USoundBase* MenuAmbienceSound = nullptr;

    /** Authored non-spatial cue used by every live front-menu action. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Audio")
    TSoftObjectPtr<USoundBase> MenuClickSound;

    /** Audio component that will play the ambience */
    UPROPERTY(Transient)
    UAudioComponent* AmbienceAudioComponent = nullptr;

    /** Canonical stock-JRPG slot kept by the existing menu/save integration.
     *  MelodiaJRPGSlot0: the single slot every writer/reader in the project uses
     *  (WBP_MainMenu CreateCanonicalJRPGSlot, BP_MelodiaJRPGGameInstance::slotName_0,
     *  BP_SavePointBase). "MelusinaSlot0" predates the unification and stranded
     *  New Game/Continue on a different slot than the save points. */
    UPROPERTY(EditDefaultsOnly, Category="MainMenu|Save")
    FString CanonicalSaveSlot = TEXT("MelodiaJRPGSlot0");

    /** Showcase entry map; the existing integrated GameInstance owns restored state. */
    UPROPERTY(EditDefaultsOnly, Category="MainMenu|Travel")
    FName OpeningMap = TEXT("/Game/Melodia/Levels/Opening/L_MelusinaMorning");

    UPROPERTY(Transient)
    TObjectPtr<UMelodiaStorySequenceWidget> ActiveOpeningSequence;

    /** Kept alive while the user chooses a canonical slot. */
    UPROPERTY(Transient)
    TObjectPtr<UUserWidget> ActiveSaveLoadPanel;

    UPROPERTY(Transient)
    TObjectPtr<UUserWidget> ActiveSettingsPanel;

    UPROPERTY(Transient)
    TObjectPtr<UTextBlock> SaveStateText;
};
