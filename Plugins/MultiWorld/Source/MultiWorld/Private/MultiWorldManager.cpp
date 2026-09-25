// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldManager.h"

#include "MultiWorld.h"

#include "MultiWorldActorInterface.h"
#include "PhysicsConstraintsReregistrationFix.h"
#include "MultiWorldStatics.h"
#include "Private/MultiWorldSeamTransitionFXLayer.h"

#if WITH_EDITOR
#include "BlueprintCompilationManager.h"
#endif // WITH_EDITOR

#include "EngineUtils.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/GameEngine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "Engine/WorldComposition.h"
#include "Engine/LevelStreaming.h"
#include "AssetCompilingManager.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AudioDeviceManager.h"
#include "AudioDevice.h"
#include "GameFramework/PlayerInput.h"
#include "Blueprint/UserWidget.h"
#include "Components/WidgetComponent.h"
#include "Slate/SceneViewport.h"
#include "RenderingThread.h"
#include "SceneInterface.h"

#include "UObject/Package.h"
#include "UObject/UObjectIterator.h"
#include "Runtime/Launch/Resources/Version.h"

#include "Kismet/GameplayStatics.h"

#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SConstraintCanvas.h"
#include "Slate/SObjectWidget.h"

#include "EnhancedInputSubsystems.h"
#include "AI/NavigationSystemBase.h"

class MultiWorldGameInstanceEx : public UGameInstance
{
public:

    void SetWorldContext(FWorldContext* InWorldContext) { WorldContext = InWorldContext; }
};

class GameViewportClientEx : public UGameViewportClient
{
public:

    void ResetWorldContext(struct FWorldContext& WorldContext)
    {
        // set reference to world context
        WorldContext.AddRef(static_cast<UWorld*&>(World));
    }

    void SetAudioDevice(FAudioDeviceHandle InAudioDeviceHandle)
    {
        AudioDevice = InAudioDeviceHandle;
    }
};



FMultiWorldTransferActorParameters::FMultiWorldTransferActorParameters()
	: bSetPhysicsActorTransform(false),
	  Transform(),
	  Teleport(ETeleportType::ResetPhysics)
{}



FMultiWorldTransferActorParameters::FMultiWorldTransferActorParameters(
	const FTransform & InTransform,
	ETeleportType InTeleport
)
	: bSetPhysicsActorTransform(InTransform.IsValid()),
	  Transform(InTransform),
	  Teleport(InTeleport)
{
}



void FMultiWorldTransferActorParameters::SetTransform(const FTransform & NewTransform)
{
	bSetPhysicsActorTransform = NewTransform.IsValid();
	Transform = NewTransform;
}



UMultiWorldManager & UMultiWorldManager::GetInstance(const UObject * context)
{
    check(context != nullptr);
    UWorld * world = context->GetWorld();
	const UGameInstance * gameInst = nullptr;
	if (world != nullptr)
	{
		gameInst = world->GetGameInstance();
	}
	else
	{
		gameInst = Cast<UGameInstance>(context);
	}

    check(gameInst != nullptr);
    UMultiWorldManager * result = gameInst->GetSubsystem<UMultiWorldManager>();
    check(result != nullptr);
    return *result;
}

bool UMultiWorldManager::ShouldCreateSubsystem(UObject* Outer) const
{
    // In the editor only PIE game instances own the PlayWorld. Standalone game
    // instances (automation, editor utilities) must not get a manager, or
    // FixupEditorEngine writes their world into GEditor->PlayWorld.
    if (GIsEditor)
    {
        const UGameInstance* GameInstance = Cast<UGameInstance>(Outer);
        const FWorldContext* WorldContext = GameInstance ? GameInstance->GetWorldContext() : nullptr;
        return WorldContext && WorldContext->WorldType == EWorldType::PIE;
    }
    return Super::ShouldCreateSubsystem(Outer);
}

void UMultiWorldManager::Initialize(FSubsystemCollectionBase& Collection)
{
    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    MainWorld = ActiveWorld = GameInstance->GetWorld();
    check(MainWorld);

    MainWorldContext = &GEngine->GetWorldContextFromWorldChecked(MainWorld);

    FTickerDelegate TickDelegate = FTickerDelegate::CreateUObject(this, &UMultiWorldManager::OnCoreTick);
    OnCoreTickDelegateHandle = FTSTicker::GetCoreTicker().AddTicker(TickDelegate);

    FWorldDelegates::OnWorldTickEnd.AddUObject(this, &UMultiWorldManager::OnWorldTickEnd);
    FWorldDelegates::OnWorldTickStart.AddUObject(this, &UMultiWorldManager::OnWorldTickStart);
    FWorldDelegates::OnWorldPostActorTick.AddUObject(this, &UMultiWorldManager::OnWorldPostActorTick);

#if WITH_EDITOR
    GEngine->OnPostEditorTick().AddUObject(this, &UMultiWorldManager::OnPostEditorTick);
    FEditorDelegates::PrePIEEnded.AddUObject(this, &UMultiWorldManager::OnPIEEnded);
    FEditorDelegates::SingleStepPIE.AddUObject(this, &UMultiWorldManager::OnSingleStepPIE);
    FEditorDelegates::OnSwitchBeginPIEAndSIE.AddUObject(this, &UMultiWorldManager::OnSwitchPIEAndSIE);
#endif // WITH_EDITOR
}

void UMultiWorldManager::OnWorldChanged(UWorld* OldWorld, UWorld* NewWorld)
{
    // is the engine unloading the main world?
    if (OldWorld == MainWorld)
    {
        // when the NewWorld is nullptr mean that the engine 
        // is unloading the current main world...
        // then the engine will load the new one, and this function will be called again
        // with a valid NewWorld ptr

        if (OldWorld)
        {
            DeleteWidgetsContainerForWorld(OldWorld);
        }

        WorldStates.Remove(MainWorld);

        if (ActiveWorld == OldWorld)
        {
            ActiveWorld = NewWorld;
        }

        MainWorld = NewWorld;

        if (NewWorld)
        {
            MainWorldContext = &GEngine->GetWorldContextFromWorldChecked(NewWorld);

            // if the active world is not the main world but an another world handled by the plugin...
            if (ActiveWorld != NewWorld)
            {
                auto& WorldState = WorldStates.FindOrAdd(ActiveWorld);

                if (WorldState.LoadParameters.bAutoHandleInputMode)
                {
                    // save the last input mode of the active world to be restored after the begin play of the main world
                    // because the begin play of the main world could override the input mode.
                    SaveInputModeForLocalPlayers(ActiveWorld, WorldStates.FindOrAdd(ActiveWorld).PlayerInputStates);

                    // Call RestoreInputModeForLocalPlayers when OnWorldBeginPlay is fired.
                    MainWorld->OnWorldBeginPlay.AddLambda([This=this]() {

                        if (This->ActiveWorld)
                        {
                            auto& WorldState = This->WorldStates.FindOrAdd(This->ActiveWorld);

                            This->RestoreInputModeForLocalPlayers(This->ActiveWorld, WorldState.PlayerInputStates);
                        }
                    });
                }
            }
        }
    }
}

void UMultiWorldManager::NotifyLoadWorldCompleted(bool Success, FMultiWorldHandle WorldHandle, const FMultiWorldLoadParameters& LoadParams, TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback)
{
    if (OnCompleteCallback)
    {
        OnCompleteCallback(Success, WorldHandle, LoadParams);
    }
    OnLoadWorldCompleted.Broadcast(Success, WorldHandle, LoadParams);
}

void UMultiWorldManager::Deinitialize()
{
    FTSTicker::GetCoreTicker().RemoveTicker(OnCoreTickDelegateHandle);

    FWorldDelegates::OnWorldPostActorTick.RemoveAll(this);
    FWorldDelegates::OnWorldTickStart.RemoveAll(this);
    FWorldDelegates::OnWorldTickEnd.RemoveAll(this);

#if WITH_EDITOR
    FEditorDelegates::OnSwitchBeginPIEAndSIE.RemoveAll(this);
    FEditorDelegates::SingleStepPIE.RemoveAll(this);
    FEditorDelegates::PrePIEEnded.RemoveAll(this);
    GEngine->OnPostEditorTick().RemoveAll(this);
#endif // WITH_EDITOR

    // Restore the main audio device to the game viewport, the engine expect that.
    // Doesn't call ActivateAudioDeviceForWorld(MainWorld); because the
    // GEngine->GetAudioDeviceManager() is already nullptr.
    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);
    if (UGameViewportClient* ThisGameViewport = GameInstance->GetGameViewportClient())
    {
        static_cast<GameViewportClientEx*>(ThisGameViewport)->SetAudioDevice(MainWorld ? MainWorld->GetAudioDevice() : FAudioDeviceHandle());
    }

    EndAllWorldsInternal();

    // it's important to do a GC here because ensures
    // that all secondary worlds are fully destroied (BeginDestroy called)
    // and so audio devices de-registered/destroied too 
    // before FAudioDeviceManager::Shutdown is called (see bug #812)
    // BUT DO NOT do it in editor (see bug #856)
