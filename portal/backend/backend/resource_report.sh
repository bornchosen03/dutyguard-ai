#!/bin/zsh
# Report backend resource usage
PORT=8080
PID=$(lsof -i :$PORT | grep LISTEN | awk '{print $2}')
if [ -n "$PID" ]; then
    ps -p $PID -o %cpu,%mem,etime,cmd
else
    echo "Backend not running."
fi
