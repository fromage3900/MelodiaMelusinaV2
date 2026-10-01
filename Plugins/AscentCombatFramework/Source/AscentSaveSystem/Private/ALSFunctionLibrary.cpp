// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSFunctionLibrary.h"
#include "ALSLoadAndSaveComponent.h"
#include "ALSLoadAndSaveSubsystem.h"
#include "ALSSavableInterface.h"
#include "ALSSaveGameSettings.h"
#include "ALSSaveTypes.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture2D.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerState.h"
#include "HighResScreenshot.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "ImageUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "Serialization/BulkData.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"
#include "TextureResource.h"
#include <Engine/TextureRenderTarget2D.h>
#include <UnrealClient.h>
#include <Kismet/KismetRenderingLibrary.h>
#include <Engine/SceneCapture2D.h>
#include <Components/SceneCaptureComponent2D.h>

FString UALSFunctionLibrary::FromSecondsToTimeString(int32 TotalSeconds, bool bIncludeSeconds)
{
	const int32 Hours = (TotalSeconds / 3600);
	const int32 Minutes = (TotalSeconds - (Hours * 3600)) / 60;

	if (bIncludeSeconds) {
		const int32 Seconds = (TotalSeconds % 60);
		return FString::Printf(TEXT("%02d:%02d:%02d"), Hours, Minutes, Seconds);
	}
	return FString::Printf(TEXT("%02d:%02d"), Hours, Minutes);
}

FString UALSFunctionLibrary::ConstructScreenshotPath(const FString& fileName)
{
	return FPaths::ProjectSavedDir() + "SaveGames/" + fileName + ".png";
	// return FPaths::ProjectUserDir() + fileName + ".png";
}

bool UALSFunctionLibrary::TrySaveScreenshot(const FString& fileName, const int32 width /*= 640*/, const int32 height /*= 480*/)
{
	if (!GEngine || !GEngine->GameViewport) {
		return false;
	}

	if (auto* Viewport = GEngine->GameViewport->Viewport) {
		const FString screenshotPath = ConstructScreenshotPath(fileName);

		FHighResScreenshotConfig& screenshotConfig = GetHighResScreenshotConfig();
		screenshotConfig.SetHDRCapture(false);
		screenshotConfig.FilenameOverride = screenshotPath;

		GScreenshotResolutionX = width;
		GScreenshotResolutionY = height;

		// Viewport->TakeHighResScreenShot();
		return UALSFunctionLibrary::GenerateScreenshot(screenshotPath, width, height);
	}
	return false;
}

UTexture2D* UALSFunctionLibrary::GetScreenshotByName(const FString& fileName)
{
	UTexture2D* Texture{ nullptr };
	const FString path = ConstructScreenshotPath(fileName);
	TArray<uint8> RawFileData;
	if (GEngine && FFileHelper::LoadFileToArray(RawFileData, *path)) {
		IImageWrapperModule& imgWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName("ImageWrapper"));
		TSharedPtr<IImageWrapper> imgWrapper = imgWrapperModule.CreateImageWrapper(EImageFormat::PNG);
		if (imgWrapper.IsValid() && imgWrapper->SetCompressed(RawFileData.GetData(), RawFileData.Num())) {
			TArray64<uint8> UncompressedBGRA;
			if (imgWrapper->GetRaw(ERGBFormat::BGRA, 8, UncompressedBGRA)) {
				Texture = UTexture2D::CreateTransient(imgWrapper->GetWidth(), imgWrapper->GetHeight(), PF_B8G8R8A8);
				void* TextureData = Texture->GetPlatformData()->Mips[0].BulkData.Lock(LOCK_READ_WRITE);
				FMemory::Memcpy(TextureData, UncompressedBGRA.GetData(), UncompressedBGRA.Num());
				Texture->GetPlatformData()->Mips[0].BulkData.Unlock();
				Texture->UpdateResource();
			}
		}
	}
	return Texture;
}

bool UALSFunctionLibrary::ShouldSaveActor(AActor* actor)
{
	if (IsValid(actor)) {
		return (actor->GetClass()->ImplementsInterface(UALSSavableInterface::StaticClass()) && !IALSSavableInterface::Execute_ShouldBeIgnored(actor));
	}
	return false;
}

