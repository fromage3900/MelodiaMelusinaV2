# AI / Compute / 3D Freebie Deep Sweep — 2026-09-09

**Verified:** 2026-09-09 against current official provider pages.  
**Scope:** second-pass discoveries beyond the canonical Student Benefits Enrollment Ledger.  
**Rule:** claim legitimate benefits only; do not fabricate student, company, revenue, funding, or institutional status.

## P0 additions

| Program | Verified free benefit | Melodia use |
|---|---|---|
| **Gaea Student + Teacher Edition** | Free 1-year educational license, renewable for free while eligible; free major-version upgrade during term; non-commercial education use. | Terrain and environment-art studies. Official: https://www.quadspinner.com/Order/Education/Students |
| **Modal Starter** | **$30/month free compute credit**, $0 base plan, 100 containers + 10 GPU concurrency. | Remote Python/procedural/ML jobs. Official: https://modal.com/pricing |
| **Cloudflare Workers AI** | **10,000 Neurons/day free**, reset daily. Some frontier models require Paid, many remain Free. | Cheap hosted inference and web tooling. Official: https://developers.cloudflare.com/workers-ai/platform/pricing/ |
| **Groq Free** | Current free limits include GPT-OSS 120B/20B and Qwen 3.6/3.8 27B at 30 RPM, 1,000 RPD, 8K TPM, 200K TPD; Compound/mini 30 RPM / 250 RPD / 70K TPM. | Fast structured calls, agents, transcription. Official: https://console.groq.com/docs/rate-limits |
| **Vercel AI Gateway** | Free users who have not made a payment currently get **$5 credits every 30 days**; some models also expose true free provider routes. | Web/Hermes-compatible model routing. Official: https://vercel.com/ai-gateway |
| **OpenRouter Free Router** | `openrouter/free` is zero token cost, currently routes among 24 free models with 200K context and can filter for tools/structured outputs. | Disposable inference/agent experiments. Official: https://openrouter.ai/openrouter/free |
| **Replit Starter** | Free plan with **daily Agent credits**, one live project and one background task. | Tiny web/app prototype agent. Official: https://replit.com/pricing |
| **Gemini Developer API Free Tier** | General free API tier remains separate from the Google AI Pro student promotion that excludes Canada. | Multimodal experiments. Free-tier data may be used to improve Google products. Official: https://ai.google.dev/gemini-api/docs/pricing |

## Free GPU / compute

- **Kaggle Notebooks:** free NVIDIA Tesla P100; weekly GPU quota is generally **30 hours or sometimes higher** depending on demand/resources. https://www.kaggle.com/docs/efficient-gpu-usage
- **Google Colab Free:** free GPU/TPU access with dynamic, unpublished limits; free notebooks can run up to **12 hours** depending on availability and usage. https://research.google.com/colaboratory/faq.html
- **Lightning AI:** current free pricing advertises a free Studio and **up to ~80 free GPU hours / up to $30 free credits to start**, hardware-dependent. Treat this as introductory, not recurring, until the dashboard says otherwise. https://lightning.ai/pricing
- **Camber Student:** already canonical — 40 CPU hours + 5 GPU hours + 50 GB + 50 agent messages/month via GitHub Student Pack.

Routing: Camber for student-entitled unattended work; Modal for repeatable container jobs; Kaggle/Colab for notebook workloads; Lightning as an extra GPU pool. Save AWS/Azure credits for workloads that need those ecosystems.

## GitHub Student Pack — undercounted entitlements

Redeem after GitHub Student verification:

- **Appwrite Education:** 2 projects with Pro-equivalent resource limits, listed value **$40/month**, while in the Student Pack.
- **Datadog:** Pro account including 10 servers, free for 2 years.
- **Sentry:** 50K errors, 100K transactions, 1 GB attachments, 500 replays, Team features; 1 year and renewable.
- **Deepnote Team:** free while a student; unlimited projects/members, basic machines up to 5 GB RAM / 2 vCPU, premium integrations.
- **BrowserStack:** Automate Mobile Plan, 1 parallel / 1 user for 1 year.
- **LocalStack:** free license to its strongest AWS emulator in a ready-to-use cloud environment. **High priority for the existing Bedrock/Mantle lane.**
- **Doppler:** free Team subscription while an active student.
- **Blackfire:** free Developer subscription for students.
- **DevCycle:** 1 free year Starter Plan.
- **Icons8:** 3 months free for icons/photos/illustrations/music.
- **Zyte Scrapy Cloud:** 1 Free Forever Scrapy Cloud Unit.

