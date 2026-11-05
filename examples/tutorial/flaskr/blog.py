from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .models import Post
from .models import db
from .uploads import UploadError
from .uploads import delete_image
from .uploads import save_image

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    posts = db.session.execute(
        db.select(Post).order_by(Post.created.desc())
    ).scalars().all()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = db.session.get(Post, id)

    if post is None:
        abort(404, f"O post {id} não existe.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "")
        error = None

        if not title:
            error = "O título é obrigatório."

        imagem = None
        if error is None:
            try:
                imagem = save_image(request.files.get("imagem_post"))
            except UploadError as e:
                error = str(e)

        if error is not None:
            flash(error, "danger")
        else:
            post = Post(title=title, body=body, author=g.user, imagem_post=imagem)
            db.session.add(post)
            db.session.commit()
            flash("Post publicado!", "success")
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "")
        error = None

        if not title:
            error = "O título é obrigatório."

        nova_imagem = None
        if error is None:
            try:
                nova_imagem = save_image(request.files.get("imagem_post"))
            except UploadError as e:
                error = str(e)

        if error is not None:
            flash(error, "danger")
        else:
            post.title = title
            post.body = body
            if nova_imagem:
                # substitui a imagem antiga
                delete_image(post.imagem_post)
                post.imagem_post = nova_imagem
            elif request.form.get("remover_imagem"):
                delete_image(post.imagem_post)
                post.imagem_post = None
            db.session.commit()
            flash("Post atualizado!", "success")
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post (and its image) if the current user is the author."""
    post = get_post(id)
    delete_image(post.imagem_post)
    db.session.delete(post)
    db.session.commit()
    flash("Post excluído.", "info")
    return redirect(url_for("blog.index"))
