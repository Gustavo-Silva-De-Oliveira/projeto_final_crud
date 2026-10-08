"""Testes de autenticação, CRUDs, busca, CSRF e páginas de erro.

Execute a partir da raiz do projeto:  python -m unittest discover -v
"""
import unittest
from unittest import mock

from sqlalchemy.exc import OperationalError

from app import app
from models import Cliente, Produto, Usuario, db

CPF_VALIDO = "529.982.247-25"
CNPJ_VALIDO = "11.222.333/0001-81"


class BaseTeste(unittest.TestCase):
    """Cria um banco limpo e um cliente HTTP a cada teste."""

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.c = app.test_client()

    def post(self, url, dados=None, token=True, **kw):
        """POST com token CSRF (a menos que token=False)."""
        with self.c.session_transaction() as sessao:
            sessao.setdefault("_csrf_token", "token-de-teste")
            valor = sessao["_csrf_token"]
        dados = dict(dados or {})
        if token:
            dados["csrf_token"] = valor
        return self.c.post(url, data=dados, **kw)

    def entrar(self, username="ana", senha="senhaforte1"):
        """Registra e autentica um usuário."""
        self.post("/registro", dict(username=username, email=f"{username}@ex.com",
                                    senha=senha, confirmacao=senha))
        return self.post("/login", dict(identificador=username, senha=senha))

    @staticmethod
    def texto(resposta):
        return resposta.get_data(as_text=True)

    def contar(self, modelo):
        with app.app_context():
            return db.session.query(modelo).count()

    def novo_cliente(self, **kw):
        dados = dict(nome="Carlos Silva", email="carlos@ex.com",
                     telefone="(11) 91234-5678", cpf_cnpj=CPF_VALIDO)
        dados.update(kw)
        return self.post("/cliente/novo", dados)

    def novo_produto(self, **kw):
        dados = dict(nome="Teclado", preco="199,90", estoque="10",
                     categoria="Periféricos", descricao="")
        dados.update(kw)
        return self.post("/produto/novo", dados)


class TestAutenticacao(BaseTeste):
    def test_paginas_internas_exigem_login(self):
        for url in ("/", "/clientes", "/produtos", "/cliente/novo", "/produto/novo"):
            r = self.c.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/login", r.headers["Location"])

    def test_registro_valida_dados(self):
        r = self.post("/registro", dict(username="a", email="x", senha="123",
                                        confirmacao="123"))
        x = self.texto(r)
        self.assertIn("nome de usuário", x)
        self.assertIn("e-mail válido", x)
        self.assertIn("pelo menos 8", x)
        self.assertEqual(self.contar(Usuario), 0)

    def test_registro_confirmacao_diferente(self):
        r = self.post("/registro", dict(username="ana", email="a@ex.com",
                                        senha="senhaforte1", confirmacao="outra"))
        self.assertIn("não confere", self.texto(r))

    def test_registro_grava_hash_e_bloqueia_duplicados(self):
        self.entrar()
        with app.app_context():
            usuario = db.session.query(Usuario).one()
            self.assertNotEqual(usuario.senha_hash, "senhaforte1")
            self.assertTrue(usuario.verificar_senha("senhaforte1"))
        self.post("/logout")
        r = self.post("/registro", dict(username="ANA", email="outro@ex.com",
                                        senha="senhaforte1", confirmacao="senhaforte1"))
        self.assertIn("nome de usuário já está em uso", self.texto(r))
        r = self.post("/registro", dict(username="bia", email="ANA@ex.com",
                                        senha="senhaforte1", confirmacao="senhaforte1"))
        self.assertIn("e-mail já está cadastrado", self.texto(r))
        self.assertEqual(self.contar(Usuario), 1)

    def test_login_invalido_e_valido(self):
        self.post("/registro", dict(username="ana", email="ana@ex.com",
                                    senha="senhaforte1", confirmacao="senhaforte1"))
        r = self.post("/login", dict(identificador="ana", senha="errada"))
        self.assertIn("inválidos", self.texto(r))
        self.assertEqual(self.c.get("/").status_code, 302)
        r = self.post("/login", dict(identificador="ANA@ex.com", senha="senhaforte1"))
        self.assertEqual(r.status_code, 302)
        x = self.texto(self.c.get("/"))
        self.assertIn("Olá, <strong>ana</strong>", x)

    def test_logout_so_por_post_e_limpa_sessao(self):
        self.entrar()
        self.assertEqual(self.c.get("/logout").status_code, 405)
        r = self.post("/logout")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.c.get("/clientes").status_code, 302)

    def test_next_externo_e_ignorado(self):
        self.post("/registro", dict(username="ana", email="ana@ex.com",
                                    senha="senhaforte1", confirmacao="senhaforte1"))
        r = self.post("/login", dict(identificador="ana", senha="senhaforte1",
                                     next="//evil.com"))
        self.assertEqual(r.headers["Location"], "/")


