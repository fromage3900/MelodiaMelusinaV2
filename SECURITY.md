# Security Policy

## Supported Versions

We actively maintain and provide security patches for the following versions of Melodia:

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :x:                |

---

## Reporting a Vulnerability

The Melodia development team takes security seriously. If you discover a security vulnerability, please report it responsibly so that we can address it before public disclosure.

### How to Report

Please **do not report security vulnerabilities via public GitHub issues**.

Instead, please send an email to:
**[melodia-security@brennanshepherd.com](mailto:melodia-security@brennanshepherd.com)**

Please include the following details in your report:
- **Type of issue**: (e.g., buffer overflow, command injection, credential exposure, path traversal)
- **Affected component**: (e.g., `MelodiaCore` C++ subsystem, Model Context Protocol server, daemon scripts)
- **Step-by-step reproduction**: Clear instructions, scripts, or payloads to reproduce the issue
- **Impact**: The potential severity and attack vector
- **Suggested remediation**: Any patches or configuration fixes you recommend (optional)

### Response Timeline

- **Initial Acknowledgment**: Within 48 hours of receiving the report.
- **Assessment & Triage**: Within 5 business days, confirming whether the report is accepted.
- **Resolution & Patching**: We strive to release a security update or mitigation within 14 days of confirmed triage.
- **Public Disclosure**: Coordinated after the fix is published and validated.

---

## Safe Harbor Policy

Activities conducted in good faith under this policy are considered authorized, and we will not pursue legal action against researchers who:
- Make a good faith effort to avoid privacy violations, destruction of data, and interruption of services.
- Provide sufficient time for remediation before disclosing findings publicly.
- Do not exploit the vulnerability beyond what is strictly necessary to establish proof-of-concept.
