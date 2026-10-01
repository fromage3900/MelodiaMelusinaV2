---
name: elevenlabs-tts-integration
description: Workflow and reference for the ElevenLabs TTS integration in the Ascent Dialogue System (ADS). Covers setting the API key in Project Settings, generating voice audio for dialogue nodes, voice selection/preview, voice caching, output paths, and TTS troubleshooting. Use when working with text-to-speech, generating dialogue voice audio, configuring ElevenLabs in ACF, or debugging TTS generation issues.
globs: []
alwaysApply: false
---

# ElevenLabs TTS Integration for Ascent Dialogue System

## Overview

The ElevenLabs TTS integration provides seamless text-to-speech functionality for the Ascent Dialogue System, allowing developers to automatically generate high-quality voice audio for dialogue nodes using ElevenLabs' advanced AI voice synthesis technology.

## Features

### 🎙️ Core TTS Functionality
- **Real-time voice generation** from dialogue text
- **Voice selection** with dynamic API integration
- **Preview voice samples** with intelligent caching
- **Automatic audio asset creation** as USoundWave assets
- **Smart file naming** using participant tags and timestamps

### 🎛️ User Interface
- **Custom detail panel** with dedicated action buttons
- **Preview Voice** - Listen to voice samples before generating
- **Generate TTS** - Create audio assets from dialogue text  
- **Refresh Voices** - Update available voices from ElevenLabs API
- **Clear Cache** - Reset cached voice data

### ⚙️ Configuration & Settings
- **Project Settings integration** for centralized configuration
- **Configurable file paths** for generated and preview audio
- **API key management** with secure storage
- **Auto-assignment toggle** for generated audio
- **Model selection** (default: eleven_multilingual_v2)

### 🧠 Smart Caching System
- **1-hour voice cache** to minimize API calls
- **Preview audio caching** to avoid redundant downloads
- **Asset existence checking** before API requests
- **Automatic cache invalidation** on API key changes

## Quick Start Guide

### 1. Setup API Key

1. Go to **Edit > Project Settings**
2. Navigate to **Plugins > Ascent Dialogue Settings**
3. Enter your **ElevenLabs API Key** in the "ElevenLabs TTS" section
4. Configure output paths if needed:
   - **Final TTS Path**: Where generated dialogue audio is saved (default: `Audio/TTS/Generated/`)
   - **Preview Samples Path**: Where voice preview samples are saved (default: `Audio/TTS/Samples/`)

### 2. Using TTS in Dialogue Nodes

1. **Open a Dialogue Graph** in the editor
2. **Select a dialogue node** 
3. In the **Details Panel**, find the **"ElevenLabs TTS"** section
4. **Enable TTS**: Check `Use ElevenLabs TTS`
5. **Select Voice**: Choose from the dropdown or enter a manual Voice ID
6. **Generate Audio**: Click the "Generate TTS" button

### 3. Voice Management

#### Refresh Available Voices
- Click **"Refresh Voices"** to fetch the latest voices from your ElevenLabs account
- Reopen the Details Panel to see updated voice options

#### Preview Voices
- Select a voice from the dropdown
- Click **"Preview Voice"** to hear a sample before generating dialogue audio

#### Clear Cache
- Click **"Clear Cache"** to reset all cached voice data
- Useful when switching API keys or troubleshooting

## Configuration Reference

### Project Settings

Navigate to **Edit > Project Settings > Plugins > Ascent Dialogue Settings**:

| Setting | Description | Default Value |
|---------|-------------|---------------|
| **ElevenLabs API Key** | Your ElevenLabs API key for authentication | (empty) |
| **ElevenLabs Model** | AI model used for voice synthesis | `eleven_multilingual_v2` |
| **Default TTS Output Path** | Legacy setting for output path | `Audio/TTS/` |
| **Final TTS Path** | Where generated dialogue audio is saved | `Audio/TTS/Generated/` |
| **Preview Samples Path** | Where voice preview samples are saved | `Audio/TTS/Samples/` |
| **Auto Assign Generated Audio** | Automatically assign generated audio to SoundToPlay property | `true` |

### Dialogue Node Properties

In each dialogue node's **ElevenLabs TTS** section:

| Property | Description | Usage |
|----------|-------------|--------|
| **Use ElevenLabs TTS** | Enable TTS for this node | Check to activate TTS features |
| **Selected Voice Name** | Voice chosen from dropdown | Select from available voices |
| **Voice ID** | Auto-populated from selected voice | Read-only, shows current voice ID |
| **Manual Voice ID** | Override voice selection | Enter custom voice ID to bypass dropdown |

## Technical Implementation

### Architecture Overview

```
Dialogue Node → ElevenLabs API → MP3 Audio → USoundWave Asset → Sound To Play
                      ↓
               Voice Cache System ← Voice Management UI
```

### Key Components

1. **ADSGraphNode** - Enhanced with TTS functionality
2. **ADSGraphNodeDetailCustomization** - Custom UI for TTS controls  
3. **ADSDialogueDeveloperSettings** - Configuration management
4. **ElevenLabsCache Namespace** - Global voice caching system

