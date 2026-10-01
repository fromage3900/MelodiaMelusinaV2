// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBuildingManagerComponent.h"

#include "ACFBuildableEntityComponent.h"
#include "ACFBuildableInterface.h"
#include "ACFBuildingSnapComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/AssetManager.h"
#include "Engine/NetSerialization.h"
#include "GameFramework/Character.h"
#include "Items/ACFItem.h"
#include "Net/UnrealNetwork.h"
#include <Engine/AssetManager.h>
#include <Engine/LocalPlayer.h>
#include <Engine/StreamableManager.h>
#include <Engine/World.h>
#include <EnhancedInputSubsystems.h>
#include <Logging.h>
#include <UObject/SoftObjectPath.h>



UACFBuildingManagerComponent::UACFBuildingManagerComponent()
{
	SetIsReplicatedByDefault(true);
	PrimaryComponentTick.bCanEverTick = true;
	SetComponentTickEnabled(true);
	RecipesIds.OwnerComponent = this;
}


void UACFBuildingManagerComponent::StartBuild(UACFBuildRecipe* Recipe)
{
	const APlayerController* Controller = GetPlayerController();
	if (!IsValid(Controller)) {
		return;
	}

	if (!Recipe || Recipe->ItemType.IsNull()) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("StartBuild failed: Recipe or ItemType is invalid"));
		return;
	}

	bFirstCheck = true;
	bLastPlacementValid = false;
	CurrentRecipe = Recipe;

	// Check if class is loaded
	if (UClass* LoadedClass = Recipe->ItemType.Get()) {
		SpawnPreviewActor(LoadedClass, Controller);
	}
	else {
		UE_LOG(LogAscentBuildingSystem, Log, TEXT("Loading actor class async: %s"), *Recipe->ItemType.ToSoftObjectPath().ToString());

		UAssetManager& AssetManager = UAssetManager::Get();
		FStreamableManager& StreamableManager = AssetManager.GetStreamableManager();

		FSoftObjectPath SoftPath = Recipe->ItemType.ToSoftObjectPath();

		TSharedPtr<FStreamableHandle> LoadingHandle = StreamableManager.RequestAsyncLoad(
			SoftPath,
			FStreamableDelegate::CreateUObject(this, &UACFBuildingManagerComponent::OnActorClassLoaded, Controller));

		if (!LoadingHandle.IsValid()) {
			UE_LOG(LogAscentBuildingSystem, Error, TEXT("Failed to start async loading for: %s"), *SoftPath.ToString());
		}
	}
}

void UACFBuildingManagerComponent::OnActorClassLoaded(const APlayerController* Controller)
{
	if (!IsValid(Controller) || !CurrentRecipe) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("OnActorClassLoaded: Invalid Controller or Recipe"));
		return;
	}

	UClass* LoadedClass = CurrentRecipe->ItemType.Get();
	if (!LoadedClass) {
		UE_LOG(LogAscentBuildingSystem, Error, TEXT("OnActorClassLoaded: Failed to load class %s"),
			*CurrentRecipe->ItemType.ToSoftObjectPath().ToString());
		return;
	}

	SpawnPreviewActor(LoadedClass, Controller);
}

void UACFBuildingManagerComponent::SpawnPreviewActor(UClass* ActorClass, const APlayerController* Controller)
{
	const FVector Location = GetLocation(Controller, { Controller->GetPawn() });
	FTransform Transform = FTransform(Location);

	AActor* NewBuild = GetWorld()->SpawnActor(ActorClass, &Transform);
	if (!IsValid(NewBuild)) {
		UE_LOG(LogAscentBuildingSystem, Error, TEXT("Failed to spawn preview actor of class: %s"), *GetNameSafe(ActorClass));
		return;
	}

	CurrentObject = NewBuild;

	if (!CurrentObject) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Build failed: CurrentObject is invalid"));
		return;
	}

	NewBuild->ForEachComponent<UMeshComponent>(false, [&](UMeshComponent* MeshComponent) {
		MeshComponent->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		MeshComponent->SetCollisionObjectType(ECollisionChannel::ECC_WorldDynamic);
		MeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Overlap);
		MeshComponent->SetCollisionResponseToChannel(ECollisionChannel::ECC_Pawn, ECollisionResponse::ECR_Overlap);
		});

	SetBuildingMode(EBuildingMode::EBuilding);
}

