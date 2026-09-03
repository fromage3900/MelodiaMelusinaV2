#include "ProceduralModelingToolkitKitbashGenerator.h"

#include "ProceduralModelingToolkitEditorModule.h"

#include "Math/RandomStream.h"

FProceduralModelingToolkitKitbashResult UProceduralModelingToolkitKitbashGenerator::GenerateKitbash(const FProceduralModelingToolkitKitbashSettings& Settings)
{
	FProceduralModelingToolkitKitbashResult Result;

	if (Settings.Parts.IsEmpty())
	{
		Result.Message = TEXT("Kitbash generation failed: no parts were provided.");
		return Result;
	}

	const FProceduralModelingToolkitKitbashPart* RootPart = FindPartById(Settings, Settings.RootPartId);
	if (!RootPart)
	{
		RootPart = &Settings.Parts[0];
	}

	FRandomStream RandomStream(Settings.Seed);

	FProceduralModelingToolkitKitbashPlacement RootPlacement;
	RootPlacement.PartId = RootPart->PartId;
	RootPlacement.Mesh = RootPart->Mesh;
	RootPlacement.Transform = FTransform::Identity;
	RootPlacement.Metadata = RootPart->Metadata;
	Result.Placements.Add(RootPlacement);

	for (int32 PlacementIndex = 0; PlacementIndex < Result.Placements.Num() && Result.Placements.Num() < FMath::Max(1, Settings.MaxParts); ++PlacementIndex)
	{
		const FProceduralModelingToolkitKitbashPlacement CurrentPlacement = Result.Placements[PlacementIndex];
		const FProceduralModelingToolkitKitbashPart* CurrentPart = FindPartById(Settings, CurrentPlacement.PartId);
		if (!CurrentPart)
		{
			continue;
		}

		for (const FProceduralModelingToolkitKitbashSocket& SourceSocket : CurrentPart->Sockets)
		{
			if (Result.Placements.Num() >= FMath::Max(1, Settings.MaxParts))
			{
				break;
			}

			for (const FProceduralModelingToolkitKitbashRule& Rule : Settings.Rules)
			{
				if (!Rule.FromSocketType.IsNone() && SourceSocket.Type != Rule.FromSocketType)
				{
					continue;
				}

				const int32 PlacementLimit = FMath::Max(1, Rule.MaxPlacements);
				for (int32 RulePlacementIndex = 0; RulePlacementIndex < PlacementLimit && Result.Placements.Num() < FMath::Max(1, Settings.MaxParts); ++RulePlacementIndex)
				{
					TArray<const FProceduralModelingToolkitKitbashPart*> Candidates;
					for (const FProceduralModelingToolkitKitbashPart& CandidatePart : Settings.Parts)
					{
						if (!PartMatchesRule(CandidatePart, Rule))
						{
							continue;
						}

						for (const FProceduralModelingToolkitKitbashSocket& CandidateSocket : CandidatePart.Sockets)
						{
							if ((Rule.ToSocketType.IsNone() || CandidateSocket.Type == Rule.ToSocketType) && AreSocketsCompatible(SourceSocket, CandidateSocket))
							{
								Candidates.Add(&CandidatePart);
								break;
							}
						}
					}

					const FProceduralModelingToolkitKitbashPart* SelectedPart = SelectWeightedPart(Candidates, RandomStream);
					if (!SelectedPart)
					{
						continue;
					}

					const FProceduralModelingToolkitKitbashSocket* TargetSocket = SelectedPart->Sockets.FindByPredicate([&Rule, &SourceSocket](const FProceduralModelingToolkitKitbashSocket& Socket)
					{
						return (Rule.ToSocketType.IsNone() || Socket.Type == Rule.ToSocketType) && AreSocketsCompatible(SourceSocket, Socket);
					});

					if (!TargetSocket)
					{
						continue;
					}

					const FTransform SourceWorldTransform = SourceSocket.LocalTransform * CurrentPlacement.Transform;
					FProceduralModelingToolkitKitbashPlacement NewPlacement;
					NewPlacement.PartId = SelectedPart->PartId;
					NewPlacement.Mesh = SelectedPart->Mesh;
					NewPlacement.Transform = MakePlacementTransform(SourceWorldTransform, *TargetSocket, Rule, RandomStream);
					NewPlacement.SourceSocket = SourceSocket.Name;
					NewPlacement.TargetSocket = TargetSocket->Name;
					NewPlacement.Metadata = SelectedPart->Metadata;
					Result.Placements.Add(NewPlacement);
				}
			}
		}
	}

	Result.bSuccess = !Result.Placements.IsEmpty();
	Result.Message = FString::Printf(TEXT("Generated %d kitbash placements."), Result.Placements.Num());
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("%s"), *Result.Message);
	return Result;
}

