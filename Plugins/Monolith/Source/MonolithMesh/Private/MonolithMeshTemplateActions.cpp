#include "MonolithMeshTemplateActions.h"
#include "MonolithMeshBlockoutActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithAssetUtils.h"
#include "MonolithJsonUtils.h"

#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFileManager.h"
#include "Editor.h"
#include "EngineUtils.h"

// ============================================================================
// Helpers
// ============================================================================

FString FMonolithMeshTemplateActions::GetTemplatesDirectory()
{
	FString Dir = FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("Monolith") / TEXT("Templates");
	IFileManager::Get().MakeDirectory(*Dir, true);
	return Dir;
}

TSharedPtr<FJsonObject> FMonolithMeshTemplateActions::LoadTemplate(const FString& TemplateName, FString& OutError)
{
	FString TemplateDir = GetTemplatesDirectory();
	FString FilePath = TemplateDir / TemplateName + TEXT(".json");

	FString JsonStr;
	if (!FFileHelper::LoadFileToString(JsonStr, *FilePath))
	{
		OutError = FString::Printf(TEXT("Template file not found: %s"), *FilePath);
		return nullptr;
	}

	TSharedPtr<FJsonObject> JsonObj;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
	if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
	{
		OutError = FString::Printf(TEXT("Failed to parse template JSON: %s"), *FilePath);
		return nullptr;
	}

	return JsonObj;
}

bool FMonolithMeshTemplateActions::SaveTemplate(const FString& TemplateName, const TSharedPtr<FJsonObject>& TemplateJson, FString& OutError)
{
	FString TemplateDir = GetTemplatesDirectory();
	FString FilePath = TemplateDir / TemplateName + TEXT(".json");

	FString JsonStr;
	TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> Writer = TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&JsonStr);
	if (!FJsonSerializer::Serialize(TemplateJson.ToSharedRef(), Writer))
	{
		OutError = TEXT("Failed to serialize template JSON");
		return false;
	}

	if (!FFileHelper::SaveStringToFile(JsonStr, *FilePath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		OutError = FString::Printf(TEXT("Failed to write template file: %s"), *FilePath);
		return false;
	}

	return true;
}

