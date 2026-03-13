from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from cache import cache

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': '缺少必要字段'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': '邮箱已被注册'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        cache.delete(cache.get_users_list_cache_key())
        
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"注册错误: {e}")
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['username', 'password']):
            return jsonify({'error': '缺少用户名或密码'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 403
        
        access_token = create_access_token(identity=user.id)
        
        cache.set(cache.get_user_cache_key(user.id), user.to_dict())
        
        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'error': f'登录失败: {str(e)}'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        
        cached_user = cache.get(cache.get_user_cache_key(user_id))
        if cached_user:
            return jsonify({'user': cached_user}), 200
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        cache.set(cache.get_user_cache_key(user_id), user.to_dict())
        
        return jsonify({'user': user.to_dict()}), 200
    except Exception as e:
        print(f"获取用户信息错误: {e}")
        return jsonify({'error': f'获取用户信息失败: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        cache.delete(cache.get_user_cache_key(user_id))
        return jsonify({'message': '登出成功'}), 200
    except Exception as e:
        print(f"登出错误: {e}")
        return jsonify({'error': f'登出失败: {str(e)}'}), 500
