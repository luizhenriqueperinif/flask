"""Utilitário de upload de imagens (avatar e imagem dos posts).

- ``secure_filename`` limpa o nome enviado pelo usuário (evita ``../`` etc).
- um prefixo aleatório evita que dois arquivos com o mesmo nome se sobrescrevam.
- o Pillow confirma que o arquivo é realmente uma imagem.
"""

import os
import uuid

from flask import current_app
from PIL import Image
from PIL import UnidentifiedImageError
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


class UploadError(ValueError):
    """Arquivo enviado é inválido."""


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_storage):
    """Valida e salva a imagem em ``UPLOAD_FOLDER``.

    :return: o nome do arquivo salvo, ou ``None`` se nenhum arquivo foi enviado.
    :raise UploadError: se o arquivo não for uma imagem permitida.
    """
    if file_storage is None or file_storage.filename == "":
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        raise UploadError(
            "Formato de imagem não permitido. Use: "
            + ", ".join(sorted(ALLOWED_EXTENSIONS))
            + "."
        )

    # confirma que o conteúdo é realmente uma imagem
    try:
        with Image.open(file_storage.stream) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as e:
        raise UploadError("O arquivo enviado não é uma imagem válida.") from e
    file_storage.stream.seek(0)

    final_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, final_name))
    return final_name


def delete_image(filename):
    """Remove fisicamente um arquivo salvo anteriormente (se existir)."""
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], secure_filename(filename))
    if os.path.isfile(path):
        os.remove(path)
