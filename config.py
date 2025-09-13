"""
إعدادات التطبيق المركزية
"""
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class Config:
    """الإعدادات الأساسية للتطبيق"""
    
    # إعدادات Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 3000))
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///osint_toolkit.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # مفاتيح API
    HIBP_API_KEY = os.environ.get('HIBP_API_KEY')
    HUNTER_API_KEY = os.environ.get('HUNTER_API_KEY')
    LEAKCHECK_API_KEY = os.environ.get('LEAKCHECK_API_KEY')
    CLEARBIT_API_KEY = os.environ.get('CLEARBIT_API_KEY')
    
    # إعدادات Rate Limiting
    RATELIMIT_PER_MINUTE = int(os.environ.get('RATELIMIT_PER_MINUTE', 30))
    RATELIMIT_PER_HOUR = int(os.environ.get('RATELIMIT_PER_HOUR', 500))
    
    # إعدادات CORS
    ENABLE_CORS = os.environ.get('ENABLE_CORS', 'True').lower() == 'true'
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    
    # إعدادات التقارير
    REPORTS_DIRECTORY = os.environ.get('REPORTS_DIRECTORY', './reports')
    MAX_REPORT_SIZE_MB = int(os.environ.get('MAX_REPORT_SIZE_MB', 50))
    
    # إعدادات اللغة
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'ar')
    SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'ar,en').split(',')
    
    # إعدادات الأمان
    SESSION_TIMEOUT = 3600  # ساعة واحدة
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # إعدادات Cache
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 دقائق

class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True
    
class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    
class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# تحديد الإعدادات بناءً على البيئة
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}