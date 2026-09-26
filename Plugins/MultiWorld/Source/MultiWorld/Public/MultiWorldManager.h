// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "Subsystems/GameInstanceSubsystem.h"
#include "Tickable.h"
#include "Containers/Ticker.h"

#include "MultiWorldHandle.h"

#include "Engine/LatentActionManager.h"

#include "MultiWorldManager.generated.h"

class SWidget;
class SOverlay;
class UUserWidget;

/** Available input modes. see FInputModeUIOnly/FInputModeGameOnly/FInputModeGameAndUI */
UENUM()
enum class EMultiWorldInputMode : uint8
{
    UIOnly,
    GameOnly,
    GameAndUI
};


class FMultiWorldLatentActionManager : public FLatentActionManager
{
public:

    typedef FLatentActionManager::FObjectToActionListMap FObjectToActionListMap2;

    FObjectToActionListMap2& GetObjectToActionListMap()
    {
        return ObjectToActionListMap;
    }
};

/** Collect all parameters to pass to the UMultiWorldStatics::LoadWorld() function. */
USTRUCT(BlueprintType)
struct MULTIWORLD_API FMultiWorldLoadParameters
{
    GENERATED_BODY()

    /** 
     * Optional name, useful to associate a human readable name to a world's handle.
     * The name, if not NONE, must be UNIQUE. Consecutive calls to LoadWorld/LoadWorldAsync
     * with the same name returns the world associated with that name if already loaded or fail otherwise. 
     * This field is even used to search for worlds by name (see GetWorldHandleByName)
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    FName WorldName;

    /**
     * An optional string of options like the one passed to the OpenLevel function.
     * e.g `?Game=<GameModeClass>` to override the game mode.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    FString URLOptions;

    /**
     * Sets whenever the InputMode must be handled and restored for this world automatically. True by default.
     * In Unreal Engine the Input Mode is defined globally and so "leaks" between worlds.
     * If AutoHandleInputMode is true, the plugin save the actual input mode when we leave the world
        and restore it when we return back to that world.
       UMultiWorldStatics::SetAutoHandleInputModeForMainWorld can be used to set the behavior for the Main World.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bAutoHandleInputMode = true;

    /**
     * Should the world be initialized automatically or not.
     * If not, UMultiWorldStatics::InitializeWorld() must be called before using the world.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bAutoInitializeWorld = true;

    /**
     * Should the loaded world tick at start.
     * UMultiWorldStatics::SetShouldTickWhenInBackground() can be used at run-time to change the setting later.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bStartWithTickEnabled = false;

    /**
     * Should the UMG world widgets be handled automatically or not (shown when the world is active, hidden when the world is not).
     * UMultiWorldStatics::SetAutoHandleWidgetsForMainWorld() can be used to set the behavior of the Main World.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bAutoHandleWidgets = true;

    /** Should be created a new dedicated audio device. Otherwise the audio device of the main world is used. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bCreateDedicatedAudioDevice = true;

    /** When set the world is loaded in a package with the strict naming convention used by the engine (if not used yet).
        Sometimes this is important because some subsystems required it (like the Level Sequencer). This can be done just the first
        time the map is loaded and only if the same map is not already loaded by the engine as main world.
        Normally you don't have to change this flag exept if you want that the engine is able to load a map already loaded as secondary world.
    */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
    bool bUseStrictPackageNameWhenPossible = true;
};



/** Options for UMultiWorldStatics::TransferActorToWorld(). */
USTRUCT(BlueprintType)
struct MULTIWORLD_API FMultiWorldTransferActorParameters
{
	GENERATED_BODY()

	/** If enabled, after the transfert set the actor transform to the value in Transform. Default: false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
	bool bSetPhysicsActorTransform;
	/** If bSetPhysicsActorTransform is enabled, the final actor transform. Default: unset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MultiWorld|Settings")
	FTransform Transform;
	/** If bSetPhysicsActorTransform is enabled, how we teleport the physics state (see AActor::SetActorTransform()). Default: ETeleportType::ResetPhysics. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, AdvancedDisplay, Category = "MultiWorld|Settings")
	ETeleportType Teleport;
	
    /// Default constructor.
	FMultiWorldTransferActorParameters();

    /**
     * Constructor.
     * 
     * @param InTransform Initialization value for #bSetPhysicsActorTransform (set to InTransform.IsValid()) and #Transform.
     * @param InTeleport Initialization value for Teleport.
     */
	FMultiWorldTransferActorParameters(const FTransform & InTransform, ETeleportType InTeleport);

    /**
     * Set both #bSetPhysicsActorTransform (to NewTransform.IsValid()) and #Transform.
     * @param NewTransform The new value for Transform.
     */
	void SetTransform(const FTransform & NewTransform);
};



