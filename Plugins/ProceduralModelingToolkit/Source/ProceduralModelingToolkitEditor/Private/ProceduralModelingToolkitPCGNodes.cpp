#include "ProceduralModelingToolkitPCGNodes.h"

#include "ProceduralModelingToolkitDynamicMeshPipeline.h"
#include "ProceduralModelingToolkitEditorModule.h"
#include "ProceduralModelingToolkitModifierStack.h"

#include "Engine/StaticMesh.h"
#include "PCGContext.h"
#include "PCGElement.h"
#include "PCGPin.h"
#include "UDynamicMesh.h"

namespace ProceduralModelingToolkit::PCG
{
	enum class EPCGToolkitOperation : uint8
	{
		GenerateOrnaments,
		ModifyMeshes,
		ProcessSplines,
		GenerateDynamicMesh,
		OutputStaticMesh
	};

	static TArray<FPCGPinProperties> DefaultInputPins()
	{
		return { FPCGPinProperties(PCGPinConstants::DefaultInputLabel, FPCGDataTypeIdentifier{EPCGDataType::Any}) };
	}

	static TArray<FPCGPinProperties> DefaultOutputPins()
	{
		return { FPCGPinProperties(PCGPinConstants::DefaultOutputLabel, FPCGDataTypeIdentifier{EPCGDataType::Any}) };
	}

	static void PassThrough(FPCGContext* Context)
	{
		if (Context)
		{
			Context->OutputData = Context->InputData;
		}
	}

	class FProceduralModelingToolkitPCGElement final : public IPCGElement
	{
	public:
		explicit FProceduralModelingToolkitPCGElement(EPCGToolkitOperation InOperation)
			: Operation(InOperation)
		{
		}

		virtual bool CanExecuteOnlyOnMainThread(FPCGContext* Context) const override
		{
			return Operation == EPCGToolkitOperation::ModifyMeshes || Operation == EPCGToolkitOperation::OutputStaticMesh || Operation == EPCGToolkitOperation::GenerateDynamicMesh;
		}

		virtual bool IsCacheable(const UPCGSettings* InSettings) const override
		{
			return Operation == EPCGToolkitOperation::GenerateOrnaments || Operation == EPCGToolkitOperation::ProcessSplines;
		}

	protected:
		virtual bool ExecuteInternal(FPCGContext* Context) const override
		{
			if (!Context)
			{
				return true;
			}

			switch (Operation)
			{
			case EPCGToolkitOperation::GenerateOrnaments:
				ExecuteGenerateOrnaments(Context);
				break;
			case EPCGToolkitOperation::ModifyMeshes:
				ExecuteModifyMeshes(Context);
				break;
			case EPCGToolkitOperation::ProcessSplines:
				ExecuteProcessSplines(Context);
				break;
			case EPCGToolkitOperation::GenerateDynamicMesh:
				ExecuteGenerateDynamicMesh(Context);
				break;
			case EPCGToolkitOperation::OutputStaticMesh:
				ExecuteOutputStaticMesh(Context);
				break;
			default:
				break;
			}

			PassThrough(Context);
			return true;
		}

	private:
		void ExecuteGenerateOrnaments(FPCGContext* Context) const
		{
			const UProceduralModelingToolkitPCGGenerateOrnamentsSettings* Settings = Context->GetInputSettings<UProceduralModelingToolkitPCGGenerateOrnamentsSettings>();
			if (!Settings)
			{
				return;
			}

			const TArray<FProceduralModelingToolkitSplinePath> Paths = Settings->bUseFiligree
				? UProceduralModelingToolkitOrnamentGenerator::GenerateFiligree(Settings->FiligreeSettings)
				: UProceduralModelingToolkitOrnamentGenerator::GenerateOrnament(Settings->OrnamentSettings);

			UE_LOG(LogProceduralModelingToolkit, Log, TEXT("PCG Generate Ornaments produced %d spline paths."), Paths.Num());
		}

		void ExecuteModifyMeshes(FPCGContext* Context) const
		{
			const UProceduralModelingToolkitPCGModifyMeshesSettings* Settings = Context->GetInputSettings<UProceduralModelingToolkitPCGModifyMeshesSettings>();
			if (!Settings || !Settings->SourceMesh)
			{
				UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("PCG Modify Meshes skipped: no SourceMesh assigned."));
				return;
			}

