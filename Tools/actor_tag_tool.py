import argparse
import json
import sys
import urllib.request
import urllib.error

MONOLITH_URL = "http://localhost:9316"


def send_to_monolith(command: str) -> dict:
    payload = json.dumps({"action": "run_python", "command": command}).encode("utf-8")
    req = urllib.request.Request(
        MONOLITH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Error connecting to Monolith at {MONOLITH_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse Monolith response: {e}", file=sys.stderr)
        sys.exit(1)


def build_python_code(args) -> str:
    lines = []
    lines.append("import unreal")

    actor_class = args.actor_class
    tag = args.tag
    level_arg = args.level
    remove_tag = args.remove_tag

    # Wrap class name in quotes, strip BP_ prefix to find the actual Blueprint class
    # In UE Python, you access blueprint classes via unreal.EditorAssetLibrary or
    # by using the string path. The most reliable way for blueprint classes
    # like BP_InteractionBattle_C is via unreal.load_object or unreal.find_object.
    # However, get_all_objects_of_class needs a class object, not a string.
    # We'll use the SystemLibrary approach: find all actors, filter by class name.

    if level_arg:
        lines.append(f"level_path = {repr(level_arg)}")
    lines.append(f"tag_name = {repr(tag)}")

    if remove_tag:
        lines.append(f"remove_tag_name = {repr(remove_tag)}")

    lines.append(f"target_class_name = {repr(actor_class)}")
    lines.append("")

    lines.append("# Load the level if specified")
    if level_arg:
        lines.append(
            'editor_subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)'
        )
        lines.append('if not editor_subsys:')
        lines.append('    print("ERROR: Could not get EditorActorSubsystem")')
        lines.append(
            '    raise Exception("EditorActorSubsystem not available")'
        )
        lines.append('loaded = editor_subsys.load_level(level_path)')
        lines.append('if not loaded:')
        lines.append(
            '    print(f"ERROR: Failed to load level: {level_path}")'
        )
        lines.append(
            '    raise Exception(f"Could not load level {level_path}")'
        )
        lines.append('print(f"Loaded level: {level_path}")')
        lines.append('')

    lines.append(
        "# Get all actors in the current world and filter by class name"
    )
    lines.append(
        "editor_subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)"
    )
    lines.append("all_actors = editor_subsys.get_all_level_actors()")
    lines.append("")
    lines.append("matched = []")
    lines.append("for actor in all_actors:")
    lines.append(
        "    cls_name = actor.get_class().get_name()"
    )
    lines.append(
        "    if cls_name == target_class_name:"
    )
    lines.append("        matched.append(actor)")
    lines.append("")
    lines.append(
        f'print(f"Found {{len(matched)}} actors of class {{target_class_name}}")'
    )
    lines.append("")

    if remove_tag:
        lines.append(f"# Remove the specified tag")
        lines.append("for actor in matched:")
        lines.append(
            "    if remove_tag_name in actor.actor_tags:"
        )
        lines.append(
            "        actor.actor_tags.remove(remove_tag_name)"
        )
        lines.append(
            f'        print(f"Removed tag \\\"{{remove_tag_name}}\\\" from: {{actor.get_name()}}")'
        )
        lines.append("    else:")
        lines.append(
            f'        print(f"Actor {{actor.get_name()}} does not have tag \\\"{{remove_tag_name}}\\\"")'
        )
        lines.append("")

    if tag:
        lines.append(f"# Add the specified tag")
        lines.append("for actor in matched:")
        lines.append(
            "    if tag_name not in actor.actor_tags:"
        )
        lines.append(
            "        actor.actor_tags.append(tag_name)"
        )
        lines.append(
            f'        print(f"Tagged: {{actor.get_name()}}")'
        )
        lines.append("    else:")
        lines.append(
            f'        print(f"Actor {{actor.get_name()}} already has tag \\\"{{tag_name}}\\"")'
        )
        lines.append("")

    lines.append("# Save the current level")
    lines.append("saved = editor_subsys.save_current_level()")
    lines.append("if saved:")
    lines.append('    print("Level saved successfully")')
    lines.append("else:")
    lines.append('    print("ERROR: Failed to save level")')

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Tag actors in UE levels via Monolith"
    )
    parser.add_argument(
        "--level", type=str, default=None, help="Level path to load (e.g. /Game/Maps/MyMap)"
    )
    parser.add_argument(
        "--class",
        dest="actor_class",
        type=str,
        required=True,
        help="Actor class name to filter (e.g. BP_InteractionBattle_C)",
    )
    parser.add_argument(
        "--tag", type=str, required=True, help="Tag to add to matched actors"
    )
    parser.add_argument(
        "--remove-tag",
        type=str,
        default=None,
        help="Optional tag to remove from matched actors",
    )

    parsed = parser.parse_args()
    code = build_python_code(parsed)

    print("Sending to Monolith...")
    result = send_to_monolith(code)

    if "result" in result:
        print(result["result"])
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
