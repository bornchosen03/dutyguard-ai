#!/bin/zsh
# Notify on backend startup
EMAIL="your@email.com"
SUBJECT="DutyGuard-AI Backend Started"
BODY="Backend server started on $(date)"
echo "$BODY" | mail -s "$SUBJECT" $EMAIL
