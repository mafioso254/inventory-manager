from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0.0)
    current_stock = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'barcode': self.barcode,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'current_stock': self.current_stock,
            'min_stock_level': self.min_stock_level,
            'status': 'LOW' if self.current_stock < self.min_stock_level else 'OK'
        }

class StockTransaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # positive = stock in, negative = stock out
    transaction_type = db.Column(db.String(20))  # 'purchase', 'sale', 'adjustment', 'return', 'stocktake', 'transfer'
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to product
    product = db.relationship('Product', backref='transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'transaction_type': self.transaction_type,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }


class StockTake(db.Model):
    __tablename__ = 'stocktakes'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'cancelled'
    notes = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    performed_by = db.relationship('User', backref='stocktakes')
    items = db.relationship('StockTakeItem', backref='stocktake', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'reference': self.reference,
            'performed_by': self.performed_by.username if self.performed_by else None,
            'status': self.status,
            'notes': self.notes,
            'timestamp': self.started_at.isoformat() if self.started_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_items': len(self.items),
            'items': [item.to_dict() for item in self.items]
        }


class StockTakeItem(db.Model):
    __tablename__ = 'stocktake_items'

    id = db.Column(db.Integer, primary_key=True)
    stocktake_id = db.Column(db.Integer, db.ForeignKey('stocktakes.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    system_count = db.Column(db.Integer, nullable=False)  # Current stock in system
    physical_count = db.Column(db.Integer, default=0)  # Counted during stock take
    variance = db.Column(db.Integer, default=0)  # physical_count - system_count

    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sku': self.product.sku if self.product else None,
            'barcode': self.product.sku if self.product else None,  # Using SKU as barcode for now
            'system_count': self.system_count,
            'physical_count': self.physical_count,
            'variance': self.variance
        }
