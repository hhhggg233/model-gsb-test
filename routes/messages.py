from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Message
from extensions import db

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/api/messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.read:
            msg.read = True
    db.session.commit()
    
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_username': m.sender.username,
        'receiver_id': m.receiver_id,
        'content': m.content,
        'created_at': m.created_at.isoformat(),
        'read': m.read
    } for m in messages])
