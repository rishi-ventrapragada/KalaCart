import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_craft_certificate_pdf(passport_dict: dict, cert_dict: dict) -> bytes:
    """Generate official A4 KalaCart GI Heritage Certificate of Authenticity PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1, # Center
        textColor=colors.HexColor('#8D4B08') # Terracotta
    )
    subtitle_style = ParagraphStyle(
        'CertSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#2E7D32') # Forest Green
    )
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#3E2723')
    )
    bold_label = ParagraphStyle(
        'CertLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#3E2723')
    )

    story = []

    # Title & Header
    story.append(Paragraph("KALACART HERITAGE PROVENANCE &amp; GI BOARD", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("NATIONAL GEOGRAPHICAL INDICATION &amp; CRAFT AUTHENTICITY CERTIFICATE", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#8D4B08'), spaceAfter=14))

    # Certificate Details Table
    cert_no = cert_dict.get('certificate_number', passport_dict.get('certificate_number', 'CERT-2026-0001'))
    craft_id = passport_dict.get('craft_id', 'KALA-GI-0001')
    issue_date = cert_dict.get('issue_date', str(date.today()))

    cert_meta = [
        [Paragraph("<b>Certificate Number:</b>", bold_label), Paragraph(cert_no, body_style),
         Paragraph("<b>Date of Issue:</b>", bold_label), Paragraph(str(issue_date), body_style)],
        [Paragraph("<b>Unique Craft ID:</b>", bold_label), Paragraph(craft_id, body_style),
         Paragraph("<b>Authenticity Status:</b>", bold_label), Paragraph("<font color='#2E7D32'><b>GOVERNMENT GI VERIFIED</b></font>", body_style)]
    ]
    meta_table = Table(cert_meta, colWidths=[120, 140, 120, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF8F0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0D5C7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Artifact & Artisan Provenance
    artisan_name = passport_dict.get('artisan_name', 'Master Artisan')
    product_title = passport_dict.get('product_title', 'Traditional Handicraft')
    craft_cat = passport_dict.get('craft_category', 'Handicraft')
    tradition = passport_dict.get('craft_tradition', 'Heritage Craft')
    village = passport_dict.get('village', '')
    district = passport_dict.get('district', '')
    state = passport_dict.get('state', '')
    materials = ", ".join(passport_dict.get('materials', [])) or "Authentic Natural Sourced Materials"

    provenance_rows = [
        [Paragraph("<b>Craft Title:</b>", bold_label), Paragraph(f"<b>{product_title}</b>", body_style)],
        [Paragraph("<b>Certified Master Artisan:</b>", bold_label), Paragraph(artisan_name, body_style)],
        [Paragraph("<b>Craft Tradition:</b>", bold_label), Paragraph(tradition, body_style)],
        [Paragraph("<b>Category:</b>", bold_label), Paragraph(craft_cat, body_style)],
        [Paragraph("<b>Geographical Origin:</b>", bold_label), Paragraph(f"{village}, {district}, {state}, India", body_style)],
        [Paragraph("<b>Natural Materials:</b>", bold_label), Paragraph(materials, body_style)],
        [Paragraph("<b>Verification Portal:</b>", bold_label), Paragraph(passport_dict.get('verification_url', 'https://kalacart.in/verify'), body_style)]
    ]
    prov_table = Table(provenance_rows, colWidths=[160, 360])
    prov_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#EFEBE9')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(prov_table)
    story.append(Spacer(1, 20))

    # Declarative text
    cert_text = (
        "This is to formally certify that the artifact described herein has been cataloged and verified under the "
        "KalaCart Provenance Standards. It complies with registered Geographical Indication practices, utilizes "
        "sustainable authentic materials, and honors the traditional generational heritage of the artisan community."
    )
    story.append(Paragraph(f"<i>{cert_text}</i>", body_style))
    story.append(Spacer(1, 24))

    # Signatures
    sig_data = [
        [Paragraph("_______________________________<br/><b>Artisan Guild Master</b>", body_style),
         Paragraph("_______________________________<br/><b>Geographical Indications Registrar</b>", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    story.append(sig_table)
    story.append(Spacer(1, 16))

    # Digital signature hash
    sig_hash = cert_dict.get('digital_signature_hash', 'SHA256:4f9b8c2d1e0a7f5b9c3e8d7a6b5c4d3e2f1a0b9c')
    story.append(Paragraph(f"<b>Digital Cryptographic Hash:</b> <font face='Courier'>{sig_hash}</font>", ParagraphStyle('Hash', fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor('#5D4037'))))

    doc.build(story)
    return buffer.getvalue()
