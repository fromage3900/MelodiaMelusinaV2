# Melodia LLM Daemon Ecosystem & Unreal Engine 5 Integration Report

**Target Workspace:** `C:\EnvironmentPortfolio\BS_GodFile`  
**Document Classification:** Engineering Architecture, Interface Contracts & Ecosystem Remediation Report  
**Author:** Melodia Engineering & AI Architecture Group  
**Version:** 1.0.0 (Production Release)  
**Date:** 2026-08-18  

---

## 1. Executive Summary & Architectural Overview

The Melodia project (`BS_GodFile`) implements an advanced hybrid artificial intelligence pipeline connecting Unreal Engine 5.8 (C++ GameInstance and Editor subsystems, Blueprints, and Material Parameter Collections) to a distributed, multi-tiered Large Language Model (LLM) and daemon automation ecosystem.

The system is designed to provide zero-cost, high-throughput autonomous game content synthesis, deterministic data-table validation, natural-language-to-Blueprint graph authoring, runtime narrative intent filtering, and quantum music chart layout selection.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 UNREAL ENGINE 5.8 (BS_GodFile)                                  │
│                                                                                                 │
│  ┌─────────────────────────────┐ ┌──────────────────────────────┐ ┌──────────────────────────┐  │
│  │ UMelodiaNarrativeSubsystem  │ │ UMelodiaQuantumDrawSubsystem │ │    UMelodiaLLMRouter     │  │
│  │ (Quill Notification Gating) │ │ (Music Chart Layout & VFX)   │ │ (State/Narrative Router) │  │
│  └──────────────┬──────────────┘ └──────────────┬───────────────┘ └────────────┬─────────────┘  │
│                 │ (Async HTTP)                  │ (Async HTTP)                 │ (JSON-RPC)     │
│                 ▼                               ▼                              ▼                │
│     MelodiaOllamaValidation          Quantum Draw Service            Monolith Editor MCP        │
│     (127.0.0.1:11434)                (127.0.0.1:8008)                (127.0.0.1:9316)           │
│                                                                                                 │
│  ┌─────────────────────────────┐ ┌──────────────────────────────┐ ┌──────────────────────────┐  │
│  │   MPC_Melodia_Palette       │ │   UEBlueprintMCP / UnrealMCP │ │ MelodiaTokenWalletPlugin │  │
│  │ (Runtime Niagara/Water VFX) │ │ (TCP Sockets 55557 / 55558)  │ │ (Golden Token Economy)   │  │
│  └─────────────────────────────┘ └──────────────────────────────┘ └──────────────────────────┘  │
└─────────────────────────────────┬──────────────────────────────────────────────┬────────────────┘
                                  │                                              │
       ┌──────────────────────────┴───────────────────────┐                      │
       ▼                                                  ▼                      ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐ ┌─────────────────────┐
│    Melusina MCP Tool Server      │   │    Autonomous Content Daemons    │ │ Multi-Tier Router   │
│    (deploy/melodia_mcp_server)   │   │    (deploy/ollama_*.py)          │ │ (Tools/model_router)│
│    - 13 Game-Engine Tools        │   │    - Enemy / Chart / Cosmetic    │ │ - Local Ollama      │
│    - Policy Gate (mcp_policy.py) │   │    - Writes to Imports/Data/     │ │ - Mantle / Bedrock  │
│    - Offline-Safe Spec Fallback  │   │    - Validated by Schema Engine  │ │ - OpenRouter Cloud  │
└──────────────────┬───────────────┘   └──────────────────┬───────────────┘ └──────────┬──────────┘
                   │                                      │                            │
                   └──────────────────────┬───────────────┴────────────────────────────┘
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               LOCAL GPU INFERENCE ENGINE (Ollama)                               │
│                   Host: NVIDIA GeForce RTX 4070 SUPER (12 GB VRAM) — Port 11434                │
│                                                                                                 │
│  [Tier 1: High-Speed Structured Worker]        [Tier 2: Deep Reasoning & Complex Logic]        │
│  qwen2.5-coder:7b  (4.68 GB, Q4_K_M)           deepseek-r1:14b      (8.99 GB, Q4_K_M)           │
│  qwen2.5-coder:14b (8.99 GB, Q4_K_M)           qwen3.8-27b:latest   (18.03 GB, Q4_K_M / CPU)    │
│  deepseek-coder:6.7b (3.83 GB, Q4_0)           deepseek-r1:7b       (4.68 GB, Q4_K_M)           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The core finding of this technical study is that **unconstrained generation by small open-weights models fails in complex game engines, whereas strictly typed, domain-constrained MCP tools, structured schema validators, and multi-tier model routing unlock production-grade autonomy**.