bool FMonolithMeshTemplateActions::ParseJsonArrayToVector(const TArray<TSharedPtr<FJsonValue>>& Arr, FVector& Out)
{
	if (Arr.Num() < 3) return false;
	Out.X = Arr[0]->AsNumber();
	Out.Y = Arr[1]->AsNumber();
	Out.Z = Arr[2]->AsNumber();
	return true;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshTemplateActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. list_room_templates
	Registry.RegisterAction(TEXT("mesh"), TEXT("list_room_templates"),
		TEXT("List available room templates from the templates directory. Optionally filter by category."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::ListRoomTemplates),
		FParamSchemaBuilder()
			.Optional(TEXT("category"), TEXT("string"), TEXT("Filter templates by category (e.g. residential, commercial, medical)"))
			.Build());

	// 2. get_room_template
	Registry.RegisterAction(TEXT("mesh"), TEXT("get_room_template"),
		TEXT("Load the full JSON definition of a room template by name."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::GetRoomTemplate),
		FParamSchemaBuilder()
			.Required(TEXT("template_name"), TEXT("string"), TEXT("Name of the template (without .json extension)"))
			.Build());

	// 3. apply_room_template
	Registry.RegisterAction(TEXT("mesh"), TEXT("apply_room_template"),
		TEXT("Apply a room template to a blockout volume. Scales furniture positions to fit, creates blockout primitives. Single undo transaction."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::ApplyRoomTemplate),
		FParamSchemaBuilder()
			.Required(TEXT("volume_name"), TEXT("string"), TEXT("Name of the blockout volume"))
			.Required(TEXT("template_name"), TEXT("string"), TEXT("Name of the template to apply"))
			.Optional(TEXT("mirror"), TEXT("boolean"), TEXT("Mirror the layout along X axis"), TEXT("false"))
			.Optional(TEXT("rotate"), TEXT("integer"), TEXT("Rotate the layout by N degrees (0, 90, 180, 270)"), TEXT("0"))
			.Build());

	// 4. create_room_template
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_room_template"),
		TEXT("Save the current blockout layout of a volume as a reusable JSON template."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::CreateRoomTemplate),
		FParamSchemaBuilder()
			.Required(TEXT("volume_name"), TEXT("string"), TEXT("Volume whose layout to save"))
			.Required(TEXT("template_name"), TEXT("string"), TEXT("Name for the new template"))
			.Optional(TEXT("category"), TEXT("string"), TEXT("Template category"), TEXT("custom"))
			.Optional(TEXT("description"), TEXT("string"), TEXT("Human-readable description"))
			.Build());

	// --- Validation actions ---

	// 5. validate_game_ready
	Registry.RegisterAction(TEXT("mesh"), TEXT("validate_game_ready"),
		TEXT("Run a game-readiness checklist on a StaticMesh: collision, LODs, lightmap UV, degenerate geo, material count, pivot, scale. Returns pass/fail per check with severity."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::ValidateGameReady),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Asset path of the StaticMesh to validate"))
			.Build());

	// 6. suggest_lod_strategy
	Registry.RegisterAction(TEXT("mesh"), TEXT("suggest_lod_strategy"),
		TEXT("Suggest LOD strategy based on triangle count. Returns ready-to-execute params for generate_lods."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::SuggestLodStrategy),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Asset path of the StaticMesh"))
			.Build());

	// 7. batch_validate
	Registry.RegisterAction(TEXT("mesh"), TEXT("batch_validate"),
		TEXT("Batch validate meshes: fast SQL pre-filter from mesh_catalog, then deep asset-load on flagged assets. Sorted by severity."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::BatchValidate),
		FParamSchemaBuilder()
			.Optional(TEXT("class"), TEXT("string"), TEXT("Asset class to validate"), TEXT("StaticMesh"))
			.Optional(TEXT("path_filter"), TEXT("string"), TEXT("Path substring filter (e.g. '/Game/Environment/')"))
			.Optional(TEXT("severity_min"), TEXT("string"), TEXT("Minimum severity to report: CRITICAL, HIGH, MEDIUM, LOW"), TEXT("HIGH"))
			.Build());

	// 8. compare_lod_chain
	Registry.RegisterAction(TEXT("mesh"), TEXT("compare_lod_chain"),
		TEXT("Compare LOD chain quality: per-step reduction ratio, screen size gaps, section mismatches. Flags unhealthy transitions."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshTemplateActions::CompareLodChain),
		FParamSchemaBuilder()
			.RequiredAssetPath(TEXT("asset_path"), TEXT("Asset path of the StaticMesh"))
			.Build());
}

