"""Create a data-only chapter using the existing runtime allowlist asset."""
import argparse
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Content.Python.Tests.test_qsc_allowlist_contract import CONFIG_ASSET, NOTIFY_RE, _gated_ids


def scaffold(chapter, root=ROOT):
    if not re.fullmatch(r"[0-9]{2}_[a-z][a-z0-9_]*", chapter):
        raise ValueError("Chapter must be NN_lowercase_slug")
    target = root / "Chapters" / chapter
    if target.exists():
        raise FileExistsError(f"Chapter already exists: {target}")
    asset = root / CONFIG_ASSET.relative_to(ROOT)
    data = asset.read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError("Hydrate DA_MelodiaIntegrationConfig with git lfs pull first")
    pending = []
    for source in sorted((root / "Chapters/_template").rglob("*")):
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8").replace("{{chapter}}", chapter)
        if source.suffix == ".qsc":
            for notify in NOTIFY_RE.findall(text):
                for kind, ident in _gated_ids(notify):
                    if ident.encode("ascii") not in data:
                        raise ValueError(f"{kind} {ident} absent from runtime allowlist")
        pending.append((target / source.relative_to(root / "Chapters/_template"), text))
    if not pending:
        raise ValueError("Chapter template missing")
    for path, text in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter")
    args = parser.parse_args()
    print(scaffold(args.chapter))
