"""Single closed-editor entry point for the landscape recovery rebuild."""
from __future__ import annotations

import importlib


def main() -> int:
    import rebuild_landscape_safe_fallback as rebuild
    import validate_landscape_safe_fallback as validate

    importlib.reload(rebuild)
    importlib.reload(validate)
    rebuild_result = rebuild.build()
    validate_result = validate.main()
    print(
        "LANDSCAPE_SAFE_RECOVERY_COMPLETE "
        f"master={rebuild_result['master']} validation_exit={validate_result}"
    )
    return validate_result


# UE 5.8's PythonScriptCommandlet executes a file with a non-__main__ module
# name, so an __name__ guard silently skips the recovery.  This file is an
# explicit commandlet entry point; execute it on import instead.
main()
