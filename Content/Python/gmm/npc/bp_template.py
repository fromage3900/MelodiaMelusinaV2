"""NPC Blueprint Template Generator — creates base BP structure for NPCs.

Run in Unreal Editor Python Console:
    import gmm.npc.bp_template; gmm.npc.bp_template.create_npc_blueprint_template()
"""
from __future__ import annotations

try:
    import unreal
except ImportError:
    unreal = None


TEMPLATE_BP_PATH = "/Game/NPCs/Blueprints/BP_NPC_Base"
ANIM_BP_PATH = "/Game/NPCs/Blueprints/ABP_NPC_Base"
ARCHEtypes = ["SakuraDreamer", "CosmicWeaver", "MirageDancer"]


def create_npc_base_blueprint() -> bool:
    """Create the base NPC Blueprint with all required components."""
    if unreal is None:
        return False

    # Check if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(TEMPLATE_BP_PATH):
        print(f"Base NPC Blueprint already exists: {TEMPLATE_BP_PATH}")
        return True

    try:
        # Create Character Blueprint
        bp_factory = unreal.BlueprintFactory()
        bp_factory.parent_class = unreal.Character
        
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_NPC_Base",
            "/Game/NPCs/Blueprints",
            unreal.Blueprint,
            bp_factory
        )

        if not bp:
            print("Failed to create base NPC Blueprint")
            return False

        # The blueprint will be created but needs manual component setup
        # We'll document what needs to be added
        unreal.EditorAssetLibrary.save_asset(TEMPLATE_BP_PATH)
        print(f"Created base NPC Blueprint: {TEMPLATE_BP_PATH}")
        return True

    except Exception as e:
        print(f"Error creating base NPC Blueprint: {e}")
        return False


def create_npc_anim_blueprint() -> bool:
    """Create base Animation Blueprint for NPCs."""
    if unreal is None:
        return False

    if unreal.EditorAssetLibrary.does_asset_exist(ANIM_BP_PATH):
        print(f"Base AnimBP already exists: {ANIM_BP_PATH}")
        return True

    try:
        abp_factory = unreal.AnimBlueprintFactory()
        abp_factory.target_skeleton = None  # Will be set per-NPC
        abp_factory.parent_class = unreal.AnimInstance
        
        abp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "ABP_NPC_Base",
            "/Game/NPCs/Blueprints",
            unreal.AnimBlueprint,
            abp_factory
        )

        if not abp:
            print("Failed to create base AnimBP")
            return False

        unreal.EditorAssetLibrary.save_asset(ANIM_BP_PATH)
        print(f"Created base AnimBP: {ANIM_BP_PATH}")
        return True

    except Exception as e:
        print(f"Error creating AnimBP: {e}")
        return False


def create_archetype_blueprints() -> dict:
    """Create specialized Blueprints for each archetype."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    results = {}
    
    for arch in ARCHEtypes:
        bp_path = f"/Game/NPCs/Blueprints/BP_NPC_{arch}"
        
        if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
            results[arch] = {"status": "exists", "path": bp_path}
            continue

        try:
            # Duplicate base BP
            new_bp = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
                TEMPLATE_BP_PATH,
                "/Game/NPCs/Blueprints",
                f"BP_NPC_{arch}"
            )
            
            if new_bp:
                results[arch] = {"status": "created", "path": bp_path}
            else:
                results[arch] = {"status": "failed", "error": "Duplicate returned None"}
                
        except Exception as e:
            results[arch] = {"status": "error", "error": str(e)}

    return results


def generate_setup_instructions() -> str:
    """Generate setup instructions for manual Blueprint configuration."""
    return f"""
═══ NPC BLUEPRINT SETUP INSTRUCTIONS ═══

