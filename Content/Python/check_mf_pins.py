"""Inspect MF pin names in the universal master graph JSON."""
import json, re, sys

GRAPH = r"Saved/Audit/m_master_toon_universal_graph.json"


def main():
    with open(GRAPH, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    for node in data.get("nodes", []):
        cls = node.get("class", "")
        if "FunctionCall" in cls:
            props = node.get("props", {})
            fn = props.get("MaterialFunction", "")
            inputs = props.get("FunctionInputs", "")
            outputs = props.get("FunctionOutputs", "")
            fn_name = fn.split("/")[-1].split(".")[0] if fn else "unknown"
            pin_names = re.findall(r'InputName=\\\\?"([^"\\\\]+)\\\\?"', inputs)
            output_names = re.findall(r'OutputName=\\\\?"([^"\\\\]+)\\\\?"', outputs)
            nid = node.get("id", "")
            print(f"{nid}: {fn_name}")
            print(f"  Inputs: {pin_names}")
            print(f"  Outputs: {output_names}")


if __name__ == "__main__":
    sys.exit(main())
