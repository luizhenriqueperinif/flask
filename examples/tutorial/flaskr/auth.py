import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from .models import User
from .models import db
from .uploads import UploadError
from .uploads import save_image

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id is not None else None


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Cadastra um novo usuário, com foto de perfil opcional."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error = None

        if not username:
            error = "O nome de usuário é obrigatório."
        elif not password:
            error = "A senha é obrigatória."
        elif db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none():
            error = f"O usuário {username} já está cadastrado."

        avatar = None
        if error is None:
            try:
                avatar = save_image(request.files.get("avatar"))
            except UploadError as e:
                error = str(e)

        if error is None:
            user = User(
                username=username,
                password=generate_password_hash(password),
                avatar=avatar,
            )
            db.session.add(user)
            db.session.commit()
            flash("Cadastro realizado! Agora faça login.", "success")
            return redirect(url_for("auth.login"))

        flash(error, "danger")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        error = None
        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user is None:
            error = "Usuário incorreto."
        elif not check_password_hash(user.password, password):
            error = "Senha incorreta."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            flash(f"Bem-vindo(a), {user.username}!", "success")
            return redirect(url_for("index"))

        flash(error, "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
