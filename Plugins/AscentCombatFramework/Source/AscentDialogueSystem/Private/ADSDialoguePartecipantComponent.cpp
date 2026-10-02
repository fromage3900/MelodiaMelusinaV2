// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSDialoguePartecipantComponent.h"

#include "ADSDialogueDeveloperSettings.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialogueMasterComponent.h"
#include "ADSDialogueSubsystem.h"
#include <Animation/AnimInstance.h>
#include <Components/SkeletalMeshComponent.h>
#include <Engine/GameInstance.h>
#include <GameFramework/Character.h>
#include <Kismet/GameplayStatics.h>
#include <Net/UnrealNetwork.h>
#include "Net/Serialization/FastArraySerializer.h"

// ============================================================================
// FADSDialogueEntry Implementation
// ============================================================================

void FADSDialogueEntry::PreReplicatedRemove(const FADSDialogueArray& InArraySerializer)
{
	if (InArraySerializer.OwnerComponent && LocalInstance)
	{
		InArraySerializer.OwnerComponent->OnDialogueEntryRemoved(LocalInstance);
	}
}

void FADSDialogueEntry::PostReplicatedAdd(const FADSDialogueArray& InArraySerializer)
{
	if (InArraySerializer.OwnerComponent)
	{
		// Create local instance on the client
		UADSDialogue* Instance = const_cast<FADSDialogueEntry*>(this)->GetDialogueInstance(InArraySerializer.OwnerComponent->GetOuter());
		if (Instance)
		{
			InArraySerializer.OwnerComponent->OnDialogueEntryAdded(Instance);
		}
	}
}

void FADSDialogueEntry::PostReplicatedChange(const FADSDialogueArray& InArraySerializer)
{
	// Recreate instance if source changed
	LocalInstance = nullptr;
	if (InArraySerializer.OwnerComponent)
	{
		GetDialogueInstance(InArraySerializer.OwnerComponent->GetOuter());
	}
}

UADSDialogue* FADSDialogueEntry::GetDialogueInstance(UObject* Outer)
{
	if (LocalInstance)
	{
		return LocalInstance;
	}

	// Load and duplicate the source dialogue
	UADSDialogue* Source = SourceDialogue.LoadSynchronous();
	if (Source && Outer)
	{
		LocalInstance = DuplicateObject(Source, Outer);
	}

	return LocalInstance;
}

// ============================================================================
// FADSDialogueArray Implementation
// ============================================================================

void FADSDialogueArray::AddDialogue(UADSDialogue* SourceDialogue)
{
	if (!SourceDialogue)
	{
		return;
	}

	FGameplayTag Tag = SourceDialogue->GetDialogueTag();

	// Check if already exists
	for (const FADSDialogueEntry& Entry : Items)
	{
		if (Entry.DialogueTag == Tag)
		{
			return;
		}
	}

	FADSDialogueEntry NewEntry(SourceDialogue, Tag);
	
	// On server, create the local instance immediately
	if (OwnerComponent)
	{
		NewEntry.GetDialogueInstance(OwnerComponent->GetOuter());
	}
	
	Items.Add(NewEntry);
	MarkItemDirty(Items.Last());
}

void FADSDialogueArray::RemoveDialogue(UADSDialogue* Dialogue)
{
	if (!Dialogue)
	{
		return;
	}

	FGameplayTag TagToRemove = Dialogue->GetDialogueTag();
	RemoveDialogueByTag(TagToRemove);
}

void FADSDialogueArray::RemoveDialogueByTag(FGameplayTag DialogueTag)
{
	for (int32 i = Items.Num() - 1; i >= 0; --i)
	{
		if (Items[i].DialogueTag == DialogueTag)
		{
			Items.RemoveAt(i);
			MarkArrayDirty();
			return;
		}
	}
}

UADSDialogue* FADSDialogueArray::FindDialogueByTag(FGameplayTag DialogueTag) const
{
	for (const FADSDialogueEntry& Entry : Items)
	{
		if (Entry.DialogueTag == DialogueTag && Entry.LocalInstance)
		{
			return Entry.LocalInstance;
		}
	}
	return nullptr;
}

// Non-const version that can create instances
UADSDialogue* FADSDialogueArray::FindOrCreateDialogueByTag(FGameplayTag DialogueTag)
{
	for (FADSDialogueEntry& Entry : Items)
	{
		if (Entry.DialogueTag == DialogueTag)
		{
			if (!Entry.LocalInstance && OwnerComponent)
			{
				Entry.GetDialogueInstance(OwnerComponent->GetOuter());
			}
			return Entry.LocalInstance;
		}
	}
	return nullptr;
}

