// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

class FPCGExIntTracker;
struct FPCGExCarryOverDetails;
class FPCGExPointIOMerger;

namespace PCGExMT
{
	class FTaskManager;
}

namespace PCGExData
{
	class FFacade;
	class FPointIO;
	class FPointIOCollection;
}

namespace PCGExGraphs
{
	/**
	 * Merges input edge groups by CONNECTIVITY: groups linked (via AddEdge, or through an appended
	 * bridge vtx) share one output edge collection; unlinked groups stay separate. Yields one output
	 * cluster per connected component, all sharing the single vtx, by patching the PCGEx endpoint
	 * attributes (Attr_PCGExVtxIdx / Attr_PCGExEdgeIdx) directly -- no GraphBuilder recompile.
	 *
	 * Two-phase, because the edge merge is async and components are only known once edges are staged:
	 *
	 *   FGraphPatcher Patcher(VtxFacade);                       // vtx must be writable (e.g. Duplicate)
	 *   for (Cluster) Patcher.AddEdgeGroup(Cluster.EdgesIO, Cluster.VtxPointIndices);
	 *   const int32 M = Patcher.AddVtx(T);                      // optional new vtx
	 *   Patcher.AddEdge(A, B);                                  // link two vtx (existing and/or new)
	 *   Patcher.ResolveAndMergeAsync(OutEdges, TaskManager, CarryOver);   // phase 1 (async)
	 *   ... let the merges finish (e.g. between a batch's CompleteWork and Write) ...
	 *   Patcher.Commit();                                       // phase 2: patch staged edges + grow vtx
	 *
	 * Both phases are single-threaded. New-vtx domain data beyond the transform is the caller's to
	 * fill after Commit, via the index returned by AddVtx.
	 */
	class PCGEXGRAPHS_API FGraphPatcher : public TSharedFromThis<FGraphPatcher>
	{
	public:
		explicit FGraphPatcher(const TSharedRef<PCGExData::FFacade>& InVtxFacade);

		/** Register an input edge group with the vtx point indices it owns. Returns the group index. */
		int32 AddEdgeGroup(const TSharedPtr<PCGExData::FPointIO>& InEdgesIO, const TArray<int32>& InVtxPointIndices);

		/** Stage a new vtx at InTransform; returns the index it will occupy in the shared vtx. */
		int32 AddVtx(const FTransform& InTransform);

		/** Stage an edge between two vtx point indices; returns a handle usable with GetEdgeOutput after Commit. */
		int32 AddEdge(const int32 VtxPointIndexA, const int32 VtxPointIndexB);

		/**
		 * Phase 1: emit one merged edge IO per connected component into OutEdges (async on TaskManager).
		 * InCarryOver must be valid and should carry the edge attributes, incl. Attr_PCGExEdgeIdx.
		 */
		void ResolveAndMergeAsync(
			const TSharedRef<PCGExData::FPointIOCollection>& OutEdges,
			const TSharedPtr<PCGExMT::FTaskManager>& InTaskManager,
			const FPCGExCarryOverDetails* InCarryOver);

		/** Phase 2 (after the async merges complete): append + patch staged edges, grow the shared vtx. */
		void Commit();

		/** The merged edge IOs, one per connected component (valid after ResolveAndMergeAsync). */
		const TArray<TSharedPtr<PCGExData::FPointIO>>& GetOutputEdges() const { return ComponentEdgeIOs; }

		/** Resolve a staged-edge handle to its output edge IO + point index (valid after Commit). */
		bool GetEdgeOutput(const int32 EdgeHandle, TSharedPtr<PCGExData::FPointIO>& OutEdgesIO, int32& OutEdgePointIndex) const;

	protected:
		TSharedPtr<FPCGExIntTracker> InternalTracker;
		TSharedRef<PCGExData::FFacade> VtxFacade;
		int32 NumInitialVtx = 0;

		struct FEdgeGroup
		{
			TSharedPtr<PCGExData::FPointIO> EdgesIO;
			TArray<int32> VtxPointIndices;
		};

		struct FPendingEdge
		{
			int32 A = -1;
			int32 B = -1;
			int32 ComponentIndex = -1; // filled during ResolveAndMergeAsync
			int32 EdgePointIndex = -1; // filled during Commit
		};

		TArray<FEdgeGroup> Groups;
		TArray<FTransform> NewVtxTransforms;
		TArray<FPendingEdge> PendingEdges;

		// Union-find over elements [0, Groups.Num()) = groups, [Groups.Num(), +NewVtx) = staged vtx.
		TArray<int32> DSU;
		int32 Find(const int32 X);
		void DSUUnion(const int32 A, const int32 B);
		int32 VtxElement(const int32 VtxPointIndex) const;

		TMap<int32, int32> VtxToElement; // vtx point index -> union-find element

		TArray<TSharedPtr<PCGExData::FPointIO>> ComponentEdgeIOs;
		TArray<TSharedPtr<PCGExData::FFacade>> ComponentEdgeFacades;
		TArray<TSharedPtr<FPCGExPointIOMerger>> Mergers;

		bool bResolved = false;
		bool bCommitted = false;
	};
}
