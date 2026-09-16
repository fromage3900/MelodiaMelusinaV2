# Melodia Compendium Bible

**Status:** DURABLE NARRATIVE / UI CONTENT REFERENCE  
**Purpose:** Define what the in-game Melodia Compendium contains, how entries sound, and how the UI reads them without becoming a second gameplay or persistence authority.  
**Runtime seam:** `UMelodiaPersonaContent::Compendium` + `UMelodiaPersonaSubsystem` Blueprint queries.  
**Voice authority:** [`MELODIA_CHARACTER_VOICE_BIBLE.md`](MELODIA_CHARACTER_VOICE_BIBLE.md).

## 1. What the Compendium is

The Compendium is **Melusina's travelling field archive**, not an omniscient wiki.

It records the people, motif creatures, instruments, places, musical phenomena, songs, and relics that become meaningful during the journey. It should feel like a beautiful object Melusina actually keeps: part field guide, part musical notebook, part scrapbook, part performer ego.

The player-facing structure is:

```text
WORLD FACT
  -> what this thing is / where it belongs

MUSICAL IDENTITY
  -> pitch, interval, mode, rhythm, timbre, motif, or response behavior

MELUSINA'S NOTE
  -> subjective marginalia in her voice

RELATIONSHIPS
  -> linked people / creatures / places / instruments / phenomena

OPTIONAL VOICE NOTE
  -> Melusina speaks or sings the marginalia
```

The Compendium should deepen curiosity, not replace environmental storytelling or Quill scenes.

## 2. Runtime ownership

The Compendium owns **presentation only**.

It does not decide:

- whether a quest is complete;
- whether an instrument is actually owned;
- combat state;
- party membership;
- wardrobe ownership;
- map state;
- progression;
- save data;
- whether a creature exists in a level.

Those remain with their existing systems.

`FMelodiaCompendiumEntry::UnlockFlagId` reads a bool from the canonical `FMelodiaNarrativeRecord::Flags`. Empty means the entry is visible from the start. Quill / gameplay may set an allowlisted narrative flag when a discovery genuinely occurs; the Compendium only reads that fact.

Do not create a Compendium-specific SaveGame, discovered-entry array, or second quest tracker.

## 3. Categories

The runtime enum is intentionally small:

### Character
People and recurring named beings whose relationships matter.

Examples: Melusina, Sir Melodious, named chapter figures.

### Motif Creature
Creatures defined partly by a musical behavior or ecological motif.

Examples: Choral Sheep and future motif-creature families.

### Instrument
The twelve major instruments and other narratively meaningful musical tools.

An instrument entry should distinguish:

- what it sounds like;
- what it does to the world;
- what idea/emotion it embodies;
- what other entries it relates to.

### Place
Worlds, regions, landmarks, settlements, gardens, routes, and stages worth remembering.

A place entry should describe **how the place answers music**, not merely its geography.

### Phenomenon
Recurring musical/world laws and observed effects.

Examples: Resonance, Chladni patterns, cymatic growth, false echoes, harmonic ecology.

### Song
Named songs, fragments, recurring motifs, duets, battle pieces, ceremonial phrases, and other compositions that acquire narrative meaning.

### Relic
Objects whose identity matters beyond ordinary inventory/equipment.

## 4. Entry schema

Runtime structure: `FMelodiaCompendiumEntry`.

| Field | Meaning |
|---|---|
| `EntryId` | Stable authored ID. Never derive gameplay identity from display text. |
| `Category` | One of the seven Compendium categories. |
| `DisplayName` | Player-facing title. |
| `Subtitle` | Short poetic/scientific descriptor. |
| `Summary` | Concise world-facing description. |
| `MusicalIdentity` | Pitch/mode/rhythm/timbre/motif/response behavior where relevant. |
| `FieldNote` | Melusina's subjective marginalia, written against the voice bible. |
| `Artwork` | Optional illustration, render, icon, plate, specimen image, or portrait. |
| `VoiceNote` | Optional spoken/sung performance snippet from Melusina's voicebank. |
| `UnlockFlagId` | Existing narrative flag that makes the entry visible; empty = always visible. |
| `RelatedEntryIds` | Stable links to other Compendium entries. |
| `Tags` | Search/filter/editorial metadata; never gameplay truth. |

The authored order inside `DA_MelodiaPersonaContent` is the default display order. The future UI may filter/group it without creating another copy of the data.

## 5. Writing grammar

### Summary = useful, clear, restrained

The Summary is not Melusina performing for the reader. It should make the world legible in one short paragraph.

Bad:

> Choral Sheep are whimsical magical sheep infused with the mystical power of music and harmony.