			const FProceduralModelingToolkitMeshPipelineResult Result =
				FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh(Settings->SourceMesh, Settings->ModifierStack);
			UE_LOG(LogProceduralModelingToolkit, Log, TEXT("PCG Modify Meshes result: success=%s output='%s' message='%s'"), Result.bSuccess ? TEXT("true") : TEXT("false"), *Result.OutputPath, *Result.Message);
		}

		void ExecuteProcessSplines(FPCGContext* Context) const
		{
			const UProceduralModelingToolkitPCGProcessSplinesSettings* Settings = Context->GetInputSettings<UProceduralModelingToolkitPCGProcessSplinesSettings>();
			if (!Settings)
			{
				return;
			}

			const TArray<FProceduralModelingToolkitSplinePath> Paths = UProceduralModelingToolkitOrnamentGenerator::GenerateOrnament(Settings->OrnamentSettings);
			int32 PointCount = 0;
			for (const FProceduralModelingToolkitSplinePath& Path : Paths)
			{
				PointCount += Path.Points.Num();
			}

			UE_LOG(LogProceduralModelingToolkit, Log, TEXT("PCG Process Splines prepared %d paths and %d points."), Paths.Num(), PointCount);
		}

		void ExecuteGenerateDynamicMesh(FPCGContext* Context) const
		{
			const UProceduralModelingToolkitPCGGenerateDynamicMeshSettings* Settings = Context->GetInputSettings<UProceduralModelingToolkitPCGGenerateDynamicMeshSettings>();
			if (!Settings || !Settings->bGeneratePreviewCube)
			{
				return;
			}

			UDynamicMesh* DynamicMesh = NewObject<UDynamicMesh>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
			DynamicMesh->ResetToCube();

			if (Settings->ModifierStack)
			{
				FProceduralModelingToolkitModifierExecutionContext ModifierContext;
				ModifierContext.SourceAssetPath = TEXT("PCG/GeneratedDynamicMesh");
				ModifierContext.OutputAssetPath = TEXT("PCG/GeneratedDynamicMesh");
				ModifierContext.StackVersion = Settings->ModifierStack->Version;
				Settings->ModifierStack->Execute(DynamicMesh, ModifierContext);
			}

			UE_LOG(LogProceduralModelingToolkit, Log, TEXT("PCG Generate Dynamic Mesh produced transient mesh with %d triangles."), DynamicMesh->GetTriangleCount());
		}

		void ExecuteOutputStaticMesh(FPCGContext* Context) const
		{
			const UProceduralModelingToolkitPCGOutputStaticMeshSettings* Settings = Context->GetInputSettings<UProceduralModelingToolkitPCGOutputStaticMeshSettings>();
			if (!Settings || !Settings->SourceMesh)
			{
				UE_LOG(LogProceduralModelingToolkit, Warning, TEXT("PCG Output Static Mesh skipped: no SourceMesh assigned."));
				return;
			}

			const FProceduralModelingToolkitMeshPipelineResult Result =
				FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh(Settings->SourceMesh, Settings->ModifierStack);
			UE_LOG(LogProceduralModelingToolkit, Log, TEXT("PCG Output Static Mesh result: success=%s output='%s' message='%s'"), Result.bSuccess ? TEXT("true") : TEXT("false"), *Result.OutputPath, *Result.Message);
		}

		EPCGToolkitOperation Operation;
	};
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGGenerateOrnamentsSettings::InputPinProperties() const
{
	return {};
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGGenerateOrnamentsSettings::OutputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultOutputPins();
}

#if WITH_EDITOR
FName UProceduralModelingToolkitPCGGenerateOrnamentsSettings::GetDefaultNodeName() const
{
	return TEXT("PMTGenerateOrnaments");
}

FText UProceduralModelingToolkitPCGGenerateOrnamentsSettings::GetDefaultNodeTitle() const
{
	return FText::FromString(TEXT("PMT Generate Ornaments"));
}

FText UProceduralModelingToolkitPCGGenerateOrnamentsSettings::GetNodeTooltipText() const
{
	return FText::FromString(TEXT("Generates deterministic procedural ornament or filigree spline paths through the Procedural Modeling Toolkit."));
}
#endif

FPCGElementPtr UProceduralModelingToolkitPCGGenerateOrnamentsSettings::CreateElement() const
{
	return MakeShared<ProceduralModelingToolkit::PCG::FProceduralModelingToolkitPCGElement>(ProceduralModelingToolkit::PCG::EPCGToolkitOperation::GenerateOrnaments);
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGModifyMeshesSettings::InputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultInputPins();
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGModifyMeshesSettings::OutputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultOutputPins();
}