class TestCsrf(BaseTeste):
    def test_formulario_traz_token_real(self):
        x = self.texto(self.c.get("/login"))
        with self.c.session_transaction() as sessao:
            token = sessao["_csrf_token"]
        self.assertEqual(len(token), 64)
        self.assertIn(f'value="{token}"', x)

    def test_post_sem_token_ou_com_token_errado_retorna_403(self):
        self.entrar()
        for url in ("/cliente/novo", "/cliente/excluir/1", "/produto/novo",
                    "/produto/editar/1", "/logout"):
            self.assertEqual(self.post(url, {"nome": "x"}, token=False).status_code,
                             403, url)
        r = self.c.post("/cliente/novo", data={"csrf_token": "errado"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.contar(Cliente), 0)


class TestClientes(BaseTeste):
    def setUp(self):
        super().setUp()
        self.entrar()

    def test_lista_vazia(self):
        self.assertIn("Nenhum cliente cadastrado", self.texto(self.c.get("/clientes")))

    def test_validacoes(self):
        x = self.texto(self.novo_cliente(nome="", email="x", telefone="123", cpf_cnpj="12"))
        for trecho in ("nome é obrigatório", "e-mail válido", "10 ou 11 dígitos",
                       "11 dígitos ou o CNPJ"):
            self.assertIn(trecho, x)
        self.assertEqual(self.contar(Cliente), 0)

    def test_cadastro_cpf_cnpj_e_telefone_opcional(self):
        self.assertEqual(self.novo_cliente().status_code, 302)
        self.assertEqual(self.novo_cliente(nome="Ana", email="a@ex.com", telefone="",
                                           cpf_cnpj=CNPJ_VALIDO).status_code, 302)
        x = self.texto(self.c.get("/clientes"))
        self.assertIn(CPF_VALIDO, x)
        self.assertIn(CNPJ_VALIDO, x)
        self.assertIn("(11) 91234-5678", x)
        self.assertLess(x.index("Ana"), x.index("Carlos Silva"))
        with app.app_context():
            self.assertIsNone(db.session.query(Cliente).filter_by(nome="Ana").one().telefone)

    def test_duplicidade_no_cadastro(self):
        self.novo_cliente()
        x = self.texto(self.novo_cliente(nome="Outro", email="CARLOS@ex.com",
                                         cpf_cnpj="39053344705"))
        self.assertIn("Já existe um cliente com este e-mail", x)
        x = self.texto(self.novo_cliente(nome="Outro", email="o@ex.com",
                                         cpf_cnpj="52998224725"))
        self.assertIn("Já existe um cliente com este CPF/CNPJ", x)
        self.assertEqual(self.contar(Cliente), 1)

    def test_edicao_e_conflitos(self):
        self.novo_cliente()
        self.novo_cliente(nome="Bia", email="bia@ex.com", telefone="", cpf_cnpj=CNPJ_VALIDO)
        x = self.texto(self.c.get("/cliente/editar/1"))
        self.assertIn('value="Carlos Silva"', x)
        self.assertIn('value="(11) 91234-5678"', x)
        r = self.post("/cliente/editar/1", dict(nome="Carlos Souza", email="carlos@ex.com",
                                                telefone="", cpf_cnpj="52998224725"))
        self.assertEqual(r.status_code, 302)
        r = self.post("/cliente/editar/1", dict(nome="Carlos", email="bia@ex.com",
                                                telefone="", cpf_cnpj="52998224725"))
        self.assertIn("Já existe um cliente com este e-mail", self.texto(r))
        r = self.post("/cliente/editar/1", dict(nome="Carlos", email="carlos@ex.com",
                                                telefone="", cpf_cnpj="11222333000181"))
        self.assertIn("Já existe um cliente com este CPF/CNPJ", self.texto(r))
        with app.app_context():
            self.assertEqual(db.session.get(Cliente, 1).nome, "Carlos Souza")

    def test_exclusao(self):
        self.novo_cliente()
        self.assertEqual(self.c.get("/cliente/excluir/1").status_code, 405)
        r = self.post("/cliente/excluir/1", follow_redirects=True)
        self.assertIn("excluído com sucesso", self.texto(r))
        self.assertEqual(self.contar(Cliente), 0)

    def test_registro_inexistente_retorna_404(self):
        self.assertEqual(self.c.get("/cliente/editar/999").status_code, 404)
        self.assertEqual(self.post("/cliente/excluir/999").status_code, 404)

    def test_busca(self):
        self.novo_cliente(nome="Maria Souza", email="m@ex.com", cpf_cnpj=CPF_VALIDO)
        self.novo_cliente(nome="José Santos", email="j@ex.com", cpf_cnpj=CNPJ_VALIDO)
        self.novo_cliente(nome="Ana 100% Lima", email="a@ex.com", cpf_cnpj="39053344705")
        x = self.texto(self.c.get("/clientes?q=MARIA"))
        self.assertIn("Maria Souza", x)
        self.assertNotIn("José Santos", x)
        x = self.texto(self.c.get("/clientes?q=100%25"))
        self.assertIn("Ana 100% Lima", x)
        self.assertNotIn("Maria Souza", x)
        self.assertNotIn("Maria Souza", self.texto(self.c.get("/clientes?q=%25")))
        x = self.texto(self.c.get("/clientes?q=%3Cscript%3E"))
        self.assertIn("&lt;script&gt;", x)
        self.assertIn("Nenhum cliente encontrado", x)


class TestProdutos(BaseTeste):
    def setUp(self):
        super().setUp()
        self.entrar()

    def test_campos_obrigatorios(self):
        x = self.texto(self.novo_produto(nome="", preco="", estoque="", categoria=""))
        for trecho in ("nome é obrigatório", "categoria é obrigatória",
                       "preço é obrigatório", "estoque é obrigatório"):
            self.assertIn(trecho, x)
        self.assertEqual(self.contar(Produto), 0)

    def test_preco_invalido(self):
        casos = {"-5": "negativo", "abc": "preço válido", "1e5": "preço válido",
                 "NaN": "preço válido", "1,5.0": "preço válido",
                 "10,999": "2 casas decimais", "100000000": "preço máximo"}
        for valor, trecho in casos.items():
            self.assertIn(trecho, self.texto(self.novo_produto(preco=valor)), valor)
        self.assertEqual(self.contar(Produto), 0)

    def test_estoque_invalido(self):
        casos = {"-1": "negativo", "1.5": "inteiro", "1,5": "inteiro",
                 "abc": "inteiro", "99999999999": "muito grande"}
        for valor, trecho in casos.items():
            self.assertIn(trecho, self.texto(self.novo_produto(estoque=valor)), valor)
        self.assertEqual(self.contar(Produto), 0)

    def test_limites_de_texto(self):
        self.assertIn("no máximo 100", self.texto(self.novo_produto(nome="x" * 101)))
        self.assertIn("no máximo 50", self.texto(self.novo_produto(categoria="x" * 51)))
        self.assertIn("no máximo 500", self.texto(self.novo_produto(descricao="x" * 501)))

    def test_cadastro_aceita_formatos_de_preco(self):
        for nome, preco in [("Item A", "1.299,50"), ("Item B", "29.9"), ("Item C", "R$ 0"), ("Item D", "199,90")]:
            self.assertEqual(self.novo_produto(nome=nome, preco=preco).status_code, 302)
        x = self.texto(self.c.get("/produtos"))
        for esperado in ("R$ 1.299,50", "R$ 29,90", "R$ 0,00", "R$ 199,90"):
            self.assertIn(esperado, x)

    def test_estoque_zero_mostra_selo(self):
        self.novo_produto(estoque="0")
        self.assertIn("Sem estoque", self.texto(self.c.get("/produtos")))

    def test_edicao_exclusao_e_404(self):
        self.novo_produto()
        x = self.texto(self.c.get("/produto/editar/1"))
        self.assertIn('value="199,90"', x)
        r = self.post("/produto/editar/1", dict(nome="Teclado RGB", preco="249,00",
                                                estoque="7", categoria="Periféricos",
                                                descricao=""))
        self.assertEqual(r.status_code, 302)
        r = self.post("/produto/editar/1", dict(nome="X", preco="-1", estoque="7",
                                                categoria="c", descricao=""))
        self.assertIn("negativo", self.texto(r))
        with app.app_context():
            p = db.session.get(Produto, 1)
            self.assertEqual((p.nome, str(p.preco), p.estoque), ("Teclado RGB", "249.00", 7))
        self.assertEqual(self.c.get("/produto/excluir/1").status_code, 405)
        self.assertEqual(self.post("/produto/excluir/1").status_code, 302)
        self.assertEqual(self.contar(Produto), 0)
        self.assertEqual(self.c.get("/produto/editar/1").status_code, 404)

    def test_banco_rejeita_valores_negativos(self):
        for kw in (dict(preco=-1, estoque=1), dict(preco=1, estoque=-1)):
            with app.app_context():
                db.session.add(Produto(nome="X", categoria="c", **kw))
                with self.assertRaises(Exception):
                    db.session.commit()
                db.session.rollback()

    def test_busca(self):
        self.novo_produto(nome="Teclado Mecânico")
        self.novo_produto(nome="Teclado Gamer")
        self.novo_produto(nome="Mouse")
        x = self.texto(self.c.get("/produtos?q=teclado"))
        self.assertIn("Teclado Mecânico", x)
        self.assertIn("Teclado Gamer", x)
        self.assertNotIn("Mouse", x)
        self.assertIn("Nenhum produto encontrado", self.texto(self.c.get("/produtos?q=xyz")))


class TestErros(BaseTeste):
    def test_404_personalizada(self):
        self.entrar()
        r = self.c.get("/nao-existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("Página não encontrada", self.texto(r))

    def test_403_personalizada(self):
        self.entrar()
        r = self.post("/cliente/novo", {"nome": "x"}, token=False)
        self.assertEqual(r.status_code, 403)
        x = self.texto(r)
        self.assertIn("Acesso negado", x)
        self.assertIn("Olá, <strong>ana</strong>", x)

    def test_erro_de_banco_faz_rollback_e_app_continua(self):
        self.entrar()
        falha = OperationalError("stmt", {}, Exception("falha simulada"))
        with mock.patch.object(db.session, "commit", side_effect=falha), \
                self.assertLogs(app.logger, level="ERROR"):
            r = self.novo_cliente()
        self.assertEqual(r.status_code, 500)
        self.assertIn("Erro interno", self.texto(r))
        self.assertEqual(self.c.get("/clientes").status_code, 200)
        self.assertEqual(self.novo_cliente().status_code, 302)
        self.assertEqual(self.contar(Cliente), 1)

    def test_rotas_que_alteram_dados_nao_aceitam_get(self):
        for regra in app.url_map.iter_rules():
            if regra.rule.startswith(("/cliente/excluir", "/produto/excluir", "/logout")):
                self.assertNotIn("GET", regra.methods, regra.rule)


if __name__ == "__main__":
    unittest.main()
