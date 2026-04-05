from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from models import db, User, FinancialRecord
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'dev_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper function for role-based access control
def check_auth(allowed_roles=None):
    if 'user_id' not in session:
        return False, "Unauthorized: Please login."
    if allowed_roles and session.get('role') not in allowed_roles:
        return False, f"Access Denied: Requires {allowed_roles} role."
    return True, None

# ==========================================
# SEED DATA FUNCTION
# ==========================================
def seed_data():
    if not User.query.first():
        u1 = User(name='Admin User', email='admin@example.com', role='Admin')
        u2 = User(name='Analyst User', email='analyst@example.com', role='Analyst')
        u3 = User(name='Viewer User', email='viewer@example.com', role='Viewer')
        db.session.add_all([u1, u2, u3])
        db.session.commit()

    if not FinancialRecord.query.first():
        # Add some sample records
        categories = {
            'income': ['Salary', 'Freelance', 'Investment'],
            'expense': ['Food', 'Rent', 'Travel', 'Bills', 'Entertainment']
        }
        
        for i in range(25):
            r_type = random.choice(['income', 'expense'])
            r_cat = random.choice(categories[r_type])
            r_amt = round(random.uniform(20.0, 500.0 if r_type == 'expense' else 3000.0), 2)
            # Create varied dates
            days_ago = random.randint(0, 60)
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            rec = FinancialRecord(
                amount=r_amt,
                type=r_type,
                category=r_cat,
                date=date_str,
                description=f"Initial {r_cat} {r_type} data point"
            )
            db.session.add(rec)
        
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_data()

# ==========================================
# FRONTEND VIEW ROUTES
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    users = User.query.all()
    return render_template('login.html', users=users)

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if user:
        session['user_id'] = user.id
        session['role'] = user.role
        session['name'] = user.name
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard_page():
    ok, err = check_auth()
    if not ok: return redirect(url_for('index'))
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/records')
def records_page():
    ok, err = check_auth()
    if not ok: return redirect(url_for('index'))
    return render_template('records.html', active_page='records')

@app.route('/add-record')
def add_record_page():
    ok, err = check_auth(['Admin'])
    if not ok: return "Access Denied", 403
    return render_template('add_record.html', active_page='add-record')

@app.route('/edit-record/<int:id>')
def edit_record_page(id):
    ok, err = check_auth(['Admin'])
    if not ok: return "Access Denied", 403
    record = FinancialRecord.query.get_or_404(id)
    return render_template('edit_record.html', record=record, active_page='records')

# ==========================================
# API ROUTES
# ==========================================

@app.route('/api/records/<int:id>', methods=['GET'])
def api_get_record(id):
    ok, err = check_auth(['Admin'])
    if not ok: return jsonify({'error': err}), 403
    r = FinancialRecord.query.get_or_404(id)
    return jsonify({
        'id': r.id, 'amount': r.amount, 'type': r.type, 
        'category': r.category, 'date': r.date, 'description': r.description
    })

@app.route('/api/records/<int:id>', methods=['PUT'])
def api_update_record(id):
    ok, err = check_auth(['Admin'])
    if not ok: return jsonify({'error': err}), 403
    
    rec = FinancialRecord.query.get_or_404(id)
    data = request.json
    try:
        amt = float(data.get('amount', rec.amount))
        if amt <= 0: return jsonify({'error': 'Amount must be positive'}), 400
        
        rec.amount = amt
        rec.type = data.get('type', rec.type)
        rec.category = data.get('category', rec.category)
        rec.date = data.get('date', rec.date)
        rec.description = data.get('description', rec.description)
        
        db.session.commit()
        return jsonify({'message': 'Record updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/summary')
def api_summary():
    ok, err = check_auth(['Admin', 'Analyst'])
    if not ok: return jsonify({'error': err}), 403
    
    records = FinancialRecord.query.all()
    
    total_income = sum(r.amount for r in records if r.type == 'income')
    total_expense = sum(r.amount for r in records if r.type == 'expense')
    
    # Category break down for Chart.js
    category_data = {}
    for r in records:
        if r.type == 'expense':
            category_data[r.category] = category_data.get(r.category, 0) + r.amount
            
    # Recent items
    recent = FinancialRecord.query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).limit(10).all()
    
    return jsonify({
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'net_balance': round(total_income - total_expense, 2),
        'category_data': category_data,
        'recent': [{
            'id': r.id, 'amount': r.amount, 'type': r.type, 
            'category': r.category, 'date': r.date, 'description': r.description
        } for r in recent]
    })

@app.route('/api/records')
def api_get_records():
    ok, err = check_auth()
    if not ok: return jsonify({'error': err}), 403
    
    # Filtering & Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    r_type = request.args.get('type')
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = FinancialRecord.query
    if r_type:
        query = query.filter(FinancialRecord.type == r_type)
    if category:
        query = query.filter(FinancialRecord.category == category)
    if search:
        query = query.filter(FinancialRecord.description.ilike(f"%{search}%"))
        
    pagination = query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'records': [{
            'id': r.id, 'amount': r.amount, 'type': r.type, 
            'category': r.category, 'date': r.date, 'description': r.description
        } for r in pagination.items],
        'total_pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@app.route('/api/records', methods=['POST'])
def api_create_record():
    ok, err = check_auth(['Admin'])
    if not ok: return jsonify({'error': err}), 403
    
    data = request.json
    try:
        amt = float(data.get('amount', 0))
        if amt <= 0: return jsonify({'error': 'Amount must be positive'}), 400
        
        new_r = FinancialRecord(
            amount=amt,
            type=data.get('type'),
            category=data.get('category'),
            date=data.get('date'),
            description=data.get('description', '')
        )
        db.session.add(new_r)
        db.session.commit()
        return jsonify({'message': 'Record added!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/records/<int:id>', methods=['DELETE'])
def api_delete_record(id):
    ok, err = check_auth(['Admin'])
    if not ok: return jsonify({'error': err}), 403
    
    rec = FinancialRecord.query.get_or_404(id)
    db.session.delete(rec)
    db.session.commit()
    return jsonify({'message': 'Deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
