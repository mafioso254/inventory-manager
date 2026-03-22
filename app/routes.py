from flask import Blueprint, request, jsonify, render_template, send_file
from app.models import db, Product, StockTransaction, User, StockTake, StockTakeItem
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt
import os
import csv
import io

main = Blueprint('main', __name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'replace-me-with-a-strong-secret')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_MINUTES = 120

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Authentication helpers ---

def create_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return data
    except Exception:
        return None


def login_required(fn):
    def wrapper(*args, **kwargs):
        # Auth bypassed - open access
        request.user = User.query.first()
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


def admin_required(fn):
    def wrapper(*args, **kwargs):
        # Auth bypassed - open access
        request.user = User.query.first()
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# ==================== WEB PAGES (no auth decorator — auth handled in JS) ====================

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/products')
def products_page():
    return render_template('products.html')

@main.route('/reports')
def reports_page():
    return render_template('reports.html')

@main.route('/stocktake')
def stocktake_page():
    return render_template('stocktake.html')

@main.route('/login')
def login_page():
    return render_template('login.html')

@main.route('/qb-clone')
def qb_clone_page():
    return render_template('qb_clone.html')


# ==================== AUTH ====================

@main.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = create_token(user)
    return jsonify({'token': token, 'user': user.to_dict()})


@main.route('/api/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify({'user': request.user.to_dict()})


# ==================== PRODUCTS ====================

@main.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@main.route('/api/products', methods=['POST'])
@admin_required
def create_product():
    data = request.json
    product = Product(
        sku=data['sku'],
        name=data['name'],
        description=data.get('description', ''),
        price=float(data.get('price', 0)),
        current_stock=int(data.get('current_stock', 0)),
        min_stock_level=int(data.get('min_stock_level', 5))
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@main.route('/api/products/download-template', methods=['GET'])
def download_product_template():
    """Download CSV template for product import — no auth needed for direct download"""
    template_rows = [
        'sku,name,price,current_stock,min_stock_level,description',
        'PROD-001,Product One,100.00,50,10,First product',
        'PROD-002,Product Two,250.50,20,5,Second product',
        'PROD-003,Product Three,75.00,100,15,Third product',
    ]
    output = io.BytesIO('\n'.join(template_rows).encode())
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='product_import_template.csv'
    )


@main.route('/api/products/upload-excel', methods=['POST'])
@admin_required
def upload_products_excel():
    """Bulk import products from Excel or CSV"""
    try:
        import pandas as pd
    except ImportError:
        return jsonify({'error': 'pandas not installed. Run: pip install pandas openpyxl'}), 500

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format. Use .xlsx, .xls, or .csv'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_excel(filepath)

        column_mapping = {
            'SKU': ['SKU', 'sku', 'Code', 'code', 'Product Code'],
            'Name': ['Name', 'name', 'Product Name', 'product_name'],
            'Price': ['Price', 'price', 'Cost', 'cost'],
            'Current Stock': ['Current Stock', 'current_stock', 'Stock', 'stock', 'Quantity'],
            'Min Stock Level': ['Min Stock Level', 'min_stock_level', 'Min Stock', 'Reorder Level'],
            'Description': ['Description', 'description', 'Notes', 'notes']
        }

        def find_column(df, possible_names):
            for col in possible_names:
                if col in df.columns:
                    return col
            return None

        sku_col = find_column(df, column_mapping['SKU'])
        name_col = find_column(df, column_mapping['Name'])

        if not sku_col or not name_col:
            os.remove(filepath)
            return jsonify({'error': 'Required columns SKU and Name not found'}), 400

        results = {'success': 0, 'failed': 0, 'errors': []}

        for index, row in df.iterrows():
            try:
                sku = str(row[sku_col]).strip() if pd.notna(row[sku_col]) else None
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None

                if not sku or not name:
                    results['failed'] += 1
                    results['errors'].append(f'Row {index + 2}: Missing SKU or Name')
                    continue

                price_col = find_column(df, column_mapping['Price'])
                stock_col = find_column(df, column_mapping['Current Stock'])
                min_col = find_column(df, column_mapping['Min Stock Level'])
                desc_col = find_column(df, column_mapping['Description'])

                price = float(row[price_col]) if price_col and pd.notna(row[price_col]) else 0.0
                current_stock = int(row[stock_col]) if stock_col and pd.notna(row[stock_col]) else 0
                min_stock_level = int(row[min_col]) if min_col and pd.notna(row[min_col]) else 5
                description = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ''

                existing = Product.query.filter_by(sku=sku).first()
                if existing:
                    existing.name = name
                    existing.price = price
                    existing.current_stock = current_stock
                    existing.min_stock_level = min_stock_level
                    existing.description = description
                else:
                    new_product = Product(
                        sku=sku, name=name, description=description,
                        price=price, current_stock=current_stock,
                        min_stock_level=min_stock_level
                    )
                    db.session.add(new_product)
                    db.session.flush()

                    if current_stock > 0:
                        transaction = StockTransaction(
                            product_id=new_product.id,
                            quantity=current_stock,
                            transaction_type='purchase',
                            notes='Initial stock from import'
                        )
                        db.session.add(transaction)

                db.session.commit()
                results['success'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f'Row {index + 2}: {str(e)}')

        os.remove(filepath)

        return jsonify({
            'success': True,
            'summary': {
                'total': results['success'] + results['failed'],
                'success': results['success'],
                'failed': results['failed']
            },
            'errors': results['errors']
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@main.route('/api/products/search', methods=['GET'])
@login_required
def search_products():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    # Search in name and description, case-insensitive
    products = Product.query.filter(
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.description.ilike(f'%{query}%'),
            Product.sku.ilike(f'%{query}%')
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': p.id,
        'sku': p.sku,
        'name': p.name,
        'description': p.description,
        'current_stock': p.current_stock,
        'price': p.price
    } for p in products])


@main.route('/api/products/sku/<string:sku>/adjust', methods=['POST'])
@admin_required
def adjust_stock_by_sku(sku):
    product = Product.query.filter_by(sku=sku).first()
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    data = request.json
    quantity = int(data.get('quantity', 0))
    transaction = StockTransaction(
        product_id=product.id,
        quantity=quantity,
        transaction_type=data.get('type', 'adjustment'),
        notes=data.get('notes', '')
    )
    product.current_stock += quantity
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'success': True, 'new_stock': product.current_stock, 'product': product.to_dict()})


