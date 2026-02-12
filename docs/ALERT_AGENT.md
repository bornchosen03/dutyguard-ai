# GuardDuty Alert Agent

The Alert Agent monitors tariff data changes and writes an alert payload to:

- `knowledge_base/tariff_alerts.json`

## Run

1) Refresh live tariff snapshot:

- `./scripts/run_scraper.sh`

2) Diff and write alert output:

- `./scripts/run_alerts.sh`

## What it does (current MVP)

- Compares `knowledge_base/live_tariffs.csv` vs `knowledge_base/tariff_history.csv` using SHA-256.
- If the data changed, it updates `tariff_history.csv` to the newest snapshot.
- Writes a JSON alert with a small preview of the current CSV and mitigation recommendations.

## Next upgrades

- Parse duty-rate columns and compute SKU/portfolio-level exposure.
- Client profiles and routing (email/Slack/Jira).
- Change attribution (EO/exemption/ruling references) and audit trail.
