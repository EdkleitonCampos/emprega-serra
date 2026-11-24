# Atendimento aos requisitos do projeto de conclusão

Documento de rastreabilidade baseado na lista fornecida pelo professor.

| Requisito | Onde está atendido |
|---|---|
| Cadastro de usuários | `/cadastro/candidato` e `/cadastro/empresa` |
| Consulta e listagem de usuários | Painel administrativo `/admin/usuarios` |
| Edição de usuários | `/admin/usuarios/<id>/editar` |
| Exclusão de usuários | `/admin/usuarios/<id>/excluir`, com exclusão transacional de registros relacionados |
| Validação de dados obrigatórios | Validações nos formulários e nas rotas de cadastro/edição |
| CRUD de outra entidade | Vagas: cadastro e edição na área empresarial; listagem, filtros e exclusão no painel administrativo |
| Listar, cadastrar, editar, visualizar e excluir registros | Vagas e usuários; detalhes de vagas disponíveis ao público e ao candidato |
| Relatórios | Relatórios administrativos |
| Exportar PDF | Rotas `/admin/exportar/*.pdf` |
| Exportar CSV | Rotas `/admin/exportar/*.csv` |
| Filtros | Filtros por texto e status em `/admin/usuarios` e `/admin/vagas` |
| Conexão com banco de dados | SQLite em `database.py` |
| Criação de tabelas | `criar_banco()` |
| Inserção, consulta, atualização e exclusão | Rotas de cadastro, edição, consulta e exclusão |
| Integridade e consistência | Chaves estrangeiras, restrições únicas, transações e verificação de integridade nos backups |
| Interface intuitiva e organizada | Templates HTML, CSS responsivo e menus por perfil |
| Mensagens de sucesso e erro | Mensagens flash nas operações |
| Python | Flask |
| Código modular | `app.py`, `database.py`, `admin.py`, `admin_database.py` |
| Separação HTML/CSS/JavaScript | `templates/` e `static/` |

## Demonstração sugerida para avaliação

1. Cadastrar um candidato e entrar na conta.
2. Cadastrar uma empresa e publicar uma vaga.
3. Entrar como candidato, pesquisar a vaga e se candidatar.
4. Voltar como empresa e atualizar a etapa da candidatura.
5. Entrar como administrador e localizar usuário/vaga usando filtros.
6. Editar e excluir um registro de teste.
7. Exportar relatórios em PDF e CSV.
8. Mostrar o acesso responsivo em um celular.

Faça a demonstração com registros fictícios ou autorizados. Não exponha dados pessoais reais do banco durante a apresentação.


## Recursos adicionados na versão 3.0

- Diretório de serviços: `/servicos`, com anúncios de empresas e profissionais cadastrados, busca por texto/cidade e contato por WhatsApp quando informado.
- Cursos e qualificação: `/cursos`, com acesso a plataformas de cursos gratuitos.
- Mapa regional: `/mapa`, com mapa aberto e resumo das cidades com vagas abertas.
- Notificações internas: avisos de novos convites e de aceite de entrevista, com opção de marcar como lida.
- Publicidade: anunciantes e campanhas seguem gerenciados pelo painel administrativo; esta é a única receita prevista da plataforma.
- Gratuidade: cadastro, vagas, candidaturas, convites e entrevistas sem taxas.
