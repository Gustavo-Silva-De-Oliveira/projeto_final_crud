"""CRUD de clientes."""
import re

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from sqlalchemy.exc import IntegrityError

from auth import login_required
from models import Cliente, db

bp = Blueprint("clientes", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def somente_digitos(valor):
    """Remove tudo que não for dígito."""
    return re.sub(r"\D", "", valor or "")


@bp.app_template_filter("cpf_cnpj")
def formatar_cpf_cnpj(valor):
    """Formata CPF (000.000.000-00) ou CNPJ (00.000.000/0000-00) para exibição."""
    d = somente_digitos(valor)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return valor or ""


@bp.app_template_filter("telefone")
def formatar_telefone(valor):
    """Formata telefone com DDD, ex.: (11) 91234-5678."""
    d = somente_digitos(valor)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return valor or ""


def _ja_existe(coluna, valor, ignorar_id=None):
    """Verifica duplicidade, ignorando o próprio cliente na edição."""
    consulta = db.select(Cliente.id).where(coluna == valor)
    if ignorar_id is not None:
        consulta = consulta.where(Cliente.id != ignorar_id)
    return db.session.execute(consulta).first() is not None


def validar_cliente(nome, email, telefone, cpf_cnpj, ignorar_id=None):
    """Valida os dados já normalizados e devolve a lista de erros."""
    erros = []

    if len(nome) < 2:
        erros.append("O nome é obrigatório (mínimo de 2 caracteres).")
    elif len(nome) > 100:
        erros.append("O nome deve ter no máximo 100 caracteres.")

    if not email:
        erros.append("O e-mail é obrigatório.")
    elif len(email) > 120 or not EMAIL_RE.match(email):
        erros.append("Informe um e-mail válido.")

    if telefone and len(telefone) not in (10, 11):
        erros.append("O telefone deve ter 10 ou 11 dígitos (com DDD).")

    if not cpf_cnpj:
        erros.append("O CPF/CNPJ é obrigatório.")
    elif len(cpf_cnpj) not in (11, 14):
        erros.append("O CPF deve ter 11 dígitos ou o CNPJ, 14 dígitos.")

    if not erros:
        if _ja_existe(Cliente.email, email, ignorar_id):
            erros.append("Já existe um cliente com este e-mail.")
        if _ja_existe(Cliente.cpf_cnpj, cpf_cnpj, ignorar_id):
            erros.append("Já existe um cliente com este CPF/CNPJ.")

    return erros


def _ler_formulario():
    """Lê o formulário e devolve (valores brutos, valores normalizados)."""
    bruto = {
        "nome": request.form.get("nome", "").strip(),
        "email": request.form.get("email", "").strip(),
        "telefone": request.form.get("telefone", "").strip(),
        "cpf_cnpj": request.form.get("cpf_cnpj", "").strip(),
    }
    normalizado = {
        "nome": bruto["nome"],
        "email": bruto["email"].lower(),
        "telefone": somente_digitos(bruto["telefone"]) or None,
        "cpf_cnpj": somente_digitos(bruto["cpf_cnpj"]),
    }
    return bruto, normalizado


@bp.route("/clientes")
@login_required
def lista():
    """Lista os clientes em ordem alfabética, com busca opcional por nome (?q=)."""
    busca = request.args.get("q", "").strip()[:100]
    consulta = db.select(Cliente).order_by(db.func.lower(Cliente.nome))
    if busca:
        consulta = consulta.where(
            db.func.lower(Cliente.nome).contains(busca.lower(), autoescape=True))
    clientes = db.session.execute(consulta).scalars().all()
    return render_template("clientes/lista.html", clientes=clientes, busca=busca)


@bp.route("/cliente/novo", methods=["GET", "POST"])
@login_required
def novo():
    """Exibe o formulário (GET) e cadastra o cliente (POST)."""
    dados = {"nome": "", "email": "", "telefone": "", "cpf_cnpj": ""}

    if request.method == "POST":
        dados, valores = _ler_formulario()
        erros = validar_cliente(**valores)

        if not erros:
            db.session.add(Cliente(**valores))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                erros.append("E-mail ou CPF/CNPJ já cadastrado.")
            else:
                flash("Cliente cadastrado com sucesso!", "success")
                return redirect(url_for("clientes.lista"))

        for erro in erros:
            flash(erro, "danger")

    return render_template("clientes/form.html", cliente=None, dados=dados)


@bp.route("/cliente/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    """Exibe o formulário preenchido (GET) e salva as alterações (POST)."""
    cliente = db.get_or_404(Cliente, id)
    dados = {
        "nome": cliente.nome,
        "email": cliente.email,
        "telefone": cliente.telefone or "",
        "cpf_cnpj": cliente.cpf_cnpj,
    }

    if request.method == "POST":
        dados, valores = _ler_formulario()
        erros = validar_cliente(**valores, ignorar_id=cliente.id)

        if not erros:
            for campo, valor in valores.items():
                setattr(cliente, campo, valor)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                erros.append("E-mail ou CPF/CNPJ já cadastrado.")
            else:
                flash("Cliente atualizado com sucesso!", "success")
                return redirect(url_for("clientes.lista"))

        for erro in erros:
            flash(erro, "danger")

    return render_template("clientes/form.html", cliente=cliente, dados=dados)


@bp.route("/cliente/excluir/<int:id>", methods=["POST"])
@login_required
def excluir(id):
    """Exclui o cliente (apenas via POST)."""
    cliente = db.get_or_404(Cliente, id)
    nome = cliente.nome
    db.session.delete(cliente)
    db.session.commit()
    flash(f"Cliente \"{nome}\" excluído com sucesso.", "success")
    return redirect(url_for("clientes.lista"))
