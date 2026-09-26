// Copyright 2019-2020 UNAmedia. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MultiWorldManager.h"

#include "Engine/GameInstance.h"

#include "MultiWorldStatics.generated.h"

/**
Static class with MultiWorld functions that can be called from both Blueprint and C++.

Few extra features (mainly *Delegates*) are available using the UMultiWorldManager subsystem.
*/
UCLASS()
class MULTIWORLD_API UMultiWorldStatics : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:

	// = Forwards to UMultiWorldManager =

	/**
    Synchronously load a World into memory.

    This is a blocking call, that do most of its job in the game thread
    and completes its activity before the end of the current engine frame.
    To guarantee a proper initialization of the loaded UWorld, some initializations
    could have to be deferred later in the current engine frame.
    The @a OnComplete callback will be called as soon as the initialization is done.

    In particular, if this method is called during the @a BeginPlay of the current world (aka the Active World),
    the @a OnComplete callback will be activated soon after the @a BeginPlay ends.

    @attention Be aware that the loaded world exists only on the local client and is not replicated.
	
	@param[in] WorldContextObject the world context object
    @param InMapAsset the map asset where the World is located.
    @param InParams optional params to customize the loading.
    @param OnComplete delegate called on loading complete.

    @see UMultiWorldManager::LoadWorldAsync() or LoadWorldAsyncWithDelegate() to load a world asynchronously.
    @see FMultiWorldLoadParameters to customize the loading.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void LoadWorldWithDelegate(const UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams, FOnLoadWorldCompletedDelegateSimple OnComplete);

	/**
    Asynchronously load a World into memory.

    The map and related assets are loaded asynchronously, using [LoadPackageAsync()](https://docs.unrealengine.com/5.1/en-US/API/Runtime/CoreUObject/UObject/LoadPackageAsync/).

    In addition to the @a OnComplete delegate, you can also use the delegate UMultiWorldManager::OnLoadWorldCompleted to be notified when the load is completed.

    @attention @parblock Be aware that the loaded world exists only on the local client and is not replicated. @endparblock

    @attention @parblock To load data asynchronously, the project setting <em>"Async Loading Thread Enabled"</em> **MUST** be enabled
    (under section <em>"Engine - Streaming"</em>) and project data **MUST** be cooked.

    You can also enable the flag adding in `DefaultEngine.ini`:
    ```{.ini}
    [/Script/Engine.StreamingSettings]
    s.AsyncLoadingThreadEnable=true
    ```
    @endparblock

	@param[in] WorldContextObject the world context object
    @param InMapAsset the map asset where the World is located.
    @param InParams optional params to customize the loading.
    @param OnComplete delegate called on loading complete.
    
    @see UMultiWorldManager::LoadWorld() or LoadWorldWithDelegate() to load a world synchronously.
    @see FMultiWorldLoadParameters to customize the loading.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void LoadWorldAsyncWithDelegate(const UObject* WorldContextObject, TSoftObjectPtr<UWorld> InMapAsset, FMultiWorldLoadParameters InParams, FOnLoadWorldCompletedDelegateSimple OnComplete);

    /**
    Setup the input World for playing; Actors are intialized, BeginPlay is called etc...
    After you call this method, the world is ready for playing and you can switch world calling SwitchWorld.

    @attention it's not necessary to call this function if the world was loaded with the setting 'bAutoInitializeWorld' set to true.

	@param[in] WorldContextObject the world context object
    @param InWorldHandle the world to setup; it should came from the function LoadWorld.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void InitializeWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle);

    /**
    Call the EndPlay to the input World and to all its actors; The World and all actors are destroyed. 
    The input world handle is not more valid after.
    If InWorldHandle is the active world (equals to GetActiveWorldHandle()), ReturnToMainWorld is called automatically.
    Can NOT be called with the main world handle (GetMainWorldHandle() is not a valid param). In this case the call doesn't have any effect.   

	@param[in] WorldContextObject the world context object
    @param[in] OnComplete delegate called when the world is disposed.
    @param InWorldHandle the world handle
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void EndWorldWithDelegate(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle, FOnEndWorldCompletedDelegateSimple OnComplete);

    /** Deprecated version of EndWorld. @see EndWorldWithDelegate */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject", DeprecatedFunction, DeprecationMessage = "EndWorld has been deprecated, Please use EndWorldWithDelegate or EndWorldAsync"))
    static void EndWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle);

    /**
    Call EndWorld for all loaded secondary worlds.

    @see EndWorld
    @param[in] WorldContextObject the world context object
    @param[in] OnComplete delegate called when all worlds are disposed.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void EndAllWorldsWithDelegate(const UObject* WorldContextObject, FOnEndWorldCompletedDelegateSimple OnComplete);

	/**
    Sets whether or not the input world is ticked by the engine when it is in background (when not in play).
    
    @attention You MUST NOT disable the background ticking of the Main World in a multi-player game.

	@param[in] WorldContextObject the world context object
    @param InWorldHandle the world handle for which to apply the setting
    @param bShouldTick the "tick-when-in-background" flag
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void SetShouldTickWhenInBackground(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle, bool bShouldTick);

	/**
    Sets whenever the UMG main world widgets must be handled automatically or not 
    (shown when the world is active, hidden when the world is not). True by default.

	@param[in] WorldContextObject the world context object
    @param[in] bAutoHandleWidgets true if widgets are handled automatically for the main world, false otherwise.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void SetAutoHandleWidgetsForMainWorld(const UObject* WorldContextObject, bool bAutoHandleWidgets);

    /**
    Sets whenever the InputMode must be handled and restored for the main world automatically. True by default.
    In Unreal Engine the Input Mode is defined globally and so "leaks" between worlds.
    If AutoHandleInputMode is true, the plugin save the actual input mode when we leave the world 
    and restore it when we return back to that world.

    @param[in] WorldContextObject the world context object
    @param[in] bAutoHandleInputMode true if the input mode is handled automatically for the main world, false otherwise.
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void SetAutoHandleInputModeForMainWorld(const UObject* WorldContextObject, bool bAutoHandleInputMode);

	/**
    Change the Active World, travelling the local players to the input world.
    Secondary Worlds are not replicated.

    All actors implementing the interface IMultiWorldActorInterface are notified accordingly
    to the interface.

    The delegate UMultiWorldManager::OnWorldSwitched is notified.

    UMG widgets are managed accordingly to the configuration (see FMultiWorldLoadParameters::bAutoHandleWidgets and SetAutoHandleWidgetsForMainWorld()).
    Player controllers input mode is managed accordingly to the configuration (see FMultiWorldLoadParameters::bAutoHandleInputMode and UMultiWorldStatics::SetAutoHandleInputModeForMainWorld()).

	@param[in] WorldContextObject the world context object
    @param InWorldHandle the world handle where to go
    @return true if succeeded, false otherwise
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static bool SwitchWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle);

	/**
    Like SwitchWorld() but the switch will take place in the next frame and outside the worlds ticking.

    @see SwitchWorld
	@param[in] WorldContextObject the world context object
    @param InWorldHandle the world handle where to go
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void RequestSwitchWorld(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle);

	/**
    Travel the local players to the main world. The main world is the world loaded by the Unreal Engine itself.
    If you call from the main world, the call doesn't have any effect.
	
	@param[in] WorldContextObject the world context object
    @return true if succeeded, false otherwise
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static bool ReturnToMainWorld(const UObject* WorldContextObject);

	/**
    Return the main world handle. The main world is the world loaded by the Unreal Engine itself.

	@param[in] WorldContextObject the world context object
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static FMultiWorldHandle GetMainWorldHandle(const UObject* WorldContextObject);

	/**
    Return the world handle where the caller lives.

    Technically it's the UWorld of the *World Context Object* implicitly passed by UE5 to the function.
	
	@param[in] WorldContextObject the world context object
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static FMultiWorldHandle GetThisWorldHandle(const UObject* WorldContextObject);

	/**
    Return the world handle of the active World.

	@param[in] WorldContextObject the world context object
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static FMultiWorldHandle GetActiveWorldHandle(const UObject* WorldContextObject);


    /**
    Return the world handle of the world with the given name if found or an invalid handle otherwise. 
    If two or more worlds have the same name, the first found is returned.

    @param[in] WorldContextObject the world context object
    @param[in] WorldName the name of the world to looking for
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static FMultiWorldHandle GetWorldHandleByName(const UObject* WorldContextObject, FName WorldName);

	/**
    Return true if the two world handle(s) are equals (they refer to the same world), false otherwise.

    @param[in] InWorldHandleA first world handle to compare
    @param[in] InWorldHandleB second world handle to compare
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld")
    static bool AreWorldsEquals(const FMultiWorldHandle& InWorldHandleA, const FMultiWorldHandle& InWorldHandleB);

	/**
    Return true if the input world handle is valid, false otherwise
	
	@param[in] WorldContextObject the world context object
    @param[in] InWorldHandle the world handle to check
    */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static bool IsValidHandle(const UObject* WorldContextObject, const FMultiWorldHandle& InWorldHandle);

    /**
    Return the world pointer from the handle if it's valid, nullptr otherwise.

    @param[in] InWorldHandle the world handle to use to get the world pointer
    @return the world pointer if the handle is valid, nullptr otherwise.
     */
    UFUNCTION(BlueprintPure, Category = "MultiWorld")
    static UWorld* GetWorldPtr(const FMultiWorldHandle& InWorldHandle);

	/**
    Transfer the input actor from its actual world to the input one.
    
    It's not network-replicated.

    @attention @copydetails AdvancedTransferActorToWorld_Group

	@param[in] WorldContextObject the world context object
    @param InActor the actor to transfer
    @param InWorldHandle the new world of the input actor
    @param Options Options to customize the transfer (including setting a final transform for the actor).
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static void TransferActorToWorld(const UObject* WorldContextObject, AActor* InActor, const FMultiWorldHandle& InWorldHandle, const FMultiWorldTransferActorParameters & Options);

	/**
    Create an actor and place it in the input world.

	@param[in] WorldContextObject the world context object
    @param[in] ActorClass the class to use to create the actor
    @param[in] InWorldHandle the world where to place the actor
    @param[in] SpawnTransform the absolute world transform of the new actor
    @param[in] CollisionHandlingOverride the strategy for handling the case of collision when the actor is spawned
    @param[in] Owner the owner of the new actor
    @return the new created actor
    */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject", DeterminesOutputType = "ActorClass"))
    static AActor* SpawnActorInWorld(const UObject* WorldContextObject, 
        TSubclassOf<class AActor> ActorClass, 
        const FMultiWorldHandle& InWorldHandle, 
        const FTransform& SpawnTransform, 
        ESpawnActorCollisionHandlingMethod CollisionHandlingOverride, 
        AActor* Owner);

    // = Utility functions =

    /**
     *	Find the first Actor in the world of the specified class.
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actor.
     *	@param	ActorClass	Class of Actor to find. Must be specified or result will be empty.
     *	@return				Actor of the specified class.
     */
    UFUNCTION(BlueprintCallable, Category="MultiWorld", meta=(DeterminesOutputType="ActorClass"))
    static class AActor* GetActorOfClass(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass);

    /** 
     *	Find all Actors in the world of the specified class. 
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actors.
     *	@param	ActorClass	Class of Actor to find. Must be specified or result array will be empty.
     *	@param	OutActors	Output array of Actors of the specified class.
     */
    UFUNCTION(BlueprintCallable, Category="MultiWorld", meta=(DeterminesOutputType="ActorClass", DynamicOutputParam="OutActors"))
    static void GetAllActorsOfClass(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass, TArray<AActor*>& OutActors);

    /** 
     *	Find all Actors in the world with the specified interface.
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actors.
     *	@param	Interface	Interface to find. Must be specified or result array will be empty.
     *	@param	OutActors	Output array of Actors of the specified interface.
     */
    UFUNCTION(BlueprintCallable, Category="MultiWorld", meta=(DeterminesOutputType="Interface", DynamicOutputParam="OutActors"))
    static void GetAllActorsWithInterface(const FMultiWorldHandle& InWorldHandle, TSubclassOf<UInterface> Interface, TArray<AActor*>& OutActors);

    /**
     *	Find all Actors in the world with the specified tag.
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actors.
     *	@param	Tag			Tag to find. Must be specified or result array will be empty.
     *	@param	OutActors	Output array of Actors of the specified tag.
     */
    UFUNCTION(BlueprintCallable, Category="MultiWorld")
    static void GetAllActorsWithTag(const FMultiWorldHandle& InWorldHandle, FName Tag, TArray<AActor*>& OutActors);

    /**
     *	Find all Actors in the world of the specified class with the specified tag.
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actors.
     *	@param	Tag			Tag to find. Must be specified or result array will be empty.
     *	@param	ActorClass	Class of Actor to find. Must be specified or result array will be empty.
     *	@param	OutActors	Output array of Actors of the specified tag.
     */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld")
    static void GetAllActorsOfClassWithTag(const FMultiWorldHandle& InWorldHandle, TSubclassOf<AActor> ActorClass, FName Tag, TArray<AActor*>& OutActors);

    /**
     *	Find all UObject(s) in the world with the specified interface.
     *	This is a slow operation, use with caution e.g. do not use every frame.
     *	@param  InWorldHandle  The handle of the world where find the actors.
     *	@param	Interface	Interface to find. Must be specified or result array will be empty.
     *	@param	OutObjects	Output array of UObject(s) of the specified interface.
     */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld")
    static void GetAllObjectsWithInterface(const FMultiWorldHandle& InWorldHandle, TSubclassOf<UInterface> Interface, TArray<UObject*>& OutObjects);

    /** 
     * Set the Actor transform, moving also all attached physics bodies as a single entity.
     *
     * @param Actor				The Actor to move.
     * @param NewTransform		The new transform.
     * @param Teleport			How we teleport the physics state (see AActor::SetActorTransform()).
     */
    UFUNCTION(BlueprintCallable, Category="MultiWorld")
    static void SetPhysicsActorTransform(AActor * Actor, const FTransform & NewTransform, ETeleportType Teleport = ETeleportType::ResetPhysics);

    /**
     * Executes a console command on a specific world
     *
     * @param	InWorldHandle	The handle of the world where to exec the command
     * @param	Command			Command to send to the console
     */
    UFUNCTION(BlueprintCallable, Category = "MultiWorld")
    static void ExecuteConsoleCommandInWorld(const FMultiWorldHandle& InWorldHandle, const FString& Command);

    /**
     * Returns the player controller found while iterating through the local available player controllers.
     * The implementation is equal to UGameplayStatics::GetPlayerController (UE 4.26)
     * 
     * WARNING: the new implementation of UGameplayStatics::GetPlayerController (UE 5.03)
     * get the player controller from the localplayer and this is wrong when it's called outside the world tick (e.g delegates).
     * So in UE5 this function must be used instead of UGameplayStatics::GetPlayerController whenever you need to get the player controller
     * in a world but the caller comes from a different world.
     * 
     * @param[in] WorldContextObject the world context object
     * @param[in] PlayerIndex the local player index for which to return the player controller
     */
    UFUNCTION(BlueprintPure, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject"))
    static class APlayerController* GetPlayerController(const UObject* WorldContextObject, int32 PlayerIndex);
};
