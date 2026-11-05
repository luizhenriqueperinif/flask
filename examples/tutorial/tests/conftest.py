import io
import os
import tempfile
from datetime import datetime

import pytest
from PIL import Image
from werkzeug.security import generate_password_hash

from flaskr import create_app
from flaskr.models import Post
from flaskr.models import User
from flaskr.models import db
from flaskr.models import init_db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    upload_dir = tempfile.mkdtemp()
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_path,
            "UPLOAD_FOLDER": upload_dir,
        }
    )

    with app.app_context():
        init_db()
        test = User(username="test", password=generate_password_hash("test"))
        other = User(username="other", password=generate_password_hash("other"))
        db.session.add_all([test, other])
        db.session.add(
            Post(
                title="test title",
                body="test\nbody",
                author=test,
                created=datetime(2018, 1, 1),
            )
        )
        db.session.commit()

    yield app

    with app.app_context():
        db.engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def png_bytes():
    """Gera uma imagem PNG válida em memória."""

    def _make():
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(buf, format="PNG")
        buf.seek(0)
        return buf

    return _make


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test"):
        return self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
