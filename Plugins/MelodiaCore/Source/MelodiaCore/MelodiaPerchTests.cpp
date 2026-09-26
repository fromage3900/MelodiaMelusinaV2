// Perch behaviour tests for Sir Melodious (runbook H-4, decision D1).
//
// The test builds its own throwaway world instead of PIE so it can spawn a
// flight pawn and perches without touching the editor's open level, without a
// game mode, and without the party subsystem. That keeps the assertion surface
// on the perch contract itself: nearest-perch choice, landing transform,
// search radius, and takeoff.

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "MelodiousFlightCharacter.h"
#include "SirPerchPoint.h"

namespace
{
UWorld* CreatePerchTestWorld()
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName("MelodiaPerchTestWorld"));
	if (World)
	{
		FURL URL;
		World->InitializeActorsForPlay(URL);
		World->BeginPlay();
	}
	return World;
}

ASirPerchPoint* SpawnPerch(UWorld* World, const FVector& Location, const FRotator& Rotation,
	const FVector& LandingOffset, const FRotator& PerchFacing)
{
	ASirPerchPoint* Perch = World->SpawnActor<ASirPerchPoint>(Location, Rotation);
	if (Perch)
	{
		Perch->LandingOffset = LandingOffset;
		Perch->bFaceAlongPerch = true;
		Perch->PerchFacing = PerchFacing;
	}
	return Perch;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaSirPerchTest,
	"Melodia.FlightTests.SirPerchLandTakeoff",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaSirPerchTest::RunTest(const FString& Parameters)
{
	UWorld* World = CreatePerchTestWorld();
	if (!TestNotNull(TEXT("Perch test world was created"), World))
	{
		return false;
	}

	// Perch A sits behind and above the bird but is much the nearest landing
	// spot; Perch B is further away and has no offset. The test fails if the
	// search ever prefers raw actor distance to the true landing spot.
	ASirPerchPoint* PerchA = SpawnPerch(World, FVector(0.0, 0.0, 0.0), FRotator(0.0, 45.0, 0.0),
		FVector(0.0, 0.0, 120.0), FRotator(0.0, 90.0, 0.0));
	ASirPerchPoint* PerchB = SpawnPerch(World, FVector(500.0, 0.0, 0.0), FRotator::ZeroRotator,
		FVector::ZeroVector, FRotator::ZeroRotator);

	AMelodiousFlightCharacter* Sir = World->SpawnActor<AMelodiousFlightCharacter>(
		FVector(100.0, 0.0, 0.0), FRotator::ZeroRotator);

	if (!TestNotNull(TEXT("Perch A spawned"), PerchA)
		|| !TestNotNull(TEXT("Perch B spawned"), PerchB)
		|| !TestNotNull(TEXT("Sir spawned"), Sir))
	{
		World->DestroyWorld(false);
		return false;
	}

	// --- Landing transform contract -------------------------------------
	TestTrue(TEXT("Perch A landing spot is offset above its origin"),
		PerchA->GetLandingLocation().Equals(FVector(0.0, 0.0, 120.0), 0.1));
	TestTrue(TEXT("Perch facing adds to the actor rotation"),
		PerchA->GetLandingRotation().Equals(FRotator(0.0, 135.0, 0.0), 0.1));

	// --- Nearest-perch selection ----------------------------------------
	float ReportedDistance = -1.0f;
	ASirPerchPoint* Nearest = Sir->FindNearestPerch(ReportedDistance);
	TestEqual(TEXT("The offset perch wins over the closer actor pivot"), Nearest, PerchA);
	TestTrue(TEXT("Reported distance is the distance to the landing spot"),
		FMath::IsNearlyEqual(ReportedDistance, FVector(100.0, 0.0, 120.0).Size(), 0.5));

	// --- Landing ---------------------------------------------------------
	TestTrue(TEXT("Sir lands on the nearest perch"), Sir->TryLandOnNearestPerch());
	TestTrue(TEXT("Sir reports being perched"), Sir->bIsPerched);
	TestEqual(TEXT("Sir records which perch he is on"), Sir->CurrentPerch.Get(), PerchA);
	TestTrue(TEXT("Sir sits at the perch's landing spot"),
		Sir->GetActorLocation().Equals(PerchA->GetLandingLocation(), 0.1));
	TestTrue(TEXT("Sir faces the authored perch direction"),
		Sir->GetActorRotation().Equals(PerchA->GetLandingRotation(), 0.1));
	TestEqual(TEXT("A perched bird keeps flying movement (no gravity transition)"),
		Sir->GetCharacterMovement()->MovementMode, MOVE_Flying);
	TestTrue(TEXT("Landing zeroes the bird's velocity"),
		Sir->GetCharacterMovement()->Velocity.IsNearlyZero(1.0));

	// Landing again while already perched is a no-op that still reports success.
	TestTrue(TEXT("Re-landing while perched is idempotent"), Sir->TryLandOnNearestPerch());
	TestEqual(TEXT("Re-landing keeps the same perch"), Sir->CurrentPerch.Get(), PerchA);

	// --- Takeoff ---------------------------------------------------------
	Sir->LeavePerch();
	TestFalse(TEXT("Leaving the perch clears the perched flag"), Sir->bIsPerched);
	TestNull(TEXT("Leaving the perch clears the perch reference"), Sir->CurrentPerch.Get());

	// --- Search radius ---------------------------------------------------
	Sir->SetActorLocation(FVector(5000.0, 0.0, 0.0), false, nullptr, ETeleportType::TeleportPhysics);
	float FarDistance = -1.0f;
	TestNull(TEXT("No perch is chosen beyond the search radius"), Sir->FindNearestPerch(FarDistance));
	TestEqual(TEXT("Distance is reported as unset when nothing is in range"), FarDistance, -1.0f);
	TestFalse(TEXT("Landing fails with no perch in range"), Sir->TryLandOnNearestPerch());
	TestFalse(TEXT("A failed landing does not set the perched flag"), Sir->bIsPerched);

	World->DestroyWorld(false);
	return true;
}

#endif
