from flask import Flask, request, jsonify, session, make_response, render_template
from config import SECRET_KEY

# 初始化Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True

# 延迟导入（解决循环依赖）
from auth import verify_password, generate_token, login_required
from blog import create_article, get_articles, get_article_by_id, update_article, delete_article


# -------------------------- 前端页面路由 --------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------- API接口 --------------------------
# 登录接口
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or request.form.to_dict()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名/密码不能为空"}), 400

    user = verify_password(username, password)
    if not user:
        return jsonify({"code": 401, "msg": "用户名/密码错误"}), 401

    session["username"] = user["username"]
    token = generate_token(user["id"], user["username"])

    resp = jsonify({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "token": token,
            "user_id": user["id"],
            "username": user["username"]
        }
    })
    resp.set_cookie("token", token, httponly=True, max_age=7200)
    return resp


# 发布文章接口
@app.route("/api/article/create", methods=["POST"])
@login_required
def create_article_api(user_info):
    data = request.get_json() or request.form.to_dict()
    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return jsonify({"code": 400, "msg": "标题/内容不能为空"}), 400

    article, err = create_article(user_info["sub"], user_info["username"], title, content)
    if err:
        return jsonify({"code": 400, "msg": err}), 400

    return jsonify({
        "code": 200,
        "msg": "文章发布成功",
        "data": {
            "article_id": article["id"],
            "title": article["title"],
            "create_time": article["create_time"]
        }
    })


# 查询文章列表
@app.route("/api/article/list", methods=["GET"])
@login_required
def list_article_api(user_info):
    articles = get_articles(user_info["sub"])
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "articles": articles,
            "count": len(articles)
        }
    })


# 查询单篇文章
@app.route("/api/article/<article_id>", methods=["GET"])
@login_required
def get_article_api(article_id, user_info):
    article, err = get_article_by_id(article_id, user_info["sub"])
    if err:
        return jsonify({"code": 400, "msg": err}), 400

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": article
    })


# 修改文章
@app.route("/api/article/update", methods=["POST"])
@login_required
def update_article_api(user_info):
    data = request.get_json() or request.form.to_dict()
    article_id = data.get("article_id")
    title = data.get("title")
    content = data.get("content")

    if not article_id:
        return jsonify({"code": 400, "msg": "article_id不能为空"}), 400
    if not title and not content:
        return jsonify({"code": 400, "msg": "至少修改标题或内容其中一项"}), 400

    article, err = update_article(article_id, user_info["sub"], title, content)
    if err:
        return jsonify({"code": 400, "msg": err}), 400

    return jsonify({
        "code": 200,
        "msg": "文章修改成功",
        "data": {
            "article_id": article["id"],
            "new_title": article["title"],
            "update_time": article["update_time"]
        }
    })


# 删除文章
@app.route("/api/article/delete", methods=["POST"])
@login_required
def delete_article_api(user_info):
    data = request.get_json() or request.form.to_dict()
    article_id = data.get("article_id")

    if not article_id:
        return jsonify({"code": 400, "msg": "article_id不能为空"}), 400

    result, err = delete_article(article_id, user_info["sub"])
    if err:
        return jsonify({"code": 400, "msg": err}), 400

    return jsonify({
        "code": 200,
        "msg": "文章删除成功",
        "data": {"article_id": article_id}
    })


# -------------------------- 运行入口 --------------------------
if __name__ == "__main__":
    # 初始化用户（仅首次运行）
    from storage import init_users

    init_users()
    # 启动服务
    print("服务启动成功：http://127.0.0.1:5008")
    app.run(host="0.0.0.0", port=5008, debug=False)