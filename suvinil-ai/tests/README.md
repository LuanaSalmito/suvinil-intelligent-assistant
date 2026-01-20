# Testes Unitários - Suvinil AI

Este diretório contém os testes unitários do projeto Suvinil AI.

## Estrutura de Testes

```
tests/
├── __init__.py                  # Pacote de testes
├── conftest.py                  # Configurações e fixtures compartilhadas
├── test_security.py             # Testes de segurança (hash, tokens)
├── test_user_schemas.py         # Testes de schemas de usuário
├── test_paint_schemas.py        # Testes de schemas de tinta
├── test_paint_models.py         # Testes de models de tinta (enums)
├── test_config.py               # Testes de configuração
└── test_user_repository.py      # Testes de repositório de usuários
```

## Arquivos de Teste

### 1. `test_security.py`
Testa funcionalidades de segurança:
- Hash de senhas (bcrypt)
- Verificação de senhas
- Criação e decodificação de tokens JWT
- Validação de expiração de tokens

### 2. `test_user_schemas.py`
Testa schemas de validação de usuários:
- Criação de usuários (UserCreate)
- Atualização de usuários (UserUpdate)
- Login de usuários (UserLogin)
- Tokens (Token, TokenData)
- Validação de email e campos obrigatórios

### 3. `test_paint_schemas.py`
Testa schemas de validação de tintas:
- Criação de tintas (PaintCreate)
- Atualização de tintas (PaintUpdate)
- Conversão de features (string → lista)
- População automática de aplicação
- Validação de enums

### 4. `test_paint_models.py`
Testa enums e models de tinta:
- Ambiente (Interno, Externo, Interno/Externo)
- Acabamento (Fosco, Acetinado, Brilhante)
- Linha (Premium, Standard)
- Aliases de enums (Environment, FinishType, PaintLine)

### 5. `test_config.py`
Testa configurações da aplicação:
- Valores padrão de configuração
- Validação de SECRET_KEY
- Configurações de JWT
- Configurações de OpenAI
- Ambientes (development, test, production)

### 6. `test_user_repository.py`
Testa operações de repositório de usuários:
- Busca por ID, email, username
- Criação de usuários
- Atualização de usuários
- Exclusão de usuários
- Paginação

## Como Executar os Testes

### Instalar Dependências

```bash
cd suvinil-ai
pip install -r requirements.txt
```

### Executar Todos os Testes

```bash
pytest
```

### Executar Testes com Cobertura

```bash
pytest --cov=app --cov-report=html
```

O relatório HTML será gerado em `htmlcov/index.html`.

### Executar Testes Específicos

```bash
# Executar apenas um arquivo
pytest tests/test_security.py

# Executar uma classe específica
pytest tests/test_security.py::TestPasswordHashing

# Executar um teste específico
pytest tests/test_security.py::TestPasswordHashing::test_get_password_hash_creates_hash
```

### Executar com Saída Verbosa

```bash
pytest -v
```

### Executar em Modo Quiet

```bash
pytest -q
```

### Ver Print Statements

```bash
pytest -s
```

## Fixtures Disponíveis

As fixtures são definidas em `conftest.py` e estão disponíveis para todos os testes:

- `test_settings`: Configurações de teste
- `sample_user_data`: Dados de usuário de exemplo
- `sample_paint_data`: Dados de tinta de exemplo
- `token_expiry`: Tempo de expiração de token

## Cobertura de Testes

Os testes cobrem:
- ✅ Módulo de segurança (security.py)
- ✅ Schemas de usuário (schemas/user.py)
- ✅ Schemas de tinta (schemas/paint.py)
- ✅ Models de tinta (models/paint.py)
- ✅ Configurações (core/config.py)
- ✅ Repositório de usuários (repositories/user_repository.py)

## Boas Práticas

1. **Nomenclatura**: Use nomes descritivos para testes
   - `test_<funcionalidade>_<cenário>`
   - Ex: `test_verify_password_correct_password`

2. **Organização**: Agrupe testes relacionados em classes
   - Ex: `class TestPasswordHashing`

3. **Arrange-Act-Assert**: Estruture os testes em 3 partes
   - Arrange: Configure o ambiente e dados
   - Act: Execute a ação
   - Assert: Verifique o resultado

4. **Mocks**: Use mocks para isolar dependências
   - Use `unittest.mock` ou `pytest-mock`
   - Evite dependências de banco de dados em testes unitários

5. **Fixtures**: Reutilize configurações comuns
   - Defina fixtures em `conftest.py`
   - Use fixtures para dados de teste

## Relatórios de Cobertura

Após executar os testes com cobertura, você pode ver:

- **Terminal**: Relatório resumido no terminal
- **HTML**: Relatório detalhado em `htmlcov/index.html`
- **XML**: Relatório para CI/CD em `coverage.xml`

## Integração Contínua

Para integrar com CI/CD, adicione ao seu pipeline:

```yaml
# Exemplo para GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Contribuindo

Ao adicionar novas funcionalidades:

1. Escreva testes para o novo código
2. Mantenha a cobertura acima de 80%
3. Execute todos os testes antes de fazer commit
4. Adicione documentação para fixtures complexas

## Suporte

Para problemas ou dúvidas sobre os testes, consulte:
- Documentação do Pytest: https://docs.pytest.org/
- Documentação do pytest-cov: https://pytest-cov.readthedocs.io/
