import os


class Config:
    DEBUG = False
    TESTING = False
    
    SQLALCHEMY_TRACK_MODIFICATION = False
    
    JWT_ERROR_MESSAGE_KEY = 'JWT token error'

    UPLOADED_IMAGES_DEST = 'static/images'
    
    MAX_CONTENT_LENGTH = 10*1024*1024
    
    CACHE_TYPE="SimpleCache"
    CACHE_DEFAULT_TIMEOUT=10*60
    
    RATELIMIT_HEADERS_ENABLED=True


class ProductionConfig(Config):

    SECRET_KEY= os.environ.get('SECRET_KEY')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')


class DevelopmentConfig(Config):

    DEBUG = True
    SECRET_KEY='some complex text for debugging must be written here'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')


class StagingConfig(Config):

    TESTING = True
    SECRET_KEY= os.environ.get('SECRET_KEY')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    