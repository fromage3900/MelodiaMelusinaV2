#include "MelodiaMultiWorldGameViewportClient.h"

#include "MultiWorldOverrides.h"

void UMelodiaMultiWorldGameViewportClient::AddViewportWidgetContent(TSharedRef<SWidget> ViewportContent, const int32 ZOrder)
{
	UMultiWorldOverrides::GameViewportClient_AddViewportWidgetContent(this, ViewportContent, ZOrder);
}

void UMelodiaMultiWorldGameViewportClient::AddViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder)
{
	UMultiWorldOverrides::GameViewportClient_AddViewportWidgetForPlayer(this, Player, ViewportContent, ZOrder);
}

void UMelodiaMultiWorldGameViewportClient::RemoveViewportWidgetContent(TSharedRef<SWidget> ViewportContent)
{
	UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetContent(this, ViewportContent);
}

void UMelodiaMultiWorldGameViewportClient::RemoveViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent)
{
	UMultiWorldOverrides::GameViewportClient_RemoveViewportWidgetForPlayer(this, Player, ViewportContent);
}

void UMelodiaMultiWorldGameViewportClient::ReceivedFocus(FViewport* InViewport)
{
	UMultiWorldOverrides::GameViewportClient_ReceivedFocus(this, InViewport);
}

void UMelodiaMultiWorldGameViewportClient::LayoutPlayers()
{
	UMultiWorldOverrides::GameViewportClient_LayoutPlayers(this);
}

void UMelodiaMultiWorldGameViewportClient::Tick(float DeltaTime)
{
	UMultiWorldOverrides::GameViewportClient_Tick(this, DeltaTime);
}
