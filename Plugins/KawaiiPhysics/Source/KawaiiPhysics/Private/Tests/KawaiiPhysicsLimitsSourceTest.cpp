#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "AnimNode_KawaiiPhysics.h"
#include "KawaiiPhysicsLimitsDataAsset.h"

namespace
{
struct FInspectableKawaiiNode : FAnimNode_KawaiiPhysics
{
 using FAnimNode_KawaiiPhysics::ApplyLimitsDataAsset;
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKawaiiLimitsSourceTest,
 "KawaiiPhysics.Collision.DataAssetRefreshDoesNotAccumulate",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FKawaiiLimitsSourceTest::RunTest(const FString& Parameters)
{
 auto* Asset = NewObject<UKawaiiPhysicsLimitsDataAsset>();
 Asset->SphericalLimits.AddDefaulted(); Asset->CapsuleLimits.AddDefaulted();
 Asset->BoxLimits.AddDefaulted(); Asset->PlanarLimits.AddDefaulted();
 FInspectableKawaiiNode Node;
 Node.LimitsDataAsset = Asset;
 FSphericalLimit PhysicsLimit;
 PhysicsLimit.SourceType = ECollisionSourceType::PhysicsAsset;
 Node.SphericalLimitsData.Add(PhysicsLimit);
 const FBoneContainer Bones;
 for (int32 Frame = 0; Frame < 100; ++Frame) Node.ApplyLimitsDataAsset(Bones);
 TestEqual(TEXT("One asset sphere plus existing physics sphere"), Node.SphericalLimitsData.Num(), 2);
 TestEqual(TEXT("One asset capsule"), Node.CapsuleLimitsData.Num(), 1);
 TestEqual(TEXT("One asset box"), Node.BoxLimitsData.Num(), 1);
 TestEqual(TEXT("One asset plane"), Node.PlanarLimitsData.Num(), 1);
 TestTrue(TEXT("Runtime copy has the actual source"), Node.SphericalLimitsData.Last().SourceType == ECollisionSourceType::DataAsset);
 TestTrue(TEXT("Authored asset unchanged"), Asset->SphericalLimits[0].SourceType == ECollisionSourceType::AnimNode);
 Node.LimitsDataAsset = nullptr;
 Node.ApplyLimitsDataAsset(Bones);
 TestEqual(TEXT("Removing asset preserves physics source"), Node.SphericalLimitsData.Num(), 1);
 TestEqual(TEXT("Removing asset removes capsules"), Node.CapsuleLimitsData.Num(), 0);
 return true;
}
#endif
