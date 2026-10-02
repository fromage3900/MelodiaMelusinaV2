#pragma once

// #include "CoreUObject.h"
// #include "Engine.h"

#include "IAGSGraphRuntime.h"

#define LOG_INFO(FMT, ...) UE_LOG(AGSGraphRuntime, Display, (FMT), ##__VA_ARGS__)
#define LOG_WARNING(FMT, ...) UE_LOG(AGSGraphRuntime, Warning, (FMT), ##__VA_ARGS__)
#define LOG_ERROR(FMT, ...) UE_LOG(AGSGraphRuntime, Error, (FMT), ##__VA_ARGS__)
