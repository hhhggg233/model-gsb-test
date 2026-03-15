from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import User
from extensions import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email
    } for u in users])

@users_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if not current_user.is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'created_at': u.created_at.isoformat()
    } for u in users])

@users_bp.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_user(user_id):
    if not current_user.is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    user = User.query.get_or_404(user_id)
    
    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    
    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'password' in data:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})