/** OnLoadWorldCompleted delegate signature */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnLoadWorldCompletedDelegate, bool, Success, FMultiWorldHandle, WorldHandle, FMultiWorldLoadParameters, LoadParams);

/** like FOnLoadWorldCompletedDelegate but not multicast. It can be used as param on blueprint functions. */
DECLARE_DYNAMIC_DELEGATE_ThreeParams(FOnLoadWorldCompletedDelegateSimple, bool, Success, FMultiWorldHandle, WorldHandle, FMultiWorldLoadParameters, LoadParams);

/** OnEndWorldCompleted delegate signature */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnEndWorldCompletedDelegate);

/** like FOnEndWorldCompletedDelegate but not multicast. It can be used as param on blueprint functions. */
DECLARE_DYNAMIC_DELEGATE(FOnEndWorldCompletedDelegateSimple);

/** OnActorTransferred delegate signature */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnActorTransferredDelegate, AActor*, Actor, UWorld*, OldWorld, UWorld*, NewWorld);

/**
 * The subsystem of the MultiWorld plugin.
 */
UCLASS()
class MULTIWORLD_API UMultiWorldManager : public UGameInstanceSubsystem, public FTickableGameObject
{
    GENERATED_BODY()

public:

    /**
     * Return the multi world manager instance.
     */
    static UMultiWorldManager & GetInstance(const UObject * context);

    /** Override USubsystem::ShouldCreateSubsystem */
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override;

    /** Override USubsystem::Initialize */
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /** Override USubsystem::Deinitialize */
    virtual void Deinitialize() override;

    // Begin FTickableGameObject Interface.
    virtual void Tick(float DeltaTime) override;    ///< Override
    virtual bool IsTickable() const override;       ///< Override
    virtual TStatId GetStatId() const override;     ///< Override
    // End FTickableGameObject Interface.

public:

    /** FOnWorldSwitched delegate signature */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWorldSwitched, FMultiWorldHandle, PreviousWorld, FMultiWorldHandle, CurrentWorld);

    /** FOnPreEndWorld delegate signature */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPreEndWorld, FMultiWorldHandle, WorldToEnd);

    /**
     * Delegate called when the world load has terminated.
     */
    UPROPERTY(BlueprintAssignable)
    FOnLoadWorldCompletedDelegate OnLoadWorldCompleted;

    /**
     * Delegate called when the world is switched.
     */
    UPROPERTY(BlueprintAssignable)
    FOnWorldSwitched OnWorldSwitched;

    /**
     * Delegate called before the world is ended.
     */
    UPROPERTY(BlueprintAssignable)
    FOnPreEndWorld OnPreWorldEnded;

    /**
     * Delegate called before an actor is transferred to a different world from the one he lives.
     */
    UPROPERTY(BlueprintAssignable)
    FOnActorTransferredDelegate OnPreActorTransferred;

    /**
     * Delegate called after an actor is transferred to a different world from the one he lives.
     */
    UPROPERTY(BlueprintAssignable)
    FOnActorTransferredDelegate OnPostActorTransferred;

