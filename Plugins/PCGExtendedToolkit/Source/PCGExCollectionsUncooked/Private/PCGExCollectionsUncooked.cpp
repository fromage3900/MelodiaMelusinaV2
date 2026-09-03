// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Modules/ModuleManager.h"

// K2-node-only module: the Blueprint Action Database discovers the node classes by
// iterating loaded UK2Node subclasses, so no startup registration is required.
IMPLEMENT_MODULE(FDefaultModuleImpl, PCGExCollectionsUncooked)
