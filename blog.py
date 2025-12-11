# -*- coding: utf-8 -*-
"""
@Time ： 2025/12/11 16:56
@Auth ： tianjiayu
"""
from datetime import datetime
from config import ARTICLE_TITLE_MIN_LEN, ARTICLE_TITLE_MAX_LEN, ARTICLE_CONTENT_MIN_LEN, ARTICLE_CONTENT_MAX_LEN
from storage import article_storage, get_next_article_id


# 校验文章字段（拟真业务规则）
def validate_article_fields(title, content):
    if len(title.strip()) < ARTICLE_TITLE_MIN_LEN or len(title) > ARTICLE_TITLE_MAX_LEN:
        return f"标题需为{ARTICLE_TITLE_MIN_LEN}-{ARTICLE_TITLE_MAX_LEN}个字符"
    if len(content.strip()) < ARTICLE_CONTENT_MIN_LEN or len(content) > ARTICLE_CONTENT_MAX_LEN:
        return f"内容需为{ARTICLE_CONTENT_MIN_LEN}-{ARTICLE_CONTENT_MAX_LEN}个字符"
    return None


# -------------------------- 接口串联核心逻辑 --------------------------
# 1. 发布文章（返回article_id，作为后续操作的核心参数）
def create_article(user_id, username, title, content):
    # 字段校验
    validate_err = validate_article_fields(title, content)
    if validate_err:
        return None, validate_err

    # 生成文章数据（含唯一article_id）
    article_id = get_next_article_id()
    article = {
        "id": article_id,  # 接口串联核心字段
        "title": title.strip(),
        "content": content.strip(),
        "author_id": user_id,
        "author_name": username,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 写入存储
    articles = article_storage.read()
    articles.append(article)
    article_storage.write(articles)
    return article, None


# 2. 查询文章（返回含article_id的完整列表，供后续修改/删除）
def get_articles(user_id):
    articles = article_storage.read()
    # 仅返回当前用户发布的文章（权限控制）
    user_articles = [art for art in articles if art["author_id"] == user_id]
    return user_articles


# 3. 查询单篇文章（通过article_id，接口串联）
def get_article_by_id(article_id, user_id):
    try:
        article_id = int(article_id)
    except ValueError:
        return None, "article_id必须为数字"

    articles = article_storage.read()
    for art in articles:
        # 校验ID+用户权限（仅能查自己的文章）
        if art["id"] == article_id and art["author_id"] == user_id:
            return art, None
    return None, "文章不存在或无权限访问"


# 4. 修改文章（依赖article_id，接口串联）
def update_article(article_id, user_id, title=None, content=None):
    # 校验ID有效性
    article, err = get_article_by_id(article_id, user_id)
    if err:
        return None, err

    # 字段校验（仅修改时校验）
    if title:
        validate_err = validate_article_fields(title, article["content"])
        if validate_err:
            return None, validate_err
        article["title"] = title.strip()
    if content:
        validate_err = validate_article_fields(article["title"], content)
        if validate_err:
            return None, validate_err
        article["content"] = content.strip()

    # 更新时间
    article["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 写入存储
    articles = article_storage.read()
    for idx, art in enumerate(articles):
        if art["id"] == article_id:
            articles[idx] = article
            break
    article_storage.write(articles)
    return article, None


# 5. 删除文章（依赖article_id，接口串联）
def delete_article(article_id, user_id):
    # 校验ID有效性
    article, err = get_article_by_id(article_id, user_id)
    if err:
        return False, err

    # 删除文章
    articles = article_storage.read()
    articles = [art for art in articles if art["id"] != int(article_id)]
    article_storage.write(articles)
    return True, None