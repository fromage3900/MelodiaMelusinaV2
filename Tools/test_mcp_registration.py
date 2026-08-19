try:
    from Tools.validate_mcp_registration import validate
except ModuleNotFoundError:
    # Direct script execution is the CI contract runner's mode; pytest/module
    # execution keeps the package-qualified import when available.
    from validate_mcp_registration import validate


def test_checked_in_mcp_registration_is_policy_covered():
    result = validate()
    assert result["status"] == "pass", result
    assert result["checks"]["agent_bridge_registered_in_session"]
    assert result["checks"]["agent_bridge_registered_in_jcode"]
    assert result["checks"]["every_bridge_tool_has_policy_entry"]


def main() -> int:
    """Run without pytest so CI cannot silently skip this contract."""
    test_checked_in_mcp_registration_is_policy_covered()
    print("validated checked-in MCP registration policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
