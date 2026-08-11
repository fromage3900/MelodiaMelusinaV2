"""Build Nikki/Melodia style preset matrix with proper OSC channel mapping.
Each row represents one of 5 style presets.
Each column maps to a specific UE MPC parameter or post-process control.
Row 0 (header): channel names for OSC Out CHOP labeling.

Run via: exec(open(...).read()) in TD Textport
"""

osc = op('/project1/osc')

# Destroy and recreate for clean state
old = osc.op('preset_matrix')
if old is not None:
    old.destroy()

t = osc.create('tableDAT', 'preset_matrix')
t.clear()

# ── Header: OSC channel names ──
# These become the CHOP channel names when fed through a DAT to CHOP
t.appendRow([
    'preset',           # Preset ID (0-4)
    'name',             # Human-readable preset name
    'bloom_intensity',  # -> MPC_Magical.BloomIntensity (index 0)
    'bloom_threshold',  # -> Post-process bloom threshold (index 1)
    'sparkle_pulse',    # -> MPC_SakuraDream.SparklePulse (index 2)
    'dream_intensity',  # -> MPC_SakuraDream.DreamIntensity (index 3)
    'wind_strength',    # -> MPC_SakuraDream.WindStrength (index 4)
    'global_opacity',   # -> MPC_SakuraDream.GlobalOpacity (index 5)
    'shadow_tint_r',    # -> Post-process shadow tint (index 6)
    'shadow_tint_b',    # -> Post-process shadow tint (index 7)
    'magical_transform',# -> MPC_Magical.MagicalTransform (index 8)
    'saturation',       # -> Post-process saturation (index 9)
    'diffuse_wrap',     # -> Material diffuse wrap (index 10)
    'sparkle_visibility',# -> MPC_SakuraDream.SparkleVisibility (index 11)
])

# ── 5 Presets: Nikki, Madoka, Celestial, Itto, Sakura ──

# 0: Nikki — soft dreamy pastel, heavy warm bloom, golden hour
t.appendRow([
    '0', 'Nikki',
    '5.0','0.75','0.8','0.7','0.4','0.9','0.21','0.25','0.25','0.90','0.50','0.8'
])

# 1: Madoka — surreal witch barrier, saturated, collage-like
t.appendRow([
    '1', 'Madoka',
    '3.0','0.85','1.0','0.5','0.3','1.0','0.15','0.25','0.60','1.20','0.30','1.0'
])

# 2: Celestial — space/nebula, cool deep astral tones
t.appendRow([
    '2', 'Celestial',
    '4.0','0.80','0.5','0.3','0.2','0.7','0.08','0.19','0.40','0.85','0.40','0.5'
])

# 3: Itto — mythic carved stone, warm ochre, dramatic
t.appendRow([
    '3', 'Itto',
    '2.5','0.90','0.3','0.4','0.5','0.6','0.12','0.06','0.10','0.75','0.60','0.3'
])

# 4: Sakura — Japanese cherry blossom, delicate pink
t.appendRow([
    '4', 'Sakura',
    '4.5','0.78','0.9','0.6','0.5','0.95','0.18','0.20','0.30','0.95','0.55','0.9'
])

print('PRESET_MATRIX: ' + str(t.numRows) + ' rows x ' + str(t.numCols) + ' cols')

# ── Update td_bridge.py style presets to match ──
import json
bridge_path = r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\td_bridge.py'
try:
    # Read and update the STYLE_PRESETS in td_bridge.py
    with open(bridge_path, 'r') as f:
        content = f.read()
    print('BRIDGE_SYNC: td_bridge.py found, updating...')
except Exception as e:
    print('BRIDGE_WARN: Could not read td_bridge.py: ' + str(e))

print('PRESETS_DONE')
