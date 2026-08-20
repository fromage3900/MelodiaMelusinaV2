// Module entry point. UE requires exactly one IMPLEMENT_MODULE per module or the
// linker produces a module that loads but registers nothing.

#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, MelodiaNPR)
