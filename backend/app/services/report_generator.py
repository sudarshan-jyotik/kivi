import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from ..models import Review


def generate_review_pdf(review: Review) -> bytes:
    """
    Generates a professional AP Audit and Approval Report in PDF format using reportlab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B')
    )

    elements = []

    # Header
    elements.append(Paragraph("AP Agent — Accounts Payable Audit Report", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Review ID: {review.id}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

    # Decision Banner
    decision = review.human_decision or review.system_decision or "PENDING"
    decision_color = colors.HexColor('#16A34A')  # Green for APPROVE
    if decision == "REJECT":
        decision_color = colors.HexColor('#DC2626')  # Red
    elif decision == "REVIEW":
        decision_color = colors.HexColor('#D97706')  # Amber

    banner_data = [
        [
            Paragraph(f"<b>SYSTEM RECOMMENDATION:</b> {review.system_decision or 'N/A'} (Score: {review.rule_score:.0f}/100)", ParagraphStyle('B1', textColor=colors.white, fontSize=11, leading=14)),
            Paragraph(f"<b>FINAL STATUS:</b> {review.status}", ParagraphStyle('B2', textColor=colors.white, fontSize=11, leading=14, alignment=2))
        ]
    ]
    banner_table = Table(banner_data, colWidths=[340, 200])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), decision_color),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 12))

    # Executive Rationale
    if review.rationale:
        elements.append(Paragraph("<b>Audit Rationale:</b>", section_heading))
        elements.append(Paragraph(review.rationale, body_style))
        elements.append(Spacer(1, 8))

    # Human Review Notes if available
    if review.human_decision:
        human_text = f"<b>Decision:</b> {review.human_decision} | <b>Timestamp:</b> {review.human_decided_at or 'N/A'}"
        if review.human_notes:
            human_text += f"<br/><b>Reviewer Notes:</b> {review.human_notes}"
        elements.append(Paragraph("<b>Human Reviewer Determination:</b>", section_heading))
        elements.append(Paragraph(human_text, body_style))
        elements.append(Spacer(1, 8))

    # Summary Metadata Table
    elements.append(Paragraph("<b>Document Comparison Summary:</b>", section_heading))
    inv_tot_str = f"₹{review.invoice_total:,.2f}" if review.invoice_total else "N/A"
    po_tot_str = f"₹{review.po_total:,.2f}" if review.po_total else "N/A"

    summary_data = [
        [
            Paragraph("<b>Vendor Name:</b>", body_style), Paragraph(str(review.vendor_name or "N/A"), body_style),
            Paragraph("<b>Currency:</b>", body_style), Paragraph(str(review.currency or "INR"), body_style)
        ],
        [
            Paragraph("<b>Invoice Number:</b>", body_style), Paragraph(str(review.invoice_number or "N/A"), body_style),
            Paragraph("<b>PO Number:</b>", body_style), Paragraph(str(review.po_number or "N/A"), body_style)
        ],
        [
            Paragraph("<b>Invoice Total:</b>", body_style), Paragraph(inv_tot_str, body_style),
            Paragraph("<b>PO Total:</b>", body_style), Paragraph(po_tot_str, body_style)
        ],
        [
            Paragraph("<b>Invoice File:</b>", body_style), Paragraph(str(review.invoice_filename or "N/A"), small_style),
            Paragraph("<b>PO File:</b>", body_style), Paragraph(str(review.po_filename or "N/A"), small_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[90, 180, 80, 190])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Discrepancies Table
    elements.append(Paragraph("<b>Audit Discrepancies & Evidence:</b>", section_heading))
    discrepancies = review.discrepancies or []

    if not discrepancies:
        elements.append(Paragraph("✅ <i>No discrepancies detected. 2-way match validated completely.</i>", body_style))
    else:
        disc_table_data = [
            [
                Paragraph("<b>Sev</b>", small_style),
                Paragraph("<b>Discrepancy / Description</b>", small_style),
                Paragraph("<b>Expected (PO)</b>", small_style),
                Paragraph("<b>Actual (Invoice)</b>", small_style),
                Paragraph("<b>Evidence Citation</b>", small_style)
            ]
        ]

        for d in discrepancies:
            sev = d.get("severity", "medium").upper()
            sev_color = "#DC2626" if sev == "HIGH" else ("#D97706" if sev == "MEDIUM" else "#2563EB")
            sev_badge = f"<font color='{sev_color}'><b>{sev}</b></font>"

            desc_text = f"<b>{d.get('title', '')}</b><br/>{d.get('description', '')}"
            exp_text = str(d.get("expected_value", "N/A"))
            act_text = str(d.get("actual_value", "N/A"))

            evidence = d.get("evidence") or {}
            evi_text = f"Doc: {evidence.get('source_document', 'N/A')} (p. {evidence.get('page_number', 1)})<br/><i>\"{evidence.get('text_snippet', '')[:80]}\"</i>"

            disc_table_data.append([
                Paragraph(sev_badge, small_style),
                Paragraph(desc_text, small_style),
                Paragraph(exp_text, small_style),
                Paragraph(act_text, small_style),
                Paragraph(evi_text, small_style)
            ])

        disc_table = Table(disc_table_data, colWidths=[40, 170, 95, 95, 140])
        disc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(disc_table)

    # Footer note
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=8))
    elements.append(Paragraph("AP Agent Automated Accounts Payable Audit Engine — For internal compliance verification.", small_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
