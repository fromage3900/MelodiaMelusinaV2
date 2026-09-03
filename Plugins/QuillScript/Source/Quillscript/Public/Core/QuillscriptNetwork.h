// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"
#include "QuillscriptNetwork.generated.h"

/**
 * .
 */
UCLASS(BlueprintType)
class QUILLSCRIPT_API AQuillscriptNetwork : public AInfo
{
	GENERATED_BODY()

public:
	AQuillscriptNetwork();


	/// Remote Procedure Calls
	#pragma region RPC

		/// Server
		#pragma region Server

			#pragma region Data

				UFUNCTION(BlueprintCallable, Server, Reliable, DisplayName = "Join", Category = "Quillscript|Remote Procedure Calls|Server|Data")
				void Server_Join(const APlayerState* CallerPlayerState);

			#pragma endregion Data

		#pragma endregion Server

		/// Clients
		#pragma region Clients

			#pragma region Data

				UFUNCTION(BlueprintCallable, NetMulticast, Reliable, DisplayName = "Join", Category = "Quillscript|Remote Procedure Calls|Clients|Data")
				void Multi_Join(const APlayerState* CallerPlayerState);

			#pragma endregion Data

		#pragma endregion Clients

	#pragma endregion RPC
};