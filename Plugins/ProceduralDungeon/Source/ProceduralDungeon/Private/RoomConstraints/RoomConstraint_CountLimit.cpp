// Copyright Benoit Pelletier 2026 All Rights Reserved.
//
// This software is available under different licenses depending on the source from which it was obtained:
// - The Fab EULA (https://fab.com/eula) applies when obtained from the Fab marketplace.
// - The CeCILL-C license (https://cecill.info/licences/Licence_CeCILL-C_V1-en.html) applies when obtained from any other source.
// Please refer to the accompanying LICENSE file for further details.

#include "RoomConstraints/RoomConstraint_CountLimit.h"
#include "ProceduralDungeonLog.h"
#include "ProceduralDungeonTypes.h"
#include "RoomData.h"
#include "DungeonGraph.h"

bool URoomConstraint_CountLimit::Check_Implementation(const UDungeonGraph* Dungeon, const URoomData* RoomData, FIntVector Location, EDoorDirection Direction) const
{
	if (!IsValid(RoomData))
	{
		DungeonLog_Error("Invalid RoomData passed to %s", *GetNameSafe(this));
		return false;
	}

	if (!IsValid(Dungeon))
	{
		DungeonLog_Error("Invalid Dungeon passed to %s", *GetNameSafe(this));
		return false;
	}

	const int32 ActualCount = Dungeon->CountRoomData(RoomData);
	return ActualCount < MaxCount;
}
