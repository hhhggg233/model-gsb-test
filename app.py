from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, emit, join_room, leave_room
from config import Config
from models import db, User, Message
from cache import cache
from auth import auth_bp
from user_routes import user_bp
from chat import chat_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
cache.init_app(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(chat_bp)

with app.app_context():
    try:
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("默认管理员账户已创建: admin / admin123")
        else:
            print("管理员账户已存在")
    except Exception as e:
        print(f"数据库初始化错误: {e}")
        db.session.rollback()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join')
def on_join(data):
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        join_room(room)
        print(f"User {user_id} joined room {room}")

@socketio.on('leave')
def on_leave(data):
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        leave_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not all([sender_id, receiver_id, content]):
        emit('error', {'message': '缺少必要字段'})
        return
    
    try:
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        message_data = message.to_dict()
        
        emit('new_message', message_data, room=f"user_{receiver_id}")
        emit('message_sent', message_data)
    except Exception as e:
        print(f"发送消息错误: {e}")
        db.session.rollback()
        emit('error', {'message': '发送失败'})

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token已过期', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': '无效的Token', 'code': 'TOKEN_INVALID'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': '缺少Token', 'code': 'TOKEN_MISSING'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '资源不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    print("启动服务器...")
    print("访问 http://localhost:5000")
    socketio.run(app, debug=True, port=5000)
