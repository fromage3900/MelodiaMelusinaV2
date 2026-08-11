# Melodia Cute UI Elements Specification

**Date:** 2026-07-31
**Purpose:** Define cute/reusable UI elements for JRPG keybinds, buttons, cursors, and decorative assets
**Style:** SoftMG parchment + Baroque filigree + Nikki-inspired cute elements

---

## 1. Reusable Button Widget: WBP_MenuButton

### Design Reference
Figma node: `Ctrl/MenuButton` (`81:1795`) from EssentialUI board

### Visual Style
**Base:** Parchment background with gold filigree border
**States:** Default, Hover, Pressed, Disabled

### Cute Elements
- **Corner decorations:** Small 4-point stars at each corner (gold/500, opacity 60%)
- **Hover sparkle:** Subtle sparkle drift animation on hover
- **Pressed feedback:** Parchment darkens + stars pulse inward
- **Disabled state:** Desaturated parchment + stars fade to 20% opacity

### Component Structure
```
WBP_MenuButton (SizeBox)
├─ Background (Border)
│  ├─ Parchment fill (gradient: parchment → parchment-deep)
│  └─ Filigree border (gold/500, 1px stroke)
├─ Corner Stars (4x Image widgets)
│  ├─ Top-Left Star (4pt star, rotated 45°)
│  ├─ Top-Right Star (4pt star, rotated -45°)
│  ├─ Bottom-Left Star (4pt star, rotated -45°)
│  └─ Bottom-Right Star (4pt star, rotated 45°)
├─ Content (Overlay)
│  ├─ Button Text (Text Block)
│  └─ Optional Icon (Image)
└─ Sparkle Overlay (Canvas Panel, opacity 0 by default)
```

### Properties
- `ButtonText` (Text): Button label
- `ButtonStyle` (Enum): Primary, Secondary, Tertiary
- `ShowCorners` (Boolean): Show/hide corner stars
- `SparkleOnHover` (Boolean): Enable sparkle animation
- `IsDisabled` (Boolean): Disable state

### Animation States
- **Default:** Corner stars static, parchment gradient normal
- **Hover:** Corner stars scale 1.1x, sparkle overlay fades in (0.3s), parchment brightens 10%
- **Pressed:** Corner stars scale 0.9x, parchment darkens 15%, sparkle burst at center
- **Disabled:** Parchment desaturated 50%, corner stars opacity 20%, no hover effects

### Size Variants
- **Large:** 200x64 (menu buttons)
- **Medium:** 160x48 (dialog buttons)
- **Small:** 120x36 (chip buttons)
- **Icon:** 48x48 (square icon buttons)

---

## 2. Parchment Panel Base: WBP_ParchmentPanel

### Design Reference
Figma node: `SoftMG/ParchmentPanel` (`62:531`)

### Visual Style
**Base:** Tintable parchment with musical clef watermark
**Usage:** Background for all meta UI panels (SaveLoad, Settings, QuestJournal, etc.)

### Cute Elements
- **Clef watermark:** Large musical clef in center (opacity 8%, gold/500)
- **Scroll edges:** Decorative scroll pattern on left/right borders
- **Subtle grain:** Noise texture overlay (opacity 3%) for paper texture

### Component Structure
```
WBP_ParchmentPanel (SizeBox)
├─ Parchment Background (Border)
│  ├─ Fill (gradient: parchment → parchment-deep, vertical)
│  ├─ Grain Overlay (Image, noise texture, blend multiply)
│  └─ Scroll Edges (Left/Right borders, decorative pattern)
├─ Clef Watermark (Image, centered, opacity 8%)
└─ Content Slot (Canvas Panel, for child widgets)
```

### Properties
- `ParchmentTint` (Color): Tint the parchment (default: game.parchment)
- `ShowClef` (Boolean): Show/hide watermark
- `ShowScrollEdges` (Boolean): Show/hide decorative borders
- `CornerRadius` (Float): Border radius (default: 8)

