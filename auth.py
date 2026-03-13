from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User

def admin_required(fn):
    """管理员权限装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if not user.is_admin():
            return jsonify({'error': '权限不足，需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def login_required(fn):
    """登录验证装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if not user.is_active:
            return jsonify({'error': '用户已被禁用'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
