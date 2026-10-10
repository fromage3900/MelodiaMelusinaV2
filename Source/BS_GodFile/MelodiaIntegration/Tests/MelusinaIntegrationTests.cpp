// Automation tests for Melusina character, presentation, wardrobe, and traversal systems.
// (Source/BS_GodFile/MelodiaIntegration/Tests/MelusinaIntegrationTests.cpp)

#if WITH_DEV_AUTOMATION_TESTS

#include "../MelodiaHairComponent.h"
#include "../MelusinaSorrowSeamComponent.h"
#include "../MelodiaNarrativeTypes.h"
#include "../MelodiaNarrativeSubsystem.h"
#include "../MelodiaTraversalCapabilityProvider.h"
#include "../MelodiaTraversalComponent.h"
#include "MelodiaLocomotionAnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Misc/AutomationTest.h"
#if WITH_EDITOR
#include "Editor.h"
#include "Tests/AutomationEditorCommon.h"
#endif

// ---------------------------------------------------------------------------
// Melusina Sorrow Seam Presentation & Sheen Constants
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaSorrowSeamConstantsTest,
	"Melodia.Melusina.SorrowSeam.ConstantsAndDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaSorrowSeamConstantsTest::RunTest(const FString& Parameters)
{
	// 1. Static sheen thresholds matching specs/melusina_sorrow_seam.v1.json
	TestEqual(TEXT("PristineSheen matches spec (0.18f)"), UMelusinaSorrowSeamComponent::PristineSheen, 0.18f);
	TestEqual(TEXT("HealedSheen matches spec (0.32f)"), UMelusinaSorrowSeamComponent::HealedSheen, 0.32f);

	// 2. Component Class Default Object (CDO) invariants
	const UMelusinaSorrowSeamComponent* CDO = GetDefault<UMelusinaSorrowSeamComponent>();
	if (!CDO)
	{
		AddError(TEXT("Could not obtain UMelusinaSorrowSeamComponent CDO."));
		return false;
	}

	TestTrue(TEXT("SorrowSeam component can tick"), CDO->PrimaryComponentTick.bCanEverTick);
	TestEqual(TEXT("SorrowSeam ticks in TG_PostPhysics"), CDO->PrimaryComponentTick.TickGroup, TG_PostPhysics);
	TestEqual(TEXT("MendLerpSpeed default is 1.5f"), CDO->MendLerpSpeed, 1.5f);

	return true;
}

// ---------------------------------------------------------------------------
// Melusina Hair Tick Defaults
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaHairTickDefaultsTest,
	"Melodia.Melusina.Hair.TickDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaHairTickDefaultsTest::RunTest(const FString& Parameters)
{
	const UMelodiaHairComponent* CDO = GetDefault<UMelodiaHairComponent>();
	if (!CDO)
	{
		AddError(TEXT("Could not obtain UMelodiaHairComponent CDO."));
		return false;
	}

	TestTrue(TEXT("Hair component can tick"), CDO->PrimaryComponentTick.bCanEverTick);
	TestEqual(TEXT("Hair ticks in TG_PrePhysics"), CDO->PrimaryComponentTick.TickGroup, TG_PrePhysics);

	return true;
}

