"""Modelos de dados do SGC."""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Usuario(db.Model):
    """Usuário do sistema. A senha nunca é guardada em texto puro."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    def definir_senha(self, senha):
        """Gera e armazena o hash da senha informada."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Retorna True se a senha informada corresponde ao hash armazenado."""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.username}>"


class Cliente(db.Model):
    """Cliente cadastrado. CPF/CNPJ e telefone são guardados só com dígitos."""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(11))
    cpf_cnpj = db.Column(db.String(14), unique=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Cliente {self.nome}>"


class Produto(db.Model):
    """Produto do catálogo. Preço em Numeric (sem erros de ponto flutuante)."""

    __tablename__ = "produtos"
    __table_args__ = (
        db.CheckConstraint("preco >= 0", name="ck_produtos_preco_nao_negativo"),
        db.CheckConstraint("estoque >= 0", name="ck_produtos_estoque_nao_negativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)

    def __repr__(self):
        return f"<Produto {self.nome}>"

