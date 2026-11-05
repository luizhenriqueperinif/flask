import os

import pytest

from flaskr.models import Post
from flaskr.models import db


def test_index(client, auth):
    text = client.get("/").get_data(as_text=True)
    assert "Entrar" in text
    assert "Cadastrar" in text
    assert "navbar-dark bg-dark" in text

    auth.login()
    text = client.get("/").get_data(as_text=True)
    assert "test title" in text
    assert "01/01/2018" in text
    assert "test\nbody" in text
    assert 'href="/1/update"' in text
    assert 'class="card shadow-sm' in text
    assert "rounded-circle" in text


@pytest.mark.parametrize("path", ("/create", "/1/update", "/1/delete"))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    with app.app_context():
        db.session.get(Post, 1).author_id = 2
        db.session.commit()

    auth.login()
    assert client.post("/1/update").status_code == 403
    assert client.post("/1/delete").status_code == 403
    assert 'href="/1/update"' not in client.get("/").get_data(as_text=True)


@pytest.mark.parametrize("path", ("/2/update", "/2/delete"))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get("/create").status_code == 200
    client.post("/create", data={"title": "created", "body": ""})

    with app.app_context():
        assert db.session.query(Post).count() == 2


def test_create_with_image(client, auth, app, png_bytes):
    auth.login()
    client.post(
        "/create",
        data={
            "title": "com foto",
            "body": "x",
            "imagem_post": (png_bytes(), "praia.png"),
        },
        content_type="multipart/form-data",
    )
    with app.app_context():
        post = db.session.execute(
            db.select(Post).filter_by(title="com foto")
        ).scalar_one()
        imagem = post.imagem_post
    assert imagem.endswith("_praia.png")
    assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], imagem))

    text = client.get("/").get_data(as_text=True)
    assert "card-img-top" in text
    assert imagem in text


def test_update(client, auth, app):
    auth.login()
    assert client.get("/1/update").status_code == 200
    client.post("/1/update", data={"title": "updated", "body": ""})

    with app.app_context():
        assert db.session.get(Post, 1).title == "updated"


def test_update_replaces_and_removes_image(client, auth, app, png_bytes):
    auth.login()
    folder = app.config["UPLOAD_FOLDER"]

    client.post(
        "/1/update",
        data={"title": "t", "body": "", "imagem_post": (png_bytes(), "a.png")},
        content_type="multipart/form-data",
    )
    with app.app_context():
        primeira = db.session.get(Post, 1).imagem_post
    assert os.path.isfile(os.path.join(folder, primeira))

    client.post(
        "/1/update",
        data={"title": "t", "body": "", "imagem_post": (png_bytes(), "b.png")},
        content_type="multipart/form-data",
    )
    with app.app_context():
        segunda = db.session.get(Post, 1).imagem_post
    assert segunda.endswith("_b.png")
    assert not os.path.exists(os.path.join(folder, primeira))

    client.post("/1/update", data={"title": "t", "body": "", "remover_imagem": "1"})
    with app.app_context():
        assert db.session.get(Post, 1).imagem_post is None
    assert os.listdir(folder) == []


@pytest.mark.parametrize("path", ("/create", "/1/update"))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={"title": "", "body": ""})
    assert "O título é obrigatório." in response.get_data(as_text=True)


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/1/delete")
    assert response.headers["Location"] == "/"

    with app.app_context():
        assert db.session.get(Post, 1) is None
