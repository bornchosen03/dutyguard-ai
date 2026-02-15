#!/bin/zsh
# Monitor backend API response time
URL="http://localhost:8080/health"
TIME=$(curl -o /dev/null -s -w "%{time_total}" $URL)
echo "API response time: $TIME seconds"
