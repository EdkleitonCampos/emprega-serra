# Validação técnica — Emprega Serra 3.0.2

## Verificações executadas

- `py_compile` nos módulos Python do projeto: aprovado.
- Compilação sintática de todos os templates Jinja: aprovada.
- SQLite: `PRAGMA integrity_check` retornou `ok`.
- Integridade referencial: `PRAGMA foreign_key_check` sem violações.
- Testes automatizados: 4 aprovados (administração, cadastro/login/perfil de candidato, publicação de vaga e candidatura, publicação/pesquisa/exclusão de serviço).
- Cliente de testes Flask: página inicial, serviços, cursos, mapa, login e cadastros retornaram HTTP 200.
- Os testes utilizam cópia temporária do banco demonstrativo; o banco incluído no pacote não é alterado.

## Limite da validação

A execução automatizada confirma os fluxos cobertos pelos testes e a renderização das rotas verificadas pelo cliente de testes. Não foi realizada inspeção visual manual em navegadores diferentes nem teste de publicação em hospedagem externa. Antes de publicar na internet, siga integralmente o checklist de `SECURITY.md`.

## Dados de demonstração

O banco incluído contém registros fictícios para facilitar a apresentação. As credenciais listadas em `CONTAS_DEMONSTRACAO.txt` são públicas e servem somente para demonstração local ou em rede privada controlada. Não publique o sistema na internet com essas credenciais.
