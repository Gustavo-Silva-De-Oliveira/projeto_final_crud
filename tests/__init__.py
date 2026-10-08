"""Testes automatizados do SGC.

As variáveis abaixo são definidas ANTES de importar a aplicação, para que os
testes usem sempre um banco em memória e nunca toquem no banco real.
"""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "chave-apenas-para-testes"
