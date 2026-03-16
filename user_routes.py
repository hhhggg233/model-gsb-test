from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from cache import cache
from permissions import admin_required

user_bp = Blueprint('user', __name__, url_prefix='/api/users')

@user_bp.route('', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    try:
        cached_users = cache.get(cache.get_users_list_cache_key())
        if cached_users:
            return jsonify({'users': cached_users}), 200
        
        users = User.query.all()
        users_dict = [user.to_dict() for user in users]
        
        cache.set(cache.get_users_list_cache_key(), users_dict)
        
        return jsonify({'users': users_dict}), 200
    except Exception as e:
        print(f"获取用户列表错误: {e}")
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user.is_admin() and current_user_id != user_id:
            return jsonify({'error': '无权查看'}), 403
        
        cached_user = cache.get(cache.get_user_cache_key(user_id))
        if cached_user:
            return jsonify({'user': cached_user}), 200
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        print(f"获取用户错误: {e}")
        return jsonify({'error': f'获取用户失败: {str(e)}'}), 500

@user_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user.is_admin() and current_user_id != user_id:
            return jsonify({'error': '无权修改'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        data = request.get_json()
        
        if current_user.is_admin() and 'role' in data:
            user.role = data['role']
        
        if current_user.is_admin() and 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'email' in data:
            existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing:
                return jsonify({'error': '邮箱已被使用'}), 400
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        cache.delete(cache.get_user_cache_key(user_id))
        cache.delete(cache.get_users_list_cache_key())
        
        return jsonify({
            'message': '更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"更新用户错误: {e}")
        return jsonify({'error': f'更新用户失败: {str(e)}'}), 500

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        
        if current_user_id == user_id:
            return jsonify({'error': '不能删除自己'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        cache.delete(cache.get_user_cache_key(user_id))
        cache.delete(cache.get_users_list_cache_key())
        
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"删除用户错误: {e}")
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500
