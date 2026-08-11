// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#ifndef PCGEX_DATA_MACROS
#define PCGEX_DATA_MACROS


#define PCGEX_INIT_IO_VOID(_IO, _INIT) if (!_IO->InitializeOutput(_INIT)) { return; }
#define PCGEX_INIT_IO(_IO, _INIT) if (!_IO->InitializeOutput(_INIT)) { return false; }

#define PCGEX_CLEAR_IO_VOID(_IO) if (!_IO->InitializeOutput(PCGExData::EIOInit::NoInit)) { return; } _IO->Disable();
#define PCGEX_CLEAR_IO(_IO) if (!_IO->InitializeOutput(PCGExData::EIOInit::NoInit)) { return false; } _IO->Disable();


#define PCGEX_SV_VIEW(_SOURCE) \
	TArray<decltype(_SOURCE->Read(0))> _SOURCE##ScopedArray; \
	if (_SOURCE) { _SOURCE##ScopedArray.SetNumUninitialized(Scope.Count); _SOURCE->ReadScope(Scope.Start, _SOURCE##ScopedArray); }

#define PCGEX_SV_VIEW_COND(_SOURCE, _COND) \
	TArray<decltype(_SOURCE->Read(0))> _SOURCE##ScopedArray; \
	if (_SOURCE && (_COND)) { _SOURCE##ScopedArray.SetNumUninitialized(Scope.Count); _SOURCE->ReadScope(Scope.Start, _SOURCE##ScopedArray); }

#define PCGEX_SV_READ(_SOURCE, _INDEX) _SOURCE##ScopedArray[_INDEX]


#endif
