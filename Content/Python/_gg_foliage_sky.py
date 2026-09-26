"""Generate PCG foliage on Glassgarden SeaAbove-style volumes + tune UDS/UDW serene tropical day."""
import unreal, json, time

LEVEL = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/LV_Glassgarden_Shoals"
PCG_LABELS = [
    "Glassgarden_PCG_PCG_SeaAbove_East_Scree",
    "Glassgarden_PCG_PCG_SeaAbove_East_TerraceGarden",
    "Glassgarden_PCG_PCG_SeaAbove_East_PhyllotaxisBiome",
    "Glassgarden_PCG_PCG_SeaAbove_BellTreeGarden",
]
# Calm tropical / serene reef shoals — soft late morning, light haze, low cloud
UDS_TUNES = [
    ("Animate Time of Day", False),
    ("Time of Day", 1030.0),          # soft morning ~10:30
    ("Cloud Coverage", 1.6),          # light fair-weather clouds
    ("Cloud Softness", 0.65),
    ("Sun Light Intensity", 3.8),     # soft, not harsh noon
    ("Overall Intensity", 1.05),
    ("Sky Ambient Intensity", 0.55),
    ("Height Fog Density", 0.012),
    ("Fog Density", 0.012),
    ("Directional Light Intensity", 3.8),
]
UDW_TUNES = [
    ("Weather", 0.0),                 # clear if numeric enum/index
    ("Rain", 0.0),
    ("Thunder/Lightning", False),
    ("Cloud Coverage", 1.6),
    ("Wind Intensity", 0.15),
    ("Enable Fog", True),
]

out = {"steps": {}}

def editor_world():
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            w = ues.get_editor_world()
            if w:
                return w
    except Exception:
        pass
    return unreal.EditorLevelLibrary.get_editor_world()

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = editor_world()
cur = w.get_path_name().split(".")[0] if w else None
if cur != LEVEL:
    out["steps"]["load"] = {"ok": bool(les.load_level(LEVEL)), "from": cur}
else:
    out["steps"]["load"] = {"ok": True, "already": cur}

def by_label():
    return {a.get_actor_label(): a for a in (eas.get_all_level_actors() or [])}

actors = by_label()

# --- Sky tune ---
sky = {"uds": {}, "udw": {}}
uds = actors.get("Glassgarden_UDS")
udw = actors.get("Glassgarden_UDW")
sky["uds"]["present"] = uds is not None
sky["udw"]["present"] = udw is not None

def apply_tunes(actor, tunes, bucket):
    changed = []
    failed = []
    before = {}
    after = {}
    for key, val in tunes:
        try:
            try:
                before[key] = actor.get_editor_property(key)
            except Exception:
                before[key] = None
            actor.set_editor_property(key, val)
            try:
                after[key] = actor.get_editor_property(key)
            except Exception:
                after[key] = val
            changed.append({"key": key, "from": before[key], "to": after[key]})
        except Exception as e:
            failed.append({"key": key, "value": val, "error": str(e)[:120]})
    bucket["changed"] = changed
    bucket["failed"] = failed
    # Also probe common alternate names if primary Time of Day failed
    return bucket

if uds:
    apply_tunes(uds, UDS_TUNES, sky["uds"])
    # Enumerate a few readable props for evidence
    probed = {}
    for k in ("Time of Day", "Cloud Coverage", "Sun Light Intensity", "Overall Intensity",
              "Animate Time of Day", "Height Fog Density", "Fog Density"):
        try:
            probed[k] = uds.get_editor_property(k)
        except Exception as e:
            probed[k] = f"unreadable:{str(e)[:60]}"
    sky["uds"]["probed"] = probed
if udw:
    apply_tunes(udw, UDW_TUNES, sky["udw"])
    # Try weather-type / state string props
    for alt in (("Current Weather", "Clear"), ("Weather Type", "Clear Skies"),
                ("Active Weather", "Clear"), ("rain_intensity", 0.0), ("snow_intensity", 0.0)):
        try:
            udw.set_editor_property(alt[0], alt[1])
            sky["udw"].setdefault("extra_ok", []).append({"key": alt[0], "to": alt[1]})
        except Exception as e:
            sky["udw"].setdefault("extra_fail", []).append({"key": alt[0], "error": str(e)[:80]})
