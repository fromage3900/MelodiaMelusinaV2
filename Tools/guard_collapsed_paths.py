"""Reject resurrection of paths removed by the owner's documentation collapse."""
import argparse
import subprocess

COLLAPSE = "08a608bc"


def git(*args):
    return subprocess.check_output(["git", *args])


def violations(base, head="HEAD"):
    deleted = set(git("diff", "--no-renames", "--diff-filter=D", "--name-only", "-z",
                      COLLAPSE + "^", COLLAPSE).split(b"\0")) - {b""}
    added = set(git("diff", "--no-renames", "--diff-filter=A", "--name-only", "-z",
                    base, head).split(b"\0")) - {b""}
    return sorted(p.decode("utf-8") for p in deleted & added)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    bad = violations(args.base, args.head)
    print("Collapsed paths re-added:\n" + "\n".join(bad) if bad else "Collapsed-path guard PASS")
    raise SystemExit(bool(bad))
