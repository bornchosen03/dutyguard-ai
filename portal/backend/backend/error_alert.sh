#!/bin/zsh
# Alert if backend log contains errors
LOG="/Users/bthrax/DutyGuard-AI/backend/uvicorn.log"
EMAIL="your@email.com"
if grep -i 'error' $LOG; then
    echo "Error found in backend log!" | mail -s "DutyGuard-AI Backend Error" $EMAIL
fi