// ============================================================================
// 1. list_room_templates
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::ListRoomTemplates(const TSharedPtr<FJsonObject>& Params)
{
	FString CategoryFilter;
	Params->TryGetStringField(TEXT("category"), CategoryFilter);

	FString TemplateDir = GetTemplatesDirectory();

	TArray<FString> Files;
	IFileManager::Get().FindFiles(Files, *(TemplateDir / TEXT("*.json")), true, false);

	TArray<TSharedPtr<FJsonValue>> TemplatesArr;

	for (const FString& File : Files)
	{
		FString FilePath = TemplateDir / File;
		FString JsonStr;
		if (!FFileHelper::LoadFileToString(JsonStr, *FilePath))
		{
			continue;
		}

		TSharedPtr<FJsonObject> JsonObj;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
		if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
		{
			continue;
		}

		FString Category;
		JsonObj->TryGetStringField(TEXT("category"), Category);

		// Apply category filter if specified
		if (!CategoryFilter.IsEmpty() && !Category.Equals(CategoryFilter, ESearchCase::IgnoreCase))
		{
			continue;
		}

		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("name"), JsonObj->GetStringField(TEXT("name")));
		Entry->SetStringField(TEXT("category"), Category);

		FString Description;
		if (JsonObj->TryGetStringField(TEXT("description"), Description))
		{
			Entry->SetStringField(TEXT("description"), Description);
		}

		// Extract dimensions from recommended_size
		const TSharedPtr<FJsonObject>* SizeObj;
		if (JsonObj->TryGetObjectField(TEXT("recommended_size"), SizeObj))
		{
			Entry->SetObjectField(TEXT("recommended_size"), *SizeObj);
		}

		// Count furniture items
		const TArray<TSharedPtr<FJsonValue>>* FurnitureArr;
		if (JsonObj->TryGetArrayField(TEXT("furniture"), FurnitureArr))
		{
			Entry->SetNumberField(TEXT("furniture_count"), FurnitureArr->Num());
		}

		TemplatesArr.Add(MakeShared<FJsonValueObject>(Entry));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("templates"), TemplatesArr);
	Result->SetNumberField(TEXT("count"), TemplatesArr.Num());
	Result->SetStringField(TEXT("templates_directory"), TemplateDir);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. get_room_template
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::GetRoomTemplate(const TSharedPtr<FJsonObject>& Params)
{
	FString TemplateName;
	if (!Params->TryGetStringField(TEXT("template_name"), TemplateName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: template_name"));
	}

	FString Error;
	TSharedPtr<FJsonObject> TemplateJson = LoadTemplate(TemplateName, Error);
	if (!TemplateJson.IsValid())
	{
		return FMonolithActionResult::Error(Error);
	}

	return FMonolithActionResult::Success(TemplateJson);
}

// ============================================================================
// 3. apply_room_template
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::ApplyRoomTemplate(const TSharedPtr<FJsonObject>& Params)
{
	FString VolumeName;
	if (!Params->TryGetStringField(TEXT("volume_name"), VolumeName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: volume_name"));
	}

	FString TemplateName;
	if (!Params->TryGetStringField(TEXT("template_name"), TemplateName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: template_name"));
	}

	bool bMirror = false;
	Params->TryGetBoolField(TEXT("mirror"), bMirror);

	int32 RotateDeg = 0;
	{
		double RotateVal = 0;
		if (Params->TryGetNumberField(TEXT("rotate"), RotateVal))
		{
			RotateDeg = static_cast<int32>(RotateVal);
		}
	}

	// Load template
	FString Error;
	TSharedPtr<FJsonObject> TemplateJson = LoadTemplate(TemplateName, Error);
	if (!TemplateJson.IsValid())
	{
		return FMonolithActionResult::Error(Error);
	}

	// Find volume
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	AActor* Volume = nullptr;
	{
		FString FindError;
		Volume = MonolithMeshUtils::FindActorByName(VolumeName, FindError);
		if (!Volume)
		{
			return FMonolithActionResult::Error(FindError);
		}
	}

	FVector VolumeOrigin, VolumeExtent;
	Volume->GetActorBounds(false, VolumeOrigin, VolumeExtent);
	FVector VolumeMin = VolumeOrigin - VolumeExtent;
	FVector VolumeSize = VolumeExtent * 2.0;

	// Get furniture array from template
	const TArray<TSharedPtr<FJsonValue>>* FurnitureArr;
	if (!TemplateJson->TryGetArrayField(TEXT("furniture"), FurnitureArr) || FurnitureArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Template has no furniture entries"));
	}

	if (FurnitureArr->Num() > 200)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Template has %d furniture items (max 200)"), FurnitureArr->Num()));
	}

	// Build batch primitives array for create_blockout_primitives_batch pattern
	// Single undo transaction
	if (!GEditor)
	{
		return FMonolithActionResult::Error(TEXT("No editor available"));
	}
	GEditor->BeginTransaction(FText::FromString(TEXT("Monolith: Apply Room Template")));

	int32 Created = 0;
	TArray<TSharedPtr<FJsonValue>> CreatedArr;
	TArray<TSharedPtr<FJsonValue>> Warnings;

	// Rotation transform
	float RotRad = FMath::DegreesToRadians(static_cast<float>(RotateDeg));
	float CosR = FMath::Cos(RotRad);
	float SinR = FMath::Sin(RotRad);

	for (const auto& FurnitureVal : *FurnitureArr)
	{
		const TSharedPtr<FJsonObject>* FurnitureObjPtr;
		if (!FurnitureVal->TryGetObject(FurnitureObjPtr)) continue;
		const TSharedPtr<FJsonObject>& FurnitureObj = *FurnitureObjPtr;

		// Parse position_pct (0-1 normalized)
		FVector PositionPct;
		{
			const TArray<TSharedPtr<FJsonValue>>* PosArr;
			if (!FurnitureObj->TryGetArrayField(TEXT("position_pct"), PosArr) || !ParseJsonArrayToVector(*PosArr, PositionPct))
			{
				continue;
			}
		}

		// Parse size_range — pick midpoint
		FVector Size(100, 100, 100); // fallback
		{
			const TSharedPtr<FJsonObject>* SizeRangeObj;
			if (FurnitureObj->TryGetObjectField(TEXT("size_range"), SizeRangeObj))
			{
				FVector MinSize, MaxSize;
				const TArray<TSharedPtr<FJsonValue>>* MinArr;
				const TArray<TSharedPtr<FJsonValue>>* MaxArr;
				if ((*SizeRangeObj)->TryGetArrayField(TEXT("min"), MinArr) && ParseJsonArrayToVector(*MinArr, MinSize) &&
					(*SizeRangeObj)->TryGetArrayField(TEXT("max"), MaxArr) && ParseJsonArrayToVector(*MaxArr, MaxSize))
				{
					Size = (MinSize + MaxSize) * 0.5;

					// Clamp to volume dimensions
					Size.X = FMath::Min(Size.X, VolumeSize.X);
					Size.Y = FMath::Min(Size.Y, VolumeSize.Y);
					Size.Z = FMath::Min(Size.Z, VolumeSize.Z);
				}
			}
		}

		// Parse rotation
		FRotator FurnitureRotation(0, 0, 0);
		{
			const TArray<TSharedPtr<FJsonValue>>* RotArr;
			if (FurnitureObj->TryGetArrayField(TEXT("rotation"), RotArr) && RotArr->Num() >= 3)
			{
				FurnitureRotation.Pitch = (*RotArr)[0]->AsNumber();
				FurnitureRotation.Yaw = (*RotArr)[1]->AsNumber();
				FurnitureRotation.Roll = (*RotArr)[2]->AsNumber();
			}
		}

		// Apply mirror: flip X position
		if (bMirror)
		{
			PositionPct.X = 1.0 - PositionPct.X;
			FurnitureRotation.Yaw = -FurnitureRotation.Yaw;
		}

		// Apply rotation transform to position_pct (rotate around center 0.5, 0.5)
		if (RotateDeg != 0)
		{
			float CX = PositionPct.X - 0.5;
			float CY = PositionPct.Y - 0.5;
			float NewX = CX * CosR - CY * SinR + 0.5;
			float NewY = CX * SinR + CY * CosR + 0.5;
			PositionPct.X = NewX;
			PositionPct.Y = NewY;

			FurnitureRotation.Yaw += RotateDeg;

			// Also rotate size X/Y for 90/270 rotations
			if (RotateDeg == 90 || RotateDeg == 270 || RotateDeg == -90 || RotateDeg == -270)
			{
				Swap(Size.X, Size.Y);
			}
		}

		// Convert normalized position to world position
		FVector WorldPos = VolumeMin + FVector(
			PositionPct.X * VolumeSize.X,
			PositionPct.Y * VolumeSize.Y,
			PositionPct.Z * VolumeSize.Z
		);

		// Shape
		FString Shape = TEXT("box");
		FurnitureObj->TryGetStringField(TEXT("shape"), Shape);

		bool bValidShape = false;
		FString MeshPath;
		{
			FString Lower = Shape.ToLower();
			if (Lower == TEXT("box") || Lower == TEXT("cube"))   { MeshPath = TEXT("/Engine/BasicShapes/Cube.Cube"); bValidShape = true; }
			else if (Lower == TEXT("cylinder"))                   { MeshPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder"); bValidShape = true; }
			else if (Lower == TEXT("sphere"))                     { MeshPath = TEXT("/Engine/BasicShapes/Sphere.Sphere"); bValidShape = true; }
			else if (Lower == TEXT("cone"))                       { MeshPath = TEXT("/Engine/BasicShapes/Cone.Cone"); bValidShape = true; }
		}
		if (!bValidShape)
		{
			MeshPath = TEXT("/Engine/BasicShapes/Cube.Cube");
		}

		UStaticMesh* ShapeMesh = FMonolithAssetUtils::LoadAssetByPath<UStaticMesh>(MeshPath);
		if (!ShapeMesh) continue;

		// BasicShapes are 100cm, so scale = size / 100
		FVector PrimScale = Size / 100.0;

		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

		AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(WorldPos, FurnitureRotation, SpawnParams);
		if (!Actor) continue;

		Actor->GetStaticMeshComponent()->SetStaticMesh(ShapeMesh);
		Actor->SetActorScale3D(PrimScale);

		// Tags
		Actor->Tags.Add(FName(TEXT("Monolith.BlockoutPrimitive")));
		Actor->Tags.Add(FName(*FString::Printf(TEXT("Monolith.Owner:%s"), *VolumeName)));
		Actor->Tags.Add(FName(*FString::Printf(TEXT("Monolith.Shape:%s"), *Shape.ToLower())));

		FString Label;
		FurnitureObj->TryGetStringField(TEXT("label"), Label);
		if (!Label.IsEmpty())
		{
			Actor->Tags.Add(FName(*FString::Printf(TEXT("Monolith.Label:%s"), *Label)));
			Actor->SetActorLabel(Label);
		}

		FString Category;
		FurnitureObj->TryGetStringField(TEXT("category"), Category);
		if (!Category.IsEmpty())
		{
			Actor->Tags.Add(FName(*FString::Printf(TEXT("Monolith.Category:%s"), *Category)));
		}

		Actor->SetFolderPath(FName(*FString::Printf(TEXT("Blockout/%s"), *VolumeName)));

		// Report
		auto CreatedObj = MakeShared<FJsonObject>();
		CreatedObj->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
		CreatedObj->SetStringField(TEXT("label"), Label);
		CreatedObj->SetStringField(TEXT("shape"), Shape);
		TArray<TSharedPtr<FJsonValue>> LocArr;
		LocArr.Add(MakeShared<FJsonValueNumber>(WorldPos.X));
		LocArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Y));
		LocArr.Add(MakeShared<FJsonValueNumber>(WorldPos.Z));
		CreatedObj->SetArrayField(TEXT("location"), LocArr);
		TArray<TSharedPtr<FJsonValue>> SizeArr;
		SizeArr.Add(MakeShared<FJsonValueNumber>(Size.X));
		SizeArr.Add(MakeShared<FJsonValueNumber>(Size.Y));
		SizeArr.Add(MakeShared<FJsonValueNumber>(Size.Z));
		CreatedObj->SetArrayField(TEXT("size"), SizeArr);
		CreatedArr.Add(MakeShared<FJsonValueObject>(CreatedObj));

		Created++;
	}

	GEditor->EndTransaction();

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("template"), TemplateName);
	Result->SetStringField(TEXT("volume"), VolumeName);
	Result->SetNumberField(TEXT("created"), Created);
	Result->SetBoolField(TEXT("mirrored"), bMirror);
	Result->SetNumberField(TEXT("rotated"), RotateDeg);
	Result->SetArrayField(TEXT("primitives"), CreatedArr);
	if (Warnings.Num() > 0)
	{
		Result->SetArrayField(TEXT("warnings"), Warnings);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. create_room_template
// ============================================================================

FMonolithActionResult FMonolithMeshTemplateActions::CreateRoomTemplate(const TSharedPtr<FJsonObject>& Params)
{
	FString VolumeName;
	if (!Params->TryGetStringField(TEXT("volume_name"), VolumeName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: volume_name"));
	}

	FString TemplateName;
	if (!Params->TryGetStringField(TEXT("template_name"), TemplateName))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: template_name"));
	}

	FString Category = TEXT("custom");
	Params->TryGetStringField(TEXT("category"), Category);

	FString Description;
	Params->TryGetStringField(TEXT("description"), Description);

	// Find the volume
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString FindError;
	AActor* Volume = MonolithMeshUtils::FindActorByName(VolumeName, FindError);
	if (!Volume)
	{
		return FMonolithActionResult::Error(FindError);
	}

	FVector VolumeOrigin, VolumeExtent;
	Volume->GetActorBounds(false, VolumeOrigin, VolumeExtent);
	FVector VolumeMin = VolumeOrigin - VolumeExtent;
	FVector VolumeSize = VolumeExtent * 2.0;

	// Find all blockout primitives owned by this volume
	FString OwnerTag = FString::Printf(TEXT("Monolith.Owner:%s"), *VolumeName);

	TArray<TSharedPtr<FJsonValue>> FurnitureArr;

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (Actor == Volume) continue;

		// Check owner tag
		bool bOwned = false;
		for (const FName& Tag : Actor->Tags)
		{
			if (Tag.ToString().StartsWith(OwnerTag, ESearchCase::IgnoreCase))
			{
				bOwned = true;
				break;
			}
		}
		if (!bOwned) continue;

		// Check it's a blockout primitive
		bool bIsPrimitive = false;
		for (const FName& Tag : Actor->Tags)
		{
			if (Tag.ToString().StartsWith(TEXT("Monolith.BlockoutPrimitive"), ESearchCase::IgnoreCase))
			{
				bIsPrimitive = true;
				break;
			}
		}
		if (!bIsPrimitive) continue;

		FVector ActorLoc = Actor->GetActorLocation();
		FVector RelativePos = ActorLoc - VolumeMin;

		// Normalize to 0-1
		FVector NormalizedPos;
		NormalizedPos.X = VolumeSize.X > 0 ? RelativePos.X / VolumeSize.X : 0.0;
		NormalizedPos.Y = VolumeSize.Y > 0 ? RelativePos.Y / VolumeSize.Y : 0.0;
		NormalizedPos.Z = VolumeSize.Z > 0 ? RelativePos.Z / VolumeSize.Z : 0.0;

		// Get actual size from scale (BasicShapes are 100cm)
		FVector Scale = Actor->GetActorScale3D();
		UStaticMeshComponent* SMC = Actor->FindComponentByClass<UStaticMeshComponent>();
		FVector ActualSize = Scale * 100.0;
		if (SMC && SMC->GetStaticMesh())
		{
			FBoxSphereBounds MeshBounds = SMC->GetStaticMesh()->GetBounds();
			ActualSize = MeshBounds.BoxExtent * 2.0 * Scale;
		}

		// Build size_range as +-10% of actual size
		FVector MinSize = ActualSize * 0.9;
		FVector MaxSize = ActualSize * 1.1;

		// Extract tags
		FString Shape = TEXT("box");
		FString Label;
		FString ItemCategory;

		for (const FName& Tag : Actor->Tags)
		{
			FString TagStr = Tag.ToString();
			if (TagStr.StartsWith(TEXT("Monolith.Shape:"), ESearchCase::IgnoreCase))
			{
				int32 ColonIdx;
				if (TagStr.FindChar(TEXT(':'), ColonIdx))
				{
					Shape = TagStr.Mid(ColonIdx + 1);
				}
			}
			else if (TagStr.StartsWith(TEXT("Monolith.Label:"), ESearchCase::IgnoreCase))
			{
				int32 ColonIdx;
				if (TagStr.FindChar(TEXT(':'), ColonIdx))
				{
					Label = TagStr.Mid(ColonIdx + 1);
				}
			}
			else if (TagStr.StartsWith(TEXT("Monolith.Category:"), ESearchCase::IgnoreCase))
			{
				int32 ColonIdx;
				if (TagStr.FindChar(TEXT(':'), ColonIdx))
				{
					ItemCategory = TagStr.Mid(ColonIdx + 1);
				}
			}
		}

		auto FurnitureObj = MakeShared<FJsonObject>();
		FurnitureObj->SetStringField(TEXT("label"), Label.IsEmpty() ? Actor->GetActorNameOrLabel() : Label);
		FurnitureObj->SetStringField(TEXT("shape"), Shape);

		// size_range
		auto SizeRange = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> MinArr, MaxArr;
		MinArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinSize.X)));
		MinArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinSize.Y)));
		MinArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinSize.Z)));
		MaxArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxSize.X)));
		MaxArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxSize.Y)));
		MaxArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxSize.Z)));
		SizeRange->SetArrayField(TEXT("min"), MinArr);
		SizeRange->SetArrayField(TEXT("max"), MaxArr);
		FurnitureObj->SetObjectField(TEXT("size_range"), SizeRange);

		// position_pct
		TArray<TSharedPtr<FJsonValue>> PosArr;
		PosArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToFloat(NormalizedPos.X * 100.0f) / 100.0f));
		PosArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToFloat(NormalizedPos.Y * 100.0f) / 100.0f));
		PosArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToFloat(NormalizedPos.Z * 100.0f) / 100.0f));
		FurnitureObj->SetArrayField(TEXT("position_pct"), PosArr);

		// rotation
		FRotator ActorRot = Actor->GetActorRotation();
		TArray<TSharedPtr<FJsonValue>> RotArr;
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Pitch));
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Yaw));
		RotArr.Add(MakeShared<FJsonValueNumber>(ActorRot.Roll));
		FurnitureObj->SetArrayField(TEXT("rotation"), RotArr);

		if (!ItemCategory.IsEmpty())
		{
			FurnitureObj->SetStringField(TEXT("category"), ItemCategory);
		}

		FurnitureArr.Add(MakeShared<FJsonValueObject>(FurnitureObj));
	}

	if (FurnitureArr.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("No blockout primitives found owned by volume '%s'"), *VolumeName));
	}

	// Build template JSON
	auto TemplateJson = MakeShared<FJsonObject>();
	TemplateJson->SetStringField(TEXT("name"), TemplateName);
	TemplateJson->SetStringField(TEXT("category"), Category);
	if (!Description.IsEmpty())
	{
		TemplateJson->SetStringField(TEXT("description"), Description);
	}

	// recommended_size from volume
	auto RecommendedSize = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> MinBoundsArr, MaxBoundsArr;
	// Use 80% to 120% of current volume as recommended range
	FVector MinBounds = VolumeSize * 0.8;
	FVector MaxBounds = VolumeSize * 1.2;
	MinBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinBounds.X)));
	MinBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinBounds.Y)));
	MinBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MinBounds.Z)));
	MaxBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxBounds.X)));
	MaxBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxBounds.Y)));
	MaxBoundsArr.Add(MakeShared<FJsonValueNumber>(FMath::RoundToInt(MaxBounds.Z)));
	RecommendedSize->SetArrayField(TEXT("min"), MinBoundsArr);
	RecommendedSize->SetArrayField(TEXT("max"), MaxBoundsArr);
	TemplateJson->SetObjectField(TEXT("recommended_size"), RecommendedSize);

	TemplateJson->SetArrayField(TEXT("furniture"), FurnitureArr);

	// Save
	FString SaveError;
	if (!SaveTemplate(TemplateName, TemplateJson, SaveError))
	{
		return FMonolithActionResult::Error(SaveError);
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("template_name"), TemplateName);
	Result->SetStringField(TEXT("category"), Category);
	Result->SetNumberField(TEXT("furniture_count"), FurnitureArr.Num());
	Result->SetStringField(TEXT("file_path"), GetTemplatesDirectory() / TemplateName + TEXT(".json"));

	return FMonolithActionResult::Success(Result);
}
