import os
import json
import glob

def generate_manifests():
    genomes_dir = "deploy/surreal_os/genomes"
    out_dir = "melodia-design-system/public/manifests"
    os.makedirs(out_dir, exist_ok=True)
    
    for g_path in glob.glob(os.path.join(genomes_dir, "*.json")):
        with open(g_path, "r") as f:
            data = json.load(f)
            
        base_name = os.path.basename(g_path).replace(".json", "")
        # Mocking some metrics that might come from blender/pcg
        manifest = {
            "theme": "dark",
            "project": data.get("name", base_name.replace("_", " ").title()),
            "category": "Environment / PCG",
            "version": data.get("version", "v1.0"),
            "rows": [
                ["Triangles", data.get("metrics", {}).get("triangles", "TBD")],
                ["Textures", "TBD"],
                ["Materials", "TBD"],
                ["Software", "Unreal Engine + PCG"],
                ["Engine", "Unreal Engine 5.8"],
                ["Date", "2026-07"]
            ]
        }
        
        out_path = os.path.join(out_dir, f"{base_name}_manifest.json")
        with open(out_path, "w") as out_f:
            json.dump(manifest, out_f, indent=2)
            
    print(f"Generated manifests in {out_dir}")

if __name__ == "__main__":
    generate_manifests()
