import io
from reportlab.lib.pagesizes import A6
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_shipping_label_pdf(shipment_data: dict, order_data: dict) -> bytes:
    buffer = io.BytesIO()
    # A6 is the standard 4x6 inch e-commerce shipping label size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A6,
        leftMargin=15,
        rightMargin=15,
        topMargin=15,
        bottomMargin=15
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'LabelTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#8D4B08'),
    )
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
    )

    story = []

    # Header with Courier Partner & KalaCart branding
    courier = shipment_data.get('courier_partner', 'India Post Speed Post')
    story.append(Paragraph(f"<b>KALACART EXPRESS</b> | {courier}", title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#8D4B08'), spaceAfter=6))

    # Tracking Number & Barcode representation
    tracking_no = shipment_data.get('tracking_number', 'INP-KC-987654321')
    story.append(Paragraph(f"<b>TRACKING #:</b> {tracking_no}", ParagraphStyle('Trk', fontName='Helvetica-Bold', fontSize=12, leading=14)))
    story.append(Paragraph(f"||||| |||||| |||| |||||||| |||||||||| ||||||| {tracking_no}", ParagraphStyle('Bar', fontName='Courier-Bold', fontSize=10, leading=12)))
    story.append(Spacer(1, 6))

    # Details table (Package Size, Weight, COD/Prepaid)
    pay_mode = "COD" if shipment_data.get('is_cod') else "PREPAID / ESCROW"
    pkg_size = str(shipment_data.get('package_size', 'Medium')).upper()
    weight = shipment_data.get('weight_kg', 1.0)
    declared = shipment_data.get('declared_value', 0.0)

    details_data = [
        [Paragraph(f"<b>Payment:</b> {pay_mode}", body_style), Paragraph(f"<b>Weight:</b> {weight} kg", body_style)],
        [Paragraph(f"<b>Package:</b> {pkg_size}", body_style), Paragraph(f"<b>Declared:</b> ?{declared}", body_style)],
    ]
    t = Table(details_data, colWidths=[120, 120])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E0D5C7')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Deliver To / Ship From
    to_name = order_data.get('buyer_name', 'Customer')
    to_addr = order_data.get('delivery_address', 'Delivery Address')
    to_pin = shipment_data.get('destination_pincode', '000000')
    to_phone = order_data.get('buyer_phone', '')

    from_name = order_data.get('seller_name', 'Artisan')
    from_addr = order_data.get('shipping_address', 'Artisan Workshop')
    from_pin = shipment_data.get('origin_pincode', '000000')

    address_table_data = [
        [Paragraph("<b>SHIP TO:</b>", bold_style), Paragraph("<b>RETURN / SHIP FROM:</b>", bold_style)],
        [
            Paragraph(f"<b>{to_name}</b><br/>{to_addr}<br/><b>PIN: {to_pin}</b><br/>Ph: {to_phone}", body_style),
            Paragraph(f"<b>{from_name}</b><br/>{from_addr}<br/><b>PIN: {from_pin}</b>", body_style)
        ]
    ]
    at = Table(address_table_data, colWidths=[130, 110])
    at.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#3E2723')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(at)
    story.append(Spacer(1, 6))

    # Badges: Fragile, Insurance
    badges = []
    if shipment_data.get('is_fragile'):
        badges.append("?? FRAGILE - HANDLE WITH CARE")
    if shipment_data.get('is_insured'):
        badges.append("??? INSURED CONSIGNMENT")
    if shipment_data.get('pickup_type') == 'self_drop':
        badges.append("?? SELF DROP AT HUB")

    if badges:
        badge_text = " | ".join(badges)
        story.append(Paragraph(f"<b>{badge_text}</b>", ParagraphStyle('Badge', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#B00020'))))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