#if WITH_EDITOR
    if (!GEditor)
#endif
    {
        CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
    }
}

void UMultiWorldManager::Tick(float DeltaTime)
{
#if WITH_EDITOR
    FixupEditorEngine();
#endif // WITH_EDITOR
}

bool UMultiWorldManager::IsTickable() const
{
    return true;
}

TStatId UMultiWorldManager::GetStatId() const
{
    return UObject::GetStatID();
}

void UMultiWorldManager::LoadWorldImpl(
    TSoftObjectPtr<UWorld> MapAsset,
    FMultiWorldLoadParameters LoadParams, 
    FName InMemoryPackageName, 
    TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback)
{
    check(InMemoryPackageName != NAME_None);

    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    FWorldContext* WorldContext = GameInstance->GetWorldContext();

    FString PackageNameToLoadOnDisk = MapAsset.GetLongPackageName();

    // This avoid that in PIE the engine initialize the world by itself
    UWorld::WorldTypePreLoadMap.FindOrAdd(InMemoryPackageName) = WorldContext->WorldType;

    UPackage* InMemoryPackage = InMemoryPackageName != FName(PackageNameToLoadOnDisk)
        ? NewObject<UPackage>(nullptr, UPackage::StaticClass(), InMemoryPackageName)
        : nullptr;

#if WITH_EDITOR
    if (GIsEditor)
    {
        check(WorldContext->PIEInstance != INDEX_NONE);

        InMemoryPackage->SetPackageFlags(PKG_PlayInEditor);
        InMemoryPackage->SetPIEInstanceID(WorldContext->PIEInstance);
    }
#endif //WITH_EDITOR

    UPackage *WorldPackage = LoadPackage(InMemoryPackage, *PackageNameToLoadOnDisk, ELoadFlags::LOAD_None);
    UWorld* LoadedWorld = WorldPackage ? GetWorldFromPackage(WorldPackage) : nullptr;

    if (LoadedWorld)
    {
        check(!WorldPackage->HasAnyFlags(RF_Standalone));
        
        PostLoadWorld(MapAsset, LoadParams, LoadedWorld, InMemoryPackageName);
    }
    else
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Unable to load the level; Check the the input MapAsset is valid."));

        PendingLoadWorlds.RemoveAll([InMemoryPackageName](const FPendingLoadWorldData& InWorldData) { return InWorldData.MemoryPackageName == InMemoryPackageName; });
        InMemoryPackage->MarkAsGarbage();
    }

    NotifyLoadWorldCompleted(LoadedWorld != nullptr, LoadedWorld, LoadParams, OnCompleteCallback);
}

void UMultiWorldManager::LoadWorld(
    TSoftObjectPtr<UWorld> MapAsset, 
    FMultiWorldLoadParameters LoadParams, 
    TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback)
{
    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    UWorld* World = GameInstance->GetWorld(); // this get the active world.
    check(World);

    FMultiWorldHandle OldHandle;
    if (!PreLoadWorld(MapAsset, LoadParams, OldHandle))
    {
        NotifyLoadWorldCompleted(OldHandle.IsValid(), OldHandle, LoadParams, OnCompleteCallback);
        return;
    }

    FWorldContext* WorldContext = GameInstance->GetWorldContext();

    FString PackageNameToLoadOnDisk = MapAsset.GetLongPackageName();

    FName InMemoryPackageName = FindUniquePackageName(PackageNameToLoadOnDisk, WorldContext->PIEInstance, LoadParams.bUseStrictPackageNameWhenPossible);

    UE_LOG(LogMultiWorld, Log, TEXT("Scheduled the loading of %s into %s"), *PackageNameToLoadOnDisk, *InMemoryPackageName.ToString());

    if (World->HasBegunPlay())
    {
        LoadWorldImpl(MapAsset, LoadParams, InMemoryPackageName, OnCompleteCallback);
    }
    else
    {
        // the world is in loading but we want to avoid nested beginplay (see bug #982)
        // delay the world loading until the world's beginplay is not over.
        // note: the delegate UWorld::OnWorldBeginPlay, when we are playing as listen-server, is called
        // before doing the real job for clients. For this reason we are not using it.
        FPendingLoadWorldData LoadWorldData;
        LoadWorldData.Type = SYNC_LOADING;
        LoadWorldData.MapAsset = MapAsset;
        LoadWorldData.LoadParams = LoadParams;
        LoadWorldData.OnCompleteCallback = MoveTemp(OnCompleteCallback);
        LoadWorldData.MemoryPackageName = InMemoryPackageName;

        PendingLoadWorlds.Emplace(LoadWorldData);
    }
}

void UMultiWorldManager::LoadWorldAsync(TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters LoadParams, TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback)
{
    FMultiWorldHandle OldHandle;
    if (!PreLoadWorld(MapAsset, LoadParams, OldHandle))
    {
        NotifyLoadWorldCompleted(OldHandle.IsValid(), OldHandle, LoadParams, OnCompleteCallback);
        return;
    }

    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    FWorldContext* WorldContext = GameInstance->GetWorldContext();

    FString PackageNameToLoadOnDisk = MapAsset.GetLongPackageName();
    FName InMemoryPackageName = FindUniquePackageName(PackageNameToLoadOnDisk, WorldContext->PIEInstance, LoadParams.bUseStrictPackageNameWhenPossible);

    UE_LOG(LogMultiWorld, Log, TEXT("Scheduled the loading of %s into %s"), *PackageNameToLoadOnDisk, *InMemoryPackageName.ToString());

    // This avoid that in PIE the engine initialize the world by itself
    UWorld::WorldTypePreLoadMap.FindOrAdd(InMemoryPackageName) = WorldContext->WorldType;

    FPendingLoadWorldData LoadWorldData;
    LoadWorldData.Type = ASYNC_LOADING;
    LoadWorldData.MapAsset = MapAsset;
    LoadWorldData.LoadParams = LoadParams;
    LoadWorldData.MemoryPackageName = InMemoryPackageName;
    LoadWorldData.OnCompleteCallback = OnCompleteCallback;

    PendingLoadWorlds.Emplace(LoadWorldData);

    LoadPackageAsync(FPackagePath::FromPackageNameChecked(PackageNameToLoadOnDisk),
        InMemoryPackageName,
        FLoadPackageAsyncDelegate::CreateLambda([this, MapAsset, LoadParams, OnCompleteCallback]
        (const FName& PackageName, UPackage* Package, EAsyncLoadingResult::Type Result)
    {
        check(IsInGameThread());

        FMultiWorldHandle WorldHandle = nullptr;

        if (Package && Result == EAsyncLoadingResult::Succeeded)
        {
            UWorld* NewWorld = GetWorldFromPackage(Package);
            if (NewWorld)
            {
                check(!Package->HasAnyFlags(RF_Standalone));

                PostLoadWorld(MapAsset, LoadParams, NewWorld, PackageName);

                WorldHandle = NewWorld;
            }
        }

        const bool Success = WorldHandle.IsValid();
        if(!Success)
        {
            PendingLoadWorlds.RemoveAll([PackageName](const FPendingLoadWorldData& InWorldData) { return InWorldData.MemoryPackageName == PackageName; });

            UE_LOG(LogMultiWorld, Warning, TEXT("Unable to load the level; Check the the input MapAsset is valid."));
        }

        NotifyLoadWorldCompleted(Success, WorldHandle, LoadParams, OnCompleteCallback);
    }),
#if WITH_EDITOR
        GIsEditor ? EPackageFlags::PKG_PlayInEditor : EPackageFlags::PKG_None,
        WorldContext->PIEInstance
#else
        EPackageFlags::PKG_None
#endif // WITH_EDITOR
    );
}