public:

    /**
    Synchronously load a World into memory.
    
    This method works like UMultiWorldStatics::LoadWorldWithDelegate(), but uses a C++ completion callback instead of a delegate.
    */
	void LoadWorld(TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters InParams, TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback);
    /**
    Asynchronously load a World into memory.
    
    This method works like UMultiWorldStatics::LoadWorldAsyncWithDelegate(), but uses a C++ completion callback instead of a delegate.
    */
    void LoadWorldAsync(TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters InParams, TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback);
    /** @copydoc UMultiWorldStatics::InitializeWorld **/
    void InitializeWorld(const FMultiWorldHandle& InWorldHandle);
    /** @copydoc UMultiWorldStatics::EndWorld */
    void EndWorld(const FMultiWorldHandle& InWorldHandle, TFunction<void()> OnCompleteCallback);
    /** @copydoc UMultiWorldStatics::EndAllWorlds */
    void EndAllWorlds(TFunction<void()> OnCompleteCallback);
    /** @copydoc UMultiWorldStatics::SetShouldTickWhenInBackground */
    void SetShouldTickWhenInBackground(const FMultiWorldHandle& InWorldHandle, bool bShouldTick);
	/** @copydoc UMultiWorldStatics::SetAutoHandleWidgetsForMainWorld */
    void SetAutoHandleWidgetsForMainWorld(bool bAutoHandleWidgets);
    /** @copydoc UMultiWorldStatics::SetAutoHandleInputModeForMainWorld */
    void SetAutoHandleInputModeForMainWorld(bool bAutoHandleWidgets);
    /** @copydoc UMultiWorldStatics::SwitchWorld */
    bool SwitchWorld(const FMultiWorldHandle& InWorldHandle);
    /** @copydoc UMultiWorldStatics::RequestSwitchWorld */
    void RequestSwitchWorld(const FMultiWorldHandle& InWorldHandle, TFunction<void(bool)> OnSwitchWorldCompleted);
    /** @copydoc UMultiWorldStatics::ReturnToMainWorld */
    bool ReturnToMainWorld();

    /** @copydoc UMultiWorldStatics::GetMainWorldHandle */
    FMultiWorldHandle GetMainWorldHandle() const { return MainWorld ? MainWorld : GetWorld(); }

    /** @copydoc UMultiWorldStatics::GetWorldHandleByName */
    FMultiWorldHandle GetWorldHandleByName(FName WorldName) const;

    /** @copydoc UMultiWorldStatics::GetThisWorldHandle */
    FMultiWorldHandle GetThisWorldHandle(const UObject* WorldContextObject) const;
    /** @copydoc UMultiWorldStatics::GetActiveWorldHandle */
    FMultiWorldHandle GetActiveWorldHandle() const;
    /** @copydoc UMultiWorldStatics::IsValidHandle */
    bool IsValidHandle(const FMultiWorldHandle& InWorldHandle) const;

    /** @copydoc UMultiWorldStatics::TransferActorToWorld */
    void TransferActorToWorld(AActor* InActor, const FMultiWorldHandle& InWorldHandle, const FMultiWorldTransferActorParameters & Options);
    /** @copydoc UMultiWorldStatics::SpawnActorInWorld */
    AActor* SpawnActorInWorld(TSubclassOf<class AActor> ActorClass,
        const FMultiWorldHandle& InWorldHandle,
        const FTransform& SpawnTransform,
        ESpawnActorCollisionHandlingMethod CollisionHandlingOverride,
        AActor* Owner);

    /** Check local player setup and fixup if it's invalid. It must be invoked by UGameViewportClient::LayoutPlayers */
    void FixUpLocalPlayers();

    /** Utility to "visit" all loaded worlds. The predicate function is called for each loaded world. */
    void ForEachSecondaryWorld(TFunction<void(UWorld*)> Predicate)
    {
        TArray<UWorld*> LoadedWorldsCopy = LoadedWorlds; // copy the array to avoid to any modifications when iterating.
        for (UWorld* SecondaryWorld : LoadedWorldsCopy)
        {
            if (SecondaryWorld)
            {
                Predicate(SecondaryWorld);
            }
        }
    }

private:

    // true if we can continue to load a new world, false otherwise and the OutWorldHandle should be returned
    bool PreLoadWorld(TSoftObjectPtr<UWorld> MapAsset, const FMultiWorldLoadParameters& LoadParams, FMultiWorldHandle& OutWorldHandle);
    void PostLoadWorld(TSoftObjectPtr<UWorld> MapAsset, const FMultiWorldLoadParameters& LoadParams, UWorld* LoadedWorld, FName PackageName);

    void LoadWorldImpl(TSoftObjectPtr<UWorld> MapAsset, FMultiWorldLoadParameters LoadParams, FName InMemoryPackageName, TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback);

    void PlayWorld(UWorld* InWorld, const FString& URLOptions);
    void EndWorldInternal(UWorld* InWorld);
    void EndAllWorldsInternal();

    TArray<UWorld*> FindLoadedWorldsByMapAsset(TSoftObjectPtr<UWorld> MapAsset) const;

    /**
     * Callback from the world context when the world changes
     * This function must be invoked by the game instance (@see UGameInstance::OnWorldChanged)
     */
    void OnWorldChanged(UWorld* OldWorld, UWorld* NewWorld);

    // Call all delegates when a world load is completed (successfully or not). 
    void NotifyLoadWorldCompleted(
        bool Success, 
        FMultiWorldHandle WorldHandle, 
        const FMultiWorldLoadParameters& LoadParams,
        TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback);

	// To call OnWorldChanged().
	friend class UMultiWorldOverrides;

private:

    const TArray<class ULocalPlayer*>& GetLocalPlayers() const;

private:

    void SpawnPlayerControllersForWorld(UWorld* InWorld);
    void SetLocalPlayerControllersForWorld(UWorld* InWorld);

    void ActivateAudioDeviceForWorld(UWorld* InWorld);

    bool OnCoreTick(float DeltaSeconds);
    void OnWorldTickEnd(UWorld*, ELevelTick, float);
    void OnWorldTickStart(UWorld*, ELevelTick, float);
    void OnWorldPostActorTick(UWorld*, ELevelTick, float);

#if WITH_EDITOR
    void OnPostEditorTick(float);
    void OnSingleStepPIE(bool);
    void OnSwitchPIEAndSIE(bool);
    void OnPIEEnded(bool);   
    void FixupEditorEngine();
