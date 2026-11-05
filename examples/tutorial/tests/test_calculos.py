import pytest

from flaskr.calculos import calcular_13_proporcional
from flaskr.calculos import calcular_irpf
from flaskr.models import Post
from flaskr.models import User
from flaskr.models import db


def test_irpf_isento_ate_5000():
    assert calcular_irpf(2000)["desconto"] == 0
    assert calcular_irpf(5000)["desconto"] == 0
    # sem a redução de 2026, o imposto em R$ 5.000 seria R$ 312,89
    assert calcular_irpf(5000)["imposto_tabela"] == 312.89


def test_irpf_faixa_de_transicao():
    r = calcular_irpf(6000)
    # base = 6000 - 607,20 = 5392,80 -> 27,5% - 908,73 = 574,29
    assert r["imposto_tabela"] == 574.29
    # redução = 978,62 - 0,133145 * 6000 = 179,75
    assert r["reducao"] == 179.75
    assert r["desconto"] == 394.54


def test_irpf_acima_de_7350_sem_reducao():
    r = calcular_irpf(10000)
    assert r["reducao"] == 0
    assert r["desconto"] == round(9392.80 * 0.275 - 908.73, 2)
    assert r["aliquota"] == 27.5


def test_irpf_negativo():
    with pytest.raises(ValueError):
        calcular_irpf(-1)


def test_13_proporcional():
    assert calcular_13_proporcional(3600, 12)["decimo_terceiro"] == 3600
    assert calcular_13_proporcional(3600, 5)["decimo_terceiro"] == 1500
    assert calcular_13_proporcional(3600, 0)["decimo_terceiro"] == 0


@pytest.mark.parametrize("meses", (-1, 13))
def test_13_meses_invalidos(meses):
    with pytest.raises(ValueError):
        calcular_13_proporcional(3000, meses)


def test_painel_get(client):
    text = client.get("/calculos/painel").get_data(as_text=True)
    assert "Cálculo de IRPF" in text
    assert "13º salário proporcional" in text


def test_painel_post_irpf(client):
    r = client.post(
        "/calculos/painel", data={"tipo": "irpf", "salario_bruto": "6.000,00"}
    )
    assert "R$ 394,54" in r.get_data(as_text=True)


def test_painel_post_rescisao(client):
    r = client.post(
        "/calculos/painel",
        data={"tipo": "rescisao", "salario_base": "3600", "meses": "5"},
    )
    assert "R$ 1.500,00" in r.get_data(as_text=True)


@pytest.mark.parametrize(
    ("data", "message"),
    (
        ({"tipo": "irpf", "salario_bruto": "abc"}, "valor numérico válido"),
        (
            {"tipo": "rescisao", "salario_base": "3000", "meses": "x"},
            "número inteiro de meses",
        ),
        (
            {"tipo": "rescisao", "salario_base": "3000", "meses": "20"},
            "entre 0 e 12",
        ),
    ),
)
def test_painel_erros(client, data, message):
    r = client.post("/calculos/painel", data=data)
    assert message in r.get_data(as_text=True)


def test_painel_nao_persiste(app, client):
    def contar():
        with app.app_context():
            return db.session.query(User).count(), db.session.query(Post).count()

    antes = contar()
    client.post("/calculos/painel", data={"tipo": "irpf", "salario_bruto": "8000"})
    assert contar() == antes
