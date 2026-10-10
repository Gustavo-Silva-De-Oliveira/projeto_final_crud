"""CRUD de produtos."""
import re
from decimal import Decimal

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from sqlalchemy.exc import SQLAlchemyError

from auth import login_required
from models import Produto, db

bp = Blueprint("produtos", __name__)

PRECO_MAX = Decimal("99999999.99")  # limite de Numeric(10, 2)
ESTOQUE_MAX = 2_147_483_647          # limite de Integer
DESCRICAO_MAX = 500


@bp.app_template_filter("moeda")
def formatar_moeda(valor):
    """Formata um valor como moeda brasileira, ex.: R$ 1.234,56."""
    if valor is None:
        return ""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _converter_preco(texto, erros):
    """Converte o texto do preço em Decimal; adiciona mensagens em `erros`."""
    texto = texto.replace("R$", "").replace(" ", "")
    if not texto:
        erros.append("O preço é obrigatório.")
        return None
    if texto.startswith("-"):
        erros.append("O preço não pode ser negativo.")
        return None
    if "," in texto:  # formato brasileiro: 1.234,56
        if not re.fullmatch(r"(\d+|\d{1,3}(\.\d{3})+),\d+", texto):
            erros.append("Informe um preço válido, por exemplo 19,90.")
            return None
        texto = texto.replace(".", "").replace(",", ".")
    elif not re.fullmatch(r"\d+(\.\d+)?", texto):  # formato 1234.56
        erros.append("Informe um preço válido, por exemplo 19,90.")
        return None

    valor = Decimal(texto)
    if valor > PRECO_MAX:
        erros.append("O preço máximo permitido é R$ 99.999.999,99.")
        return None
    if valor != valor.quantize(Decimal("0.01")):
        erros.append("O preço deve ter no máximo 2 casas decimais.")
        return None
    return valor


def _converter_estoque(texto, erros):
    """Converte o texto do estoque em inteiro >= 0; adiciona erros se inválido."""
    texto = texto.replace(" ", "")
    if not texto:
        erros.append("O estoque é obrigatório.")
        return None
    if texto.startswith("-"):
        erros.append("O estoque não pode ser negativo.")
        return None
    if not re.fullmatch(r"\d+", texto):
        erros.append("O estoque deve ser um número inteiro (sem casas decimais).")
        return None

    valor = int(texto)
    if valor > ESTOQUE_MAX:
        erros.append("O estoque informado é muito grande.")
        return None
    return valor


def validar_produto(bruto):
    """Valida os dados brutos do formulário.

    Devolve (valores prontos para o modelo, lista de erros).
    """
    erros = []
    nome = bruto["nome"]
    categoria = bruto["categoria"]
    descricao = bruto["descricao"]

    if len(nome) < 2:
        erros.append("O nome é obrigatório (mínimo de 2 caracteres).")
    elif len(nome) > 100:
        erros.append("O nome deve ter no máximo 100 caracteres.")

    if not categoria:
        erros.append("A categoria é obrigatória.")
    elif len(categoria) > 50:
        erros.append("A categoria deve ter no máximo 50 caracteres.")

    preco = _converter_preco(bruto["preco"], erros)
    estoque = _converter_estoque(bruto["estoque"], erros)

    if len(descricao) > DESCRICAO_MAX:
        erros.append(f"A descrição deve ter no máximo {DESCRICAO_MAX} caracteres.")

    valores = {
        "nome": nome,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
        "descricao": descricao or None,
    }
    return valores, erros


def _ler_formulario():
    """Lê o formulário como texto bruto (usado também para reexibir erros)."""
    return {campo: request.form.get(campo, "").strip()
            for campo in ("nome", "preco", "estoque", "categoria", "descricao")}


@bp.route("/produtos")
@login_required
def lista():
    """Lista os produtos em ordem alfabética, com busca opcional por nome (?q=)."""
    busca = request.args.get("q", "").strip()[:100]
    consulta = db.select(Produto).order_by(db.func.lower(Produto.nome))
    if busca:
        consulta = consulta.where(
            db.func.lower(Produto.nome).contains(busca.lower(), autoescape=True))
    produtos = db.session.execute(consulta).scalars().all()
    return render_template("produtos/lista.html", produtos=produtos, busca=busca)


def _salvar(produto, valores):
    """Aplica os valores ao produto e grava. Devolve True em caso de sucesso."""
    for campo, valor in valores.items():
        setattr(produto, campo, valor)
    db.session.add(produto)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Não foi possível salvar o produto. Tente novamente.", "danger")
        return False
    return True


@bp.route("/produto/novo", methods=["GET", "POST"])
@login_required
def novo():
    """Exibe o formulário (GET) e cadastra o produto (POST)."""
    dados = {"nome": "", "preco": "", "estoque": "0", "categoria": "",
             "descricao": ""}

    if request.method == "POST":
        dados = _ler_formulario()
        valores, erros = validar_produto(dados)

        if not erros and _salvar(Produto(), valores):
            flash("Produto cadastrado com sucesso!", "success")
            return redirect(url_for("produtos.lista"))

        for erro in erros:
            flash(erro, "danger")

    return render_template("produtos/form.html", produto=None, dados=dados)


@bp.route("/produto/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    """Exibe o formulário preenchido (GET) e salva as alterações (POST)."""
    produto = db.get_or_404(Produto, id)
    dados = {
        "nome": produto.nome,
        "preco": f"{produto.preco:.2f}".replace(".", ","),
        "estoque": str(produto.estoque),
        "categoria": produto.categoria,
        "descricao": produto.descricao or "",
    }

    if request.method == "POST":
        dados = _ler_formulario()
        valores, erros = validar_produto(dados)

        if not erros and _salvar(produto, valores):
            flash("Produto atualizado com sucesso!", "success")
            return redirect(url_for("produtos.lista"))

        for erro in erros:
            flash(erro, "danger")

    return render_template("produtos/form.html", produto=produto, dados=dados)


@bp.route("/produto/excluir/<int:id>", methods=["POST"])
@login_required
def excluir(id):
    """Exclui o produto (apenas via POST)."""
    produto = db.get_or_404(Produto, id)
    nome = produto.nome
    db.session.delete(produto)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Não foi possível excluir o produto. Tente novamente.", "danger")
    else:
        flash(f"Produto \"{nome}\" excluído com sucesso.", "success")
    return redirect(url_for("produtos.lista"))

