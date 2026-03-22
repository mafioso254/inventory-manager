from flask import Flask
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for local development
        basedir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.join(basedir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "inventory.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    # Register routes
    from app.routes import main
    app.register_blueprint(main)
    
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    
    # Import the report function here to avoid circular imports
    from app.reports import generate_daily_report
    
    # Schedule daily report at 00:00
    scheduler.add_job(
        func=generate_daily_report,
        trigger=CronTrigger(hour=0, minute=0),
        id='daily_report',
        name='Generate Daily Transaction Report',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    
    # Store scheduler in app for potential shutdown
    app.scheduler = scheduler
    
    return app
