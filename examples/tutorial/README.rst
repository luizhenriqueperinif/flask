Flaskr — MVC + SQLAlchemy + Bootstrap 5
=======================================

Evolução do blog do `tutorial`_ oficial do Flask, reorganizado no padrão MVC:

- **Model** (``flaskr/models.py``): classes ``User`` e ``Post`` com
  Flask-SQLAlchemy e relacionamento 1:N (``User.posts`` / ``Post.author``).
  O antigo ``db.py`` com ``sqlite3`` e o ``schema.sql`` foram removidos.
- **Controller** (``auth.py``, ``blog.py``, ``calculos.py``): rotas que usam
  ``db.session.add()`` / ``db.session.commit()``. Uploads de avatar e de imagem
  de post passam por ``flaskr/uploads.py``, que usa ``secure_filename``, lista
  de extensões permitidas, validação com Pillow e nome único. Os arquivos são
  salvos em ``flaskr/static/uploads/``.
- **View** (``flaskr/templates/``): Bootstrap 5 via CDN, navbar escura e
  responsiva com a foto do usuário em ``rounded-circle``, posts em cards e
  alertas para as mensagens flash.

Módulo de cálculos (``/calculos/painel``)
-----------------------------------------

Funciona só em memória, sem gravar nada no banco:

- **IRPF mensal**: aplica o desconto simplificado (R$ 607,20) e a tabela
  progressiva. Também aplica a redução da Lei 15.270/2025, que deixa isento
  quem ganha até R$ 5.000 e dá desconto parcial até R$ 7.350.
- **Rescisão: 13º proporcional**: ``salário / 12 × meses trabalhados``.

As funções de cálculo (``calcular_irpf``, ``calcular_13_proporcional``) são
puras e ficam separadas da rota e do template.

.. _tutorial: https://flask.palletsprojects.com/tutorial/


Instalação
----------

::

    $ git clone https://github.com/<seu-usuario>/flask
    $ cd flask/examples/tutorial
    $ python -m venv venv
    # Windows
    $ venv\Scripts\activate
    # Linux/macOS
    $ source venv/bin/activate
    $ pip install flask Flask-SQLAlchemy Werkzeug Pillow
    $ pip install -e .


Execução
--------

::

    $ flask --app flaskr init-db
    $ flask --app flaskr run --debug

Abra http://127.0.0.1:5000 no navegador. As tabelas também são criadas
automaticamente na primeira execução.


Testes
------

::

    $ pip install -e ".[test]"
    $ pytest
