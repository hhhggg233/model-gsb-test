from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Message
from cache import cache

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    sender_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not all(k in data for k in ['receiver_id', 'content']):
        return jsonify({'error': '缺少必要字段'}), 400
    
    receiver_id = data['receiver_id']
    
    if sender_id == receiver_id:
        return jsonify({'error': '不能给自己发送消息'}), 400
    
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'error': '接收者不存在'}), 404
    
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=data['content']
    )
    
    db.session.add(message)
    db.session.commit()
    
    cache.delete(cache.get_messages_cache_key(sender_id))
    cache.delete(cache.get_messages_cache_key(receiver_id))
    
    return jsonify({
        'message': '发送成功',
        'data': message.to_dict()
    }), 201

@chat_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    user_id = get_jwt_identity()
    other_user_id = request.args.get('user_id', type=int)
    
    cached_messages = cache.get(cache.get_messages_cache_key(user_id))
    if cached_messages and not other_user_id:
        return jsonify({'messages': cached_messages}), 200
    
    query = Message.query.filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc())
    
    if other_user_id:
        query = query.filter(
            (Message.sender_id == other_user_id) | (Message.receiver_id == other_user_id)
        )
    
    messages = query.all()
    messages_dict = [msg.to_dict() for msg in messages]
    
    if not other_user_id:
        cache.set(cache.get_messages_cache_key(user_id), messages_dict)
    
    return jsonify({'messages': messages_dict}), 200

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = get_jwt_identity()
    
    sent = db.session.query(
        Message.receiver_id, User.username
    ).join(User, Message.receiver_id == User.id).filter(
        Message.sender_id == user_id
    ).distinct()
    
    received = db.session.query(
        Message.sender_id, User.username
    ).join(User, Message.sender_id == User.id).filter(
        Message.receiver_id == user_id
    ).distinct()
    
    conversations = {}
    for user_id_conv, username in sent:
        conversations[user_id_conv] = username
    for user_id_conv, username in received:
        conversations[user_id_conv] = username
    
    return jsonify({
        'conversations': [{'user_id': uid, 'username': name} for uid, name in conversations.items()]
    }), 200

@chat_bp.route('/read/<int:message_id>', methods=['PUT'])
@jwt_required()
def mark_as_read(message_id):
    user_id = get_jwt_identity()
    
    message = Message.query.get(message_id)
    if not message:
        return jsonify({'error': '消息不存在'}), 404
    
    if message.receiver_id != user_id:
        return jsonify({'error': '无权操作'}), 403
    
    message.is_read = True
    db.session.commit()
    
    cache.delete(cache.get_messages_cache_key(user_id))
    
    return jsonify({'message': '已标记为已读'}), 200

@chat_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    user_id = get_jwt_identity()
    count = Message.query.filter_by(receiver_id=user_id, is_read=False).count()
    return jsonify({'unread_count': count}), 200
