"""Tests for Tools/animation/verify_clip_gate.py — pure-logic coverage (no editor needed).

Covers the classification and verdict composition rules. The Monolith-backed checks
(arm canon / seam / foot) are exercised live via the editor, not here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Tools" / "animation"))

import verify_clip_gate as gate
from unittest.mock import patch
import pytest


def test_unknown_one_shots_do_not_receive_a_loop_requirement():
    for name in ('A_Q_Melusina_Death01', 'A_Q_Melusina_Hit_Head', 'A_Melusina_Roll'):
        assert not gate.requires_seam(name)


def test_no_body_payload_is_an_error_even_when_rpc_reports_success():
    with patch.object(gate, 'call', return_value={'success': True, 'output': [
            {'type': 'warning', 'output': 'deprecated'},
            {'type': 'error', 'output': 'canonical mesh did not load'}]}):
        with pytest.raises(RuntimeError, match='no verified pose payload'):
            gate.actual_body_samples('/Game/TestMissingBody')


def test_wrong_body_payload_cannot_pass():
    import json
    payload={'body':'/Game/WrongBody','mode':'COMPRESSED','keys':1,'samples':[{}]}
    with patch.object(gate, 'call', return_value={'output':[
            {'type':'info','output':'MELUSINA_BODY_POSES='+json.dumps(payload)}]}):
        with pytest.raises(RuntimeError, match='wrong-body'):
            gate.actual_body_samples('/Game/TestWrongBody')


def test_final_key_root_scale_regression_is_rejected():
    rows=[{'root_scale':[1,1,1],'world':{'root_x':[0,0,88]}} for _ in range(61)]
    rows[-1]['root_scale']=[100,100,100]
    with patch.object(gate,'actual_body_samples',return_value={'samples':rows}):
        result=gate.check_root_units('/Game/TestUnits')
        assert result['pass'] is False and result['frame']==60


def test_final_key_right_arm_regression_is_rejected():
    contract={'arm_canon_cm':{'pass':[15.774,28.561,28.615],
                             'reject':[34.789,9.52,28.615],'tol_cm':1}}
    def positions(asset,bone,frame):
        chain=['shoulder','arm_stretch','forearm_stretch','hand']
        lengths=[15.774,28.561,28.615]
        if bone.endswith('_r') and frame==60: lengths=[34.789,9.52,28.615]
        index=chain.index(bone.rsplit('_',1)[0])
        return (sum(lengths[:index]),0,0)
    with patch.object(gate,'bone',side_effect=positions):
        result=gate.check_arm_canon('/Game/TestArms',contract,61)
        assert result['pass'] is False and result['worst']['r']['frame']==60


def test_middle_key_invalid_foot_quaternion_cannot_hide_in_a_one_shot():
    import copy
    names=['root','root_x','head_x','spine_01_x','foot_l','foot_r','toes_01_l','toes_01_r']+[
        b+'_'+s for s in ('l','r') for b in ('shoulder','arm_stretch','forearm_stretch','hand')]
    row={'world':{n:[0,0,0] for n in names},'root_scale':[1,1,1],
         'local':{n:{'p':[0,0,0],'q':[0,0,0,1]} for n in ['root','foot_l','foot_r','toes_01_l','toes_01_r']}}
    data={'samples':[copy.deepcopy(row) for _ in range(3)]}
    gate.validate_pose_payload(data)
    data['samples'][1]['local']['foot_r']['q']=[0,0,0,0]
    with pytest.raises(RuntimeError,match='zero quaternion'):
        gate.validate_pose_payload(data)


def test_single_key_regression_cannot_escape_sampling():
    assert gate._sample_frames(162) == list(range(162))


def test_charged_hold_and_air_loops_require_seam():
    for name in ('A_Spar_Mel_RMB_Loop', 'A_Melusina_JumpLoop', 'A_Melusina_Glide_InPlace'):
        assert gate.requires_seam(name)
    for name in ('A_Spar_Mel_RMB_Fire', 'A_Spar_Mel_RMB_Drawback', 'A_Shin_Cast'):
        assert not gate.requires_seam(name)


def test_disabled_root_motion_is_not_missing():
    assert gate.root_motion_value({'has_root_motion': False}) is False
    assert gate.root_motion_value({'bEnableRootMotion': False}) is False
    assert gate.root_motion_value({}) is None


def test_invalid_transforms_fail_closed():
    for fn in (lambda: gate.dist((float('nan'), 0, 0), (0, 0, 0)),
               lambda: gate._quat_angle((0, 0, 0, 0), (0, 0, 0, 1)),
               lambda: gate._quat_angle((0, 0, 0, float('inf')), (0, 0, 0, 1))):
        try:
            fn()
        except RuntimeError:
            continue
        raise AssertionError('invalid transform passed')
    assert gate._quat_angle((0, 0, 0, 2), (0, 0, 0, 1)) == 0


def test_classify_known_classes():
    assert gate.classify("A_Melusina_Idle") == "idle"
    assert gate.classify("A_Melusina_Walk_Loop") == "walk"
    assert gate.classify("A_Melusina_Sprint_Mocap") == "sprint"
    assert gate.classify("A_Shin_Cast") == "cast"
    assert gate.classify("A_Spar_Mel_RMB_Fire") == "fire"


def test_classify_unknown_is_default():
    assert gate.classify("SomeWeirdClip") == "default"


def test_loop_classes_are_true_loops_only():
    # true loops are seam-gated
    for c in ("idle", "walk", "run", "sprint"):
        assert c in gate.LOOP_CLASSES
    # one-shots animate THROUGH the clip and must NOT be seam-gated
    for c in ("cast", "fire", "drawback", "emote"):
        assert c not in gate.LOOP_CLASSES


def test_dist():
    assert gate.dist((0, 0, 0), (3, 4, 0)) == 5.0


def test_foot_class_ranges_exist():
    for k in ("idle", "walk", "run", "sprint", "jump", "land", "cast", "default"):
        lo, hi = gate.FOOT_CLASS[k]
        assert lo < hi


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all gate tests passed")
