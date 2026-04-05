from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Viewer') # Admin, Analyst, Viewer
    status = db.Column(db.String(50), default='active')

class FinancialRecord(db.Model):
    __tablename__ = 'financial_records'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False) # e.g. 'income' or 'expense'
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False) # Storing as YYYY-MM-DD string for simplicity
    description = db.Column(db.String(255), nullable=True)
