"""Camada de Modelo (M do MVC).

Substitui o antigo ``db.py`` + ``schema.sql`` (sqlite3 procedural) por
classes mapeadas com Flask-SQLAlchemy.
"""

from datetime import datetime

import click
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # nome do arquivo da foto de perfil salvo em static/uploads/
    avatar = db.Column(db.String(255), nullable=True)

    # relacionamento 1:N -> um usuário possui vários posts
    posts = db.relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    # nome do arquivo da imagem anexada ao post em static/uploads/
    imagem_post = db.Column(db.String(255), nullable=True)

    author = db.relationship("User", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.id} {self.title!r}>"


def init_db():
    """Apaga as tabelas existentes e cria tabelas novas e vazias."""
    db.drop_all()
    db.create_all()


@click.command("init-db")
def init_db_command():
    """Apaga os dados existentes e cria tabelas novas."""
    init_db()
    click.echo("Banco de dados inicializado.")


def init_app(app):
    """Registra a extensão e o comando ``flask init-db`` na aplicação."""
    db.init_app(app)
    app.cli.add_command(init_db_command)

    # cria as tabelas automaticamente caso ainda não existam
    with app.app_context():
        db.create_all()