@main.route('/api/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    if 'name' in data: product.name = data['name']
    if 'price' in data: product.price = float(data['price'])
    if 'min_stock_level' in data: product.min_stock_level = int(data['min_stock_level'])
    if 'description' in data: product.description = data['description']
    db.session.commit()
    return jsonify(product.to_dict())


@main.route('/api/products/<int:product_id>/history', methods=['GET'])
@login_required
def get_product_history(product_id):
    """Get transaction history for a specific product"""
    product = Product.query.get_or_404(product_id)
    
    transactions = StockTransaction.query.filter_by(product_id=product_id)\
        .order_by(StockTransaction.timestamp.desc())\
        .all()
    
    return jsonify([t.to_dict() for t in transactions])


@main.route('/api/products/<int:product_id>/min-level', methods=['PUT'])
@admin_required
def update_product_min_level(product_id):
    """Update the minimum stock level for a product"""
    product = Product.query.get_or_404(product_id)
    
    data = request.json
    new_min_level = int(data.get('min_stock_level', 0))
    
    if new_min_level < 0:
        return jsonify({'message': 'Minimum stock level cannot be negative'}), 400
    
    product.min_stock_level = new_min_level
    db.session.commit()
    
    return jsonify({
        'success': True,
        'product': product.to_dict()
    })


@main.route('/api/products/<int:product_id>/adjust', methods=['POST'])
@admin_required
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    quantity = int(data.get('quantity', 0))
    transaction = StockTransaction(
        product_id=product_id,
        quantity=quantity,
        transaction_type=data.get('type', 'adjustment'),
        notes=data.get('notes', '')
    )
    product.current_stock += quantity
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'success': True, 'new_stock': product.current_stock, 'product': product.to_dict()})


# ==================== STOCKTAKE ====================

@main.route('/api/stocktake', methods=['POST'])
@admin_required
def perform_stocktake():
    payload = request.json or {}
    counted_items = payload.get('items')
    if not isinstance(counted_items, list) or len(counted_items) == 0:
        return jsonify({'message': 'items must be a non-empty list'}), 400

    # Generate unique reference
    import uuid
    reference = f"ST-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    stocktake = StockTake(
        reference=reference,
        performed_by_id=request.user.id,
        status='completed',
        completed_at=datetime.utcnow()
    )
    db.session.add(stocktake)
    report_items = []

    for item in counted_items:
        sku = item.get('sku')
        counted_stock = int(item.get('counted_stock', 0))
        product = Product.query.filter_by(sku=sku).first()
        if not product:
            continue

        previous_stock = product.current_stock
        variance = counted_stock - previous_stock
        product.current_stock = counted_stock

        stocktake_item = StockTakeItem(
            stocktake=stocktake,
            product_id=product.id,
            system_count=previous_stock,
            physical_count=counted_stock,
            variance=variance
        )
        db.session.add(stocktake_item)
        db.session.add(StockTransaction(
            product_id=product.id,
            quantity=variance,
            transaction_type='stocktake',
            notes=f'Stocktake variance: {variance}'
        ))
        report_items.append(stocktake_item.to_dict())

    db.session.commit()
    
    # Generate variance report data
    total_variance = sum(item['variance'] for item in report_items)
    total_value_impact = sum(
        item['variance'] * Product.query.get(item['product_id']).price 
        for item in report_items
    )
    
    return jsonify({
        'success': True, 
        'stocktake': stocktake.to_dict(), 
        'items': report_items,
        'variance_report': {
            'total_items_counted': len(report_items),
            'total_variance': total_variance,
            'total_value_impact': total_value_impact,
            'report_url': f'/api/stocktake/{stocktake.id}/variance-report'
        }
    })


