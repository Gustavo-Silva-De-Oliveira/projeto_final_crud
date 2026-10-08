"""SGC - Sistema de Gerenciamento de Clientes e Produtos.

Ponto de entrada da aplicação Flask.
"""
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    """Página inicial: confirma que a aplicação está em execução."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
