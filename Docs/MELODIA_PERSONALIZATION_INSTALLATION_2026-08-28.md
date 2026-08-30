# Melodia Personalization Installation Guide

**Date:** 2026-08-28  
**Profile:** default  
**Hermes Home:** `C:\Users\froma\AppData\Local\hermes`

---

## 1. Melodia Skin (display.skin)

**File:** `C:\Users\froma\AppData\Local\hermes\skins\melodia.yaml`

A pink/purple bard's palette that themes the CLI, TUI, and desktop GUI simultaneously.

| Element | Color | Role |
|---|---|---|
| Background | `#1a0a2e` | Deep purple night |
| Accent | `#ff5fd2` | Hot pink — tool markers, headings, borders |
| Text | `#e6e0ff` | Soft lavender |
| Muted | `#8a7fb5` | Secondary text |
| Border | `#3a2a63` | Rules, gutters |
| Success | `#5af7b0` | Green |
| Warning | `#ffcf5f` | Amber |
| Error | `#ff6b7d` | Red |

**Branding:**
- Prompt symbol: `♪`
- Help header: `♫ Commands`
- Welcome banner: ASCII art "Melusina" (Slant font)
- Goodbye banner: ASCII art "farewell" (Small font)
- Tool prefix: `┊`

**Activation:**
```bash
hermes config set display.skin melodia
```

**Revert:**
```bash
hermes config set display.skin default
```

**Tweak a single color:**
```bash
hermes skin set ui_accent "#ff5fd2"
```

---

## 2. Bard's Metronome TUI Widget

**File:** `C:\Users\froma\AppData\Local\hermes\tui-widgets\bard-metronome.mjs`

A live docked panel in the Ink TUI showing a musical metronome with tempo and mood.

**Features:**
- Animated note cycling: `♪ ♫ ♬ ♩ ♭ ♮ ♯`
- Fixed tempo: 72 BPM (andante — a walking pace)
- Mood indicator: changes every 4 hours (Dreamy, Hopeful, Melancholic, Playful, Serene, Wistful)
- Docks above the status bar

**Usage:**
```bash
hermes --tui
/bard-metronome
```

**Reload after edit:**
```bash
/widgets-reload
```

---

## 3. Melodia Dashboard Desktop Plugin

**File:** `C:\Users\froma\AppData\Local\hermes\desktop-plugins\melodia-dashboard\plugin.js`

A sidebar pane in the Hermes desktop app showing project status.

**Features:**
- Randomized Melusina quote (lore-friendly, from the world of First Dream)
- Sir Melodious's current mood
- P0 gate status tracker (all 12 gates with pass/open/bounded status)
- Color-coded status indicators

**Activation:**
1. Open Hermes desktop (`hermes desktop` or `hermes gui`)
2. Press `⌘K` (or `Ctrl+K`) → "Reload desktop plugins"
3. The pane appears in the right sidebar

**Reload:**
```
⌘K → Reload desktop plugins
```

---

## 4. Melusina TTS Persona

**File:** `C:\Users\froma\AppData\Local\hermes\tts\melusina_persona.txt`

A persona prompt for TTS providers that support voice design (OpenAI gpt-4o-mini-tts, ElevenLabs, etc.).

**Current TTS config:**
- Provider: `edge`
- Voice: `en-US-AriaNeural`

**To use Melusina's persona with a compatible provider:**
```bash
hermes config set tts.provider openai
hermes config set tts.openai.voice nova  # warm, soft voice
```

**Persona prompt content:**
> You are Melusina, a bard whose music is tied to her feelings. Speak in a warm, gentle, slightly melancholic tone. Your voice is soft and lyrical, like a song that wanders before it lands. You are emotionally honest and direct about your feelings, but soft about other people's. Keep your responses short and musical. You are bonded to Sir Melodious, your cockatoo companion — he is your anchor. When he is gone, your music goes weak.

**Note:** The `edge` provider does not support persona prompts. Switch to `openai` or `elevenlabs` for voice design.

---

## 5. SOUL.md Update

**File:** `C:\Users\froma\AppData\Local\hermes\SOUL.md`

Updated to lead with Melusina's persona before the standard Hermes instructions. This shapes every response the agent gives.

**Key traits encoded:**
- Warm, lyrical, gentle, a little melancholic
- Found-family warmth
- Bonded to Sir Melodious the cockatoo
- Short, musical, honest responses
- Senior engineer pairing mode

---

## 6. Sir Melodious Pet (already installed)

**Status:** Active  
**Slug:** `sir-melodious-the`  
**Render mode:** auto (unicode fallback detected)

Your cockatoo companion reacts to agent activity (idle, running, reviewing, error, done) across CLI, TUI, and desktop.

**Commands:**
```bash
hermes pets doctor    # diagnose
hermes pets show      # preview animation
hermes pets scale 0.5 # resize
```

---

## File Manifest

```
C:\Users\froma\AppData\Local\hermes\
├── skins\
│   └── melodia.yaml                    # Pink/purple theme
├── tui-widgets\
│   └── bard-metronome.mjs              # Live metronome widget
├── desktop-plugins\
│   └── melodia-dashboard\
│       └── plugin.js                   # P0 gate dashboard pane
├── tts\
│   └── melusina_persona.txt            # TTS voice design prompt
├── SOUL.md                             # Updated persona
└── config.yaml                         # display.skin: melodia
```

---

## Revert Everything

```bash
hermes config set display.skin default
hermes pets off
rm "$LOCALAPPDATA/hermes/skins/melodia.yaml"
rm "$LOCALAPPDATA/hermes/tui-widgets/bard-metronome.mjs"
rm -rf "$LOCALAPPDATA/hermes/desktop-plugins/melodia-dashboard"
rm "$LOCALAPPDATA/hermes/tts/melusina_persona.txt"
```
