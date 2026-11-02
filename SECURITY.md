# Security

This is a bounded local portfolio MVP. It has no server, authentication, telemetry, outbound requests, or credentials. No tool can guarantee absence of vulnerabilities.

Do not file sensitive information in public issues. For a suspected vulnerability, use GitHub's private reporting feature if enabled; otherwise ask the maintainer for a private channel without disclosing the exploit or personal data.

Review performed: input bounds, error behavior, external execution, data exposure, dependencies, CI permissions and pinned actions. No eval, shell interpolation of user input, pickle loading, or dynamically fetched runtime code exists. CI has read-only repository permissions. Shared outputs may contain user-supplied information; review before distributing them.

See docs/VERIFICATION.md for actual checks and limitations.
