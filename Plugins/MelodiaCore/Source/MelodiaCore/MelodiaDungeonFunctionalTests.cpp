#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Tests/AutomationEditorCommon.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Components/BoxComponent.h"
#include "Misc/AutomationTest.h"
#include "MelodiaBattleSession.h"
#include "MelodiaDungeonRunCoordinator.h"
#include "MelodiaRoomExit.h"
#include "MelodiaRoguelikeRunSubsystem.h"

namespace
{
class FMelodiaThreeStagePhysicalRouteCommand final : public IAutomationLatentCommand
{
public:
    FMelodiaThreeStagePhysicalRouteCommand(FAutomationTestBase* InTest, const bool bInRunEndlessSoak = false)
        : Test(InTest)
        , StartedAt(FPlatformTime::Seconds())
        , bRunEndlessSoak(bInRunEndlessSoak)
    {
    }

    virtual bool Update() override
    {
        if (FPlatformTime::Seconds() - StartedAt > (bRunEndlessSoak ? 240.0 : 120.0))
        {
            Test->AddError(TEXT("Physical dungeon route timed out."));
            return true;
        }

        UWorld* World = FindPIEWorld();
        if (!World)
        {
            return false;
        }

        AMelodiaDungeonRunCoordinator* Coordinator = FindCoordinator(World);
        UGameInstance* GameInstance = World->GetGameInstance();
        UMelodiaRoguelikeRunSubsystem* Run = GameInstance
            ? GameInstance->GetSubsystem<UMelodiaRoguelikeRunSubsystem>()
            : nullptr;
        UMelodiaBattleSession* Battle = GameInstance
            ? GameInstance->GetSubsystem<UMelodiaBattleSession>()
            : nullptr;
        if (!Coordinator || !Run || !Battle)
        {
            return false;
        }

        if (!bRunStarted)
        {
            if (!Coordinator->StartFirstDungeonRun(31077))
            {
                Test->AddError(TEXT("Coordinator rejected StartFirstDungeonRun."));
                return true;
            }
            bRunStarted = true;
            InitialHP = Battle->PersistentPartyHP;
            InitialSP = Battle->PersistentSkillPoints;
            return false;
        }

        if (Run->LifecyclePhase == EMelodiaRunLifecyclePhase::RecoverableFailure)
        {
            Test->AddError(FString::Printf(TEXT("Generation entered RecoverableFailure at stage %d (%s)."),
                Run->CurrentStageIndex, *Run->AuthoritativeStage.RoomDataId.ToString()));
            return true;
        }
        if (Run->LifecyclePhase == EMelodiaRunLifecyclePhase::Defeated)
        {
            Test->AddError(TEXT("Run was defeated during the physical-route smoke."));
            return true;
        }

        if (bWaitingForExitAdvance)
        {
            if (Run->CurrentStageIndex > StageBeforeExit)
            {
                bWaitingForExitAdvance = false;
                bMovedOutside = false;
                bMovedInside = false;
                return false;
            }
            return MovePawnAcrossExit(World, Coordinator);
        }

        if (Run->LifecyclePhase != EMelodiaRunLifecyclePhase::Exploring)
        {
            return false;
        }

        Test->TestEqual(TEXT("Persistent HP survives regeneration"), Battle->PersistentPartyHP, InitialHP);
        Test->TestEqual(TEXT("Persistent SP survives regeneration"), Battle->PersistentSkillPoints, InitialSP);

        if (bRunEndlessSoak && Run->bEndlessMode && LastCountedEndlessStage != Run->CurrentStageIndex)
        {
            LastCountedEndlessStage = Run->CurrentStageIndex;
            ++SuccessfulEndlessGenerations;
            if (SuccessfulEndlessGenerations >= 25)
            {
                Test->TestEqual(TEXT("Twenty-five generated endless rooms reach depth 25"), Run->EndlessDepth, 25);
                return true;
            }
        }

        if (!Run->NotifyEncounterStarted())
        {
            Test->AddError(FString::Printf(TEXT("Could not start encounter at stage %d."), Run->CurrentStageIndex));
            return true;
        }
        if (!Run->RecordEncounterResult(EMelodiaEncounterResult::Victory))
        {
            Test->AddError(FString::Printf(TEXT("Could not record victory at stage %d."), Run->CurrentStageIndex));
            return true;
        }

        if (!Run->bEndlessMode && Run->CurrentStageIndex >= 2)
        {
            Test->TestEqual(TEXT("Three-stage route reaches Complete phase"), Run->Phase, EMelodiaRunPhase::Complete);
            Test->TestEqual(TEXT("Structured completion offers endless continuation"), Run->LifecyclePhase, EMelodiaRunLifecyclePhase::EndlessOffer);
            Test->TestTrue(TEXT("Three-stage completion makes Sir Melodious available"), Run->bSirMelodiousAvailable);
            if (!bRunEndlessSoak)
            {
                return true;
            }
            if (!Coordinator->ContinueEndlessRun())
            {
                Test->AddError(TEXT("Coordinator rejected the earned endless continuation offer."));
                return true;
            }
            return false;
        }

        if (!Coordinator->CommitReward(0))
        {
            Test->AddError(FString::Printf(TEXT("Could not commit reward at stage %d."), Run->CurrentStageIndex));
            return true;
        }
        if (!Coordinator->ActiveRoomExit || Coordinator->ActiveRoomExit->bLocked)
        {
            Test->AddError(FString::Printf(TEXT("Stage %d has no unlocked authoritative exit."), Run->CurrentStageIndex));
            return true;
        }

        StageBeforeExit = Run->CurrentStageIndex;
        bWaitingForExitAdvance = true;
        return false;
    }

private:
    static UWorld* FindPIEWorld()
    {
        if (!GEngine)
        {
            return nullptr;
        }
        for (const FWorldContext& Context : GEngine->GetWorldContexts())
        {
            if (Context.WorldType == EWorldType::PIE)
            {
                return Context.World();
            }
        }
        return nullptr;
    }

