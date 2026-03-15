from flask_login import current_user
from flask_socketio import emit
from models import Message
from extensions import db

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            print(f"User {current_user.username} connected to chat")

    @socketio.on('send_message')
    def handle_message(data):
        if not current_user.is_authenticated:
            return
        
        message = Message(
            sender_id=current_user.id,
            receiver_id=data['receiver_id'],
            content=data['content']
        )
        db.session.add(message)
        db.session.commit()
        
        emit('receive_message', {
            'id': message.id,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'receiver_id': data['receiver_id'],
            'content': data['content'],
            'created_at': message.created_at.isoformat()
        }, broadcast=True)
