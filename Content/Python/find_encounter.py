import unreal
import sys
L = unreal.log_warning

# Find encounter-related BPs
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# Search for encounter triggers
enc_filter = unreal.ARFilter()
enc_filter.set_editor_property('package_paths', ['/Game/Melodia/Enemies', '/Game/Melodia/Blueprints', '/Game/Melodia/_PROJECT/Blueprints'])
enc_filter.set_editor_property('recursive_paths', True)

assets = ar.get_assets(enc_filter)
for a in assets:
    name = str(a.asset_name)
    if 'encounter' in name.lower() or 'trigger' in name.lower() or 'enemy' in name.lower():
        L('Encounter asset: {} ({})'.format(name, a.package_path))

# Also check what RULES contains for opening flow
try:
    from gmm.game.rules_generated import RULES
    opening = RULES.get('opening_flow', {})
    L('Opening rules: {}'.format(json.dumps(opening, indent=2)))
except:
    L('Cannot import rules_generated')
    # Try direct path
    try:
        import importlib.util
        import os
        spec = importlib.util.spec_from_file_location('rules', unreal.Paths.project_dir() + 'Content/Python/gmm/game/rules_generated.py')
        rules_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_mod)
        opening = rules_mod.RULES.get('opening_flow', {})
        L('Opening rules (direct): {}'.format(str(opening)))
    except Exception as ex:
        L('Rules import failed: {}'.format(str(ex)))

L('DONE')
