"""fromage-side runner: python ue_v4_run.py probe|import|materials|level|assemble|capture
Sends ONE editor run_python via the verified Monolith client (unique JSON-RPC ids)."""
import sys
sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Tools\Audio")
from monolith_client import MonolithClient
S = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\scripts"
stage = sys.argv[1]
mc = MonolithClient(timeout=900)
if stage == "probe":
    src = 'exec(open(r"%s\\ue_v4_probe_readonly.py").read())' % S
else:
    src = 'STAGE = "%s"\nexec(open(r"%s\\ue_v4_build_write.py").read())' % (stage, S)
print(mc.run_python(src, timeout=900)[:4000])