bool UALSFunctionLibrary::ShouldDestroyActorIfMissingInSave(const AActor* Actor)
{
	if (!IsValid(Actor)) {
		return false;
	}
	if (const UALSLoadAndSaveComponent* Comp = Actor->FindComponentByClass<UALSLoadAndSaveComponent>()) {
		return Comp->GetDestroyIfMissingInSave();
	}
	const UALSSaveGameSettings* Settings = GetDefault<UALSSaveGameSettings>();
	return Settings ? Settings->GetDestroyActorsMissingInSaveByDefault() : false;
}

bool UALSFunctionLibrary::IsNewGame(const UObject* WorldContextObject)
{
	return UGameplayStatics::GetGameInstance(WorldContextObject)->GetSubsystem<UALSLoadAndSaveSubsystem>()->GetLoadType() == ELoadType::EDontReload;
}

bool UALSFunctionLibrary::IsSpecialActor(const UObject* WorldContextObject, const AActor* actor)
{
	const APlayerController* pc = Cast<APlayerController>(actor);
	if (pc) {
		return true;
	}
	const APawn* pawn = Cast<APawn>(actor);
	if (pawn) {
		return pawn->IsPlayerControlled();
	}
	const AGameStateBase* gameState = Cast<AGameStateBase>(actor);
	if (gameState) {
		return true;
	}
	const APlayerState* playerState = Cast<APlayerState>(actor);
	if (playerState) {
		return true;
	}
	return false;
}

void UALSFunctionLibrary::ExecuteFunctionsOnSavableComponents(const AActor* actorOwner, const FName& functionName)
{
	TArray<UActorComponent*> Components = IALSSavableInterface::Execute_GetComponentsToSave(actorOwner);
	for (auto component : Components) {

		UFunction* func = component->FindFunction(functionName);
		if (func) {
			component->ProcessEvent(func, nullptr);
		}
	}
}

void UALSFunctionLibrary::ExecuteFunctionsOnSavableActor(AActor* actorOwner, const FName& functionName)
{
	IALSSavableInterface::Execute_OnLoaded(actorOwner);
	UALSFunctionLibrary::ExecuteFunctionsOnSavableComponents(actorOwner,
		functionName);
}

void UALSFunctionLibrary::DeserializeActor(AActor* Actor, const FALSActorData& Record)
{
	Actor->Tags = Record.Tags;

	Actor->SetActorHiddenInGame(Record.bHiddenInGame);

	UALSFunctionLibrary::DeserializeActorComponents(Actor, Record);

	FMemoryReader MemoryReader(Record.Data, true);
	FALSSaveGameArchive Archive(MemoryReader, false);
	Actor->Serialize(Archive);
}

void UALSFunctionLibrary::FullDeserializeActor(AActor* Actor, const FALSActorData& Record, bool bLoadTransform)
{
	DeserializeActor(Actor, Record);
	if (bLoadTransform) {
		// Only location/rotation are runtime state: scale is authored data (level
		// instance / Blueprint) and re-applying the saved world scale through a full
		// SetActorTransform deforms actors whose root is scaled != 1.
		Actor->SetActorLocationAndRotation(Record.Transform.GetLocation(), Record.Transform.GetRotation(), false, nullptr, ETeleportType::TeleportPhysics);
	}
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (UKismetSystemLibrary::DoesImplementInterface(Actor, UALSSavableInterface::StaticClass())) {
		ExecuteFunctionsOnSavableActor(Actor, saveSettings->GetOnComponentLoadedFunctionName());
	}
}

void UALSFunctionLibrary::DeserializeActorComponents(AActor* Actor, const FALSActorData& ActorRecord)
{
	TArray<UActorComponent*> Components = IALSSavableInterface::Execute_GetComponentsToSave(Actor);
	for (auto* Component : Components) {

		const FALSComponentData* Record = ActorRecord.GetComponentData(Component);

		if (!Record) {
			continue;
		}

		/*TO CHECK
		USceneComponent* Scene = Cast<USceneComponent>(Component);
		if (Scene && Scene->Mobility == EComponentMobility::Movable) {
			Scene->SetRelativeTransform(Record->Transform);
		}*/

		FMemoryReader MemoryReader(Record->Data, true);
		FALSSaveGameArchive Archive(MemoryReader, false);
		Component->Serialize(Archive);
	}
}

