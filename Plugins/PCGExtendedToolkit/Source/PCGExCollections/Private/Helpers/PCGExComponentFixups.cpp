// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Helpers/PCGExComponentFixups.h"

#include "PCGExVersion.h"
#include "Components/SplineComponent.h"
#include "Helpers/PCGExActorPropertyDelta.h"

namespace PCGExComponentFixups
{
	namespace
	{
		TArray<PCGExActorDelta::FPostApplyFixupHandle>& GetBuiltinHandles()
		{
			static TArray<PCGExActorDelta::FPostApplyFixupHandle> Instance;
			return Instance;
		}

		/**
		 * USplineComponent invariants that the per-property delta cannot express on its own.
		 *
		 * UE 5.7+ has two EditAnywhere spline properties that alias each other:
		 *   - `FSplineCurves SplineCurves` (legacy)
		 *   - `FSpline Spline` (new, experimental)
		 * `UE::SplineComponent::ShouldUseSplineCurves()` selects which one the runtime reads
		 * from for point queries. Authoring code keeps the two in sync, but the delta system
		 * serializes them independently: if the source only modified one side, only that side
		 * reaches the target, and the unchanged side reads back as archetype defaults. If the
		 * runtime then resolves against the unchanged side, the rendered spline looks reset
		 * to BP defaults.
		 *
		 * Strategy (5.7+): after the per-property delta is applied, diff each spline property
		 * against its archetype. If only one side diverged, call SetSpline() to rebuild the
		 * other from it (both overloads update both sides). If both agree or neither changed,
		 * leave them alone. If both changed but disagree, we can't pick a winner without
		 * losing data; leave as-is.
		 *
		 * In UE 5.6 the new `Spline` field is Transient + private and never appears in the
		 * delta; only SplineCurves is ever written, so no sync branch is needed -- only the
		 * reparam-table rebuild at the end.
		 *
		 * Always call UpdateSpline() to rebuild the transient reparam table -- it's
		 * CPF_Transient so the delta never includes it, and rendering/sampling depend on it.
		 */
		void FixupSplineComponent(UActorComponent* Component, UObject* Archetype)
		{
			USplineComponent* Spline = Cast<USplineComponent>(Component);
			if (!Spline)
			{
				return;
			}

#if PCGEX_ENGINE_VERSION > 506
			if (const USplineComponent* ArchSpline = Cast<USplineComponent>(Archetype))
			{
				PRAGMA_DISABLE_EXPERIMENTAL_WARNINGS

				// FSpline::operator== returns false for two "disabled" FSplines (no LegacyData
				// and no NewData) even when they are functionally equivalent -- the inner
				// if-branches both skip and the function falls through to `return false`.
				// Without this guard, two empty/disabled splines would be reported as
				// diverged and the fixup would try to rebuild SplineCurves from the empty
				// Spline via SetSpline(GetSpline()), wiping the archetype's SplineCurves data.
				const int32 CurSplinePts = Spline->GetSpline().GetNumberOfSegments();
				const int32 ArchSplinePts = ArchSpline->GetSpline().GetNumberOfSegments();
				const bool bBothSplinesEmpty = (CurSplinePts == 0 && ArchSplinePts == 0);


				const bool bSplineDiverged = !bBothSplinesEmpty
					&& Spline->GetSpline() != ArchSpline->GetSpline();
				const bool bCurvesDiverged = Spline->GetSplineCurves() != ArchSpline->GetSplineCurves();

				if (bCurvesDiverged && !bSplineDiverged)
				{
					// SplineCurves edited, Spline at default. SetSpline(FSplineCurves)
					// updates both sides from the curves. (Was SynchronizeSplines()
					// pre-5.8, which did exactly this internally; it's now a deprecated
					// no-op, so calling it would silently skip the sync.)
					Spline->SetSpline(Spline->GetSplineCurves());
				}
				else if (bSplineDiverged && !bCurvesDiverged)
				{
					// Spline edited, SplineCurves at default. SetSpline(FSpline) updates both
					// sides from the new spline.
					Spline->SetSpline(Spline->GetSpline());
				}

				PRAGMA_ENABLE_EXPERIMENTAL_WARNINGS
			}
#endif

			Spline->UpdateSpline();
		}
	}

	void RegisterBuiltins()
	{
		GetBuiltinHandles().Add(PCGExActorDelta::RegisterPostApplyFixup(
			USplineComponent::StaticClass(), &FixupSplineComponent));
	}

	void UnregisterBuiltins()
	{
		GetBuiltinHandles().Empty();
	}
}
