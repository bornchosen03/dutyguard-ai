#!/bin/zsh
# Daily backup of backend data and logs
BACKUP_DIR="/Users/bthrax/DutyGuard-AI/backend/backup_$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp -r /Users/bthrax/DutyGuard-AI/backend/data $BACKUP_DIR/
cp /Users/bthrax/DutyGuard-AI/backend/uvicorn.log $BACKUP_DIR/
echo "Backup completed at $BACKUP_DIR"
