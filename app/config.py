import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env (ใช้ตอนรันใน local)
load_dotenv()


class Config:
    """🔧 Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """🧩 Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@db:5432/todo_dev'
    ).strip()


class TestingConfig(Config):
    """🧪 Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """🚀 Production configuration"""
    DEBUG = False

    # ✅ ลบช่องว่างเกินใน DATABASE_URL ป้องกัน error 'database "railway " does not exist'
    db_url = os.getenv('DATABASE_URL', '').strip()

    # ✅ ตรวจสอบความถูกต้องของ URL
    if not db_url.startswith('postgresql://'):
        raise ValueError("Invalid DATABASE_URL: must start with 'postgresql://'")

    SQLALCHEMY_DATABASE_URI = db_url

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Production-specific initialization
        assert os.getenv('DATABASE_URL'), 'DATABASE_URL must be set in production'


# ✅ ใช้ dictionary สำหรับเลือก config ตาม environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
