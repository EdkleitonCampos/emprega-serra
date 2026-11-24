# Emprega Serra

Plataforma web de oportunidades de emprego para Serra Talhada e região. Desenvolvida em Python/Flask, SQLite, HTML, CSS e JavaScript.

## Emprega Serra 3.0.2 — Sertão contemporâneo

Esta edição consolida uma identidade visual regional e profissional: verde mandacaru, areia, terracota e amarelo-sol. A fotografia real de Serra Talhada conduz a página inicial; formulários, páginas de serviços e cursos, mapa, painéis e administração seguem a mesma linguagem visual responsiva.

## Funcionalidades

- Cadastro e autenticação de candidatos e empresas.
- Perfil profissional e currículo do candidato.
- Busca, detalhes e candidatura às vagas.
- Painel do candidato com acompanhamento das candidaturas.
- Painel empresarial para criar, editar, pausar e encerrar vagas.
- Gerenciamento de candidaturas e atualização de etapas.
- Convites de entrevista gratuitos com liberação dos dados após o aceite, sem cobrança.
- Diretório de serviços locais: empresas e profissionais autônomos podem anunciar gratuitamente e interessados podem pesquisar por categoria e cidade.
- Vitrine de plataformas com cursos gratuitos para qualificação.
- Mapa regional com contagem de vagas abertas por cidade.
- Notificações internas de convites e respostas de entrevista.
- Painel administrativo separado, com gerenciamento de usuários, empresas, candidatos, vagas, anunciantes e campanhas.
- Relatórios PDF e CSV.
- Filtros por texto e status em consultas administrativas.
- Banco de dados SQLite com criação/migração de tabelas e índices.
- Proteções CSRF, rate limiting, cookies de sessão protegidos e cabeçalhos HTTP de segurança.
- Backup consistente do banco SQLite.

A plataforma é gratuita para candidatos e empresas: cadastro, publicação de vagas, candidaturas, convites e entrevistas não têm taxas. A única fonte de receita prevista é a publicidade, com anunciantes e campanhas gerenciados pelo painel administrativo.

## Gratuidade e publicidade

Não existe cobrança por cadastro, publicação de vagas, candidaturas, convites, aceite de entrevistas ou contratação. A monetização prevista é exclusivamente por publicidade, com anunciantes e campanhas administrados no painel administrativo.

## Dados de demonstração incluídos

Esta edição acompanha um banco SQLite já preenchido com 10 empresas fictícias, 25 candidatos fictícios, 20 vagas, 50 candidaturas, 4 anunciantes e 4 campanhas publicitárias ativas. Os anúncios aparecem na página inicial e também ficam disponíveis no painel administrativo.

- Senha de todas as contas de empresas e candidatos: `1234567890`.
- Relação completa de nomes e e-mails: `CONTAS_DEMONSTRACAO.txt`. Os e-mails são identificadores fictícios no formato solicitado; não são caixas de e-mail reais.
- Primeiro acesso administrativo: `admin@empregaserra.com` / `Admin@1234567890`. O sistema exige a troca dessa senha no primeiro acesso.
- As campanhas publicitárias usam links de exemplo (`example.com`) e não representam anunciantes reais.

Os dados são destinados somente a demonstrações. Não publique o sistema com essas credenciais.

## Requisitos

- Windows 10/11 ou Linux/macOS.
- Python 3.10 ou superior.
- Internet na primeira instalação para baixar dependências.

## Rodar no computador

1. Extraia a pasta do projeto para um local novo, sem substituir arquivos de uma versão anterior.
2. Execute `iniciar_emprega_serra.bat`.
3. O script confere as dependências, prepara os dados demonstrativos sem duplicá-los e inicia o servidor. A primeira instalação precisa de internet para baixar as dependências.
4. Abra `http://127.0.0.1:5000`.
5. Para encerrar, pressione `CTRL+C` no terminal.

## Acessar pelo celular na mesma rede Wi-Fi

