#!/bin/zsh
# Monitor backend uptime and log it
PORT=8080
LOG="/Users/bthrax/DutyGuard-AI/backend/uptime.log"
DATE=$(date)
if lsof -i :$PORT | grep LISTEN > /dev/null; then
    echo "$DATE: Backend is UP" >> $LOG
else
    echo "$DATE: Backend is DOWN" >> $LOG
fi