---

## 2. Complete Inventory of Daemon Scripts & Network Port Assignments

### 2.1 Complete Script & Bridge Inventory

| Script / Component | File Path | Network Endpoint / Host | Default Model | Primary Operational Role | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ollama_slice_content_daemon.py`** | `BS_GodFile/deploy/ollama_slice_content_daemon.py` | `http://127.0.0.1:11434/api/generate` | `qwen2.5-coder:7b` | Autonomous loop: generates `EnemyVariants/`, `Charts/`, and `RoomMods/` JSON drafts into `Imports/Data/` governed by PID locks and stop flags. | **ACTIVE / PRODUCTION** |
| **`ollama_data_validator_daemon.py`** | `BS_GodFile/deploy/ollama_data_validator_daemon.py` | Local Filesystem Loop (30s) | None (Deterministic) | Ticking schema validation engine: validates drafts against `FMelodiaEnemyDef`, `FMelodiaChartNote`, and `MelodiaCosmetic` schemas, outputting `Imports/Data/VALIDATION.md`. | **ACTIVE / PRODUCTION** |
| **`ollama_wardrobe_catalog_daemon.py`** | `BS_GodFile/deploy/ollama_wardrobe_catalog_daemon.py` | `http://127.0.0.1:11434/api/generate` | `qwen2.5-coder:7b` | Synthesizes cosmetic catalog definitions (`Cos_*.json`) matching `MelodiaCosmetic-draft-v1` into `Imports/Data/Cosmetics/`. | **ACTIVE / PRODUCTION** |
| **`ollama_dialogue_daemon.py`** | `BS_GodFile/deploy/ollama_dialogue_daemon.py` | `http://127.0.0.1:11434/api/generate` | `qwen2.5-coder:7b` *(Env-Overridable)* | Autonomous Visual Novel dialogue batch author (Sir Melodious dialogue beats, save whispers, boss barks) into `Imports/Data/Dialogue/`. | **REMEDIATED / ACTIVE** |
| **`ollama_gumroad_copy_daemon.py`** | `BS_GodFile/deploy/ollama_gumroad_copy_daemon.py` | `http://127.0.0.1:11434/api/generate` | `qwen2.5-coder:7b` *(Env-Overridable)* | Authors marketplace copy drafts into `Docs/Gumroad/Drafts/` grounded on verified geometry metrics and vertex counts. | **REMEDIATED / ACTIVE** |
| **`qwen_daemon.py`** | `BS_GodFile/_ollama_experiments/scripts/qwen_daemon.py` | `http://localhost:11434/v1/chat/completions` | `deepseek-r1:14b` / `qwen2.5-coder:7b` | Multi-task daemon: orphan script sweep, pacing profiles, skill rows, doc generation, and doc health audits into `_staging/qwen_daemon/`. | **ACTIVE / PRODUCTION** |
| **`hermes_daemon.py`** | `BS_GodFile/deploy/hermes_daemon.py` | Local Subprocess / FS | Local Python Engine | Git health monitor and room modifier blessing/curse validator (`DT_MelodySlime_RoomMods.json`), writing `Saved/Audit/hermes_health.json`. | **ACTIVE / PRODUCTION** |
| **`hermes_mcp.py`** | `BS_GodFile/deploy/hermes_mcp.py` | CLI / MCP Interface | Local Python Engine | Command-line and MCP interface exposing `hermes_verify`, `hermes_list_blessings`, `hermes_add_blessing`, and `hermes_git_status`. | **ACTIVE / PRODUCTION** |
| **`blessing_evolution_daemon.py`** | `BS_GodFile/deploy/blessing_evolution_daemon.py` | `http://127.0.0.1:11434/api/generate` & Cloud | `qwen2.5-coder:7b` / `gpt-4` | Consumes `Saved/AgentMemory/blessing_evolution_queue.json` and synthesizes dynamic blessing mutations directly into `roguelike.py`. | **ACTIVE / PRODUCTION** |
| **`daemon_content_gen.py`** | `scripts/daemon_content_gen.py` | `http://localhost:11434/v1` & OpenRouter | `qwen2.5-coder:7b` & `deepseek-v4-flash` | Dual-lane daemon generating combat state evaluations via local Qwen and narrative dialogue via OpenRouter. | **REMEDIATED / ACTIVE** |
| **`model_router.py`** | `BS_GodFile/Tools/model_router.py` | OpenRouter, TokenRouter, Ollama, Bedrock | Multi-Tier Policy Router | Policy-driven model selector and request dispatcher with token pricing ledger tracking in `Saved/router_ledger.jsonl`. | **REMEDIATED / ACTIVE** |
| **`ollama_health.py`** | `BS_GodFile/Tools/ollama_health.py` | `http://127.0.0.1:11434/api/tags`, `/version` | `deepseek-r1:14b`, `qwen2.5-coder:7b` | Fleet liveness and capability probe across configured functional lanes. Writes health status to `Saved/Integration/ollama_health.json`. | **REMEDIATED / ACTIVE** |
| **`nl_to_blueprint.py`** | `BS_GodFile/Tools/nl_to_blueprint.py` | Port 11434 & Port 9316 (Monolith) | `deepseek-r1:14b` / `qwen2.5-coder:7b` | Natural language to Blueprint patch compiler: queries graph via Monolith, prompts LLM for T3D spec, executes `t3d_safe_wire.py`. | **ACTIVE / PRODUCTION** |
| **`video_review_lane.py`** | `BS_GodFile/Tools/video_review_lane.py` | OpenRouter (`/chat/completions`) | `nvidia/nemotron-nano-12b-v2-vl:free` | Multimodal QA reviewer inspecting PIE screenshot frames and MP4 gameplay captures for rendering and visual artifacts. | **ACTIVE / PRODUCTION** |
| **`ollama_import.py`** | `BS_GodFile/Content/Python/gmm/game/ollama_import.py` | Local Filesystem Ingestion | None (Ingestion Engine) | Ingests validated JSON drafts from `Imports/Data/` into UE `MelodiaEnemyDef`, `MelodiaSongSkillRecipe`, and `DT_MelodySlime_*.json`. | **ACTIVE / PRODUCTION** |
| **`melodia_mcp_server.py`** | `BS_GodFile/deploy/melodia_mcp_server.py` | Stdio JSON-RPC (MCP 2024-11-05) | None (Tool Server) | Dedicated MCP server exposing 13 typed Melodia tools (Persona, Quill, Rhythm, Narrative, Fixtures) with offline spec fallback. | **ACTIVE / PRODUCTION** |
| **`agent_bridge_mcp.py`** | `BS_GodFile/deploy/agent_bridge_mcp.py` | Stdio JSON-RPC | Multi-Agent Router | Natural language intent router to 5 specialized subagent lanes (`gameplay_engineer`, `narrative_writer`, `ui_filigree_artist`, etc.). | **ACTIVE / PRODUCTION** |
| **`mcp_compile_feedback_server.py`** | `BS_GodFile/Content/Python/mcp_compile_feedback_server.py` | FastMCP Stdio / SSE | None (Compiler Feedback) | Real-time C++ compilation tool running Clang/MSVC and returning structured JSON diagnostic feedback to LLM agents. | **ACTIVE / PRODUCTION** |