void UACFBuildingManagerComponent::Build()
{
	AActor* placeable = CastChecked<AActor>(CurrentObject.GetObject());
	if (!IsBuildablePlaceable(placeable)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Build failed: placement not valid for %s"), *GetNameSafe(placeable));
		return;
	}
	if (!CurrentRecipe) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Build failed: recipe not valid for %s"), *GetNameSafe(placeable));
		return;
	}

	// Verifica che la classe sia ancora caricata prima di fare il build
	if (CurrentRecipe->ItemType.IsNull() || !CurrentRecipe->ItemType.Get()) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Build failed: ItemType class not loaded for recipe %s"), *GetNameSafe(CurrentRecipe));
		return;
	}

	bLastPlacementValid = false;
	ServerBuild(
		CurrentRecipe->GetPrimaryAssetId(),
		CastChecked<AActor>(CurrentObject.GetObject())->GetActorLocation(),
		CastChecked<AActor>(CurrentObject.GetObject())->GetActorRotation());
}

void UACFBuildingManagerComponent::ServerBuild_Implementation(const FPrimaryAssetId& Id, const FVector& Location, const FRotator& Rotation)
{
	auto* const Inventory = GetInventoryComponent();
	if (!Inventory) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("ServerBuild failed: InventoryComponent not found"));
		return;
	}

	auto* Recipe = GetRecipeCheckedById(Id);
	if (!IsValid(Recipe)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("ServerBuild failed: no recipe with Id %s"), *Id.ToString());
		return;
	}

	const auto& RequiredMaterials = Recipe->RequiredItems;
	if (!Inventory->HasEnoughItemsOfType(RequiredMaterials)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("ServerBuild failed: not enough materials for recipe %s"), *Id.ToString());
		return;
	}

	// Check if the class is loaded
	UClass* ActorClass = Recipe->ItemType.Get();
	if (!ActorClass) {
		UE_LOG(LogAscentBuildingSystem, Log, TEXT("ServerBuild: Class not loaded, starting async load: %s"), *Recipe->ItemType.ToSoftObjectPath().ToString());

		// Async loading anche sul server
		UAssetManager& AssetManager = UAssetManager::Get();
		FStreamableManager& StreamableManager = AssetManager.GetStreamableManager();

		FSoftObjectPath SoftPath = Recipe->ItemType.ToSoftObjectPath();

		TSharedPtr<FStreamableHandle> LoadingHandle = StreamableManager.RequestAsyncLoad(
			SoftPath,
			FStreamableDelegate::CreateLambda([this, Id, Location, Rotation]() {
				OnServerActorClassLoaded(Id, Location, Rotation);
				}));

		if (!LoadingHandle.IsValid()) {
			UE_LOG(LogAscentBuildingSystem, Error, TEXT("ServerBuild failed: Could not start async loading for: %s"), *SoftPath.ToString());
		}
		return; // Exit here, callback will continue the build
	}

	// Classe già caricata, procedi con lo spawn
	SpawnActorOnServer(Recipe, ActorClass, Location, Rotation);
}

void UACFBuildingManagerComponent::OnServerActorClassLoaded(const FPrimaryAssetId& Id, const FVector& Location, const FRotator& Rotation)
{
	auto* Recipe = GetRecipeCheckedById(Id);
	if (!IsValid(Recipe)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("OnServerActorClassLoaded: Recipe no longer valid for Id %s"), *Id.ToString());
		return;
	}

	UClass* ActorClass = Recipe->ItemType.Get();
	if (!ActorClass) {
		UE_LOG(LogAscentBuildingSystem, Error, TEXT("OnServerActorClassLoaded: Failed to load class %s"),
			*Recipe->ItemType.ToSoftObjectPath().ToString());
		return;
	}

	UE_LOG(LogAscentBuildingSystem, Log, TEXT("OnServerActorClassLoaded: Successfully loaded class %s"), *ActorClass->GetName());

	// Verifica di nuovo i materiali (potrebbero essere cambiati durante il loading)
	auto* const Inventory = GetInventoryComponent();
	if (!Inventory || !Inventory->HasEnoughItemsOfType(Recipe->RequiredItems)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("OnServerActorClassLoaded: Materials no longer available"));
		return;
	}

	SpawnActorOnServer(Recipe, ActorClass, Location, Rotation);
}

