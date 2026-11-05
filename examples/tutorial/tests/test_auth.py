import io
import os

import pytest
from flask import g
from flask import session

from flaskr.models import User
from flaskr.models import db


def _get_user(username):
    return db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none()


def test_register(client, app):
    page = client.get("/auth/register")
    assert page.status_code == 200
    assert b'enctype="multipart/form-data"' in page.data

    response = client.post("/auth/register", data={"username": "a", "password": "a"})
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        user = _get_user("a")
        assert user is not None
        assert user.avatar is None


def test_register_with_avatar(client, app, png_bytes):
    response = client.post(
        "/auth/register",
        data={
            "username": "foto",
            "password": "a",
            "avatar": (png_bytes(), "../../minha foto.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302

    with app.app_context():
        user = _get_user("foto")
        # secure_filename remove "../" e troca espaços por "_"
        assert user.avatar.endswith("_minha_foto.png")
        assert "/" not in user.avatar and ".." not in user.avatar
        assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], user.avatar))


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    (
        ("virus.exe", b"MZ...", "Formato de imagem não permitido"),
        ("fake.png", b"isto nao e imagem", "não é uma imagem válida"),
    ),
)
def test_register_rejects_bad_avatar(client, app, filename, content, message):
    response = client.post(
        "/auth/register",
        data={
            "username": "x",
            "password": "x",
            "avatar": (io.BytesIO(content), filename),
        },
        content_type="multipart/form-data",
    )
    assert message in response.get_data(as_text=True)
    with app.app_context():
        assert _get_user("x") is None
    assert os.listdir(app.config["UPLOAD_FOLDER"]) == []


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", "O nome de usuário é obrigatório."),
        ("a", "", "A senha é obrigatória."),
        ("test", "test", "já está cadastrado"),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/register", data={"username": username, "password": password}
    )
    assert message in response.get_data(as_text=True)


def test_login(client, auth):
    assert client.get("/auth/login").status_code == 200

    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user.username == "test"


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (("a", "test", "Usuário incorreto."), ("test", "a", "Senha incorreta.")),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.get_data(as_text=True)


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "user_id" not in session
