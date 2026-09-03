// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "Details/PCGExInlineNumericWidgets.h"

// Thin aliases over PCGExInlineNumericWidgets::Make*Widget -- kept for backward compatibility.
// Use the namespaced helpers directly in new code.
#define PCGEX_VECTORINPUTBOX(_HANDLE) PCGExInlineNumericWidgets::MakeVectorWidget((_HANDLE).ToSharedRef())
#define PCGEX_ROTATORINPUTBOX(_HANDLE) PCGExInlineNumericWidgets::MakeRotatorWidget((_HANDLE).ToSharedRef())
