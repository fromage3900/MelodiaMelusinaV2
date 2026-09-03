# Interlocking Modular Architecture System - Cohesive Framework

## 🎯 Vision

Create a **unified procedural architecture system** that combines:
- ✅ Baroque cathedral vaulting (ornament, curves, ribs)
- ✅ M.C. Escher impossible geometry (paradoxes, recursion)
- ✅ Interlocking modular pieces (builds coherently)
- ✅ Advanced ornamental generation (procedural detail)

**Result**: Greybox architecture that feels **cohesive, ornate, and architecturally sound** while remaining **impossible, disorienting, and game-unique**.

---

## 🧩 Modular Architecture Hierarchy

### LEVEL 0: Primitive Components (Atoms)

```
WALLS
├── Straight Wall (configurable length, height, thickness)
├── Curved Wall (arc, radius, sweep angle)
├── Angled Wall (pitch, yaw, configurable)
└── Impossible Wall (forced perspective variant)

FLOORS
├── Flat Floor (with optional slope)
├── Curved Floor (spherical or hyperbolic)
├── Stepped Floor (staircase integrated)
└── Gravity-Rotated Floor (perpendicular plane)

CEILINGS
├── Flat Ceiling (barrel vault over room)
├── Barrel Vault Ceiling (curved surface)
├── Ribbed Vault Ceiling (baroque detail)
└── Impossible Ceiling (non-euclidean variant)

DOORS & OPENINGS
├── Standard Door Frame
├── Arched Doorway (baroque)
├── Portal Frame (Escher-style transition)
└── Impossible Aperture (doesn't align properly)

ORNAMENT ELEMENTS
├── Pilasters (wall-mounted columns)
├── Capitals (column tops)
├── Moldings (cornices, baseboards)
├── Bosses (vault ornament)
└── Keystones (arch detail)
```

### LEVEL 1: Room Types (Modular Rooms)

```
STANDARD ROOMS
├── Rectangular Room (1-4 doors, 1 ceiling type)
├── Circular Room (radial symmetry)
├── Hexagonal Room (efficient packing)
└── L-Shaped Room (multiple sub-zones)

BAROQUE ROOMS
├── Grand Hall (high ceilings, vault, niches)
├── Chapel (altar focus, dome/vault)
├── Salon (ornate, formal)
├── Gallery (long, picture-focused)
└── Vestibule (entrance space)

ESCHER ROOMS
├── Staircase Loop (impossible stairs)
├── Gravity Chamber (multiple gravity directions)
├── Recursive Room (room contains itself)
├── Metamorphic Chamber (morphing walls/floor/ceiling)
└── Perspective Trick Room (forced camera angles)

HYBRID ROOMS
├── Baroque + Escher (ornate impossible)
├── Cathedral + Portal (vaulted with Escher exit)
└── Recursive Baroque (nested ornate spaces)

SPECIFICATIONS (Each Room Type)
├── Interior dimensions (width, depth, height ranges)
├── Connection points (door positions, portal locations)
├── Ceiling type (flat, vault, ribbed, impossible)
├── Ornament style (baroque, gothic, minimal, escher)
├── Gravity direction (vertical, multiple, rotating)
└── Tessellation (how it connects to adjacent rooms)
```

### LEVEL 2: Room Combinations (Tessellation)

```
SIMPLE GRIDS
├── 2×2 rooms (4 connected spaces)
├── 3×3 rooms (9 connected spaces)
├── 1×N corridor (linear progression)
└── Radial hub (central room + 6 satellites)

BAROQUE PATTERNS
├── Enfilade (doors aligned through rooms)
├── Symmetrical pairs (mirror layouts)
├── Grand staircase hub (rooms radiate from stairs)
└── Chapel + vestibule + nave (sacred sequence)

ESCHER PATTERNS
├── Impossible loop (rooms connect A→B→C→A)
├── Nested recursion (small room contains large room)
├── Gravity gradient (gravity rotates between rooms)
└── Metamorphic progression (style changes room-to-room)

HYBRID PATTERNS
├── Baroque ornament + Escher geometry (best of both)
├── Cathedral vault + impossible exits
├── Recursive baroque (ornate at each level)
└── Tessellated impossible rooms
```

### LEVEL 3: Complete Architecture (Spaces)

