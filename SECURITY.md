# Security Policy

## Supported versions

Only the latest release on the `main` branch is supported with security fixes.

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please do **not** open a public issue for security vulnerabilities. Instead,
report them privately to `3558918010@qq.com`.

Include:

- affected version,
- a short description of the issue,
- steps to reproduce,
- potential impact.

We will acknowledge your report within 7 days and aim to publish a fix within
90 days. We prefer coordinated disclosure and will credit reporters unless they
ask to remain anonymous.

## Scope

- Arbitrary file reads/writes through model paths or preset paths
- Command injection through CLI arguments or HuggingFace repository identifiers
- Memory-safety or deserialization issues in vendored code

Model weights downloaded from HuggingFace are untrusted input. VIvoice opens
them only through the libraries documented in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); report any deserialization
vector you find.
