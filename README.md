# SGC — Sistema de Gerenciamento de Clientes e Produtos

Aplicação web para cadastrar e gerenciar **clientes** e **produtos**, com
autenticação de usuários. Desenvolvida em Python/Flask, com interface em
português do Brasil.

## Funcionalidades

- **Autenticação**: registro, login (por usuário ou e-mail), logout e proteção
  de todas as páginas internas. Senhas guardadas apenas como hash.
- **Clientes**: listar, cadastrar, editar e excluir (com confirmação), com
  validação de campos e bloqueio de e-mail e CPF/CNPJ duplicados.
- **Produtos**: listar, cadastrar, editar e excluir (com confirmação), com
  validação de preço (`Numeric(10,2)`) e estoque (inteiro maior ou igual a zero).
- **Busca por nome** em clientes e produtos.
- **Segurança**: proteção CSRF em todos os formulários, rotas que alteram dados
  apenas via POST, cookie de sessão `SameSite=Lax`.
- **Páginas de erro** personalizadas (403, 404 e 500) e rollback automático em
  falhas de banco de dados.

## Tecnologias

- Python 3.12 (versão em que o projeto foi testado) ou superior
- Flask 3.1 e Flask-SQLAlchemy 3.1
- SQLite (padrão; pode ser trocado via `DATABASE_URL`)
- python-dotenv
- HTML, CSS e Bootstrap 5.3 (carregado por CDN, é necessário acesso à internet
  para o visual)

## Requisitos

- Python 3.12 ou superior (testado na 3.12)
- `pip` e `venv`
- Git (opcional)

## Instalação

```bash
# 1. Entre na pasta do projeto
cd sgc

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

## Configuração (variáveis de ambiente)

As configurações ficam em um arquivo `.env` na raiz do projeto. Esse arquivo
**não é versionado** (está no `.gitignore`). Crie-o a partir do modelo:

```bash
cp .env.example .env            # Windows: copy .env.example .env
```

| Variável       | Obrigatória | Descrição                                                                                                                        |
| -------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`   | Recomendada | Chave que assina a sessão. Sem ela, uma chave temporária é gerada a cada início e todos os usuários são deslogados ao reiniciar. |
| `DATABASE_URL` | Não         | URL do banco. Padrão: `sqlite:///sgc.db` (arquivo `instance/sgc.db`).                                                            |

Para gerar uma `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Nunca coloque a chave diretamente no código nem a envie ao repositório.

## Banco de dados

Não é necessário rodar nenhum comando: as tabelas (`usuarios`, `clientes` e
`produtos`) são criadas automaticamente na primeira execução. Com o SQLite, o
arquivo fica em `instance/sgc.db`.

- **Zerar o banco**: pare a aplicação e apague `instance/sgc.db`.
- **Outro banco** (por exemplo MySQL): defina `DATABASE_URL` no `.env` e instale
  o driver correspondente (por exemplo `pip install pymysql`, usando
  `mysql+pymysql://usuario:senha@host/banco`). Não há migrações: alterações nos
  modelos de tabelas já existentes exigem ajuste manual.

## Executando

```bash
python app.py
```

Acesse **http://127.0.0.1:5000**. No primeiro acesso, clique em
**Registrar-se**, crie um usuário e faça login.

> O servidor embutido do Flask, com `debug=True`, é apenas para desenvolvimento.
> Não o utilize em produção.

## Testes

A suíte usa apenas a biblioteca padrão (`unittest`) e um banco em memória, sem
tocar no banco real:

```bash
python -m unittest discover -v
```

Ela cobre autenticação, CSRF, CRUD de clientes e produtos, validações, busca,
páginas de erro e rollback em falha de banco.

## Estrutura do projeto

```
sgc/
├── app.py              # Criação da aplicação, configuração e rota inicial
├── models.py           # Modelos: Usuario, Cliente, Produto
├── auth.py             # Registro, login, logout e login_required
├── clientes.py         # CRUD de clientes e busca
├── produtos.py         # CRUD de produtos e busca
├── seguranca.py        # Proteção CSRF
├── erros.py            # Páginas de erro e tratamento de falhas de banco
├── requirements.txt
├── .env.example        # Modelo de configuração
├── static/
│   ├── css/style.css
│   └── js/excluir-modal.js
├── templates/
│   ├── base.html, index.html, _modal_excluir.html
│   ├── auth/           # login e registro
│   ├── clientes/       # lista e formulário
│   ├── produtos/       # lista e formulário
│   └── erros/          # 403, 404 e 500
└── tests/
    └── test_sgc.py
```

## Rotas

| Método    | Rota                    | Descrição                    |
| --------- | ----------------------- | ---------------------------- |
| GET       | `/`                     | Página inicial (exige login) |
| GET, POST | `/registro`             | Cadastro de usuário          |
| GET, POST | `/login`                | Login                        |
| POST      | `/logout`               | Logout                       |
| GET       | `/clientes?q=`          | Lista e busca de clientes    |
| GET, POST | `/cliente/novo`         | Cadastro de cliente          |
| GET, POST | `/cliente/editar/<id>`  | Edição de cliente            |
| POST      | `/cliente/excluir/<id>` | Exclusão de cliente          |
| GET       | `/produtos?q=`          | Lista e busca de produtos    |
| GET, POST | `/produto/novo`         | Cadastro de produto          |
| GET, POST | `/produto/editar/<id>`  | Edição de produto            |
| POST      | `/produto/excluir/<id>` | Exclusão de produto          |

Todas as rotas, exceto `/registro` e `/login`, exigem usuário autenticado.

## Regras de validação

- **Usuário**: nome de 3 a 30 caracteres (letras, números e `_`), e-mail válido,
  senha com no mínimo 8 caracteres; nome de usuário e e-mail únicos.
- **Cliente**: nome, e-mail e CPF/CNPJ obrigatórios; telefone opcional (10 ou
  11 dígitos). CPF (11 dígitos) ou CNPJ (14 dígitos), aceitos com ou sem
  pontuação e guardados só com números. E-mail e CPF/CNPJ únicos. Os dígitos
  verificadores do CPF/CNPJ não são conferidos.
- **Produto**: nome, categoria, preço e estoque obrigatórios; descrição opcional
  (até 500 caracteres). Preço de 0 a 99.999.999,99, com até 2 casas decimais
  (aceita `19,90` ou `19.90`). Estoque inteiro maior ou igual a zero.

## Limitações conhecidas

- No SQLite, a busca ignora maiúsculas/minúsculas apenas em letras sem acento.
- Não há perfis de permissão: todo usuário autenticado acessa todos os recursos.
- Não há paginação nas listagens.
- O Bootstrap é carregado por CDN.

## Status do projeto

- [x] Fase 1 — Setup e Ambiente
- [x] Fase 2 — Módulo de Usuários e Autenticação
- [x] Fase 3 — CRUD de Clientes
- [x] Fase 4 — CRUD de Produtos
- [x] Fase 5 — Usabilidade, Segurança e Filtros
- [x] Fase 6 — Documentação e Entrega