UWorld* UMultiWorldManager::GetWorldFromPackage(UPackage* InWorldPackage)
{
    UWorld* LoadedWorld = UWorld::FindWorldInPackage(InWorldPackage);
    if (!LoadedWorld)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Unable to get the UWorld from the level."));
        return nullptr;
    }

    return LoadedWorld;
}

void UMultiWorldManager::HandleViewportWidgetsVisibility(UWorld* FromWorld, UWorld* ToWorld)
{
    check(FromWorld);
    check(ToWorld);

    TSharedPtr<SOverlay> FromWorldWidgetContainer = GetWidgetsContainerForWorld(FromWorld, /*bCreateIfNull=*/false);
    TSharedPtr<SOverlay> ToWorldWidgetContainer = GetWidgetsContainerForWorld(ToWorld, /*bCreateIfNull=*/false);

    if (FromWorldWidgetContainer)
    {
        FromWorldWidgetContainer->SetVisibility(EVisibility::Collapsed);
    }
    if (ToWorldWidgetContainer)
    {
        ToWorldWidgetContainer->SetVisibility(EVisibility::SelfHitTestInvisible);
    }
}

TSharedPtr<SOverlay> UMultiWorldManager::GetWidgetsContainerForWorld(UWorld* World, bool bCreateIfNull)
{
    check(World);

    auto& State = WorldStates.FindOrAdd(World);
    if (State.WidgetsContainer)
    {
        return State.WidgetsContainer;
    }
    else if (bCreateIfNull)
    {
        FWorldContext& WorldContext = GEngine->GetWorldContextFromWorldChecked(World);
        if (ensure(WorldContext.GameViewport))
        {
            State.WidgetsContainer = SNew(SOverlay);
            State.WidgetsContainer->SetVisibility(
                World == ActiveWorld
                ? EVisibility::SelfHitTestInvisible
                : EVisibility::Collapsed);

            WorldContext.GameViewport->AddGameLayerWidget(State.WidgetsContainer.ToSharedRef(), /*ZOrder=*/INDEX_NONE);
        }

        return State.WidgetsContainer;
    }

    return nullptr;
}

void UMultiWorldManager::DeleteWidgetsContainerForWorld(UWorld* World)
{
    check(World);

    TSharedPtr<SOverlay> WidgetsContainer = GetWidgetsContainerForWorld(World, /*bCreateIfNull=*/false);
    if (WidgetsContainer)
    {
        WidgetsContainer->ClearChildren();

        if (MainWorldContext && MainWorldContext->GameViewport) // note: GameViewport is nullptr at shutdown.
        {
            MainWorldContext->GameViewport->RemoveGameLayerWidget(WidgetsContainer.ToSharedRef());
        }
    }
}

void UMultiWorldManager::SaveInputModeForLocalPlayers(UWorld* World, TMap<int32, InputState>& PlayerInputStateMap)
{
    for (auto LocalPlayer : GetLocalPlayers())
    {
        const int32 ControllerId = LocalPlayer->GetControllerId();

        APlayerController* PlayerController = UGameplayStatics::GetPlayerControllerFromID(World, ControllerId);

        InputState& is = PlayerInputStateMap.FindOrAdd(ControllerId);
        SaveInputMode(PlayerController, is);
    }
}

void UMultiWorldManager::RestoreInputModeForLocalPlayers(UWorld* World, const TMap<int32, InputState>& PlayerInputStateMap)
{
    for (auto LocalPlayer : GetLocalPlayers())
    {
        const int32 ControllerId = LocalPlayer->GetControllerId();

        APlayerController* PlayerController = UGameplayStatics::GetPlayerControllerFromID(World, ControllerId);

        if (const InputState* is = PlayerInputStateMap.Find(ControllerId))
        {
            RestoreInputMode(PlayerController, *is);
        }
    }
}

void UMultiWorldManager::SaveInputMode(APlayerController* PC, InputState& is)
{
    UGameViewportClient* GVC = GetWorld()->GetGameViewport();

    if (GVC->IgnoreInput())
    {
        is.InputMode = EMultiWorldInputMode::UIOnly;
    }
    else
    {
        const auto CaptureMode = GVC->GetMouseCaptureMode();
        // Game-only mode captures permanently, that seems to be the best way to detect
        if (CaptureMode == EMouseCaptureMode::CapturePermanently ||
            CaptureMode == EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown)
        {
            is.InputMode = EMultiWorldInputMode::GameOnly;
        }
        else
        {
            is.InputMode = EMultiWorldInputMode::GameAndUI;
        }
    }

    UGameViewportClient* Viewport = GEngine->GameViewportForWorld(GetActiveWorld());
    if (Viewport)
    {
        is.MouseCaptureMode = Viewport->GetMouseCaptureMode();
        is.MouseLockMode = Viewport->GetMouseLockMode();
    }
}

void UMultiWorldManager::RestoreInputMode(APlayerController* PC, const InputState& is)
{
    switch (is.InputMode)
    {
    case EMultiWorldInputMode::UIOnly:
        PC->SetInputMode(FInputModeUIOnly().SetLockMouseToViewportBehavior(is.MouseLockMode));
        break;
    case EMultiWorldInputMode::GameAndUI:
        PC->SetInputMode(FInputModeGameAndUI().SetLockMouseToViewportBehavior(is.MouseLockMode));
        break;
    case EMultiWorldInputMode::GameOnly:
        PC->SetInputMode(FInputModeGameOnly().SetConsumeCaptureMouseDown(is.MouseCaptureMode == EMouseCaptureMode::CapturePermanently));
    }
}

FName UMultiWorldManager::FindUniquePackageName(const FString& InPackageName, int PIEInstance, bool bUseStrictPackageNameWhenPossible) const
{
    FString NewPackageName = InPackageName;

#if WITH_EDITOR
    if (GIsEditor)
    {
        NewPackageName = UWorld::ConvertToPIEPackageName(InPackageName, PIEInstance);
    }
#endif // WITH_EDITOR

    // if not already loaded, load the world using the standard/Unreal path convention so that the world can work with the sequencer.
    if (bUseStrictPackageNameWhenPossible)
    {
        UPackage* Package = FindObject<UPackage>(nullptr, *NewPackageName);
        if (Package == nullptr)
        {
            // ...but check there is not a pending load with that package name!
            if (!PendingLoadWorlds.ContainsByPredicate([&](const FPendingLoadWorldData& LoadWorldData)
                {
                    return LoadWorldData.MemoryPackageName == FName(NewPackageName);
                }))
            {
                return FName(NewPackageName);
            }
        }
    }

    NewPackageName = MakeUniqueObjectName(nullptr, UPackage::StaticClass(), *NewPackageName).ToString();

#if WITH_EDITOR
    // in editor add the Temp subfolder to avoid that new packages are visible in the content browser!
    NewPackageName = TEXT("/Temp") / NewPackageName;
#endif // WITH_EDITOR

    return FName(NewPackageName);
}

void UMultiWorldManager::AddViewportWidgetContent(TSharedRef<SWidget> InWidget, int32 ZOrder)
{
    if (UUserWidget* Widget = GetUserWidget(InWidget))
    {
        // don't take in account the UMG used for the transition fx
        if (!Widget->IsA<UMultiWorldSeamTransitionFXLayer>())
        {
            UWorld* WidgetWorld = Widget->GetWorld();
            if (ensure(WidgetWorld))
            {
                if (ShouldHandleWidgetsForWorld(WidgetWorld))
                {
                    TSharedPtr<SOverlay> Container = GetWidgetsContainerForWorld(WidgetWorld, /*bCreateIfNull=*/true);

                    Container->AddSlot(ZOrder)
                        [
                            InWidget
                        ];

                    return;
                }
            }
        }
    }

    if (MainWorldContext && MainWorldContext->GameViewport)
    {
        MainWorldContext->GameViewport->UGameViewportClient::AddViewportWidgetContent(InWidget, ZOrder);
    }
}

void UMultiWorldManager::RemoveViewportWidgetContent(TSharedRef<SWidget> InWidget)
{
    if (UUserWidget* Widget = GetUserWidget(InWidget))
    {
        UWorld* WidgetWorld = Widget->GetWorld();
        if (ensure(WidgetWorld))
        {
            if (ShouldHandleWidgetsForWorld(WidgetWorld))
            {
                TSharedPtr<SOverlay> Container = GetWidgetsContainerForWorld(WidgetWorld, /*bCreateIfNull=*/false);

                if (Container && Container->RemoveSlot(InWidget))
                {
                    return;
                }
            }
        }
    }

    if (MainWorldContext && MainWorldContext->GameViewport)
    {
        MainWorldContext->GameViewport->UGameViewportClient::RemoveViewportWidgetContent(InWidget);
    }
}

