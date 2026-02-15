#!/bin/zsh
# Check for backend memory leaks
PORT=8080
PID=$(lsof -i :$PORT | grep LISTEN | awk '{print $2}')
if [ -n "$PID" ]; then
    ps -p $PID -o pid,%mem,cmd
    echo "Check for abnormal memory growth in backend process."
else
    echo "Backend not running."
fi
