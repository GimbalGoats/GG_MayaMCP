# Security Policy

## Supported Versions

Security fixes are applied to the latest `main` branch and the most recent
release tag.

## Reporting a Vulnerability

Do not open a public issue for suspected security vulnerabilities.

Use GitHub's private vulnerability reporting flow for this repository if it is
enabled. If private reporting is not available, contact the maintainers through
GitHub without posting exploit details publicly.

Include:

- A short description of the issue
- Affected versions or commit SHAs
- Reproduction steps or a proof of concept
- Any suggested mitigation or workaround

You can expect an initial acknowledgment within 5 business days.

## Scope Notes

This project is a localhost-only MCP server for Autodesk Maya. Security work is
prioritized for issues involving:

- unintended remote exposure
- arbitrary code execution outside the documented opt-in paths
- unsafe path handling or traversal
- secret disclosure in logs or error payloads
