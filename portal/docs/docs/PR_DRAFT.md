PR draft: feat/import-htsdata

Summary

This branch imports user-provided HTS data (CSV + PDF) and adds an import helper:

- `knowledge_base/htsdata.csv` — imported CSV (481 rows).
- `scripts/import_htsdata.py` — normalizes `htsdata.csv` to `knowledge_base/live_tariffs.csv` and runs change detection.
- `knowledge_base/live_tariffs.csv` updated; `knowledge_base/tariff_alerts.json` indicates a change.
- `knowledge_base/imported_files.json` updated with checksums.
- Large PDF `finalCopy_2026HTSRev3.pdf` moved to `backend/data/backups/` and is intentionally untracked.

Notes

- The branch excludes the large PDF from git and keeps it in backups to avoid exceeding GitHub limits.
- Alert webhook tested (posted to `ALERT_WEBHOOK_URL` configured in `.env`).

Suggested reviewer checklist

- Verify CSV normalization matches expected columns.
- Confirm `scripts/import_htsdata.py` behavior and whether to run it on a schedule.
- Decide whether to store the PDF in a file server or cloud storage instead of the repo.

Links

- Branch: `feat/import-htsdata`
- Create PR: https://github.com/bornchosen03/dutyguard-ai/pull/new/feat/import-htsdata
