# GenesisCore - Blender AI Automation Addon

## Introduction

A Blender automation addon driven by large language models (e.g. Deepseek, Claude).\
Using MCP protocol standardized interface, supports multiple LLM providers including DeepSeek, OpenAI, Anthropic, OpenRouter, SilicorFlow, etc.

## Manuals / 手册

* [中文](./README_CN.md)
* [English](./README.md)

## Features

* Built-in MCP Client implementation (No external MCP Host required)
* Supports multiple LLM providers: DeepSeek, OpenAI, Anthropic, OpenRouter, SilicorFlow, etc.
* Integrated Polyhaven online asset system (Models/HDRI)
* Supports local model libraries
* Conversational history control
* One-click provider switching with auto-loaded configurations
* SSE external MCP Host connection support
* Modular Tools system (Extendable)
* Modular Client integration (Extendable)

## Installation

### Blender

> Download and install [Blender](https://www.blender.org/download/) (Recommended version 4.0+)

### Windows

* Method 1: Using ZIP package
  1. Download package: <https://github.com/AIGODLIKE/GenesisCore.git>
  2. Blender -> Preferences -> Add-ons: Install from ZIP
  3. Or drag ZIP file directly into Blender window and follow prompts

* Method 2: Manual install (Requires Git)
  ```shell
  cd %USERPROFILE%\AppData\Roaming\Blender Foundation\blender\%blender_version%\scripts\addons
  git clone https://github.com/AIGODLIKE/GenesisCore.git
  ```
  * Enable addon via Blender Preferences -> Add-ons -> Search "GenesisCore"

### Linux

> For Linux users (Assumes basic proficiency):

```bash
cd /home/**USER**/.config/blender/**BLENDER_VERSION**/scripts/addons
git clone https://github.com/AIGODLIKE/GenesisCore.git
```

* Enable addon via Blender Preferences -> Add-ons -> Search "GenesisCore"

## Usage

### Basic Usage

1. Open UI panel in 3DViewport (N-Panel) -> GenesisCore panel
2. Select LLM provider (DeepSeek/OpenAI/Anthropic etc.)
3. Obtain corresponding API Key
4. Enter API Key in addon settings
5. Fetch supported model list
6. Select model
7. Choose tool modules (Disable "Asset Tools" if no custom assets needed)
   1. Hold shift to select multiple modules
8. Enter command
9. Execute command

### Advanced

1. Conversation History
   * Enabled: Consumes more tokens but maintains context
   * Disabled: Lower token usage, each command is isolated
   * Use "Clear History" to reset conversation context

2. Configuration Management
   * Config auto-saves when refreshing model list
   * Click "Save Config" to manually save current settings
   * Each provider maintains independent configurations

3. Polyhaven Integration
   * Requires enabling "Asset Tools" module
   * AI intelligently decides when to use Polyhaven assets
   * Downloaded assets cache to:
     * Windows: `C:\Users\{USER}\AppData\Local\Temp\polyhaven_{asset_type}`
     * Linux: `/tmp/polyhaven_{asset_type}` (I guess, caz I'm not a Linux user)
     * Asset types: `models`, `hdris`
   * Cached assets auto-load without re-downloading

4. External MCP Host Connection (Port 45677)
   ```json
   {
    "mcpServers": {
        "BlenderGenesis": {
        "url": "http://localhost:45677"
        }
    }
   }
   ```

5. Custom Tool Development
   * Reference existing modules in `src/tools/`
   * Note: Import new modules in `src/tools/__init__.py` (Order affects UI display)

6. Custom Client Development
   * Reference `src/client/openai.py` (MCPClientOpenAI implementation)

## Links

### Acknowledgements

Inspired by [BlenderMCP - Blender Model Context Protocol Integration](https://github.com/ahujasid/blender-mcp)

### Our AI Platform

[AIGODLIKE Community](https://www.aigodlike.com/)
