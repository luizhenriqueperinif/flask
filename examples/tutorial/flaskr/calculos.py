"""Módulo de cálculos financeiros em memória.

Nada aqui é salvo no banco: o ciclo é só
Requisição -> Processamento Lógico -> Resposta.

As funções de cálculo são puras (não dependem do Flask), o que as mantém
separadas da View/Template e facilita testar.
"""

from flask import Blueprint
from flask import render_template
from flask import request

bp = Blueprint("calculos", __name__, url_prefix="/calculos")

# Tabela progressiva mensal do IRPF (vigente desde maio/2025)
# (limite superior da faixa, alíquota, parcela a deduzir)
TABELA_IRPF = [
    (2428.80, 0.0, 0.0),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    (float("inf"), 0.275, 908.73),
]

# Desconto simplificado mensal (substitui deduções legais quando mais vantajoso)
DESCONTO_SIMPLIFICADO = 607.20


def _reducao_lei_15270(salario_bruto, imposto_tabela):
    """Redução mensal do IR instituída pela Lei 15.270/2025 (a partir de 2026).

    - até R$ 5.000,00: zera o imposto;
    - de R$ 5.000,01 a R$ 7.350,00: redução decrescente;
    - acima disso: sem redução.
    """
    if salario_bruto <= 5000.00:
        return imposto_tabela
    if salario_bruto <= 7350.00:
        return max(0.0, min(imposto_tabela, 978.62 - 0.133145 * salario_bruto))
    return 0.0


def calcular_irpf(salario_bruto):
    """Calcula o IRPF mensal estimado sobre o salário bruto.

    Usa o desconto simplificado como dedução e aplica a redução de 2026.
    """
    if salario_bruto < 0:
        raise ValueError("O salário não pode ser negativo.")

    base = max(0.0, salario_bruto - DESCONTO_SIMPLIFICADO)

    for limite, aliquota, deducao in TABELA_IRPF:
        if base <= limite:
            break

    imposto_tabela = max(0.0, base * aliquota - deducao)
    reducao = _reducao_lei_15270(salario_bruto, imposto_tabela)
    imposto = round(imposto_tabela - reducao, 2)

    return {
        "salario_bruto": salario_bruto,
        "base_calculo": round(base, 2),
        "aliquota": round(aliquota * 100, 1),
        "imposto_tabela": round(imposto_tabela, 2),
        "reducao": round(reducao, 2),
        "desconto": imposto,
        "aliquota_efetiva": round(imposto / salario_bruto * 100, 2)
        if salario_bruto
        else 0.0,
        "salario_liquido_ir": round(salario_bruto - imposto, 2),
    }


def calcular_13_proporcional(salario_base, meses_trabalhados):
    """Calcula o 13º salário proporcional: (salário / 12) x meses trabalhados.

    Pela CLT, fração igual ou superior a 15 dias conta como mês inteiro, por
    isso o valor recebido aqui já deve ser em meses completos (0 a 12).
    """
    if salario_base < 0:
        raise ValueError("O salário não pode ser negativo.")
    if not 0 <= meses_trabalhados <= 12:
        raise ValueError("Os meses trabalhados devem estar entre 0 e 12.")

    valor = round(salario_base / 12 * meses_trabalhados, 2)
    return {
        "salario_base": salario_base,
        "meses": meses_trabalhados,
        "valor_mensal": round(salario_base / 12, 2),
        "decimo_terceiro": valor,
    }


def _ler_float(nome):
    """Lê um número do formulário aceitando vírgula ou ponto ("3.500,50")."""
    valor = request.form.get(nome, "").strip()
    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        raise ValueError("Informe um valor numérico válido.") from None


def _ler_meses():
    try:
        return int(request.form.get("meses", "").strip())
    except ValueError:
        raise ValueError("Informe um número inteiro de meses (0 a 12).") from None


@bp.route("/painel", methods=("GET", "POST"))
def painel():
    """Painel com a calculadora de IRPF e a de 13º proporcional."""
    resultado_irpf = None
    resultado_13 = None
    erro_irpf = None
    erro_13 = None
    aba = "irpf"

    if request.method == "POST":
        tipo = request.form.get("tipo")
        aba = tipo if tipo in ("irpf", "rescisao") else "irpf"

        if tipo == "irpf":
            try:
                resultado_irpf = calcular_irpf(_ler_float("salario_bruto"))
            except ValueError as e:
                erro_irpf = str(e)
        elif tipo == "rescisao":
            try:
                salario = _ler_float("salario_base")
                meses = _ler_meses()
                resultado_13 = calcular_13_proporcional(salario, meses)
            except ValueError as e:
                erro_13 = str(e)

    return render_template(
        "calculos/index.html",
        resultado_irpf=resultado_irpf,
        resultado_13=resultado_13,
        erro_irpf=erro_irpf,
        erro_13=erro_13,
        aba=aba,
    )
