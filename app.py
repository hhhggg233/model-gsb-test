import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import Config
from models import db, User, Message
from redis_client import redis_client
from auth import admin_required, login_required

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

db.init_app(app)

with app.app_context():
    db.create_all()
    # 创建默认管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('默认管理员用户已创建: admin/admin123')

@app.route('/')
def index():
    return render_template('index.html')

# ==================== 认证相关API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': '缺少必要字段'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 409
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已存在'}), 409
    
    # 创建新用户
    user = User(
        username=data['username'],
        email=data['email'],
        role='user'  # 默认普通用户
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({'error': '缺少用户名或密码'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'error': '用户已被禁用'}), 403
    
    # 创建JWT令牌
    access_token = create_access_token(identity=user.id)
    
    # 缓存用户信息
    redis_client.cache_user(user.id, user.to_dict())
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': user.to_dict()
    })

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前登录用户信息"""
    current_user_id = get_jwt_identity()
    
    # 先尝试从缓存获取
    cached_user = redis_client.get_cached_user(current_user_id)
    if cached_user:
        return jsonify(cached_user)
    
    user = User.query.get_or_404(current_user_id)
    
    # 缓存用户信息
    redis_client.cache_user(user.id, user.to_dict())
    
    return jsonify(user.to_dict())

# ==================== 用户管理API（管理员权限） ====================

@app.route('/api/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户（仅管理员）"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """获取指定用户信息（仅管理员）"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户信息（仅管理员）"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    
    # 更新缓存
    redis_client.cache_user(user.id, user.to_dict())
    
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（仅管理员）"""
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    current_user_id = get_jwt_identity()
    if user.id == current_user_id:
        return jsonify({'error': '不能删除当前登录用户'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    # 清除缓存
    redis_client.invalidate_user_cache(user.id)
    
    return jsonify({'message': '用户删除成功'})

@app.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """切换用户状态（启用/禁用）"""
    user = User.query.get_or_404(user_id)
    
    current_user_id = get_jwt_identity()
    if user.id == current_user_id:
        return jsonify({'error': '不能禁用自己'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    # 更新缓存
    redis_client.cache_user(user.id, user.to_dict())
    
    return jsonify({
        'message': f'用户已{"启用" if user.is_active else "禁用"}',
        'user': user.to_dict()
    })

# ==================== 聊天相关API ====================

@app.route('/api/users/list', methods=['GET'])
@jwt_required()
def get_users_list():
    """获取用户列表（用于聊天）"""
    current_user_id = get_jwt_identity()
    users = User.query.filter(User.id != current_user_id, User.is_active == True).all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/messages/<int:user_id>', methods=['GET'])
@jwt_required()
def get_messages(user_id):
    """获取与指定用户的聊天记录"""
    current_user_id = get_jwt_identity()
    
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.created_at.asc()).all()
    
    # 标记消息为已读
    unread_messages = Message.query.filter_by(
        sender_id=user_id, 
        receiver_id=current_user_id, 
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/messages/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读消息数量"""
    current_user_id = get_jwt_identity()
    
    count = Message.query.filter_by(
        receiver_id=current_user_id,
        is_read=False
    ).count()
    
    return jsonify({'unread_count': count})

# ==================== WebSocket 事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端已断开连接')

@socketio.on('join')
def handle_join(data):
    """用户加入聊天室"""
    user_id = data.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        join_room(room)
        redis_client.set_user_online(user_id)
        emit('user_online', {'user_id': user_id}, broadcast=True)
        print(f'用户 {user_id} 加入房间 {room}')

@socketio.on('leave')
def handle_leave(data):
    """用户离开聊天室"""
    user_id = data.get('user_id')
    if user_id:
        room = f'user_{user_id}'
        leave_room(room)
        redis_client.set_user_offline(user_id)
        emit('user_offline', {'user_id': user_id}, broadcast=True)
        print(f'用户 {user_id} 离开房间 {room}')

@socketio.on('send_message')
def handle_send_message(data):
    """处理发送消息"""
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not all([sender_id, receiver_id, content]):
        emit('error', {'message': '缺少必要字段'})
        return
    
    # 保存消息到数据库
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    # 发送给接收者
    receiver_room = f'user_{receiver_id}'
    emit('new_message', message.to_dict(), room=receiver_room)
    
    # 发送给发送者（确认消息已发送）
    sender_room = f'user_{sender_id}'
    emit('message_sent', message.to_dict(), room=sender_room)
    
    print(f'消息从 {sender_id} 发送到 {receiver_id}')

@socketio.on('typing')
def handle_typing(data):
    """处理正在输入状态"""
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    
    if sender_id and receiver_id:
        receiver_room = f'user_{receiver_id}'
        emit('user_typing', {
            'sender_id': sender_id,
            'sender_username': data.get('sender_username')
        }, room=receiver_room)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
