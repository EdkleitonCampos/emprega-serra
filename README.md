# Emprega Serra

Aplicação web para aproximar candidatos e empresas de Serra Talhada. O projeto usa Flask, SQLite, HTML, CSS e JavaScript e inclui cadastro e login, além de publicação e gerenciamento de vagas por empresas.

## Requisitos

- Python 3.10 ou superior
- pip

## Executar localmente

No PowerShell, na pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000 no navegador. O banco SQLite é criado automaticamente na primeira execução; o arquivo do banco é local e não deve ser enviado ao GitHub.

Para produção, defina uma chave secreta estável antes de iniciar a aplicação:

```powershell
$env:SECRET_KEY = "substitua-por-uma-chave-secreta-forte"
python app.py
```

Sem essa variável, a aplicação gera uma chave temporária para uso local. Sessões locais deixam de valer quando o processo reinicia.

## Estrutura

- `app.py`: rotas e lógica da aplicação Flask.
- `database.py`: criação e conexão com o banco SQLite.
- `templates/`: páginas HTML.
- `static/`: arquivos CSS, JavaScript e imagens.
- `requirements.txt`: dependências Python.