#if WITH_EDITOR
FName UProceduralModelingToolkitPCGModifyMeshesSettings::GetDefaultNodeName() const
{
	return TEXT("PMTModifyMeshes");
}

FText UProceduralModelingToolkitPCGModifyMeshesSettings::GetDefaultNodeTitle() const
{
	return FText::FromString(TEXT("PMT Modify Meshes"));
}

FText UProceduralModelingToolkitPCGModifyMeshesSettings::GetNodeTooltipText() const
{
	return FText::FromString(TEXT("Applies a Procedural Modeling Toolkit modifier stack to an assigned Static Mesh asset."));
}
#endif

FPCGElementPtr UProceduralModelingToolkitPCGModifyMeshesSettings::CreateElement() const
{
	return MakeShared<ProceduralModelingToolkit::PCG::FProceduralModelingToolkitPCGElement>(ProceduralModelingToolkit::PCG::EPCGToolkitOperation::ModifyMeshes);
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGProcessSplinesSettings::InputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultInputPins();
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGProcessSplinesSettings::OutputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultOutputPins();
}

#if WITH_EDITOR
FName UProceduralModelingToolkitPCGProcessSplinesSettings::GetDefaultNodeName() const
{
	return TEXT("PMTProcessSplines");
}

FText UProceduralModelingToolkitPCGProcessSplinesSettings::GetDefaultNodeTitle() const
{
	return FText::FromString(TEXT("PMT Process Splines"));
}

FText UProceduralModelingToolkitPCGProcessSplinesSettings::GetNodeTooltipText() const
{
	return FText::FromString(TEXT("Processes deterministic procedural spline paths for downstream PCG graph use."));
}
#endif

FPCGElementPtr UProceduralModelingToolkitPCGProcessSplinesSettings::CreateElement() const
{
	return MakeShared<ProceduralModelingToolkit::PCG::FProceduralModelingToolkitPCGElement>(ProceduralModelingToolkit::PCG::EPCGToolkitOperation::ProcessSplines);
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::InputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultInputPins();
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::OutputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultOutputPins();
}

#if WITH_EDITOR
FName UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::GetDefaultNodeName() const
{
	return TEXT("PMTGenerateDynamicMesh");
}

FText UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::GetDefaultNodeTitle() const
{
	return FText::FromString(TEXT("PMT Generate Dynamic Mesh"));
}

FText UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::GetNodeTooltipText() const
{
	return FText::FromString(TEXT("Generates a transient Dynamic Mesh and optionally runs a Procedural Modeling Toolkit modifier stack."));
}
#endif

FPCGElementPtr UProceduralModelingToolkitPCGGenerateDynamicMeshSettings::CreateElement() const
{
	return MakeShared<ProceduralModelingToolkit::PCG::FProceduralModelingToolkitPCGElement>(ProceduralModelingToolkit::PCG::EPCGToolkitOperation::GenerateDynamicMesh);
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGOutputStaticMeshSettings::InputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultInputPins();
}

TArray<FPCGPinProperties> UProceduralModelingToolkitPCGOutputStaticMeshSettings::OutputPinProperties() const
{
	return ProceduralModelingToolkit::PCG::DefaultOutputPins();
}

#if WITH_EDITOR
FName UProceduralModelingToolkitPCGOutputStaticMeshSettings::GetDefaultNodeName() const
{
	return TEXT("PMTOutputStaticMesh");
}

FText UProceduralModelingToolkitPCGOutputStaticMeshSettings::GetDefaultNodeTitle() const
{
	return FText::FromString(TEXT("PMT Output Static Mesh"));
}

FText UProceduralModelingToolkitPCGOutputStaticMeshSettings::GetNodeTooltipText() const
{
	return FText::FromString(TEXT("Runs the Dynamic Mesh pipeline and saves the result as a new Static Mesh asset."));
}
#endif

FPCGElementPtr UProceduralModelingToolkitPCGOutputStaticMeshSettings::CreateElement() const
{
	return MakeShared<ProceduralModelingToolkit::PCG::FProceduralModelingToolkitPCGElement>(ProceduralModelingToolkit::PCG::EPCGToolkitOperation::OutputStaticMesh);
}
