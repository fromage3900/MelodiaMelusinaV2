#pragma once

#include "IDetailCustomization.h"
#include "Graph/ACFRerouteNode.h"

class UACFRerouteNode;

class FRerouteNodeDetailsCustomization : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance();

    // Called to customize the details view
    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override;

private:
    // Generates the list of reroute nodes for the dropdown
    void GenerateRerouteNodeOptions();

    // Callback when a reroute node is selected
    void OnRerouteNodeSelected(TSharedPtr<FName> NewSelection, ESelectInfo::Type SelectInfo);

    // Dropdown Options
    TArray<TSharedPtr<FName>> RerouteNodeOptions;

    // Current Selection in Dropdown
    TSharedPtr<FName> CurrentSelection;

    // Pointer to the current reroute node being edited
    TWeakObjectPtr<UACFRerouteNode> EditedRerouteNode;
};