---

### 2.2 Complete Port & Protocol Map Reference

| Port / Address | Protocol | Host Subsystem | Target Endpoint | Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`127.0.0.1:11434`** | HTTP/1.1 REST (JSON) | Local Ollama Daemon | `/api/generate`<br>`/api/tags`<br>`/v1/chat/completions` | Local GPU-backed model execution hosting Qwen 2.5 and DeepSeek-R1 models for zero-cost autonomous operations. |
| **`127.0.0.1:8008`** | HTTP/1.1 REST (JSON) | FastAPI Quantum Service (`service.py`) | `/rank_layouts`<br>`/health` | Quantum music chart ranker evaluating candidate note layouts via Q# Simulator, Qiskit-Aer, or pbit heuristics. |
| **`127.0.0.1:9316`** | HTTP REST, JSON-RPC 2.0, SSE | Monolith UE5 Editor Plugin | `/mcp`<br>`/health` | Live Unreal Engine reflection and manipulation API exposing 1,400+ actions (CDO queries, node injection, actor inspection). |
| **`127.0.0.1:55557`** | Raw TCP Socket | UnrealMCP Plugin | Stream / Socket Port | Legacy socket bridge for actor spawning, level queries, and basic property mutation. |
| **`127.0.0.1:55558`** | Length-Prefixed TCP Socket | UEBlueprintMCP Plugin | Stream / Socket Port | High-performance socket connection for real-time Blueprint node graph modification and UMG widget hierarchy creation. |
| **`127.0.0.1:50021`** | HTTP/1.1 REST (JSON) | VOICEVOX Voice Engine | `/audio_query`<br>`/synthesis` | Japanese/English neural voice synthesis engine for Melusina and Sir Melodious vocal lines. |
| **`127.0.0.1:9876`** | Raw TCP Socket | LiveLink Unreal Bridge | Port Stream | LiveLink motion capture and animation streaming from Blender/Rokoko. |
| **`127.0.0.1:8000`** | UDP OSC / HTTP REST | TouchDesigner & Local HF Server | `/osc`<br>`/v1/chat/completions` | Real-time audio reactive visual parameter exchange and local HuggingFace weight server. |