```
DUNGEONS
├── Baroque dungeon (ornate torture chamber aesthetic)
├── Escher dungeon (disorienting maze)
└── Hybrid dungeon (beautiful but impossible)

TEMPLES / CATHEDRALS
├── Baroque cathedral (vaulted, ribbed, ornate)
├── Escher temple (impossible sacred geometry)
└── Hybrid temple (ornate vaulted with impossible layout)

PALACES
├── Baroque palace (grand halls, salons, enfilade)
├── Escher palace (impossible perspective layout)
└── Hybrid palace (combines both aesthetics)

TOWERS
├── Baroque tower (spiraling, ornate)
├── Escher tower (gravity-shifting, impossible climbs)
└── Hybrid tower (ornate but disorienting)

GARDENS / COURTYARDS
├── Baroque garden (formal, symmetrical)
├── Escher garden (impossible perspective view)
└── Hybrid garden (ornate with spatial tricks)
```

---

## 🔗 Interlocking Mechanism Design

### CONNECTOR TYPES

```
TYPE 1: STANDARD DOOR
├── Alignment: Perfect (connects properly)
├── Geometry: Both rooms' doorways align
├── Usage: Normal navigation
├── Feel: Expected, logical

TYPE 2: PORTAL / TELEPORTATION
├── Alignment: Impossible (can't geometrically connect)
├── Geometry: Portal on each side (visually separate)
├── Usage: Connects impossible layouts
├── Feel: Magical, surreal, intentional break from logic

TYPE 3: CURVED / WARPED CORRIDOR
├── Alignment: Geometrically continuous
├── Geometry: Corridor bends space (hyperbolic or spherical)
├── Usage: Connects while maintaining illusion
├── Feel: Disorienting but navigable

TYPE 4: FORCED PERSPECTIVE PASSAGE
├── Alignment: Camera-trick connection
├── Geometry: Rooms appear disconnected but are adjacent
├── Usage: Creates visual paradox
├── Feel: Confusing until understood

TYPE 5: RECURSIVE PASSAGE
├── Alignment: Room leads back to itself
├── Geometry: Spiral that loops
├── Usage: Escher-like continuous path
├── Feel: Mesmerizing, impossible, yet coherent
```

### CONNECTION RULES

**Geometric Alignment**:
```
Each room type has defined connection points:
  Standard room:  4 sides, 1 center (floor), 1 ceiling
  Circular room:  360° perimeter + center + ceiling
  Hexagonal room: 6 sides + center + ceiling
  
Connection logic:
  Adjacent rooms must have matching connection types
  OR bridged by special transitional geometry
```

**Gravity Alignment**:
```
Single-gravity rooms: All have same "up" direction
Multiple-gravity rooms: Each has own up direction
Mixed rooms: Transition zones gradually shift gravity

Rule: Gravity must be consistent within each room
      Gravity CAN change between rooms
```

**Scale Consistency**:
```
Doors should be similar height
Corridors should be consistent width (or intentionally shift)
Ceilings should follow logical progression (or intentionally violate)

Rule: Consistency is expected
      Breaking consistency = Escher moment
```

---

## 🎨 Ornamental Generation System

### COMPONENT-BASED ORNAMENT

```
PILASTER SYSTEM
├── Base plate (plinth)
├── Fluted shaft (12-20 grooves)
├── Capital (doric/ionic/corinthian style)
└── Optional: reliefs, scrolls, inscriptions

Parameters:
  ├── Width (0.5-2.0m)
  ├── Height (follows room height)
  ├── Style (doric=simple, corinthian=ornate)
  ├── Flute count (8-20)
  └── Material (stone/stucco variant)
```

**Placement Algorithm**:
```
1. Identify wall length
2. Determine pilaster count (1-12 per wall)
3. Distribute evenly along wall
4. Place at corners first (required)
5. Fill gaps with additional pilasters
6. Ensure spacing looks intentional

Result: Formal, symmetrical arrangement
```

### VAULT RIB SYSTEM