void FADSDialogueArray::ClearAll()
{
	Items.Empty();
	MarkArrayDirty();
}

// ============================================================================
// UADSDialoguePartecipantComponent Implementation
// ============================================================================

UADSDialoguePartecipantComponent::UADSDialoguePartecipantComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	ParticipantNameText = FText::FromString("Default Name");
	SetIsReplicatedByDefault(true);

	// Initialize the replicated array owner
	ReplicatedDialogues.OwnerComponent = this;
}

void UADSDialoguePartecipantComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UADSDialoguePartecipantComponent, ReplicatedDialogues);
}

void UADSDialoguePartecipantComponent::BeginPlay()
{
	Super::BeginPlay();

	// Ensure owner reference is set (might be cleared during serialization)
	ReplicatedDialogues.OwnerComponent = this;

	if (UADSDialogueSubsystem* adsSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>())
	{
		adsSubsystem->RegisterParticipant(this);
	}

	// Only create instances on the server (they will replicate to clients)
	if (GetOwner() && GetOwner()->HasAuthority())
	{
		// Backward compatibility: Instance dialogues from the editor-set array.
		// Pass the original asset to AddDialogue so that SourceDialogue (TSoftObjectPtr)
		// keeps a stable on-disk path that clients can LoadSynchronous(). AddDialogue
		// already creates the LocalInstance locally via GetDialogueInstance().
		for (const auto& dialogue : Dialogues)
		{
			if (dialogue)
			{
				// Pass the ORIGINAL asset to AddDialogue so the TSoftObjectPtr
				// stores a valid asset path that clients can resolve.
				// AddDialogue internally calls GetDialogueInstance() which
				// creates the server's local duplicate via DuplicateObject.
				ReplicatedDialogues.AddDialogue(dialogue);

				// Retrieve the server's local instance for the legacy array
				UADSDialogue* localInstance = ReplicatedDialogues.FindDialogueByTag(dialogue->GetDialogueTag());
				if (localInstance)
				{
					instancedDialogues.Add(localInstance);
				}
			}
		}
	}
}

void UADSDialoguePartecipantComponent::EndPlay(EEndPlayReason::Type reason)
{
	Super::EndPlay(reason);

	if (UADSDialogueSubsystem* adsSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>())
	{
		adsSubsystem->UnregisterParticipant(PartecipantTag);
	}
}

UADSDialogue* UADSDialoguePartecipantComponent::CreateDialogueInstance(UADSDialogue* SourceDialogue)
{
	if (!SourceDialogue)
	{
		return nullptr;
	}

	UADSDialogue* NewDialogue = DuplicateObject(SourceDialogue, GetOuter());
	return NewDialogue;
}

// ============================================================================
// Dialogue Starting
// ============================================================================

bool UADSDialoguePartecipantComponent::TryStartDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSDialogue* dialogueToStart)
{
	if (!IsValid(dialogueToStart))
	{
		UE_LOG(LogTemp, Error, TEXT("No ADS Dialogue Set!- UADSDialoguePartecipantComponent::TryStartDialogue"));
		return false;
	}
	if (participants.Num() == 0)
	{
		UE_LOG(LogTemp, Error, TEXT("No participants provided to TryStartDialogue!"));
		return false;
	}
	for (int32 i = 0; i < participants.Num(); ++i)
	{
		if (!IsValid(participants[i]))
		{
			UE_LOG(LogTemp, Error, TEXT("Participant at index %d is invalid!"), i);
		}
		else
		{
			FText name = participants[i]->GetParticipantName();
			if (name.IsEmpty() || name.ToString().Equals(TEXT("Unknown")))
			{
				UE_LOG(LogTemp, Warning, TEXT("Participant at index %d has unknown name!"), i);
			}
			else
			{
				UE_LOG(LogTemp, Log, TEXT("Participant at index %d: %s"), i, *name.ToString());
			}
		}
	}
	RegisterDialogueEvents(dialogueToStart);

	if (UADSDialogueSubsystem* adsSubsystem = GEngine->GetEngineSubsystem<UADSDialogueSubsystem>())
	{
		adsSubsystem->StopAllWorldDialogues();
	}

	const bool result = IsValid(dialogueToStart->StartDialogue(UGameplayStatics::GetPlayerController(this, 0), participants));
	if (!result)
	{
		UE_LOG(LogTemp, Warning, TEXT("StartDialogue failed in TryStartDialogue!"));
	}
	return result;
}

