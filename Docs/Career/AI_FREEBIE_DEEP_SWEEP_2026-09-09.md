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


---

## Trench IV — coding agents, UV/clothing, photogrammetry, audio middleware, and render credits

Verified 2026-09-10 from current official provider pages. This pass focuses on offers that are easy to miss because they are either general free tiers rather than "student" plans, or specialist game/3D tools.

### P0: new agent / API capacity

#### Mistral Free — $10/month API credits + Vibe

Mistral's current **Free ($0)** plan includes:
- limited Vibe agentic coding sessions
- Mistral Studio access
- **$10/month in API credits**
- limited chat/search/image generation
- 100+ connectors

Official: https://mistral.ai/pricing/

**Routing:** this is now a real recurring free inference budget. Test Vibe for low-risk coding tasks and use the $10 monthly API pool for Hermes/Mantle experiments before spending premium provider credits.

#### Google Antigravity Individual — $0 agent platform

Current Individual plan is **$0/month** and lists:
- Gemini 3.8 Flash
- Gemini 3.7 Flash
- Gemini 3.6 Flash
- Gemini 3.1 Pro
- Claude Sonnet 4.6 and Opus 4.6
- gpt-oss-120b
- **Unlimited Tab completions**
- **Unlimited Command requests**
- basic weekly agent rate limits

Antigravity includes a multi-agent desktop app, CLI, SDK, IDE, Agent Manager, background subagents, browser integration, and project/workspace orchestration.

Official:
- https://antigravity.google/pricing
- https://antigravity.google/

**Correction:** the old consumer Gemini CLI / Gemini Code Assist free route is no longer the lane to plan around. Google announced that consumer requests moved to Antigravity on 2026-06-18. Use Antigravity for the current Google free coding-agent lane.

Official transition: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

#### Qwen Code OAuth — dead free tier, do not plan around it

Qwen Code's former OAuth free tier was discontinued **2026-04-15**. Current Qwen Code should use supported providers such as Alibaba ModelStudio, OpenRouter, or another configured provider.

Official project docs: https://github.com/QwenLM/qwen-code/blob/main/docs/users/configuration/auth.md

This is a cleanup note so agents stop rediscovering obsolete "1,000 free Qwen requests/day" advice.

### AWS: two separate free lanes

#### AWS Educate
AWS Educate remains completely free, requires only an email, and **does not require a credit card**. It provides hands-on cloud labs for services such as EC2, S3, VPC, RDS, operations, and related cloud skills.

Official: https://aws.amazon.com/education/awseducate/

**Action:** enroll even though Bedrock/Mantle already exists. Treat Educate as free sandbox/training capacity rather than production Bedrock funding.

#### New-customer AWS Free Tier — up to $200, but do not multi-account
AWS's current Free Tier gives **new customers**:
- $100 credits at sign-up
- up to another $100 by exploring foundational services
- up to 6 months on the Free plan
- 30+ Always Free services

Official:
- https://aws.amazon.com/free/
- https://aws.amazon.com/free/free-tier-faqs/

**Existing-account caveat:** this is for new AWS customers. Because Melodia already has an AWS/Bedrock/Mantle setup, first inspect whether the existing account was created under this program. **Do not open duplicate accounts to harvest signup credits.**

### NVIDIA — free training + credit pathways

Free NVIDIA Developer Program membership currently includes access to NIM and Omniverse resources for development/testing, DLI resources, early-access programs, and academic-grant pathways.

It also advertises a Google Cloud + NVIDIA learning path where achievements can unlock **Google Cloud and NVIDIA credits**; exact credit amounts are pathway/account dependent and must be verified in the live dashboard.

Official: https://developer.nvidia.com/developer-program

Separately, joining the Developer Program currently lets members select **one complimentary self-paced NVIDIA DLI course worth up to $90**. Options include accelerated computing/CUDA, generative AI/diffusion, transformer NLP, synthetic data, and related topics.

Official: https://developer.nvidia.com/join-nvidia-developer-program

**Faculty multiplier:** approved NVIDIA DLI Teaching Kit educators can receive free course codes for students; each course includes browser-based access to a GPU-accelerated cloud workstation. This is a legitimate faculty outreach target rather than an individual student self-claim.

Official: https://developer.nvidia.com/teaching-kits

### Anthropic student-builder lane — apply/watch, not guaranteed

Anthropic's education program explicitly says student builders can apply for **funding in the form of API credits**, alongside Campus Ambassador / Builder Club programs.