// ---------------------------------------------------------------------------
// Melusina Wardrobe Slot Mapping & Narrative Record Persistence Contract
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaWardrobeEquipContractTest,
	"Melodia.Melusina.Wardrobe.SlotEquipContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaWardrobeEquipContractTest::RunTest(const FString& Parameters)
{
	FMelodiaNarrativeRecord Record;
	Record.Version = FMelodiaNarrativeRecord::CurrentVersion;

	// Populate Melusina wardrobe slots
	const FName DressId(TEXT("Cos_Dress_Melusina"));
	const FName GlovesId(TEXT("Cos_Gloves_Melusina"));
	const FName TrailId(TEXT("Cos_Trail_Melusina_SorrowSeam"));
	const FName HairCharmId(TEXT("Cos_Hair_Melusina_Water"));

	Record.OwnedCosmeticIds.Add(DressId);
	Record.OwnedCosmeticIds.Add(GlovesId);
	Record.OwnedCosmeticIds.Add(TrailId);
	Record.OwnedCosmeticIds.Add(HairCharmId);

	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Body, DressId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Gloves, GlovesId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::Trail, TrailId);
	Record.EquippedCosmeticIds.Add(EMelodiaWardrobeSlot::HairCharm, HairCharmId);

	TestEqual(TEXT("Record contains 4 owned cosmetics"), Record.OwnedCosmeticIds.Num(), 4);
	TestEqual(TEXT("Record contains 4 equipped slots"), Record.EquippedCosmeticIds.Num(), 4);

	// Test migration preserves all equipped Melusina slots
	TestTrue(TEXT("Migration succeeds"), UMelodiaNarrativeSubsystem::MigrateRecord(Record));
	TestEqual(TEXT("Equipped Body is Dress"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Body), DressId);
	TestEqual(TEXT("Equipped Gloves is Gloves"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Gloves), GlovesId);
	TestEqual(TEXT("Equipped Trail is SorrowSeam"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::Trail), TrailId);
	TestEqual(TEXT("Equipped HairCharm is WaterHair"), Record.EquippedCosmeticIds.FindRef(EMelodiaWardrobeSlot::HairCharm), HairCharmId);

	return true;
}

// ---------------------------------------------------------------------------
// Melusina Traversal Capability Invariants
// ---------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelusinaTraversalCapabilityContractTest,
	"Melodia.Melusina.Traversal.CapabilityContract",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaTraversalCapabilityContractTest::RunTest(const FString& Parameters)
{
	// Canonical traversal capability identifiers
	TestEqual(TEXT("Glide capability ID"), MelodiaTraversalCapability::Glide, FName(TEXT("capability.melodia.glide")));
	TestEqual(TEXT("Dash capability ID"), MelodiaTraversalCapability::Dash, FName(TEXT("capability.melodia.dash")));
	TestEqual(TEXT("Swim capability ID"), MelodiaTraversalCapability::Swim, FName(TEXT("capability.melodia.swim")));

	return true;
}

#if WITH_EDITOR
namespace
{
// Opt-in integration test: the existing PIE pawn receives simulated controller
// key events. No traversal methods, transforms, or movement modes are forced.
class FMelusinaLiveJumpInputCommand : public IAutomationLatentCommand
{
public:
	FMelusinaLiveJumpInputCommand(FAutomationTestBase* InTest)
		: Test(InTest), WallStartedAt(FPlatformTime::Seconds())
	{
	}

	virtual ~FMelusinaLiveJumpInputCommand() override { SetJumpHeld(false); }

