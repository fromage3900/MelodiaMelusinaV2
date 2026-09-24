# -*- coding: utf-8 -*-
"""Melodia / Melusina — build_sbs.py (v2 M1 Nikki deepen)

Generates openable Adobe Substance 3D Designer package:
  SBS_Melusina_SimpleDiffuse.sbs

M1 denser than v1 scaffold:
  - Fashion color stack (Primary→AO/wear→Secondary wash→Accent rim→stroke→soft post)
  - Gouache Normal From Height (curvature + stroke → levels → blur → NFH)
  - Moonglow cymatics (procedural rings via levels/distance/warp + optional bitmaps)
  - vcol_melodia masks + BeatBoost×B emissive makeup
  - All lookdev knobs dynamically wired

Run:
  python build_sbs.py
  python build_sbs.py --cook

Author: Melodia pipeline (HandpaintPrep 2026-09-23 / M1 2026-09-24)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
OUT_SBS = HERE / "SBS_Melusina_SimpleDiffuse.sbs"
EXPORTS = HERE / "exports"

DESIGNER_DIR = Path(r"C:\Program Files\Adobe\Adobe Substance 3D Designer")
SBSCOOKER = DESIGNER_DIR / "sbscooker.exe"

# ZenLantern / Melodia defaults — Infinity Nikki soft fashion bar
PRIMARY = (0.9608, 0.9255, 0.8431, 1.0)   # #F5ECD7 paper
SECONDARY = (0.5451, 0.3686, 0.2353, 1.0) # #8B5E3C cedar
ACCENT = (1.0, 0.7882, 0.4706, 1.0)       # #FFC978 glow
SHADOW = (0.22, 0.20, 0.28, 1.0)          # cool grey-lavender (not brown mud)

_uid = 2100000000


def uid() -> int:
    global _uid
    _uid += 1
    return _uid


def f4(t) -> str:
    return " ".join(f"{float(x):.8g}" for x in t)


def dyn_get_float1(param_name: str) -> str:
    root = uid()
    return f"""\
                  <dynamicValue>
                    <rootnode v="{root}"/>
                    <paramNodes>
                      <paramNode>
                        <uid v="{root}"/>
                        <function v="get_float1"/>
                        <type v="256"/>
                        <funcDatas>
                          <funcData>
                            <name v="get_float1"/>
                            <constantValue><constantValueString v="{param_name}"/></constantValue>
                          </funcData>
                        </funcDatas>
                      </paramNode>
                    </paramNodes>
                  </dynamicValue>"""


def dyn_get_float4(param_name: str) -> str:
    root = uid()
    return f"""\
                  <dynamicValue>
                    <rootnode v="{root}"/>
                    <paramNodes>
                      <paramNode>
                        <uid v="{root}"/>
                        <function v="get_float4"/>
                        <type v="2048"/>
                        <funcDatas>
                          <funcData>
                            <name v="get_float4"/>
                            <constantValue><constantValueString v="{param_name}"/></constantValue>
                          </funcData>
                        </funcDatas>
                      </paramNode>
                    </paramNodes>
                  </dynamicValue>"""


def slider(ident, label, default, lo=0.0, hi=1.0, step=0.01, group="Melusina Lookdev", desc=""):
    u = uid()
    desc_xml = f"<description v=\"{escape(desc)}\"/>" if desc else ""
    return u, f"""\
      <paraminput>
        <identifier v="{ident}"/>
        <uid v="{u}"/>
        <attributes>
          <label v="{escape(label)}"/>
          {desc_xml}
        </attributes>
        <type v="256"/>
        <defaultValue><constantValueFloat1 v="{default}"/></defaultValue>
        <defaultWidget>
          <name v="slider"/>
          <options>
            <option><name v="clamp"/><value v="1"/></option>
            <option><name v="default"/><value v="{default}"/></option>
            <option><name v="max"/><value v="{hi}"/></option>
            <option><name v="min"/><value v="{lo}"/></option>
            <option><name v="step"/><value v="{step}"/></option>
          </options>
        </defaultWidget>
        <group v="{escape(group)}"/>
      </paraminput>"""


def color_param(ident, label, rgba, group="Melusina Colors", desc=""):
    u = uid()
    d = f"{rgba[0]};{rgba[1]};{rgba[2]};{rgba[3]}"
    desc_xml = f"<description v=\"{escape(desc)}\"/>" if desc else ""
    return u, f"""\
      <paraminput>
        <identifier v="{ident}"/>
        <uid v="{u}"/>
        <attributes>
          <label v="{escape(label)}"/>
          {desc_xml}
        </attributes>
        <type v="2048"/>
        <defaultValue><constantValueFloat4 v="{f4(rgba)}"/></defaultValue>
        <defaultWidget>
          <name v="color"/>
          <options>
            <option><name v="default"/><value v="{d}"/></option>
            <option><name v="min"/><value v="0"/></option>
            <option><name v="max"/><value v="1"/></option>
            <option><name v="clamp"/><value v="1"/></option>
          </options>
        </defaultWidget>
        <group v="{escape(group)}"/>
      </paraminput>"""


def img_input(ident, label, gray: bool, usage: str | None, group="Mesh Maps"):
    u = uid()
    usages = ""
    if usage:
        comps = "RGBA"
        usages = f"""\
        <usages>
          <usage>
            <components v="{comps}"/>
            <name v="{usage}"/>
          </usage>
        </usages>"""
    default = '<defaultValue><constantValueFloat1 v="0.5"/></defaultValue>' if gray else \
              '<defaultValue><constantValueFloat4 v="0.5 0.5 0.5 1"/></defaultValue>'
    return u, f"""\
      <paraminput>
        <identifier v="{ident}"/>
        <uid v="{u}"/>
        <attributes>
          <label v="{escape(label)}"/>
        </attributes>
        {usages}
        <isConnectable v="1"/>
        <type v="{2 if gray else 1}"/>
        {default}
        <defaultWidget><name v=""/><options/></defaultWidget>
        <group v="{escape(group)}"/>
      </paraminput>"""


def graph_out(ident, label, usage: str | None):
    u = uid()
    usages = ""
    if usage:
        usages = f"""\
        <usages>
          <usage>
            <components v="RGBA"/>
            <name v="{usage}"/>
          </usage>
        </usages>"""
    return u, f"""\
      <graphoutput>
        <identifier v="{ident}"/>
        <uid v="{u}"/>
        <attributes><label v="{escape(label)}"/></attributes>
        {usages}
      </graphoutput>"""


def input_bridge(entry_uid: int, gray: bool, x: float, y: float):
    n, o = uid(), uid()
    ctype = 2 if gray else 1
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="{ctype}"/></compOutput></compOutputs>
        <compImplementation>
          <compInputBridge>
            <entry v="{entry_uid}"/>
            <parameters>
              <parameter><name v="outputsize"/><relativeTo v="1"/><paramValue><constantValueInt2 v="0 0"/></paramValue></parameter>
              <parameter><name v="format"/><relativeTo v="1"/><paramValue><constantValueInt32 v="0"/></paramValue></parameter>
              <parameter><name v="pixelsize"/><relativeTo v="1"/><paramValue><constantValueFloat2 v="1 1"/></paramValue></parameter>
              <parameter><name v="pixelratio"/><relativeTo v="1"/><paramValue><constantValueInt32 v="1"/></paramValue></parameter>
              <parameter><name v="tiling"/><relativeTo v="1"/><paramValue><constantValueInt32 v="0"/></paramValue></parameter>
              <parameter><name v="randomseed"/><relativeTo v="1"/><paramValue><constantValueInt32 v="0"/></paramValue></parameter>
            </parameters>
          </compInputBridge>
        </compImplementation>
      </compNode>"""


