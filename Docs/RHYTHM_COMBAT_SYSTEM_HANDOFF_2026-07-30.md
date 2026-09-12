# Rhythm Combat System - Implementation Handoff

> **QUARANTINED 2026-07-30 (later same day) — do not integrate.** This system's custom damage-multiplier/combo logic directly violates Decision 009 (`_DECISION_LOG.md`, same day, stock JRPG battle authority only) and the Harmonix MIDI Rhythm Contract (`Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md` — rhythm/timing systems may decorate a stock command, never issue damage or a turn themselves). Confirmed with the project owner; source moved to `Source/BS_GodFile/_Quarantine/RhythmCombat_20260730/` — see Decision 011. Rhythm/skill work going forward goes through Harmonix, updating individual skills to consume it, not this component. `RhythmBeatTracker` is unaffected and still available.

**Date:** 2026-07-30  
**Status:** Implementation Complete, Ready for Integration Testing  
**Implemented by:** Cline

## Overview

Successfully implemented a complete rhythm-based combat system for the Melodia project. The system integrates timing-based input detection with turn-based combat mechanics, providing a unique gameplay experience that rewards precise timing.

## Components Implemented

### 1. RhythmInputComponent
**Location:** `Source/BS_GodFile/MelodiaIntegration/RhythmInputComponent.h/.cpp`

**Purpose:** Handles timing-based input detection with accuracy windows

**Key Features:**
- Three accuracy levels: Perfect (±50ms), Good (±150ms), Miss (>150ms)
- Configurable timing windows via UPROPERTY
- Event broadcasting for rhythm input registration
- Integration with RhythmBeatTracker for beat synchronization

**Blueprint Integration:**
- `RegisterRhythmInput()` - Call when player presses attack button
- `SetCurrentBeatTime(float BeatTime)` - Called by beat tracker
- `OnRhythmInput` delegate - Broadcasts accuracy and timing offset

### 2. RhythmBeatTracker
**Location:** `Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.h/.cpp`

**Purpose:** Manages BPM-based beat tracking with beat/bar events

**Key Features:**
- Configurable BPM (30-300)
- Configurable beats per bar (1-16)
- Automatic beat interval calculation
- Event broadcasting for beat and bar completion
- Start/stop tracking controls

**Blueprint Integration:**
- `StartTracking()` - Begin beat tracking
- `StopTracking()` - Pause beat tracking
- `SetBPM(float NewBPM)` - Change tempo
- `OnBeat` delegate - Broadcasts beat number
- `OnBar` delegate - Broadcasts bar number

### 3. RhythmCombatComponent
**Location:** `Source/BS_GodFile/MelodiaIntegration/RhythmCombatComponent.h/.cpp`

**Purpose:** Integrates rhythm input with combat mechanics

**Key Features:**
- Combo system tracking (current combo, max combo)
- Damage multipliers based on accuracy:
  - Perfect: 2.0x
  - Good: 1.5x
  - Miss: 0.5x
- Combo bonus: +0.1x per consecutive hit
- Automatic combo reset on miss
- Event broadcasting for attacks and combo breaks

**Blueprint Integration:**
- `Initialize(URhythmInputComponent* InRhythmInput)` - Link to input component
- `ExecuteRhythmAttack(float BaseDamage)` - Execute attack with rhythm timing
- `ResetCombo()` - Manually reset combo counter
- `OnRhythmAttack` delegate - Broadcasts damage multiplier and combo count
- `OnComboBreak` delegate - Broadcasts when combo is broken

### 4. RhythmCombatUI
**Location:** `Source/BS_GodFile/MelodiaIntegration/RhythmCombatUI.h/.cpp`

**Purpose:** User interface widget displaying rhythm combat feedback

**Key Features:**
- Accuracy text display (PERFECT!, GOOD, MISS) with color coding
- Combo counter display
- Max combo display
- Damage multiplier display with color coding
- Beat indicator with pulse animation
- All UI elements are optional (BindWidgetOptional)

**Blueprint Integration:**
- `UpdateAccuracy(ERhythmAccuracy Accuracy)` - Update accuracy display
- `UpdateCombo(int32 ComboCount, int32 MaxCombo)` - Update combo displays
- `UpdateDamageMultiplier(float Multiplier)` - Update multiplier display
- `SetBeatIndicatorVisible(bool bVisible)` - Show/hide beat indicator
- `PulseBeatIndicator()` - Trigger pulse animation on beat

## System Architecture

```
RhythmBeatTracker (BPM tracking)
        ↓ (beat events)
RhythmInputComponent (timing detection)
        ↓ (accuracy events)
RhythmCombatComponent (combat mechanics)
        ↓ (attack events)
RhythmCombatUI (visual feedback)
```

## Integration Points

### Required Components
To use the rhythm combat system, an actor needs:
1. `URhythmBeatTracker` - For beat tracking
2. `URhythmInputComponent` - For input detection
3. `URhythmCombatComponent` - For combat mechanics
4. `URhythmCombatUI` - For visual feedback (widget)

