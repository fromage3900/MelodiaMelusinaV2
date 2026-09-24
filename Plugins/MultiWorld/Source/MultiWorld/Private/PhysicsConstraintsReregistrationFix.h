// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class AActor;
class UPhysicsConstraintComponent;



/**
Fix broken UPhysicsConstraintComponent instances when they must be re-registered.

UPhysicsConstraintComponent brokes when it's un-registered (see https://github.com/EpicGames/UnrealEngine/blob/f8f4b403eb682ffc055613c7caf9d2ba5df7f319/Engine/Source/Runtime/Engine/Private/PhysicsEngine/PhysicsConstraintComponent.cpp#L326).

This could happens, for example, when calling Rename() on their owning actor. That's exactly what
UMultiWorldManager::TransferActorToWorld() does: it calls Rename() to transfer an actor to another UWorld,
this in turn causes the un-registering and re-registering of all involved components.

@note This object must be used on the stack and a "scoped" functional object, as it stores
"raw" pointers to involved UObjects (including components).
*/
class FScopePhysicsConstraintsReregistrationFix
{
public:
	/**
	This object must be constructed *before* starting the re-registration of components owned by Actor.

	@param Actor The actor on which the components will be re-registrated.
	@param ActorReferences Optional additional objects, referenced by Actor, for which we want to check and fix UPhysicsConstraintComponent instances.
	*/
	FScopePhysicsConstraintsReregistrationFix(AActor * Actor, const TArray<UObject *> & ActorReferences);

	/// Call this method after having re-registered the involved objects.
	~FScopePhysicsConstraintsReregistrationFix();

private:
	/**
	List of actors that could contains Physics Components to restore.

	@note We store "raw" pointers for efficiency, as this class must be used as a "scoped"
	functional object and no calls to UE5 GC are expected during its usage.
	*/
	TArray<AActor *> Actors;
};
