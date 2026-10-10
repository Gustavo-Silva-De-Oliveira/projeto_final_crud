"""Páginas de erro personalizadas e tratamento de falhas de banco."""
from flask import render_template
from sqlalchemy.exc import SQLAlchemyError

from models import db


def registrar_erros(app):
    """Registra os tratadores de erro na aplicação."""

    @app.errorhandler(403)
    def acesso_negado(erro):
        """Página 403: acesso negado ou token CSRF inválido."""
        return render_template("erros/403.html"), 403

    @app.errorhandler(404)
    def nao_encontrado(erro):
        """Página 404: rota ou registro inexistente."""
        return render_template("erros/404.html"), 404

    @app.errorhandler(SQLAlchemyError)
    def erro_de_banco(erro):
        """Falha de banco de dados: desfaz a transação e mostra a página 500."""
        # Desfaz a transação pendente para não deixar a sessão inutilizável.
        db.session.rollback()
        app.logger.exception("Erro de banco de dados")
        return render_template("erros/500.html"), 500

    @app.errorhandler(500)
    def erro_interno(erro):
        """Página 500 para erros internos inesperados."""
        db.session.rollback()
        return render_template("erros/500.html"), 500

