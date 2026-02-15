# Maintenance & Scheduling

This document shows examples for regularly pruning the intake notification fallback log and running periodic release checks.

Cron examples

- Prune `intake_notifications.jsonl` to last 1000 entries every night at 03:00 UTC:

```cron
# m  h   dom mon dow command
0 3 * * * /usr/bin/env bash -lc "cd /path/to/DutyGuard-AI && ./scripts/prune_notifications.sh backend/data/intake_notifications.jsonl 1000 >> logs/prune.log 2>&1"
```

- Run the release check every hour (useful for CI smoke in dev/staging):

```cron
0 * * * * /usr/bin/env bash -lc "cd /path/to/DutyGuard-AI && ./scripts/release_check.sh >> logs/release_check.log 2>&1"
```

Systemd timer example

Create `/etc/systemd/system/dutyguard-prune.service`:

```ini
[Unit]
Description=Prune DutyGuard intake_notifications

[Service]
Type=oneshot
WorkingDirectory=/path/to/DutyGuard-AI
ExecStart=/usr/bin/env bash -lc './scripts/prune_notifications.sh backend/data/intake_notifications.jsonl 1000 >> logs/prune.log 2>&1'
```

Create `/etc/systemd/system/dutyguard-prune.timer`:

```ini
[Unit]
Description=Daily prune of DutyGuard fallback log

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Notes
- Replace `/path/to/DutyGuard-AI` with the repository path. The example uses `logs/` for output; create that directory and ensure the running user has write permissions.
- For production, prefer running `release_check` and pruning from a dedicated CI/ops user or runner. Do not run frequent release checks against production unless you intend that behaviour.

Rollback / safety
- `scripts/prune_notifications.sh` creates a timestamped backup before truncating the log.