void UADSDialoguePartecipantComponent::RegisterDialogueEvents(UADSDialogue* dialogueToStart)
{
	if (!dialogueToStart->OnDialogueStarted.IsAlreadyBound(this, &UADSDialoguePartecipantComponent::HandleDialogueStarted))
	{
		dialogueToStart->OnDialogueStarted.AddDynamic(this, &UADSDialoguePartecipantComponent::HandleDialogueStarted);
	}
	if (!dialogueToStart->OnDialogueEnded.IsAlreadyBound(this, &UADSDialoguePartecipantComponent::HandleDialogueEnded))
	{
		dialogueToStart->OnDialogueEnded.AddDynamic(this, &UADSDialoguePartecipantComponent::HandleDialogueEnded);
	}
	if (!dialogueToStart->OnDialogueNodeActivated.IsAlreadyBound(this, &UADSDialoguePartecipantComponent::HandleNodeActivated))
	{
		dialogueToStart->OnDialogueNodeActivated.AddDynamic(this, &UADSDialoguePartecipantComponent::HandleNodeActivated);
	}
}

bool UADSDialoguePartecipantComponent::TryStartDialogueFromActors(const TArray<AActor*>& participants, UADSDialogue* dialogueToStart)
{
	TArray<UADSBaseDialoguePartecipantComponent*> participantComps;
	for (const auto& actor : participants)
	{
		UADSBaseDialoguePartecipantComponent* dialogueComp = actor->FindComponentByClass<UADSBaseDialoguePartecipantComponent>();
		if (dialogueComp)
		{
			participantComps.Add(dialogueComp);
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("No ADS Dialogue Component in the participant actor %s!"), *actor->GetName());
			return false;
		}
	}
	return TryStartDialogue(participantComps, dialogueToStart);
}

// ============================================================================
// Dialogue Management - Runtime Modifiable & Replicated
// ============================================================================

UADSDialogue* UADSDialoguePartecipantComponent::GetDialogue(FGameplayTag dialogueTag, bool& bFound) const
{
	// First check the replicated array (use const version)
	UADSDialogue* Found = ReplicatedDialogues.FindDialogueByTag(dialogueTag);
	if (Found)
	{
		bFound = true;
		return Found;
	}

	// Try to create instance if entry exists but instance doesn't
	UADSDialogue* FoundOrCreated = const_cast<FADSDialogueArray&>(ReplicatedDialogues).FindOrCreateDialogueByTag(dialogueTag);
	if (FoundOrCreated)
	{
		bFound = true;
		return FoundOrCreated;
	}

	// Fallback to legacy array for backward compatibility
	for (const auto& dial : instancedDialogues)
	{
		if (dial && dial->GetDialogueTag() == dialogueTag)
		{
			bFound = true;
			return dial;
		}
	}

	bFound = false;
	return nullptr;
}

void UADSDialoguePartecipantComponent::AddDialogue(UADSDialogue* Dialogue)
{
	if (!Dialogue)
	{
		UE_LOG(LogTemp, Warning, TEXT("AddDialogue called with null dialogue"));
		return;
	}

	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		UE_LOG(LogTemp, Warning, TEXT("AddDialogue called on client - this should only be called on the server"));
		return;
	}

	// Add to replicated array (will create instance internally and sync to clients)
	ReplicatedDialogues.AddDialogue(Dialogue);

	// Get the created instance for legacy array and broadcast
	UADSDialogue* NewInstance = ReplicatedDialogues.FindDialogueByTag(Dialogue->GetDialogueTag());
	if (NewInstance)
	{
		// Also add to legacy array for backward compatibility
		if (!instancedDialogues.Contains(NewInstance))
		{
			instancedDialogues.Add(NewInstance);
		}

		// Broadcast locally (clients will get this via replication callbacks)
		OnDialogueAdded.Broadcast(NewInstance);

		UE_LOG(LogTemp, Log, TEXT("Dialogue added: %s"), *Dialogue->GetDialogueTag().ToString());
	}
}

