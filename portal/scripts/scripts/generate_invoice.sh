#!/bin/zsh
# Usage: ./generate_invoice.sh <customer_name> <service> <amount>
DATE=$(date +%Y-%m-%d)
INVOICE_ID="INV-$(date +%s)"
CUSTOMER="$1"
SERVICE="$2"
AMOUNT="$3"
OUT="/Users/bthrax/DutyGuard-AI/customer_uploads/invoice_${INVOICE_ID}.txt"

if [ -z "$CUSTOMER" ] || [ -z "$SERVICE" ] || [ -z "$AMOUNT" ]; then
  echo "Usage: $0 <customer_name> <service> <amount>"
  exit 1
fi

echo "Invoice ID: $INVOICE_ID" > $OUT
echo "Date: $DATE" >> $OUT
echo "Customer: $CUSTOMER" >> $OUT
echo "Service: $SERVICE" >> $OUT
echo "Amount Due: $AMOUNT" >> $OUT
echo "Status: Unpaid" >> $OUT
echo "---" >> $OUT
echo "Please remit payment to DutyGuard-AI." >> $OUT
echo "Invoice generated: $OUT"
