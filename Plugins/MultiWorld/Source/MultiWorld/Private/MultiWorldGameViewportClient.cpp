// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldGameViewportClient.h"

#include "MultiWorldOverrides.h"

void UMultiWorldGameViewportClient::AddViewportWidgetContent(TSharedRef<class SWidget> ViewportContent, const int32 ZOrder)
{
    UMultiWorldOverrides::GameViewportClient_AddViewportWidgetContent(this, ViewportContent, ZOrder);
}

void UMultiWorldGameViewportClient::AddViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder)
{
    UMultiWorldOverrides::GameViewportClient_AddViewportWidgetForPlayer(this, Player, ViewportContent, ZOrder);
}

void UMultiWorldGameViewportClient::RemoveViewportWidgetContent(TSharedRef<class SWidget> ViewportContent)
{
    UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetContent(this, ViewportContent);
}

void UMultiWorldGameViewportClient::RemoveViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent)
{
    UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetForPlayer(this, Player, ViewportContent);
}

void UMultiWorldGameViewportClient::ReceivedFocus(FViewport* InViewport)
{
    UMultiWorldOverrides::GameViewportClient_ReceivedFocus(this, InViewport);
}

void UMultiWorldGameViewportClient::LayoutPlayers()
{
    UMultiWorldOverrides::GameViewportClient_LayoutPlayers(this);
}

void UMultiWorldGameViewportClient::Tick(float DeltaTime)
{
    UMultiWorldOverrides::GameViewportClient_Tick(this, DeltaTime);
}