### API Integration

- **Voice Listing**: `GET /v2/voices` - Fetches available voices
- **TTS Generation**: `POST /v1/text-to-speech/{voice_id}` - Generates audio
- **Preview Audio**: Uses `preview_url` from voice data

### Asset Management

- **Temporary Files**: Created in `ProjectIntermediateDir/ElevenLabsTTS/`
- **Final Assets**: Imported as USoundWave using AssetTools
- **Automatic Cleanup**: Temporary files removed after import
- **Package Management**: Proper UE5 asset registry integration

## File Structure

```
Content/
├── Audio/
│   └── TTS/
│       ├── Generated/          # Final dialogue audio assets
│       │   ├── TTS_Character_Player_20250817_183753.uasset
│       │   └── TTS_Character_NPC_20250817_184012.uasset
│       └── Samples/            # Voice preview samples
│           ├── Preview_lUTamkMw7gOzZbFIwmq4.uasset
│           └── Preview_9BWtsMqFjuBwoZ4n.uasset
│
ProjectIntermediateDir/
└── ElevenLabsCache/           # Temporary files (auto-cleaned)
    ├── Preview_lUTamkMw7gOzZbFIwmq4.mp3
    └── voices_cache.json
```

## Troubleshooting

### Common Issues

#### "No voices showing in dropdown"
- **Solution**: Click "Refresh Voices" button and reopen Details Panel
- **Cause**: Voice cache is empty or expired

#### "API key not set" error
- **Solution**: Set API key in Project Settings > Ascent Dialogue Settings
- **Location**: Edit > Project Settings > Plugins > Ascent Dialogue Settings

#### "Failed to generate TTS audio" 
- **Check**: API key validity and account credits
- **Check**: Network connectivity to ElevenLabs API
- **Check**: Voice ID exists in your account

#### Confirmation dialogs during import
- **Cause**: Unreal asking about import template usage
- **Solution**: Click "Yes" to use previous settings or "No" for defaults
- **Note**: This is normal Unreal Engine behavior for audio imports

#### Audio not playing after generation
- **Check**: Sound To Play property is properly assigned
- **Check**: Audio settings allow editor playback
- **Try**: Manually assign the generated USoundWave asset

### Debug Information

Enable logging by adding to your project's logging configuration:

```ini
[Core.Log]
LogTemp=Verbose
```

Look for log entries with:
- `"ElevenLabs"` - TTS operations
- `"Generated TTS audio"` - Successful generation
- `"Successfully imported TTS audio"` - Asset creation

## Best Practices

### Performance Optimization
- Use **voice caching** effectively - avoid clearing cache unnecessarily
- **Batch generate** multiple dialogue lines when possible
- Consider **pre-generating** critical dialogue during development

### Content Organization
- Use **meaningful participant tags** for better file naming
- Organize voice samples in the **Samples folder** for easy management
- Keep **generated audio** separate from preview samples

### Workflow Tips
- **Preview voices** before committing to generation
- Use **Manual Voice ID** for custom or premium voices
- **Test audio assignment** after generation to ensure proper playback
- **Save your project** after generating audio assets

### Voice Selection
- **Choose appropriate voices** for character types
- **Consider language/accent** matching for immersion
- **Test voice consistency** across multiple dialogue lines
- **Use preview function** to compare voices before deciding

## API Limits and Considerations

### ElevenLabs API Limits
- **Character limits** per request (check your plan)
- **Monthly usage quotas** (monitor in ElevenLabs dashboard)
- **Concurrent request limits** 
- **Voice access** depends on subscription tier

### Cost Management
- **Cache effectively** to reduce API calls
- **Preview first** to avoid generating unwanted audio
- **Monitor usage** through ElevenLabs dashboard
- **Consider batch processing** for large projects

## Advanced Usage

### Custom Voice Integration
1. Create custom voices in ElevenLabs dashboard
2. Use **Manual Voice ID** field to specify custom voice
3. Test with preview before generation

### Automation Workflows
- Generate TTS for all nodes in a dialogue tree
- Batch process multiple dialogue files
- Integrate with CI/CD pipelines for automated asset generation

### Integration with Other Systems
- **Animation System**: Sync lip-sync with generated audio
- **Localization**: Generate TTS for multiple languages
- **Character System**: Map voices to specific character archetypes

## Support and Resources

### Documentation
- [ElevenLabs API Documentation](https://elevenlabs.io/docs)
- [Unreal Engine Audio Documentation](https://docs.unrealengine.com/5.6/en-US/audio-and-sound-in-unreal-engine/)

### Community
- Report issues in the project repository
- Share feedback and feature requests
- Contribute improvements via pull requests

---

*This integration was developed to seamlessly combine ElevenLabs' cutting-edge TTS technology with Unreal Engine's robust dialogue system, providing developers with professional-quality voice generation capabilities directly within their development workflow.*