UUserWidget* UMultiWorldManager::GetUserWidget(TSharedRef<SWidget> InWidget)
{
    // 99.9% of times the ViewportContent is SConstraintCanvas with a SObjectWidget as first child
    // but we know some cases for which this assumption is not true (IMGUI, virtual joysitck, etc)
    // Skip these cases...
    if (InWidget->GetType() != FName(TEXT("SConstraintCanvas")))
    {
        return nullptr;
    }

    TSharedRef<SConstraintCanvas> CCanvas = StaticCastSharedRef<SConstraintCanvas>(InWidget);

    check(CCanvas->GetChildren() && CCanvas->GetChildren()->Num() == 1);
    check(CCanvas->GetChildren()->GetChildAt(0)->GetType() == FName(TEXT("SObjectWidget")));
    TSharedRef<SObjectWidget> ObjectWidget = StaticCastSharedRef<SObjectWidget>(CCanvas->GetChildren()->GetChildAt(0));

    UUserWidget* UserWidget = ObjectWidget->GetWidgetObject();
    check(UserWidget);

    return UserWidget;
}

bool UMultiWorldManager::ShouldHandleWidgetsForWorld(UWorld* World)
{
    if (auto* State = WorldStates.Find(World))
    {
        return State->LoadParameters.bAutoHandleWidgets;
    }
    else
    {
        const bool IsMainWorld = MainWorld == World;
        return IsMainWorld; // by default the widgets of Main World are handled.
    }
}

//https://answers.unrealengine.com/questions/461839/multiple-world-scenecapturecomponent.html
//https://forums.unrealengine.com/development-discussion/c-gameplay-programming/1576984-some-problems-while-implement-a-function-that-allow-player-switch-between-multiple-uworld
//https://forums.unrealengine.com/development-discussion/engine-source-github/64053-multiple-concurrent-uworlds
//https://forums.unrealengine.com/development-discussion/engine-source-github/118411-state-of-multiple-uworlds
//https://answers.unrealengine.com/questions/602604/syncing-actors-in-distinct-uworlds.html
void UMultiWorldManager::InitializeWorld(const FMultiWorldHandle& InWorldHandle)
{
    UWorld* NewWorld = GetWorldChecked(InWorldHandle, false);
    if (!NewWorld)
        return;

    if (InWorldHandle.IsActivated())
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Input WorldHandle is already activated, aborted..."));
        return;
    }

    if (!GetActiveWorld())
    {
        UE_LOG(LogMultiWorld, Error, TEXT("InitializeWorld() aborted! Are you using the MultiWorldGameInstance?"));
        return;
    }

    UGameInstance* GameInstance = GetGameInstance();

    FWorldContext* ActualWorldContext = GameInstance->GetWorldContext();

    FAudioDeviceManager* AudioDeviceManager = GEngine->GetAudioDeviceManager();
    FAudioDeviceHandle AudioDeviceHandle;

    auto& WorldState = WorldStates.FindOrAdd(NewWorld);

    const bool bCreateDedicatedAudioDevice 
        = WorldState.LoadParameters.bCreateDedicatedAudioDevice;

    if (AudioDeviceManager && bCreateDedicatedAudioDevice)
    {
        // EAudioDeviceScope::Shared could be used when the user doesn't want a dedicated audio device but 
        // it's not because in PIE, RequestAudioDevice returns a generic editor audio device and
        // not the main world once.
        FAudioDeviceParams DeviceParams = AudioDeviceManager->GetDefaultParamsForNewWorld();
        DeviceParams.Scope = EAudioDeviceScope::Unique;
        DeviceParams.AssociatedWorld = NewWorld;

        // make a new audio device
        // minimizing the scope of the audio thread suspension
        {
            // the FAudioThreadSuspendContext is used instead of FAudioThread::RunCommandOnAudioThread and the fence (FAudioCommandFence)
            // because the code checks for, in different points, IsInGameThread() and IsInAudioThread()
            FAudioThreadSuspendContext AudioThreadSuspendContext;
            AudioDeviceHandle = AudioDeviceManager->RequestAudioDevice(DeviceParams);
        }

        check(AudioDeviceHandle.IsValid());

        AudioDeviceHandle.GetAudioDevice()->SetDefaultBaseSoundMix(NewWorld->GetWorldSettings()->DefaultBaseSoundMix);

        AudioDeviceManager->SetActiveDevice(ActualWorldContext->AudioDeviceID);
    }
    else
    {
        // warning in editor: AudioDeviceManager->GetMainAudioDeviceHandle() != MainWorld->GetAudioDevice()
        check(MainWorld);
        AudioDeviceHandle = MainWorld->GetAudioDevice();
    }

    // From UE4.26: SetAudioDevice implementation has changed and the check below assert when bCreateDedicatedAudioDevice is false
    // https://github.com/EpicGames/UnrealEngine/blob/4.26/Engine/Source/Runtime/Engine/Private/World.cpp#L7781
    // To avoid this i have extrapolated the useful work below
    //NewWorld->SetAudioDevice(AudioDeviceHandle);
    {
        NewWorld->AudioDeviceHandle = AudioDeviceHandle;
        if (AudioDeviceManager)
        {
            AudioDeviceManager->RegisterWorld(NewWorld, AudioDeviceHandle.GetDeviceID());
        }
    }

    EWorldType::Type WorldType = ActualWorldContext->WorldType;

    NewWorld->WorldType = WorldType;
    NewWorld->SetFeatureLevel(MainWorld->GetFeatureLevel());
    NewWorld->SetGameInstance(GameInstance);
#if WITH_EDITOR
    if (ActualWorldContext->PIEInstance != -1)
    {
        NewWorld->RenameToPIEWorld(ActualWorldContext->PIEInstance);

        // Before UE5.8, UWorldComposition::PostInitProperties() and UWorldComposition::ReinitializeForPIE() called UWorldComposition::Rescan() to populate Tiles and TilesStreaming in-editor.
        // In UE5.8, this initialization flow changed, relying more on Serialize/PostDuplicate/PostLoad for PIE and cooked data, assuming tile data already exists or is recoverable from the duplicated object.
        if (NewWorld->WorldComposition)
        {
            NewWorld->WorldComposition->Rescan(/*bForce*/true);
            NewWorld->SetStreamingLevels(NewWorld->WorldComposition->TilesStreaming);

            for (ULevelStreaming* LevelStreaming : NewWorld->GetStreamingLevels())
            {
                LevelStreaming->RenameForPIE(ActualWorldContext->PIEInstance);
            }
        }
    }
#endif // WITH_EDITOR
    NewWorld->SetShouldTick(WorldState.ShouldTickWhenInBackground());
    NewWorld->InitWorld();

    FWorldContext& NewWorldContext = GEngine->CreateNewWorldContext(WorldType);
    NewWorldContext.AudioDeviceID = AudioDeviceHandle.GetDeviceID();
    NewWorldContext.SetCurrentWorld(NewWorld); // NewWorldContext.AudioDeviceHandle must be set before this call
    NewWorldContext.OwningGameInstance = GameInstance;
    NewWorldContext.GameViewport = ActualWorldContext->GameViewport;
    NewWorldContext.PIEInstance = ActualWorldContext->PIEInstance;
    NewWorldContext.PIEPrefix = ActualWorldContext->PIEPrefix;
    NewWorldContext.PIEWorldFeatureLevel = ActualWorldContext->PIEWorldFeatureLevel;
    NewWorldContext.bIsPrimaryPIEInstance = ActualWorldContext->bIsPrimaryPIEInstance;

#if WITH_EDITOR
    if (GEditor)
    {
        auto SlatePlayInEditorInfo = GEditor->SlatePlayInEditorMap.Find(ActualWorldContext->ContextHandle);
        if (SlatePlayInEditorInfo)
        {
            GEditor->SlatePlayInEditorMap.Add(NewWorldContext.ContextHandle, *SlatePlayInEditorInfo);
        }
    }
#endif // WITH_EDITOR

    PlayWorld(NewWorld, WorldState.LoadParameters.URLOptions);

