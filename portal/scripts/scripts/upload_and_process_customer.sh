#!/bin/zsh
# Usage: ./upload_and_process_customer.sh <customer_file>
UPLOAD_DIR="/Users/bthrax/DutyGuard-AI/customer_uploads"
PIPELINE_DIR="/Users/bthrax/DutyGuard-AI/scripts"

if [ -z "$1" ]; then
  echo "Usage: $0 <customer_file>"
  exit 1
fi

cp "$1" "$UPLOAD_DIR/"
echo "File $1 uploaded to $UPLOAD_DIR."

# Example: run pipeline scripts (customize as needed)
cd "$PIPELINE_DIR"
python3 parse_finalcopy_normalized.py
python3 filter_pdf_candidates.py
python3 reconcile_tariffs.py
python3 produce_canonical_csv.py
python3 extract_duties.py
python3 merge_duties_into_canonical.py
python3 normalize_duties.py
echo "Pipeline processing complete. Check knowledge_base/ for results."
