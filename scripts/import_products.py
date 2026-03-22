#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line tool to import products from Excel
Usage: python import_products.py products.xlsx
"""

import sys
import os
import io

# Fix stdout encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the parent directory to path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import create_app
from app.models import db, Product, StockTransaction

def import_products_from_excel(filepath):
    """Import products from Excel file"""

    app = create_app()

    with app.app_context():
        try:
            # Read Excel file
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, on_bad_lines='skip')
            else:
                df = pd.read_excel(filepath)

            print(f"[INFO] Found {len(df)} rows to process")
            print("=" * 50)

            success_count = 0
            error_count = 0

            for index, row in df.iterrows():
                try:
                    # Get values (handle different column names)
                    sku = str(row.get('SKU', row.get('sku', ''))).strip()
                    name = str(row.get('Name', row.get('name', ''))).strip()

                    if not sku or not name:
                        print(f"[WARN] Row {index + 2}: Skipped - missing SKU or Name")
                        error_count += 1
                        continue

                    # Check if product exists
                    existing = Product.query.filter_by(sku=sku).first()

                    # Get optional fields
                    barcode = str(row.get('Barcode', row.get('barcode', ''))).strip() or None
                    price = float(row.get('Price', row.get('price', 0)))
                    current_stock = int(row.get('Current Stock', row.get('current_stock', 0)))
                    min_stock = int(row.get('Min Stock Level', row.get('min_stock_level', 5)))
                    description = str(row.get('Description', row.get('description', '')))

                    if existing:
                        # Update existing
                        existing.name = name
                        existing.barcode = barcode or existing.barcode
                        existing.price = price
                        existing.current_stock = current_stock
                        existing.min_stock_level = min_stock
                        existing.description = description
                        print(f"[UPDATE] Updated: {sku} - {name} (Stock: {current_stock})")
                    else:
                        # Create new
                        product = Product(
                            sku=sku,
                            barcode=barcode,
                            name=name,
                            description=description,
                            price=price,
                            current_stock=current_stock,
                            min_stock_level=min_stock
                        )
                        db.session.add(product)
                        db.session.flush()  # Get ID without committing

                        # Add initial transaction if stock > 0
                        if current_stock > 0:
                            transaction = StockTransaction(
                                product_id=product.id,
                                quantity=current_stock,
                                transaction_type='purchase',
                                notes='Initial stock from Excel import'
                            )
                            db.session.add(transaction)

                        print(f"[OK] Created: {sku} - {name} (Stock: {current_stock})")

                    db.session.commit()
                    success_count += 1

                except Exception as e:
                    print(f"[ERROR] Row {index + 2}: Error - {str(e)}")
                    error_count += 1
                    db.session.rollback()

            print("\n" + "=" * 50)
            print(f"[COMPLETE] IMPORT COMPLETE!")
            print(f"[OK] Successfully imported: {success_count}")
            print(f"[ERROR] Failed: {error_count}")
            print("=" * 50)

        except Exception as e:
            print(f"[ERROR] Error reading file: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_products.py <excel_file>")
        print("\nExample:")
        print("  python scripts/import_products.py products.xlsx")
        print("  python scripts/import_products.py C:\\Users\\aaa\\Desktop\\inventory.csv")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    import_products_from_excel(filepath)