1. Conecte o computador e o celular à mesma rede Wi-Fi.
2. No computador, execute `iniciar_rede_local.bat`.
3. O terminal mostrará os endereços IPv4 do computador.
4. No navegador do celular, abra `http://IP-DO-COMPUTADOR:5000` (substitua pelo IP exibido).
5. Se o Windows Firewall perguntar, permita acesso somente em redes privadas confiáveis.

Se o celular não conseguir abrir o endereço, confira se a rede do Windows está definida como **Privada**. Como último passo, execute `liberar_firewall_rede_privada.ps1` no PowerShell como Administrador; ele libera somente a porta 5000 em perfil de rede privada.

Esse modo serve para demonstração na mesma rede local. Não torna o site público na internet e não deve ser usado em Wi-Fi público.

## Compartilhar com pessoas fora da sua rede

Para que pessoas em outras casas/cidades acessem pelo celular, publique o projeto em uma hospedagem web com HTTPS e armazenamento persistente. O arquivo `Procfile` fornece o comando WSGI de referência para serviços compatíveis com Gunicorn. Configure as variáveis de ambiente descritas em `.env.example`, use armazenamento persistente para `DATABASE_PATH` e configure `COOKIE_SECURE=1`.

O servidor local do Flask e o modo Wi-Fi local não são hospedagem pública. Não exponha diretamente a porta 5000 do computador na internet.

## Acesso administrativo

Na primeira execução, o pacote de demonstração cria automaticamente `admin@empregaserra.com` com a senha temporária `Admin@1234567890`. Entre em `http://127.0.0.1:5000/login`; será obrigatório definir uma senha nova com pelo menos 12 caracteres. O painel fica em `/admin/`.

Para criar outros administradores depois, use `criar_administrador.bat`. As contas administrativas são armazenadas em banco separado, fora do banco principal.

## Banco de dados e backups

- O banco principal é `emprega_serra.db` e já acompanha os dados fictícios desta demonstração.
- O script `popular_dados_demo.py` é idempotente e não duplica os registros quando executado novamente.
- Na inicialização, o sistema cria tabelas ausentes e aplica as migrações previstas.
- Antes de qualquer atualização, mantenha uma cópia externa do banco.
- Execute `backup_emprega_serra.bat` para criar um backup consistente em `backups/`.
- O script mantém até 30 cópias recentes.
- O banco de administradores fica separado na pasta de dados privada do usuário.

## Segurança

Consulte `SECURITY.md`. Nenhum software pode garantir proteção contra todos os tipos de ataque. A proteção real também depende da hospedagem, HTTPS, configuração de segredos, atualização contínua, backups e operação segura.

Para produção com múltiplos processos, configure `RATELIMIT_STORAGE_URI` com Redis privado. Não deixe o modo debug ativado nem publique arquivos `.db`, `.env`, backups ou credenciais no Git.

## Executar testes locais

Com o ambiente virtual ativado e as dependências do projeto instaladas, execute:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam uma cópia temporária do banco demonstrativo e removem os registros de teste; o banco original não é alterado.

## Requisitos do projeto de conclusão

O arquivo `REQUISITOS_ATENDIDOS.md` mapeia os itens solicitados pelo professor para as funcionalidades e telas do sistema.

## Estrutura principal

- `app.py`: rotas da aplicação.
- `database.py`: conexão, criação e migrações do banco principal.
- `admin.py`: rotas administrativas, relatórios e CRUD.
- `admin_database.py`: armazenamento separado dos administradores.
- `wsgi.py`: ponto de entrada WSGI.
- `templates/`: páginas HTML/Jinja.
- `static/`: CSS, JavaScript e imagens.
- `backup_database.py`: backup consistente do banco.
- `SECURITY.md`: proteções e checklist de publicação.


## Versão 3.0.2
Consulte `CHANGELOG_3.0.2.md` para o acabamento visual final, a padronização da identidade regional e as verificações realizadas para esta entrega.

## Apresentação
O arquivo `Apresentacao_Emprega_Serra_3.0.2.pptx` acompanha o pacote de entrega. O roteiro sugerido está em `ROTEIRO_APRESENTACAO.md`.
