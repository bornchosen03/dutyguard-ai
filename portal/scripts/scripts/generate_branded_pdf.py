from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import sys

# Usage: python generate_branded_pdf.py <type> <customer_name> <service> <amount> <output_path>
# type: 'quote', 'invoice', or 'result'

def generate_pdf(doc_type, customer_name, service, amount, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    # Branding
    c.setFillColor(colors.HexColor('#2563eb'))
    c.rect(0, height - 1*inch, width, 1*inch, fill=1)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 24)
    c.drawString(0.75*inch, height - 0.7*inch, 'DutyGuard-AI')
    c.setFont('Helvetica', 14)
    c.drawString(4.5*inch, height - 0.7*inch, doc_type.capitalize() + ' Summary')

    # Main content
    c.setFillColor(colors.HexColor('#111827'))
    c.setFont('Helvetica', 16)
    c.drawString(0.75*inch, height - 1.5*inch, f'Customer: {customer_name}')
    c.drawString(0.75*inch, height - 2*inch, f'Service: {service}')
    c.drawString(0.75*inch, height - 2.5*inch, f'Amount: ${amount}')
    c.drawString(0.75*inch, height - 3*inch, f'Type: {doc_type}')

    # Footer
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.HexColor('#f59e42'))
    c.drawString(0.75*inch, 0.75*inch, 'Thank you for choosing DutyGuard-AI. For support, contact us at support@dutyguard.ai')

    c.save()

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print('Usage: python generate_branded_pdf.py <type> <customer_name> <service> <amount> <output_path>')
        sys.exit(1)
    doc_type, customer_name, service, amount, output_path = sys.argv[1:6]
    generate_pdf(doc_type, customer_name, service, amount, output_path)
