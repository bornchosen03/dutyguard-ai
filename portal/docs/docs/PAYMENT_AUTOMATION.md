# Payment Automation for DutyGuard-AI

## 1. Quoting
- Use `scripts/generate_quote.sh` to create a quote for a customer and service.
- Example: `./generate_quote.sh "Acme Corp" "Tariff Analysis" "$500"`

## 2. Invoicing
- Use `scripts/generate_invoice.sh` to create an invoice for a customer and service.
- Example: `./generate_invoice.sh "Acme Corp" "Tariff Analysis" "$500"`

## 3. Payment Collection (Stripe)
- Integrate Stripe for secure online payments.
- Use Stripe Dashboard or add a payment link to your invoice.
- (Optional) Add a Stripe payment button to your web UI for self-serve checkout.

## 4. Workflow
1. Generate quote → send to customer.
2. Upon acceptance, generate invoice → send to customer.
3. Customer pays via Stripe link or button.
4. Mark invoice as paid and deliver results.

## 5. Next Steps
- To fully automate, connect Stripe API to your backend or web UI.
- Optionally, automate invoice emails and payment status checks.

---

*Contact GitHub Copilot for help integrating Stripe or building a customer payment portal!*