bool UProceduralModelingToolkitKitbashGenerator::AreSocketsCompatible(const FProceduralModelingToolkitKitbashSocket& SourceSocket, const FProceduralModelingToolkitKitbashSocket& CandidateSocket)
{
	return SourceSocket.Type == CandidateSocket.Type
		|| SourceSocket.CompatibleTypes.Contains(CandidateSocket.Type)
		|| CandidateSocket.CompatibleTypes.Contains(SourceSocket.Type);
}

const FProceduralModelingToolkitKitbashPart* UProceduralModelingToolkitKitbashGenerator::FindPartById(const FProceduralModelingToolkitKitbashSettings& Settings, FName PartId)
{
	return Settings.Parts.FindByPredicate([PartId](const FProceduralModelingToolkitKitbashPart& Part)
	{
		return Part.PartId == PartId;
	});
}

const FProceduralModelingToolkitKitbashPart* UProceduralModelingToolkitKitbashGenerator::SelectWeightedPart(const TArray<const FProceduralModelingToolkitKitbashPart*>& Candidates, FRandomStream& RandomStream)
{
	if (Candidates.IsEmpty())
	{
		return nullptr;
	}

	float TotalWeight = 0.0f;
	for (const FProceduralModelingToolkitKitbashPart* Candidate : Candidates)
	{
		TotalWeight += Candidate ? FMath::Max(0.0f, Candidate->Metadata.Weight) : 0.0f;
	}

	if (TotalWeight <= UE_SMALL_NUMBER)
	{
		return Candidates[RandomStream.RandRange(0, Candidates.Num() - 1)];
	}

	float Pick = RandomStream.FRandRange(0.0f, TotalWeight);
	for (const FProceduralModelingToolkitKitbashPart* Candidate : Candidates)
	{
		Pick -= Candidate ? FMath::Max(0.0f, Candidate->Metadata.Weight) : 0.0f;
		if (Pick <= 0.0f)
		{
			return Candidate;
		}
	}

	return Candidates.Last();
}

bool UProceduralModelingToolkitKitbashGenerator::PartMatchesRule(const FProceduralModelingToolkitKitbashPart& Part, const FProceduralModelingToolkitKitbashRule& Rule)
{
	if (Rule.RequiredStyle != EProceduralModelingToolkitArchitecturalStyle::Any
		&& Part.Metadata.Style != Rule.RequiredStyle
		&& Part.Metadata.Style != EProceduralModelingToolkitArchitecturalStyle::Any)
	{
		return false;
	}

	for (const FName& RequiredTag : Rule.RequiredTags)
	{
		if (!Part.Metadata.Tags.Contains(RequiredTag))
		{
			return false;
		}
	}

	return true;
}

FTransform UProceduralModelingToolkitKitbashGenerator::MakePlacementTransform(const FTransform& SourceWorldTransform, const FProceduralModelingToolkitKitbashSocket& TargetSocket, const FProceduralModelingToolkitKitbashRule& Rule, FRandomStream& RandomStream)
{
	FRotator Rotation = SourceWorldTransform.Rotator();
	switch (Rule.RotationRule)
	{
	case EProceduralModelingToolkitKitbashRotationRule::RandomYaw:
		Rotation.Yaw += RandomStream.FRandRange(0.0f, 360.0f);
		break;
	case EProceduralModelingToolkitKitbashRotationRule::FixedRotation:
		Rotation += Rule.FixedRotation;
		break;
	case EProceduralModelingToolkitKitbashRotationRule::RandomFull:
		Rotation += FRotator(RandomStream.FRandRange(-180.0f, 180.0f), RandomStream.FRandRange(0.0f, 360.0f), RandomStream.FRandRange(-180.0f, 180.0f));
		break;
	case EProceduralModelingToolkitKitbashRotationRule::SocketForward:
	default:
		break;
	}

	const float MinScale = FMath::Min(Rule.ScaleRange.X, Rule.ScaleRange.Y);
	const float MaxScale = FMath::Max(Rule.ScaleRange.X, Rule.ScaleRange.Y);
	const float Scale = RandomStream.FRandRange(FMath::Max(UE_SMALL_NUMBER, MinScale), FMath::Max(UE_SMALL_NUMBER, MaxScale));

	FTransform TargetSocketInverse = TargetSocket.LocalTransform.Inverse();
	FTransform DesiredSocketTransform(Rotation, SourceWorldTransform.GetLocation(), FVector(Scale));
	return TargetSocketInverse * DesiredSocketTransform;
}
