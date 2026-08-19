#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaLLMRouter.generated.h"

UCLASS(BlueprintType, Blueprintable)
class BS_GODFILE_API UMelodiaLLMRouter : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    UFUNCTION(BlueprintCallable, Category = "Melodia|LLM")
    void RouteNarrativeToGlimmer(const FString& Context, const FString& Prompt);

    UFUNCTION(BlueprintCallable, Category = "Melodia|LLM")
    void RouteStateToQwen(const FString& BattleStateJSON);

private:
    FString MelusinaMCPEndpoint = TEXT("http://localhost:9316/mcp");

    void SendMCPRequest(const FString& ModelTarget, const FString& Payload);
};