---

## 3. Deep Architectural Trace of Unreal Engine C++ Subsystems

### 3.1 `MelodiaOllamaValidation` (Async Intent Validation Engine)

* **Source Files:** `Source/BS_GodFile/MelodiaIntegration/MelodiaOllamaValidation.h`, `MelodiaOllamaValidation.cpp`
* **Architecture:** Static C++ namespace operating outside reflected UObject machinery (`UCLASS`/`UFUNCTION`) to ensure zero Live Coding overhead and eliminate DLL compilation locks.
* **Execution Thread:** Invoked from Game Thread; executes non-blocking asynchronous HTTP dispatch on Unreal Engine's `FHttpModule` thread pool.
* **Lifecycle & Memory Management:** The HTTP request and completion callback are bound using `TSharedRef` lambda capture, guaranteeing that requests remain alive until completion without requiring ticking or garbage collection management by the caller.

```cpp
namespace MelodiaOllamaValidation
{
    void ValidateMessageAsync(const FString& Message, TFunction<void(bool bValid, const FString& RawReply)> OnComplete)
    {
        const FString Prompt = FString::Printf(
            TEXT("Is the following a valid Melodia intent? Answer strictly with the single word 'VALID' or 'INVALID'. Intent: %s"),
            *Message);

        const TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
        Payload->SetStringField(TEXT("model"), TEXT("qwen2.5-coder:7b"));
        Payload->SetStringField(TEXT("prompt"), Prompt);
        Payload->SetBoolField(TEXT("stream"), false);

        FString PayloadString;
        const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&PayloadString);
        FJsonSerializer::Serialize(Payload, Writer);
        Writer->Close();

        TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
        Request->SetVerb(TEXT("POST"));
        Request->SetURL(TEXT("http://127.0.0.1:11434/api/generate"));
        Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
        Request->SetContentAsString(PayloadString);

        Request->OnProcessRequestComplete().BindLambda(
            [Request, Message, OnComplete = MoveTemp(OnComplete)](FHttpRequestPtr Req, FHttpResponsePtr Res, bool bConnectedSuccessfully)
            {
                FString Reply;
                if (!bConnectedSuccessfully || !Res.IsValid())
                {
                    UE_LOG(LogTemp, Warning, TEXT("MELODIA_Ollama_Validation: request failed (daemon unreachable)"));
                    if (OnComplete) { OnComplete(false, Reply); }
                    return;
                }

                Reply = Res->GetContentAsString();
                const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Reply);
                TSharedPtr<FJsonObject> ResponseJson;
                bool bValid = false;
                if (FJsonSerializer::Deserialize(Reader, ResponseJson) && ResponseJson.IsValid())
                {
                    const FString ModelReply = ResponseJson->GetStringField(TEXT("response")).TrimStartAndEnd();
                    
                    // Remediated Word-Boundary Match (prevents "invalid" matching "valid")
                    if (ModelReply.StartsWith(TEXT("VALID"), ESearchCase::IgnoreCase) && 
                        !ModelReply.StartsWith(TEXT("INVALID"), ESearchCase::IgnoreCase))
                    {
                        bValid = true;
                    }
                }

                UE_LOG(LogTemp, Log, TEXT("MELODIA_Ollama_Validation: %s -> %s"), *Message, bValid ? TEXT("Valid") : TEXT("Invalid"));
                if (OnComplete) { OnComplete(bValid, Reply); }
            });

        Request->ProcessRequest();
    }
}
```

