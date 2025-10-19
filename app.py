from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os

app = Flask(__name__, template_folder='.')  # Templates in root directory
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'c0c78d70edc4268cd0bf114c825907d21258f8c2d85522af08b78a09a820b951')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')  # user, creator, admin
    referral_code = db.Column(db.String(36), unique=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved = db.Column(db.Boolean, default=False)  # For creators

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.referral_code = str(uuid.uuid4())

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))  # bot, userbot, website, app, coding
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    demo_url = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create DB
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', password=generate_password_hash('adminpass'), role='admin', approved=True)
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')  # No variables passed, Vue handles user data

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    referral_code = data.get('referral_code')
    referred_by = None
    if referral_code:
        referrer = User.query.filter_by(referral_code=referral_code).first()
        if referrer:
            referred_by = referrer.id
    new_user = User(username=data['username'], email=data['email'], password=hashed_password, referred_by=referred_by)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({'message': 'Logged in', 'role': user.role, 'approved': user.approved, 'username': user.username})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({'role': current_user.role, 'approved': current_user.approved, 'username': current_user.username})

@app.route('/api/request_creator', methods=['POST'])
@login_required
def request_creator():
    if current_user.role == 'user':
        current_user.role = 'creator'
        current_user.approved = False
        db.session.commit()
        return jsonify({'message': 'Request sent for approval'})
    return jsonify({'message': 'Already creator or admin'}), 400

@app.route('/api/admin/approve_creator/<int:user_id>', methods=['POST'])
@login_required
def approve_creator(user_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    user = User.query.get(user_id)
    if user:
        user.approved = True
        db.session.commit()
        return jsonify({'message': 'Approved'})
    return jsonify({'message': 'User not found'}), 404

@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def products():
    if request.method == 'POST':
        if current_user.role != 'creator' or not current_user.approved:
            return jsonify({'message': 'Unauthorized'}), 403
        data = request.json
        new_product = Product(name=data['name'], description=data['description'], price=data['price'], type=data['type'], creator_id=current_user.id, demo_url=data.get('demo_url'))
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': 'Product added'}), 201
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description, 'price': p.price, 'type': p.type, 'demo_url': p.demo_url} for p in products])

@app.route('/api/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role, 'approved': u.approved} for u in users])

@app.route('/api/referral')
@login_required
def referral():
    return jsonify({'referral_code': current_user.referral_code, 'referral_link': f'https://{request.host}/signup?ref={current_user.referral_code}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