Official:
- https://www.anthropic.com/news/introducing-claude-for-education
- https://www.anthropic.com/news/advancing-claude-for-education

Treat this as **APPLY / WATCH** because the amount and current cohort availability are not guaranteed on the public program page. A truthful Melodia capstone / UE production-tooling proposal is a valid thing to ask about; do not imply Humber is already an Anthropic partner.

Canada-specific future lane: Anthropic announced that startups affiliated with Vector, Mila, and Amii will receive **at least US$5,000 each in API credits** through Anthropic for Startups. This is only relevant if a future legitimate company becomes affiliated with one of those institutions; do not fabricate startup or affiliation status.

Official: https://www.anthropic.com/news/canadian-ai-research

---

## P0: specialist 3D / environment-art student wins

### RizomUV — FREE for students

RizomUV currently offers its student license **free for students**. The student license is for learning/non-commercial use, but its terms explicitly allow work created for a portfolio, during studies, and for contests.

Official:
- https://www.rizomuv.com/virtual-spaces/plans-prices/
- https://www.rizomuv.com/general-terms/

**Action:** claim while Humber verification is current. This is a direct professional UV-production tool and one of the strongest student-specific DCC finds in the sweep.

### Marvelous Designer — first 3 months FREE until 2026-10-31

Marvelous Designer's revised 2026 Student Plan currently gives **new student subscribers their first 3 months free** if started by **October 31, 2026**. After the free period, the current student price is $8.25/month. Student eligibility can remain available for up to four years from initial verification, subject to the current policy.

Official:
- https://www.marvelousdesigner.com/support/news/view/0c224dc5ea144c0a893ff4a81ce6a37e
- https://support.marvelousdesigner.com/hc/en-us/articles/59985521768345-Marvelous-Designer-Student-License-Reorganization-4-Year-Usage-and-3-Month-Free-Benefit-Guide-updated-July-2026

**Deadline:** **2026-10-31.**
**Action:** claim the 3-month free period if clothing simulation / garment authoring is useful this semester, then cancel before paid billing unless the $8.25/month student plan is worth keeping.

### Plask Motion — 15 seconds of AI mocap every day

Plask Freemium is $0 and currently includes:
- **15 seconds/day** AI motion capture
- full-body + hand capture
- multi-person mocap
- FBX / GLB / BVH export
- 1 GB storage
- video rendering and collaboration

Official: https://plask.ai/en-US/pricing

**Routing:** add as a fourth mocap solver beside Rokoko, DeepMotion and Autodesk Flow. Daily quota is ideal for tiny validation clips.

### Tripo Free — 300 3D generation credits/month

Tripo's current Free Studio tier provides **300 credits/month** and exports formats including USD, FBX, OBJ, STL, GLB and 3MF. Current Tripo pages state that Free-tier generated models **do not include commercial rights**.

Official: https://www.tripo3d.ai/

**Routing:** prototype/blockout/reference only unless licensing is upgraded. Never silently ship a free-tier generated asset in a commercial release.

### ZBrush for iPad — robust free edition

Current free ZBrush for iPad includes 28 brushes plus limited ZRemesher, DynaMesh, ZSpheres, Sculptris Pro, introductory hard-surface sculpting, PolyPaint and BPR rendering.

Official: https://www.maxon.net/en/zbrush-for-ipad

Useful as a portable sculpt/sketch lane; it is not a replacement for the full desktop student/Maxon entitlement.

---

## Photogrammetry / scanning

### RealityScan (formerly RealityCapture) — full tool FREE

Epic's current RealityScan licensing says the desktop tool is **free to use for students**, educators, and individuals/small businesses under **US$1M revenue**, with **all RealityScan features**.

Official:
- https://www.realityscan.com/license?lang=en-US
- https://www.realityscan.com/download

RealityScan Mobile is also a free mobile scanning application.

**Melodia role:** this should become the default high-quality photogrammetry lane for real-world environment capture, material/reference acquisition, and scan-to-UE experiments.

### Agisoft Cloud — 50 GB + 20 processing hours/month, conditional

Agisoft Cloud's Free Plan currently includes:
- **50 GB storage**
- **20 cloud processing hours renewing monthly**

However, cloud processing requires an activated **Metashape Professional** license; Educational and Trial licenses qualify.

Official: https://www.agisoft.com/features/cloud/

**Action:** inspect Humber myApps/labs for Metashape Professional before paying. If Humber already supplies a valid Pro license, this becomes a recurring 20-hour/month photogrammetry compute grant.

