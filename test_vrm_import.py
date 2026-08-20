"""Test VRM4U import module loading."""
import sys
from pathlib import Path

# Add the correct paths
bs_godfile = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
sys.path.insert(0, str(bs_godfile / "Content" / "Python"))
sys.path.insert(0, str(bs_godfile / "Content" / "Python" / "gmm"))
sys.path.insert(0, str(bs_godfile / "Content" / "Python" / "gmm" / "npc"))

# Test importing the vrm4u_import module
try:
    from gmm.npc import vrm4u_import
    print("OK VRM4U import module loaded successfully")
    print(f"  Module file: {vrm4u_import.__file__}")
    
    # Test capabilities function
    try:
        caps = vrm4u_import.vrm4u_capabilities()
        print(f"  vrm4u_capabilities() result: ok={caps.get('ok')}, state={caps.get('state')}")
    except Exception as e:
        print(f"  vrm4u_capabilities() error: {type(e).__name__}: {e}")
    
    # Test ensure_vrm4u_available
    try:
        available = vrm4u_import.ensure_vrm4u_available()
        print(f"  ensure_vrm4u_available(): {available}")
    except Exception as e:
        print(f"  ensure_vrm4u_available() error: {type(e).__name__}: {e}")
        
except ImportError as e:
    print(f"XX Failed to import VRM4U module: {e}")
    print("  This is expected when running outside UE Python environment")
    print(f"  sys.path count: {len(sys.path)}")
except Exception as e:
    print(f"XX Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()