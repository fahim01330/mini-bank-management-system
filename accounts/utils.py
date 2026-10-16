import csv
import io
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def export_statement_csv(account, transactions, start_date=None, end_date=None):
    """
    Generates a CSV response containing the account statement.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}.csv"'

    writer = csv.writer(response)
    writer.writerow(['MINI BANK MANAGEMENT SYSTEM - ACCOUNT STATEMENT'])
    writer.writerow(['Account Number:', account.account_number])
    writer.writerow(['Account Type:', account.get_account_type_display()])
    writer.writerow(['Account Holder:', account.owner.get_full_name() or account.owner.username])
    writer.writerow(['Email:', account.owner.email])
    writer.writerow(['Current Balance:', f"${account.balance:.2f}"])
    if start_date:
        writer.writerow(['Start Date:', start_date])
    if end_date:
        writer.writerow(['End Date:', end_date])
    writer.writerow([])
    writer.writerow([
        'Timestamp',
        'Transaction Reference',
        'Type',
        'Amount ($)',
        'Balance After ($)',
        'Related Account',
        'Description',
        'Status'
    ])

    for txn in transactions:
        related = txn.related_account.account_number if txn.related_account else 'N/A'
        writer.writerow([
            txn.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            txn.transaction_reference,
            txn.transaction_type,
            f"{txn.amount:.2f}",
            f"{txn.balance_after:.2f}",
            related,
            txn.description,
            txn.status
        ])

    return response


def export_statement_pdf(account, transactions, start_date=None, end_date=None):
    """
    Generates a clean PDF response containing the account statement using ReportLab.
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
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=6,
    )
    normal_style = styles['Normal']

    # Header
    elements.append(Paragraph("MINI BANK MANAGEMENT SYSTEM", title_style))
    date_range_str = f"Period: {start_date or 'Beginning'} to {end_date or 'Present'}"
    elements.append(Paragraph(f"Official Account Statement — {date_range_str}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Account summary table
    summary_data = [
        [
            Paragraph("<b>Account Holder:</b>", normal_style),
            Paragraph(account.owner.get_full_name() or account.owner.username, normal_style),
            Paragraph("<b>Account Number:</b>", normal_style),
            Paragraph(account.account_number, normal_style),
        ],
        [
            Paragraph("<b>Email:</b>", normal_style),
            Paragraph(account.owner.email, normal_style),
            Paragraph("<b>Account Type:</b>", normal_style),
            Paragraph(account.get_account_type_display(), normal_style),
        ],
        [
            Paragraph("<b>Status:</b>", normal_style),
            Paragraph(account.get_status_display(), normal_style),
            Paragraph("<b>Current Balance:</b>", normal_style),
            Paragraph(f"<b>${account.balance:,.2f}</b>", normal_style),
        ]
    ]

    summary_table = Table(summary_data, colWidths=[100, 160, 110, 170])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # Transactions Table
    elements.append(Paragraph("Transaction Activity", section_style))

    table_data = [[
        Paragraph("<b>Date / Time</b>", normal_style),
        Paragraph("<b>Reference</b>", normal_style),
        Paragraph("<b>Type</b>", normal_style),
        Paragraph("<b>Amount</b>", normal_style),
        Paragraph("<b>Balance</b>", normal_style),
        Paragraph("<b>Counterparty</b>", normal_style),
    ]]

    for txn in transactions:
        counterparty = txn.related_account.account_number if txn.related_account else "-"
        table_data.append([
            Paragraph(txn.timestamp.strftime('%Y-%m-%d %H:%M'), normal_style),
            Paragraph(txn.transaction_reference, normal_style),
            Paragraph(txn.transaction_type, normal_style),
            Paragraph(f"${txn.amount:,.2f}", normal_style),
            Paragraph(f"${txn.balance_after:,.2f}", normal_style),
            Paragraph(counterparty, normal_style),
        ])

    if len(transactions) == 0:
        table_data.append([
            Paragraph("No transactions recorded for this period.", normal_style),
            "", "", "", "", ""
        ])

    txn_table = Table(table_data, colWidths=[90, 130, 75, 75, 85, 85])
    txn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(txn_table)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}.pdf"'
    return response
