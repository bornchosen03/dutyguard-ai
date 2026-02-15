

#!/bin/zsh
# Usage: ./generate_quote.sh <customer_name> <service> <amount>
DATE=$(date +%Y-%m-%d)
QUOTE_ID="Q-$(date +%s)"
CUSTOMER="$1"
SERVICE="$2"
AMOUNT="$3"
OUT="/Users/bthrax/DutyGuard-AI/customer_uploads/quote_${QUOTE_ID}.txt"
TRACKER="/Users/bthrax/DutyGuard-AI/customer_uploads/quote_tracker.txt"

if [ -z "$CUSTOMER" ] || [ -z "$SERVICE" ] || [ -z "$AMOUNT" ]; then
  echo "Usage: $0 <customer_name> <service> <amount>"
  exit 1
fi

# Count previous quotes for this customer
COUNT=0
if [ -f "$TRACKER" ]; then
  COUNT=$(grep -c "^$CUSTOMER:" "$TRACKER")
fi

if [ "$COUNT" -lt 1 ]; then
  echo "$CUSTOMER: $DATE $QUOTE_ID (free)" >> "$TRACKER"
  AMOUNT_DISPLAY="FREE (first quote is free)"
else
  echo "$CUSTOMER: $DATE $QUOTE_ID (paid)" >> "$TRACKER"
  AMOUNT_DISPLAY="$AMOUNT (standard pricing applies)"
fi

echo "Quote ID: $QUOTE_ID" > $OUT
echo "Date: $DATE" >> $OUT
echo "Customer: $CUSTOMER" >> $OUT
echo "Service: $SERVICE" >> $OUT
echo "Amount: $AMOUNT_DISPLAY" >> $OUT
echo "Status: Pending" >> $OUT
echo "---" >> $OUT
if [ "$COUNT" -lt 1 ]; then
  echo "This quote is free (first quote is free)!" >> $OUT
else
  echo "Standard pricing applies for this and future quotes." >> $OUT
fi
echo "Thank you for considering DutyGuard-AI!" >> $OUT
echo "Quote generated: $OUT"