def output_bridge(graph_out_uid: int, src_node: int, src_out: int, x: float, y: float):
    n = uid()
    return n, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <connections>
          <connection>
            <identifier v="inputNodeOutput"/>
            <connRef v="{src_node}"/>
            <connRefOutput v="{src_out}"/>
          </connection>
        </connections>
        <compImplementation>
          <compOutputBridge><output v="{graph_out_uid}"/></compOutputBridge>
        </compImplementation>
      </compNode>"""


def uniform_color_from_param(param_name: str, x: float, y: float):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="1"/></compOutput></compOutputs>
        <compImplementation>
          <compFilter>
            <filter v="uniform"/>
            <parameters>
              <parameter>
                <name v="outputcolor"/>
                <paramValue>
{dyn_get_float4(param_name)}
                </paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def uniform_const(rgba, gray: bool, x: float, y: float):
    n, o = uid(), uid()
    ctype = 2 if gray else 1
    color_switch = ""
    if gray:
        color_switch = """\
              <parameter>
                <name v="colorswitch"/>
                <paramValue><constantValueBool v="0"/></paramValue>
              </parameter>"""
        oc = f"{rgba[0]} {rgba[0]} {rgba[0]} 1"
    else:
        oc = f4(rgba)
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="{ctype}"/></compOutput></compOutputs>
        <compImplementation>
          <compFilter>
            <filter v="uniform"/>
            <parameters>
              {color_switch}
              <parameter>
                <name v="outputcolor"/>
                <paramValue><constantValueFloat4 v="{oc}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def grayconv(src_n, src_o, weights, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="grayscaleconversion"/>
            <parameters>
              <parameter>
                <name v="channelsweights"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{f4(weights)}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def blend(dst_n, dst_o, src_n, src_o, mode: int, x, y, opacity=1.0,
          mask_n=None, mask_o=None, gray=False, opacity_param: str | None = None):
    n, o = uid(), uid()
    ctype = 2 if gray else 1
    conns = f"""\
        <connections>
          <connection>
            <identifier v="destination"/>
            <connRef v="{dst_n}"/>
            <connRefOutput v="{dst_o}"/>
          </connection>
          <connection>
            <identifier v="source"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>"""
    if mask_n is not None:
        conns += f"""
          <connection>
            <identifier v="opacity"/>
            <connRef v="{mask_n}"/>
            <connRefOutput v="{mask_o}"/>
          </connection>"""
    conns += "\n        </connections>"
    if opacity_param:
        opac_xml = f"""\
              <parameter>
                <name v="opacitymult"/>
                <relativeTo v="0"/>
                <paramValue>
{dyn_get_float1(opacity_param)}
                </paramValue>
              </parameter>"""
    else:
        opac_xml = f"""\
              <parameter>
                <name v="opacitymult"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{opacity}"/></paramValue>
              </parameter>"""
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="{ctype}"/></compOutput></compOutputs>
        {conns}
        <compImplementation>
          <compFilter>
            <filter v="blend"/>
            <parameters>
              <parameter>
                <name v="blendingmode"/>
                <relativeTo v="0"/>
                <paramValue><constantValueInt32 v="{mode}"/></paramValue>
              </parameter>
{opac_xml}
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def dyn_float1_as_float4(param_name: str) -> str:
    """Pack exposed float1 into float4 for levels levelinmid (cooker-safe)."""
    g = uid(); v2 = uid(); v4 = uid()
    return f"""\
                  <dynamicValue>
                    <rootnode v="{v4}"/>
                    <paramNodes>
                      <paramNode>
                        <uid v="{g}"/>
                        <function v="get_float1"/>
                        <type v="256"/>
                        <funcDatas>
                          <funcData>
                            <name v="get_float1"/>
                            <constantValue><constantValueString v="{param_name}"/></constantValue>
                          </funcData>
                        </funcDatas>
                      </paramNode>
                      <paramNode>
                        <uid v="{v2}"/>
                        <function v="vector2"/>
                        <type v="512"/>
                        <connections>
                          <connection><identifier v="componentsin"/><connRef v="{g}"/></connection>
                          <connection><identifier v="componentslast"/><connRef v="{g}"/></connection>
                        </connections>
                      </paramNode>
                      <paramNode>
                        <uid v="{v4}"/>
                        <function v="vector4"/>
                        <type v="2048"/>
                        <connections>
                          <connection><identifier v="componentsin"/><connRef v="{v2}"/></connection>
                          <connection><identifier v="componentslast"/><connRef v="{v2}"/></connection>
                        </connections>
                      </paramNode>
                    </paramNodes>
                  </dynamicValue>"""


def levels_mid(src_n, src_o, x, y, mid=0.5, mid_param: str | None = None,
               in_low=0.0, in_high=1.0, out_low=0.0, out_high=1.0):
    n, o = uid(), uid()
    if mid_param:
        mid_xml = f"""\
              <parameter>
                <name v="levelinmid"/>
                <relativeTo v="0"/>
                <paramValue>
{dyn_float1_as_float4(mid_param)}
                </paramValue>
              </parameter>"""
    else:
        mid_xml = f"""\
              <parameter>
                <name v="levelinmid"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{mid} {mid} {mid} 0.5"/></paramValue>
              </parameter>"""
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="levels"/>
            <parameters>
              <parameter>
                <name v="levelinlow"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{in_low} {in_low} {in_low} 0"/></paramValue>
              </parameter>
              <parameter>
                <name v="levelinhigh"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{in_high} {in_high} {in_high} 1"/></paramValue>
              </parameter>
{mid_xml}
              <parameter>
                <name v="leveloutlow"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{out_low} {out_low} {out_low} 0"/></paramValue>
              </parameter>
              <parameter>
                <name v="levelouthigh"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat4 v="{out_high} {out_high} {out_high} 1"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def blur(src_n, src_o, intensity: float, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="blur"/>
            <parameters>
              <parameter>
                <name v="intensity"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{intensity}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def sharpen(src_n, src_o, intensity: float, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="sharpen"/>
            <parameters>
              <parameter>
                <name v="intensity"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{intensity}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def distance_filter(mask_n, mask_o, dist_val: float, x, y):
    """Atomic distance from mask — soft moonglow rings (cooker-safe dyn distance)."""
    n, o = uid(), uid()
    root = uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="mask"/>
            <connRef v="{mask_n}"/>
            <connRefOutput v="{mask_o}"/>
          </connection>
          <connection>
            <identifier v="source"/>
            <connRef v="{mask_n}"/>
            <connRefOutput v="{mask_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="distance"/>
            <parameters>
              <parameter>
                <name v="distance"/>
                <relativeTo v="0"/>
                <paramValue>
                  <dynamicValue>
                    <rootnode v="{root}"/>
                    <paramNodes>
                      <paramNode>
                        <uid v="{root}"/>
                        <function v="const_float1"/>
                        <type v="256"/>
                        <funcDatas>
                          <funcData>
                            <name v="const_float1"/>
                            <constantValue><constantValueFloat1 v="{dist_val}"/></constantValue>
                          </funcData>
                        </funcDatas>
                      </paramNode>
                    </paramNodes>
                  </dynamicValue>
                </paramValue>
              </parameter>
              <parameter>
                <name v="combinedistance"/>
                <relativeTo v="0"/>
                <paramValue><constantValueBool v="0"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def warp(src_n, src_o, grad_n, grad_o, intensity: float, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
          <connection>
            <identifier v="inputgradient"/>
            <connRef v="{grad_n}"/>
            <connRefOutput v="{grad_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="warp"/>
            <parameters>
              <parameter>
                <name v="intensity"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{intensity}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def directional_warp(src_n, src_o, inten_n, inten_o, intensity: float, angle: float, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="2"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
          <connection>
            <identifier v="inputintensity"/>
            <connRef v="{inten_n}"/>
            <connRefOutput v="{inten_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="directionalwarp"/>
            <parameters>
              <parameter>
                <name v="intensity"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{intensity}"/></paramValue>
              </parameter>
              <parameter>
                <name v="warpangle"/>
                <relativeTo v="0"/>
                <paramValue><constantValueFloat1 v="{angle}"/></paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""


def normal_from_height(src_n, src_o, strength_param: str, x, y):
    n, o = uid(), uid()
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="1"/></compOutput></compOutputs>
        <connections>
          <connection>
            <identifier v="input1"/>
            <connRef v="{src_n}"/>
            <connRefOutput v="{src_o}"/>
          </connection>
        </connections>
        <compImplementation>
          <compFilter>
            <filter v="normal"/>
            <parameters>
              <parameter>
                <name v="intensity"/>
                <relativeTo v="0"/>
                <paramValue>
{dyn_get_float1(strength_param)}
                </paramValue>
              </parameter>
            </parameters>
          </compFilter>
        </compImplementation>
      </compNode>"""