### Size Variants
- **Full Panel:** 1440x900 (desktop menu panels)
- **Half Panel:** 620x900 (side panels like QuestJournal)
- **Card:** 400x300 (info cards)
- **Chip:** 120x48 (small item tiles)

---

## 3. JRPG Keybind Visual Elements: WBP_KeybindBadge

### Purpose
Display keyboard key prompts (F, J, K, L, E, ESC) with cute styling

### Visual Style
**Base:** Rounded keycap with Nikki-inspired colors
**Cute Elements:** Small star icon next to key letter, subtle glow on active

### Keybind Mappings
| Key | Action | Color | Icon |
|-----|--------|-------|------|
| **F** | Interact | Rose (#E8A9A1) | Hand/heart |
| **J** | Attack | Amber (#D9A566) | Sword |
| **K** | Skill | Lavender (#B6A6D9) | Sparkle |
| **L** | Ultimate | Seafoam (#8FC9BD) | Star |
| **E** | Menu | Parchment (#F2E6CF) | Book |
| **ESC** | Back | Ink (#3B2A22) | Arrow |

### Component Structure
```
WBP_KeybindBadge (SizeBox, 48x48)
├─ Keycap Background (Border)
│  ├─ Fill (solid color based on action)
│  └─ Border (gold/500, 1px, radius 4)
├─ Key Letter (Text Block, centered, bold)
├─ Action Icon (Image, 16x16, bottom-right corner)
└─ Glow Overlay (Border, opacity 0, pulses when active)
```

### Properties
- `KeyLetter` (Text): Single character (F, J, K, L, E, ESC)
- `ActionType` (Enum): Interact, Attack, Skill, Ultimate, Menu, Back
- `IsActive` (Boolean): Key is currently pressed
- `ShowIcon` (Boolean): Show/hide action icon

### Animation States
- **Default:** Solid fill, no glow
- **Pressed:** Fill brightens 20%, glow overlay fades in (0.15s), key letter scales 1.1x
- **Cooldown:** Fill desaturated 30%, glow disabled

### Size Variants
- **Standard:** 48x48 (normal keybinds)
- **Large:** 64x64 (important actions like Ultimate)
- **Small:** 32x32 (secondary actions)

---

## 4. Cute Cursor Assets

### Cursor Set
All cursors use 8-point star motif with Nikki color palette

### Cursor Types

#### 1. Default Cursor (Pointer)
- **Shape:** 8-point star with upward-pointing tip
- **Colors:** Gold/500 fill, gold/700 stroke
- **Size:** 32x32
- **Hotspot:** Tip of star (top center)
- **Animation:** Subtle pulse (scale 1.0 → 1.05 → 1.0, 2s loop)

#### 2. Hover Cursor (Hand)
- **Shape:** Star with small hand icon overlay
- **Colors:** Rose (#E8A9A1) fill, gold stroke
- **Size:** 32x32
- **Hotspot:** Center
- **Animation:** Star rotates slowly (360° in 4s)

#### 3. Click Cursor (Sparkle)
- **Shape:** Star burst (8 rays expanding outward)
- **Colors:** Gold/500 → transparent fade
- **Size:** 48x48
- **Hotspot:** Center
- **Animation:** One-shot burst on click (0.3s duration)

#### 4. Drag Cursor (Grab)
- **Shape:** Star with small grab icon (pinched fingers)
- **Colors:** Lavender (#B6A6D9) fill, gold stroke
- **Size:** 32x32
- **Hotspot:** Center of grab icon
- **Animation:** Subtle bounce (offset Y 0 → -2 → 0, 1s loop)

#### 5. Wait Cursor (Loading)
- **Shape:** Spinning 8-point star outline
- **Colors:** Gold/500 stroke, transparent fill
- **Size:** 32x32
- **Hotspot:** Center
- **Animation:** Continuous rotation (360° in 1s)

#### 6. Interact Cursor (F Key)
- **Shape:** Star with "F" badge overlay
- **Colors:** Rose (#E8A9A1) fill, gold stroke
- **Size:** 40x40
- **Hotspot:** Center
- **Animation:** Badge pulses (scale 1.0 → 1.15 → 1.0, 1.5s loop)

### Implementation
- **Format:** PNG with alpha channel
- **Resolution:** 64x64 (downscaled in-engine)
- **Path:** `/Game/Melodia/UI/Cursors/Cursor_*.png`
- **UE Setup:** Slate cursor resources in `DefaultGame.ini`

---

## 5. Sparkle FX Widget: WBP_SparkleFX

### Purpose
Shared sparkle animation widget for all UI feedback (success, hover, burst)

### Design Reference
Figma nodes: `Motion/SparkleBurst` (`72:2007`), `SparkleDrift` (`72:2101`)

### Visual Style
**Base:** Particle system of 4-point and 8-point stars
**Density:** Controlled by `data-mg` tier (full/soft/chrome/off)

### Sparkle Types

#### 1. Sparkle Burst (One-shot)
- **Trigger:** On success (save complete, level up, etc.)
- **Count:** 12 stars (8x 4pt, 4x 8pt)
- **Duration:** 0.6s
- **Pattern:** Radial burst from center
- **Colors:** Gold/500 → fade to transparent

#### 2. Sparkle Drift (Ambient)
- **Trigger:** On hover, idle state
- **Count:** 6 stars (all 4pt)
- **Duration:** 2s loop
- **Pattern:** Slow upward drift with horizontal sine wave
- **Colors:** Gold/500, opacity 40-60%

#### 3. Orrery Sparkle Orbit (Special)
- **Trigger:** Comic Orrery selection
- **Count:** 8 stars (all 8pt)
- **Duration:** 3s loop
- **Pattern:** Circular orbit around target
- **Colors:** Iris/500 (#6E5AA6), gold/500

### Component Structure
```
WBP_SparkleFX (Canvas Panel)
├─ Particle System (Niagara or UMG image array)
│  ├─ Star Pool (20 star images, recycled)
│  └─ Emitter Logic (spawn/move/fade)
└─ Density Controller (Float parameter)
```

### Properties
- `SparkleType` (Enum): Burst, Drift, Orbit
- `DensityTier` (Enum): Full, Soft, Chrome, Off
- `ColorOverride` (Color): Optional custom color
- `AutoPlay` (Boolean): Start animation on spawn
- `Loop` (Boolean): Loop animation (false for burst)

### Integration
- **C++ Hook:** `UMelodiaRhythmHUDWidget::TriggerSparkleBurst()`
- **UMG Hook:** Call `PlaySparkle()` from Blueprint
- **Settings:** Density tier from `WBP_Settings` → global variable

---

## 6. Filigree Border Widget: WBP_FiligreeBorder

### Design Reference
Figma node: `Game/FiligreeBatchO_Baroque` (`58:716`)

### Visual Style
**Base:** Baroque scrollwork borders
**Cute Elements:** Corner rosettes, divider scrolls, crest accents

### Filigree Types

#### 1. Corner Baroque
- **Shape:** Scrollwork corner with rosette
- **Usage:** Panel corners (MainMenu, SaveLoad)
- **Size:** 64x64
- **Color:** Gold/500

#### 2. Divider Scroll
- **Shape:** Horizontal scroll divider
- **Usage:** Section separators
- **Size:** Variable width, 16px height
- **Color:** Gold/500

#### 3. Crest Baroque
- **Shape:** Central crest with star
- **Usage:** Header accents
- **Size:** 128x64
- **Color:** Gold/500

#### 4. Medallion Rosette
- **Shape:** Circular rosette with star center
- **Usage:** Decorative accents
- **Size:** 48x48
- **Color:** Gold/500

### Component Structure
```
WBP_FiligreeBorder (SizeBox)
├─ Border Images (4x Image widgets for corners)
│  ├─ Top-Left (Corner Baroque)
│  ├─ Top-Right (Corner Baroque, mirrored)
│  ├─ Bottom-Left (Corner Baroque, mirrored)
│  └─ Bottom-Right (Corner Baroque, rotated)
├─ Top Edge (Image, repeatable scroll pattern)
├─ Bottom Edge (Image, repeatable scroll pattern)
├─ Left Edge (Image, repeatable scroll pattern)
├─ Right Edge (Image, repeatable scroll pattern)
└─ Optional Crest (Image, centered top)
```

### Properties
- `BorderThickness` (Float): Edge thickness (default: 16)
- `ShowCorners` (Boolean): Show/hide corner filigree
- `ShowCrest` (Boolean): Show/hide top crest
- `ColorOverride` (Color): Custom border color

---

## 7. Implementation Order

### Phase 1: Core Atoms (Today)
1. **Generate Design Tokens** → Run `generate_melodia_design_tokens.py`
2. **WBP_MenuButton** → Reusable button with cute corners
3. **WBP_ParchmentPanel** → Base panel for all UI

### Phase 2: Keybind System (This Week)
4. **WBP_KeybindBadge** → JRPG keybind badges
5. **Cursor Assets** → 6 cursor PNGs
6. **WBP_SparkleFX** → Shared sparkle widget

### Phase 3: Decorative Elements (Next Week)
7. **WBP_FiligreeBorder** → Baroque borders
8. **Additional Atoms** → SealSP, LaneInk, Hitline, PillowChip

---

## 8. Asset Requirements

### Textures Needed
- `T_ParchmentNoise` (noise texture for paper grain)
- `T_ScrollEdge` (repeatable scroll border pattern)
- `T_ClefWatermark` (musical clef for watermark)
- `T_Star4pt` (4-point star sprite)
- `T_Star8pt` (8-point star sprite)
- `T_FiligreeCorner` (corner scrollwork)
- `T_FiligreeScroll` (horizontal divider)
- `T_FiligreeCrest` (header crest)
- `T_FiligreeRosette` (circular rosette)

### Fonts Needed (verify import)
- `F_Syne` (brand/display)
- `F_InstrumentSerif` (display)
- `F_BricolageGrotesque` (body)
- `F_AzeretMono` (mono/technical)
- `F_Cinzel` (optional cover)

### Icons Needed
- `I_Hand` (interact)
- `I_Sword` (attack)
- `I_Sparkle` (skill)
- `I_Star` (ultimate)
- `I_Book` (menu)
- `I_Arrow` (back)

---

## 9. UE Data Asset Structure

### DA_MelodiaDesignTokens
```cpp
USTRUCT(BlueprintType)
struct FMelodiaColorToken
{
    GENERATED_BODY()
    FLinearColor Color;
    FString Description;
};

USTRUCT(BlueprintType)
struct FMelodiaSpacingToken
{
    GENERATED_BODY()
    float Value;
    FString Description;
};

USTRUCT(BlueprintType)
struct FMelodiaTypographyToken
{
    GENERATED_BODY()
    FFontFamily FontFamily;
    int32 FontSize;
    FString FontWeight;
    int32 LineHeight;
    float LetterSpacing;
    FString TextCase;
};

UCLASS()
class UMelodiaDesignTokens : public UDataAsset
{
    GENERATED_BODY()
    
public:
    // Color tokens
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FMelodiaColorToken> Colors;
    
    // Spacing tokens
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FMelodiaSpacingToken> Spacing;
    
    // Typography tokens
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FMelodiaTypographyToken> Typography;
    
    // Game-specific colors
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FLinearColor> GameColors;
    
    // Keybind colors
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FString, FLinearColor> KeybindColors;
};
```

---

## 10. Integration Checklist

### Design Tokens
- [ ] Run `generate_melodia_design_tokens.py`
- [ ] Create `DA_MelodiaDesignTokens` data asset
- [ ] Import JSON output to UE
- [ ] Verify all colors map correctly

### Widget Atoms
- [ ] Author `WBP_MenuButton` with all states
- [ ] Author `WBP_ParchmentPanel` with variants
- [ ] Author `WBP_KeybindBadge` with action mappings
- [ ] Author `WBP_SparkleFX` with density tiers
- [ ] Author `WBP_FiligreeBorder` with corner/edge variants

### Asset Pipeline
- [ ] Create/import all required textures
- [ ] Verify fonts are imported
- [ ] Create cursor PNGs
- [ ] Set up Slate cursor resources

### Testing
- [ ] Test button states in PIE
- [ ] Test keybind badge color mappings
- [ ] Test sparkle density tiers
- [ ] Test cursor hotspots
- [ ] Verify parchment panel tints

---

## 11. Figma MCP Integration

Since Figma MCP is available (`figma-remote-mcp-server`), we can:

1. **Pull Component Specs:**
   - Use `get_design_context(nodeId)` to pull exact dimensions
   - Extract color values directly from Figma
   - Get spacing measurements from Auto Layout

2. **Sync Tokens:**
   - Read `tokens.json` from Figma file
   - Compare with local version
   - Auto-generate UE data asset on change

3. **Export Assets:**
   - Export star sprites from Figma
   - Export filigree patterns
   - Export cursor designs

### MCP Actions to Implement
```python
# Pull button specs from Figma
figma.get_design_context(
    file_key="Yx8ud7n39NdWZvnNvo4Xlf",
    node_id="81:1795"  # Ctrl/MenuButton
)

# Pull parchment panel specs
figma.get_design_context(
    file_key="Yx8ud7n39NdWZvnNvo4Xlf",
    node_id="62:531"  # SoftMG/ParchmentPanel
)

# Export star sprite
figma.export(
    file_key="Yx8ud7n39NdWZvnNvo4Xlf",
    node_id="72:2007",  # SparkleBurst
    format="svg",
    scale=2
)
```

---

This spec provides a complete roadmap for creating cute, reusable UI elements that bridge the Figma design system to UE5 widgets with JRPG-specific keybind visualizations and adorable cursor assets.

## 12. 2026-08-01 Production Scope Update

### Canonical asset ownership
- Visual SSOT: `melodia-design-system/DESIGN-SYSTEM.md`.
- Generated game-art provenance: `my-site-clean/generated/assets/melodia-game-ui/ART_SOURCE.json`.
- Runtime beauty path: SoftMG plus `FiligreeBatchO_Baroque` only. Batch N and non-Baroque Batch O duplicates remain retired.
- `T_Melodia_SoftMG_Parchment` is an arch-shaped ornamental composition and must not be stretched as a generic panel fill.
- Use `/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise` for scalable parchment fields; use `T_Melodia_FiligreeDividerScroll` only as a shallow ornamental divider.

### Reusable production atoms
The project-wide implementation target is one shared set rather than per-screen styling:
1. Melodia CommonButton styles for Primary, Secondary, Choice, and Keybind states.
2. Typed Melodia text styles backed by Syne, Instrument Serif, Twinkle Star, and Noto Music roles; engine-default fonts are not an acceptable final state.
3. CommonInput action rows/controller data for Confirm, Back, Navigate, Interact, Open Menu, Dialogue Advance, and Dialogue Skip.
4. A focus-aware CommonActivatableWidget base that restores initial focus and delegates input-mode ownership to `UMelodiaInputContextSubsystem`.
5. A semantic UI feedback profile/router mapping hover, focus, confirm, back, denied, quest, Harmony, dialogue advance, and choice selection to sound/motion/FX.
6. One pooled UI sparkle renderer using the existing star sprites and respecting Full/Soft/Chrome/Off motion tiers.

### Cosmic Orrery main-menu treatment
The canonical website references are `components/melodia-cosmic.js` and `public/melodia/melodia-hero-cosmic.html`. Their palette, typography, constellation navigation, galaxy rotation, nebula drift, dust, shooting trails, responsive framing, and reduced-motion rules are design references—not a runtime WebBrowser dependency.

The Unreal implementation is native:
- CommonUI owns menu focus/actions.
- `AOrreryMainMenuGameMode` retains New/Continue/Load/Settings/opening/save/travel authority.
- `DA_OrreryRegistry` retains destination, unlock, icon, and map semantics.
- A 3D Orrery presentation actor and menu camera react to selection through presentation-only events.
- Niagara/material layers provide restrained stars, dust, nebula, orbit sparkle, and shooting trails with reduced-motion scaling.
- Existing assets to reuse include `L_WP_CosmicOrrery`, `SM_Terrain_CosmicOrrery`, `MI_NikkiHero_CosmicOrrery`, and the Cosmic Orrery PCG styles.

### Verified slideshow baseline
`/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow` now preserves `SlideArtwork`, `KickerText`, `TitleText`, `BodyText`, `AdvanceButton`, and `SkipButton`; uses full-screen artwork plus a render-safe parchment lower third; and compiles with zero warnings/errors. Proof: `Saved/MelodiaOpeningSlideshowPreview_Final.png`.

## 12. 2026-08-01 Production Scope Update

### Canonical asset ownership
- Visual SSOT: `melodia-design-system/DESIGN-SYSTEM.md`.
- Generated game-art provenance: `my-site-clean/generated/assets/melodia-game-ui/ART_SOURCE.json`.
- Runtime beauty path: SoftMG plus `FiligreeBatchO_Baroque` only. Batch N and non-Baroque Batch O duplicates remain retired.
- `T_Melodia_SoftMG_Parchment` is an arch-shaped ornamental composition and must not be stretched as a generic panel fill.
- Use `/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise` for scalable parchment fields; use `T_Melodia_FiligreeDividerScroll` only as a shallow ornamental divider.

### Reusable production atoms
The project-wide implementation target is one shared set rather than per-screen styling:
1. Melodia CommonButton styles for Primary, Secondary, Choice, and Keybind states.
2. Typed text styles backed by Syne, Instrument Serif, Twinkle Star, and Noto Music roles; engine-default fonts are not an acceptable final state.
3. CommonInput action rows/controller data for Confirm, Back, Navigate, Interact, Open Menu, Dialogue Advance, and Dialogue Skip.
4. A focus-aware CommonActivatableWidget base that restores initial focus and delegates input-mode ownership to `UMelodiaInputContextSubsystem`.
5. A semantic UI feedback profile/router mapping hover, focus, confirm, back, denied, quest, Harmony, dialogue advance, and choice selection to sound/motion/FX.
6. One pooled UI sparkle renderer using existing star sprites and respecting Full/Soft/Chrome/Off motion tiers.

### Cosmic Orrery main-menu treatment
The canonical website references are `components/melodia-cosmic.js` and `public/melodia/melodia-hero-cosmic.html`. Their palette, typography, constellation navigation, galaxy rotation, nebula drift, dust, shooting trails, responsive framing, and reduced-motion rules are design references—not a runtime WebBrowser dependency.

The Unreal implementation is native:
- CommonUI owns menu focus/actions.
- `AOrreryMainMenuGameMode` retains New/Continue/Load/Settings/opening/save/travel authority.
- `DA_OrreryRegistry` retains destination, unlock, icon, and map semantics.
- A 3D Orrery presentation actor and menu camera react to selection through presentation-only events.
- Niagara/material layers provide restrained stars, dust, nebula, orbit sparkle, and shooting trails with reduced-motion scaling.
- Reuse `L_WP_CosmicOrrery`, `SM_Terrain_CosmicOrrery`, `MI_NikkiHero_CosmicOrrery`, and the Cosmic Orrery PCG styles.

### Verified slideshow baseline
`/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow` preserves `SlideArtwork`, `KickerText`, `TitleText`, `BodyText`, `AdvanceButton`, and `SkipButton`; uses full-screen artwork plus a render-safe parchment lower third; and compiles with zero warnings/errors. Proof: `Saved/MelodiaOpeningSlideshowPreview_Final.png`.