#endif // WITH_EDITOR

    void SetActiveWorldContext(FWorldContext* InWorldContext);

    UWorld* GetActiveWorld() const;

    UWorld* GetWorldChecked(const FMultiWorldHandle& InWorldHandle, bool bActivated);

    UWorld* GetWorldFromPackage(UPackage* InWorldPackage);

    FName FindUniquePackageName(const FString& DiskPackageName, int PIEInstance, bool bUseStandardPackageNameWhenPossible) const;

    static class UUserWidget* GetUserWidget(TSharedRef<class SWidget> InWidget);
    bool ShouldHandleWidgetsForWorld(UWorld* World);
    void AddViewportWidgetContent(TSharedRef<class SWidget> InWidget, int32 ZOrder);
    void RemoveViewportWidgetContent(TSharedRef<class SWidget> InWidget);
    void HandleViewportWidgetsVisibility(UWorld* FromWorld, UWorld* ToWorld);
    TSharedPtr<class SOverlay> GetWidgetsContainerForWorld(UWorld* World, bool bCreateIfNull);
    void DeleteWidgetsContainerForWorld(UWorld* World);

    struct InputState
    {
        EMultiWorldInputMode InputMode;
        EMouseCaptureMode MouseCaptureMode;
        EMouseLockMode MouseLockMode;
    };

    void SaveInputModeForLocalPlayers(UWorld* World, TMap<int32, InputState>& PlayerInputStateMap);
    void RestoreInputModeForLocalPlayers(UWorld* World, const TMap<int32, InputState>& PlayerInputStateMap);

    void SaveInputMode(APlayerController* PC, InputState& is);
    void RestoreInputMode(APlayerController* PC, const InputState& is);

private:

    // the main world, handled by UE and not by this plugin!
    UPROPERTY(Transient)
    UWorld* MainWorld = nullptr;

    // the active world (the world in play/rendering)
    UPROPERTY(Transient)
    UWorld* ActiveWorld = nullptr;

    // the context of the main world
    // @note it's a "raw" pointer cos FWorldContext is not an UObject, 
    // this ptr is always aligned with the MainWorld (@see OnWorldChanged)
    FWorldContext* MainWorldContext = nullptr;

    // the list of loaded worlds
    // @note We track "raw" pointers as loaded worlds objects are added to root.
    TArray<UWorld*> LoadedWorlds;

    // All needed data saved when we schedule an end world.
    struct FPendingEndWorldData
    {
        TWeakObjectPtr<UWorld> World;
        TFunction<void()> OnCompleteCallback;

        friend bool operator==(const FPendingEndWorldData& a, const FPendingEndWorldData& b)
        {
            return a.World == b.World;
        }
    };

    // list of worlds to be deleted
    TArray<FPendingEndWorldData> PendingEndWorlds;

    // private data collection about a world
    struct WorldState
    {
        TSoftObjectPtr<UWorld> MapAsset;
        FMultiWorldLoadParameters LoadParameters;
        TOptional<bool> bShouldTickWhenInBackground;
        TMap<int32, InputState> PlayerInputStates; // ControllerId -> InputState
        TSharedPtr<SOverlay> WidgetsContainer;

        bool ShouldTickWhenInBackground() const
        {
            if (bShouldTickWhenInBackground.IsSet())
                return bShouldTickWhenInBackground.GetValue();
            else
                return true;
        }
    };

    // a map to keep track of some useful data for each world
    // @note it's safe to have a raw ptr here as the ptr is never dereferenced, it's used as a key
    // and when a world is deleted the relative entry is removed from the map.
    TMap<UWorld*, WorldState> WorldStates;

    FMultiWorldLatentActionManager::FObjectToActionListMap2 LatentActionsToRestoreOnPostTick;

    FTSTicker::FDelegateHandle OnCoreTickDelegateHandle;

    // The type of loading (sync or async)
    enum ELoadWorldType
    {
        SYNC_LOADING,
        ASYNC_LOADING
    };

    // All needed data saved when we have scheduled a world load.
    struct FPendingLoadWorldData
    {
        // the type of loading (sync or async)
        // NOTE: the sync loading is postponed (so deferred) if the LoadSync function
        // is called before the MainWorld's BeginPlay. 
        // This is the reason why a synchronous loading can not be synchronous for real.
        ELoadWorldType Type;

        // the map asset to load
        TSoftObjectPtr<UWorld> MapAsset;

        // loaded parameters with which we have scheduled the load
        FMultiWorldLoadParameters LoadParams;

        // package name where the map asset will be loaded in memory
        FName MemoryPackageName;

        // Callback to call when the loading is completed.
        TFunction<void(bool, FMultiWorldHandle, FMultiWorldLoadParameters)> OnCompleteCallback;
    };

    // The collection of all scheduled loading (sync or async)
    TArray<FPendingLoadWorldData> PendingLoadWorlds;
};