@main.route('/api/stocktake/<int:stocktake_id>/variance-report', methods=['GET'])
@login_required
def generate_variance_report(stocktake_id):
    stocktake = StockTake.query.get_or_404(stocktake_id)
    
    # Get all items for this stocktake
    items = StockTakeItem.query.filter_by(stocktake_id=stocktake_id).all()
    
    report_data = []
    total_variance = 0
    total_value_lost = 0
    total_value_gained = 0
    
    for item in items:
        variance = item.variance
        total_variance += variance
        
        # Calculate value impact (assuming we have price data)
        product = item.product
        if variance > 0:
            total_value_gained += variance * product.price
        elif variance < 0:
            total_value_lost += abs(variance) * product.price
            
        report_data.append({
            'SKU': product.sku,
            'Product Name': product.name,
            'Description': product.description or '',
            'System Count': item.system_count,
            'Physical Count': item.physical_count,
            'Variance': variance,
            'Variance %': f"{(variance / item.system_count * 100):.1f}%" if item.system_count > 0 else "N/A",
            'Unit Price': product.price,
            'Value Impact': variance * product.price
        })
    
    summary = {
        'stocktake_reference': stocktake.reference,
        'performed_by': stocktake.performed_by.username if stocktake.performed_by else 'Unknown',
        'completed_at': stocktake.completed_at.isoformat() if stocktake.completed_at else None,
        'total_items': len(items),
        'total_variance': total_variance,
        'total_value_gained': total_value_gained,
        'total_value_lost': total_value_lost,
        'net_value_impact': total_value_gained - total_value_lost
    }
    
    if request.args.get('format') == 'csv':
        output = io.StringIO()
        if report_data:
            writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'variance_report_{stocktake.reference}.csv'
        )
    
    return jsonify({
        'summary': summary,
        'items': report_data
    })


@main.route('/api/stocktake/reports', methods=['GET'])
@login_required
def get_stocktake_reports():
    stocktakes = StockTake.query.order_by(StockTake.completed_at.desc()).all()
    reports = []

    for st in stocktakes:
        items = StockTakeItem.query.filter_by(stocktake_id=st.id).all()
        total_variance = sum(item.variance for item in items) if items else 0

        reports.append({
            'id': st.id,
            'reference': st.reference,
            'timestamp': st.completed_at.isoformat() if st.completed_at else None,
            'performed_by': st.performed_by.username if st.performed_by else 'Unknown',
            'items': [item.to_dict() for item in items] if items else [],
            'total_variance': total_variance
        })

    return jsonify(reports)