out["steps"]["sky_tune"] = sky

# Soft fog host density to match
fog = actors.get("Glassgarden_ExponentialHeightFog")
if fog:
    try:
        comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            try:
                comp.set_editor_property("fog_density", 0.015)
            except Exception:
                pass
            try:
                comp.set_editor_property("fog_height_falloff", 0.15)
            except Exception:
                pass
            out["steps"]["fog_tune"] = {"ok": True, "fog_density": 0.015}
    except Exception as e:
        out["steps"]["fog_tune"] = {"error": str(e)[:120]}

# --- PCG foliage generate ---
gen_rows = []
for label in PCG_LABELS:
    vol = actors.get(label)
    row = {"label": label, "present": vol is not None}
    if not vol:
        gen_rows.append(row)
        continue
    comp = vol.get_component_by_class(unreal.PCGComponent)
    row["has_comp"] = comp is not None
    if not comp:
        gen_rows.append(row)
        continue
    # Ensure on-demand / allow generate
    for prop, val in (
        ("generation_trigger", getattr(getattr(unreal, "PCGComponentGenerationTrigger", object), "GENERATE_ON_DEMAND", None)),
        ("activated", True),
        ("generate_on_load", False),
    ):
        if val is None and prop == "generation_trigger":
            continue
        try:
            comp.set_editor_property(prop, val)
        except Exception:
            pass
    notes = []
    try:
        comp.cleanup_local(False)
        notes.append("cleanup_local=ok")
    except Exception as e:
        notes.append("cleanup_local=" + str(e)[:80])
    generated = False
    for attempt in range(3):
        try:
            comp.generate_local(True)
            generated = True
            notes.append(f"generate_local[{attempt}]=ok")
        except Exception as e:
            notes.append(f"generate_local[{attempt}]=" + str(e)[:80])
        try:
            comp.generate(True)
            notes.append(f"generate[{attempt}]=ok")
            generated = True
        except Exception as e:
            notes.append(f"generate[{attempt}]=" + str(e)[:80])
        time.sleep(0.5)
    row["generated"] = generated
    row["notes"] = notes
    # Count ISM / HISM instances under this volume's owned components if any
    instance_total = 0
    ism_comps = 0
    try:
        for c in vol.get_components_by_class(unreal.InstancedStaticMeshComponent) or []:
            ism_comps += 1
            try:
                instance_total += int(c.get_instance_count())
            except Exception:
                pass
        for c in vol.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or []:
            ism_comps += 1
            try:
                instance_total += int(c.get_instance_count())
            except Exception:
                pass
    except Exception as e:
        row["ism_error"] = str(e)[:120]
    row["ism_component_count"] = ism_comps
    row["instance_count"] = instance_total
    gen_rows.append(row)

# Also count level-wide ISM after generate (PCG often parents ISMs on PCGComponent managed actors)
level_ism = {"ism_comps": 0, "hism_comps": 0, "instances": 0, "pcg_managed_actors": 0}
for a in (eas.get_all_level_actors() or []):
    cls = a.get_class().get_name()
    if "PCG" in cls or "Partition" in cls:
        level_ism["pcg_managed_actors"] += 1
    for ccls, key in (
        (unreal.InstancedStaticMeshComponent, "ism_comps"),
        (unreal.HierarchicalInstancedStaticMeshComponent, "hism_comps"),
    ):
        try:
            for c in a.get_components_by_class(ccls) or []:
                level_ism[key] += 1
                try:
                    level_ism["instances"] += int(c.get_instance_count())
                except Exception:
                    pass
        except Exception:
            pass
out["steps"]["foliage_generate"] = {"volumes": gen_rows, "level_ism": level_ism}

# Actor inventory
final = [{"label": a.get_actor_label(), "class": a.get_class().get_name()} for a in (eas.get_all_level_actors() or [])]
out["actors"] = final
out["actor_count"] = len(final)

# Save
out["steps"]["save_current"] = bool(unreal.EditorLevelLibrary.save_current_level())
try:
    unreal.EditorAssetLibrary.save_asset(LEVEL, only_if_is_dirty=False)
except Exception:
    pass
print(json.dumps(out, default=str))
