from flask import Flask, request, send_file, jsonify
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime, timedelta
import io
from flask import render_template
from reportlab.platypus import Image
app = Flask(__name__)

class InvoiceTemplate:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter
        
    def create_header_style(self):
        return ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
    
    def create_info_style(self):
        return ParagraphStyle(
            'CustomInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
        )

def create_invoice(client_name, billing_items):
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Initialize template
    template = InvoiceTemplate()
    
    # Create story (content) for the PDF
    story = []
    
    # Add company logo/header
    logo_path = "./static/logo.png"  # Update this path to your logo file
    logo = Image(logo_path, 2*inch, 2*inch)
    story.append(logo)
    
    # Add company info
    info_style = template.create_info_style()
    company_info = [
        "Giza, 6 October 12554",
        "Phone: +20 111 7488 570",
        "Email: info@codhaheroes.social"
    ]
    for info in company_info:
        story.append(Paragraph(info, info_style))
    
    story.append(Spacer(1, 20))
    
    # Add invoice details
    invoice_data = [
        ["Invoice Number:", f"INV-{int(datetime.now().timestamp())}"],
        ["Date:", datetime.now().strftime('%Y-%m-%d')],
        ["Due Date:", (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')],
        ["Client:", client_name]
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(invoice_table)
    
    story.append(Spacer(1, 20))
    
    # Add billing details
    billing_data = [["Description", "Amount", "Discount (%)", "Total"]]
    total_amount = 0
    for item in billing_items:
        amount = float(item['amount'])
        discount = float(item['discount'])
        total = amount - (amount * discount / 100)
        billing_data.append([item['description'], f"{amount:.2f} L.E.", f"{discount:.2f}%", f"{total:.2f} L.E."])
        total_amount += total
    billing_data.append(["", "", "Total", f"{total_amount:.2f} L.E."])
    
    billing_table = Table(billing_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 2*inch])
    billing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row bold
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),  # Line above header
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Line below header
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),  # Line above total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Total row bold
    ]))
    story.append(billing_table)
    
    story.append(Spacer(1, 40))
    
    # Add payment terms and notes
    terms_style = template.create_info_style()
    terms = [
        "Payment Terms:",
        "- Payment is due within 30 days",
        "- Please include invoice number with payment",
        "- Make checks payable to Your Company Name",
        "",
        "Thank you for your business!"
    ]
    for term in terms:
        story.append(Paragraph(term, terms_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    data = request.get_json()
    client_name = data.get('client_name')
    billing_items = data.get('billing_items')
    
    if not client_name or not billing_items:
        return jsonify({"error": "Missing client_name or billing_items"}), 400
    
    try:
        pdf_buffer = create_invoice(client_name, billing_items)
        return send_file(pdf_buffer, as_attachment=True, download_name=f"{client_name}_invoice.pdf", mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)