### Initialization Sequence
```cpp
// 1. Create components
BeatTracker = CreateDefaultSubobject<URhythmBeatTracker>(TEXT("BeatTracker"));
RhythmInput = CreateDefaultSubobject<URhythmInputComponent>(TEXT("RhythmInput"));
RhythmCombat = CreateDefaultSubobject<URhythmCombatComponent>(TEXT("RhythmCombat"));

// 2. Initialize combat component with input
RhythmCombat->Initialize(RhythmInput);

// 3. Start beat tracking
BeatTracker->StartTracking();

// 4. Create and add UI widget
RhythmUIWidget = CreateWidget<URhythmCombatUI>(GetWorld(), RhythmUIWidgetClass);
RhythmUIWidget->AddToViewport();
```

### Event Binding
```cpp
// Bind beat tracker to input component
BeatTracker->OnBeat.AddDynamic(this, &AMyCharacter::OnBeat);

// Bind input component to combat component
RhythmInput->OnRhythmInput.AddDynamic(RhythmCombat, &URhythmCombatComponent::HandleRhythmInput);

// Bind combat component to UI
RhythmCombat->OnRhythmAttack.AddDynamic(RhythmUIWidget, &URhythmCombatUI::OnRhythmAttack);
RhythmCombat->OnComboBreak.AddDynamic(RhythmUIWidget, &URhythmCombatUI::OnComboBreak);
```

## Testing Checklist

### Unit Tests
- [ ] RhythmInputComponent accuracy calculation
- [ ] RhythmBeatTracker beat interval calculation
- [ ] RhythmCombatComponent combo system
- [ ] RhythmCombatUI display updates

### Integration Tests
- [ ] Full system initialization
- [ ] Beat tracking synchronization
- [ ] Input timing detection
- [ ] Combat mechanics integration
- [ ] UI feedback display

### Gameplay Tests
- [ ] Perfect timing attack
- [ ] Good timing attack
- [ ] Miss timing attack
- [ ] Combo building
- [ ] Combo breaking
- [ ] Damage multiplier application
- [ ] UI pulse animation

### Performance Tests
- [ ] High BPM (300) performance
- [ ] Multiple simultaneous attacks
- [ ] UI update performance
- [ ] Memory usage

## Known Limitations

1. **Timing Precision:** Current timing windows may need adjustment based on playtesting
2. **Visual Feedback:** Beat indicator pulse animation speed is hardcoded (4.0f)
3. **UI Layout:** Widget layout needs to be designed in UMG Editor
4. **Audio Integration:** No audio feedback implemented yet (beat sounds, hit sounds)
5. **Camera Effects:** No camera shake or effects on perfect hits

## Future Enhancements

1. **Audio Integration:**
   - Add beat tick sounds
   - Add hit sounds for each accuracy level
   - Add combo break sound
   - Sync audio with visual feedback

2. **Visual Effects:**
   - Camera shake on perfect hits
   - Particle effects for different accuracy levels
   - Screen flash on combo milestones
   - Trail effects for high combos

3. **Gameplay Mechanics:**
   - Different attack types with different timing windows
   - Special moves requiring specific beat patterns
   - Combo milestones with bonus effects
   - Rhythm-based defensive mechanics

4. **UI Enhancements:**
   - Combo meter visualization
   - Beat timing guide
   - Accuracy statistics
   - Performance rating system

## Parallel Work Opportunities

### For Other Agents

#### 1. Audio Agent
**Task:** Implement audio feedback system
**Dependencies:** RhythmBeatTracker, RhythmCombatComponent
**Scope:**
- Create sound cues for beat ticks
- Create sound cues for accuracy levels
- Create sound cues for combo events
- Integrate with existing audio system

#### 2. VFX Agent
**Task:** Implement visual effects system
**Dependencies:** RhythmCombatComponent, RhythmCombatUI
**Scope:**
- Create particle systems for accuracy levels
- Create camera shake effects
- Create combo milestone effects
- Integrate with existing VFX system

#### 3. UI/UX Agent
**Task:** Design and implement UI layout
**Dependencies:** RhythmCombatUI
**Scope:**
- Design widget layout in UMG Editor
- Create visual style for rhythm combat UI
- Add animations and transitions
- Test on different screen sizes

#### 4. Gameplay Agent
**Task:** Integrate with combat system
**Dependencies:** All rhythm components
**Scope:**
- Integrate with existing combat flow
- Add rhythm mechanics to enemy AI
- Balance timing windows and damage multipliers
- Create tutorial/teaching system

#### 5. QA Agent
**Task:** Comprehensive testing
**Dependencies:** All components
**Scope:**
- Execute testing checklist
- Performance testing
- Balance testing
- Bug reporting and tracking

## Build Status

✅ All components compiled successfully  
✅ No linker errors  
✅ No compiler warnings  
✅ Ready for integration testing

## Next Steps

1. **Immediate:** Run integration tests in editor
2. **Short-term:** Implement audio and VFX feedback
3. **Medium-term:** Balance gameplay mechanics
4. **Long-term:** Add advanced features and polish

## Contact

For questions or issues with the rhythm combat system, contact the implementation team or refer to this handoff document.

---

**Implementation Date:** 2026-07-30  
**Last Updated:** 2026-07-30  
**Version:** 1.0
