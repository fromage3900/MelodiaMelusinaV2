// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldOverrides.h"

#include "MultiWorldGameViewportClient.h"
#include "MultiWorldManager.h"
#include "MultiWorld.h"

#include "Engine/GameInstance.h"
#include "Engine/Engine.h"

#include "Widgets/Layout/SConstraintCanvas.h"
#include "Slate/SObjectWidget.h"

#include "AudioDeviceManager.h"

bool UMultiWorldOverrides::GameInstance_Exec(UGameInstance* Caller, UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar)
{
    check(Caller);

    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);

    FMultiWorldHandle MainWorldHandle = MultiWorldManager.GetMainWorldHandle();
    FMultiWorldHandle OtherWorldHandle = MultiWorldManager.GetThisWorldHandle(InWorld);

    // if the world where we are executing the command is not even the main world
    // filter some dangerous commands
    if (MainWorldHandle != OtherWorldHandle)
    {
        static TArray<const TCHAR*> BlackListCmds = {
            TEXT("OPEN"),
            TEXT("DISCONNECT"),
            TEXT("RECONNECT"),
            TEXT("TRAVEL"),
            TEXT("SERVERTRAVEL")
        };

        bool ShouldFilter = false;

        for (const TCHAR* BLCmd : BlackListCmds)
        {
            ShouldFilter |= FParse::Command(&Cmd, BLCmd);
        }

        if (ShouldFilter)
        {
            UE_LOG(LogMultiWorld, Warning, TEXT("Console command \"%s\" was filtered out because executed in a secondary world."), Cmd);
            return true;
        }
    }

    return Caller->UGameInstance::Exec(InWorld, Cmd, Ar);
}

void UMultiWorldOverrides::GameInstance_OnWorldChanged(UGameInstance* Caller, UWorld* OldWorld, UWorld* NewWorld)
{
    check(Caller);

    // Do NOT call UGameInstance::OnWorldChanged because it reset/null the WorldContext of the GameInstance
    // when we unload a secondary world. At the moment (UE5.5) it's safe to disable it because no other useful job is done.
    // see https://github.com/EpicGames/UnrealEngine/commit/566010c542102f327d07d41dd0f7df78fd812bfe
    // and https://github.com/EpicGames/UnrealEngine/commit/0a184c34b53db5ec136c60b1d78d1d92fe11d8f3
    // and internal bug #1529
    //Caller->UGameInstance::OnWorldChanged(OldWorld, NewWorld);

    // here the MultiWorldManager subsystem could be not initialized yet cos 
    // even the game instance is not initialized fully
    //UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);
    UMultiWorldManager* MultiWorldManager = Caller->GetSubsystem<UMultiWorldManager>();
    if (MultiWorldManager)
    {
        MultiWorldManager->OnWorldChanged(OldWorld, NewWorld);
    }
}

void UMultiWorldOverrides::GameViewportClient_AddViewportWidgetContent(UGameViewportClient* Caller, TSharedRef<class SWidget> ViewportContent, const int32 ZOrder)
{
    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);
    MultiWorldManager.AddViewportWidgetContent(ViewportContent, ZOrder);
}

void UMultiWorldOverrides::GameViewportClient_AddViewportWidgetForPlayer(UGameViewportClient* Caller, ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder)
{
    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);
    MultiWorldManager.AddViewportWidgetContent(ViewportContent, ZOrder);
}

void UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetContent(UGameViewportClient* Caller, TSharedRef<SWidget> ViewportContent)
{
    UMultiWorldManager& MultiWorldManager = *Caller->GetGameInstance()->GetSubsystem<UMultiWorldManager>();
    MultiWorldManager.RemoveViewportWidgetContent(ViewportContent);
}

void UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetForPlayer(UGameViewportClient* Caller, ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent)
{
    UMultiWorldManager& MultiWorldManager = *Caller->GetGameInstance()->GetSubsystem<UMultiWorldManager>();
    MultiWorldManager.RemoveViewportWidgetContent(ViewportContent);
}

void UMultiWorldOverrides::GameViewportClient_ReceivedFocus(UGameViewportClient* Caller, FViewport* InViewport)
{
    check(Caller);

    // it must be called, it is the only one that can handle the private var bHasAudioFocus
    Caller->UGameViewportClient::ReceivedFocus(InViewport);

    // Set the right audio device based on the active world
    if (GEngine && GEngine->GetAudioDeviceManager())
    {
        UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);

        FMultiWorldHandle ActiveWorldHandle = MultiWorldManager.GetActiveWorldHandle();

        // In PIE - testing multiplayer and so when there are at least a standalone viewport -
        // the ActiveWorldHandle could be already invalid because we have clear
        // the MultiWorld manager due to PIEEnded delegate but the ReceivedFocus is called again...
        if (MultiWorldManager.IsValidHandle(ActiveWorldHandle))
        {
            UWorld* ActiveWorld = ActiveWorldHandle.GetWorldContextObject()->GetWorld();

            MultiWorldManager.ActivateAudioDeviceForWorld(ActiveWorld);
        }
    }
}

void UMultiWorldOverrides::GameViewportClient_LayoutPlayers(UGameViewportClient* Caller)
{
    check(Caller);

#if WITH_EDITOR
    if (GIsEditor)
    {
        const bool GameRenderingEnabled = ShouldTickAndDraw(Caller);
        Caller->Viewport->SetGameRenderingEnabled(GameRenderingEnabled);
    }
#endif // WITH_EDITOR

    Caller->UGameViewportClient::LayoutPlayers();

    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);
    MultiWorldManager.FixUpLocalPlayers();
}

void UMultiWorldOverrides::GameViewportClient_Tick(UGameViewportClient* Caller, float DeltaTime)
{
#if WITH_EDITOR
    if (ShouldTickAndDraw(Caller))
    {
        // for the active world we tick normally...
        Caller->UGameViewportClient::Tick(DeltaTime);
    }
    else
    {
        // Still need to call UpdateLevelStreaming() even when not rendering
        // GameViewportClient::Tick in editor is ticked multiple times for each world
        // remember that the GetWorld() is always the same (active world) but GWorld changes.
        if (GWorld)
        {
            GWorld->UpdateLevelStreaming();
        }

        return;
    }
#else
    // When we are NOT in-editor, the viewport is ticked just once even
    // if there are multiple worlds loaded. Viewport client GetWorld() returns the active world
    // Tick it normally...
    Caller->UGameViewportClient::Tick(DeltaTime);
#endif

#if WITH_EDITOR
    if (!GIsEditor)
#endif
    {
        // We have ticked the viewport for the active world but we still have
        // to call UpdateLevelStreaming() for not active/rendered worlds...
        UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(Caller);
        UWorld* ActiveWorld = (UWorld*)MultiWorldManager.GetActiveWorldHandle().GetWorldContextObject();
        MultiWorldManager.ForEachSecondaryWorld([ActiveWorld](UWorld* SecondaryWorld) {
            if (SecondaryWorld != ActiveWorld)
            {
                SecondaryWorld->UpdateLevelStreaming();
            }
    });
}
}

#if WITH_EDITOR

bool UMultiWorldOverrides::ShouldTickAndDraw(UGameViewportClient* ViewportClient)
{
    // this prevent that the Editor tick multiple time the viewport
    // because the viewport is shared by all worlds.
    return !GIsEditor || GWorld == ViewportClient->GetWorld();
}

#endif // WITH_EDITOR
