# Customer Upload & Processing Workflow

1. Place the customer file (PDF, CSV, etc.) in the `customer_uploads/` folder or use the script below.
2. Run the automation script:

```sh
cd scripts
./upload_and_process_customer.sh /path/to/customer_file.pdf
```

3. The script will:
   - Copy the file to `customer_uploads/`
   - Run all pipeline steps automatically
   - Output results to `knowledge_base/`

4. Search and analyze the processed data using the API or UI.

**Note:**
- You can customize the script for different file types or pipeline steps.
- For multiple files, loop over them or extend the script.