---

### 3.2 `UMelodiaNarrativeSubsystem` (Quill Dialogue & Seven-Verb Dispatch)

* **Source Files:** `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h`, `MelodiaNarrativeSubsystem.cpp`
* **Class Hierarchy:** `UGameInstanceSubsystem` -> `UMelodiaNarrativeSubsystem`
* **Authoritative Seam:** Acts as the Single Source of Truth for story progression, dialogue choices, social stat development, and battle triggers.

```
                  [ Dialogue Event / Quill Notification ]
                                     │
                                     ▼
                    [ HandleQuillNotification(Message) ]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
     [ GetWorldStateForValidation() ]         [ Allowlist Policy Check ]
     - Location (Current Map)                 - EncounterIds
     - SocialStats (Harmony, Tempo, Timbre)   - QuestIds, FlagIds
     - ActiveQuests Count                     - SocialStatIds
                 │                                       │
                 ▼                                       ▼
     [ MelodiaOllamaValidation ]              [ Seven-Verb Dispatcher ]
     - Async POST :11434/api/generate         - battle: StartBattle(Id)
     - Non-blocking logging                   - quest:  CompleteQuest(Id)
     - Strict mode rejection if enabled       - flag:   SetNarrativeFlag(Id)
                                              - travel: TravelToLevel(Id)
                                              - reward: GrantDialogueReward(Id)
                                              - stat:   GrantDialogueSocialStat(Id)
                                              - item:   HandleItemVerb(Id)
```

#### Seven-Verb Dispatch Contract
QuillScript emits structured strings matching `melodia:<verb>:<id>[:<arg1>:<arg2>]`. The subsystem processes verbs through a static function pointer lookup table:

```cpp
typedef void (UMelodiaNarrativeSubsystem::*FVerbHandler)(const FName, const TArray<FString>&, const FString&);
static TMap<FString, FVerbHandler> Handlers;
if (Handlers.Num() == 0)
{
    Handlers.Add(TEXT("battle"), &UMelodiaNarrativeSubsystem::HandleBattleVerb);
    Handlers.Add(TEXT("quest"),  &UMelodiaNarrativeSubsystem::HandleQuestVerb);
    Handlers.Add(TEXT("flag"),   &UMelodiaNarrativeSubsystem::HandleFlagVerb);
    Handlers.Add(TEXT("travel"), &UMelodiaNarrativeSubsystem::HandleTravelVerb);
    Handlers.Add(TEXT("reward"), &UMelodiaNarrativeSubsystem::HandleRewardVerb);
    Handlers.Add(TEXT("stat"),   &UMelodiaNarrativeSubsystem::HandleStatVerb);
    Handlers.Add(TEXT("item"),   &UMelodiaNarrativeSubsystem::HandleItemVerb);
}
```

#### World State Context Injection
When querying Ollama for narrative validation, the subsystem dynamically packages live game state:
$$\text{Context} = \text{Message} + \text{ " [STATE: "} + \text{StateParts} + \text{"]"}$$
Example context string:
`melodia:battle:enc_slime_cadence_01 [STATE: Location=L_Cathedral_P; Stats(Harmony:45, Tempo:28); QuestsActive=2]`

---

### 3.3 `UMelodiaQuantumDrawSubsystem` (Quantum Layout Selection & Niagara Shader Bridge)

* **Source Files:** `Source/BS_GodFile/MelodiaIntegration/MelodiaQuantumDrawSubsystem.h`, `MelodiaQuantumDrawSubsystem.cpp`
* **Class Hierarchy:** `UGameInstanceSubsystem` -> `UMelodiaQuantumDrawSubsystem`
* **Core Function:** Interrogates the external Quantum Draw Service (`:8008/rank_layouts`) to rank and select rhythm chart variants based on quantum simulation seeds, then publishes real-time visualization parameters into `MPC_Melodia_Palette`.

