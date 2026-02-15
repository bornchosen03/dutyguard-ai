#!/bin/zsh
# Check SSL certificate expiry for backend (if using HTTPS)
DOMAIN="localhost"
PORT=443
if nc -z $DOMAIN $PORT; then
    echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:$PORT 2>/dev/null | openssl x509 -noout -dates
else
    echo "No SSL service running on $DOMAIN:$PORT"
fi
