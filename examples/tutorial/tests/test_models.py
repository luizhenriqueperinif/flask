from flaskr.models import Post
from flaskr.models import User
from flaskr.models import db
from flaskr.models import init_db


def test_relationship(app):
    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(username="test")
        ).scalar_one()
        assert len(user.posts) == 1
        assert user.posts[0].author is user


def test_init_db_command(runner, monkeypatch):
    class Recorder:
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("flaskr.models.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "inicializado" in result.output
    assert Recorder.called


def test_init_db_clears(app):
    with app.app_context():
        init_db()
        assert db.session.execute(db.select(Post)).first() is None
