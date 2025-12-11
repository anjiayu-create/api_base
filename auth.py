import jwt
import hashlib
from datetime import datetime, timedelta
from flask import request, session, jsonify, Response
from config import JWT_SECRET_KEY, JWT_EXPIRES

# 修复：原生pbkdf2_hex实现（匹配Python3.13标准库）
def pbkdf2_hex(data, salt, iterations=10000, dklen=64, digest=None):
    if digest is None:
        digest = hashlib.sha256
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

# 生成Token（仅用于身份认证，有效期2小时）
def generate_token(user_id, username):
    expire = datetime.utcnow() + timedelta(hours=2)  # 明确2小时有效期
    token = jwt.encode(
        {"sub": user_id, "username": username, "exp": expire},
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    return token.decode("utf-8") if isinstance(token, bytes) else token

# 核心鉴权：严格分离Token（身份）+ Session（会话）双重校验
def auth_validate():
    # 1. 校验Token（仅从Authorization请求头获取，身份认证）
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"code": 401, "msg": "未提供有效身份认证Token"}), 401
    token = auth_header.replace("Bearer ", "")
    if not token:
        return jsonify({"code": 401, "msg": "身份认证Token不能为空"}), 401

    # 验证Token有效性
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"code": 401, "msg": "身份认证Token已过期"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"code": 401, "msg": "身份认证Token无效/被篡改"}), 401

    # 2. 校验Session（仅从服务端Session校验，会话保持）
    if not session.get("username"):
        return jsonify({"code": 401, "msg": "登录会话已失效，请重新登录"}), 401
    # 关键：Token中的用户与Session中的用户必须匹配
    if payload["username"] != session["username"]:
        return jsonify({"code": 401, "msg": "身份认证与登录会话不匹配"}), 401

    # 3. 校验通过，返回用户信息
    return payload

# 登录装饰器（无改动，仅依赖强化后的auth_validate）
def login_required(f):
    def wrapper(*args, **kwargs):
        validate_result = auth_validate()
        if isinstance(validate_result, tuple):
            return validate_result
        kwargs["user_info"] = validate_result
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper