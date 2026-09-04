"""Prepare a relocatable derivative of the shared BellTree graph for SeaAbove.

Does not assign it to a live volume or regenerate actors. All authored topology,
meshes and point transforms are inherited; only point coordinate space changes.
"""
import unreal
import json
from pathlib import Path

src='/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden'
dst='/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden'
original=unreal.load_asset(src)
assert original
graph=unreal.load_asset(dst)
if graph is None:
    graph=unreal.EditorAssetLibrary.duplicate_asset(src,dst)
assert graph
assert len(graph.get_editor_property('nodes'))==len(original.get_editor_property('nodes'))
graph.modify()
points=0
groups=0
for node in graph.get_editor_property('nodes'):
    settings=node.get_settings()
    if isinstance(settings,unreal.PCGCreatePointsSettings):
        settings.modify()
        settings.set_editor_property('coordinate_space',unreal.PCGCoordinateSpace.LOCAL_COMPONENT)
        points+=len(settings.get_editor_property('points_to_create'))
        groups+=1
assert points==63 and groups==5,(points,groups)
for node in original.get_editor_property('nodes'):
    settings=node.get_settings()
    if isinstance(settings,unreal.PCGCreatePointsSettings):
        assert settings.get_editor_property('coordinate_space')==unreal.PCGCoordinateSpace.WORLD
unreal.EditorAssetLibrary.set_metadata_tag(graph,'SeaAboveSourceGraph',src)
unreal.EditorAssetLibrary.set_metadata_tag(graph,'SeaAbovePlacementConvention','LOCAL_COMPONENT; unit actor scale; authored centimeter transforms retained')
assert unreal.EditorAssetLibrary.save_loaded_asset(graph,False)
report={'source':src,'derivative':dst,'point_groups':groups,'authored_points':points,
        'coordinate_space':'LOCAL_COMPONENT','source_preserved':True,
        'assigned_to_live_volume':False,'generation_verified':False}
Path('C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/sea_above_belltree_derivative.json').write_text(json.dumps(report,indent=2))
print(report)