1. BASE BLUEPRINT: {TEMPLATE_BP_PATH}
   Open in Blueprint Editor and add components:
   
   [Components]
   - CapsuleComponent (root)
     - Capsule Half Height: 96
     - Capsule Radius: 34
   
   - SkeletalMeshComponent (Mesh)
     - Parent: CapsuleComponent
     - Relative Location: (0, 0, -96)
     - Relative Rotation: (0, -90, 0)
     - Animation Mode: Use Animation Blueprint
     - Anim Class: Set per-archetype
   
   - SpringArmComponent (CameraBoom)
     - Parent: CapsuleComponent
     - Target Arm Length: 300
     - Socket Offset: (0, 50, 50)
     - Use Pawn Control Rotation: True
     - Enable Camera Lag: True
     - Camera Lag Speed: 10
   
   - CameraComponent (FollowCamera)
     - Parent: CameraBoom
     - Use Pawn Control Rotation: False
     - Field of View: 60

   - MelodiaNPCComponent (Custom)
     - NPCId: Set per-instance
     - Archetype: Set per-instance
     - MPC Reference: MPC_NPC_<Archetype>
   
   - MelodiaInteractionComponent (Custom)
     - InteractionType: Set per-instance
     - DialogueTree: Set per-instance
     - ShopInventory: Set per-instance
   
   - MelodiaBattleComponent (Custom)
     - EnemyId: Set per-instance
     - Difficulty: Set per-instance
     - BattleRewards: Set per-instance

   [Event Graph - Input Bindings]
   - Enhanced Input Actions:
     * IA_Move -> AddMovementInput
     * IA_Look -> AddControllerYawInput/PitchInput
     * IA_Jump -> Jump
     * IA_Interact -> Custom Event: OnInteract

   [Construction Script]
   - Get MPC_SakuraDream reference
   - Bind material parameters to NPC MPC
   - Apply outfit variant materials

2. ARCHETYPE ANIMATION BLUEPRINTS:
   For each archetype, create:
   - ABP_NPC_SakuraDreamer
   - ABP_NPC_CosmicWeaver
   - ABP_NPC_MirageDancer

   Each should have:
   - State Machine: Locomotion (Idle/Walk/Run) + Interaction Montage Slot
   - Blend Space 1D: BS_Locomotion (Speed 0-600)
   - Facial Expression Blendspace (Blend by enum)
   - Spring Bone Update (Late Update) for hair/cloth
   - Spring Bone Collision for body/skirt

3. PER-NPC BLUEPRINTS (10 total):
   For each NPC in vrm_source.py, create:
   BP_NPC_<SourceID> (e.g., BP_NPC_SD_01_SakuraMaiden)
   
   Inherit from: BP_NPC_<Archetype>
   Override defaults:
   - Mesh: SK_<SourceID>
   - AnimClass: ABP_NPC_<Archetype>
   - MPC: MPC_NPC_<Archetype>
   - OutfitVariant: per vrm_source
   - InteractionConfig: per level_populator.py
   - SpawnTransform: per level_populator.py

4. MATERIAL PARAMETER BINDING:
   In Construction Script of each NPC BP:
   
   ```
   MPC = LoadObject(MPC_NPC_Archetype)
   DynamicMI = CreateDynamicMaterialInstance(0, Mesh)
   DynamicMI.SetScalarParameterValue("NPC_DreamIntensity", 1.0)
   DynamicMI.SetVectorParameterValue("NPC_ColorShift", ArchetypeColor)
   Mesh.SetMaterial(0, DynamicMI)
   ```

5. COLLISION PRESETS:
   - Capsule: Pawn
   - Mesh: CharacterMesh (custom - ignore camera, overlap pawn)
   - SpringArm: NoCollision

═══════════════════════════════════════
"""

def print_setup_instructions():
    print(generate_setup_instructions())


if __name__ == "__main__":
    if unreal:
        print("Creating NPC Blueprint templates...")
        create_npc_base_blueprint()
        create_npc_anim_blueprint()
        results = create_archetype_blueprints()
        print(f"Archetype BPs: {results}")
        print_setup_instructions()
    else:
        print("NPC Blueprint Template Generator")
        print("Run in Unreal Editor Python Console")
        print_setup_instructions()