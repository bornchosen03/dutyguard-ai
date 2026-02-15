#!/bin/zsh
# Run scheduled backend tasks
/Users/bthrax/DutyGuard-AI/backend/restart_backend.sh
/Users/bthrax/DutyGuard-AI/backend/health_check.sh
/Users/bthrax/DutyGuard-AI/backend/daily_backup.sh
/Users/bthrax/DutyGuard-AI/backend/uptime_monitor.sh
/Users/bthrax/DutyGuard-AI/backend/error_alert.sh
/Users/bthrax/DutyGuard-AI/backend/auto_update.sh
/Users/bthrax/DutyGuard-AI/backend/resource_report.sh