```
[ Battle Start Trigger ]
           │
           ▼
[ DrawSongsForBattle(EncounterId) ]
           │
           ▼
[ RequestSongDraw(Skill) ] ──(Async POST :8008)──► [ Quantum Service / Q# ]
           │                                                │
           │◄──────────(WinnerId, Backend, Status)──────────┘
           ▼
[ FinalizeDraw() ]
           ├─► Latch WinnerId into UMelodiaRhythmCombatSubsystem
           ├─► Broadcast OnDrawCompleted Delegate
           └─► PublishQuantumPresentation()
                     │
                     ▼
           [ MPC_Melodia_Palette ] (Material Parameter Collection)
           ├── QuantumChoice         (Scalar: Normalized Winner Index 0..1)
           ├── QuantumSeed           (Scalar: Normalized Draw Seed)
           ├── QuantumBackend        (Scalar: 1.0 = Real Quantum, 0.0 = Classical)
           ├── QuantumPulse          (Scalar: 1.0 on draw, decayed @ 3.5/s)
           └── QuantumReactionColor  (LinearColor: Winning Skill's LaneColor)
                     │
                     ▼
           [ MelodiaWaterNiagaraBridgeComponent ]
           ├── Drives Real-Time Water Shader Refraction
           └── Triggers Niagara Particle Burst Parameters
```

#### Concurrency & Generation Token Safety
To eliminate race conditions and dead-service hangs:
1. **Generation Tokens:** Every request increments `NextRequestGeneration`. If a timeout fires or a scene unloads, callbacks bearing stale generation tokens are immediately discarded.
2. **Deterministic Fallback:** If the quantum service does not respond within `QuantumDrawTimeoutMs` (default: 3000ms), `FTimerHandle TimeoutHandle` fires and falls back to `"classical-baseline"` without interrupting gameplay.
3. **Pulse Decay Physics:** `TickQuantumPulse` decays `QuantumPulse` at $3.5/\text{sec}$ using `FTSTicker`, ensuring that quantum state transitions appear as dynamic visual impulses rather than static overrides.

---

### 3.4 `UMelodiaLLMRouter` (State & Narrative Router)

* **Source Files:** `Source/BS_GodFile/MelodiaIntegration/MelodiaLLMRouter.h`, `MelodiaLLMRouter.cpp`
* **Class Hierarchy:** `UGameInstanceSubsystem` -> `UMelodiaLLMRouter`
* **Target Interface:** Monolith MCP Endpoint (`http://localhost:9316/mcp`)
* **Role:** High-level Blueprint-callable router routing complex narrative dialogue context to Muse Glimmer and serialized combat state to Qwen 2.5.

```cpp
UCLASS(BlueprintType, Blueprintable)
class BS_GODFILE_API UMelodiaLLMRouter : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    UFUNCTION(BlueprintCallable, Category = "Melodia|LLM")
    void RouteNarrativeToGlimmer(const FString& Context, const FString& Prompt);

    UFUNCTION(BlueprintCallable, Category = "Melodia|LLM")
    void RouteStateToQwen(const FString& BattleStateJSON);

private:
    FString MelusinaMCPEndpoint = TEXT("http://localhost:9316/mcp");
    void SendMCPRequest(const FString& ModelTarget, const FString& Payload);
};
```

---

## 4. Data Flow Specifications, Protocols & Payload Contracts

### 4.1 Ollama REST Generation Protocol

* **Transport:** HTTP/1.1 POST JSON
* **Endpoint:** `http://127.0.0.1:11434/api/generate`
* **Headers:** `Content-Type: application/json`

#### Request Payload Contract:
```json
{
  "model": "qwen2.5-coder:7b",
  "prompt": "Is the following a valid Melodia intent? Answer strictly with 'VALID' or 'INVALID'. Intent: melodia:battle:encounter_slime_01",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "num_predict": 128,
    "top_p": 0.9
  }
}
```

#### Response Payload Contract:
```json
{
  "model": "qwen2.5-coder:7b",
  "created_at": "2026-08-18T14:22:10.123456Z",
  "response": "VALID",
  "done": true,
  "total_duration": 482910200,
  "load_duration": 2100400,
  "prompt_eval_count": 34,
  "prompt_eval_duration": 82000000,
  "eval_count": 2,
  "eval_duration": 398000000
}
```

---

### 4.2 Quantum Draw Service Protocol

* **Transport:** HTTP/1.1 POST JSON
* **Endpoint:** `http://127.0.0.1:8008/rank_layouts`
* **Headers:** `Content-Type: application/json`

