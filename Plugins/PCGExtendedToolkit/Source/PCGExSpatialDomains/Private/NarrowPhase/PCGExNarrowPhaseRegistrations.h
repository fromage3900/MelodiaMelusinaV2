// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

namespace PCGExSpatial::NarrowPhase
{
	/**
	 * Per-shape pair-test registration entry points. Each pair-test .cpp
	 * defines static pair-test functions and exposes a single Register*
	 * function that the module's StartupModule calls during init.
	 *
	 * Adding a new shape kind: add a Register* declaration here, implement
	 * it in a new .cpp file alongside the pair-test functions, call it from
	 * the module's StartupModule. Existing files unchanged.
	 */
	void RegisterOBBPairTests();
	void RegisterPolygonPairTests();
}
