import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USE_MYSQL = False
    
    if USE_MYSQL:
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123123@localhost/gsb_db'
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///gsb.db'