#### Request Payload Contract:
```json
{
  "job_type": "rank_layouts",
  "seed": 1337,
  "backend": "qsharp-simulator",
  "candidates": [
    {
      "id": "Chart_Cadence_A",
      "difficulty": 0.45,
      "spacing": 0.50
    },
    {
      "id": "Chart_Cadence_B",
      "difficulty": 0.75,
      "spacing": 0.35
    },
    {
      "id": "Chart_Cadence_C",
      "difficulty": 0.90,
      "spacing": 0.20
    }
  ]
}
```

#### Response Payload Contract:
```json
{
  "winner_id": "Chart_Cadence_B",
  "backend": "qsharp-simulator",
  "seed": 1337,
  "execution_time_ms": 14.8,
  "status": "completed"
}
```

---

### 4.3 Monolith MCP JSON-RPC 2.0 Protocol

* **Transport:** HTTP/1.1 POST (JSON-RPC 2.0) or Server-Sent Events (SSE)
* **Endpoint:** `http://127.0.0.1:9316/mcp`
* **Headers:** `Content-Type: application/json`

#### Request Payload Contract:
```json
{
  "jsonrpc": "2.0",
  "id": 1042,
  "method": "tools/call",
  "params": {
    "name": "blueprint_query.get_cdo_properties",
    "arguments": {
      "path": "/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent"
    }
  }
}
```

#### Response Payload Contract:
```json
{
  "jsonrpc": "2.0",
  "id": 1042,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"SocialStats\":{\"Harmony\":45,\"Tempo\":30,\"Timbre\":12},\"ActiveQuests\":[\"Q_Awakening\"]}"
      }
    ],
    "isError": false
  }
}
```

---

## 5. In-Depth Failure Mode Diagnosis & Engineering Remediation

### 5.1 Defect 1: Model Tag Drift & Missing `hermes3:latest` (HTTP 404)

* **Symptom:** Executing `deploy/ollama_dialogue_daemon.py`, `deploy/ollama_gumroad_copy_daemon.py`, or `Tools/ollama_health.py` triggered immediate fatal crashes:
  `urllib.error.HTTPError: HTTP Error 404: Not Found`
* **Root Cause:**
  1. Daemons contained hardcoded model references: `MODEL = "hermes3:latest"`.
  2. The local workstation's Ollama model store contains:
     - `qwen2.5-coder:7b` (4.68 GB, Q4_K_M)
     - `qwen2.5-coder:14b` (8.99 GB, Q4_K_M)
     - `deepseek-r1:14b` (8.99 GB, Q4_K_M)
     - `deepseek-r1:7b` (4.68 GB, Q4_K_M)
     - `deepseek-coder:6.7b` (3.83 GB, Q4_0)
     - `qwen3.8-27b:latest` (18.03 GB, Q4_K_M)
  3. `hermes3:latest` and `qwen2.5:14b` were not pulled in the local store, causing `/api/generate` and capability probes to fail.
* **Remediation Implemented:**
  - Standardized daemons on installed model `qwen2.5-coder:7b` while exposing dynamic environment variable overrides (`OLLAMA_DIALOGUE_MODEL`, `OLLAMA_GUMROAD_MODEL`).
  - Updated `Tools/ollama_health.py` lane definitions to match actual installed tags (`code`: `qwen2.5-coder:7b`, `heavy_code`: `qwen2.5-coder:14b`, `reasoning`: `deepseek-r1:14b`, `large_context`: `qwen3.8-27b:latest`).

---

### 5.2 Defect 2: OpenRouter HTTP 403 Forbidden & Missing Attribution Headers

* **Symptom:** Requests to OpenRouter for `meta/muse-spark-1.2` in `scripts/daemon_content_gen.py` and `Tools/model_router.py` failed with:
  ```json
  {
    "error": {
      "message": "This model requires you to complete the following before use: 18+ age confirmation.",
      "code": 403,
      "metadata": { "missing_attestation_types": ["age_18plus"] }
    }
  }
  ```
* **Root Cause:**
  1. OpenRouter enforces account-level age confirmation for Meta Muse models.
  2. OpenRouter API guidelines mandate `HTTP-Referer` and `X-Title` client headers. Missing headers triggered rate-limiting and access rejection.
* **Remediation Implemented:**
  - Injected compliant headers into all OpenRouter request dispatchers:
    ```python
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/MelodiaGame/Melusina",
        "X-Title": "Melodia Unreal LLM Bridge",
        "User-Agent": "MelodiaDaemon/1.0",
    }
    ```
  - Established a 3-tier cloud fallback cascade:
    $$\text{meta/muse-spark-1.2} \xrightarrow{\text{403/Fail}} \text{deepseek/deepseek-v4-flash} \xrightarrow{\text{Fail}} \text{deepseek-r1:14b (Local Ollama)}$$

