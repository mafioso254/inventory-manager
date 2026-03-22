from app.models import db, StockTransaction, Product
from datetime import datetime, timedelta
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pandas as pd

def generate_daily_report():
    """Generate daily transaction report for yesterday's transactions"""
    try:
        # Calculate yesterday's date range
        yesterday = datetime.now() - timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get all transactions from yesterday
        transactions = StockTransaction.query.filter(
            StockTransaction.timestamp >= start_of_yesterday,
            StockTransaction.timestamp <= end_of_yesterday
        ).order_by(StockTransaction.timestamp).all()

        if not transactions:
            print(f"No transactions found for {yesterday.strftime('%Y-%m-%d')}")
            return

        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # Generate PDF report
        pdf_filename = f"daily_report_{yesterday.strftime('%Y%m%d')}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)
        generate_pdf_report(transactions, yesterday, pdf_path)

        # Generate Excel report
        excel_filename = f"daily_report_{yesterday.strftime('%Y%m%d')}.xlsx"
        excel_path = os.path.join(reports_dir, excel_filename)
        generate_excel_report(transactions, yesterday, excel_path)

        print(f"Daily reports generated: {pdf_filename}, {excel_filename}")

    except Exception as e:
        print(f"Error generating daily report: {str(e)}")


def generate_pdf_report(transactions, report_date, filepath):
    """Generate PDF report"""
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph(f"Daily Transaction Report - {report_date.strftime('%Y-%m-%d')}", title_style))
    story.append(Spacer(1, 12))

    # Summary
    total_transactions = len(transactions)
    total_value = sum(abs(t.quantity) * t.product.price for t in transactions if t.product)

    summary_data = [
        ['Total Transactions:', str(total_transactions)],
        ['Total Value Impact:', f"Kshs {total_value:.2f}"],
        ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]

    summary_table = Table(summary_data, colWidths=[200, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Transactions table
    if transactions:
        table_data = [['Time', 'Product', 'SKU', 'Type', 'Quantity', 'Value Impact', 'Notes']]

        for t in transactions:
            if t.product:
                value_impact = abs(t.quantity) * t.product.price
                table_data.append([
                    t.timestamp.strftime('%H:%M:%S'),
                    t.product.name,
                    t.product.sku,
                    t.transaction_type.title(),
                    str(t.quantity),
                    f"Kshs {value_impact:.2f}",
                    t.notes or ''
                ])

        # Create table
        col_widths = [60, 120, 80, 70, 60, 80, 100]
        transaction_table = Table(table_data, colWidths=col_widths)

        # Style the table
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(transaction_table)

    doc.build(story)


def generate_excel_report(transactions, report_date, filepath):
    """Generate Excel report"""
    data = []

    for t in transactions:
        if t.product:
            value_impact = abs(t.quantity) * t.product.price
            data.append({
                'Timestamp': t.timestamp,
                'Product Name': t.product.name,
                'SKU': t.product.sku,
                'Transaction Type': t.transaction_type,
                'Quantity': t.quantity,
                'Unit Price': t.product.price,
                'Value Impact': value_impact,
                'Notes': t.notes or '',
                'Current Stock': t.product.current_stock
            })

    if data:
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')

        # Add summary sheet
        with pd.ExcelWriter(filepath, engine='openpyxl', mode='a') as writer:
            summary_data = {
                'Metric': ['Report Date', 'Total Transactions', 'Total Value Impact', 'Generated At'],
                'Value': [
                    report_date.strftime('%Y-%m-%d'),
                    len(data),
                    f"Kshs {sum(d['Value Impact'] for d in data):.2f}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
    else:
        # Create empty Excel file with summary
        summary_data = {
            'Metric': ['Report Date', 'Total Transactions', 'Total Value Impact', 'Generated At'],
            'Value': [
                report_date.strftime('%Y-%m-%d'),
                0,
                'Kshs 0.00',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(filepath, index=False, engine='openpyxl')