#if ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 3
    // this call fix an assert that fires if the secondary world use the world partition.
    ENQUEUE_RENDER_COMMAND(UpdateAllPrimitiveSceneInfosCmd)(
        [NewWorld](FRHICommandListImmediate& RHICmdList)
        {
            NewWorld->Scene->UpdateAllPrimitiveSceneInfos(RHICmdList);
        }
    );
#endif
}

bool UMultiWorldManager::PreLoadWorld(TSoftObjectPtr<UWorld> MapAsset, const FMultiWorldLoadParameters& LoadParams, FMultiWorldHandle& OutWorldHandle)
{
    if (MapAsset.IsNull())
    {
        UE_LOG(LogMultiWorld, Error, TEXT("Invalid map name; unable to load the world."));
        return false;
    }

    if (LoadParams.WorldName != NAME_None)
    {
        // check if there is a world with that name...

        FMultiWorldHandle WorldWithInputName = GetWorldHandleByName(LoadParams.WorldName);
        if (IsValidHandle(WorldWithInputName))
        {
            UE_LOG(LogMultiWorld, Warning, TEXT("A World with name=\"%s\" already exists, this instance is returned."), *LoadParams.WorldName.ToString());

            OutWorldHandle = WorldWithInputName;

            return false;
        }

        // check if we have scheduled a world loading with that name...

        for (auto& PendingLoadWorldData : PendingLoadWorlds)
        {
            if (PendingLoadWorldData.LoadParams.WorldName == LoadParams.WorldName)
            {
                UE_LOG(LogMultiWorld, Warning, TEXT("A World with name=\"%s\" is scheduled for loading but not loaded yet. Unable to return a valid world handle."), *LoadParams.WorldName.ToString());

                OutWorldHandle = FMultiWorldHandle();

                return false;
            }
        }
    }

    return true;
}

void UMultiWorldManager::PostLoadWorld(TSoftObjectPtr<UWorld> MapAsset, const FMultiWorldLoadParameters& LoadParams, UWorld* LoadedWorld, FName PackageName)
{
    check(LoadedWorld);
    check(PackageName != NAME_None);

#if WITH_EDITOR
    // In Editor, when the LoadPackageAsync completition callback is called, 
    // it could happen that the package, despite it's marked as "fully loaded" and
    // all blueprints are compiled, they are not reistanced yet and this bring to a lot of issues 
    // (e.g when we call the BeginPlay nothing happen to these actors...).
    // This happen because the completition callback is called before calling FBlueprintSupport::FlushReinstancingQueue()
    // see FAsyncLoadingThread::ProcessLoadedPackages. This issue was found for the first time in UE 5.4 preview 1.
    // Calling FlushCompilationQueueAndReinstance seems to solve the issue.
    FBlueprintCompilationManager::FlushCompilationQueueAndReinstance();
#endif // WITH_EDITOR

    LoadedWorld->AddToRoot();
    LoadedWorld->ClearFlags(RF_Standalone);

    LoadedWorlds.AddUnique(LoadedWorld);

    PendingLoadWorlds.RemoveAll([PackageName](const FPendingLoadWorldData& InWorldData) { return InWorldData.MemoryPackageName == PackageName; });

    auto& State = WorldStates.FindOrAdd(LoadedWorld);
    State.MapAsset = MapAsset;
    State.LoadParameters = LoadParams;
    State.bShouldTickWhenInBackground = LoadParams.bStartWithTickEnabled;

    if (LoadParams.bAutoInitializeWorld)
    {
        InitializeWorld(LoadedWorld);
    }
}

void UMultiWorldManager::PlayWorld(UWorld* InWorld, const FString& URLOptions)
{
    check(InWorld);

    UWorld* CurrentWorld = GetActiveWorld();
    check(CurrentWorld);

    // Save local players input modes (they could be override by the BeginPlay of the new world)
    TMap<int, InputState> LocalPlayersInputModes;
    SaveInputModeForLocalPlayers(CurrentWorld, LocalPlayersInputModes);

    // temp overwrite the active world context
    // this is needed because some objects constructed on the BeginPlay could
    // access to the worldcontext to retrieve the World (e.g UserWidget)
    // In this way the World ptr will be the right one!
    SetActiveWorldContext(&GEngine->GetWorldContextFromWorldChecked(InWorld));

    InWorld->FlushLevelStreaming(EFlushLevelStreamingType::Visibility);

    // Build the World URL (see UEditorEngine::BuildPlayWorldURL but not used because editor only)
    FString MapName = UWorld::RemovePIEPrefix(InWorld->GetMapName());
    FString URLString(MapName);
    URLString += URLOptions;

    FURL URL(nullptr, *URLString, ETravelType::TRAVEL_Absolute);

    InWorld->SetGameMode(URL);
    InWorld->InitializeActorsForPlay(URL);

    InWorld->bWorldWasLoadedThisTick = true;

    // calling it after InitializeActorsForPlay has been called to have all potential bounding boxed initialized
    FNavigationSystem::AddNavigationSystemToWorld(*InWorld, FNavigationSystemRunMode::InferFromWorldMode);

    SpawnPlayerControllersForWorld(InWorld);
    SetLocalPlayerControllersForWorld(InWorld);

#if WITH_EDITOR
    // Gives a chance to any assets being used for PIE/game to complete
    FAssetCompilingManager::Get().ProcessAsyncTasks();
#endif

    InWorld->BeginPlay();

    // Save / Keep track of input mode for local players of the new world.
    SaveInputModeForLocalPlayers(InWorld, WorldStates.FindOrAdd(InWorld).PlayerInputStates);

    for (auto Level : InWorld->GetLevels())
    {
        for (auto Actor : Level->Actors)
        {
            InWorld->RemoveNetworkActor(Actor);
        }
    }

    SetLocalPlayerControllersForWorld(CurrentWorld);

    // restore the input mode for local players
    RestoreInputModeForLocalPlayers(CurrentWorld, LocalPlayersInputModes);

    // restore the previous context
    SetActiveWorldContext(&GEngine->GetWorldContextFromWorldChecked(CurrentWorld));
}

void UMultiWorldManager::EndAllWorldsInternal()
{
    TArray<UWorld*> LoadedWorldsCopy = LoadedWorlds;
    for (auto World : LoadedWorldsCopy)
    {
        EndWorldInternal(World);
    }

    LoadedWorlds.Empty();

    if (MainWorld)
    {
        DeleteWidgetsContainerForWorld(MainWorld);

        check(MainWorldContext);
        check(&GEngine->GetWorldContextFromWorldChecked(MainWorld) == MainWorldContext);

        // it's very important to restore the main world context (the engine expect it)
        SetActiveWorldContext(MainWorldContext);

        if (ActiveWorld != MainWorld)
        {
#if WITH_EDITOR
            if (MainWorldContext->GameViewport)
            {
                static_cast<GameViewportClientEx*>(MainWorldContext->GameViewport)->ResetWorldContext(*MainWorldContext);
            }
#endif // WITH_EDITOR
        }

#if WITH_EDITOR
        UEditorEngine* const EditorEngine = Cast<UEditorEngine>(GEngine);
        if (EditorEngine)
        {
            EditorEngine->PlayWorld = MainWorld;
        }
#endif // WITH_EDITOR

        //MainWorld->DestroyWorld(true);
        //MainWorld->MarkObjectsPendingKill();
        MainWorld = nullptr;
        ActiveWorld = nullptr;
        MainWorldContext = nullptr;
    }

    WorldStates.Empty();
}