```
AUTOMATIC RIB GENERATION
├── Base vault (barrel, groin, or shell)
├── Primary ribs (4-8 main structural lines)
├── Secondary ribs (fill between primaries)
├── Tertiary ribs (fine detail, optional)
├── Bosses (at rib intersections)
├── Coffers (panels between ribs)
└── Keystones (tiny stone detail along ribs)

Parameters:
  ├── Vault type (barrel/groin/shell)
  ├── Rib count (8-32 total)
  ├── Boss size (0.5-2.0m diameter)
  ├── Coffer size (0.5-1.5m × 0.5-1.5m)
  ├── Detail level (low/medium/high)
  └── Material variation (stone/stucco options)
```

**Procedural Algorithm**:
```
1. Create base vault surface (mathematical surface)
2. Place primary ribs (follow major curves)
3. Subdivide spaces with secondary ribs
4. Add tertiary ribs for detail (if detail_level=high)
5. Place bosses at rib intersections
6. Create coffer grid on ceiling
7. Optional: add relief details to bosses
8. Optional: add painted/frescoed elements
```

### MOLDING & TRIM SYSTEM

```
PREDEFINED PROFILES
├── Astragal (simple bead molding)
├── Scotia (concave base transition)
├── Cyma (S-curve molding)
├── Dentil (tooth pattern, repeating)
├── Egg-and-Dart (ornamental pattern)
├── Torus (rounded bulge)
└── Custom profiles (user-defined)

PLACEMENT
├── Crown molding (top of walls, under ceiling)
├── Baseboard (bottom of walls, above floor)
├── Door frame (around doorways)
├── Window frame (around windows)
├── Arch surround (around arches)
└── Cornice overhang (ceiling perimeter)

Parameters:
  ├── Profile type (astragal/scotia/etc)
  ├── Size (scale of profile)
  ├── Placement (crown/base/frame)
  └── Material (stone/stucco/painted)
```

---

## 🔄 Ornament Variation System

### STYLE VARIANTS

```
MINIMAL ORNAMENT
├── Pilasters: None (clean walls)
├── Moldings: Simple baseboards only
├── Vault: Plain barrel, no ribs
├── Feel: Modern, clean, geometric

BAROQUE ORNAMENT
├── Pilasters: Multiple, decorative capitals
├── Moldings: Complex profiles everywhere
├── Vault: Ribbed, bosses, coffered
├── Feel: Opulent, historical, ornate

GOTHIC ORNAMENT
├── Pilasters: Pointed arches, ribbed surfaces
├── Moldings: Sharp, flowing curves
├── Vault: Complex ribbed geometry
├── Feel: Vertical emphasis, spiritual

ROCOCO ORNAMENT
├── Pilasters: Curving, organic
├── Moldings: Elaborate scroll work
├── Vault: Shell-like, undulating
├── Feel: Playful, asymmetrical, organic

BRUTALIST ORNAMENT
├── Pilasters: Structural ribs (non-decorative intent)
├── Moldings: Minimal, geometric
├── Vault: Exposed concrete suggest curved ribs
├── Feel: Raw, structural, honest
```

### PROCEDURAL VARIATION

```
Algorithm:
  1. Base style selected (baroque/gothic/etc)
  2. Variation slider (0=canonical, 1=wild variation)
  3. Random seed for determinism
  4. Apply style characteristics
  5. Vary parameters within style rules
  
Examples:
  ├── Baroque + high variation = elaborate baroque excess
  ├── Gothic + low variation = strict gothic rules
  ├── Minimal + medium variation = clean with subtle details
  └── Rococo + high variation = wildly organic shapes
```

---

## 📊 System Coherence Map

### Coherence Principles

```
PRINCIPLE 1: CONSISTENT GEOMETRY
├── Within a room: Geometry must be internally consistent
├── Between connected rooms: Geometry must align (or intentionally break)
├── Across complex: Overall layout must make sense (or Escher-intentional sense)

PRINCIPLE 2: CONSISTENT ORNAMENT
├── Pilaster style matches across walls of room
├── Rib style matches across vault surfaces
├── Molding profiles match where they meet
├── Material appearance consistent (unless style-specified otherwise)

PRINCIPLE 3: INTENTIONAL BREAKS
├── Breaks are marked (usually with transitional geometry)
├── Player understands breaks (or discovers them)
├── Breaks feel intentional, not accidental

PRINCIPLE 4: SCALE RELATIONSHIPS
├── Pilasters to room width (1:8 ratio typical)
├── Door height to wall height (2/3 to 3/4 typical)
├── Ceiling height to room width (1.5:1 to 2:1 typical)
├── Rib spacing to room size (proportional scale)
```

