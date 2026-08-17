# Security Policy

## Reporting

Please report suspected vulnerabilities privately to security@ecosystem.network. Do not include secrets or personal data in reports.

## Scope

The active `main` branch is the only supported version. CyberFilm is a hackathon-stage system and must not be used for production media, financial, or rights-management decisions without an independent review.

## Security model

- Credentials are loaded from Google Secret Manager or local untracked environment files.
- Production workloads use Google Cloud workload identity; service-account key files are not supported.
- Agent tools are allowlisted, schema-validated, least-privilege operations.
- Actions with external side effects require explicit approval.
- User-provided content is treated as untrusted data, never as agent instructions.