void UACFBuildingManagerComponent::SpawnActorOnServer(UACFBuildRecipe* Recipe, UClass* ActorClass, const FVector& Location, const FRotator& Rotation)
{
	AActor* NewActor = GetWorld()->SpawnActor<AActor>(ActorClass, Location, Rotation);
	if (!IsValid(NewActor)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("SpawnActorOnServer failed: could not spawn Actor of type %s"),
			*GetNameSafe(ActorClass));
		return;
	}

	// Consume required materials
	auto* const Inventory = GetInventoryComponent();
	if (Inventory) {
		Inventory->ConsumeItems(Recipe->RequiredItems);
	}

	// Call interface method if supported
	if (NewActor->GetClass()->ImplementsInterface(UACFBuildableInterface::StaticClass())) {
		IACFBuildableInterface::Execute_OnPlaced(NewActor);
	}

	// Try to call Build() on the building system component
	if (UACFBuildableEntityComponent* BuildComp = NewActor->FindComponentByClass<UACFBuildableEntityComponent>()) {
		if (APlayerController* PC = GetPlayerController()) {
			BuildComp->Build(PC, Recipe);
		}
	}

	UE_LOG(LogAscentBuildingSystem, Log, TEXT("SpawnActorOnServer: Successfully built %s"), *NewActor->GetName());
}

void UACFBuildingManagerComponent::BeginPlay()
{
	Super::BeginPlay();
	if (GetOwner()->HasAuthority())
	{
		for (UACFBuildRecipe* Recipe : Recipes)
		{
			if (Recipe)
			{
				FACFRecipeIdItem NewItem(Recipe);
				RecipesIds.Items.Add(NewItem);
				RecipesIds.MarkItemDirty(RecipesIds.Items.Last());
			}
		}
	}
}

bool UACFBuildingManagerComponent::IsBuilding() const
{
	return GetBuildingMode() == EBuildingMode::EBuilding;
}

bool UACFBuildingManagerComponent::IsDismantling() const
{
	return GetBuildingMode() == EBuildingMode::EDismantling;
}

bool UACFBuildingManagerComponent::IsBuildablePlaceable(AActor* BuildableActor) const
{
	if (!IsValid(BuildableActor)) {
		return false;
	}

	const UACFBuildableEntityComponent* buildComp = BuildableActor->FindComponentByClass<UACFBuildableEntityComponent>();

	if (!buildComp) {
		return false;
	}

	if (!CurrentRecipe) {
		return false;
	}
	UACFInventoryComponent* invComp = GetInventoryComponent();

	if (!invComp || !invComp->HasEnoughItemsOfType(CurrentRecipe->RequiredItems)) {
		return false;
	}
	if (BuildableActor->GetClass()->ImplementsInterface(UACFBuildableInterface::StaticClass())) {
		return IACFBuildableInterface::Execute_IsPlacementValid(
			BuildableActor, // Execute_ richiede non-const
			BuildableActor->GetActorLocation(),
			BuildableActor->GetActorRotation())
			&& buildComp->IsPlacementValid();
	}

	return false;
}

void UACFBuildingManagerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	if (GetBuildingMode() != EBuildingMode::EBuilding) {
		return;
	}

	AActor* actor = Cast<AActor>(CurrentObject.GetObject());
	const auto* const Controller = GetPlayerController();
	if (Controller && actor) {
		const FVector Location = GetLocation(Controller, { Controller->GetPawn(), actor });
		MoveBuildingTo(Location);
	}
}

void UACFBuildingManagerComponent::RotateBuildingBy(const FRotator& RotationToAdd)
{
	CastChecked<AActor>(CurrentObject.GetObject())->AddActorWorldRotation(RotationToAdd.Quaternion());
	UpdateValidityFeedback();
}

void UACFBuildingManagerComponent::RotateBuildingByStep()
{
	RotateBuildingBy(DefaultRotationStep);
}

const TArray<UACFBuildRecipe*>& UACFBuildingManagerComponent::GetRecipes() const
{
	return Recipes;
}

UACFBuildRecipe* UACFBuildingManagerComponent::GetRecipeCheckedById(const FPrimaryAssetId& Id)
{
	return *Recipes.FindByPredicate([&](UACFBuildRecipe* Recipe) { return Recipe->GetPrimaryAssetId() == Id; });
}

UACFBuildRecipe* UACFBuildingManagerComponent::GetRecipeCheckedByClass(UClass* ItemType)
{
	return *Recipes.FindByPredicate([&](UACFBuildRecipe* Recipe) { return Recipe->ItemType == ItemType; });
}