Better:

> A flocking motif creature whose fleece carries visible resonance patterns. Individuals answer nearby pitches with short harmonic calls; groups tend to settle into stable intervals.

### Musical Identity = observable musical behavior

Prefer concrete language:

- `C / E / G response cluster`;
- `bell-like attack; long glass decay`;
- `answers one measure late`;
- `phyllotaxis density rises with Resonance`;
- `minor-second interference around injured growth`.

Avoid ornamental pseudo-music theory that does not correspond to anything the project can represent.

### Field Note = Melusina is allowed to have opinions

This is where the Compendium becomes hers.

The note may be:

- funny;
- vain;
- affectionate;
- petty;
- wrong in an explicitly subjective way;
- revised by later knowledge;
- unexpectedly vulnerable.

It should usually be 1–4 sentences.

Example energy for a Choral Sheep note:

> It copied my middle C perfectly and then added a third above me. I was going to be offended, but unfortunately it was adorable.

Example energy for a Bell Tree note:

> They do not require an audience. This is apparently considered healthy behavior. I am studying it.

The Summary tells the player what is known. The Field Note tells the player something about **Melusina**.

## 6. Voicebank / audio rule

`VoiceNote` is optional and should be treated as a performance layer, not required narration for every entry.

Best uses:

- unusually funny notes;
- emotional revisions to an old entry;
- a hummed motif rather than speech;
- pronunciation / timbre demonstrations;
- instrument invocations;
- short creature imitations;
- chapter-ending observations.

Do not turn the Compendium into hundreds of mandatory voiced paragraphs. Short, characterful fragments will make the voicebank feel more alive and keep production bounded.

A strong trick is to let the **Musical Identity** field include a playable sound/motif later while `VoiceNote` contains Melusina reacting to it.

## 7. Discovery grammar

Entries should unlock because the player actually encountered/learned something, not because they opened a menu.

Preferred flow:

```text
world / Quill / progression establishes discovery
  -> existing narrative flag becomes true
  -> Compendium query now returns the entry
  -> UI may show NEW / update animation
```

Some foundational entries may have no unlock flag and exist from the start.

Do not create completion percentages that pressure the player to exhaustively collect lore unless the design later explicitly calls for it.

## 8. Revision as storytelling

The Compendium can express character growth by changing interpretation without falsifying objective world facts.

Preferred model:

- Summary stays stable unless knowledge genuinely changes.
- Field Note may change after later narrative flags / chapter variants are authored.
- Related entries can make old information newly meaningful.

If variant notes are added later, use existing progression/narrative truth to select them. Do not create a parallel emotional-state system.

This is especially useful for Melusina: an early note may interpret silence personally; a later one may notice the same phenomenon without assuming it is about her.

## 9. Initial seed set

The first authored pass should stay small enough to polish properly.

Suggested seed entries:

**Characters**
- Melusina
- Sir Melodious

**Motif Creatures**
- Choral Sheep

**Instruments**
- Sonic Scepter
- Phase Bell
- Crescendo Fan

**Places**
- Sea Above
- Bell Tree Garden

**Phenomena**
- Resonance
- Chladni Pattern
- Cymatic Ecology

This is a seed roster, not a completion checklist. Add entries when the game contains something worth remembering.

## 10. UI direction

The eventual UI should feel like an **illuminated field notebook crossed with a magical record sleeve**, not a settings database.

Useful layout:

```text
[category tabs / constellation index]

        ARTWORK / SPECIMEN

DISPLAY NAME
subtitle

WORLD NOTE
summary

MUSICAL IDENTITY
motif / pitch / behavior

MELUSINA'S NOTE        [play voice note]
field note

RELATED
linked entry chips / constellation lines
```

Design priorities:

1. illustration/specimen first;
2. typography and negative space;
3. musical identity as a visually distinct block;
4. handwritten/marginal-feeling Melusina note;
5. related entries as a navigable constellation;
6. optional voice playback;
7. no dense RPG-stat-table aesthetic unless a specific category needs numbers.

The UI should query `UMelodiaPersonaSubsystem`; it should not cache a second editable lore database inside widgets.

## 11. Identity test

A Compendium entry belongs when it helps answer at least one of these:

- What does this thing sound like?
- What answers it?
- What does it answer?
- How does it change in relationship with something else?
- What did Melusina initially think about it?
- What does knowing it reveal about the world?

If an entry is only generic fantasy lore that could be pasted into another game unchanged, rewrite or cut it.

**The Compendium is not where Melodia explains itself. It is where the player notices how much of Melodia is connected.**
