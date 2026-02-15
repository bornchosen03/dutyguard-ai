#!/bin/zsh
# Health check for backend server
PORT=8080
URL="http://localhost:$PORT/health"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)
if [ "$STATUS" = "200" ]; then
    echo "Backend is healthy."
else
    echo "Backend is NOT healthy. Status: $STATUS"
fi
