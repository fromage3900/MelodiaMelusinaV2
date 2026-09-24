// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "PhysicsConstraintsReregistrationFix.h"

#include <PhysicsEngine/PhysicsConstraintComponent.h>

#include "GameFramework/Actor.h" // for TInlineComponentArray
#include <Misc/EngineVersionComparison.h>



FScopePhysicsConstraintsReregistrationFix::FScopePhysicsConstraintsReregistrationFix(
	AActor * Actor,
	const TArray<UObject *> & ActorReferences
)
{
	Actors.Reset(ActorReferences.Num() + 1);
	Actors.Emplace(Actor);
	
	// Analyze any other referenced actor.
	for (UObject * Obj: ActorReferences)
	{
		if (AActor * RefActor = Cast<AActor>(Obj))
		{
			// NOTE: it can be equals for Pawns
			if (RefActor != Actor)
			{
				Actors.Emplace(RefActor);
			}
		}
	}
}




FScopePhysicsConstraintsReregistrationFix::~FScopePhysicsConstraintsReregistrationFix()
{
	for (AActor * Actor: Actors)
	{
		TInlineComponentArray<UPhysicsConstraintComponent *> PhysicsComponents;
		Actor->GetComponents<UPhysicsConstraintComponent>(PhysicsComponents, /*bIncludeFromChildActors=*/false);

		for (UPhysicsConstraintComponent * C: PhysicsComponents)
		{
			static_assert(UE_VERSION_OLDER_THAN(5, 9, 0), "Verify if the fix is still needed, and if we can re-introduce working checkf() calls to identify the bug.");
			// Checks commented because they fire but the fix is still needed (see bug #1643).
			// 
			// To repro: project MWTest, open level "/Game/Samples/HelloWorld/HelloMultiWorld_1", PIE, set a World name for "HelloMultiWorld_2", press "Load World", press "Transfer Actor", checks fail.
			// 
			// When renaming actors, the OnRegister of the physics constraint could be called before the OnRegister of the primitive component
			// and in this case the physics constraint will be initialized in a wrong way. This dependens of the actor's hierarchy:
			//
			// - this hierarchy fails: Root <- PrimitiveComponent0 <- PhysicsConstraint <- PrimitiveComponent1
			// - this hierarchy works: Root <- PrimitiveComponent0 <- PrimitiveComponent1 <- PhysicsConstraint
			// 
			// See bug #1643 for more details.
			//checkf(!C->ConstraintInstance.IsValidConstraintInstance(), TEXT("If this fails [1], maybe the fix is no more needed."));
			//checkf(C->ConstraintInstance.IsTerminated(), TEXT("If this fails [2], maybe the fix is no more needed."));

			// InitComponentConstraint() uses the current rigid bodies transforms as reference frames,
			// but as they could be moving while simulating, they could not match anymore the correct setting.
			// We save the correct reference frames before restoring the constraint, to set them later.
			const FTransform RefFrame1 = C->ConstraintInstance.GetRefFrame(EConstraintFrame::Frame1);
			const FTransform RefFrame2 = C->ConstraintInstance.GetRefFrame(EConstraintFrame::Frame2);

			C->InitComponentConstraint();

			C->ConstraintInstance.SetRefFrame(EConstraintFrame::Frame1, RefFrame1);
			C->ConstraintInstance.SetRefFrame(EConstraintFrame::Frame2, RefFrame2);

			check(C->ConstraintInstance.IsValidConstraintInstance());
			check(!C->ConstraintInstance.IsTerminated());
		}
	}
}