	virtual bool Update() override
	{
		if (FPlatformTime::Seconds() - WallStartedAt > 60.0)
		{
			Test->AddError(TEXT("Live input test exceeded its wall-clock limit."));
			return Finish();
		}
		if (Phase < 0)
		{
			UWorld* World = GEditor->PlayWorld;
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			ACharacter* Pawn = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
			if (!Pawn || !Pawn->GetCharacterMovement()->IsMovingOnGround()) { return false; }
			if (Pawn->GetClass()->GetName() != TEXT("BP_MelusinaJRPGCharacter_C")
				|| !Pawn->FindComponentByClass<UMelodiaTraversalComponent>())
			{
				Test->AddError(TEXT("Morning did not possess canonical Melusina with the existing traversal component."));
				return Finish();
			}
			Character = Pawn;
			Controller = PC;
			Traversal = Pawn->FindComponentByClass<UMelodiaTraversalComponent>();
			StartedAt = World->GetTimeSeconds();
			StartZ = Pawn->GetActorLocation().Z;
			OriginalGravity = Pawn->GetCharacterMovement()->GravityScale;
			Advance(0, StartedAt);
		}
		if (!Character.IsValid() || !Controller.IsValid() || !Traversal.IsValid())
		{
			Test->AddError(TEXT("PIE pawn/controller/traversal disappeared during live input test."));
			return Finish();
		}

		ACharacter* Pawn = Character.Get();
		UCharacterMovementComponent* Movement = Pawn->GetCharacterMovement();
		const double Now = Pawn->GetWorld()->GetTimeSeconds();
		const double Elapsed = Now - PhaseStartedAt;
		const double Height = Pawn->GetActorLocation().Z - StartZ;
		const UMelodiaLocomotionAnimInstance* Anim = Cast<UMelodiaLocomotionAnimInstance>(Pawn->GetMesh()->GetAnimInstance());
		const bool bGliding = Traversal->IsGliding();
		const int32 MachineIndex = Anim ? Anim->GetStateMachineIndex(FName(TEXT("MelusinaLocomotion"))) : INDEX_NONE;
		const FName StateName = MachineIndex != INDEX_NONE ? Anim->GetCurrentStateName(MachineIndex) : NAME_None;
		if (!Anim || Anim->GetClass()->GetName() != TEXT("ABP_Melusina_Current_C") || StateName.IsNone())
		{
			Test->AddError(TEXT("Live input requires canonical ABP_Melusina_Current and its running MelusinaLocomotion state machine."));
			return Finish();
		}
		ObservedStates.AddUnique(StateName.ToString());
		// Eligibility comes from movement/traversal, independently of the AnimInstance flags.
		// Allow the longest airborne blend (0.16s), or the contact blend (0.10s),
		// plus one animation-update frame before accepting the actual state as evidence.
		// Early/transitional samples stay in the trace.
		const bool bGrounded = Movement->IsMovingOnGround();
		const bool bRising = Movement->IsFalling() && !bGliding && Movement->Velocity.Z > 0.0f;
		const bool bDescending = Movement->IsFalling() && !bGliding && Movement->Velocity.Z <= 0.0f;
		UpdateEligibility(bRising, Now, RisingSince);
		UpdateEligibility(bDescending, Now, DescendingSince);
		UpdateEligibility(bGliding && !bGrounded, Now, GlidingSince);
		UpdateEligibility(bGrounded, Now, GroundedSince);
		const double StateGrace = 0.16 + Pawn->GetWorld()->GetDeltaSeconds();
		const double ContactGrace = 0.10 + Pawn->GetWorld()->GetDeltaSeconds();
		bTapJumpStart |= (Phase == 1 || Phase == 2) && ObserveState(TEXT("tap_rising_jump_start"), TEXT("JumpStart"), StateName, RisingSince, StateGrace, Now);
		bHoldJumpStart |= Phase == 4 && ObserveState(TEXT("hold_rising_jump_start"), TEXT("JumpStart"), StateName, RisingSince, StateGrace, Now);
		bTapAirborne |= Phase == 2 && ObserveState(TEXT("tap_descending_airborne"), TEXT("Airborne"), StateName, DescendingSince, StateGrace, Now);
		bStateGlided |= Phase == 4 && ObserveState(TEXT("held_glide"), TEXT("Glide"), StateName, GlidingSince, StateGrace, Now);
		bTapLanded |= Phase == 3 && ObserveState(TEXT("tap_landing"), TEXT("Land"), StateName, GroundedSince, ContactGrace, Now);
		bHoldLanded |= (Phase == 5 || Phase == 6) && ObserveState(TEXT("hold_landing"), TEXT("Land"), StateName, GroundedSince, ContactGrace, Now);
		bInitialIdle |= Phase == 0 && ObserveState(TEXT("initial_idle"), TEXT("Idle"), StateName, GroundedSince, StateGrace, Now);
		bReturnedIdle |= Phase == 6 && Elapsed >= 0.5 && ObserveState(TEXT("final_idle"), TEXT("Idle"), StateName, GroundedSince, StateGrace, Now);
		TSharedPtr<FJsonObject> Sample = MakeShared<FJsonObject>();
		Sample->SetNumberField(TEXT("time"), Now - StartedAt);
		Sample->SetNumberField(TEXT("phase"), Phase);
		Sample->SetNumberField(TEXT("height_cm"), Height);
		Sample->SetNumberField(TEXT("vertical_speed"), Movement->Velocity.Z);
		Sample->SetNumberField(TEXT("gravity"), Movement->GravityScale);
		Sample->SetBoolField(TEXT("grounded"), bGrounded);
		Sample->SetBoolField(TEXT("gliding"), bGliding);
		Sample->SetBoolField(TEXT("anim_gliding"), Anim && Anim->bRuntimeIsGliding);
		Sample->SetBoolField(TEXT("anim_in_air"), Anim->bRuntimeIsInAir);
		Sample->SetBoolField(TEXT("anim_rising"), Anim->bRuntimeIsRising);
		Sample->SetBoolField(TEXT("anim_descending"), Anim->bRuntimeIsDescending);
		Sample->SetStringField(TEXT("locomotion_state"), StateName.ToString());
		Sample->SetNumberField(TEXT("state_grace_seconds"), StateGrace);
		Sample->SetNumberField(TEXT("contact_grace_seconds"), ContactGrace);
		Sample->SetNumberField(TEXT("rising_eligible_seconds"), RisingSince >= 0.0 ? Now - RisingSince : -1.0);
		Sample->SetNumberField(TEXT("descending_eligible_seconds"), DescendingSince >= 0.0 ? Now - DescendingSince : -1.0);
		Sample->SetNumberField(TEXT("gliding_eligible_seconds"), GlidingSince >= 0.0 ? Now - GlidingSince : -1.0);
		Sample->SetNumberField(TEXT("grounded_eligible_seconds"), GroundedSince >= 0.0 ? Now - GroundedSince : -1.0);
		Sample->SetBoolField(TEXT("key_held"), bKeyHeld);
		Samples.Add(MakeShared<FJsonValueObject>(Sample));

		if (Now - StartedAt > 25.0 || Samples.Num() > 3000)
		{
			Test->AddError(TEXT("Live input test timed out; jump key released."));
			return Finish();
		}
		if (Phase == 0 && Elapsed >= 0.5 && bInitialIdle)
		{
			SetJumpHeld(true);
			Advance(1, Now);
		}
		else if (Phase == 1 || Phase == 2)
		{
			TapApex = FMath::Max(TapApex, Height);
			bTapLeftGround |= Movement->IsFalling();
			bTapGlided |= bGliding;
			if (Phase == 1 && Elapsed >= 0.06)
			{
				TapHoldSeconds = Elapsed;
				SetJumpHeld(false);
				Advance(2, Now);
			}
			else if (Phase == 2 && bTapLeftGround && Movement->IsMovingOnGround())
			{
				Advance(3, Now);
			}
			else if (Elapsed > 6.0)
			{
				Test->AddError(TEXT("Tap jump did not take off and land through the live input binding."));
				return Finish();
			}
		}
		else if (Phase == 3 && Elapsed >= 0.5)
		{
			SetJumpHeld(true);
			Advance(4, Now);
		}
		else if (Phase == 4)
		{
			HoldApex = FMath::Max(HoldApex, Height);
			bHoldGlided |= bGliding;
			bAnimGlided |= Anim && Anim->bRuntimeIsGliding;
			if (bGliding && FirstGlideAt < 0.0) { FirstGlideAt = Now; }
			if ((FirstGlideAt >= 0.0 && Now - FirstGlideAt >= 0.4) || Elapsed >= 4.0)
			{
				SetJumpHeld(false);
				Advance(5, Now);
			}
		}
		else if (Phase == 5)
		{
			if (Elapsed >= 0.2)
			{
				bReleaseStoppedGlide = !bGliding;
				bReleaseRestoredGravity = FMath::IsNearlyEqual(Movement->GravityScale, OriginalGravity, 0.01f);
			}
			if (Elapsed >= 0.2 && Movement->IsMovingOnGround())
			{
				Advance(6, Now);
			}
		}
		else if (Phase == 6)
		{
			// Retain the natural landing/settle interval; do not finish at first contact.
			if (Elapsed >= 0.5 && (bReturnedIdle || Elapsed >= 3.0))
			{
				Test->TestTrue(TEXT("Tap jump took off"), bTapLeftGround);
				Test->TestFalse(TEXT("Tap jump does not start glide"), bTapGlided);
				Test->TestTrue(TEXT("Held jump has a visibly higher apex"), HoldApex > TapApex + 10.0);
				Test->TestTrue(TEXT("Holding through apex starts glide"), bHoldGlided);
				Test->TestTrue(TEXT("Existing AnimInstance sees glide"), bAnimGlided);
				Test->TestTrue(TEXT("Release stops glide"), bReleaseStoppedGlide);
				Test->TestTrue(TEXT("Release restores gravity"), bReleaseRestoredGravity);
				Test->TestTrue(TEXT("Held jump returns to grounded movement"), Movement->IsMovingOnGround());
				Test->TestTrue(TEXT("Canonical locomotion starts in stable Idle"), bInitialIdle);
				Test->TestTrue(TEXT("Tap rising reaches JumpStart after transition allowance"), bTapJumpStart);
				Test->TestTrue(TEXT("Held rising reaches JumpStart after transition allowance"), bHoldJumpStart);
				Test->TestTrue(TEXT("Tap descending reaches Airborne after transition allowance"), bTapAirborne);
				Test->TestTrue(TEXT("Held glide reaches Glide after transition allowance"), bStateGlided);
				Test->TestTrue(TEXT("Tap ground contact reaches Land after transition allowance"), bTapLanded);
				Test->TestTrue(TEXT("Held ground contact reaches Land after transition allowance"), bHoldLanded);
				Test->TestTrue(TEXT("Landing returns to Idle within three seconds"), bReturnedIdle);
				bCompletedSequence = bInitialIdle && bTapJumpStart && bHoldJumpStart && bTapAirborne
					&& bStateGlided && bTapLanded && bHoldLanded && bReturnedIdle
					&& bTapLeftGround && !bTapGlided && HoldApex > TapApex + 10.0
					&& bHoldGlided && bAnimGlided && bReleaseStoppedGlide && bReleaseRestoredGravity;
				return Finish();
			}
		}
		return false;
	}

private:
	void UpdateEligibility(bool bEligible, double Now, double& Since)
	{
		if (!bEligible) { Since = -1.0; }
		else if (Since < 0.0) { Since = Now; }
	}
	bool ObserveState(const TCHAR* Gate, const TCHAR* Expected, FName StateName, double EligibleSince, double Grace, double Now)
	{
		if (EligibleSince < 0.0 || Now - EligibleSince < Grace || StateName != FName(Expected)) { return false; }
		if (!StateEvidence->HasField(Gate))
		{
			TSharedPtr<FJsonObject> Evidence = MakeShared<FJsonObject>();
			Evidence->SetStringField(TEXT("state"), StateName.ToString());
			Evidence->SetNumberField(TEXT("time"), Now - StartedAt);
			Evidence->SetNumberField(TEXT("eligible_since"), EligibleSince - StartedAt);
			Evidence->SetNumberField(TEXT("eligible_seconds"), Now - EligibleSince);
			Evidence->SetNumberField(TEXT("grace_seconds"), Grace);
			StateEvidence->SetObjectField(Gate, Evidence);
		}
		return true;
	}
	void Advance(int32 NextPhase, double Now) { Phase = NextPhase; PhaseStartedAt = Now; }
	void SetJumpHeld(bool bHeld)
	{
		if (Controller.IsValid() && bKeyHeld != bHeld)
		{
			Controller->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::SpaceBar, bHeld ? IE_Pressed : IE_Released, bHeld ? 1.0f : 0.0f));
		}
		bKeyHeld = bHeld;
	}
	bool Finish()
	{
		SetJumpHeld(false);
		TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
		Report->SetStringField(TEXT("proof"), TEXT("Live PIE simulated PlayerController key events; not physical keyboard or visual acceptance"));
		Report->SetBoolField(TEXT("completed_sequence"), bCompletedSequence);
		Report->SetNumberField(TEXT("tap_hold_seconds"), TapHoldSeconds);
		Report->SetNumberField(TEXT("tap_apex_cm"), TapApex);
		Report->SetNumberField(TEXT("hold_apex_cm"), HoldApex);
		Report->SetBoolField(TEXT("hold_glided"), bHoldGlided);
		Report->SetBoolField(TEXT("anim_glided"), bAnimGlided);
		Report->SetBoolField(TEXT("release_stopped_glide"), bReleaseStoppedGlide);
		Report->SetBoolField(TEXT("release_restored_gravity"), bReleaseRestoredGravity);
		Report->SetStringField(TEXT("state_machine"), TEXT("MelusinaLocomotion"));
		Report->SetBoolField(TEXT("initial_idle_observed"), bInitialIdle);
		Report->SetBoolField(TEXT("tap_jump_start_observed"), bTapJumpStart);
		Report->SetBoolField(TEXT("hold_jump_start_observed"), bHoldJumpStart);
		Report->SetBoolField(TEXT("tap_descending_airborne_observed"), bTapAirborne);
		Report->SetBoolField(TEXT("glide_state_observed"), bStateGlided);
		Report->SetBoolField(TEXT("tap_land_observed"), bTapLanded);
		Report->SetBoolField(TEXT("hold_land_observed"), bHoldLanded);
		Report->SetBoolField(TEXT("returned_idle_observed"), bReturnedIdle);
		Report->SetObjectField(TEXT("state_evidence"), StateEvidence);
		TArray<TSharedPtr<FJsonValue>> States;
		for (const FString& State : ObservedStates) { States.Add(MakeShared<FJsonValueString>(State)); }
		Report->SetArrayField(TEXT("observed_states"), States);
		Report->SetStringField(TEXT("running_jump_gate"), TEXT("SKIPPED: this stationary Space-input sequence does not exercise running jumps"));
		Report->SetStringField(TEXT("ledge_fall_gate"), TEXT("SKIPPED: descent is from input-driven jumps; no ledge fall is exercised"));
		Report->SetArrayField(TEXT("samples"), Samples);
		FString Json;
		FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
		const FString Directory = FPaths::ProjectSavedDir() / TEXT("Audit/MelusinaTraversalLiveInput");
		IFileManager::Get().MakeDirectory(*Directory, true);
		const FString Path = Directory / (FDateTime::UtcNow().ToString(TEXT("%Y%m%d_%H%M%S")) + TEXT(".json"));
		Test->TestTrue(TEXT("Live input evidence written"), FFileHelper::SaveStringToFile(Json, *Path));
		Test->AddInfo(FString::Printf(TEXT("Live input receipt: %s; tap %.1f cm, hold %.1f cm"), *Path, TapApex, HoldApex));
		return true;
	}

	FAutomationTestBase* Test;
	TWeakObjectPtr<ACharacter> Character;
	TWeakObjectPtr<APlayerController> Controller;
	TWeakObjectPtr<UMelodiaTraversalComponent> Traversal;
	double WallStartedAt;
	double StartedAt = 0.0, PhaseStartedAt = 0.0, StartZ = 0.0;
	float OriginalGravity = 0.0f;
	int32 Phase = -1;
	double TapApex = 0.0, HoldApex = 0.0, TapHoldSeconds = 0.0, FirstGlideAt = -1.0;
	bool bKeyHeld = false, bTapLeftGround = false, bTapGlided = false, bHoldGlided = false, bAnimGlided = false;
	bool bReleaseStoppedGlide = false, bReleaseRestoredGravity = false, bCompletedSequence = false;
	double RisingSince = -1.0, DescendingSince = -1.0, GlidingSince = -1.0, GroundedSince = -1.0;
	bool bInitialIdle = false, bTapJumpStart = false, bHoldJumpStart = false, bTapAirborne = false;
	bool bStateGlided = false, bTapLanded = false, bHoldLanded = false, bReturnedIdle = false;
	TArray<FString> ObservedStates;
	TSharedPtr<FJsonObject> StateEvidence = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> Samples;
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelusinaLiveJumpInputTest,
	"Melodia.LivePIE.Melusina.JumpInput",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelusinaLiveJumpInputTest::RunTest(const FString& Parameters)
{
	const UWorld* World = GEditor->GetEditorWorldContext().World();
	if (!World || World->GetOutermost()->GetName() != TEXT("/Game/Melodia/Levels/Opening/L_MelusinaMorning"))
	{
		AddError(TEXT("Open Morning before running this opt-in test; it never changes or saves the loaded level."));
		return false;
	}
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FMelusinaLiveJumpInputCommand(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}
#endif // WITH_EDITOR

#endif // WITH_DEV_AUTOMATION_TESTS
