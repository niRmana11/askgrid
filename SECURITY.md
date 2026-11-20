# Security Policy

## Core Security Principles
AskGrid is designed with a security- and privacy-first architecture:
- **No arbitrary code execution:** LLMs never generate or execute code on the server.
- **Deterministic math:** All calculations run via allowlisted Python/Pandas operations.
- **Schema-only AI prompts:** Dataset row values are never sent to external LLM providers.
- **Ephemeral sessions (MVP-0):** Uploaded CSVs are deleted on request or upon session expiry.

## Reporting a Vulnerability
If you discover a security vulnerability, **please do not open a public GitHub issue**.
Instead, report it privately via GitHub's **Security → Advisories → Report a vulnerability** tab (or contact the maintainer directly via GitHub profile).

We aim to acknowledge reports within 72 hours.