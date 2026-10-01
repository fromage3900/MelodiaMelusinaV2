// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "AGSGraph.h"
#include "AGSGraphNode.h"
#include "AGSGraphEdge.h"

// You should place include statements to your module's private header files here.  You only need to
// add includes for headers that are used in most of your module's source files though.
#include "IAGSGraphEditor.h"

#define LOG_INFO(FMT, ...) UE_LOG(AGSGraphEditor, Display, (FMT), ##__VA_ARGS__)
#define LOG_WARNING(FMT, ...) UE_LOG(AGSGraphEditor, Warning, (FMT), ##__VA_ARGS__)
#define LOG_ERROR(FMT, ...) UE_LOG(AGSGraphEditor, Error, (FMT), ##__VA_ARGS__)