def instance_node(path: str, out_id: str, x, y, connections=None, params_xml="", gray=True):
    """compInstance referencing sbs:// package graph (cook-flattened → denser SBSAR)."""
    n, o = uid(), uid()
    ctype = 2 if gray else 1
    conns = ""
    if connections:
        parts = []
        for ident, sn, so in connections:
            parts.append(f"""\
          <connection>
            <identifier v="{ident}"/>
            <connRef v="{sn}"/>
            <connRefOutput v="{so}"/>
          </connection>""")
        conns = "<connections>" + "".join(parts) + "\n        </connections>"
    return n, o, f"""\
      <compNode>
        <uid v="{n}"/>
        <GUILayout><gpos v="{x} {y} 0"/></GUILayout>
        <compOutputs><compOutput><uid v="{o}"/><comptype v="{ctype}"/></compOutput></compOutputs>
        {conns}
        <compImplementation>
          <compInstance>
            <path v="{path}"/>
            <parameters>
{params_xml}
            </parameters>
            <outputBridgings>
              <outputBridging>
                <uid v="{o}"/>
                <identifier v="{out_id}"/>
              </outputBridging>
            </outputBridgings>
          </compInstance>
        </compImplementation>
      </compNode>"""


def build() -> str:
    global _uid
    _uid = 2100000000
    file_uid = "{" + str(uuid.uuid4()) + "}"
    graph_uid = uid()

    chunks_pi = []
    _, xml = color_param("PrimaryColor", "Primary Color", PRIMARY,
                         desc="Melodia base albedo — ZenLantern paper / fashion block")
    chunks_pi.append(xml)
    _, xml = color_param("SecondaryColor", "Secondary Color", SECONDARY,
                         desc="Cedar / lacquer wash on ribs, frames, charms")
    chunks_pi.append(xml)
    _, xml = color_param("AccentColor", "Accent Color", ACCENT,
                         desc="Glow embroidery + beat emissive tint")
    chunks_pi.append(xml)
    _, xml = color_param("ShadowColor", "Shadow Color", SHADOW,
                         desc="Cool grey-lavender multiply under AO/wear (Nikki soft NPR)")
    chunks_pi.append(xml)

    _, xml = slider("BrushStrokeIntensity", "Brush / Stroke Intensity", 0.25,
                    desc="NPR stroke breakup into albedo + gouache height")
    chunks_pi.append(xml)
    _, xml = slider("GouacheDepth", "Gouache Depth", 0.55,
                    desc="Curvature bent to height before Normal From Height")
    chunks_pi.append(xml)
    _, xml = slider("CymaticIntensity", "Cymatic Intensity", 0.35,
                    desc="Moonglow rings / FrozenFracture contribution 0→hero")
    chunks_pi.append(xml)
    _, xml = slider("BeatBoost", "Beat Boost", 0.45,
                    desc="vcol.B amplify for stage-makeup emissive + cymatic")
    chunks_pi.append(xml)
    _, xml = slider("RoughnessMin", "Roughness Min", 0.35)
    chunks_pi.append(xml)
    _, xml = slider("RoughnessMax", "Roughness Max", 0.72)
    chunks_pi.append(xml)
    _, xml = slider("MetallicAccent", "Metallic Accent", 0.12,
                    desc="Jewelry kisses only — not full-surface metal")
    chunks_pi.append(xml)
    _, xml = slider("NormalStrength", "Normal Strength", 1.15, lo=0.0, hi=4.0, step=0.05)
    chunks_pi.append(xml)
    _, xml = slider("ShadowSpread", "Shadow / AO Spread", 0.55,
                    desc="Tighten / open AO×wear cavity darken")
    chunks_pi.append(xml)
    _, xml = slider("CurvatureOpacity", "Curvature Color Opacity", 0.40,
                    desc="Secondary / decoration edge wash strength")
    chunks_pi.append(xml)

    i_ao, xml = img_input("MeshAO", "Mesh AO", True, "ambientOcclusion", "Mesh Maps")
    chunks_pi.append(xml)
    i_curv, xml = img_input("Curvature", "Curvature", True, "curvature", "Mesh Maps")
    chunks_pi.append(xml)
    i_wn, xml = img_input("WorldNormal", "World Normal (optional)", False, "worldSpaceNormal", "Mesh Maps")
    chunks_pi.append(xml)
    i_vcol, xml = img_input("vcol_melodia", "vcol_melodia (RGBA)", False, None, "Melodia Vertex Color")
    chunks_pi.append(xml)
    i_cym_h, xml = img_input("CymaticHeight", "Cymatic / FrozenFracture Height", True, "height", "Cymatic")
    chunks_pi.append(xml)
    i_cym_op, xml = img_input("CymaticOpacity", "Cymatic Opacity / Seed Mask", True, None, "Cymatic")
    chunks_pi.append(xml)
    i_brush, xml = img_input("BrushStrokeMap", "Brush / Stroke Map (optional)", True, None, "NPR")
    chunks_pi.append(xml)

    chunks_go = []
    outs = {}
    for ident, label, usage in [
        ("BaseColor", "Melodia BaseColor", "baseColor"),
        ("Normal", "Melodia Normal (Gouache)", "normal"),
        ("Roughness", "Melodia Roughness", "roughness"),
        ("Metallic", "Melodia Metallic", "metallic"),
        ("Height", "Melodia Height", "height"),
        ("Emissive", "Melodia Emissive", "emissive"),
        ("Opacity", "Melodia Opacity", "opacity"),
        ("Mask_Wear", "Mask Wear (vcol.R)", None),
        ("Mask_Decoration", "Mask Decoration (vcol.G)", None),
        ("Mask_Beat", "Mask Beat (vcol.B)", None),
        ("Mask_Cymatic", "Mask Cymatic", None),
        ("ORM", "Optional ORM pack (AO Rough Metal)", None),
    ]:
        u, xml = graph_out(ident, label, usage)
        outs[ident] = u
        chunks_go.append(xml)

    nodes = []

    # ========== INPUT BRIDGES ==========
    y0 = 0
    ao_n, ao_o, xml = input_bridge(i_ao, True, -1600, y0); nodes.append(xml)
    cv_n, cv_o, xml = input_bridge(i_curv, True, -1600, y0 + 160); nodes.append(xml)
    wn_n, wn_o, xml = input_bridge(i_wn, False, -1600, y0 + 320); nodes.append(xml)
    vc_n, vc_o, xml = input_bridge(i_vcol, False, -1600, y0 + 480); nodes.append(xml)
    ch_n, ch_o, xml = input_bridge(i_cym_h, True, -1600, y0 + 640); nodes.append(xml)
    co_n, co_o, xml = input_bridge(i_cym_op, True, -1600, y0 + 800); nodes.append(xml)
    br_n, br_o, xml = input_bridge(i_brush, True, -1600, y0 + 960); nodes.append(xml)

    # ========== VCOL SPLITS ==========
    vr_n, vr_o, xml = grayconv(vc_n, vc_o, (1, 0, 0, 0), -1300, 480); nodes.append(xml)
    vg_n, vg_o, xml = grayconv(vc_n, vc_o, (0, 1, 0, 0), -1300, 560); nodes.append(xml)
    vb_n, vb_o, xml = grayconv(vc_n, vc_o, (0, 0, 1, 0), -1300, 640); nodes.append(xml)
    va_n, va_o, xml = grayconv(vc_n, vc_o, (0, 0, 0, 1), -1300, 720); nodes.append(xml)

    # ========== COLOR UNIFORMS ==========
    u_pri_n, u_pri_o, xml = uniform_color_from_param("PrimaryColor", -1000, 0); nodes.append(xml)
    u_sec_n, u_sec_o, xml = uniform_color_from_param("SecondaryColor", -1000, 120); nodes.append(xml)
    u_acc_n, u_acc_o, xml = uniform_color_from_param("AccentColor", -1000, 240); nodes.append(xml)
    u_sh_n, u_sh_o, xml = uniform_color_from_param("ShadowColor", -1000, 360); nodes.append(xml)

    # ========== MASKS ==========
    # Wear = AO × vcol.R, then levels shaped by ShadowSpread
    wear0_n, wear0_o, xml = blend(ao_n, ao_o, vr_n, vr_o, mode=3, x=-1000, y=480,
                                   opacity=1.0, gray=True)
    nodes.append(xml)
    wear_n, wear_o, xml = levels_mid(wear0_n, wear0_o, -760, 480, mid_param="ShadowSpread")
    nodes.append(xml)

    # Decoration = Curvature × vcol.G, shaped by CurvatureOpacity mid
    deco0_n, deco0_o, xml = blend(cv_n, cv_o, vg_n, vg_o, mode=3, x=-1000, y=640,
                                   opacity=1.0, gray=True)
    nodes.append(xml)
    deco_n, deco_o, xml = levels_mid(deco0_n, deco0_o, -760, 640, mid=0.45,
                                     in_low=0.15, in_high=0.95)
    nodes.append(xml)
    deco_sh_n, deco_sh_o, xml = sharpen(deco_n, deco_o, 0.35, -520, 640)
    nodes.append(xml)

    # Beat mask = vcol.B levels (kept clean for stage makeup)
    beat_lvl_n, beat_lvl_o, xml = levels_mid(vb_n, vb_o, -1000, 800, mid=0.5,
                                              in_low=0.05, in_high=0.9)
    nodes.append(xml)

    # ========== CYMATICS (moonglow embroidery, not HUD) ==========
    # Seed edges from curvature (soft threshold) → distance rings → warp fracture
    cym_seed_n, cym_seed_o, xml = levels_mid(cv_n, cv_o, -1000, 1100, mid=0.62,
                                              in_low=0.35, in_high=0.85)
    nodes.append(xml)
    cym_seed2_n, cym_seed2_o, xml = sharpen(cym_seed_n, cym_seed_o, 0.4, -760, 1100)
    nodes.append(xml)
    # Moonglow embroidery seeds: gaussian spots + soft disk shape (sacred geometry, not HUD)
    gauss_n, gauss_o, xml = instance_node(
        "pkg:///gaussian_spots_1?dependency=1298547731", "Few_Gauss", -760, 980,
        params_xml="""              <parameter><name v="outputsize"/><relativeTo v="1"/><paramValue><constantValueInt2 v="0 0"/></paramValue></parameter>""")
    nodes.append(xml)
    shape_n, shape_o, xml = instance_node(
        "pkg:///shape?dependency=1290776979", "Simple_Shape", -520, 980,
        params_xml="""              <parameter><name v="Pattern"/><relativeTo v="0"/><paramValue><constantValueInt32 v="1"/></paramValue></parameter>
              <parameter><name v="Tiling"/><relativeTo v="0"/><paramValue><constantValueInt32 v="3"/></paramValue></parameter>""")
    nodes.append(xml)
    # Fuse spots × shape → soft ring seeds
    cym_spots_n, cym_spots_o, xml = blend(gauss_n, gauss_o, shape_n, shape_o, mode=3, x=-280, y=980,
                                           opacity=0.65, gray=True)
    nodes.append(xml)
    # Histogram scan on curvature for clean edge embroidery mask
    hist_n, hist_o, xml = instance_node(
        "pkg:///histogram_scan?dependency=1149349207", "Output", -760, 1280,
        connections=[("Input_1", cv_n, cv_o)],
        params_xml="""              <parameter><name v="Position"/><relativeTo v="0"/><paramValue><constantValueFloat1 v="0.55"/></paramValue></parameter>
              <parameter><name v="Contrast"/><relativeTo v="0"/><paramValue><constantValueFloat1 v="0.35"/></paramValue></parameter>""")
    nodes.append(xml)
    cym_seed3_n, cym_seed3_o, xml = blend(cym_seed2_n, cym_seed2_o, cym_spots_n, cym_spots_o, mode=1,
                                           x=-40, y=1100, opacity=0.55, gray=True)
    nodes.append(xml)
    cym_seed4_n, cym_seed4_o, xml = blend(cym_seed3_n, cym_seed3_o, hist_n, hist_o, mode=1,
                                           x=160, y=1100, opacity=0.4, gray=True)
    nodes.append(xml)
    # Distance creates soft concentric falloff from edge seeds
    cym_dist_n, cym_dist_o, xml = distance_filter(cym_seed4_n, cym_seed4_o, 48.0, 400, 1100)
    nodes.append(xml)
    # Ring bands via levels (invert-ish mid push)
    cym_ring_n, cym_ring_o, xml = levels_mid(cym_dist_n, cym_dist_o, -280, 1100, mid=0.4,
                                              in_low=0.1, in_high=0.75)
    nodes.append(xml)
    # Fracture warp using curvature as gradient
    cym_warp_n, cym_warp_o, xml = warp(cym_ring_n, cym_ring_o, cv_n, cv_o, 12.0, -40, 1100)
    nodes.append(xml)
    # Directional swirl for sacred-geometry stitch feel
    cym_dir_n, cym_dir_o, xml = directional_warp(cym_warp_n, cym_warp_o, cym_ring_n, cym_ring_o,
                                                  8.0, 35.0, 200, 1100)
    nodes.append(xml)
    cym_blur_n, cym_blur_o, xml = blur(cym_dir_n, cym_dir_o, 0.35, 440, 1100)
    nodes.append(xml)
    # Mix procedural rings with optional FrozenFracture Height (bitmap input)
    cym_bm_n, cym_bm_o, xml = blend(cym_blur_n, cym_blur_o, ch_n, ch_o, mode=1, x=680, y=1100,
                                     opacity=0.7, mask_n=co_n, mask_o=co_o, gray=True)
    nodes.append(xml)
    # Intensity gate — CymaticIntensity knob (0 = silent, hero = full)
    u_cym0_n, u_cym0_o, xml = uniform_const((0.0, 0.0, 0.0, 1), True, 680, 1220)
    nodes.append(xml)
    cym_n, cym_o, xml = blend(u_cym0_n, u_cym0_o, cym_bm_n, cym_bm_o, mode=0, x=920, y=1100,
                               opacity=1.0, opacity_param="CymaticIntensity", gray=True)
    nodes.append(xml)
    # Beat-boosted cymatic for emissive / mask (× vcol.B)
    cym_beat_n, cym_beat_o, xml = blend(cym_n, cym_o, vb_n, vb_o, mode=3, x=1160, y=1100,
                                         opacity=1.0, opacity_param="BeatBoost", gray=True)
    nodes.append(xml)
    # Mask_Cymatic = procedural×opacity seed × beat whisper
    cym_mask_n, cym_mask_o, xml = blend(cym_n, cym_o, co_n, co_o, mode=3, x=1160, y=1220,
                                         opacity=0.85, gray=True)
    nodes.append(xml)
    cym_mask2_n, cym_mask2_o, xml = blend(cym_mask_n, cym_mask_o, beat_lvl_n, beat_lvl_o,
                                           mode=3, x=1400, y=1220, opacity=0.6, gray=True)
    nodes.append(xml)

    # ========== COLOR STACK (fashion-readable) ==========
    # 1) Primary × Shadow under wear (AO·R shaped by ShadowSpread)
    b1_n, b1_o, xml = blend(u_pri_n, u_pri_o, u_sh_n, u_sh_o, mode=3, x=-400, y=0,
                            opacity=0.9, mask_n=wear_n, mask_o=wear_o, gray=False)
    nodes.append(xml)
    # 2) SoftLight Secondary wash (cedar) lightly overall
    b2_n, b2_o, xml = blend(b1_n, b1_o, u_sec_n, u_sec_o, mode=11, x=-150, y=0,
                            opacity=0.18, gray=False)
    nodes.append(xml)
    # 3) Overlay Secondary on curvature×G decoration (embroidery lane)
    b3_n, b3_o, xml = blend(b2_n, b2_o, u_sec_n, u_sec_o, mode=9, x=100, y=0,
                            opacity=1.0, mask_n=deco_sh_n, mask_o=deco_sh_o,
                            opacity_param="CurvatureOpacity", gray=False)
    nodes.append(xml)
    # 4) Accent rim — Copy glow on sharpened decoration edges + light cymatic kiss
    rim_mask_n, rim_mask_o, xml = blend(deco_sh_n, deco_sh_o, cym_n, cym_o, mode=1, x=100, y=160,
                                         opacity=0.35, gray=True)
    nodes.append(xml)
    b4_n, b4_o, xml = blend(b3_n, b3_o, u_acc_n, u_acc_o, mode=0, x=350, y=0,
                            opacity=0.5, mask_n=rim_mask_n, mask_o=rim_mask_o, gray=False)
    nodes.append(xml)
    # 5) Stroke overlay — Multiply secondary through BrushStrokeMap × BrushStrokeIntensity
    b5_n, b5_o, xml = blend(b4_n, b4_o, u_sec_n, u_sec_o, mode=3, x=600, y=0,
                            opacity=1.0, mask_n=br_n, mask_o=br_o,
                            opacity_param="BrushStrokeIntensity", gray=False)
    nodes.append(xml)
    # 6) Soft post Overlay primary lightly (Nikki polish — keeps paper clean)
    b6_n, b6_o, xml = blend(b5_n, b5_o, u_pri_n, u_pri_o, mode=9, x=850, y=0,
                            opacity=0.12, gray=False)
    nodes.append(xml)
    # 7) SoftLight Accent whisper for glow readability at thumbnail
    b7_n, b7_o, xml = blend(b6_n, b6_o, u_acc_n, u_acc_o, mode=11, x=1100, y=0,
                            opacity=0.08, gray=False)
    nodes.append(xml)

    # ========== GOUACHE HEIGHT → NORMAL ==========
    # Curvature shaped by GouacheDepth mid → add stroke breakup → blur → NFH
    gou_lvl_n, gou_lvl_o, xml = levels_mid(cv_n, cv_o, -400, 800, mid_param="GouacheDepth",
                                            in_low=0.1, in_high=0.9)
    nodes.append(xml)
    # Optional stroke as fine height breakup
    gou_stroke_n, gou_stroke_o, xml = blend(gou_lvl_n, gou_lvl_o, br_n, br_o, mode=1, x=-150, y=800,
                                             opacity=1.0, opacity_param="BrushStrokeIntensity",
                                             gray=True)
    nodes.append(xml)
    # Add moonglow cymatic into height (embroidery relief)
    gou_h_n, gou_h_o, xml = blend(gou_stroke_n, gou_stroke_o, cym_n, cym_o, mode=1, x=100, y=800,
                                   opacity=0.55, gray=True)
    nodes.append(xml)
    # Soft blur — brushed gouache / soft impasto, never photo pores
    gou_blur_n, gou_blur_o, xml = blur(gou_h_n, gou_h_o, 0.55, 350, 800)
    nodes.append(xml)
    gou_blur2_n, gou_blur2_o, xml = blur(gou_blur_n, gou_blur_o, 0.25, 550, 800)
    nodes.append(xml)
    # HQ blur for soft porcelain/gouache (Nikki hand-finish)
    gou_hq_n, gou_hq_o, xml = instance_node(
        "pkg:///blur_hq_grayscale?dependency=1299236171", "Blur_HQ", 700, 720,
        connections=[("Source", gou_blur2_n, gou_blur2_o)],
        params_xml="""              <parameter><name v="Intensity"/><relativeTo v="0"/><paramValue><constantValueFloat1 v="0.45"/></paramValue></parameter>""")
    nodes.append(xml)
    # Light sharpen pass so edges still catch light
    gou_fin_n, gou_fin_o, xml = sharpen(gou_hq_n, gou_hq_o, 0.2, 900, 800)
    nodes.append(xml)
    # Normal From Height
    nrm_n, nrm_o, xml = normal_from_height(gou_fin_n, gou_fin_o, "NormalStrength", 1000, 800)
    nodes.append(xml)
    # Light combine with WorldNormal if present (Overlay low)
    nrm2_n, nrm2_o, xml = blend(nrm_n, nrm_o, wn_n, wn_o, mode=9, x=1250, y=800,
                                 opacity=0.2, gray=False)
    nodes.append(xml)

    # Height output = gouache height (curv + stroke + cymatic)
    height_n, height_o = gou_fin_n, gou_fin_o

    # ========== ROUGHNESS (band + wear lift, no grit soup) ==========
    u_rmin_n, u_rmin_o, xml = uniform_const((0.35, 0.35, 0.35, 1), True, -400, 1400)
    nodes.append(xml)
    # Drive min/max via levels isn't direct for uniforms; blend rmin→rmax by wear
    u_rmax_n, u_rmax_o, xml = uniform_const((0.72, 0.72, 0.72, 1), True, -400, 1480)
    nodes.append(xml)
    # Shape wear for roughness lift
    rgh_mask_n, rgh_mask_o, xml = levels_mid(wear_n, wear_o, -150, 1400, mid=0.5)
    nodes.append(xml)
    rgh0_n, rgh0_o, xml = blend(u_rmin_n, u_rmin_o, u_rmax_n, u_rmax_o, mode=0, x=100, y=1400,
                                 opacity=0.75, mask_n=rgh_mask_n, mask_o=rgh_mask_o, gray=True)
    nodes.append(xml)
    # Slight soften so roughness isn't noisy
    rgh_n, rgh_o, xml = blur(rgh0_n, rgh0_o, 0.4, 350, 1400)
    nodes.append(xml)

    # ========== METALLIC (jewelry kisses × cymatic) ==========
    u_met_n, u_met_o, xml = uniform_const((0.12, 0.12, 0.12, 1), True, -400, 1600)
    nodes.append(xml)
    u_m0_n, u_m0_o, xml = uniform_const((0.0, 0.0, 0.0, 1), True, -400, 1680)
    nodes.append(xml)
    met_mask_n, met_mask_o, xml = blend(cym_mask2_n, cym_mask2_o, deco_sh_n, deco_sh_o,
                                         mode=3, x=-150, y=1600, opacity=0.7, gray=True)
    nodes.append(xml)
    met_n, met_o, xml = blend(u_m0_n, u_m0_o, u_met_n, u_met_o, mode=0, x=100, y=1600,
                               opacity=1.0, mask_n=met_mask_n, mask_o=met_mask_o,
                               opacity_param="MetallicAccent", gray=True)
    nodes.append(xml)

    # ========== EMISSIVE (stage makeup — Accent × A · BeatBoost×B · cymatic whisper) ==========
    em_zone_n, em_zone_o, xml = blend(va_n, va_o, cym_beat_n, cym_beat_o, mode=1, x=-400, y=1800,
                                       opacity=0.55, gray=True)
    nodes.append(xml)
    em_zone2_n, em_zone2_o, xml = blend(em_zone_n, em_zone_o, beat_lvl_n, beat_lvl_o, mode=3,
                                         x=-150, y=1800, opacity=1.0, opacity_param="BeatBoost",
                                         gray=True)
    nodes.append(xml)
    u_em0_n, u_em0_o, xml = uniform_const((0, 0, 0, 1), False, -400, 1900)
    nodes.append(xml)
    em_n, em_o, xml = blend(u_em0_n, u_em0_o, u_acc_n, u_acc_o, mode=0, x=100, y=1800,
                            opacity=0.85, mask_n=em_zone2_n, mask_o=em_zone2_o, gray=False)
    nodes.append(xml)
    # SoftLight self so glow doesn't crush albedo when composited
    em2_n, em2_o, xml = blend(em_n, em_o, u_acc_n, u_acc_o, mode=11, x=350, y=1800,
                               opacity=0.25, gray=False)
    nodes.append(xml)

    # ========== OPACITY ==========
    # Default opaque; open slightly where heavy cymatic hero (optional glass charms)
    u_op_n, u_op_o, xml = uniform_const((1, 1, 1, 1), True, -400, 2000)
    nodes.append(xml)
    u_op_open_n, u_op_open_o, xml = uniform_const((0.92, 0.92, 0.92, 1), True, -400, 2080)
    nodes.append(xml)
    op_n, op_o, xml = blend(u_op_n, u_op_o, u_op_open_n, u_op_open_o, mode=0, x=100, y=2000,
                             opacity=0.15, mask_n=cym_n, mask_o=cym_o, gray=True)
    nodes.append(xml)

    # ========== ORM pack R=AO G=Rough B=Metal ==========
    u_r_n, u_r_o, xml = uniform_const((1, 0, 0, 1), False, 600, 1400); nodes.append(xml)
    u_g_n, u_g_o, xml = uniform_const((0, 1, 0, 1), False, 600, 1480); nodes.append(xml)
    u_b_n, u_b_o, xml = uniform_const((0, 0, 1, 1), False, 600, 1560); nodes.append(xml)
    orm0_n, orm0_o, xml = uniform_const((0, 0, 0, 1), False, 600, 1320); nodes.append(xml)
    orm1_n, orm1_o, xml = blend(orm0_n, orm0_o, u_r_n, u_r_o, mode=1, x=850, y=1320,
                                 opacity=1.0, mask_n=ao_n, mask_o=ao_o)
    nodes.append(xml)
    orm2_n, orm2_o, xml = blend(orm1_n, orm1_o, u_g_n, u_g_o, mode=1, x=1100, y=1320,
                                 opacity=1.0, mask_n=rgh_n, mask_o=rgh_o)
    nodes.append(xml)
    orm3_n, orm3_o, xml = blend(orm2_n, orm2_o, u_b_n, u_b_o, mode=1, x=1350, y=1320,
                                 opacity=1.0, mask_n=met_n, mask_o=met_o)
    nodes.append(xml)

    # ========== OUTPUT BRIDGES ==========
    ox = 1700
    for ident, src_n, src_o, yy in [
        ("BaseColor", b7_n, b7_o, 0),
        ("Normal", nrm2_n, nrm2_o, 160),
        ("Roughness", rgh_n, rgh_o, 320),
        ("Metallic", met_n, met_o, 480),
        ("Height", height_n, height_o, 640),
        ("Emissive", em2_n, em2_o, 800),
        ("Opacity", op_n, op_o, 960),
        ("Mask_Wear", wear_n, wear_o, 1120),
        ("Mask_Decoration", deco_sh_n, deco_sh_o, 1280),
        ("Mask_Beat", beat_lvl_n, beat_lvl_o, 1440),
        ("Mask_Cymatic", cym_mask2_n, cym_mask2_o, 1600),
        ("ORM", orm3_n, orm3_o, 1760),
    ]:
        _, xml = output_bridge(outs[ident], src_n, src_o, ox, yy)
        nodes.append(xml)

    root_outs = "\n".join(
        f'        <rootOutput><output v="{outs[k]}"/><format v="0"/><usertag v=""/></rootOutput>'
        for k in outs
    )

    xml_doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<package>
  <identifier v="SBS_Melusina_SimpleDiffuse"/>
  <formatVersion v="1.1.0.202202"/>
  <updaterVersion v="1.1.0.202202"/>
  <fileUID v="{file_uid}"/>
  <versionUID v="0"/>
  <dependencies>
    <dependency>
      <filename v="sbs://functions.sbs"/>
      <uid v="1290776887"/>
      <type v="package"/>
      <fileUID v="0"/>
      <versionUID v="0"/>
    </dependency>
    <dependency>
      <filename v="sbs://blur_hq.sbs"/>
      <uid v="1299236171"/>
      <type v="package"/>
      <fileUID v="0"/>
      <versionUID v="0"/>
    </dependency>
    <dependency>
      <filename v="sbs://histogram_scan.sbs"/>
      <uid v="1149349207"/>
      <type v="package"/>
      <fileUID v="0"/>
      <versionUID v="0"/>
    </dependency>
    <dependency>
      <filename v="sbs://gaussian_spots_1.sbs"/>
      <uid v="1298547731"/>
      <type v="package"/>
      <fileUID v="0"/>
      <versionUID v="0"/>
    </dependency>
    <dependency>
      <filename v="sbs://shape.sbs"/>
      <uid v="1290776979"/>
      <type v="package"/>
      <fileUID v="0"/>
      <versionUID v="0"/>
    </dependency>
  </dependencies>
  <content>
    <graph>
      <identifier v="Melusina_SimpleDiffuse"/>
      <uid v="{graph_uid}"/>
      <attributes>
        <category v="Melodia/Melusina"/>
        <label v="Melusina Simple Diffuse"/>
        <author v="Melodia"/>
        <tags v="Melusina,Melodia,Handpaint,Cymatic,Gouache,NPR,InfinityNikkiBar"/>
        <description v="Melodia M1 Nikki-bar Simple Diffuse: fashion color stack, gouache normals from curvature, moonglow cymatics, vcol_melodia masks, beat emissive. Pair with SMS_Melusina_Handpaint. Not a Nhance clone."/>
      </attributes>
      <paraminputs>
{"".join(chunks_pi)}
      </paraminputs>
      <graphOutputs>
{"".join(chunks_go)}
      </graphOutputs>
      <compNodes>
{"".join(nodes)}
      </compNodes>
      <baseParameters/>
      <options>
        <option><name v="defaultParentSize"/><value v="9x9"/></option>
      </options>
      <root>
        <rootOutputs>
{root_outs}
        </rootOutputs>
      </root>
    </graph>
  </content>