void UMultiWorldManager::EndWorldInternal(UWorld* InWorld)
{
    check(InWorld);

    DeleteWidgetsContainerForWorld(InWorld);

    // Stop all audio to remove references to current level.
    if (FAudioDevice* AudioDevice = InWorld->GetAudioDevice().GetAudioDevice())
    {
        AudioDevice->Flush(InWorld);
    }

    // BUG: if multiple audio devices are disposed at Engine Exit (so GIsRequestingExit is true),
    // the application could crash because the xaudio2_9redist.dll is unloaded too early.
    // see Engine\Source\Runtime\Windows\AudioMixerXAudio2\Private\AudioMixerPlatformXAudio2.cpp@626 and @727
    // they said:
    // <<Work around the fact the x64 version of XAudio2_7.dll does not properly ref count by forcing it to be always loaded>>
    // But when GIsRequestingExit is true they call FreeLibrary (FMixerPlatformXAudio2::TeardownHardware()). 
    // Seems that after the SECOND hardware teardown, the dll is unloaded but the main audio device is still active...
    // As workaround we set GIsRequestingExit to false before disposing the audio device. 
    // see bug #1159
    {
        PRAGMA_DISABLE_DEPRECATION_WARNINGS
        bool bRequestingExit = GIsRequestingExit;
        GIsRequestingExit = false;

        FAudioThreadSuspendContext AudioThreadSuspendContext;

        // Release the audio device setting an invalid handle.
        // This is done even in UWorld::BeginDestroy but we force here
        // due to the issue described above.
        FAudioDeviceHandle EmptyHandle;
        InWorld->SetAudioDevice(EmptyHandle);

        GIsRequestingExit = bRequestingExit;
        PRAGMA_ENABLE_DEPRECATION_WARNINGS
    }

    // this calls BeginTearingDown() and RouteEndPlay() for each actors.
    InWorld->EndPlay(EEndPlayReason::Quit);

    InWorld->SetShouldForceUnloadStreamingLevels(true);
    InWorld->FlushLevelStreaming();
    InWorld->DestroyWorld(true);
    InWorld->MarkObjectsPendingKill();

    InWorld->RemoveFromRoot();

    GEngine->DestroyWorldContext(InWorld);

    // we have to force a "full purge" to avoid
    // any issues with world subsystem tickables that otherwise
    // are still accessed by FTickableGameObject::TickObjects despite they are marked pendingkill.
    // With a ***incremental*** GC we can incur in the scenario where the world is destroied 
    // but not the world subsystem tickable and so calling GetTickableGameObjectWorld deference a dangling pointer.
    //@see internal bug #1044 and https://udn.unrealengine.com/s/question/0D54z000094rAbNCAU/crash-looping-tickables
    //CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
    GEngine->ForceGarbageCollection(/*bForcePurge=*/true); // tick delayed

    LoadedWorlds.Remove(InWorld);
    WorldStates.Remove(InWorld);
}

TArray<UWorld*> UMultiWorldManager::FindLoadedWorldsByMapAsset(TSoftObjectPtr<UWorld> MapAsset) const
{
    TArray<UWorld*> Worlds;

    for (auto& KeyAndWorldState : WorldStates)
    {
        if (KeyAndWorldState.Value.MapAsset == MapAsset)
            Worlds.Add(KeyAndWorldState.Key);
    }

    return Worlds;
}

bool UMultiWorldManager::OnCoreTick(float DeltaSeconds)
{
    for (auto& PendingEndWorldData : PendingEndWorlds)
    {
        EndWorldInternal(PendingEndWorldData.World.Get());

        if (PendingEndWorldData.OnCompleteCallback)
        {
            PendingEndWorldData.OnCompleteCallback();
        }
    }

    LoadedWorlds = LoadedWorlds.FilterByPredicate([](UWorld* InWorld) {
        return InWorld != nullptr;
    });

    PendingEndWorlds.Empty();

    return true;
}

void UMultiWorldManager::OnWorldTickEnd(UWorld* InWorld, ELevelTick, float)
{
    if (PendingLoadWorlds.Num() > 0)
    {
        UGameInstance* GameInstance = GetGameInstance();
        check(GameInstance);

        UWorld* World = GameInstance->GetWorld(); // this get the active world.
        check(World);
        check(World->HasBegunPlay());

        TArray<FPendingLoadWorldData> PendingLoadWorldsCopy = PendingLoadWorlds; // a copy because it could be modified.
        for (FPendingLoadWorldData& PendingLoadWorldData : PendingLoadWorldsCopy)
        {
            if (PendingLoadWorldData.Type == SYNC_LOADING)
            {
                LoadWorldImpl(
                    PendingLoadWorldData.MapAsset, 
                    PendingLoadWorldData.LoadParams, 
                    PendingLoadWorldData.MemoryPackageName, 
                    PendingLoadWorldData.OnCompleteCallback);
            }
        }
    }
}

void UMultiWorldManager::OnWorldTickStart(UWorld* InWorld, ELevelTick, float)
{
#if WITH_EDITOR
    if (InWorld != MainWorld && !LoadedWorlds.Contains(InWorld))
        return;
#endif // WITH_EDITOR

    // Set the right player controller on each local player.
    SetLocalPlayerControllersForWorld(InWorld);

    // to avoid to tick latent actions multiple times (because the LatentActionManager can be the same for each world!), 
    //actions are filtered and just the actions with a reference to uobject that lives in the world in tick are preserved
    // Other actions are saved and restored at the end of the tick!

    FMultiWorldLatentActionManager& LatentActionManager = static_cast<FMultiWorldLatentActionManager&>(InWorld->GetLatentActionManager());
    if (&InWorld->GetLatentActionManager() == &GetGameInstance()->GetLatentActionManager())
    {
        FMultiWorldLatentActionManager::FObjectToActionListMap2 ThisWorldObjectToActionListMap;

        for (auto& ObjectToAction : LatentActionManager.GetObjectToActionListMap())
        {
            if (ObjectToAction.Key.IsValid())
            {
                UObject* Object = ObjectToAction.Key.Get();
                check(Object);

                if (Object->GetWorld() == InWorld)
                    ThisWorldObjectToActionListMap.Add(Object, ObjectToAction.Value);
                else
                    LatentActionsToRestoreOnPostTick.Add(Object, ObjectToAction.Value);
            }
        }

        LatentActionManager.GetObjectToActionListMap() = ThisWorldObjectToActionListMap;
    }
}

void UMultiWorldManager::OnWorldPostActorTick(UWorld* InWorld, ELevelTick, float)
{
#if WITH_EDITOR
    if (InWorld != MainWorld && !LoadedWorlds.Contains(InWorld))
        return;
#endif // WITH_EDITOR

    // merge back all other latent actions
    FMultiWorldLatentActionManager& LatentActionManager = static_cast<FMultiWorldLatentActionManager&>(InWorld->GetLatentActionManager());
    if (&InWorld->GetLatentActionManager() == &GetGameInstance()->GetLatentActionManager())
    {
        LatentActionManager.GetObjectToActionListMap().Append(LatentActionsToRestoreOnPostTick);
        LatentActionsToRestoreOnPostTick.Empty();
    }
}

#if WITH_EDITOR

void UMultiWorldManager::OnSingleStepPIE(bool)
{
    TArray<UWorld*> Worlds = LoadedWorlds;
    Worlds.Add(MainWorld);

    for (UWorld* World : Worlds)
    {
        World->bDebugFrameStepExecution = true;
        World->bDebugPauseExecution = false;
    }
}

void UMultiWorldManager::OnSwitchPIEAndSIE(bool bIsSimulating)
{
    if (bIsSimulating)
    {
        UGameViewportClient* Viewport = GEngine->GameViewportForWorld(MainWorld);
        if (Viewport)
        {
            Viewport->GetGameViewport()->SetGameRenderingEnabled(true);
        }
    }
}

void UMultiWorldManager::OnPostEditorTick(float)
{
    FixupEditorEngine();
}

void UMultiWorldManager::FixupEditorEngine()
{
    UEditorEngine* const EditorEngine = Cast<UEditorEngine>(GEngine);
    if (EditorEngine)
    {
        UWorld* CurrentWorld = GetActiveWorld();
        if (CurrentWorld)
        {
            // the editor changes the PlayWorld/GameViewport ptrs during the tick while it is iterating 
            // on the game world context list but this is wrong. Overwrite them using the current world.
            EditorEngine->PlayWorld = CurrentWorld;
            EditorEngine->GameViewport = GEngine->GameViewportForWorld(CurrentWorld);
        }
    }
}

void UMultiWorldManager::OnPIEEnded(bool)
{
   EndAllWorldsInternal();
}

#endif // WITH_EDITOR

void UMultiWorldManager::SetActiveWorldContext(FWorldContext* InWorldContext)
{
    check(InWorldContext)

    if (UGameInstance* GameInstance = GetGameInstance())
    {
        static_cast<MultiWorldGameInstanceEx*>(GameInstance)->SetWorldContext(InWorldContext);

        if (UGameViewportClient* ThisGameViewport = GameInstance->GetGameViewportClient())
        {
            static_cast<GameViewportClientEx*>(ThisGameViewport)->ResetWorldContext(*InWorldContext);
        }
    }
}

UWorld* UMultiWorldManager::GetActiveWorld() const
{
    //return GetGameInstance()->GetWorld();
    return ActiveWorld;
}

