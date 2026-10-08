"""SGC - Sistema de Gerenciamento de Clientes e Produtos.

Ponto de entrada da aplicação Flask.
"""
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

from auth import bp as auth_bp, login_required  # noqa: E402
from clientes import bp as clientes_bp  # noqa: E402
from erros import registrar_erros  # noqa: E402
from models import db  # noqa: E402
from produtos import bp as produtos_bp  # noqa: E402
from seguranca import init_csrf  # noqa: E402

app = Flask(__name__)
# Defina SECRET_KEY no .env. Sem ela, uma chave temporária é gerada e as
# sessões são invalidadas a cada reinício da aplicação.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///sgc.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(produtos_bp)
init_csrf(app)
registrar_erros(app)

with app.app_context():
    db.create_all()


@app.route("/")
@login_required
def index():
    """Página inicial (área interna, exige login)."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
