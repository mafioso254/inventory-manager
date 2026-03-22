#!/usr/bin/env python
"""
Inventory Manager - Production Server with Waitress
Run this script to start the inventory management system
"""

import os
import sys

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from waitress import serve
from app import create_app
from werkzeug.security import generate_password_hash
import os

# Create the Flask app
app = create_app()

# Ensure database exists
with app.app_context():
    from app.models import db, User
    from sqlalchemy import text
    db.create_all()

    # Migration: Add barcode column if it doesn't exist
    try:
        db.session.execute(text("ALTER TABLE products ADD COLUMN barcode VARCHAR(100)"))
        db.session.commit()
        print("Added barcode column to products table")
    except Exception as e:
        # Column might already exist, ignore error
        db.session.rollback()
        pass

    admin_username = 'admin-Mwangi'
    admin_password = os.environ.get('ADMIN_MWANGI_PASSWORD', 'ChangeMe123!')

    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin = User(
            username=admin_username,
            password_hash=generate_password_hash(admin_password),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✓ Created admin user '{admin_username}' (change password ASAP)")
    else:
        print(f"✓ Admin user '{admin_username}' already exists")

    print("✓ Database initialized")

if __name__ == '__main__':
    # Get port from environment variable (for deployment)
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("=" * 50)
    print("📦 Inventory Manager v1.0")
    print("=" * 50)
    print(f"🚀 Server starting on http://{host}:{port}")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)
    
    # Start Waitress server
    serve(app, host=host, port=port, threads=4)
    
    