import os

from flask import Flask


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # banco SQLite na pasta instance, acessado via SQLAlchemy
        SQLALCHEMY_DATABASE_URI="sqlite:///"
        + os.path.join(app.instance_path, "flaskr.sqlite"),
        # pasta onde avatares e imagens dos posts são salvos
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        # limite de 5 MB por requisição
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # inicializa o SQLAlchemy e o comando "flask init-db"
    from . import models

    models.init_app(app)

    # apply the blueprints to the app
    from . import auth
    from . import blog
    from . import calculos

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(calculos.bp)

    # make url_for('index') == url_for('blog.index')
    app.add_url_rule("/", endpoint="index")

    return app
