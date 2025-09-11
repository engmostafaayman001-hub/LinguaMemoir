import os
import secrets
from datetime import datetime
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=(800, 600)):
    """Resize image to maximum dimensions while maintaining aspect ratio"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
    except Exception as e:
        print(f"Error resizing image: {e}")

def generate_invoice_number():
    """Generate unique invoice number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(2).upper()
    return f"INV-{timestamp}-{random_suffix}"

def create_invoice_pdf(sale):
    """Create PDF invoice for a sale"""
    filename = f"invoice_{sale.invoice_number}.pdf"
    filepath = os.path.join("static", "invoices", filename)
    
    # Create invoices directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Title
    story.append(Paragraph("فاتورة مبيعات", title_style))
    story.append(Spacer(1, 12))
    
    # Invoice details
    invoice_data = [
        ['رقم الفاتورة:', sale.invoice_number],
        ['التاريخ:', sale.created_at.strftime('%Y-%m-%d %H:%M')],
        ['الكاشير:', sale.employee.full_name],
        ['العميل:', sale.customer_name or 'عميل عادي'],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Items table
    items_data = [['المنتج', 'الكمية', 'سعر الوحدة', 'الإجمالي']]
    
    for item in sale.items:
        items_data.append([
            item.product.name_ar,
            str(item.quantity),
            f"{item.unit_price:.2f} ر.س",
            f"{item.total_price:.2f} ر.س"
        ])
    
    # Add totals
    items_data.append(['', '', 'المجموع الفرعي:', f"{sum(item.total_price for item in sale.items):.2f} ر.س"])
    if sale.discount_amount > 0:
        items_data.append(['', '', 'الخصم:', f"-{sale.discount_amount:.2f} ر.س"])
    items_data.append(['', '', 'الإجمالي النهائي:', f"{sale.total_amount:.2f} ر.س"])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Footer
    footer_text = "شكراً لزيارتكم - نتمنى لكم يوماً سعيداً"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1  # Center alignment
    )
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    
    return filepath

def calculate_profit_margin(selling_price, cost_price):
    """Calculate profit margin percentage"""
    if not cost_price or cost_price == 0:
        return 0
    return ((selling_price - cost_price) / cost_price) * 100
