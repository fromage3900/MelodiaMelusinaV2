// SPDX-License-Identifier: MIT
//
// RIPathUtils — single definition of the shared project-relative path resolver.
// See RIPathUtils.h for the rationale (unity-build C2084 consolidation). The
// body is a verbatim lift of the formerly-duplicated anonymous-namespace helper;
// no behaviour change.

#include "Shared/RIPathUtils.h"

#include "Misc/Paths.h"

FString RIToProjectRelative(const FString& AbsPath, const FString& ProjectRoot)
{
	FString Full = FPaths::ConvertRelativePathToFull(AbsPath);
	FString RootFull = FPaths::ConvertRelativePathToFull(ProjectRoot);
	Full.ReplaceInline(TEXT("\\"), TEXT("/"));
	RootFull.ReplaceInline(TEXT("\\"), TEXT("/"));
	if (Full.StartsWith(RootFull, ESearchCase::IgnoreCase))
	{
		FString Rel = Full.Mid(RootFull.Len());
		while (!Rel.IsEmpty() && Rel[0] == TEXT('/')) { Rel.RightChopInline(1); }
		return Rel;
	}
	// Not under project root (engine-plugin scan) — return forward-slashed
	// absolute. Cppreflect/risk queries that ship in v0.17.0 still match cleanly.
	return Full;
}
