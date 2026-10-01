// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "AMSTypes.h"
#include "AMSMarkerWidget.h"

bool FAMSMarker::ValidCheck() const
{
	return IsValid(markerComp) && IsValid(markerWidget);
}