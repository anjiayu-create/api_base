import json
import os
import hashlib
from config import DATA_DIR, USER_STORAGE_PATH, ARTICLE_STORAGE_PATH, INIT_USERS

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

# 初始化数据目录
os.makedirs(DATA_DIR, exist_ok=True)

# 通用存储类
class SimpleStorage:
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False)

    def read(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

# 初始化存储实例
user_storage = SimpleStorage(USER_STORAGE_PATH)
article_storage = SimpleStorage(ARTICLE_STORAGE_PATH)

def init_users():
    """仅当用户列表为空时，初始化预设用户（彻底解决KeyError）"""
    users = user_storage.read()
    # 只有用户列表为空时，才初始化预设用户
    if not users:
        # 深拷贝INIT_USERS，避免修改原配置
        init_users_list = [u.copy() for u in INIT_USERS]
        for user in init_users_list:
            # 检查是否有password字段（防止配置错误）
            if "password" not in user:
                continue
            # 生成盐值+加密密码
            salt = os.urandom(16).hex()
            pwd_hash = pbkdf2_hex(
                data=user["password"].encode("utf-8"),
                salt=salt.encode("utf-8"),
                iterations=10000,
                dklen=64
            )
            user["salt"] = salt
            user["hash"] = pwd_hash
            del user["password"]  # 删除明文密码
        # 写入初始化用户
        user_storage.write(init_users_list)
    # 非空则跳过初始化（避免KeyError）
    else:
        print("用户数据已存在，跳过初始化")

def get_next_article_id():
    """获取下一个文章ID"""
    articles = article_storage.read()
    return max([art["id"] for art in articles], default=0) + 1

# 仅在直接运行storage.py时初始化（避免导入时执行）
if __name__ == "__main__":
    init_users()