void UADSDialoguePartecipantComponent::RemoveDialogue(UADSDialogue* Dialogue)
{
	if (!Dialogue)
	{
		return;
	}

	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		UE_LOG(LogTemp, Warning, TEXT("RemoveDialogue called on client - this should only be called on the server"));
		return;
	}

	FGameplayTag TagToRemove = Dialogue->GetDialogueTag();
	
	// Find the local instance before removal
	UADSDialogue* LocalInstance = ReplicatedDialogues.FindDialogueByTag(TagToRemove);
	
	if (LocalInstance)
	{
		// Remove from legacy array
		instancedDialogues.Remove(LocalInstance);
		
		// Broadcast locally
		OnDialogueRemoved.Broadcast(LocalInstance);
	}
	
	// Remove from replicated array
	ReplicatedDialogues.RemoveDialogueByTag(TagToRemove);

	UE_LOG(LogTemp, Log, TEXT("Dialogue removed: %s"), *TagToRemove.ToString());
}

void UADSDialoguePartecipantComponent::RemoveDialogueByTag(FGameplayTag DialogueTag)
{
	if (!DialogueTag.IsValid())
	{
		return;
	}

	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		UE_LOG(LogTemp, Warning, TEXT("RemoveDialogueByTag called on client - this should only be called on the server"));
		return;
	}

	UADSDialogue* LocalInstance = ReplicatedDialogues.FindDialogueByTag(DialogueTag);
	if (LocalInstance)
	{
		// Remove from legacy array
		instancedDialogues.Remove(LocalInstance);

		// Broadcast locally
		OnDialogueRemoved.Broadcast(LocalInstance);
	}
	
	// Remove from replicated array
	ReplicatedDialogues.RemoveDialogueByTag(DialogueTag);

	UE_LOG(LogTemp, Log, TEXT("Dialogue removed by tag: %s"), *DialogueTag.ToString());
}

void UADSDialoguePartecipantComponent::ClearAllDialogues()
{
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		UE_LOG(LogTemp, Warning, TEXT("ClearAllDialogues called on client - this should only be called on the server"));
		return;
	}

	// Broadcast removal for each dialogue
	for (FADSDialogueEntry& Entry : ReplicatedDialogues.Items)
	{
		if (Entry.LocalInstance)
		{
			OnDialogueRemoved.Broadcast(Entry.LocalInstance);
		}
	}

	ReplicatedDialogues.ClearAll();
	instancedDialogues.Empty();

	UE_LOG(LogTemp, Log, TEXT("All dialogues cleared"));
}

TArray<UADSDialogue*> UADSDialoguePartecipantComponent::GetAllDialogues() const
{
	TArray<UADSDialogue*> Result;

	for (const FADSDialogueEntry& Entry : ReplicatedDialogues.Items)
	{
		if (Entry.LocalInstance)
		{
			Result.Add(Entry.LocalInstance);
		}
	}

	return Result;
}

int32 UADSDialoguePartecipantComponent::GetDialogueCount() const
{
	return ReplicatedDialogues.Items.Num();
}

bool UADSDialoguePartecipantComponent::HasDialogueWithTag(FGameplayTag DialogueTag) const
{
	return ReplicatedDialogues.FindDialogueByTag(DialogueTag) != nullptr;
}

void UADSDialoguePartecipantComponent::OnDialogueEntryAdded(UADSDialogue* Dialogue)
{
	// Called on clients when replication adds a dialogue
	if (Dialogue)
	{
		// Ensure it's also in the legacy array for backward compatibility
		if (!instancedDialogues.Contains(Dialogue))
		{
			instancedDialogues.Add(Dialogue);
		}

		OnDialogueAdded.Broadcast(Dialogue);
		
		UE_LOG(LogTemp, Log, TEXT("[Client] Dialogue replicated: %s"), *Dialogue->GetDialogueTag().ToString());
	}
}

void UADSDialoguePartecipantComponent::OnDialogueEntryRemoved(UADSDialogue* Dialogue)
{
	// Called on clients when replication removes a dialogue
	if (Dialogue)
	{
		instancedDialogues.Remove(Dialogue);
		OnDialogueRemoved.Broadcast(Dialogue);
		
		UE_LOG(LogTemp, Log, TEXT("[Client] Dialogue removed via replication: %s"), *Dialogue->GetDialogueTag().ToString());
	}
}

// ============================================================================
// Skeletal Mesh Management
// ============================================================================

USkeletalMeshComponent* UADSDialoguePartecipantComponent::GetOwnerMesh()
{
	if (skeletalMesh)
	{
		return skeletalMesh;
	}

	const ACharacter* CharacterOwner = Cast<ACharacter>(GetOwner());
	if (CharacterOwner)
	{
		skeletalMesh = CharacterOwner->GetMesh();
	}

	skeletalMesh = GetOwner()->FindComponentByClass<USkeletalMeshComponent>();
	return skeletalMesh;
}