### Quality Checksum

```
Before approving a generated space:

GEOMETRY CHECK
├── [ ] Walls meet at corners without overlap
├── [ ] Doors align with wall placement
├── [ ] Ceilings are above walls (no clipping)
├── [ ] Connections to adjacent rooms are valid

ORNAMENT CHECK
├── [ ] Pilasters are consistent in style across walls
├── [ ] Vault ribs follow consistent logic
├── [ ] Moldings align where pieces meet
├── [ ] Detail level consistent throughout space

COHERENCE CHECK
├── [ ] Room feels intentional (not random)
├── [ ] Ornament supports architecture (not fighting it)
├── [ ] Impossible elements are intentional Escher moments
├── [ ] Overall composition feels cohesive

GAME DESIGN CHECK
├── [ ] Space is navigable (not impossible to move through)
├── [ ] Space is interesting (rewards exploration)
├── [ ] Space supports gameplay (combat, puzzles, narrative)
└── [ ] Space is memorable (unique feel)
```

---

## 🎮 Gameplay Integration

### Combat Spaces
```
Ornament provides:
├── Cover opportunities (pillars, ribs, bosses)
├── Verticality (vaulted ceilings, platforms)
├── Sightline complexity (not all areas visible)
└── Navigation challenge (understand space layout)

Design principle:
  Beautiful ornament should not impede combat
  Ornament should enhance tactical options
```

### Puzzle Spaces
```
Ornament provides:
├── Visual focus points (bosses, capitals, rosettes)
├── Geometric logic (rib intersections, coffer grids)
├── Spatial clues (proportions suggest function)
└── Escher paradoxes (impossible geometry = puzzle)

Design principle:
  Ornament hints at solution without solving
  Geometry suggests mechanical relationships
```

### Narrative Spaces
```
Ornament provides:
├── Cultural flavor (baroque = wealth, history)
├── Emotional tone (ornate = grandeur, impossible = surreal)
├── Visual storytelling (frescoes, relief sculpture)
└── Sense of place (each room feels intentional)

Design principle:
  Ornament communicates story without dialogue
  Architecture itself tells history
```

---

## 🚀 Implementation Priority

### Phase 1: Foundation (Weeks 1-2)
- [ ] Core room types (rectangular, circular, hexagonal)
- [ ] Standard connections (doors, corridors)
- [ ] Basic pilaster system
- [ ] Simple vault generation (barrel vault)

**Output**: Functional greybox rooms with basic ornament

---

### Phase 2: Baroque System (Weeks 3-4)
- [ ] Advanced vault types (groin, ribbed)
- [ ] Boss and coffer generation
- [ ] Molding profiles system
- [ ] Ornament variation

**Output**: Full baroque architectural generation

---

### Phase 3: Escher System (Weeks 5-6)
- [ ] Impossible room types
- [ ] Portal connections
- [ ] Gravity-shifting chambers
- [ ] Recursive geometry

**Output**: Escher-inspired impossible spaces

---

### Phase 4: Integration (Weeks 7-8)
- [ ] Hybrid baroque + Escher spaces
- [ ] Tessellation and complex layouts
- [ ] Advanced ornamental generation
- [ ] Full coherence system

**Output**: Complete, cohesive architecture system

---

## 💡 Design Philosophy

```
COHERENCE IS KING
├── Every ornament serves a purpose
├── Every geometry has a reason
├── Impossible elements are intentional art
└── System maintains internal logic (even when illogical)

PROCEDURAL WITH CONTROL
├── Generation is automatic
├── But controllable at every level
├── Artists can fine-tune any parameter
└── Hybrid manual + procedural workflow

BAROQUE MEETS ESCHER
├── Ornamental richness (baroque tradition)
├── Spatial paradox (Escher inspiration)
├── Game readiness (greybox to final asset)
└── Unique aesthetic (not quite either tradition)
```

---

**Status**: Framework Design Complete  
**Complexity Level**: Advanced (4-week implementation)  
**Game Design Value**: Extremely High (unique visual identity)  
**Asset Generation**: Fully Procedural + Artist-Controllable

