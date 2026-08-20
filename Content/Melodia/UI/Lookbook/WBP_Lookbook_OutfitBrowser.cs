// WBP_Lookbook_OutfitBrowser — Infinity Nikki-style outfit browser grid.
// Reuses .nikki-outfit-board CSS class for card layout.
//
// Layout: 10 glam → 10 outfit cards grid
// Each card: beauty render + material swatches + vibe tags
// Clickable: selects outfit → equips outfit + shows detail page
// Supports filtering by rarity, category, slot via .game-ui-phase-switch

class UWBP_Lookbook_OutfitBrowser_C : public UUserWidget
{
    GENERATED_BODY()

public:
    UWBP_Lookbook_OutfitBrowser_C(const FObjectInitializer& ObjectInitializer);

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Initialization
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    virtual void NativeConstruct() override;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Outfit browsing
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    /** Load the outfit catalog and populate the grid. */
    UFUNCTION(BlueprintCallable, Category="Lookbook")
    void LoadCatalog();

    /** Select an outfit by ID and equip it. */
    UFUNCTION(BlueprintCallable, Category="Lookbook")
    void SelectOutfit(FName CosmeticId);

    /** Filter outfits by rarity. */
    UFUNCTION(BlueprintCallable, Category="Lookbook")
    void FilterByRarity(EMelodiaCosmeticRarity Rarity);

    /** Filter outfits by slot. */
    UFUNCTION(BlueprintCallable, Category="Lookbook")
    void FilterBySlot(EMelodiaWardrobeSlot Slot);

    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Slots and events
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    UPROPERTY(BlueprintReadWrite, Category="Lookbook")
    TWidgetPath OutfitCardClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lookbook")
    TArray<FMelodiaCosmeticRecord> Catalog;

    UPROPERTY(BlueprintReadOnly, Category="Lookbook")
    int32 SelectedOutfitId;

    FOnOutfitSelected OnOutfitSelected;

    /** Delegation: blueprint can bind to this for outfit selection results. */
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnOutfitSelected, FName, CosmeticId, int32, Rarity, FString, Notes);
};