USkeletalMeshComponent* UADSDialoguePartecipantComponent::GetFacialAnimationMesh()
{
	if (facialMesh)
	{
		return facialMesh;
	}

	TArray<UActorComponent*> Components;
	GetOwner()->GetComponents(USkeletalMeshComponent::StaticClass(), Components);
	for (UActorComponent* Component : Components)
	{
		USkeletalMeshComponent* SkeletalMeshComp = Cast<USkeletalMeshComponent>(Component);
		if (SkeletalMeshComp && SkeletalMeshComp->ComponentHasTag(FacialSkeletonComponentTag))
		{
			facialMesh = SkeletalMeshComp;
			return facialMesh = SkeletalMeshComp;
		}
	}

	return nullptr;
}

// ============================================================================
// Animation
// ============================================================================

void UADSDialoguePartecipantComponent::PlayAnimationOnCharacterOwner(UAnimMontage* animation)
{
	if (GetOwnerMesh())
	{
		UAnimInstance* animInstance = skeletalMesh->GetAnimInstance();

		if (animInstance)
		{
			animInstance->Montage_Play(animation);
		}
	}
}

void UADSDialoguePartecipantComponent::PlayFacialAnimationOnCharacterOwner(UAnimMontage* animation)
{
	if (GetFacialAnimationMesh())
	{
		UAnimInstance* animInstance = facialMesh->GetAnimInstance();

		if (animInstance)
		{
			animInstance->Montage_Play(animation);
		}
	}
}

void UADSDialoguePartecipantComponent::StopFacialAnimationOnCharacterOwner(UAnimMontage* animation)
{
	if (GetFacialAnimationMesh())
	{
		UAnimInstance* animInstance = facialMesh->GetAnimInstance();

		if (animInstance)
		{
			animInstance->Montage_Stop(AnimationBlendoutTime, animation);
		}
	}
}

void UADSDialoguePartecipantComponent::StopAnimationOnCharacterOwner(UAnimMontage* animation)
{
	if (GetOwnerMesh())
	{
		UAnimInstance* animInstance = skeletalMesh->GetAnimInstance();

		if (animInstance)
		{
			animInstance->Montage_Stop(AnimationBlendoutTime, animation);
		}
	}
}

// ============================================================================
// Objective Dialogues
// ============================================================================

void UADSDialoguePartecipantComponent::AddObjectiveDialogue(FGuid objectiveID, UADSDialogue* dialogue)
{
	if (dialogue)
	{
		dialogue->DeactivateAllNodes();
		ObjectiveDialogues.Add(objectiveID, dialogue);
	}
}

void UADSDialoguePartecipantComponent::RemoveObjectiveDialogue(FGuid objectiveID)
{
	if (ObjectiveDialogues.Contains(objectiveID))
	{
		ObjectiveDialogues.FindAndRemoveChecked(objectiveID);
	}
}

// ============================================================================
// Event Implementations
// ============================================================================

void UADSDialoguePartecipantComponent::OnDialogueStartedEvent_Implementation()
{
}

void UADSDialoguePartecipantComponent::OnDialogueEndedEvent_Implementation()
{
}

void UADSDialoguePartecipantComponent::HandleDialogueStarted(UADSDialogue* dialogue)
{
	OnDialogueStartedEvent();
	OnDialogueStarted.Broadcast(dialogue);
}

void UADSDialoguePartecipantComponent::HandleDialogueEnded(UADSDialogue* dialogue)
{
	APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
	UADSDialogueMasterComponent* dialogueMaster = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(this);
	if (dialogueMaster)
	{
		dialogueMaster->StopCurrentShot();
	}

	UnregisterDialogueEvents(dialogue);

	OnDialogueEndedEvent();

	OnDialogueEnded.Broadcast(dialogue);
}

void UADSDialoguePartecipantComponent::UnregisterDialogueEvents(UADSDialogue* dialogue)
{
	if (dialogue)
	{
		dialogue->OnDialogueStarted.RemoveDynamic(this, &UADSDialoguePartecipantComponent::HandleDialogueStarted);
		dialogue->OnDialogueEnded.RemoveDynamic(this, &UADSDialoguePartecipantComponent::HandleDialogueEnded);
		dialogue->OnDialogueNodeActivated.RemoveDynamic(this, &UADSDialoguePartecipantComponent::HandleNodeActivated);
	}
}

void UADSDialoguePartecipantComponent::HandleNodeActivated(const FGuid& nodeId)
{
	OnNodeActivated.Broadcast(nodeId);
}