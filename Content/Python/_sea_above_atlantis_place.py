import unreal
import json
import math
import random

# ============================================================
# ATLANTIS KITBASH PLACEMENT — Structured Integration
# ============================================================

random.seed(2026)

# Cathedral center
CX, CY, CZ = 0, 0, 13405

# ============================================================
# ATLANTIS MESH CATEGORIES
# ============================================================

ATLANTIS = {
    "arch": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchB.SM_ATL_Palace_ArchB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchC.SM_ATL_Palace_ArchC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchD.SM_ATL_Palace_ArchD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchE.SM_ATL_Palace_ArchE",
    ],
    "columns": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsA.SM_ATL_Palace_ColumnsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsB.SM_ATL_Palace_ColumnsB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsC.SM_ATL_Palace_ColumnsC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsD.SM_ATL_Palace_ColumnsD",
    ],
    "decorative": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BannerA.SM_ATL_Palace_BannerA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BannerB.SM_ATL_Palace_BannerB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BannerC.SM_ATL_Palace_BannerC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BannerD.SM_ATL_Palace_BannerD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_Cornice.SM_ATL_Palace_Cornice",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_DecorativeVaseA.SM_ATL_Palace_DecorativeVaseA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_DecorativeVaseB.SM_ATL_Palace_DecorativeVaseB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_DecorativeVaseC.SM_ATL_Palace_DecorativeVaseC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_DecorativeVaseD.SM_ATL_Palace_DecorativeVaseD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FountainA.SM_ATL_Palace_FountainA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FountainB.SM_ATL_Palace_FountainB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FountainC.SM_ATL_Palace_FountainC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailA.SM_ATL_Palace_GuardrailA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailB.SM_ATL_Palace_GuardrailB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailC.SM_ATL_Palace_GuardrailC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailD.SM_ATL_Palace_GuardrailD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailE.SM_ATL_Palace_GuardrailE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailF.SM_ATL_Palace_GuardrailF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailG.SM_ATL_Palace_GuardrailG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailH.SM_ATL_Palace_GuardrailH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailI.SM_ATL_Palace_GuardrailI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GuardrailJ.SM_ATL_Palace_GuardrailJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_NicheA.SM_ATL_Palace_NicheA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_NicheB.SM_ATL_Palace_NicheB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_NicheC.SM_ATL_Palace_NicheC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_NicheD.SM_ATL_Palace_NicheD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_NicheE.SM_ATL_Palace_NicheE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_OrnamentsA.SM_ATL_Palace_OrnamentsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_OrnamentsB.SM_ATL_Palace_OrnamentsB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_OrnamentsC.SM_ATL_Palace_OrnamentsC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_OrnamentsD.SM_ATL_Palace_OrnamentsD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_OrnamentsE.SM_ATL_Palace_OrnamentsE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PergolaA.SM_ATL_Palace_PergolaA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PergolaB.SM_ATL_Palace_PergolaB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PergolaC.SM_ATL_Palace_PergolaC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PergolaD.SM_ATL_Palace_PergolaD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterA.SM_ATL_Palace_PlanterA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterB.SM_ATL_Palace_PlanterB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterC.SM_ATL_Palace_PlanterC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterD.SM_ATL_Palace_PlanterD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterE.SM_ATL_Palace_PlanterE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterF.SM_ATL_Palace_PlanterF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterG.SM_ATL_Palace_PlanterG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterH.SM_ATL_Palace_PlanterH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterI.SM_ATL_Palace_PlanterI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterJ.SM_ATL_Palace_PlanterJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterK.SM_ATL_Palace_PlanterK",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterL.SM_ATL_Palace_PlanterL",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterM.SM_ATL_Palace_PlanterM",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterN.SM_ATL_Palace_PlanterN",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterO.SM_ATL_Palace_PlanterO",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterP.SM_ATL_Palace_PlanterP",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterQ.SM_ATL_Palace_PlanterQ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterR.SM_ATL_Palace_PlanterR",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterS.SM_ATL_Palace_PlanterS",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterT.SM_ATL_Palace_PlanterT",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterU.SM_ATL_Palace_PlanterU",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterV.SM_ATL_Palace_PlanterV",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_PlanterW.SM_ATL_Palace_PlanterW",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TorchA.SM_ATL_Palace_TorchA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TorchB.SM_ATL_Palace_TorchB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TorchC.SM_ATL_Palace_TorchC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TorchD.SM_ATL_Palace_TorchD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TorchE.SM_ATL_Palace_TorchE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseA.SM_ATL_Palace_VaseA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseB.SM_ATL_Palace_VaseB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseC.SM_ATL_Palace_VaseC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseD.SM_ATL_Palace_VaseD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseE.SM_ATL_Palace_VaseE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseF.SM_ATL_Palace_VaseF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseG.SM_ATL_Palace_VaseG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseH.SM_ATL_Palace_VaseH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseI.SM_ATL_Palace_VaseI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseJ.SM_ATL_Palace_VaseJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_VaseK.SM_ATL_Palace_VaseK",
    ],
    "seating": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchA.SM_ATL_Palace_BenchA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchB.SM_ATL_Palace_BenchB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchC.SM_ATL_Palace_BenchC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchD.SM_ATL_Palace_BenchD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchE.SM_ATL_Palace_BenchE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ChairA.SM_ATL_Palace_ChairA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ChairB.SM_ATL_Palace_ChairB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ChairC.SM_ATL_Palace_ChairC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolA.SM_ATL_Palace_StoolA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolB.SM_ATL_Palace_StoolB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolC.SM_ATL_Palace_StoolC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableA.SM_ATL_Palace_TableA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableB.SM_ATL_Palace_TableB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableC.SM_ATL_Palace_TableC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableD.SM_ATL_Palace_TableD",
    ],
    "nature": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeA.SM_ATL_Palace_TreeA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeB.SM_ATL_Palace_TreeB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeC.SM_ATL_Palace_TreeC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeD.SM_ATL_Palace_TreeD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeE.SM_ATL_Palace_TreeE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeF.SM_ATL_Palace_TreeF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeG.SM_ATL_Palace_TreeG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeH.SM_ATL_Palace_TreeH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeI.SM_ATL_Palace_TreeI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeJ.SM_ATL_Palace_TreeJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeK.SM_ATL_Palace_TreeK",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeL.SM_ATL_Palace_TreeL",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeM.SM_ATL_Palace_TreeM",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeN.SM_ATL_Palace_TreeN",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeO.SM_ATL_Palace_TreeO",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeP.SM_ATL_Palace_TreeP",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeQ.SM_ATL_Palace_TreeQ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeR.SM_ATL_Palace_TreeR",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeS.SM_ATL_Palace_TreeS",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsA.SM_ATL_Palace_ShrubsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsB.SM_ATL_Palace_ShrubsB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsC.SM_ATL_Palace_ShrubsC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsD.SM_ATL_Palace_ShrubsD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsE.SM_ATL_Palace_ShrubsE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsF.SM_ATL_Palace_ShrubsF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsG.SM_ATL_Palace_ShrubsG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsH.SM_ATL_Palace_ShrubsH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsI.SM_ATL_Palace_ShrubsI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsJ.SM_ATL_Palace_ShrubsJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsK.SM_ATL_Palace_ShrubsK",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsL.SM_ATL_Palace_ShrubsL",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsM.SM_ATL_Palace_ShrubsM",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsN.SM_ATL_Palace_ShrubsN",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsO.SM_ATL_Palace_ShrubsO",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsP.SM_ATL_Palace_ShrubsP",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsQ.SM_ATL_Palace_ShrubsQ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsR.SM_ATL_Palace_ShrubsR",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsS.SM_ATL_Palace_ShrubsS",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsT.SM_ATL_Palace_ShrubsT",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsU.SM_ATL_Palace_ShrubsU",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsV.SM_ATL_Palace_ShrubsV",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsW.SM_ATL_Palace_ShrubsW",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsX.SM_ATL_Palace_ShrubsX",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingA.SM_ATL_Palace_IvyHangingA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingB.SM_ATL_Palace_IvyHangingB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingC.SM_ATL_Palace_IvyHangingC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingD.SM_ATL_Palace_IvyHangingD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingE.SM_ATL_Palace_IvyHangingE",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingF.SM_ATL_Palace_IvyHangingF",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingG.SM_ATL_Palace_IvyHangingG",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingH.SM_ATL_Palace_IvyHangingH",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingI.SM_ATL_Palace_IvyHangingI",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingJ.SM_ATL_Palace_IvyHangingJ",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingK.SM_ATL_Palace_IvyHangingK",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingL.SM_ATL_Palace_IvyHangingL",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_IvyHangingM.SM_ATL_Palace_IvyHangingM",
    ],
    "props": [
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_Barrel.SM_ATL_Palace_Barrel",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelRackA.SM_ATL_Palace_BarrelRackA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelRackB.SM_ATL_Palace_BarrelRackB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelRackC.SM_ATL_Palace_BarrelRackC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelRackD.SM_ATL_Palace_BarrelRackD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelsA.SM_ATL_Palace_BarrelsA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelsB.SM_ATL_Palace_BarrelsB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelsC.SM_ATL_Palace_BarrelsC",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BarrelsD.SM_ATL_Palace_BarrelsD",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BasketA.SM_ATL_Palace_BasketA",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BasketB.SM_ATL_Palace_BasketB",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_GrapesStand.SM_ATL_Palace_GrapesStand",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_Harp.SM_ATL_Palace_Harp",
        "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_HayStack.SM_ATL_Palace_HayStack",
    ],
}