Official pack: https://education.github.com/pack

Priority: **Appwrite → LocalStack → Sentry → BrowserStack → Deepnote → Doppler**.

## 3D / animation / environment-art additions

### Gaea Student + Teacher Edition
Biggest direct art miss from the first sweep. QuadSpinner explicitly targets students in Game Design, VFX and **Environment Art**. License lasts 1 year and can be renewed free while eligible. Educational/non-commercial.  
Official: https://www.quadspinner.com/Order/Education/Students and https://quadspinner.com/Support/FAQ/Educational

### Rokoko Starter
Current free-forever Starter includes:
- record/export mocap and cleanup filters
- FBX export
- **30 seconds/month Vision AI video-to-motion**
- **unlimited Text-to-Motion generation**
- **5 Text-to-Motion Studio imports/month**
- 1 month motion-asset cloud storage

Official: https://www.rokoko.com/pricing

### Meshy Free
Current free tier:
- **100 credits/month**, reset monthly, no rollover
- no card required
- current help page states **10 downloads/month for Meshy 6 Lite**
- free outputs are **CC BY 4.0**, including commercial use with attribution
- Discord connection gives **100 one-time bonus credits**
- accepted Contributor Program members can receive free Pro monthly

Official: https://www.meshy.ai/pricing/ and https://help.meshy.ai/en/articles/9991982-can-i-get-free-credits

Use for blockouts/reference/background ideation, with provenance and attribution review before portfolio use.

### V-Ray for Blender Community Edition
Chaos now provides a free V-Ray for Blender Community Edition, renewable every **3 months** at no cost. It is aimed at students, learning, content creation, and small-scale/personal freelance projects.  
Official: https://www.chaos.com/vray/blender/community

## Humber-specific trench

- **Microsoft Copilot Enterprise:** Humber's current GenAI guidance says the Humber Community has enterprise Microsoft Copilot with Humber privacy/data protections. Log in with Humber credentials and verify the exact student-tenant feature set. https://humber.ca/innovativelearning/generative-artificial-intelligence-teachlearn/
- **Microsoft 365 + 1 TB OneDrive:** Humber students receive 1 TB OneDrive during studies. https://humber.ca/its/resource-centre/microsoft-365
- **LinkedIn Learning:** campus-wide access for students/faculty/staff. https://humber.ca/linkedinlearning/
- **myApps / AppsAnywhere:** academic application catalog accessible from personal devices; some software streams or runs through AppStream/labs. **Browse this live catalog before graduation because it may expose expensive DCC/VFX licenses that public student-deal searches miss.** https://humber.ca/its/resource-centre/myapps-apps-anywhere

## Corrections / traps

1. Google AI Pro student subscription and Gemini Developer API Free Tier are separate; the former currently excludes Canada, the latter remains a general developer free route.
2. **GitHub Models was retired on 2026-07-30.** Do not plan around old GitHub Models free inference.
3. Cloudflare's 10K Neurons/day does not mean every model is accessible on Workers Free.
4. Free API privacy/retention varies. Check provider terms before sending unreleased project code.
5. Do not create multiple accounts to bypass quotas.
6. Do not count introductory credits as monthly unless the provider explicitly says they recur.

## Revised routing

| Workload | First free lane | Second lane | Premium reserve |
|---|---|---|---|
| Routine implementation | Kiro Student | Replit / OpenRouter / Groq | Astra / Codex |
| Fast LLM calls | Groq Free | Cloudflare Workers AI | Bedrock / Azure |
| Web model routing | Vercel AI Gateway | OpenRouter | direct paid provider |
| Cloud Python jobs | Modal | Camber | AWS / Azure |
| GPU notebooks | Kaggle | Colab / Lightning | paid GPU |
| AWS tests | LocalStack Student | existing AWS free/credits | Bedrock/Mantle spend |
| AI mocap | Rokoko Starter | Autodesk Flow Education | paid mocap |
| Terrain | Gaea Student | Houdini Apprentice | paid Houdini |
| 3D ideation | Meshy Free | Blender procedural tools | paid generation |
| Blender offline rendering | V-Ray Community | Cycles | paid renderer |
| Website backend | Appwrite Education | current static stack | paid cloud |