TScriptInterface<IACFBuildableInterface> UACFBuildingManagerComponent::GetCurrentObject() const
{
	return CurrentObject;
}

void UACFBuildingManagerComponent::AddRecipe(UACFBuildRecipe* Recipe)
{
	AddRecipeServer(Recipe);
}

void UACFBuildingManagerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UACFBuildingManagerComponent, BuildingMode);
	DOREPLIFETIME(UACFBuildingManagerComponent, RecipesIds);
}

void UACFBuildingManagerComponent::StartDismantling()
{
	/* if (CurrentObject) {
		GetWorld()->DestroyActor(CastChecked<AActor>(CurrentObject.GetObject()));
		CurrentObject = nullptr;
	}*/
	SetBuildingMode(EBuildingMode::EDismantling);
}

void UACFBuildingManagerComponent::EndBuildMode()
{
	if (CurrentObject) {
		GetWorld()->DestroyActor(CastChecked<AActor>(CurrentObject.GetObject()));
		CurrentObject = nullptr;
	}
	SetBuildingMode(EBuildingMode::ENone);
}

EBuildingMode UACFBuildingManagerComponent::GetBuildingMode() const
{
	return BuildingMode;
}

void UACFBuildingManagerComponent::Dismantle_Implementation(AActor* buildable)
{
	if (!GetOwner()->HasAuthority()) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Dismantle failed: called on client, must run on server"));

		return;
	}
	if (!IsValid(buildable)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("Dismantle failed: invalid buildable actor"));

		return;
	}
	UACFInventoryComponent* const Inventory = GetInventoryComponent();
	if (!IsValid(Inventory)) {
		return;
	}


	const UACFBuildRecipe* recipe = GetRecipeCheckedByClass(buildable->GetClass());
	if (!IsValid(recipe)) {
		return;
	}

	UACFBuildableEntityComponent* buildComp = buildable->GetComponentByClass<UACFBuildableEntityComponent>();
	if (!buildComp) {
		return;
	}
	if (!buildComp->CanBeDismantled(GetPlayerController()->GetPawn())) {
		return;
	}

	if (buildable->GetClass()->ImplementsInterface(UACFBuildableInterface::StaticClass())) {
		IACFBuildableInterface::Execute_OnDismantled(buildable);
	}

	buildComp->Dismantle(GetPlayerController());
	for (const auto& Item : recipe->ReturnedItems) {
		Inventory->AddItemToInventory(Item);
	}
	buildable->SetLifeSpan(.2f);
	return;
}

void UACFBuildingManagerComponent::SetBuildingMode_Implementation(EBuildingMode val)
{
	BuildingMode = val;
	if (GetOwner()->HasAuthority()) {
		UpdateMappingContext();
	}
	OnBuildingModeChanged.Broadcast(BuildingMode);
}

void UACFBuildingManagerComponent::OnRep_BuildingMode()
{
	UpdateMappingContext();

	OnBuildingModeChanged.Broadcast(BuildingMode);
}

void UACFBuildingManagerComponent::UpdateMappingContext()
{
	UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetPlayerController()->GetLocalPlayer());

	if (Subsystem && BuildInputMappingContext)
	{
		if (BuildingMode == EBuildingMode::ENone) {
			Subsystem->RemoveMappingContext(BuildInputMappingContext);
		}
		else {
			Subsystem->AddMappingContext(BuildInputMappingContext, MappingContextPriority);
		}
	}
}

void UACFBuildingManagerComponent::RebuildCachedRecipes()
{
	Recipes.Reset(RecipesIds.Items.Num());
	for (const FACFRecipeIdItem& Item : RecipesIds.Items)
	{
		if (Item.Recipe)
		{
			Recipes.Add(Item.Recipe);
		}
	}
}

void UACFBuildingManagerComponent::MoveBuildingTo(const FVector& Location)
{
	if (Location.Equals(LastLocation)) {
		return;
	}
	LastLocation = Location;
	float LowestZ = UE_BIG_NUMBER;
	FVector Center = FVector::ZeroVector;
	auto* const CurrentActor = CastChecked<AActor>(CurrentObject.GetObject());
	CurrentActor->ForEachComponent<UMeshComponent>(false, [&](const UMeshComponent* const MeshComponent) {
		const FBox MeshBounds = MeshComponent->Bounds.GetBox();
		LowestZ = FMath::Min(MeshBounds.Min.Z, LowestZ);
		});
	CurrentActor->SetActorLocation(FVector(Location.X, Location.Y, Location.Z)); //+ (CurrentActor->GetActorLocation().Z - LowestZ)));
	if (auto* SnapComponent = CurrentActor->GetComponentByClass<UACFBuildingSnapComponent>(); IsValid(SnapComponent)) {
		SnapComponent->TrySnap();
	}

	UpdateValidityFeedback();
}