# Copernicus MIs
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
mis = [m for m in mis if "MI_Copernicus_" in m]

def pick_mi(mesh_name):
    """Pick a Copernicus MI based on mesh type."""
    if "Arch" in mesh_name or "Column" in mesh_name or "Base" in mesh_name:
        return next((m for m in mis if "CavernWeave" in m or "ChoirStone" in m), mis[0])
    elif "Tree" in mesh_name or "Shrub" in mesh_name or "Ivy" in mesh_name:
        return next((m for m in mis if "FrostBloom" in m or "FrozenFracture" in m), mis[1])
    elif "Bench" in mesh_name or "Chair" in mesh_name or "Table" in mesh_name or "Stool" in mesh_name:
        return next((m for m in mis if "PearlWeave" in m or "SingingSilk" in m), mis[2])
    elif "Banner" in mesh_name or "Cornice" in mesh_name or "Ornament" in mesh_name:
        return next((m for m in mis if "GildedCoral" in m or "MoltenCore" in m), mis[3])
    elif "Vase" in mesh_name or "Fountain" in mesh_name or "Planter" in mesh_name:
        return next((m for m in mis if "CrystalCathedral" in m or "FractalCathedral" in m), mis[4])
    elif "Torch" in mesh_name or "Harp" in mesh_name:
        return next((m for m in mis if "StarlitLoom" in m or "Voronoi" in m), mis[5])
    else:
        return mis[random.randint(0, len(mis)-1)]