---

## Professional game-audio middleware — free legitimate indie paths

### FMOD Indie

FMOD currently provides a free Indie license when:
- game development budget is **under US$600K**
- developer gross revenue/funding is **under US$200K/year**
- project is registered with FMOD
- required attribution/logo terms are followed

Official:
- https://www.fmod.com/licensing
- https://www.fmod.com/legal

**Melodia role:** serious alternative/companion to Unreal audio for adaptive music, rhythm systems, profiling and interactive audio.

### Wwise Indie

Audiokinetic currently lists **Wwise Indie as free** for game productions with a production budget **under US$250K**, with full platform access, unlimited sounds and all engine features; premium plug-ins are optional. Wwise also supports free non-commercial and academic project licensing.

Official: https://www.audiokinetic.com/en/products/licensing/

**Melodia role:** extremely relevant to a rhythm-JRPG. Even if the shipping stack stays native Unreal, learning/benchmarking Wwise is professionally valuable.

### Houdini Engine for Unreal — FREE

SideFX currently provides free commercial Houdini Engine licenses for the UE5 and Unity plug-ins. Indie users also have free Houdini Engine Indie licenses. **Important:** Houdini Apprentice-created assets cannot be used with the Engine plug-ins.

Official:
- https://www.sidefx.com/products/houdini-engine/
- https://www.sidefx.com/faq/houdini-engine-faq/

**Action:** if procedural HDAs become part of the UE pipeline, distinguish the authoring license (Apprentice/Education/Indie) from the free Engine runtime/plugin license.

---

## Render-farm trench

### SheepIt — free forever Blender distributed farm
SheepIt is currently free forever, no subscription and no credit card, supporting Blender Cycles, Eevee and Workbench.

Official: https://www.sheepit-renderfarm.com/home

**Caution:** this is a community distributed render farm. Review its current privacy/scene-sharing terms before sending unreleased or sensitive assets.

### GarageFarm — $25 no-card starter credit
New GarageFarm accounts currently receive **$25 free render credit**, no credit card required. It supports Blender, Maya, 3ds Max, Cinema 4D and multiple render engines.

Official:
- https://garagefarm.net/
- https://garagefarm.net/pricing

### Fox Renderfarm — $25 new-user credit
Fox Renderfarm currently advertises a **$25 free trial/render coupon** for new users. Promotional challenge coupons can temporarily raise this, but do not count expired event codes as permanent entitlements.

Official: https://www.foxrenderfarm.com/

### RebusFarm student — 50% off
Not free, but current students can receive **50% off purchases for educational projects** after submitting current enrollment proof.

Official: https://rebusfarm.net/buy

Use only after exhausting SheepIt, local rendering, GarageFarm/Fox trial credits, and other free compute.

---

## Revised P0 claim additions

1. **RizomUV Student — free.**
2. **Marvelous Designer Student — claim 3 free months before 2026-10-31.**
3. **Mistral Free — activate $10/month API credit + Vibe.**
4. **Google Antigravity Individual — use $0 agent plan as a major coding lane.**
5. **NVIDIA Developer Program — claim one free DLI course and inspect credit-earning paths.**
6. **RealityScan desktop + mobile — activate full free photogrammetry workflow.**
7. **Plask Free — add 15 sec/day AI mocap lane.**
8. **AWS Educate — free labs, no card.**
9. **GarageFarm + Fox — bank legitimate one-time $25 starter credits for future render emergencies.**
10. **FMOD + Wwise — register/learn only when the project needs an audio-middleware experiment.**
11. **Agisoft Cloud — unlock only if a valid Metashape Pro license is already available through Humber/trial.**
12. **Anthropic student-builder API credits — apply/watch with truthful project framing; no guaranteed amount.**

## Agent-stack correction after Trench IV

The current free coding hierarchy should now include:

- **Kiro Student** — high-volume primary worker
- **Google Antigravity Individual** — $0 multi-model agent/CLI/IDE lane
- **Mistral Vibe + $10/month API** — recurring free coding/inference reserve
- **Groq / NVIDIA NIM / Cerebras / Cohere / OpenRouter / Cloudflare / Vercel** — API/model swarm
- **Copilot Student / Codespaces** — GitHub-native worker and remote machine
- **Astra/Codex** — reserve for hard reasoning and final passes

Do not spend premium Astra/Codex capacity on a task that one of these verified free lanes can safely complete.
