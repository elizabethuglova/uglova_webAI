import datetime
import random
import string
from flask import Flask, request, redirect, jsonify, render_template, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from data import db_session
from data.short_links import ShortLink
from data.users import Users

# Инициализация Flask-приложения
app = Flask(__name__)
app.secret_key = 'some'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Генерация уникального короткого кода для ссылки
def generate_unique_code(db, length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not db.query(ShortLink).filter(ShortLink.short_code == code).first():
            return code

# Проверка и деактивация всех устаревших ссылок текущего пользователя
def deactivate_expired_links(db, user_id):
    now = datetime.datetime.utcnow()
    expired_links = db.query(ShortLink).filter(
        ShortLink.user_id == user_id,
        ShortLink.is_active == True,
        ShortLink.expired_at < now
    ).all()
    for link in expired_links:
        link.is_active = False
    if expired_links:
        db.commit()

# Загрузка пользователя по ID (используется Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as db:
        return db.query(Users).get(user_id)

# Главная страница — форма для создания короткой ссылки
@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    short_url = None
    if request.method == "POST":
        original_url = request.form.get("url")
        if original_url:
            with db_session.create_session() as db:
                short_code = generate_unique_code(db)
                new_link = ShortLink(
                    original_url=original_url,
                    short_code=short_code,
                    created_at=datetime.datetime.utcnow(),
                    expired_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=1),
                    is_active=True,
                    user_id=current_user.id
                )
                db.add(new_link)
                db.commit()
                short_url = f"http://localhost:8000/{short_code}"
    return render_template("index.html", short_url=short_url)

# Регистрация нового пользователя
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        with db_session.create_session() as db:
            email = request.form["email"]
            if db.query(Users).filter_by(email=email).first():
                flash("Пользователь уже существует", "error")
                return redirect("/register")

            user = Users(
                name=request.form["name"],
                email=email,
                password=generate_password_hash(request.form["password"])
            )
            db.add(user)
            db.commit()
            flash("Регистрация прошла успешно", "success")
            return redirect("/login")
    return render_template("register.html")

# Авторизация пользователя
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with db_session.create_session() as db:
            user = db.query(Users).filter_by(email=request.form["email"]).first()
            if user and check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect("/")
            flash("Неверный логин или пароль", "error")
    return render_template("login.html")

# Выход из аккаунта
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect("/login")

# Обработка перехода по короткой ссылке
@app.route('/<short_code>')
def redirect_to_original(short_code):
    with db_session.create_session() as db:
        link = db.query(ShortLink).filter_by(short_code=short_code).first()
        if link and link.is_active and link.expired_at < datetime.datetime.utcnow():
            link.is_active = False
            db.commit()

        if not link or not link.is_active:
            return render_template("expired.html"), 403

        link.clicks += 1
        db.commit()
        return redirect(link.original_url)

# Страница со списком всех ссылок пользователя
@app.route("/mylinks")
@login_required
def my_links_page():
    with db_session.create_session() as db:
        deactivate_expired_links(db, current_user.id)
        links = db.query(ShortLink).filter_by(user_id=current_user.id).order_by(ShortLink.created_at.desc()).all()
        return render_template("my_links.html", links=links)

# Страница со статистикой переходов по ссылкам
@app.route("/stats")
@login_required
def stats_page():
    with db_session.create_session() as db:
        links = db.query(ShortLink).filter_by(user_id=current_user.id).order_by(ShortLink.clicks.desc()).all()
        return render_template("stats.html", links=links)

# Страница с формой для деактивации ссылок
@app.route('/deactivate')
@login_required
def deactivate_page():
    return render_template("deactivate.html")

# API: Получение списка ссылок пользователя (с фильтрацией и пагинацией)
@app.route("/api/links", methods=["GET"])
@login_required
def get_links():
    with db_session.create_session() as db:
        deactivate_expired_links(db, current_user.id)

        page = int(request.args.get("page", 1))
        per_page = 10
        offset = (page - 1) * per_page

        query = db.query(ShortLink).filter_by(user_id=current_user.id)
        active_filter = request.args.get("active")
        if active_filter == "true":
            query = query.filter(ShortLink.is_active == True)
        elif active_filter == "false":
            query = query.filter(ShortLink.is_active == False)

        total = query.count()
        links = query.offset(offset).limit(per_page).all()

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total": total,
            "links": [
                {
                    "short_code": link.short_code,
                    "original_url": link.original_url,
                    "is_active": link.is_active,
                    "expired_at": link.expired_at.isoformat()
                } for link in links
            ]
        })

# API: Получение статистики переходов по ссылкам
@app.route("/api/stats", methods=["GET"])
@login_required
def stats():
    with db_session.create_session() as db:
        links = db.query(ShortLink).filter_by(user_id=current_user.id).order_by(ShortLink.clicks.desc()).all()
        return jsonify([
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "clicks": link.clicks
            } for link in links
        ])

# API: Деактивация ссылки (только своей)
@app.route('/api/deactivate/<short_code>', methods=["PATCH"])
@login_required
def deactivate_link(short_code):
    with db_session.create_session() as db:
        link = db.query(ShortLink).filter_by(short_code=short_code).first()

        if not link:
            return jsonify({"error": "Ссылка не найдена"}), 404

        if link.user_id != current_user.id:
            return jsonify({"error": "Вы не можете деактивировать чужую ссылку"}), 403

        if not link.is_active:
            return jsonify({"message": "Ссылка уже деактивирована"}), 200

        link.is_active = False
        db.commit()
        return jsonify({"message": "Ссылка успешно деактивирована"}), 200

# Точка входа: запуск приложения
if __name__ == '__main__':
    db_session.global_init("db.sqlite")
    app.run(port=8000)
