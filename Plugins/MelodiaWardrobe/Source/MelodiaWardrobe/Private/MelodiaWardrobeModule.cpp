// MelodiaWardrobe module — startup / shutdown.
//
// This file exists because UE 5.8's IMPLEMENT_MODULE registers the module with
// the module manager through a global FModuleInitializerEntry constructed here.
// Without it the DLL loads but FindModule() returns null and the plugin fails
// with "module could not be initialized successfully after it was loaded",
// followed by a GC-purge access violation at shutdown.

#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, MelodiaWardrobe)