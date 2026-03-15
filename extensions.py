from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
import redis

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")
cors = CORS()
r = None

def init_redis():
    global r
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("Redis connected successfully")
    except:
        r = None
        print("Redis connection failed, caching disabled")
