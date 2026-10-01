// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Factory/ACFBaseFactory.h"
#include "ACFAssetCreatorClassPicker.h"
#include "ACFEditorSubsystem.h"
#include "AscentEditorExtensions.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "KismetCompilerModule.h"
#include "Runtime/Launch/Resources/Version.h"

#define LOCTEXT_NAMESPACE "UAssetCreator_BaseFactory"

UACFBaseFactory::UACFBaseFactory()
{
    bCreateNew = true;
    bEditAfterNew = true;
    DefaultAssetName = UBlueprintFactory::GetDefaultNewAssetName();

#if ENGINE_MAJOR_VERSION == 5
#if ENGINE_MINOR_VERSION == 1
    BlueprintType = BPTYPE_Normal;
#endif
    bSkipClassPicker = true;
#endif
}

void UACFBaseFactory::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
    Super::PostEditChangeProperty(PropertyChangedEvent);

    if (UACFEditorSubsystem::HasFactory(ParentClass) == false) {
        OldClass = ParentClass;
        SupportedClass = ParentClass;
    } else {
        ParentClass = OldClass;
    }
}

uint32 UACFBaseFactory::GetMenuCategories() const
{
    if (SupportedClass == nullptr || SupportedClass == UBlueprint::StaticClass() || ParentClass == nullptr || GetOuter()->GetName() == "/Engine/Transient") {
        return 0;
    }

    return Super::GetMenuCategories();
}

bool UACFBaseFactory::ConfigureProperties()
{
    if (UseClassPicker) {
        TSharedRef<SACFAssetCreatorClassPicker> Dialog = SNew(SACFAssetCreatorClassPicker);
        return Dialog->ConfigureProperties(this);
    }

    return true;
}

FString UACFBaseFactory::GetDefaultNewAssetName() const
{
    if (DefaultAssetName.IsEmpty()) {
        return Super::GetDefaultNewAssetName();
    }

    return DefaultAssetName;
}

UObject* UACFBaseFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn, FName CallingContext)
{
    if (ParentClass == nullptr || !FKismetEditorUtilities::CanCreateBlueprintOfClass(ParentClass)) {
        FFormatNamedArguments Args;
        Args.Add(TEXT("ClassName"), (ParentClass != nullptr) ? FText::FromString(ParentClass->GetName()) : LOCTEXT("Null", "(null)"));
        FMessageDialog::Open(EAppMsgType::Ok, FText::Format(LOCTEXT("CannotCreateBlueprintFromClass", "Cannot create a blueprint based on the class '{0}'."), Args));
        return nullptr;
    } else {
        if (ParentClass->IsChildOf(UDataAsset::StaticClass())) {

            return NewObject<UDataAsset>(InParent, ParentClass, InName, Flags | RF_Transactional);
        }
        UClass* BlueprintClass = nullptr;
        UClass* BlueprintGeneratedClass = nullptr;

        IKismetCompilerInterface& KismetCompilerModule = FModuleManager::LoadModuleChecked<IKismetCompilerInterface>("KismetCompiler");
        KismetCompilerModule.GetBlueprintTypesForClass(ParentClass, BlueprintClass, BlueprintGeneratedClass);

        return FKismetEditorUtilities::CreateBlueprint(ParentClass, InParent, InName, BPTYPE_Normal, BlueprintClass, BlueprintGeneratedClass, CallingContext);
    }
}

FText UACFBaseFactory::GetDisplayName() const
{
    // Avoid ensures on startup
    if (!IsValid(ParentClass)) {
        return LOCTEXT("ACFactory_MissingParentClass", "Missing Parent Class");
    }
    return Super::GetDisplayName();
}

#undef LOCTEXT_NAMESPACE
