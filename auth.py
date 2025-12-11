import jwt
import hashlib
from datetime import datetime
from flask import request, session, jsonify, Response  # 新增：导入Response类型
from config import JWT_SECRET_KEY, JWT_EXPIRES

# 修复：原生pbkdf2_hex实现（匹配Python3.13标准库）
def pbkdf2_hex(data, salt, iterations=10000, dklen=64, digest=None):
    if digest is None:
        digest = hashlib.sha256
    # 正确参数：hash_name, password, salt, iterations, dklen
    pbkdf2 = hashlib.pbkdf2_hmac(
        hash_name=digest().name,
        password=data,
        salt=salt,
        iterations=iterations,
        dklen=dklen
    )
    return pbkdf2.hex()

# 验证密码（依赖storage的user_storage，延迟导入）
def verify_password(username, password):
    from storage import user_storage  # 延迟导入，避免循环依赖
    users = user_storage.read()
    for user in users:
        if user["username"] == username:
            # 校验密码
            pwd_hash = pbkdf2_hex(
                data=password.encode("utf-8"),
                salt=user["salt"].encode("utf-8"),
                iterations=10000,
                dklen=64
            )
            return user if pwd_hash == user["hash"] else None
    return None

# 生成Token
def generate_token(user_id, username):
    expire = datetime.utcnow() + JWT_EXPIRES
    token = jwt.encode(
        {"sub": user_id, "username": username, "exp": expire},
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    return token.decode("utf-8") if isinstance(token, bytes) else token

# 验证Token+Session
def auth_validate():
    # 获取Token
    header_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    cookie_token = request.cookies.get("token")
    if not header_token or not cookie_token or header_token != cookie_token:
        return jsonify({"code": 401, "msg": "未登录或Token失效"}), 401

    # 验证Token
    try:
        payload = jwt.decode(header_token, JWT_SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        return jsonify({"code": 401, "msg": f"Token失效：{str(e)}"}), 401

    # 验证Session
    if session.get("username") != payload["username"]:
        return jsonify({"code": 401, "msg": "登录态失效，请重新登录"}), 401

    return payload  # 正确返回payload（dict），错误时返回 (Response, 状态码)

# 修复：login_required装饰器（核心解决TypeError）
def login_required(f):
    def wrapper(*args, **kwargs):
        validate_result = auth_validate()
        # 正确判断：错误时返回的是 (Response对象, 状态码) 元组
        if isinstance(validate_result, tuple):
            return validate_result
        # 正常时将payload传入视图函数
        kwargs["user_info"] = validate_result
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper