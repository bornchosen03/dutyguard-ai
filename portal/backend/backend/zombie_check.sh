#!/bin/zsh
# Check for zombie backend processes
ZOMBIES=$(ps aux | awk '$8 ~ /Z/ { print $2 }')
if [ -n "$ZOMBIES" ]; then
    echo "Zombie processes found: $ZOMBIES" | mail -s "DutyGuard-AI Zombie Process Alert" your@email.com
else
    echo "No zombie processes found."
fi
