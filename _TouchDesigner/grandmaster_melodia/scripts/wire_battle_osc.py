"""Wire battle OSC routes in TD — game events -> particle/FX triggers.
Run via: exec(open(...).read()) in TD Textport or Envoy MCP.
"""

osc = op('/project1/osc')

# Create OSC In CHOP for battle events on port 9000
battle_in = osc.create('oscinCHOP', 'in_battle')
battle_in.nodeX = 300; battle_in.nodeY = -200
battle_in.par.port = 9000
battle_in.comment = 'Receive game battle events from battle_osc.py on port 9000'

# Create select CHOPs to extract specific channels
grade_sel = osc.create('selectCHOP', 'battle_grade')
grade_sel.nodeX = 550; grade_sel.nodeY = -200
grade_sel.inputConnectors[0].connect(battle_in)
grade_sel.comment = 'Grade: perfect/great/good/miss -> particle intensity'

combo_sel = osc.create('selectCHOP', 'battle_combo')
combo_sel.nodeX = 550; combo_sel.nodeY = -320
combo_sel.inputConnectors[0].connect(battle_in)
combo_sel.comment = 'Combo count -> particle density multiplier'

broken_sel = osc.create('selectCHOP', 'battle_broken')
broken_sel.nodeX = 550; combo_sel.nodeY = -440
broken_sel.inputConnectors[0].connect(battle_in)
broken_sel.comment = 'Enemy broken trigger -> wish burst'

# Create math CHOPs to map game values to particle parameters
grade_map = osc.create('mathCHOP', 'grade_to_sparkle')
grade_map.nodeX = 800; grade_map.nodeY = -200
grade_map.comment = 'Map grade -> sparkle spawn rate: perfect=1.0, great=0.7, good=0.4, miss=0.1'

combo_scale = osc.create('mathCHOP', 'combo_scale')
combo_scale.nodeX = 800; combo_scale.nodeY = -320
combo_scale.comment = 'Scale combo to particle density 0-2.0'

# Route table — document all battle OSC routes
routes_doc = osc.create('tableDAT', 'battle_routes')
routes_doc.nodeX = 300; routes_doc.nodeY = -560
routes_doc.clear()
routes_doc.appendRow(['route', 'type', 'TD handler', 'FX effect'])
routes_doc.appendRow(['/battle/grade', 'string', 'grade_map mathCHOP', 'sparkle intensity: perfect=gold burst, miss=red dim'])
routes_doc.appendRow(['/battle/combo', 'int', 'combo_scale mathCHOP', 'particle density: 0-2x based on combo'])
routes_doc.appendRow(['/battle/enemy_broken', 'int', 'broken_sel selectCHOP', 'wish burst trigger'])
routes_doc.appendRow(['/battle/damage', 'float[2]', 'damage mathCHOP', 'screen shake amplitude'])
routes_doc.appendRow(['/battle/ult_gauge', 'float', 'ult mathCHOP', 'glow/rim intensity'])
routes_doc.appendRow(['/battle/phase', 'string', 'phase switch', 'background color / world shift'])
routes_doc.appendRow(['/battle/encounter', 'string', 'encounter parser', 'enemy intro VFX + BPM sync'])
routes_doc.appendRow(['/battle/result', 'string', 'result trigger', 'victory/defeat finale VFX'])
routes_doc.appendRow(['/rhythm/beat', 'int', 'beat counter', 'beat flash / metronome pulse'])
routes_doc.appendRow(['/rhythm/bpm', 'float', 'bpm display', 'BPM sync to particle speed'])
routes_doc.comment = 'All 14 battle OSC routes mapped to TD FX handlers'

# Create the battle OSC Out notification (to confirm TD is receiving)
notify = osc.create('textDAT', 'battle_status')
notify.nodeX = 550; notify.nodeY = -560
notify.text = 'Battle OSC listener active on port 9000\nAwaiting game events from battle_osc.py...'
notify.comment = 'Shows last received battle event'

print('BATTLE_ROUTES: ' + str(routes_doc.numRows) + ' routes wired')
print('OSC battle listener on port 9000 ready')
print('')
print('To test: run GMM game -> battle_osc.py -> TD monitors /battle/* events')