FALSActorData UALSFunctionLibrary::SerializeActor(AActor* actor)
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (UKismetSystemLibrary::DoesImplementInterface(actor, UALSSavableInterface::StaticClass())) {
		IALSSavableInterface::Execute_OnSaved(actor);
		UALSFunctionLibrary::ExecuteFunctionsOnSavableComponents(actor, saveSettings->GetOnComponentSavedFunctionName());
	}

	FALSActorData Record = { actor };

	Record.bHiddenInGame = actor->IsHidden();
	Record.Transform = actor->GetTransform();
	Record.Tags = actor->Tags;

	UALSFunctionLibrary::SerializeComponents(actor, Record);

	FMemoryWriter MemoryWriter(Record.Data, true);
	FALSSaveGameArchive Archive(MemoryWriter, false);
	actor->Serialize(Archive);

	return Record;
}

void UALSFunctionLibrary::SerializeComponents(const AActor* Actor, FALSActorData& ActorRecord)
{
	TArray<UActorComponent*> Components = IALSSavableInterface::Execute_GetComponentsToSave(Actor);
	for (auto* Component : Components) {
		FALSComponentData ComponentRecord;
		ComponentRecord.alsName = Component->GetFName();
		ComponentRecord.Class = Component->GetClass();
		const USceneComponent* Scene = Cast<USceneComponent>(Component);
		if (Scene && Scene->Mobility == EComponentMobility::Movable) {
			ComponentRecord.Transform = Scene->GetRelativeTransform();
		}
		FMemoryWriter MemoryWriter(ComponentRecord.Data, true);
		FALSSaveGameArchive Archive(MemoryWriter, false);
		Component->Serialize(Archive);
		ActorRecord.AddComponentData(ComponentRecord);
	}
}

bool UALSFunctionLibrary::GenerateScreenshot(const FString& FileName, int32 TargetWidth /* = 640*/, int32 TargetHeight /* = 480*/)
{
	if (!GEngine || !GEngine->GameViewport) {
		return false;
	}

	UWorld* World = GEngine->GameViewport->GetWorld();
	if (!World) {
		return false;
	}

	APlayerController* PlayerController = World->GetFirstPlayerController();
	if (!PlayerController || !PlayerController->GetPawn()) {
		UE_LOG(LogTemp, Error, TEXT("No valid PlayerController or Pawn found!"));
		return false;
	}

	// Get player camera transform
	FVector CameraLocation;
	FRotator CameraRotation;
	PlayerController->GetPlayerViewPoint(CameraLocation, CameraRotation);

	// Create SceneCapture2D
	ASceneCapture2D* SceneCapture = World->SpawnActor<ASceneCapture2D>();
	if (!SceneCapture || !SceneCapture->GetCaptureComponent2D()) {
		UE_LOG(LogTemp, Error, TEXT("Failed to create Scene Capture 2D!"));
		return false;
	}

	// Attach SceneCapture to the player's camera location
	SceneCapture->SetActorLocation(CameraLocation);
	SceneCapture->SetActorRotation(CameraRotation);

	USceneCaptureComponent2D* CaptureComponent = SceneCapture->GetCaptureComponent2D();
	CaptureComponent->CaptureSource = SCS_FinalColorLDR;
	CaptureComponent->FOVAngle = 90.0f; // Match player's FOV

	// Create and assign render target
	UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>();
	RenderTarget->InitAutoFormat(TargetWidth, TargetHeight);
	RenderTarget->UpdateResourceImmediate(true);

	CaptureComponent->TextureTarget = RenderTarget;
	CaptureComponent->CaptureScene();

	// Wait for the render to complete
	FPlatformProcess::Sleep(0.1f);

	TArray<FColor> Bitmap;
	FTextureRenderTargetResource* RenderResource = RenderTarget->GameThread_GetRenderTargetResource();
	RenderResource->ReadPixels(Bitmap);

	SceneCapture->Destroy();

	if (Bitmap.Num() == 0) {
		UE_LOG(LogTemp, Error, TEXT("Render Target read failed!"));
		return false;
	}

	TArray64<uint8> CompressedBitmap;
	FImageUtils::PNGCompressImageArray(TargetWidth, TargetHeight, Bitmap, CompressedBitmap);
	if (CompressedBitmap.Num() == 0) {
		UE_LOG(LogTemp, Error, TEXT("PNGCompressImageArray failed!"));
		return false;
	}

	if (FFileHelper::SaveArrayToFile(CompressedBitmap, *FileName)) {
		UE_LOG(LogTemp, Warning, TEXT("Screenshot saved successfully: %s"), *FileName);
		return true;
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Failed to save the screenshot!"));
	}

	return false;
}

