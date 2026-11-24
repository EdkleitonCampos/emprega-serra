# Segurança do Emprega Serra

## Proteções incluídas nesta versão

- Token CSRF validado em todas as requisições que alteram dados.
- Limitação de requisições e tentativas de login/cadastro via Flask-Limiter.
- Cookies de sessão HttpOnly e SameSite=Lax; Secure habilitável em HTTPS.
- Renovação da sessão após autenticação.
- Cabeçalhos contra MIME sniffing, clickjacking e exposição excessiva de referenciador.
- Content Security Policy inicial.
- Limite de tamanho de requisições.
- Consultas SQL parametrizadas no código da aplicação.
- Senhas armazenadas com hash Werkzeug, nunca em texto puro.
- Área administrativa separada e protegida.
- Backup consistente do SQLite e verificação de integridade.

## Limites importantes

Nenhum sistema pode prometer proteção contra todo tipo de invasão. Segurança depende também de hospedagem, atualização de dependências, configuração de HTTPS, senhas fortes, controle do computador/servidor e monitoramento.

O limitador usa `memory://` por padrão para facilitar execução local. Em produção com vários processos/instâncias, configure `RATELIMIT_STORAGE_URI` para um Redis privado e gerenciado. Não exponha o Redis à internet.

## Antes de publicar na internet

1. Hospede em servidor atualizado e confiável.
2. Configure HTTPS obrigatório e `COOKIE_SECURE=1`.
3. Defina `SECRET_KEY` longa, aleatória e exclusiva via variável de ambiente.
4. Configure `DATABASE_PATH` em armazenamento persistente e restrito.
5. Configure `RATELIMIT_STORAGE_URI` com Redis privado para várias instâncias.
6. Não publique `.db`, `instance/`, backups, `.env` ou credenciais no Git.
7. Use usuário de sistema sem privilégios administrativos.
8. Configure backup externo criptografado e teste restauração.
9. Mantenha dependências atualizadas e revise logs.
10. Publique política de privacidade e cumpra a LGPD para dados pessoais.

## Acesso pelo celular

- Mesma rede Wi-Fi: execute `iniciar_rede_local.bat`; o script mostra o IP local. No celular, conectado ao mesmo Wi-Fi, abra `http://IP-DO-COMPUTADOR:5000`.
- Pessoas fora da rede: é necessário hospedar o sistema na internet com HTTPS e domínio/URL público. O modo de rede local não cria um endereço público.
