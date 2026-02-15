# DutyGuard-AI Security Guidance

This document summarizes practical, lightweight security measures and deployment recommendations for DutyGuard-AI.

Not all security controls can be fully enforced inside the development repo; many require deployment-time configuration (load balancer, TLS certificates, secrets management, etc.). The repository includes several protective measures, including security headers, upload size/rate limits, and basic input sanitation.

Quick checklist (recommended for production):

- TLS / HTTPS
  - Terminate TLS at a trusted load balancer (Cloud provider LB, Nginx, or Caddy).
  - Set `DUTYGUARD_FORCE_HTTPS=true` in environments where you want the app to redirect HTTP->HTTPS.

- Secrets and environment variables
  - Never commit secrets to Git. Use a secrets manager (AWS Secrets Manager, Vault, Azure Key Vault) or environment variables in CI/CD.
  - Required env vars for email: `DUTYGUARD_NOTIFY_EMAIL_TO`, `DUTYGUARD_SMTP_HOST`, `DUTYGUARD_SMTP_USERNAME`, `DUTYGUARD_SMTP_PASSWORD`.

- Network and access controls
  - Restrict management ports (e.g., 8080) to internal networks and use a reverse proxy for public traffic.
  - Use firewall rules and security groups.

- Upload and abuse protection
  - Backend enforces `DUTYGUARD_MAX_UPLOAD_BYTES` (default 10MB) and `DUTYGUARD_MAX_TOTAL_INTAKE_BYTES` (default 25MB).
  - Upload rate limits are enabled by default; tune `DUTYGUARD_UPLOAD_RATE_MAX` and `DUTYGUARD_UPLOAD_RATE_WINDOW`.

- HTTP security headers
  - The backend sets `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and `Strict-Transport-Security`.

- Input validation
  - The app sanitizes filenames and limits user key characters. Keep validating and normalizing external inputs.

- Authentication & Authorization
  - If you expose admin routes or sensitive APIs, add an authentication layer (OAuth/OpenID Connect, API keys, or JWTs). Consider `python-jose` + JWT for lightweight token auth in FastAPI.

- Logging & monitoring
  - Centralize logs and audit trails. The repo writes simple audit records to `backend/data/audit_trail.jsonl`.
  - Configure monitoring and alerting (Prometheus + Alertmanager, hosted solutions, or cloud provider monitoring).

- Vulnerability management
  - Regularly run `npm audit`, `pip-audit` (or Snyk), and update dependencies.

- WAF and IDS
  - Place a Web Application Firewall (WAF) (Cloud provider WAF, CloudFlare, or ModSecurity) in front of the app for additional protection.

- Backups and data retention
  - Back up `backend/data` regularly and secure backups.

If you want, I can:
- Add JWT-based admin auth and a small admin route to manage review tickets.
- Add integration scripts for automated dependency scanning (e.g., a simple GitHub Action for `npm audit` and `pip-audit`).
- Harden CSP further and remove `unsafe-inline` usage, which requires migrating inline scripts/styles.

Contact me which of these you want implemented next and I'll proceed.