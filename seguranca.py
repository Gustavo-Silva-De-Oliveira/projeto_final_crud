"""Proteção CSRF para formulários que alteram dados."""
import secrets

from flask import abort, request, session

METODOS_PROTEGIDOS = ("POST", "PUT", "PATCH", "DELETE")


def gerar_token():
    """Devolve o token CSRF da sessão, criando-o se ainda não existir."""
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["_csrf_token"] = token
    return token


def verificar_token():
    """Bloqueia (403) requisições que alteram dados sem um token CSRF válido."""
    if request.method not in METODOS_PROTEGIDOS:
        return
    esperado = session.get("_csrf_token")
    enviado = (request.form.get("csrf_token")
               or request.headers.get("X-CSRFToken"))
    if not esperado or not enviado or not secrets.compare_digest(esperado, enviado):
        abort(403)


def init_csrf(app):
    """Registra a verificação e o helper `csrf_token()` nos templates."""
    app.jinja_env.globals["csrf_token"] = gerar_token
    app.before_request(verificar_token)
