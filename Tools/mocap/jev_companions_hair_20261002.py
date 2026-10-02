"""Jev packet - companion animation + perch + hair, 2026-10-02. Closed candidate sets; Jev selects only."""
import json
STATE = {
 "sir": "ABP_SirMelodious FlightLocomotion: Fly/Perch/Takeoff/Land. Fly->Land when Speed<T; Land->Fly only when Speed>=T, so a stationary Sir plays Land once and holds the last frame. Measured: zero bone motion over 2.2s. A_Sir_Fly_Loop moves 18 cm (feathers); A_Sir_Perch_Idle moves 0.56 cm (effectively static). Pawn is CMC walking, mesh relative z +62, capsule half-height 88 => mesh hovers ~shoulder height 68 cm beside Melusina. No ASirPerchPoint in Morning. CURRENT_STATE: no named shoulder-perch socket on Melusina; stock Sir is an AI-following JRPG pawn; do not replace with a flight pawn or create a second companion owner.",
 "sheep": "ABP_ChoralSheep Locomotion Idle/Walk/Run + new Graze/Harmonize (wired). Old A_Sheep_Idle moves one toe 3 cm over 6s (near-static). New clips A_ChoralSheep_TailWag (16 cm), EarFlick, Bleat exist and are not used by idle. Sheep follow + grounding + Speed-driven run already verified.",
 "hair": "WaterHairMesh (SK_MelusinaHair, KawaiiPhysics ABP) attached to CharacterMesh0 head_x with rel (0,144.2,-15.9); hair comp world sits ~144cm below head_x by design (cancels bone-space offset). Owner reports hair offset from head bone. Not yet measured in motion.",
 "eyes": "Eye irises/lashes attach to head_x in BP BeginPlay; root cause of one failure mode found and fixed (GetComponentByClass(SkeletalMeshComponent) was ambiguous once my WaveHarp instrument skeletal comp existed); an intermittent detach to socket None remains unexplained.",
}
Q = {
 "sir_idle": ("How does a stationary Sir animate?", ["GATE_LAND_TRANSITION_SO_FLY_LOOP_IS_THE_HOVER_IDLE","AUTHOR_NEW_GROUND_IDLE_IN_CASCADEUR_FIRST","LEAVE_AS_IS"]),
 "sheep_idle": ("How does a stationary sheep gain life?", ["LAYER_TAILWAG_AND_EARFLICK_AS_TIMED_IDLE_VARIANTS_IN_ABP","AUTHOR_NEW_IDLE_IN_BLENDER_FIRST","LEAVE_AS_IS"]),
 "sir_perch": ("How is Sir perched neatly?", ["FOLLOW_TO_A_SHOULDER_SOCKET_ON_MELUSINA_WITHOUT_REPLACING_THE_PAWN","LAND_ON_AUTHORED_SIRPERCHPOINT_IN_MORNING","LEAVE_HOVER_AND_ONLY_FIX_OFFSET"]),
 "hair_next": ("What is the first hair step?", ["MEASURE_HAIR_VS_HEAD_BONE_IN_MOTION_FIRST","RETARGET_HAIR_ROOT_OFFSET_NOW","LEAVE_AS_IS"]),
}
from typesafe_sdk import TypeSafeClient
from typesafe_sdk._core.questions import Choice
qs = {k: Choice(instructions=v[0], criteria={o: None for o in v[1]}) for k, v in Q.items()}
with TypeSafeClient() as c:
    r = c.system_one(state={"verified_state": STATE}, questions=qs)
out = {"schema":"melodia.jev.companions_hair.v1","source":"jev-live","model":str(getattr(r,"model",None)),"answers":{k:{"choice":a.choice,"reason":getattr(a,"reason",None)} for k,a in r.answers.items()}}
json.dump(out, open("Saved/Audit/ArcheryGoalSession_20261001/JevCompanionsHair_20261002.json","w"), indent=2); print(json.dumps(out, indent=1))
