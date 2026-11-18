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

O painel administrativo fica em `/admin/` e usa a tela comum de login. As credenciais de administrador ficam em um SQLite separado, fora do repositório, por padrão em `%LOCALAPPDATA%\EmpregaSerra\admin_users.sqlite3` no Windows ou em `~/.local/share/EmpregaSerra/admin_users.sqlite3` no Linux/macOS. O arquivo guarda somente hashes das senhas; os dados operacionais exibidos no painel continuam no banco principal. A conta que executa a aplicação deve ser a única com acesso ao arquivo e à pasta.

Crie uma conta administrativa pelo terminal. A senha é solicitada sem aparecer na tela e será temporária; no primeiro login pela página comum, o administrador deverá definir uma nova senha com pelo menos 12 caracteres:

```text
flask --app app create-admin email@exemplo.com
```

No Windows, execute a aplicação com a mesma conta de usuário que criou e protege a pasta em `%LOCALAPPDATA%`. Em hospedagem, defina `ADMIN_DATABASE_PATH` para um local privado acessível somente pela conta do serviço. Não coloque senhas nem o banco de administradores no GitHub.

O administrador pode cadastrar anunciantes e campanhas em `/admin/anunciantes` e `/admin/anuncios`. Campanhas novas começam pausadas. Ao ativar uma campanha, ela poderá aparecer na página inicial dentro do período configurado. As empresas continuam sem cobrança para cadastro e publicação de vagas.

Na visão geral do painel, os relatórios em PDF permitem baixar as vagas abertas, a relação de todos os candidatos cadastrados e os candidatos aprovados por empresas.

As páginas administrativas `/admin/empresas` e `/admin/candidatos` listam os cadastros da plataforma. O painel também exibe as empresas mais recentes e permite exportar a relação de empresas em PDF.

Para hospedagem, configure `SECRET_KEY`, `DATABASE_PATH` e, se necessário, `ADMIN_DATABASE_PATH`; defina `COOKIE_SECURE=1` quando o site estiver servido por HTTPS. Crie as contas administrativas no ambiente de hospedagem com o comando acima. Use um servidor WSGI de produção; não publique com o servidor de desenvolvimento do Flask.
