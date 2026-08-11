"""Wire battle OSC routes — FIXED: uses existing in_blender OSC In on port 9000.
Removes duplicate oscinCHOP issue that crashed TD.
"""
osc = op('/project1/osc')

# REUSE existing oscinCHOP on port 9000 (do NOT create duplicate)
battle_in = osc.op('in_blender')
if battle_in is None:
    battle_in = osc.create('oscinCHOP', 'in_blender')
    battle_in.par.port = 9000
battle_in.comment = 'OSC input on :9000 — receives Blender camera AND game battle events'
battle_in.nodeX = 200; battle_in.nodeY = -200

# Route table documenting battle OSC routes
routes_doc = osc.op('battle_routes')
if routes_doc is None:
    routes_doc = osc.create('tableDAT', 'battle_routes')
routes_doc.nodeX = 50; routes_doc.nodeY = -400
routes_doc.clear()
routes_doc.appendRow(['route', 'type', 'FX effect'])
routes_doc.appendRow(['/battle/grade', 'string', 'sparkle: perfect=gold burst, miss=red dim'])
routes_doc.appendRow(['/battle/combo', 'int', 'particle density 0-2x'])
routes_doc.appendRow(['/battle/enemy_broken', 'int', 'wish burst trigger'])
routes_doc.appendRow(['/battle/damage', 'float[2]', 'screen shake amp'])
routes_doc.appendRow(['/battle/ult_gauge', 'float', 'glow/rim intensity'])
routes_doc.appendRow(['/battle/phase', 'string', 'world BG shift'])
routes_doc.appendRow(['/battle/result', 'string', 'victory finale VFX'])
routes_doc.appendRow(['/rhythm/beat', 'int', 'beat flash pulse'])
routes_doc.appendRow(['/rhythm/bpm', 'float', 'BPM sync speed'])

print('BATTLE ROUTES: ' + str(routes_doc.numRows) + ' routes documented')
print('Listener: port 9000 (shared with Blender camera)')
print('')
print('Game -> TD flow:')
print('  battle_osc.py -> /battle/grade -> TD :9000 -> particles/sparkles')
print('  battle_osc.py -> /battle/combo -> TD :9000 -> particle density')
print('  battle_osc.py -> /battle/enemy_broken -> TD :9000 -> burst trigger')
