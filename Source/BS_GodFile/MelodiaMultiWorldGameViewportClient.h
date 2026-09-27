#pragma once

#include "CoreMinimal.h"
#include "CommonGameViewportClient.h"
#include "MelodiaMultiWorldGameViewportClient.generated.h"

/** CommonUI viewport with the MultiWorld widget/render/audio routing hooks. */
UCLASS(NotBlueprintable)
class BS_GODFILE_API UMelodiaMultiWorldGameViewportClient final : public UCommonGameViewportClient
{
	GENERATED_BODY()

public:
	virtual void AddViewportWidgetContent(TSharedRef<SWidget> ViewportContent, const int32 ZOrder = 0) override;
	virtual void AddViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder) override;
	virtual void RemoveViewportWidgetContent(TSharedRef<SWidget> ViewportContent) override;
	virtual void RemoveViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent) override;
	virtual void ReceivedFocus(FViewport* InViewport) override;
	virtual void LayoutPlayers() override;
	virtual void Tick(float DeltaTime) override;
};