void UACFBuildingManagerComponent::AddRecipeServer_Implementation(UACFBuildRecipe* Recipe)
{
	FACFRecipeIdItem NewItem(Recipe);
	RecipesIds.Items.Add(NewItem);
	RecipesIds.MarkItemDirty(RecipesIds.Items.Last());
	OnRep_RecipesIds();
}

void UACFBuildingManagerComponent::OnRep_RecipesIds()
{
	RebuildCachedRecipes();
}

void UACFBuildingManagerComponent::UpdateValidityFeedback()
{
	AActor* const CurrentActor = CastChecked<AActor>(CurrentObject.GetObject());
	if (!IsValid(CurrentActor)) {
		UE_LOG(LogAscentBuildingSystem, Warning, TEXT("UpdateValidityFeedback failed: CurrentActor is invalid."));

		return;
	}

	bool bPlacementValid = false;
	if (CurrentActor->GetClass()->ImplementsInterface(UACFBuildableInterface::StaticClass())) {
		bPlacementValid = IsBuildablePlaceable(CurrentActor);
	}
	// AVOID REAPPLYING MATERIAL
	if (bPlacementValid == bLastPlacementValid && !bFirstCheck) {
		return;
	}
	bLastPlacementValid = bPlacementValid;

	UMaterialInterface* MaterialToApply = bPlacementValid ? ValidMaterial : InvalidMaterial;

	CurrentActor->ForEachComponent<UMeshComponent>(false, [&](UMeshComponent* MeshComponent) {
		const int32 NumMats = MeshComponent->GetNumMaterials();
		for (int32 i = 0; i < NumMats; ++i) {
			if (MeshComponent->GetMaterial(i) != MaterialToApply) {
				MeshComponent->SetMaterial(i, MaterialToApply);
			}
		}
		});
	bFirstCheck = false;
}

APlayerController* UACFBuildingManagerComponent::GetPlayerController() const
{

	APlayerController* Controller = Cast<APlayerController>(GetOwner());
	if (!Controller) {
		return nullptr;
	}

	return Controller;
}

UACFInventoryComponent* UACFBuildingManagerComponent::GetInventoryComponent() const
{

	const APlayerController* Controller = GetPlayerController();

	if (Controller) {
		const APawn* pawn = Controller->GetPawn();
		if (pawn) {
			return pawn->FindComponentByClass<UACFInventoryComponent>();
		}
	}
	return nullptr;
}

FVector UACFBuildingManagerComponent::GetLocation(const APlayerController* Controller, const TArray<AActor*>& ToIgnore)
{
	FVector WorldLocation;
	FVector WorldDirection;
	int32 ViewportX;
	int32 ViewportY;
	Controller->GetViewportSize(ViewportX, ViewportY);

	if (!Controller) {
		return FVector::ZeroVector;
	}
	// TODO: The only reason why this function needs the controller, might want to do this outside and pass the resulting location and direction in
	const bool bSuccess = Controller->DeprojectScreenPositionToWorld(ViewportX / 2, ViewportY / 2, WorldLocation, WorldDirection);
	if (!bSuccess) {
		return FVector::ZeroVector;
	}

	const FVector EndLocation = WorldLocation + (WorldDirection * 2000);
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActors(ToIgnore);
	FHitResult HitResult;
	const bool bHit = GetWorld()->LineTraceSingleByChannel(HitResult, WorldLocation, EndLocation, ECC_Visibility, QueryParams);
	if (!bHit) {
		GetWorld()->LineTraceSingleByChannel(HitResult, EndLocation, EndLocation + FVector::DownVector * 5000, ECC_Visibility, QueryParams);
	}
	else {
		const auto Start = HitResult.ImpactPoint + (HitResult.ImpactNormal * 5);
		GetWorld()->LineTraceSingleByChannel(HitResult, Start, Start + (FVector::DownVector * 5000), ECC_Visibility, QueryParams);
	}
	return HitResult.ImpactPoint;
}