def place_mesh(mesh_path, location, rotation=None, scale=None):
    """Place a mesh in the level."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        return None
    
    loc = unreal.Vector(location[0], location[1], location[2])
    rot = unreal.Rotator(0, 0, 0) if rotation is None else unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scl = unreal.Vector(1, 1, 1) if scale is None else unreal.Vector(scale[0], scale[1], scale[2])
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        
        # Apply Copernicus MI
        mi_path = pick_mi(mesh_path.split('/')[-1])
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        if mi:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("override_materials", [mi])
        
        return actor
    return None

# ============================================================
# PLACEMENT ZONES
# ============================================================

print("=== ATLANTIS KITBASH PLACEMENT ===\n")

total_placed = 0

# Zone 1: Processional arches (front of cathedral)
print("--- Zone 1: Processional Arches ---")
for i, mesh in enumerate(ATLANTIS["arch"]):
    angle = -90 + (i - len(ATLANTIS["arch"])/2) * 15  # Spread in front
    angle_rad = math.radians(angle)
    radius = 2500 + i * 200
    x = CX + math.cos(angle_rad) * radius
    y = CY + math.sin(angle_rad) * radius - 2000
    z = CZ + random.uniform(-200, 500)
    scale = random.uniform(2.0, 4.0)
    place_mesh(mesh, (x, y, z), rotation=(0, 0, angle + 90), scale=(scale, scale, scale))
    total_placed += 1

# Zone 2: Columned courtyard (sides)
print("--- Zone 2: Columned Courtyard ---")
for i, mesh in enumerate(ATLANTIS["columns"]):
    side = 1 if i % 2 == 0 else -1
    x = CX + side * (2000 + (i // 2) * 400)
    y = CY + random.uniform(-2000, 2000)
    z = CZ + random.uniform(-200, 800)
    scale = random.uniform(2.0, 4.0)
    place_mesh(mesh, (x, y, z), scale=(scale, scale, scale))
    total_placed += 1

# Zone 3: Decorative ring (around cathedral)
print("--- Zone 3: Decorative Ring ---")
for i, mesh in enumerate(ATLANTIS["decorative"][:30]):  # First 30
    angle = (i / 30) * 2 * math.pi
    radius = 3500 + random.uniform(-500, 500)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + random.uniform(-300, 1000)
    scale = random.uniform(1.5, 3.5)
    yaw = random.uniform(0, 360)
    place_mesh(mesh, (x, y, z), rotation=(0, 0, yaw), scale=(scale, scale, scale))
    total_placed += 1

# Zone 4: Seating area (plaza)
print("--- Zone 4: Seating Plaza ---")
for i, mesh in enumerate(ATLANTIS["seating"]):
    angle = random.uniform(0, 2 * math.pi)
    radius = 1500 + random.uniform(-500, 500)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius - 3000
    z = CZ + random.uniform(-200, 300)
    scale = random.uniform(1.5, 3.0)
    yaw = random.uniform(0, 360)
    place_mesh(mesh, (x, y, z), rotation=(0, 0, yaw), scale=(scale, scale, scale))
    total_placed += 1

# Zone 5: Nature border (outer ring)
print("--- Zone 5: Nature Border ---")
for i, mesh in enumerate(ATLANTIS["nature"][:30]):  # First 30
    angle = random.uniform(0, 2 * math.pi)
    radius = 5000 + random.uniform(-1000, 1000)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + random.uniform(-500, 500)
    scale = random.uniform(2.0, 4.0)
    place_mesh(mesh, (x, y, z), scale=(scale, scale, scale))
    total_placed += 1

# Zone 6: Props (scattered)
print("--- Zone 6: Props ---")
for i, mesh in enumerate(ATLANTIS["props"]):
    angle = random.uniform(0, 2 * math.pi)
    radius = 2000 + random.uniform(-1000, 2000)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + random.uniform(-300, 500)
    scale = random.uniform(1.5, 3.0)
    yaw = random.uniform(0, 360)
    place_mesh(mesh, (x, y, z), rotation=(0, 0, yaw), scale=(scale, scale, scale))
    total_placed += 1

print(f"\n=== Total Atlantis pieces placed: {total_placed} ===")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
