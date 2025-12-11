import os
from datetime import timedelta

# -------------------------- 安全配置 --------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_123456")  # Session加密
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_654321")  # JWT加密
JWT_EXPIRES = timedelta(hours=2)  # Token过期时间
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Session过期时间

# -------------------------- 业务规则（接口串联依赖） --------------------------
ARTICLE_TITLE_MIN_LEN = 2
ARTICLE_TITLE_MAX_LEN = 50
ARTICLE_CONTENT_MIN_LEN = 5
ARTICLE_CONTENT_MAX_LEN = 5000

# -------------------------- 存储配置（轻量化） --------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USER_STORAGE_PATH = os.path.join(DATA_DIR, "users.json")
ARTICLE_STORAGE_PATH = os.path.join(DATA_DIR, "articles.json")

# -------------------------- 预设测试用户 --------------------------
INIT_USERS = [
    {"id": 1, "username": "admin", "password": "Admin@123456", "salt": "", "hash": ""},
    {"id": 2, "username": "test", "password": "Test@123456", "salt": "", "hash": ""}
]