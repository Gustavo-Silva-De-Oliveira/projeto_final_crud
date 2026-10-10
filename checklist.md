# Checklist de Desenvolvimento – Projeto SGC (Expandido)

## Informações do Aluno

- **Nome:** Gustavo Silva De Oliveira
- **Turma:** N19
- **Data de início:** 08/10/2026

---

## Fase 1: Setup e Ambiente

- [x] Criar estrutura do projeto (`app.py`, `templates/`)
- [x] Inicializar Git e configurar `.gitignore`
- [x] Configurar `requirements.txt` (Flask, Flask-SQLAlchemy, etc.)
- [x] Criar template base com Bootstrap 5 e barra de navegação responsiva
- [x] **COMMIT:** "Setup inicial do projeto SGC"

---

## Fase 2: Módulo de Usuários e Autenticação

- [x] Modelar classe `Usuario` (`id`, `username`, `email`, `senha_hash`)
- [x] Criar rota e formulário de Registro de Usuários com hashing de senha
- [x] Criar rota e tela de Login validando hash
- [x] Criar rota de Logout limpando a sessão
- [x] Implementar controle de acesso (bloquear páginas do sistema para não autenticados)
- [x] **COMMIT:** "Implementa sistema de autenticação e sessões"

---

## Fase 3: CRUD de Clientes

- [x] Modelar classe `Cliente` (`id`, `nome`, `email`, `telefone`, `cpf_cnpj`, `data_cadastro`)
- [x] Rota `GET /clientes` com listagem em tabela
- [x] Rotas `GET` e `POST /cliente/novo` para cadastro
- [x] Rotas `GET` e `POST /cliente/editar/<id>` para edição
- [x] Rota `POST /cliente/excluir/<id>` com confirmação
- [x] Validações de duplicidade de e-mail/documento
- [x] **COMMIT:** "Implementa CRUD completo de clientes"

---

## Fase 4: CRUD de Produtos

- [x] Modelar classe `Produto` (`id`, `nome`, `preco`, `estoque`, `categoria`, `descricao`)
- [x] Implementar Listagem com tabela estilizada
- [x] Implementar Criação, Edição e Exclusão
- [x] Validação de dados numéricos (preço e estoque >= 0)
- [x] **COMMIT:** "Implementa CRUD completo de produtos"

---

## Fase 5: Usabilidade, Segurança e Filtros

- [x] Campo de busca ou filtro (por nome em Produtos e Clientes)
- [x] Exibição dinâmica da barra de navegação (exibir nome do usuário logado)
- [x] Tratamento de erros de banco com `db.session.rollback()`
- [x] Páginas personalizadas de erro 404 e 403 (Acesso Negado)
- [x] Mensagens de feedback (`flash`) em todas as operações
- [x] **COMMIT:** "Aprimora segurança, feedbacks e filtros de busca"

---

## Fase 6: Documentação e Entrega

- [x] Documentar endpoints e funções com docstrings
- [x] Criar `README.md` completo com guia de instalação, informações do projeto e tecnologias utilizadas
- [x] Limpar código, imports não utilizados e prints
- [x] **COMMIT FINAL:** "Entrega da versão final do SGC"
