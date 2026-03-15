from flask import Flask
from config import Config
from extensions import db, login_manager, socketio, cors, init_redis, r
from models import User
from socket_events import register_socketio_events

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    cors.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app)
    
    init_redis()
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.persons import persons_bp
    from routes.messages import messages_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(messages_bp)
    
    register_socketio_events(socketio)
    
    return app

def init_db(app):
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")

if __name__ == '__main__':
    app = create_app()
    init_db(app)
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
