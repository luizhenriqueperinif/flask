from flaskr import create_app
from flaskr.models import db


def _dispose(app):
    with app.app_context():
        db.engine.dispose()


def test_config(tmp_path):
    """Test create_app without passing test config."""
    uri = "sqlite:///" + str(tmp_path / "t.sqlite")
    app = create_app({"SQLALCHEMY_DATABASE_URI": uri})
    assert not app.testing
    _dispose(app)

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    assert app.testing
    _dispose(app)


def test_hello(client):
    response = client.get("/hello")
    assert response.data == b"Hello, World!"
