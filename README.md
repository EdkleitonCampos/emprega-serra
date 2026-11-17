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


## Administração e publicidade

O painel administrativo fica em `/admin/`. A primeira conta de administrador é criada/promovida somente quando as variáveis de ambiente `ADMIN_EMAIL` e `ADMIN_PASSWORD` estão configuradas. Use uma senha forte com pelo menos 12 caracteres. Não coloque essas credenciais no código nem no GitHub.

Exemplo no PowerShell (a partir da pasta do projeto):

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:ADMIN_EMAIL = "seu-email-administrador"
$env:ADMIN_PASSWORD = "escolha-uma-senha-forte-com-12-ou-mais-caracteres"
python app.py
```

Depois entre pela tela normal de login com o e-mail e a senha configurados. O sistema encaminha a conta administrativa para `/admin/`. Se o e-mail já pertencer a uma conta existente, a inicialização a promove para administrador e atualiza a senha conforme a variável `ADMIN_PASSWORD`; configure com cuidado.

O administrador pode cadastrar anunciantes e campanhas em `/admin/anunciantes` e `/admin/anuncios`. Campanhas novas começam pausadas. Ao ativar uma campanha, ela poderá aparecer na página inicial dentro do período configurado. As empresas continuam sem cobrança para cadastro e publicação de vagas.

Para hospedagem, configure `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `DATABASE_PATH` (se necessário) e `COOKIE_SECURE=1` quando o site estiver servido por HTTPS. Use um servidor WSGI de produção; não publique com o servidor de desenvolvimento do Flask.
