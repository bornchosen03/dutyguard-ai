#!/bin/zsh
# Report backend disk usage
REPORT="/Users/bthrax/DutyGuard-AI/backend/disk_usage.log"
du -sh /Users/bthrax/DutyGuard-AI/backend/* > $REPORT
echo "Disk usage report written to $REPORT"