## Human-action shortlist

1. Claim **Gaea Student**.
2. After GitHub Education approval, redeem **Appwrite + LocalStack + Sentry + BrowserStack + Deepnote + Doppler** in addition to Camber.
3. Create Modal Starter and confirm the $30/month free credit.
4. Create Vercel AI Gateway key and confirm the free-user $5/30-day credit.
5. Create Groq free API key and inspect live limits.
6. Enable Cloudflare Workers AI on Free and keep spend at $0.
7. Verify Kaggle and Colab GPU access.
8. Activate Rokoko Starter and test one sub-30-second Vision capture.
9. Claim Meshy free monthly credits; optional legitimate Discord bonus.
10. Sign into Humber Copilot Enterprise and browse **myApps** for additional licensed DCC/VFX tools.

## Watchlist

Kiro student expansions; GitHub Student Pack additions; Canadian Google AI student eligibility; Azure/AWS/GCP academic GPU grants; NVIDIA individual academic compute; Foundry/Humber partner status; render-farm student grants; AI-mocap education grants; new free routes on Vercel/OpenRouter; Cerebras on AWS Bedrock (relevant to Mantle when available, but not itself counted as free).


---

## Trench III — model APIs, animation, and hidden compute

### GitHub Pro compute unlocked by Student Pack

GitHub Student verification includes GitHub Pro. Current GitHub plan allowances give Pro accounts:

- **180 Codespaces core-hours/month**
- **20 GB Codespaces storage/month**
- **3,000 GitHub Actions minutes/month**
- 1 GB Actions storage

Official plan allowance reference: https://docs.github.com/en/billing/reference/product-usage-included

This is easy to overlook because it is not branded as an AI credit. Treat Codespaces as another remote coding/test machine for repository-shaped work. Core-hours are compute-weighted, so a larger machine consumes the allowance faster.

### NVIDIA NIM developer endpoints

NVIDIA's current NIM developer page explicitly offers **free access to NVIDIA-hosted NIM API endpoints for prototyping** through free NVIDIA Developer Program membership. Access is rate-limited/model-dependent; do not assume an unlimited production quota or a fixed credit count unless the account dashboard shows it.

Official: https://developer.nvidia.com/nim

**Melodia role:** another strong inference/agent/model-evaluation lane, especially useful given the existing NVIDIA/Omniverse/UE interests.

### Cohere free trial API

Every Cohere account gets a free rate-limited Trial API key. Current docs state:

- trial usage is free and intended for evaluation/prototyping, not production
- Chat models generally allow **20 requests/minute**
- trial keys are limited to **1,000 API calls/month**
- **North Mini Code** is an agentic coding model with a **256K context window**, tool use and structured outputs, and is free until trial limits are reached
- Command A+, Command A Reasoning, vision, embed and rerank are also available under trial limits

Official:
- https://docs.cohere.com/v2/docs/rate-limits
- https://docs.cohere.com/docs/north-mini-code-1.0
- https://cohere.com/pricing

**Routing:** use North Mini Code as another disposable repo/coding-agent candidate before paying for routine work.

### Mistral Studio free mode

Mistral Studio enables **Free mode by default** with usage and rate limits, including its model playground.

Official: https://docs.mistral.ai/getting-started/quickstarts/studio/test-model-playground

Use for model comparison, lightweight inference and experiments. Record the live dashboard limits rather than hard-coding a quota that may change.

### Cerebras Inference free tier

Cerebras continues to expose a **$0 Free tier** with lower rate limits and a free API key. Current 2026 model docs still refer to free-tier limits for models such as GPT-OSS 120B. Exact limits have been adjusted under demand, so trust the live console rather than old “X tokens/day” claims.

Official:
- https://inference-docs.cerebras.ai/models/overview
- https://inference-docs.cerebras.ai/support/pricing

**Melodia role:** ultra-fast open-model evaluation and agent experiments; also watch the previously recorded Cerebras/AWS Bedrock integration path.

### DeepMotion Animate 3D Freemium

Current Animate 3D pricing provides a **free, no-card Freemium plan** with:

- **25 animation credits/month**
- clips up to 20 seconds
- FBX, BVH, GLB, MP4, JPG, PNG and GIF outputs
- up to 2-person tracking and up to 3 custom characters on the current table
- recurring monthly reset
- free-credit earning through animation labeling/correction

Free-plan use is personal/non-commercial; premium is required for commercial licensing.

Official: https://www.deepmotion.com/pricing-animate3d

**Melodia role:** add beside Rokoko Starter and Autodesk Flow as another AI mocap solver. Good for A/B testing difficult captures rather than relying on one solver.

### ElevenLabs free sound-design allowance

The current ElevenLabs Sound Effects free plan includes **10,000 credits/month** and up to 50 sound-effect generations on the displayed plan, with max 30-second clips. Free output is **personal-use only**; commercial use requires a paid tier.

Official: https://elevenlabs.io/sound-effects

**Melodia role:** placeholder/prototype sound design, UI sounds and mood experiments only. Do not ship free-plan audio commercially.

### Reallusion AccuRIG

ActorCore AccuRIG is a **free automatic character-rigging application** with direct export workflows to major 3D tools including Unreal Engine, Blender, Maya, MotionBuilder and 3ds Max.

Official Reallusion references:
- https://magazine.reallusion.com/2022/09/01/reallusion-releases-accurig-the-next-generation-automatic-character-rigging/
- https://forum.reallusion.com/522071/Just-Released-AccuRIG-AutoRigging-Tool-%E2%80%93-FREE-DOWNLOAD

**Melodia role:** emergency/secondary rigging lane for characters, creatures and generated blockouts.

### Vercel current true-free model routes

In addition to the recurring free-user AI Gateway credit already recorded, Vercel currently exposes some zero-price provider routes, for example **MiniMax M2.7 (Free)**. Availability can change, so prefer querying the model catalog at execution time instead of pinning the production stack to a promotional free route.

Official example: https://vercel.com/ai-gateway/models/minimax-m2.7-free

### Oracle Cloud — optional persistent free server lane

OCI currently offers:

- a **US$300 / 30-day** trial in eligible regions
- Always Free compute after the trial
- current Always Free Ampere allowance equivalent to **2 OCPUs / 12 GB RAM total**
- **200 GB** Always Free block-volume storage
- Always Free databases and other infrastructure

Oracle usually requires a real credit/debit card for account verification; do not start this tonight if avoiding card-backed clouds.

Official:
- https://www.oracle.com/cloud/free/
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

**Melodia role:** persistent low-cost Linux service/tooling host. Lower priority than Modal/Camber because those are cleaner no-cost wins.

### Fab Limited-Time Free

Fab currently exposes a **Limited-Time Free** content channel alongside sales. Inventory rotates, so do not document individual assets as permanently free without checking their current listing/license.

Official: https://www.fab.com/

**Action:** periodically check Limited-Time Free for UE-ready environment, material, animation and tooling assets that genuinely serve the project.

## Trench III routing additions

| Need | Free lane to test |
|---|---|
| Additional coding agent | Cohere North Mini Code trial |
| Ultra-fast open-model inference | NVIDIA NIM / Cerebras / Groq |
| General model playground | Mistral Studio Free |
| Remote repo machine | GitHub Codespaces via Student Pro |
| CI/test minutes | GitHub Actions via Student Pro |
| Alternate AI mocap solve | DeepMotion Freemium |
| Prototype SFX | ElevenLabs Free — personal/non-commercial only |
| Auto-rigging | AccuRIG |
| Persistent tiny server | Oracle Always Free |
| UE asset scavenging | Fab Limited-Time Free |

## New human actions from Trench III

1. Join/confirm **NVIDIA Developer Program** and test a free NIM endpoint.
2. Create a Cohere Trial key and test **North Mini Code** on a small disposable repository task.
3. Enable Mistral Studio Free mode and record the real current limits.
4. Create a Cerebras free API key and record its live limits.
5. Activate **DeepMotion Freemium** and compare one short clip against Rokoko/Flow.
6. Activate ElevenLabs Free only for non-commercial sound prototyping.
7. Download AccuRIG if a rigging test would actually save time.
8. After GitHub Student approval, record the live **Codespaces and Actions** allowances shown on the account.
9. Check Fab Limited-Time Free on a cadence rather than hoarding irrelevant assets.