</package>
"""
    return xml_doc


def try_cook(sbs_path: Path) -> Path | None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    if not SBSCOOKER.is_file():
        print("[cook] sbscooker not found:", SBSCOOKER)
        return None
    cmd = [
        str(SBSCOOKER),
        "--inputs", str(sbs_path),
        "--output-path", str(EXPORTS),
        "--output-name", "{inputName}",
        "--verbose",
    ]
    print("[cook]", " ".join(cmd))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:
        print("[cook] failed to launch:", e)
        return None
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    print("[cook] exit", r.returncode)
    for p in [
        EXPORTS / "SBS_Melusina_SimpleDiffuse.sbsar",
        EXPORTS / "Melusina_SimpleDiffuse.sbsar",
        sbs_path.with_suffix(".sbsar"),
    ]:
        if p.is_file():
            return p
    candidates = list(EXPORTS.glob("*.sbsar"))
    return candidates[0] if candidates else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cook", action="store_true", help="Run sbscooker after write")
    ap.add_argument("--out", type=Path, default=OUT_SBS)
    args = ap.parse_args()
    doc = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc, encoding="utf-8")
    print("[write]", args.out, "bytes", args.out.stat().st_size)
    cooked = None
    if args.cook:
        cooked = try_cook(args.out)
        print("[cook-result]", cooked)
        if cooked and cooked.is_file():
            print("[cook-size]", cooked.stat().st_size)
    return 0 if args.out.is_file() else 1


if __name__ == "__main__":
    raise SystemExit(main())
