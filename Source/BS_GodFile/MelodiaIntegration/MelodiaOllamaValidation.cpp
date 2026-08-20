#include "MelodiaOllamaValidation.h"

#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"

namespace MelodiaOllamaValidation
{
	void ValidateMessageAsync(const FString& Message, TFunction<void(bool bValid, const FString& RawReply)> OnComplete)
	{
		const FString Prompt = FString::Printf(
			TEXT("Is the following a valid Melodia intent? Answer with 'valid' or 'invalid'. Intent: %s"),
			*Message);

		const TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
		Payload->SetStringField(TEXT("model"), TEXT("qwen2.5-coder:7b"));
		Payload->SetStringField(TEXT("prompt"), Prompt);
		Payload->SetBoolField(TEXT("stream"), false);

		FString PayloadString;
		const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&PayloadString);
		FJsonSerializer::Serialize(Payload, Writer);
		Writer->Close();

		TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
		Request->SetVerb(TEXT("POST"));
		Request->SetURL(TEXT("http://127.0.0.1:11434/api/generate"));
		Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
		Request->SetContentAsString(PayloadString);

		// The request stays alive because the lambda below captures it by value
		// (TSharedRef copy keeps the refcount up until the callback runs).
		Request->OnProcessRequestComplete().BindLambda(
			// FIX 2026-07-31 (Claude, unblocking a shared build -- DeepSeek's file, not touching
			// anything else): Message was used at line ~62 but not captured. By value, not by
			// reference -- the outer function returns immediately after ProcessRequest() and this
			// callback fires later, so a reference would dangle.
			[Request, Message, OnComplete = MoveTemp(OnComplete)](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bConnectedSuccessfully)
			{
				FString Reply;
				if (!bConnectedSuccessfully || !Res.IsValid())
				{
					UE_LOG(LogTemp, Warning, TEXT("MELODIA_Ollama_Validation: request failed (daemon down?)"));
					if (OnComplete)
					{
						OnComplete(false, Reply);
					}
					return;
				}

				Reply = Res->GetContentAsString();

				const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Reply);
				TSharedPtr<FJsonObject> ResponseJson;
				bool bValid = false;
				if (FJsonSerializer::Deserialize(Reader, ResponseJson) && ResponseJson.IsValid())
				{
					const FString ModelReply = ResponseJson->GetStringField(TEXT("response")).TrimStartAndEnd();
					const FString LowerReply = ModelReply.ToLower();

					// Tokenize words to prevent substring false-positives (e.g. "invalid" containing "valid")
					TArray<FString> Tokens;
					LowerReply.ParseIntoArray(Tokens, TEXT(" \t\r\n.,;:!?'\"()[]{}"), true);

					bool bFoundValid = false;
					bool bFoundInvalid = false;
					for (int32 Idx = 0; Idx < Tokens.Num(); ++Idx)
					{
						const FString& Token = Tokens[Idx];
						if (Token == TEXT("invalid") || Token == TEXT("false"))
						{
							bFoundInvalid = true;
							break;
						}
						if (Token == TEXT("not") && (Idx + 1 < Tokens.Num()) && Tokens[Idx + 1] == TEXT("valid"))
						{
							bFoundInvalid = true;
							break;
						}
						if (Token == TEXT("valid") || Token == TEXT("true"))
						{
							bFoundValid = true;
						}
					}

					bValid = bFoundValid && !bFoundInvalid;
				}

				UE_LOG(LogTemp, Log, TEXT("MELODIA_Ollama_Validation: %s -> %s"), *Message, bValid ? TEXT("Valid") : TEXT("Invalid"));
				if (OnComplete)
				{
					OnComplete(bValid, Reply);
				}
			});

		Request->ProcessRequest();
	}
}
