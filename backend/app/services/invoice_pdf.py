"""Service for generating professional B2B Tax Invoice PDFs."""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_invoice_pdf(order_data: dict, invoice_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#8C3A00'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#555555')
    )
    header_right_style = ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=2,
        textColor=colors.HexColor('#222222')
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=13
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    inv_num = invoice_data.get('invoice_number', 'INV-0000')
    inv_date = invoice_data.get('invoice_date', datetime.utcnow().strftime('%d-%b-%Y'))
    if isinstance(inv_date, datetime):
        inv_date = inv_date.strftime('%d-%b-%Y')
    elif isinstance(inv_date, str) and 'T' in inv_date:
        inv_date = inv_date.split('T')[0]

    header_data = [
        [
            Paragraph('<b>KalaCart Marketplace</b><br/>Handmade with Heritage &amp; Escrow Protection', title_style),
            Paragraph(f'<b>TAX INVOICE</b><br/>Invoice #: {inv_num}<br/>Date: {inv_date}<br/>Order #: {order_data.get("order_number", "N/A")}', header_right_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[310, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    seller_name = order_data.get('seller_name', 'Artisan')
    seller_phone = order_data.get('seller_phone', '')
    buyer_name = order_data.get('buyer_name', 'Buyer')
    buyer_phone = order_data.get('buyer_phone', '')
    shipping_addr = order_data.get('shipping_address', 'N/A')
    delivery_addr = order_data.get('delivery_address', 'N/A')

    parties_data = [
        [
            Paragraph('<b>SOLD BY / ARTISAN:</b>', body_bold),
            Paragraph('<b>BILL TO / SHIP TO:</b>', body_bold)
        ],
        [
            Paragraph(f'<b>{seller_name}</b><br/>Phone: {seller_phone}<br/>Dispatch Location:<br/>{shipping_addr}', body_style),
            Paragraph(f'<b>{buyer_name}</b><br/>Phone: {buyer_phone}<br/>Delivery Address:<br/>{delivery_addr}', body_style)
        ]
    ]
    parties_table = Table(parties_data, colWidths=[270, 270])
    parties_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F5F2')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0D8D0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0D8D0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 15))

    items_rows = [
        [
            Paragraph('<b>Item Description</b>', body_bold),
            Paragraph('<b>Qty</b>', body_bold),
            Paragraph('<b>Unit Price</b>', body_bold),
            Paragraph('<b>Total</b>', body_bold)
        ]
    ]

    items = order_data.get('items', [])
    if not items:
        qty = order_data.get('quantity', 1)
        sub = float(order_data.get('subtotal', 0.0))
        items_rows.append([
            Paragraph('Artisan Order Item', body_style),
            Paragraph(str(qty), body_style),
            Paragraph(f'INR {sub:,.2f}', body_style),
            Paragraph(f'INR {sub:,.2f}', body_style),
        ])
    else:
        for itm in items:
            items_rows.append([
                Paragraph(str(itm.get('product_title', 'Handicraft Item')), body_style),
                Paragraph(str(itm.get('quantity', 1)), body_style),
                Paragraph(f'INR {float(itm.get("unit_price", 0)):,.2f}', body_style),
                Paragraph(f'INR {float(itm.get("subtotal", 0)):,.2f}', body_style),
            ])

    items_table = Table(items_rows, colWidths=[290, 50, 100, 100])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8C3A00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#8C3A00')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8E0D8')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    subtotal = float(order_data.get('subtotal', 0.0))
    gst_rate = float(order_data.get('gst_rate', 18.0))
    gst_amount = float(order_data.get('gst_amount', 0.0))
    shipping = float(order_data.get('shipping_charges', 0.0))
    total = float(order_data.get('total_amount', 0.0))
    advance = float(order_data.get('advance_amount', 0.0))
    balance = float(order_data.get('remaining_balance', 0.0))

    totals_data = [
        [Paragraph('Subtotal:', body_style), Paragraph(f'INR {subtotal:,.2f}', body_bold)],
        [Paragraph(f'GST ({gst_rate:.0f}%):', body_style), Paragraph(f'INR {gst_amount:,.2f}', body_style)],
        [Paragraph('Shipping Charges:', body_style), Paragraph(f'INR {shipping:,.2f}', body_style)],
        [Paragraph('<b>Total Order Value:</b>', body_bold), Paragraph(f'<b>INR {total:,.2f}</b>', body_bold)],
        [Paragraph('<b>Advance Escrow (Secured):</b>', body_style), Paragraph(f'INR {advance:,.2f}', body_bold)],
        [Paragraph('<b>Balance on Delivery:</b>', body_style), Paragraph(f'INR {balance:,.2f}', body_bold)],
    ]

    totals_table = Table(totals_data, colWidths=[390, 150])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 3), (1, 3), 1, colors.HexColor('#8C3A00')),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 20))

    terms_text = (
        '<b>Escrow Protection Terms:</b><br/>'
        '1. Funds are held in KalaCart Secure Escrow Trust until delivery &amp; acceptance.<br/>'
        '2. Advance is disbursed to artisan upon production milestone approval.<br/>'
        '3. Remaining balance is released upon confirmed delivery and buyer satisfaction.<br/>'
        '4. For any disputes, both buyer and seller can raise a dispute via the KalaCart Order Screen.'
    )
    story.append(Paragraph(terms_text, subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