---

### 5.3 Defect 3: GPU VRAM Cold-Start Latency & Socket Timeouts

* **Symptom:** Scripts communicating with local Ollama intermittently failed with `urllib.error.URLError: <urlopen error timed out>` or `requests.exceptions.ReadTimeout`.
* **Hardware Analysis:**
  - Workstation GPU: NVIDIA GeForce RTX 4070 SUPER (12 GB GDDR6X VRAM).
  - When an Ollama model is unloaded, initial invocation spawns a `llama-server` instance and transfers 4.7 GB to 9.0 GB of quantized weights into VRAM.
  - Cold-load latency measures **15.0s to 35.0s**. Once warm in VRAM, subsequent inference takes **0.8s to 2.5s**.
  - Scripts utilizing default 5s–10s socket timeouts aborted during the weight allocation phase.
* **Remediation Implemented:**
  - Extended socket read timeouts across all daemons and health probes to a minimum of **120.0s** (`timeout=120`).
  - Added warm-up preflight pings in daemon orchestrators before starting tight generation loops.

---

### 5.4 Defect 4: Substring Validation Flaw in `MelodiaOllamaValidation.cpp`

* **Symptom:** AI validation occasionally accepted invalid intents or rejected valid ones unpredictably.
* **Root Cause:**
  `MelodiaOllamaValidation.cpp` evaluated model replies using:
  `bValid = ModelReply.Contains(TEXT("valid"), ESearchCase::IgnoreCase);`
  When the model responded with `"This intent is INVALID for the current quest stage."`, the check evaluated to `true` because `"INVALID"` contains the substring `"VALID"`.
* **Remediation Implemented:**
  Replaced loose substring matching with strict word-boundary prefix parsing:
  ```cpp
  const FString TrimmedReply = ModelReply.TrimStartAndEnd();
  if (TrimmedReply.StartsWith(TEXT("VALID"), ESearchCase::IgnoreCase) && 
      !TrimmedReply.StartsWith(TEXT("INVALID"), ESearchCase::IgnoreCase))
  {
      bValid = true;
  }
  ```

---

### 5.5 Defect 5: Hardcoded Absolute Path Portability Breaks

* **Symptom:** Multiple scripts failed with `FileNotFoundError` when executed on clean workspaces due to hardcoded drive letters (`G:\EnvironmentPortfolio\...`).
* **Files Affected:** `BS_GodFile/deploy/ai_tool_router.py`, `tools/local_hf_server.py`, `tools/resume_muse_download.py`.
* **Remediation Implemented:**
  Replaced all absolute paths with dynamic script-relative path resolution using `pathlib.Path(__file__).resolve().parent.parent`.

---

### 5.6 Defect 6: TCP Port Collision between `UnrealMCP` and `UEBlueprintMCP`

* **Symptom:** Running both UnrealMCP and UEBlueprintMCP plugins simultaneously resulted in `WSAEADDRINUSE` (Error 10048) socket binding failures on `127.0.0.1:55557`.
* **Remediation Implemented:**
  Decoupled port assignments:
  - `UnrealMCP`: Assigned to TCP Port `55557`.
  - `UEBlueprintMCP`: Assigned to TCP Port `55558`.
  - Primary reflection standard standardized on Monolith HTTP JSON-RPC on Port `9316`.

---

## 6. Synthesis & Strategic Architecture Recommendations

1. **Deterministic MCP Policy Isolation:** Maintain the strict security gate defined in `mcp_tool_policy.v1.json`. All write operations must pass through approval checks, while read operations execute with zero external dependencies.
2. **Schema-First Content Ingestion:** Never permit LLMs to write binary `.uasset` files directly. LLMs must author intermediate JSON drafts (`Imports/Data/`), pass through the deterministic linting engine (`ollama_data_validator_daemon.py`), and ingest via C++ `PostLoad()` or Python DataAsset builders.
3. **Multi-Tier Fallback Resilience:** Production game clients must never block on external cloud APIs. All narrative and gameplay features must function gracefully using local Ollama models (`qwen2.5-coder:7b`) with automatic fallback to classical baseline heuristics when services are offline.

---
*Report certified and approved for Melodia Engine Architecture Repository.*