UWorld* UMultiWorldManager::GetWorldChecked(const FMultiWorldHandle& InWorldHandle, bool bActivated)
{
    UWorld* InWorld = InWorldHandle.World;
    bool bIsValid = InWorld && (LoadedWorlds.FindByKey(InWorld) || InWorld == GetMainWorldHandle().World);

    if (!bIsValid)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Input WorldHandle is not valid, aborted..."));
        return nullptr;
    }

    if (bActivated && !InWorldHandle.IsActivated())
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Input WorldHandle is not activated, you have to call InitializeWorld() before; aborted..."));
        return nullptr;
    }

    return InWorld;
}

void UMultiWorldManager::EndWorld(const FMultiWorldHandle& InWorldHandle, TFunction<void()> OnCompleteCallback)
{
    if (InWorldHandle == GetMainWorldHandle())
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("EndWorld can't be called on the main world; aborted..."));
        
        // always call the callback even in case of error
        if (OnCompleteCallback) 
            OnCompleteCallback();
        return;
    }

    if (InWorldHandle == GetActiveWorldHandle())
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("EndWorld is been called on the active world; Automatically switched to the main world."));
        
        ReturnToMainWorld();
    }

    if (UWorld* World = GetWorldChecked(InWorldHandle, false))
    {
        OnPreWorldEnded.Broadcast(InWorldHandle);

        // Stop ticking now
        // For how it's implemented ticking in EditorEngine (PIE), 
        // it's important to stop the world before deleting it/removing its world context
        // even if this task is postponed.
        World->SetShouldTick(false);

        // it's not safe to delete a world/removing its world context in a tick function
        // the world will be deleted outside the tick function later.
        FPendingEndWorldData PendingEndWorldData;
        PendingEndWorldData.World = World;
        PendingEndWorldData.OnCompleteCallback = OnCompleteCallback;
        PendingEndWorlds.AddUnique(PendingEndWorldData);
    }
    else
    {       
        // always call the callback even in case of error
        if (OnCompleteCallback)
            OnCompleteCallback();
    }
}

void UMultiWorldManager::EndAllWorlds(TFunction<void()> OnCompleteCallback)
{
    auto OnCompleteInternal = [this, OnCompleteCallback]() {
        if (LoadedWorlds.Num() == 0)
        {
            if (OnCompleteCallback)
            {
                OnCompleteCallback();
            }
        }
    };

    ForEachSecondaryWorld([&](UWorld* InWorld) {
        EndWorld(InWorld, OnCompleteInternal);
    });
}

void UMultiWorldManager::SetShouldTickWhenInBackground(const FMultiWorldHandle& InWorldHandle, bool bShouldTick)
{
    UWorld* InWorld = GetWorldChecked(InWorldHandle, false);
    if (!InWorld)
        return;

    auto& State = WorldStates.FindOrAdd(InWorld);
    State.bShouldTickWhenInBackground = bShouldTick;

    InWorld->SetShouldTick(bShouldTick);
}

void UMultiWorldManager::SetAutoHandleWidgetsForMainWorld(bool bAutoHandleWidgets)
{
    auto& State = WorldStates.FindOrAdd(MainWorld);
    State.LoadParameters.bAutoHandleWidgets = bAutoHandleWidgets;
}

void UMultiWorldManager::SetAutoHandleInputModeForMainWorld(bool bAutoHandleInputMode)
{
    auto& State = WorldStates.FindOrAdd(MainWorld);
    State.LoadParameters.bAutoHandleInputMode = bAutoHandleInputMode;
}

bool UMultiWorldManager::SwitchWorld(const FMultiWorldHandle& InWorldHandle)
{
    UWorld* NewWorld = GetWorldChecked(InWorldHandle, true);
    if (!NewWorld)
        return false;

    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    UWorld* CurrentWorld = GetActiveWorld();
    check(CurrentWorld);

    if (CurrentWorld != NewWorld
        && ensure(NewWorld))
    {
        UE_LOG(LogMultiWorld, Log, TEXT("Moving from %s to %s"), *CurrentWorld->GetName(), *NewWorld->GetName());
        
        // flush pressed keys otherwise if a key is released when we have already moved on the other world
        // the event is lost.
        // e.g. the W key is pressed, the pawn moves forward. if the world is switched before the W key is released,
        // the pawn continue to move and don't stop.
        for (FConstPlayerControllerIterator iter = CurrentWorld->GetPlayerControllerIterator(); iter; ++iter)
        {
            APlayerController* playerController = iter->Get();
            if (playerController->IsLocalPlayerController())
            {
                playerController->PlayerInput->FlushPressedKeys();
            }
        }

        auto& CurrentWorldState = WorldStates.FindOrAdd(CurrentWorld);

        // Save the input mode of all local players so when we return back to this world we can restore it
        //if (CurrentWorldState.LoadParameters.bAutoHandleInputMode) // regardless the flag ALWAYS keep track
        {
            SaveInputModeForLocalPlayers(CurrentWorld, CurrentWorldState.PlayerInputStates);
        }

        CurrentWorld->SetShouldTick(CurrentWorldState.ShouldTickWhenInBackground());
        NewWorld->SetShouldTick(true);

        for (FActorIterator It(CurrentWorld); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor->GetClass()->ImplementsInterface(UMultiWorldActorInterface::StaticClass()))
            {
                IMultiWorldActorInterface::Execute_OnExitingWorld(Actor);
            }
        }

        FWorldContext* ToWorldContext = (NewWorld == MainWorld) 
            ? MainWorldContext : &GEngine->GetWorldContextFromWorldChecked(NewWorld);
        FWorldContext* FromWorldContext = GameInstance->GetWorldContext();

        HandleViewportWidgetsVisibility(CurrentWorld, NewWorld);

        ActiveWorld = NewWorld;

        SetActiveWorldContext(ToWorldContext);

        ActivateAudioDeviceForWorld(NewWorld);

        // this is needed for the callback below that it's done on actors of the new world.
        SetLocalPlayerControllersForWorld(NewWorld);

        for (FActorIterator It(NewWorld); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor->GetClass()->ImplementsInterface(UMultiWorldActorInterface::StaticClass()))
            {
                IMultiWorldActorInterface::Execute_OnEnteringWorld(Actor);
            }
        }

        auto& WorldState = WorldStates.FindOrAdd(NewWorld);

        // Restore InputMode for local players.
        if (WorldState.LoadParameters.bAutoHandleInputMode)
        {
            RestoreInputModeForLocalPlayers(NewWorld, WorldState.PlayerInputStates);
        }

        // restore the PC of the local player: we have switched the world but we are still
        // in the old world tick...the PC will be updated on the tick start of each world.
        SetLocalPlayerControllersForWorld(CurrentWorld);

        // request a rebuild of control mappings. (see bug #981)
        for (auto LocalPlayer : GetLocalPlayers())
        {
            if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(LocalPlayer))
            {
                FModifyContextOptions Options;
                Options.bForceImmediately = true;
                Subsystem->RequestRebuildControlMappings(Options);
            }
        }

        // WARNING: this delegate, as others, can be catched on every worlds regardless of which world is ticking. 
        // Be aware that in this scenario, with UE5.0, calling UGameplayStatics::GetPlayerController 
        // could returns the wrong player controller (in this case you can use UGameplayStatics::GetPlayerState()->GetPlayerController() ).
        FMultiWorldHandle PreviousWorldHandle{ CurrentWorld };
        OnWorldSwitched.Broadcast(PreviousWorldHandle, InWorldHandle);

        return true;
    }

    return false;
}

void UMultiWorldManager::RequestSwitchWorld(const FMultiWorldHandle& InWorldHandle, TFunction<void(bool)> OnSwitchWorldCompleted)
{
    FTSTicker::GetCoreTicker().AddTicker(TEXT("SwitchWorldDeferredTicker"), 0.0f, [this, InWorldHandle, OnSwitchWorldCompleted](float DeltaTime) -> bool
        {
            const bool bResult = SwitchWorld(InWorldHandle);
            OnSwitchWorldCompleted(bResult);
            return false;
        });
}

bool UMultiWorldManager::ReturnToMainWorld()
{
    return SwitchWorld(GetMainWorldHandle());
}

FMultiWorldHandle UMultiWorldManager::GetWorldHandleByName(FName WorldName) const
{
    auto SearchWorldByName = [&](FName InName) -> UWorld*
    {
        for (auto& ws : WorldStates)
        {
            if (ws.Value.LoadParameters.WorldName.IsEqual(InName))
                return ws.Key;
        }
        return nullptr;
    };
    
    UWorld* World = SearchWorldByName(WorldName);

    return FMultiWorldHandle{ World };
}