    static AMelodiaDungeonRunCoordinator* FindCoordinator(UWorld* World)
    {
        for (TActorIterator<AMelodiaDungeonRunCoordinator> It(World); It; ++It)
        {
            return *It;
        }
        return nullptr;
    }

    bool MovePawnAcrossExit(UWorld* World, AMelodiaDungeonRunCoordinator* Coordinator)
    {
        APlayerController* PC = World->GetFirstPlayerController();
        APawn* Pawn = PC ? PC->GetPawn() : nullptr;
        AMelodiaRoomExit* Exit = Coordinator->ActiveRoomExit;
        if (!Pawn || !Exit || !Exit->TriggerVolume)
        {
            return false;
        }

        const FVector ExitLocation = Exit->TriggerVolume->GetComponentLocation();
        if (!bMovedOutside)
        {
            Pawn->SetActorLocation(ExitLocation + FVector(500.0, 0.0, 0.0), false, nullptr, ETeleportType::TeleportPhysics);
            Exit->TriggerVolume->UpdateOverlaps();
            bMovedOutside = true;
            return false;
        }
        if (!bMovedInside)
        {
            Pawn->SetActorLocation(ExitLocation, false, nullptr, ETeleportType::TeleportPhysics);
            Exit->TriggerVolume->UpdateOverlaps();
            bMovedInside = true;
        }
        return false;
    }

    FAutomationTestBase* Test = nullptr;
    double StartedAt = 0.0;
    float InitialHP = 0.0f;
    int32 InitialSP = 0;
    int32 StageBeforeExit = INDEX_NONE;
    bool bRunStarted = false;
    bool bWaitingForExitAdvance = false;
    bool bMovedOutside = false;
    bool bMovedInside = false;
    bool bRunEndlessSoak = false;
    int32 LastCountedEndlessStage = INDEX_NONE;
    int32 SuccessfulEndlessGenerations = 0;
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaThreeStagePhysicalRouteTest,
    "Melodia.Roguelike.Functional.ThreeStagePhysicalRoute",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaThreeStagePhysicalRouteTest::RunTest(const FString& Parameters)
{
    // CommonUI's stock viewport warning is unrelated to dungeon correctness but is promoted to an automation error.
    AddExpectedError(TEXT("Using CommonUI without a CommonGameViewportClient"), EAutomationExpectedErrorFlags::Contains, 1);
    ADD_LATENT_AUTOMATION_COMMAND(FEditorLoadMap(TEXT("/Game/ZenForestTest")));
    ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
    ADD_LATENT_AUTOMATION_COMMAND(FMelodiaThreeStagePhysicalRouteCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
    return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMelodiaTwentyFiveGenerationSoakTest,
    "Melodia.Roguelike.Functional.TwentyFiveGenerationSoak",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaTwentyFiveGenerationSoakTest::RunTest(const FString& Parameters)
{
    AddExpectedError(TEXT("Using CommonUI without a CommonGameViewportClient"), EAutomationExpectedErrorFlags::Contains, 1);
    ADD_LATENT_AUTOMATION_COMMAND(FEditorLoadMap(TEXT("/Game/ZenForestTest")));
    ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
    ADD_LATENT_AUTOMATION_COMMAND(FMelodiaThreeStagePhysicalRouteCommand(this, true));
    ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
    return true;
}

#endif
