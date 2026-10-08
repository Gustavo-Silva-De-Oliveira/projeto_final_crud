"""Autenticação: registro, login, logout e proteção de rotas."""
import re
from functools import wraps

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from models import Usuario, db

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MIN = 8


@bp.before_app_request
def carregar_usuario_logado():
    """Disponibiliza o usuário autenticado (ou None) em `g.usuario`."""
    usuario_id = session.get("usuario_id")
    g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
    if usuario_id and g.usuario is None:
        # Sessão aponta para um usuário que não existe mais.
        session.clear()


def login_required(view):
    """Redireciona para o login quando o usuário não está autenticado."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.usuario is None:
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _destino_seguro(destino):
    """Aceita apenas caminhos internos, evitando redirecionamento externo."""
    if destino and destino.startswith("/") and not destino.startswith("//") \
            and "\\" not in destino:
        return destino
    return None


def validar_registro(username, email, senha, confirmacao):
    """Valida os dados do registro e devolve uma lista de erros."""
    erros = []

    if not USERNAME_RE.match(username):
        erros.append("O nome de usuário deve ter de 3 a 30 caracteres, "
                     "usando apenas letras, números e _.")
    if len(email) > 120 or not EMAIL_RE.match(email):
        erros.append("Informe um e-mail válido.")
    if len(senha) < SENHA_MIN:
        erros.append(f"A senha deve ter pelo menos {SENHA_MIN} caracteres.")
    elif senha != confirmacao:
        erros.append("A confirmação da senha não confere.")

    if not erros:
        if db.session.execute(
            db.select(Usuario).where(
                func.lower(Usuario.username) == username.lower())
        ).first():
            erros.append("Este nome de usuário já está em uso.")
        if db.session.execute(
            db.select(Usuario).where(Usuario.email == email)
        ).first():
            erros.append("Este e-mail já está cadastrado.")

    return erros


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Cadastro de novo usuário."""
    if g.usuario:
        return redirect(url_for("index"))

    username = email = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        erros = validar_registro(username, email, senha, confirmacao)
        if not erros:
            usuario = Usuario(username=username, email=email)
            usuario.definir_senha(senha)
            db.session.add(usuario)
            try:
                db.session.commit()
            except IntegrityError:
                # Cadastro simultâneo com os mesmos dados.
                db.session.rollback()
                erros.append("Nome de usuário ou e-mail já cadastrado.")
            else:
                flash("Cadastro realizado com sucesso! Faça login.", "success")
                return redirect(url_for("auth.login"))

        for erro in erros:
            flash(erro, "danger")

    return render_template("auth/registro.html", username=username, email=email)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login por nome de usuário ou e-mail."""
    destino = _destino_seguro(request.values.get("next"))

    if g.usuario:
        return redirect(destino or url_for("index"))

    identificador = ""
    if request.method == "POST":
        identificador = request.form.get("identificador", "").strip()
        senha = request.form.get("senha", "")

        usuario = db.session.execute(
            db.select(Usuario).where(or_(
                func.lower(Usuario.username) == identificador.lower(),
                Usuario.email == identificador.lower(),
            ))
        ).scalar_one_or_none()

        if usuario and usuario.verificar_senha(senha):
            session.clear()
            session["usuario_id"] = usuario.id
            flash(f"Bem-vindo, {usuario.username}!", "success")
            return redirect(destino or url_for("index"))

        flash("Usuário/e-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html", identificador=identificador,
                           next=destino)


@bp.route("/logout", methods=["POST"])
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