FMultiWorldHandle UMultiWorldManager::GetThisWorldHandle(const UObject* WorldContextObject) const
{
    return Cast<UWorld>(WorldContextObject->GetWorld());
}

FMultiWorldHandle UMultiWorldManager::GetActiveWorldHandle() const
{
    return GetActiveWorld();
}

bool UMultiWorldManager::IsValidHandle(const FMultiWorldHandle& InWorldHandle) const
{
    for (auto LocalWorld : LoadedWorlds)
    {
        if (LocalWorld == InWorldHandle.World)
            return true;
    }

    return GetMainWorldHandle() == InWorldHandle;
}

void UMultiWorldManager::TransferActorToWorld(
	AActor* InActor,
	const FMultiWorldHandle& InWorldHandle,
	const FMultiWorldTransferActorParameters & Options
)
{
    UWorld* DestinationWorld = GetWorldChecked(InWorldHandle, true);
    if (!DestinationWorld)
        return;

    if (!InActor)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Invalid InActor, the actor to move can't be null."));
        return;
    }

    if (InActor->GetWorld() == DestinationWorld)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("InActor is already located on the destination world."));
        return;
    }

    if (InActor->IsA<APawn>() && Cast<APawn>(InActor)->IsPlayerControlled())
    {
        UE_LOG(LogMultiWorld, Error, TEXT("A Pawn actor controlled by a player cannot be transferred."));
        return;
    }

    UWorld* StartWorld = InActor->GetWorld();

    OnPreActorTransferred.Broadcast(InActor, StartWorld, DestinationWorld);

    if (InActor->Implements<UMultiWorldActorInterface>())
    {
        IMultiWorldActorInterface::Execute_OnPreTransferredToWorld(InActor, StartWorld, DestinationWorld);
    }

    auto OldOuter = InActor->GetOuter();
    auto NewOuter = DestinationWorld->GetCurrentLevel();

    // Find (recursively) all references inside the input actor, that have the same direct outer.
	// These are the objects that must change the owner (i.e. transferred into another level).
	TArray<UObject*> OutReferences;
    FReferenceFinder{ 
        OutReferences, // InObjectArray
        OldOuter,       // InOuter
        true,         // bInRequireDirectOuter
        true,          // bInShouldIgnoreArchetype
        true,          // bInSerializeRecursively
        false          // bInShouldIgnoreTransient
    }.FindReferences(InActor);

	{
		FScopePhysicsConstraintsReregistrationFix PhysicsContraintsFixer(InActor, OutReferences);

		// Move the actor to the new world updating the outer
		InActor->Rename(nullptr, NewOuter, REN_None);

		// Move the inner references too
		for (auto Ref : OutReferences)
		{
			Ref->Rename(nullptr, NewOuter, REN_None);
		}
	}

	if (Options.bSetPhysicsActorTransform && Options.Transform.IsValid())
	{
		UMultiWorldStatics::SetPhysicsActorTransform(InActor, Options.Transform, Options.Teleport);
	}

    if (InActor->Implements<UMultiWorldActorInterface>())
    {
        IMultiWorldActorInterface::Execute_OnPostTransferredToWorld(InActor, StartWorld, DestinationWorld);
    }

    OnPostActorTransferred.Broadcast(InActor, StartWorld, DestinationWorld);
}

AActor* UMultiWorldManager::SpawnActorInWorld(
    TSubclassOf<class AActor> ActorClass,
    const FMultiWorldHandle& InWorldHandle,
    const FTransform& SpawnTransform,
    ESpawnActorCollisionHandlingMethod CollisionHandlingOverride,
    AActor* Owner)
{
    UWorld* DestinationWorld = GetWorldChecked(InWorldHandle, true);
    if (!DestinationWorld)
        return nullptr;

    if (!ActorClass)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Invalid InActorClass, the actor class can't be null."));
        return nullptr;
    }

    if (Owner && Owner->GetWorld() != DestinationWorld)
    {
        UE_LOG(LogMultiWorld, Warning, TEXT("Invalid Owner, the owner's world should match the world of the new spawned actor."));
        return nullptr;
    }

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = CollisionHandlingOverride;
    Params.Owner = Owner;

    return DestinationWorld->SpawnActor(ActorClass, &SpawnTransform, Params);
}

void UMultiWorldManager::FixUpLocalPlayers()
{
    // if the UE loads a new Main World while we are in a secondary world,
    // playercontrollers of ULocalPlayer(s) are set to the new world.
    // we want to avoid this because the active world is not changed!
    if (ActiveWorld)
    {
        bool InvalidPlayerControllers = false;

        for (auto LocalPlayer : GetLocalPlayers())
        {
            InvalidPlayerControllers |= (LocalPlayer->PlayerController
                && LocalPlayer->PlayerController->GetWorld() != ActiveWorld);
        }

        if(InvalidPlayerControllers)
            SetLocalPlayerControllersForWorld(ActiveWorld);
    }
}

const TArray<class ULocalPlayer*>& UMultiWorldManager::GetLocalPlayers() const
{
    return GetGameInstance()->GetLocalPlayers();
}

void UMultiWorldManager::SpawnPlayerControllersForWorld(UWorld* InWorld)
{
    FURL URL;
    FString OutError;
    for (auto LocalPlayer : GetLocalPlayers())
    {
        // SpawnPlayActor overwrite the LocalPlayer PC but we don't want it!
        // backup the current player controller
        auto OldPC = LocalPlayer->PlayerController;

        // Temp clear all delegates to LocalPlayer's OnPlayerControllerChanged because otherwise ALL widgets that live on other worlds
        // are notified that the local player PC has changed and this set the wrong local player /PC on these widgets
        // see internal bug #1748 and commit https://github.com/EpicGames/UnrealEngine/commit/25daabb3d92f7030e00ba9095f08b80163ac972c
        ULocalPlayer::FOnPlayerControllerChanged OnPlayerControllerChangedDelegatesCopy = LocalPlayer->OnPlayerControllerChanged();
        LocalPlayer->OnPlayerControllerChanged().Clear();

        LocalPlayer->SpawnPlayActor(URL.ToString(), OutError, InWorld);

        auto NewPC = LocalPlayer->PlayerController;
        InWorld->RemoveNetworkActor(NewPC);

        // Restore delegates
        LocalPlayer->OnPlayerControllerChanged() = MoveTemp(OnPlayerControllerChangedDelegatesCopy);

        // restore the player controller
        LocalPlayer->PlayerController = OldPC;
    }
}

void UMultiWorldManager::SetLocalPlayerControllersForWorld(UWorld* InWorld)
{
#if WITH_EDITOR
    // editor worlds are ticked too, skip them.
    if (InWorld->WorldType != EWorldType::PIE && InWorld->WorldType != EWorldType::Game)
        return;

    check(InWorld == MainWorld || LoadedWorlds.Contains(InWorld));
#endif // WITH_EDITOR

    for (auto LocalPlayer : GetLocalPlayers())
    {
        if (LocalPlayer->PlayerController == nullptr)// || LocalPlayer->PlayerController->GetWorld() == InWorld)
            continue;

        APlayerController* PlayerController = UGameplayStatics::GetPlayerControllerFromID(InWorld, LocalPlayer->GetControllerId());
        if (PlayerController)
        {
            LocalPlayer->PlayerController = PlayerController;
        }
        else
        {
            UE_LOG(LogMultiWorld, Warning, TEXT("Unable to find the player controller for the local player with id=%d"), LocalPlayer->GetControllerId());
        }
    }
}

void UMultiWorldManager::ActivateAudioDeviceForWorld(UWorld* InWorld)
{
    check(MainWorld);

    UGameInstance* GameInstance = GetGameInstance();
    check(GameInstance);

    FAudioDeviceManager* AudioDeviceManager = GEngine->GetAudioDeviceManager();
    if (AudioDeviceManager)
    {
        AudioDeviceManager->SetActiveDevice(InWorld->GetAudioDevice().GetDeviceID());

        if (UGameViewportClient* ThisGameViewport = GameInstance->GetGameViewportClient())
        {
            static_cast<GameViewportClientEx*>(ThisGameViewport)->SetAudioDevice(InWorld->GetAudioDevice());
        }
    }
}
