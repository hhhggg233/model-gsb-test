from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, login_required, logout_user, current_user
from models import User
from extensions import db
from utils import is_valid_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    if not is_valid_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'email': user.email
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/api/current_user', methods=['GET'])
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'email': current_user.email
        })
    return jsonify({'error': 'Not logged in'}), 401
