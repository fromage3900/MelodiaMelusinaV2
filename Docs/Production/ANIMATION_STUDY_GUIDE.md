# Animation Study Guide
> **For:** BS_GodFile character animation pipeline (Melusina, Rokoko mocap, FACS face)
> **Companion to:** `CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`
> **Audience:** Animators preparing for 2 semesters of character animation study

---

## Table of Contents

1. [The 12 Principles of Animation](#1-the-12-principles-of-animation)
2. [Body Mechanics Curriculum (Weeks 1-4)](#2-body-mechanics-curriculum-weeks-1-4)
3. [Acting for Animation Curriculum (Weeks 5-8)](#3-acting-for-animation-curriculum-weeks-5-8)
4. [Recommended Resources](#4-recommended-resources)
5. [Weekly Practice Exercises](#5-weekly-practice-exercises)
6. [How to Use Reference](#6-how-to-use-reference)
7. [Mocap Cleanup Workflow](#7-mocap-cleanup-workflow)
8. [Appendices](#8-appendices)

---

## 1. The 12 Principles of Animation

Disney animators Frank Thomas and Ollie Johnston codified these in *The Illusion of Life* (1981). They remain the foundation of all character animation — 2D, 3D, hand-keyed, and mocap.

---

### 1.1 Squash and Stretch

**What it is:** Deforming a volume to show weight, flexibility, and impact. The total volume stays constant — squash when compressed, stretch when elongated.

**Why it matters:** Without it, movement feels stiff and weightless. A ball that doesn't squash on impact feels like it's made of stone (unless that's the intent).

**Examples:**
- A bouncing ball squashes flat on the ground, stretches at the top of the arc
- A character's face squashes when cheeks are pushed, stretches when jaw drops for a scream
- Melusina's dress or hair stretching during a fast spin, squashing when she lands

**How to practice:**
1. Animate a bouncing ball with proper squash/stretch (start with 12 frames down, 8 frames up)
2. Add a tail or appendage that continues moving after the main body stops (overlapping action preview)
3. In Blender, animate a simple cube "jumping" — squash on land, stretch on the way up
4. Apply to Melusina: animate her hair squashing when she lands from a jump

**Common mistakes:**
- Losing volume (the ball gets smaller when squashed, larger when stretched)
- Overdoing it (looks like jelly, not flesh)
- Applying to rigid objects (a metal sword should NOT squash)

---

### 1.2 Anticipation

**What it is:** A small movement in the opposite direction of the main action that telegraphs what's about to happen. Prepares the audience's eye and builds energy.

**Why it matters:** Without anticipation, actions feel sudden and unreadable. The audience can't follow fast movement unless they're prepped for it.

**Examples:**
- A character bends their knees before jumping (down before up)
- A fist pulls back before punching (back before forward)
- Eyes look at a door before opening it (look before act)
- A breath intake before speaking (inhale before sound)

**How to practice:**
1. Animate a character throwing a ball — key the wind-up before the throw
2. Animate Melusina looking at something off-screen, then running toward it
3. Find 5 examples of anticipation in film and note the frame count (usually 6-12 frames)
4. Record yourself performing an action; watch the tiny prep movements you do unconsciously

**Common mistakes:**
- Too long (becomes the main action instead of a setup)
- Too short (invisible — why bother?)
- Missing entirely (action feels robotic)

---

### 1.3 Staging

**What it is:** Presenting an idea so it's unmistakably clear. Includes camera angle, character position, lighting contrast, and background elements.

**Why it matters:** If the audience can't read what's happening, no amount of polish saves the shot. Good staging makes complex actions instantly understandable.

**Examples:**
- A single character centered in frame with clear silhouette for an emotional moment
- Camera placed to show the reaction, not just the action (show the face, not the fist)
- A dark silhouette against a bright background for a dramatic entrance
- Melusina's face framed with macro camera (90mm) for a lip-sync shot

**How to practice:**
1. Stage a "character finds a key" shot — try 3 angles, pick the clearest
2. Use the "silhouette test": if you fill the character with black, can you still read the pose?
3. Animate the same action from a bad angle, then a good angle — compare readability
4. Block a 5-second shot with 3 different camera positions and test which communicates best

**Common mistakes:**
- Camera too far away (can't read facial expression)
- Camera too close (can't read body language)
- Background clutter competing with the subject
- Character facing away from camera during a key emotional beat

---

### 1.4 Straight Ahead Action and Pose to Pose

**What it is:** Two approaches to blocking animation.
- **Straight ahead:** Animate frame 1, then 2, then 3... flowing forward. Organic, spontaneous.
- **Pose to pose:** Set the key poses first, then fill in the breakdowns. Controlled, structured.

**Why it matters:** Most professional work uses pose-to-pose for planning, with straight-ahead flourishes for detail passes. Knowing both lets you choose the right tool.

**Examples:**
- Pose-to-pose: Block the key storytelling poses of Melusina's performance first, then spline
- Straight-ahead: Animate hair, cloth, or secondary motion flowing naturally without pre-planning
- Hybrid: Pose-to-pose the body, straight-ahead the hair/cloth

**How to practice:**
1. Animate a simple jump straight-ahead (don't plan — just go)
2. Animate the same jump pose-to-pose (plan 6 key poses first)
3. Compare: which is more controlled? Which has better energy?
4. Use pose-to-pose for your polished pieces; use straight-ahead for hair/cloth passes

---

### 1.5 Follow Through and Overlapping Action

**What it is:** Different parts of a body move at different rates. When the main body stops, secondary elements (hair, clothes, tail, ears) continue moving.

**Why it matters:** Everything moving at the same rate looks mechanical. Overlapping action creates organic, believable motion.

**Examples:**
- Melusina's hair continues moving after she stops turning her head
- A coat settles after the character stops walking
- Ears lag behind a head turn, then catch up
- A character's arm continues swinging after they stop walking

**How to practice:**
1. Animate a character stopping a run — body stops first, then arms, then hair
2. Add a long skirt or cape to a walk cycle and animate it lagging behind
3. Animate Melusina's ears (if rigged) with a 4-6 frame delay on head turns
4. Study how different materials overlap: hair (fast, bouncy) vs. cloth (slow, heavy)

---

### 1.6 Slow In and Slow Out (Ease In / Ease Out)

**What it is:** Movement accelerates and decelerates. More frames clustered at the start/end of an action, fewer in the middle (fast part).

**Why it matters:** Real objects don't move at constant speed. Ease gives weight and believability.

**Examples:**
- A pendulum: slow at the top, fast at the bottom
- A character standing up: slow start, fast middle, slow settle
- A head turn: eases out of the start, eases into the stop
- Melusina's arm reaching for something: accelerates, then decelerates to a precise stop

**How to practice:**
1. Animate a simple arm raise with linear spacing, then with ease — compare
2. Graph editor exercise: take a linear animation and add ease curves manually
3. Animate a character picking up a cup — note the slow approach, fast grab, slow lift
4. Study the spacing on a bouncing ball: clustered at the top (slow), spread at the bottom (fast)

---

### 1.7 Arc (Arc of Motion)

**What it is:** Most natural movement follows a curved path, not a straight line. Arms, heads, and bodies move in arcs.

**Why it matters:** Linear motion looks robotic. Arcs give fluidity and life.

**Examples:**
- A hand reaching for a cup arcs up and over, not straight line
- A head turn arcs slightly up or down, not perfectly horizontal
- Melusina's walk cycle: arms swing in arcs, hips trace a figure-8
- A thrown ball follows a parabolic arc

**How to practice:**
1. Animate a character pointing at something — make the finger arc, not go straight
2. In the graph editor, check that rotation curves are smooth, not angular
3. Film yourself reaching for an object — trace the arc your hand makes
4. Animate a simple head turn with and without an arc — compare

**Common mistakes:**
- Straight-line interpolation (default in most software — you must override)
- Broken arcs (the curve changes direction abruptly)
- Forgetting arcs on small movements (fingers, eyes)

---

### 1.8 Secondary Action

**What it is:** Supporting actions that reinforce the main action without distracting from it. Adds dimension and reality.

**Why it matters:** Real people don't do one thing at a time. Secondary actions make characters feel alive.

**Examples:**
- A character walking (main) while whistling (secondary)
- Melusina talking (main) while fidgeting with her hands (secondary)
- A character waiting (main) while tapping their foot (secondary)
- A sad character wiping a tear while trying to smile

**How to practice:**
1. Animate a character waiting in line — add a secondary action (checking phone, tapping foot)
2. Animate Melusina delivering dialogue while her hands gesture to emphasize points
3. Add a blink or breath to a static pose — does it feel more alive?
4. Animate a character eating (main) while having a conversation (secondary)

**Common mistakes:**
- Secondary action overpowers the main action (distracting)
- No secondary action at all (feels sterile)
- Secondary action contradicts the emotion (happy character with angry gestures)

---

### 1.9 Timing

**What it is:** How many frames an action takes. Timing communicates weight, mood, and personality.

**Why it matters:** The same pose with different timing reads completely differently. Fast timing = light/energetic; slow timing = heavy/sad.

**Examples:**
- A heavy character moves slowly (more frames per action)
- A light character moves quickly (fewer frames per action)
- A sad walk: 16-20 frames per step; a happy walk: 10-12 frames per step
- Melusina's combat moves: fast (8-12 frames); her sad moments: slow (20-30 frames)

**How to practice:**
1. Animate the same action at 3 different timings — compare the feeling
2. Time real actions with a stopwatch: how long does it take to stand up? To blink?
3. Animate a character reacting to surprising news — try 4 frames (fast/shocked) vs. 20 frames (slow/dawning)
4. Study the timing in your favorite animated film — count frames for key actions

---

### 1.10 Exaggeration

**What it is:** Pushing poses, timing, and expressions beyond reality to make them read clearly. Not distortion — amplification.

**Why it matters:** Realistic reference is often subtle to the point of invisibility. Exaggeration makes animation readable and entertaining.

**Examples:**
- A character's eyes popping wide for surprise (wider than real life)
- A squash that's slightly more extreme than physics would allow
- Melusina's hair flowing more dramatically than real hair would
- A character's reaction shot held 20% longer than realistic

**How to practice:**
1. Animate a realistic take (double-take), then push it 30% further
2. Take a subtle facial expression and exaggerate it until it reads on screen
3. Animate a jump with realistic timing, then exaggerate the hang time
4. Study anime vs. realistic film — note what's exaggerated and what's not

**Common mistakes:**
- Exaggerating everything (no contrast — everything is "loud")
- Not exaggerating enough (looks like mocap with no cleanup)
- Exaggerating the wrong thing (the emotion, not the body mechanics)

---

### 1.11 Solid Drawing / Solid Posing

**What it is:** Creating poses that have clear weight, balance, and three-dimensionality. In 3D, this translates to strong silhouettes and clear line of action.

**Why it matters:** Weak poses make even well-timed animation feel flat. Strong poses communicate character and emotion instantly.

**Examples:**
- A pose with a clear line of action (C-curve or S-curve running through the body)
- Weight clearly on one leg, not evenly distributed (unless that's the point)
- Melusina's idle pose: slight contrapposto, weight on one hip
- A "ready" pose that shows tension in the muscles

**How to practice:**
1. Draw/pose 10 gesture drawings from life (30 seconds each)
2. Pose Melusina in 5 different emotions — check the silhouette test
3. Study classical sculpture — note the contrapposto and weight shifts
4. Animate a character shifting weight from one foot to the other

**Common mistakes:**
- Symmetrical poses (feels stiff and unnatural)
- No clear weight distribution (character looks like they're floating)
- Weak silhouette (can't read the pose in black)

---

### 1.12 Appeal

**What it is:** The character is interesting to watch. Not just "cute" — charismatic, clear, and engaging. Even villains have appeal.

**Why it matters:** If the audience doesn't care about the character, nothing else matters. Appeal is what makes someone want to keep watching.

**Examples:**
- Melusina's design: flowing hair, expressive eyes, elegant proportions
- A character with a distinctive walk (personality in locomotion)
- Clear, readable expressions (not muddy or ambiguous)
- A character who does unexpected things (surprises the audience)

**How to practice:**
1. Animate Melusina's idle pose — does it show personality?
2. Study characters you love — what makes them appealing? Can you replicate that quality?
3. Animate a character entering a room — make it memorable
4. Get feedback: do people want to watch this character for 30 seconds?

---

## 2. Body Mechanics Curriculum (Weeks 1-4)

Body mechanics is the foundation. Before you can act, you must make a body move believably. This curriculum builds from simple physics to complex physical actions.

---

### Week 1: Weight and Timing

**Goal:** Understand how weight affects movement and how timing communicates mass.

**Study topics:**
- Center of gravity and balance
- How weight transfers during movement
- Timing charts (how many frames for common actions)
- The relationship between mass and speed

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Bouncing ball | Animate a rubber ball and a bowling ball bouncing | 2 clips (each 3 sec) | Rubber ball: bouncy, stretchy. Bowling ball: heavy, minimal squash. |
| Weight shift | Melusina shifts weight from one foot to the other | 1 clip (4 sec) | Clear weight transfer, hips move first, shoulders follow |
| Pendulum swing | Animate a pendulum (or Melusina's hair strand) | 1 clip (3 sec) | Smooth arcs, slow at extremes, fast in middle |
| Push a box | Melusina pushes a heavy box across the floor | 1 clip (6 sec) | Box moves slowly, Melusina's body shows effort |

**Daily practice (30 min):**
- Day 1: Bouncing ball (rubber) — focus on squash/stretch
- Day 2: Bouncing ball (bowling ball) — focus on weight and minimal deformation
- Day 3: Weight shift — film yourself, study the hip movement
- Day 4: Pendulum — focus on arcs and ease
- Day 5: Push a box — combine weight, timing, and effort

**Reading:** *The Animator's Survival Kit* — Chapters on "Timing," "Weight"

---

### Week 2: Locomotion — Walks and Runs

**Goal:** Master the four basic gaits (walk, run, sneak, stride) and understand how mood affects locomotion.

**Study topics:**
- Walk cycle phases: contact, recoil, passing, high point
- Run cycle: adds a float phase (both feet off ground)
- How mood changes a walk (speed, arm swing, head position)
- Root motion and hip movement

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Neutral walk | Melusina walks at a normal pace | 1 clip (4 sec loop) | Clean loop, no foot slide, arms swing opposite legs |
| Happy walk | Bouncy, energetic walk | 1 clip (4 sec loop) | Higher steps, more arm swing, head bob |
| Sad walk | Slow, heavy, defeated walk | 1 clip (4 sec loop) | Shorter steps, arms still, head down |
| Run cycle | Melusina runs at full speed | 1 clip (2 sec loop) | Float phase visible, arms pump, body leans forward |

**Daily practice (30 min):**
- Day 1: Block neutral walk in stepped mode (contact poses only)
- Day 2: Add passing poses and breakdowns to neutral walk
- Day 3: Spline the walk, fix arcs and foot slide
- Day 4: Animate happy walk — focus on energy and bounce
- Day 5: Animate sad walk — focus on weight and slowness

**Reading:** *The Animator's Survival Kit* — "Walks," "Runs"

---

### Week 3: Jumps, Turns, and Physical Actions

**Goal:** Analyze and animate actions that involve full-body coordination and momentum.

**Study topics:**
- Jump phases: anticipation (crouch), takeoff, hang time, landing, recovery
- Turn mechanics: which way do the arms swing? Where do the eyes go?
- Physical actions: lifting, pulling, throwing, catching
- How the body chains movement (kinetic chain)

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Vertical jump | Melusina jumps straight up and lands | 1 clip (3 sec) | Clear crouch, hang time, squash on land |
| Jump with turn | Melusina jumps, turns 180° in air, lands | 1 clip (4 sec) | Turn happens at apex of jump, lands facing opposite direction |
| Lift a heavy object | Melusina lifts a box from ground to waist height | 1 clip (5 sec) | Shows effort: legs straighten, back stays straight, weight shifts |
| Throw a ball | Melusina throws a ball off-screen | 1 clip (3 sec) | Wind-up, follow-through, body rotation |

**Daily practice (30 min):**
- Day 1: Block vertical jump (crouch, up, down, land)
- Day 2: Add hang time and squash/stretch to jump
- Day 3: Block jump with turn — focus on the rotation at apex
- Day 4: Animate lift — study your own reference of lifting something heavy
- Day 5: Animate throw — focus on the follow-through

**Reading:** *The Animator's Survival Kit* — "Jumps," "Acting"

---

### Week 4: Mocap Cleanup Fundamentals

**Goal:** Learn to take raw mocap data and clean it into polished animation.

**Study topics:**
- Common mocap artifacts: foot slide, hand penetration, jitter, drift
- IK vs. FK for fixing foot plants
- Filtering high-frequency noise without losing performance
- When to keep mocap "imperfections" (they add life)

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Foot slide fix | Take a raw mocap walk, fix the foot plants | 1 clip (4 sec) | Feet stay planted when they should, no sliding |
| Jitter removal | Smooth a noisy mocap clip | 1 clip (5 sec) | No high-frequency jitter, performance preserved |
| Hand penetration fix | Fix a clip where hands pass through the body | 1 clip (4 sec) | Hands clear the body, natural arm arc |
| Full cleanup | Take a 10-second mocap clip and clean it end-to-end | 1 clip (10 sec) | No artifacts, performance intact |

**Daily practice (30 min):**
- Day 1: Import a raw Rokoko clip, identify all artifacts
- Day 2: Fix foot plants using IK pinning
- Day 3: Filter jitter from the spine and arms
- Day 4: Fix hand/shoulder penetrations
- Day 5: Polish pass — check arcs, timing, and overall quality

**Reading:** *The Animator's Survival Kit* — "Polishing"

---

## 3. Acting for Animation Curriculum (Weeks 5-8)

Acting is what separates animation from motion capture. A performance is about what the character is thinking and feeling, not just what they're doing.

---

### Week 5: Emotion and Expression

**Goal:** Understand the 7 universal emotions and how to portray them clearly through body and face.

**Study topics:**
- The 7 universal emotions: joy, sadness, anger, fear, surprise, disgust, contempt
- How emotions manifest in the body (not just the face)
- Emotional intensity levels (subtle → extreme)
- Emotional transitions (how one feeling becomes another)

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Emotion poses | Pose Melusina in 7 emotions (static) | 7 still poses | Each emotion readable from silhouette alone |
| Emotion walk | Melusina walks expressing 3 different emotions | 3 clips (3 sec each) | Same walk mechanics, different emotional read |
| Emotional transition | Melusina goes from happy to sad | 1 clip (5 sec) | Clear shift, not abrupt, body leads face |
| Subtle expression | Melusina shows "trying not to cry" | 1 clip (4 sec) | Audience reads the effort, not just the sadness |

**Daily practice (30 min):**
- Day 1: Study the 7 emotions — find reference images/video for each
- Day 2: Pose Melusina in each emotion — check silhouette readability
- Day 3: Animate an emotion walk — focus on body, not face
- Day 4: Animate an emotional transition — film yourself first
- Day 5: Animate a subtle expression — less is more

**Reading:** *Acting for Animators* by Ed Hooks — Chapters 1-4

---

### Week 6: Thought Process and Internal Monologue

**Goal:** Show what a character is thinking, not just what they're doing. The audience should be able to "read the mind."

**Study topics:**
- The 3 dimensions of acting: dialogue, subtext, and context
- How thought process shows in the eyes (eye darts, focus shifts, blinks)
- The "moment before" — what happens before the action
- Internal conflict (wanting two opposite things)

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Decision moment | Melusina is offered something she wants but shouldn't take | 1 clip (6 sec) | Audience sees the internal debate |
| Realization | Melusina suddenly understands something | 1 clip (4 sec) | Eyes change first, then body reacts |
| Lying | Melusina says something she doesn't believe | 1 clip (5 sec) | Micro-expressions betray the lie |
| Waiting | Melusina waits for news (good or bad?) | 1 clip (6 sec) | Body language shows anxiety/hope |

**Daily practice (30 min):**
- Day 1: Study eye movement — how eyes reveal thought
- Day 2: Animate a "decision moment" — focus on the pause before the choice
- Day 3: Animate a realization — eyes lead, body follows
- Day 4: Animate a lie — study micro-expressions in film
- Day 5: Animate waiting — show anxiety through small movements

**Reading:** *Acting for Animators* — Chapters 5-8

---

### Week 7: Lip-Sync and Dialogue

**Goal:** Make a character speak believably. Lip-sync is not just mouth shapes — it's the whole face and body.

**Study topics:**
- The 15 standard visemes (mouth shapes for speech)
- How consonants and vowels differ in timing
- Jaw movement and cheek involvement
- Body language during speech (gestures, posture shifts)
- The FACS-based face rig (Melusina's 68 morph targets)

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| Viseme set | Animate Melusina saying each of the 15 visemes | 1 clip (15 sec) | Each shape clear and distinct |
| Single sentence | Melusina speaks a 5-word sentence | 1 clip (4 sec) | Mouth syncs to audio, blinks happen naturally |
| Emotional speech | Melusina says the same line 3 different ways | 3 clips (3 sec each) | Same words, different emotional reads |
| Singing | Melusina sings a line from OpenUtau | 1 clip (6 sec) | Held notes, breath, emotion in face |

**Daily practice (30 min):**
- Day 1: Study the 15 visemes — film your own mouth
- Day 2: Animate a single sentence — focus on mouth shapes only
- Day 3: Add blinks and head movement to the sentence
- Day 4: Animate the same line with different emotions
- Day 5: Animate to a singing voice — focus on held notes and breath

**Reading:** *Facial Animation: A Practical Guide* (3DTotal) — Lip-sync chapters

---

### Week 8: Full Performance (Body + Face Combined)

**Goal:** Combine everything — body mechanics, emotion, thought process, lip-sync — into a complete character performance.

**Study topics:**
- Blocking a performance: body first, then face, then polish
- The importance of the "hold" (when not moving is the most powerful choice)
- Breathing and small movements that keep a character alive
- Editing and camera choices that support the performance

**Key exercises:**

| Exercise | Description | Deliverable | Success Criteria |
|----------|-------------|-------------|------------------|
| 15-second monologue | Melusina delivers a short speech with clear intention | 1 clip (15 sec) | Body and face work together, clear emotion |
| Reaction shot | Melusina reacts to something off-screen | 1 clip (6 sec) | Audience believes what she's reacting to |
| Silent performance | Melusina tells a story without words | 1 clip (10 sec) | Clear narrative through body language alone |
| Full scene | Melusina in a complete scene with dialogue and action | 1 clip (30 sec) | Polished, camera-ready performance |

**Daily practice (30 min):**
- Day 1: Block the body for a 15-second monologue
- Day 2: Add face (eyes, brows, mouth) to the monologue
- Day 3: Polish timing — add holds, breathing, small movements
- Day 4: Animate a reaction shot — study film references
- Day 5: Review and refine — get feedback from someone else

**Reading:** *The Animator's Survival Kit* — "Acting," "Polishing"

---

## 4. Recommended Resources

---

### 4.1 Books (Essential)

| Book | Author | Why Read It | Priority |
|------|--------|-------------|----------|
| **The Animator's Survival Kit** | Richard Williams | THE bible. Every principle, every exercise, every "how many frames." Read it 3 times. | ESSENTIAL |
| **Timing for Animation** | Harold Whitaker | The definitive guide to how many frames each action takes. Charts and tables. | ESSENTIAL |
| **Acting for Animators** | Ed Hooks | Performance = acting, not moving. The best book on the psychology of animated performance. | ESSENTIAL |
| **Drawn to Life** (Vol 1 & 2) | Walt Stanchfield | Disney's gesture and force. Short, punchy lectures on making drawings come alive. | HIGH |
| **Facial Animation: A Practical Guide** | 3DTotal | FACS, blendshapes, lip-sync. Practical workflows for facial rigs. | HIGH |
| **The Illusion of Life** | Frank Thomas & Ollie Johnston | The original source of the 12 principles. More philosophical than practical. | MEDIUM |
| **Character Animation Crash Course!** | Eric Goldberg | Fun, accessible, great for beginners. Focuses on 2D but principles apply to 3D. | MEDIUM |
| **Stop Staring: Facial Modeling and Animation Done Right** | Jason Osder | Deep dive into facial anatomy and FACS. Great for FACS rig users. | MEDIUM |
| **Animation from Pencils to Pixels** | Tony White | Comprehensive overview of the entire animation pipeline. | LOW |
| **The Art of Pixar / The Art of DreamWorks** | Various | Visual inspiration. Study the character design and posing. | LOW |

---

### 4.2 YouTube Channels

| Channel | Content | Why Watch | Link |
|---------|---------|-----------|------|
| **Sir Wade Neistadter** | Animation principles, Blender workflows | Clear explanations of the 12 principles with practical demos | youtube.com/@SirWadeNeistadter |
| **Howard Wimshurst** | 2D/3D animation theory, career advice | Deep dives into animation theory and industry practice | youtube.com/@HowardWimshurst |
| **The Animator's Survival Kit (app)** | Richard Williams' demos | The master himself demonstrating principles | youtube.com/@AnimatorsSurvivalKit |
| **AnimState** | Game animation breakdowns, community | Game-focused animation, mocap cleanup, state machines | youtube.com/@AnimState |
| **Taylor Hokanson** | Facial animation, FACS, blendshapes | The best resource for facial animation theory | youtube.com/@TaylorHokanson |
| **Toniko Pantoja** | 2D animation, character performance | Great for acting and emotion in animation | youtube.com/@TonikoPantoja |
| **The Animation Collaborative** | Lectures from industry pros | Full-length lectures from Disney/Pixar animators | youtube.com/@TheAnimationCollaborative |
| **Blender Animation** | Blender-specific animation tutorials | Practical Blender workflows | youtube.com/@BlenderAnimation |
| **Rokoko** | Mocap tutorials, cleanup workflows | Directly relevant to your pipeline | youtube.com/@Rokoko |
| **Flipped Normals** | Animation and rigging tutorials | Great for technical animation topics | youtube.com/@FlippedNormals |

---

### 4.3 Websites and Online Resources

| Site | Content | Why Use It | Link |
|------|---------|------------|------|
| **Animation World Network (AWN)** | Industry news, articles, tutorials | Stay current with the industry | awn.com |
| **11 Second Club** | Monthly animation competition | Practice with deadlines, get feedback | 11secondclub.com |
| **Animation Mentor Blog** | Tips from professional animators | Free advice from working pros | animationmentor.com/blog |
| **iAnimate Blog** | Game animation insights | Game-focused animation advice | ianimate.net/blog |
| **AnimSchool Blog** | Rigging and animation tutorials | Technical deep-dives | animschool.com/blog |
| **Rokoko Motion Library** | Free mocap clips | Practice cleanup on real data | rokoko.com/motion-library |
| **Mixamo** | Pre-made animations | Study timing, use as reference | mixamo.com |
| **Pinterest** | Pose reference, facial expressions | Build visual reference boards | pinterest.com |
| **ArtStation** | Professional portfolios | Study what "good" looks like | artstation.com |
| **CGSociety** | Community, tutorials, forums | Connect with other artists | cgsociety.org |

---

### 4.4 Online Courses

| Course | Platform | Focus | Cost | Link |
|--------|----------|-------|------|------|
| **Animation Bootcamp** | Animation Mentor | Body mechanics, acting | $$$$ | animationmentor.com |
| **Game Animation Workshop** | iAnimate | Game animation, mocap cleanup | $$$ | ianimate.net |
| **Character Animation Program** | AnimSchool | Full program, rigging + animation | $$$$ | animschool.com |
| **Character Animation** | CGMA | Portfolio-focused | $$$ | cgmasteracademy.com |
| **Blender Animation** | GDQuest | Blender-specific workflows | $ | gdquest.com |
| **Animation Basics** | School of Motion | Fundamentals for motion designers | $$ | schoolofmotion.com |
| **Character Animation with Blender** | Udemy | Blender animation from scratch | $ | udemy.com |
| **iAnimate Game Animation** | iAnimate | Game industry pipeline | $$$ | ianimate.net |

---

### 4.5 Software-Specific Resources

| Tool | Resource | Why |
|------|----------|-----|
| **Blender** | blender.org/documentation | Official docs, always up to date |
| **Blender** | Blender Animation (YouTube) | Practical tutorials |
| **Unreal Engine** | docs.unrealengine.com | Animation system docs |
| **Unreal Engine** | Unreal Sensei (YouTube) | UE animation tutorials |
| **Rokoko** | rokoko.com/tutorials | Mocap pipeline tutorials |
| **Rokoko** | Rokoko Studio docs | Software-specific workflows |

---

## 5. Weekly Practice Exercises

Each week has 5 daily exercises (30 minutes each) and one larger deliverable. The daily exercises build skills; the deliverable demonstrates mastery.

---

### Week 1: Weight and Timing

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Bouncing ball (rubber) — focus on squash/stretch | 30 min | 3-sec clip |
| 2 | Bouncing ball (bowling ball) — focus on weight | 30 min | 3-sec clip |
| 3 | Weight shift — film yourself first | 30 min | 4-sec clip |
| 4 | Pendulum swing — focus on arcs | 30 min | 3-sec clip |
| 5 | Push a box — combine weight and effort | 30 min | 6-sec clip |
| **Week** | **Deliverable: Bouncing ball comparison** | **2 hrs** | **Side-by-side of rubber vs bowling ball** |

---

### Week 2: Locomotion

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Block neutral walk (stepped mode) | 30 min | 4-sec blocked |
| 2 | Add breakdowns to neutral walk | 30 min | 4-sec refined |
| 3 | Spline and polish neutral walk | 30 min | 4-sec loop |
| 4 | Animate happy walk | 30 min | 4-sec loop |
| 5 | Animate sad walk | 30 min | 4-sec loop |
| **Week** | **Deliverable: Walk cycle comparison** | **2 hrs** | **3 walks side-by-side** |

---

### Week 3: Jumps and Physical Actions

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Block vertical jump | 30 min | 3-sec blocked |
| 2 | Polish vertical jump (hang time, squash) | 30 min | 3-sec polished |
| 3 | Block jump with turn | 30 min | 4-sec blocked |
| 4 | Animate lift (heavy object) | 30 min | 5-sec clip |
| 5 | Animate throw | 30 min | 3-sec clip |
| **Week** | **Deliverable: Jump compilation** | **2 hrs** | **Vertical jump + turn jump** |

---

### Week 4: Mocap Cleanup

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Import raw Rokoko clip, identify artifacts | 30 min | Audit notes |
| 2 | Fix foot plants (IK pinning) | 30 min | Fixed clip |
| 3 | Filter jitter from spine/arms | 30 min | Smoothed clip |
| 4 | Fix hand/shoulder penetrations | 30 min | Fixed clip |
| 5 | Full polish pass | 30 min | Polished clip |
| **Week** | **Deliverable: Before/after mocap cleanup** | **2 hrs** | **Side-by-side comparison** |

---

### Week 5: Emotion and Expression

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Study 7 emotions — gather reference | 30 min | Reference board |
| 2 | Pose Melusina in 7 emotions | 30 min | 7 still poses |
| 3 | Animate emotion walk (happy) | 30 min | 4-sec loop |
| 4 | Animate emotional transition | 30 min | 5-sec clip |
| 5 | Animate subtle expression | 30 min | 4-sec clip |
| **Week** | **Deliverable: Emotion pose sheet** | **2 hrs** | **7 poses + 1 transition** |

---

### Week 6: Thought Process

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Study eye movement in film | 30 min | Notes |
| 2 | Animate "decision moment" | 30 min | 6-sec clip |
| 3 | Animate realization | 30 min | 4-sec clip |
| 4 | Animate a lie | 30 min | 5-sec clip |
| 5 | Animate waiting | 30 min | 6-sec clip |
| **Week** | **Deliverable: Thought process compilation** | **2 hrs** | **3 clips showing internal state** |

---

### Week 7: Lip-Sync

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Study 15 visemes — film yourself | 30 min | Reference video |
| 2 | Animate viseme set | 30 min | 15-sec clip |
| 3 | Animate single sentence (mouth only) | 30 min | 4-sec clip |
| 4 | Add blinks and head movement | 30 min | 4-sec refined |
| 5 | Animate emotional speech | 30 min | 3x 3-sec clips |
| **Week** | **Deliverable: Lip-sync demo** | **2 hrs** | **Sentence + emotional variations** |

---

### Week 8: Full Performance

| Day | Exercise | Time | Deliverable |
|-----|----------|------|-------------|
| 1 | Block body for 15-sec monologue | 30 min | Blocked clip |
| 2 | Add face (eyes, brows, mouth) | 30 min | Face added |
| 3 | Polish timing (holds, breathing) | 30 min | Polished clip |
| 4 | Animate reaction shot | 30 min | 6-sec clip |
| 5 | Review and refine | 30 min | Final clip |
| **Week** | **Deliverable: 30-second performance** | **2 hrs** | **Polished character performance** |

---

## 6. How to Use Reference

Reference is not cheating — it's how professionals work. The goal is not to copy reference but to understand the principles behind it.

---

### 6.1 The Reference Library

Your reference lives in `Saved/AnimationReference/`. The folder structure:

```
Saved/AnimationReference/
├── body_mechanics/     # Jumps, turns, lifts, falls, weight shifts
├── acting/             # Emotional performances, facial expressions
├── lipsync/            # Close-up mouth, tongue, jaw, viseme reference
├── walk_cycles/        # Different moods (sad, happy, sneaky, tired)
└── gestures/           # Hand gestures, pointing, reaching
```

---

### 6.2 How to Gather Reference

**Before animating any shot:**

1. **Watch 3-5 reference clips** for the action you're doing
2. **Study the weight:** Where is the center of gravity? When does weight transfer?
3. **Note the timing:** How many frames for each phase? Where are the holds?
4. **Record yourself:** Act it out on phone — you'll notice things reference hides
5. **Don't copy, understand:** Reference teaches principles, not poses to trace

**Sources:**

| Source | Type | Best For | How to Access |
|--------|------|----------|---------------|
| Pinterest | Images | Pose reference, facial expressions | pinterest.com — create a board |
| YouTube "acting reference" | Video | Film scenes, emotional performances | youtube.com — search "acting reference" |
| Your own phone | Video | Acting out the shot yourself | Record yourself performing |
| Mixamo | 3D animation | Timing study, pre-mocap planning | mixamo.com |
| Rokoko Motion Library | Mocap | Cleanup practice, variety | rokoko.com/motion-library |

---

### 6.3 Reference Workflow

**Step 1: Define the action**
- What is the character doing? (physical action)
- Why are they doing it? (intention/emotion)
- What are they thinking? (internal state)

**Step 2: Find reference**
- Search `Saved/AnimationReference/` for similar actions
- If not found, gather from external sources (Pinterest, YouTube, phone)
- Save to the appropriate subfolder

**Step 3: Study the reference**
- Watch it 5 times without animating
- Note the key poses (freeze frame at extremes)
- Count the frames for each phase
- Identify the weight shifts and arcs

**Step 4: Apply the principles**
- Don't trace — understand WHY the reference looks right
- Apply the 12 principles to your animation
- Exaggerate where needed for clarity

**Step 5: Compare**
- Play your animation next to the reference
- Does it have the same weight? Timing? Energy?
- Adjust until it feels right

---

### 6.4 Building Your Reference Library

**Week 1-2: Body Mechanics**
- [ ] Jump (straight up, with turn, from height)
- [ ] Turn (180° quick, 360° slow)
- [ ] Lift (heavy object, light object)
- [ ] Fall (trip, collapse, controlled roll)
- [ ] Push/pull (heavy door, cart)

**Week 3-4: Acting**
- [ ] Joy (subtle smile → full laugh)
- [ ] Sadness (holding it in → breaking down)
- [ ] Anger (suppressed → explosive)
- [ ] Fear (wide eyes → flinch → retreat)
- [ ] Surprise (quick shock → slow realization)
- [ ] Disgust (nose wrinkle → full recoil)

**Week 5-6: Lip-Sync**
- [ ] Vowels (A, E, I, O, U — wide mouth shapes)
- [ ] Consonants (M, P, B — lip closure; S, T — tongue visible)
- [ ] Viseme set (15 standard visemes for animation)
- [ ] Fast dialogue (how mouth simplifies at speed)
- [ ] Singing (held notes, breath, emotion)

**Week 7-8: Walk Cycles**
- [ ] Neutral walk (baseline)
- [ ] Happy walk (bouncy, arms swinging)
- [ ] Sad walk (slow, head down, small steps)
- [ ] Sneaky walk (toe-first, arms in, slow)
- [ ] Tired walk (heavy, dragging feet)
- [ ] Confident walk (chest out, long strides)

---

## 7. Mocap Cleanup Workflow

The project uses a Rokoko mocap pipeline. This section documents the cleanup workflow from raw data to polished animation.

---

### 7.1 Pipeline Overview

```
Rokoko Studio → FBX Export → UE Import → Retarget → Cleanup → Polish → Render
```

**Key files and tools:**

| Tool | Location | Purpose |
|------|----------|---------|
| `import_rokoko_mocap.py` | `Content/Python/` | Rokoko FBX → `A_Src_Rokoko_*` on `SK_MocapSource` |
| `headless_retarget_mocap.py` | `Content/Python/` | `A_Src_*` → `A_Mocap_*` on `SK_Melusina` |
| `run_headless_mocap_retarget.ps1` | `Tools/` | Editor-closed batch retarget |
| `probe_ue_animation_tracks.py` | `Tools/` | Read-only bone pose sampling |
| `RTG_Mocap_to_Melusina_Current` | `Content/Melodia/Mocap/Retarget/` | Canonical IK retargeter (19 chains) |
| `test_melusina_animation_library.py` | `Tools/` | 343-line offline test suite |

---

### 7.2 Step-by-Step Cleanup Workflow

#### Step 1: Import Raw Mocap

```bash
# Drop FBX in Imports/Mocap/Rokoko/Inbox/
# Run import:
python Content/Python/import_rokoko_mocap.py --inbox
```

**What happens:** Rokoko FBX is imported as `A_Src_Rokoko_*` on `SK_MocapSource` skeleton.

**Check:** Open the clip in UE. Does the character move? Are all bones mapped?

#### Step 2: Retarget to Melusina

```bash
# Run headless retarget (editor CLOSED):
Tools/run_headless_mocap_retarget.ps1

# Check report:
cat Saved/Melodia/retarget_report.json
```

**What happens:** `A_Src_*` is retargeted to `A_Mocap_*` on `SK_Melusina` via the IK retargeter.

**Check:** `A_Mocap_*` clip exists, skeleton = `SK_Melusina_Skeleton`, no errors.

**If it fails:** Check `Saved/Melodia/retarget_report.json` for the specific error. Common issues:
- FBX bone names don't match `SK_MocapSource_Skeleton` → re-export from Rokoko with correct profile
- Target skeleton rebind failed → run `unreal.MelodiaAssetRepairLibrary.set_skeletal_mesh_skeleton()` manually in editor

#### Step 3: Audit for Artifacts

Open the retargeted clip in UE. Check for:

| Artifact | What to Look For | Severity |
|----------|------------------|----------|
| **Foot slide** | Foot moves while planted (sliding on floor) | HIGH |
| **Hand penetration** | Hand passes through body or prop | HIGH |
| **Jitter** | High-frequency noise on any bone | MEDIUM |
| **Drift** | Character slowly moves off-root | MEDIUM |
| **Shoulder twist** | Arm rotates unnaturally at shoulder | MEDIUM |
| **Pop** | Sudden jump in rotation between frames | LOW |

**Document findings** in `Saved/Audit/mocap_audit_YYYY-MM-DD.json`.

#### Step 4: Fix Foot Plants (IK Pinning)

**Problem:** Foot slides across the floor when it should stay planted.

**Solution:**
1. Identify the contact frames (when foot touches ground)
2. Switch to IK mode for the leg chain
3. Pin the foot position during contact frames
4. Blend back to IK/FK at the transition

**In UE:**
- Use the IK Retargeter's contact settings
- Or manually key the foot bone position during contact frames
- Check: foot stays planted, no sliding

#### Step 5: Fix Hand Penetration

**Problem:** Hand passes through the body or prop.

**Solution:**
1. Identify the penetration frames
2. Rotate the shoulder and elbow to move the hand clear
3. Maintain the arc of the arm (don't break the motion)
4. Check: hand clears the body, motion still looks natural

#### Step 6: Filter Jitter

**Problem:** High-frequency noise makes the animation look "buzzy."

**Solution:**
1. Identify which bones are jittery (usually fingers, spine, head)
2. Apply a low-pass filter or manual smoothing
3. Be careful: over-filtering kills the performance
4. Keep the "life" — some noise is natural

**In UE:**
- Use the Animation Modifier system for curve filtering
- Or export to Blender, smooth, re-import

#### Step 7: Polish Pass

**Final checks:**
- [ ] No foot slide
- [ ] No hand penetration
- [ ] No jitter
- [ ] Arcs are smooth (no linear motion)
- [ ] Timing feels right (not too fast/slow)
- [ ] Performance has "life" (not over-smoothed)
- [ ] Root motion is clean (no drift)

#### Step 8: Export and Render

```bash
# Export cleaned animation:
python Tools/export_melusina_animation_source.py --clip A_Melusina_Dance_Cleaned_v01

# Render in Blender:
# Open Templates/Melusina_Animation_Stage.blend
# Import the animation
# Set up cameras and lighting
# Render at 1600×2000, 30 FPS
```

---

### 7.3 When to Keep "Imperfections"

Not all mocap artifacts are bad. Some add life and realism:

| Imperfection | Keep When... | Fix When... |
|--------------|--------------|-------------|
| Slight foot slide | Character is on uneven ground | Character is on flat ground |
| Hand near body | Natural resting position | Clearly passing through |
| Head bob | Walking/running | Standing still |
| Finger jitter | Character is nervous/energetic | Character is calm |
| Asymmetry | Adds personality | Looks like a bug |

**Rule of thumb:** If it reads as intentional, keep it. If it reads as a bug, fix it.

---

### 7.4 Mocap Cleanup Checklist

Use this checklist for every mocap clip you clean:

```
MOcap CLEANUP CHECKLIST
=======================

Clip: _________________________ Date: _____________

IMPORT & RETARGET
[ ] FBX imported without errors
[ ] Retargeted to SK_Melusina
[ ] Report shows no errors

AUDIT
[ ] Foot slide identified
[ ] Hand penetration identified
[ ] Jitter identified
[ ] Drift identified
[ ] Shoulder twist identified

FIXES
[ ] Foot plants pinned (IK)
[ ] Hand penetration resolved
[ ] Jitter filtered
[ ] Drift corrected
[ ] Shoulder twist fixed

POLISH
[ ] Arcs are smooth
[ ] Timing feels right
[ ] Performance has life
[ ] Root motion is clean

EXPORT
[ ] Animation exported
[ ] Render test complete
[ ] Saved to Content/Melodia/.../Animations/

Notes:
_________________________________________________
_________________________________________________
```

---

## 8. Appendices

---

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **ABP** | Animation Blueprint — UE's animation state machine system |
| **Arc** | The curved path that a body part follows during movement |
| **Breakdown** | The pose between two key poses that defines the arc |
| **Contact pose** | The pose where the foot touches the ground in a walk cycle |
| **Ease in/out** | Slowing down at the start/end of an action (also: slow in/slow out) |
| **FACS** | Facial Action Coding System — a system for describing facial expressions |
| **FK** | Forward Kinematics — rotating joints from parent to child |
| **IK** | Inverse Kinematics — positioning a child bone and solving the chain |
| **Key pose** | The main storytelling poses of an animation |
| **Line of action** | An imaginary line running through a pose that shows its energy |
| **Mocap** | Motion capture — recording real movement for animation |
| **Overlapping action** | Different parts of the body moving at different rates |
| **Passing pose** | The pose where one foot passes the other in a walk cycle |
| **Pose-to-pose** | An animation method: set key poses first, then fill in breakdowns |
| **Retargeting** | Applying animation from one skeleton to another |
| **Root motion** | Movement of the root bone (hips) that drives the character's position |
| **Secondary action** | Supporting actions that reinforce the main action |
| **Spline** | Converting stepped keys to smooth interpolation |
| **Stepped mode** | Animation mode where keys hold until the next key (no interpolation) |
| **Staging** | Presenting an idea so it's unmistakably clear |
| **Straight-ahead** | An animation method: animate frame by frame without pre-planning |
| **Viseme** | A mouth shape corresponding to a sound in speech |

---

### Appendix B: Animation File Naming Convention

```
A_Melusina_<Action>_<Variation>_<Version>

Examples:
A_Melusina_JumpTurnLand_v01
A_Melusina_Walk_Happy_v02
A_Melusina_Speaking_Joy_v01
A_Melusina_Dance_Cleaned_v01
```

**Prefixes:**
- `A_` = Animation
- `SK_` = Skeleton
- `RTG_` = Retargeter
- `ABP_` = Animation Blueprint

---

### Appendix C: Render Settings for Animation Tests

| Setting | Value | Notes |
|---------|-------|-------|
| Resolution | 1600×2000 | Portrait orientation, good for social media |
| Frame rate | 30 FPS | Standard for animation |
| Samples | 64 (EEVEE) / 256 (Cycles) | Higher = cleaner, slower |
| Output | PNG sequence | Easier to fix than a single video file |
| Color space | sRGB | Standard for web/video |
| Denoising | ON | Clean up noise without extra samples |

---

### Appendix D: Weekly Self-Assessment

At the end of each week, rate yourself 1-5 on each principle:

| Principle | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Week 6 | Week 7 | Week 8 |
|-----------|--------|--------|--------|--------|--------|--------|--------|--------|
| Squash/Stretch | | | | | | | | |
| Anticipation | | | | | | | | |
| Staging | | | | | | | | |
| Pose-to-pose | | | | | | | | |
| Overlapping action | | | | | | | | |
| Ease in/out | | | | | | | | |
| Arcs | | | | | | | | |
| Secondary action | | | | | | | | |
| Timing | | | | | | | | |
| Exaggeration | | | | | | | | |
| Solid posing | | | | | | | | |
| Appeal | | | | | | | | |

**Scoring:**
- 1 = Don't understand it yet
- 2 = Understand it but can't apply it
- 3 = Can apply it with effort
- 4 = Can apply it consistently
- 5 = It's second nature

---

### Appendix E: Troubleshooting Common Problems

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Animation feels "floaty" | No weight, no timing variation | Add more frames to slow parts, fewer to fast parts |
| Character looks "robotic" | Linear interpolation, no arcs | Check graph editor, add ease curves, fix arcs |
| Foot slides on ground | No IK pinning during contact | Pin foot position during contact frames |
| Face looks dead | No blinks, no micro-movements | Add blinks (every 2-7 sec), small head movements |
| Lip-sync doesn't match audio | Wrong viseme timing | Check audio waveform, align visemes to phonemes |
| Animation feels "samey" | No contrast in timing | Vary the timing — some fast, some slow |
| Character looks off-balance | Weight not on a leg | Shift hips over the supporting leg |
| Mocap has too much jitter | High-frequency noise | Apply low-pass filter, but keep some "life" |
| Render takes too long | Too many samples | Use denoising, reduce samples, render at lower res for tests |

---

*Guide written 2026-09-03. Companion to `CHARACTER_ANIMATION_2_SEMESTER_PLAN.md`. Update as you learn what works for you.*
