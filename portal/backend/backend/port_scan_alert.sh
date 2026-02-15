#!/bin/zsh
# Alert if unexpected ports are open
EXPECTED_PORTS=(8080)
OPEN_PORTS=($(lsof -iTCP -sTCP:LISTEN -P -n | awk '{print $9}' | grep -oE '[0-9]+$' | sort -u))
for PORT in $OPEN_PORTS; do
    if [[ ! " ${EXPECTED_PORTS[@]} " =~ " $PORT " ]]; then
        echo "Unexpected port open: $PORT" | mail -s "DutyGuard-AI Port Alert" your@email.com
    fi
 done
