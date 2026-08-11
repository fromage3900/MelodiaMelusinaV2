// Copyright Benoit Pelletier 2026 All Rights Reserved.
//
// This software is available under different licenses depending on the source from which it was obtained:
// - The Fab EULA (https://fab.com/eula) applies when obtained from the Fab marketplace.
// - The CeCILL-C license (https://cecill.info/licences/Licence_CeCILL-C_V1-en.html) applies when obtained from any other source.
// Please refer to the accompanying LICENSE file for further details.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "DoorInterface.generated.h"

class UDoorType;
class URoomConnection;

UINTERFACE(MinimalAPI, Blueprintable, BlueprintType)
class UDoorInterface : public UInterface
{
	GENERATED_BODY()
};

/**
 * Interface to implement on any Actor or ActorComponent used as a Door in the dungeon.
 */
class PROCEDURALDUNGEON_API IDoorInterface
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = "Door Interface")
	const UDoorType* GetDoorType() const;

	UFUNCTION(BlueprintNativeEvent, Category = "Door Interface")
	void SetRoomConnection(URoomConnection* RoomConnection);
};