@main.route('/api/stocktake/upload-excel', methods=['POST'])
@admin_required
def upload_stocktake_excel():
    """Bulk import stocktake data from Excel or CSV"""
    try:
        import pandas as pd
    except ImportError:
        return jsonify({'error': 'pandas not installed. Run: pip install pandas openpyxl'}), 500

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format. Use .xlsx, .xls, or .csv'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_excel(filepath)

        column_mapping = {
            'SKU': ['SKU', 'sku', 'Code', 'code', 'Product Code', 'Barcode'],
            'Counted Stock': ['Counted Stock', 'counted_stock', 'Physical Count', 'physical_count', 'Quantity', 'Count']
        }

        def find_column(df, possible_names):
            for col in possible_names:
                if col in df.columns:
                    return col
            return None

        sku_col = find_column(df, column_mapping['SKU'])
        count_col = find_column(df, column_mapping['Counted Stock'])

        if not sku_col or not count_col:
            os.remove(filepath)
            return jsonify({'error': 'Required columns SKU and Counted Stock not found'}), 400

        # Generate unique reference
        import uuid
        reference = f"ST-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        stocktake = StockTake(
            reference=reference,
            performed_by_id=request.user.id,
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(stocktake)

        results = {'success': 0, 'failed': 0, 'errors': []}
        report_items = []

        for index, row in df.iterrows():
            try:
                sku = str(row[sku_col]).strip() if pd.notna(row[sku_col]) else None
                counted_stock = int(row[count_col]) if pd.notna(row[count_col]) else 0

                if not sku:
                    results['failed'] += 1
                    results['errors'].append(f'Row {index + 2}: Missing SKU')
                    continue

                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    results['failed'] += 1
                    results['errors'].append(f'Row {index + 2}: Product with SKU "{sku}" not found')
                    continue

                previous_stock = product.current_stock
                variance = counted_stock - previous_stock
                product.current_stock = counted_stock

                stocktake_item = StockTakeItem(
                    stocktake=stocktake,
                    product_id=product.id,
                    system_count=previous_stock,
                    physical_count=counted_stock,
                    variance=variance
                )
                db.session.add(stocktake_item)

                if variance != 0:
                    transaction = StockTransaction(
                        product_id=product.id,
                        quantity=variance,
                        transaction_type='stocktake',
                        notes=f'Stocktake variance: {variance}'
                    )
                    db.session.add(transaction)

                report_items.append(stocktake_item.to_dict())
                results['success'] += 1

            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f'Row {index + 2}: {str(e)}')

        db.session.commit()
        os.remove(filepath)

        return jsonify({
            'success': True,
            'stocktake': stocktake.to_dict(),
            'summary': {
                'total': results['success'] + results['failed'],
                'success': results['success'],
                'failed': results['failed']
            },
            'errors': results['errors'],
            'items': report_items
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


# ==================== TRANSACTIONS ====================

@main.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    limit = request.args.get('limit', 100, type=int)
    transactions = StockTransaction.query.order_by(
        StockTransaction.timestamp.desc()
    ).limit(limit).all()
    return jsonify([t.to_dict() for t in transactions])


# ==================== REPORTS ====================

@main.route('/api/reports/stock-levels', methods=['GET'])
@login_required
def stock_levels_report():
    products = Product.query.all()
    report_data = [{
        'SKU': p.sku,
        'Product Name': p.name,
        'Current Stock': p.current_stock,
        'Min Stock Level': p.min_stock_level,
        'Status': 'LOW STOCK' if p.current_stock < p.min_stock_level else 'OK',
        'Price': p.price
    } for p in products]

    if request.args.get('format') == 'csv':
        output = io.StringIO()
        if report_data:
            writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='stock_report.csv'
        )

    return jsonify(report_data)


@main.route('/api/reports/variance', methods=['GET'])
@login_required
def variance_report():
    limit = request.args.get('limit', 10, type=int)
    takes = StockTake.query.order_by(StockTake.timestamp.desc()).limit(limit).all()
    return jsonify([st.to_dict() for st in takes])


@main.route('/api/reports/daily', methods=['GET'])
@login_required
def get_daily_reports():
    """List available daily reports"""
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    if not os.path.exists(reports_dir):
        return jsonify([])
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.startswith('daily_report_') and (filename.endswith('.pdf') or filename.endswith('.xlsx')):
            filepath = os.path.join(reports_dir, filename)
            reports.append({
                'filename': filename,
                'date': filename.split('_')[2].split('.')[0],  # Extract date from filename
                'type': 'PDF' if filename.endswith('.pdf') else 'Excel',
                'size': os.path.getsize(filepath),
                'url': f'/api/reports/daily/{filename}'
            })
    
    # Sort by date descending
    reports.sort(key=lambda x: x['date'], reverse=True)
    return jsonify(reports)


@main.route('/api/reports/daily/<filename>', methods=['GET'])
@login_required
def download_daily_report(filename):
    """Download a specific daily report"""
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    filepath = os.path.join(reports_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Report not found'}), 404
    
    # Security check - only allow daily report files
    if not filename.startswith('daily_report_'):
        return jsonify({'error': 'Invalid file'}), 403

    inline = request.args.get('inline', '0') == '1'
    if inline and filename.endswith('.pdf'):
        # Let browser display PDF inline for print-friendly rendering
        return send_file(filepath, mimetype='application/pdf', as_attachment=False, download_name=filename)

    return send_file(filepath, as_attachment=True)


# ==================== DASHBOARD ====================

@main.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.current_stock < Product.min_stock_level).count()
    total_value = db.session.query(
        db.func.sum(Product.current_stock * Product.price)
    ).scalar() or 0

    recent_transactions = StockTransaction.query.order_by(
        StockTransaction.timestamp.desc()
    ).limit(5).all()

    return jsonify({
        'total_products': total_products,
        'low_stock_items': low_stock,
        'total_inventory_value': total_value,
        'recent_transactions': [t.to_dict() for t in recent_transactions]
    })