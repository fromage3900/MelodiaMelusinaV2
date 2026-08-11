## Ultimate “napo loop” plan (UE 5.8) — Material Library

Designed so the project can keep improving while you’re away: each loop produces a small, reviewable artifact and never blocks on manual work.

### Loop cadence (every ~15 minutes)

1. **Audit status (fast)**  
   - Run `Content/Python/review_portfolio_masters.py` headless (always with `-DisablePlugins=Monolith`).  
   - Output: confirm `Saved/Audit/master_review.json` remains `clean: true`.

2. **Pick one micro‑task (single change-set)**  
   Choose exactly one of:
   - **New instance preset**: add one `MI_Universal_*` entry in `Content/Python/universal_instance_presets.py` using an existing texture profile and 3–8 parameters max.
   - **Starter instance polish**: adjust one `MI_Show_*` (scalars/vectors only) in `Content/Python/starter_instances.py` so it better demonstrates a capability (no new textures).
   - **Library wiring enhancement**: add a small, neutral/off parameter + wiring to the universal master in `Content/Python/setup_master_universal.py` (no topology churn outside its section).
   - **Docs alignment**: update one row/section in `Docs/MATERIAL_INTEGRATION.md` to match reality (param names, group names, purpose).

3. **Rebuild + validate (safe)**  
   - `setup_master_universal.py --force` headless (only if wiring changed).  
   - `apply_starter_instances.py` headless (only if starters changed).  
   - Re-run `review_portfolio_masters.py` headless.

4. **Research checkpoint (UE 5.8)**  
   Capture one short note per tick (append-only) under `Docs/Research/UE58_MaterialNotes.md`:
   - Any engine behavior seen (pin name changes, Substrate quirks, function call input naming, compile warnings).
   - Any recurring errors (e.g. `String is too long`, `GameFeatureData` asset manager warning) and whether they are benign.

### Always-on guardrails

- **Headless runs**: always pass `-DisablePlugins=Monolith` to avoid the known crash.
- **Neutral defaults**: every new parameter must default to no-op/off.
- **No texture churn**: avoid adding new texture assets in loops; focus on parameters + wiring + instances.
- **One intent per change**: each tick should be trivially revertible if a direction is wrong.

### Suggested expansion tracks (pick one per day)

1. **Infinity Nikki environment stack**  
   - Iterate on rim/glow/sparkle/grading controls and add 1–2 showcase instances that demonstrate it clearly.

2. **SDF master integration**  
   - Identify the top 5 SDF masters used most in environments and ensure consistent parameter naming and presets.

3. **Trimsheet library**  
   - Add a small set of trimsheet instances that demonstrate Layer A/B blending + parallax + macro breakup, with clean naming.

4. **VFX + material cohesion**  
   - Align VFX sprite materials with the universal master color language (Nikki, Magical, FairyDust).

### Loop paused (2026-06-20)

Napo loop **paused** for specialist pivot (water, landscape). Resume when user asks.

