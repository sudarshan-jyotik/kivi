import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def build_pdf_document(
    filepath: str,
    doc_type: str,
    vendor_name: str,
    vendor_address: str,
    gstin: str,
    doc_number: str,
    doc_date: str,
    buyer_name: str,
    buyer_gstin: str,
    items: list,
    subtotal: float,
    cgst: float,
    sgst: float,
    igst: float,
    grand_total: float,
    notes: str = ""
):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#0284C7') if doc_type == "PURCHASE ORDER" else colors.HexColor('#1E293B')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=2
    )
    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B')
    )
    meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155')
    )
    cell_right = ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        alignment=2,
        textColor=colors.HexColor('#334155')
    )
    cell_bold_right = ParagraphStyle(
        'TableCellBoldRight',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        alignment=2,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Title & Type
    story.append(Paragraph(doc_type, title_style))
    story.append(Paragraph(f"Tax Compliant Document • Original Copy", meta_label))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=14))

    # Parties Metadata Table
    meta_table_data = [
        [
            Paragraph("<b>ISSUED BY:</b>", meta_label),
            Paragraph("<b>DOCUMENT DETAILS:</b>", meta_label)
        ],
        [
            Paragraph(f"<b>{vendor_name}</b><br/>{vendor_address}<br/><b>GSTIN:</b> {gstin}", cell_style),
            Paragraph(
                f"<b>{doc_type} Number:</b> {doc_number}<br/>"
                f"<b>Date:</b> {doc_date}<br/>"
                f"<b>Currency:</b> INR (₹)<br/>"
                f"<b>Place of Supply:</b> Karnataka (29)",
                cell_style
            )
        ],
        [
            Paragraph("<b>BILLED TO:</b>", meta_label),
            Paragraph("<b>STATUS / REF:</b>", meta_label)
        ],
        [
            Paragraph(f"<b>{buyer_name}</b><br/>Outer Ring Road, Bellandur, Bangalore 560103<br/><b>GSTIN:</b> {buyer_gstin}", cell_style),
            Paragraph(f"<b>Reference:</b> Direct Corporate Procurement<br/><b>Payment Terms:</b> Net 30 Days", cell_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[280, 252])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))

    # Line Items Table
    headers = [
        Paragraph("#", table_header),
        Paragraph("Description", table_header),
        Paragraph("HSN/SAC", table_header),
        Paragraph("Qty", table_header),
        Paragraph("Unit Price (₹)", table_header),
        Paragraph("Tax Rate", table_header),
        Paragraph("Amount (₹)", table_header),
    ]
    item_rows = [headers]

    for idx, it in enumerate(items, 1):
        item_rows.append([
            Paragraph(str(idx), cell_style),
            Paragraph(it["description"], cell_style),
            Paragraph(it.get("hsn", "8471"), cell_style),
            Paragraph(f"{it['quantity']:.0f}", cell_right),
            Paragraph(f"{it['unit_price']:,.2f}", cell_right),
            Paragraph(f"{it['tax_rate']:.0f}%", cell_right),
            Paragraph(f"{it['line_total']:,.2f}", cell_bold_right),
        ])

    items_table = Table(item_rows, colWidths=[24, 210, 54, 40, 74, 50, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    # Totals Summary Table
    totals_rows = [
        [Paragraph("Subtotal (Taxable Value):", cell_style), Paragraph(f"₹{subtotal:,.2f}", cell_bold_right)],
    ]
    if cgst > 0 or sgst > 0:
        totals_rows.append([Paragraph("CGST (Central GST):", cell_style), Paragraph(f"₹{cgst:,.2f}", cell_right)])
        totals_rows.append([Paragraph("SGST (State GST):", cell_style), Paragraph(f"₹{sgst:,.2f}", cell_right)])
    if igst > 0:
        totals_rows.append([Paragraph("IGST (Integrated GST):", cell_style), Paragraph(f"₹{igst:,.2f}", cell_right)])

    totals_rows.append([
        Paragraph("<b>Grand Total:</b>", ParagraphStyle('GB', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')),
        Paragraph(f"<b>₹{grand_total:,.2f}</b>", ParagraphStyle('GTB', parent=styles['Normal'], fontSize=10, alignment=2, fontName='Helvetica-Bold', textColor=primary_color))
    ])

    totals_table = Table(totals_rows, colWidths=[150, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, primary_color),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
    ]))

    # Wrap totals on right side
    layout_data = [
        [
            Paragraph(f"<b>Notes:</b><br/>{notes or 'Standard electronic compliance document.'}<br/><br/><i>Authorized Signatory</i>", meta_label),
            totals_table
        ]
    ]
    layout_table = Table(layout_data, colWidths=[282, 250])
    layout_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(layout_table)

    doc.build(story)
    print(f"Generated: {filepath}")


def generate_all():
    print("Generating Sample PDF documents under /samples ...")

    buyer_name = "Zenith Retail & Logistics Pvt Ltd"
    buyer_gstin = "29AABCZ9876E1Z4"

    # =========================================================================
    # Sample 1: Clean Match -> APPROVE
    # =========================================================================
    vendor_1 = "Acme Technologies India Pvt Ltd"
    address_1 = "Tower B, Prestige Tech Park, Marathahalli, Bangalore 560087"
    gstin_1 = "29AABCA1234F1Z5"

    items_1 = [
        {"description": "Dell Latitude 5440 Core i7 16GB 512GB SSD Laptop", "quantity": 5.0, "unit_price": 75000.0, "tax_rate": 18.0, "line_total": 375000.0, "hsn": "8471"},
        {"description": "Dell 27-inch 4K UHD USB-C Hub Monitor (P2723QE)", "quantity": 5.0, "unit_price": 25000.0, "tax_rate": 18.0, "line_total": 125000.0, "hsn": "8528"},
        {"description": "Logitech MX Keys Wireless Keyboard & Mouse Combo", "quantity": 5.0, "unit_price": 2500.0, "tax_rate": 18.0, "line_total": 12500.0, "hsn": "8471"},
    ]
    subtotal_1 = 512500.0
    cgst_1 = 46125.0
    sgst_1 = 46125.0
    total_1 = 604750.0

    # PO 1
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_1_po.pdf"),
        doc_type="PURCHASE ORDER",
        vendor_name=vendor_1,
        vendor_address=address_1,
        gstin=gstin_1,
        doc_number="PO-2024-001",
        doc_date="2024-10-15",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=items_1,
        subtotal=subtotal_1,
        cgst=cgst_1,
        sgst=sgst_1,
        igst=0.0,
        grand_total=total_1,
        notes="Approved purchase order. Ship to Bangalore facility."
    )

    # Invoice 1 (Clean Match)
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_1_invoice.pdf"),
        doc_type="TAX INVOICE",
        vendor_name=vendor_1,
        vendor_address=address_1,
        gstin=gstin_1,
        doc_number="INV-2024-101",
        doc_date="2024-10-18",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=items_1,
        subtotal=subtotal_1,
        cgst=cgst_1,
        sgst=sgst_1,
        igst=0.0,
        grand_total=total_1,
        notes="Payment due within 30 days. Reference PO-2024-001."
    )

    # =========================================================================
    # Sample 2: Price and quantity mismatch + wrong GST rate -> REJECT/REVIEW
    # =========================================================================
    vendor_2 = "Nexa Enterprise Networks Ltd"
    address_2 = "Unit 402, Andheri East, Mumbai 400069"
    gstin_2 = "27AABCN5678G1Z2"

    # PO 2
    po_items_2 = [
        {"description": "Cisco Catalyst 24-Port Gigabit Managed Switch", "quantity": 2.0, "unit_price": 40000.0, "tax_rate": 18.0, "line_total": 80000.0, "hsn": "8517"},
        {"description": "Cat6 Shielded High-Speed Patch Cable 5-Meter", "quantity": 50.0, "unit_price": 300.0, "tax_rate": 18.0, "line_total": 15000.0, "hsn": "8544"},
    ]
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_2_po.pdf"),
        doc_type="PURCHASE ORDER",
        vendor_name=vendor_2,
        vendor_address=address_2,
        gstin=gstin_2,
        doc_number="PO-2024-002",
        doc_date="2024-10-20",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=po_items_2,
        subtotal=95000.0,
        cgst=8550.0,
        sgst=8550.0,
        igst=0.0,
        grand_total=112100.0,
        notes="Standard IT infrastructure expansion order."
    )

    # Invoice 2 (Price Mismatch: ₹48,000 vs ₹40,000; Qty Mismatch: 70 vs 50; Wrong Tax: 28% vs 18%)
    inv_items_2 = [
        {"description": "Cisco Catalyst 24-Port Gigabit Managed Switch", "quantity": 2.0, "unit_price": 48000.0, "tax_rate": 28.0, "line_total": 96000.0, "hsn": "8517"},
        {"description": "Cat6 Shielded High-Speed Patch Cable 5-Meter", "quantity": 70.0, "unit_price": 300.0, "tax_rate": 28.0, "line_total": 21000.0, "hsn": "8544"},
    ]
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_2_invoice.pdf"),
        doc_type="TAX INVOICE",
        vendor_name=vendor_2,
        vendor_address=address_2,
        gstin=gstin_2,
        doc_number="INV-2024-102",
        doc_date="2024-10-24",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=inv_items_2,
        subtotal=117000.0,
        cgst=16380.0,
        sgst=16380.0,
        igst=0.0,
        grand_total=149760.0,
        notes="Includes revised market component pricing and supplementary cable dispatch."
    )

    # =========================================================================
    # Sample 3: Extra line item not in PO + total mismatch -> REVIEW
    # =========================================================================
    vendor_3 = "Apex Industrial Machinery LLP"
    address_3 = "Industrial Area Phase 2, Okhla, New Delhi 110020"
    gstin_3 = "07AABCA9999H1Z8"

    # PO 3
    po_items_3 = [
        {"description": "Heavy Duty Industrial Hydraulic Water Pump 5HP", "quantity": 1.0, "unit_price": 120000.0, "tax_rate": 18.0, "line_total": 120000.0, "hsn": "8413"},
        {"description": "High Performance Synthetic Hydraulic Lubricant 20L", "quantity": 4.0, "unit_price": 8500.0, "tax_rate": 18.0, "line_total": 34000.0, "hsn": "2710"},
    ]
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_3_po.pdf"),
        doc_type="PURCHASE ORDER",
        vendor_name=vendor_3,
        vendor_address=address_3,
        gstin=gstin_3,
        doc_number="PO-2024-003",
        doc_date="2024-10-25",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=po_items_3,
        subtotal=154000.0,
        cgst=0.0,
        sgst=0.0,
        igst=27720.0,
        grand_total=181720.0,
        notes="Plant maintenance equipment. Interstate supply via IGST."
    )

    # Invoice 3 (Includes unauthorized extra line item: Emergency Express Rigging & Handling)
    inv_items_3 = [
        {"description": "Heavy Duty Industrial Hydraulic Water Pump 5HP", "quantity": 1.0, "unit_price": 120000.0, "tax_rate": 18.0, "line_total": 120000.0, "hsn": "8413"},
        {"description": "High Performance Synthetic Hydraulic Lubricant 20L", "quantity": 4.0, "unit_price": 8500.0, "tax_rate": 18.0, "line_total": 34000.0, "hsn": "2710"},
        {"description": "Unscheduled Priority Express Rigging & Handling Fee", "quantity": 1.0, "unit_price": 25000.0, "tax_rate": 18.0, "line_total": 25000.0, "hsn": "9985"},
    ]
    build_pdf_document(
        filepath=os.path.join(SAMPLES_DIR, "sample_3_invoice.pdf"),
        doc_type="TAX INVOICE",
        vendor_name=vendor_3,
        vendor_address=address_3,
        gstin=gstin_3,
        doc_number="INV-2024-103",
        doc_date="2024-10-28",
        buyer_name=buyer_name,
        buyer_gstin=buyer_gstin,
        items=inv_items_3,
        subtotal=179000.0,
        cgst=0.0,
        sgst=0.0,
        igst=32220.0,
        grand_total=211220.0,
        notes="Includes express turnaround handling surcharge."
    )

    print("All 3 pairs generated successfully in /samples.")


if __name__ == "__main__":
    generate_all()
