# Emprega Serra 3.0.0 — Sertão Tecnológico

## O que mudou
- Nova identidade visual com paleta mandacaru, verde profundo, areia, terracota e amarelo-sol, aplicada ao site público, formulários e painéis.
- Navegação responsiva com acesso a Serviços, Cursos e Mapa.
- Diretório de serviços locais: contas de candidato (profissionais/pessoas físicas) e empresas podem publicar anúncios gratuitos; visitantes podem pesquisar por texto e cidade; contato via WhatsApp quando o anunciante informa o número; o autor pode remover o próprio anúncio.
- Página de cursos com links para plataformas de qualificação gratuita.
- Mapa regional centrado em Serra Talhada, com lista de cidades que possuem vagas abertas e acesso ao OpenStreetMap.
- Notificações internas para novos convites de entrevista e aceite de convite, com opção de marcar como lida.
- Contato de WhatsApp para empresas nas vagas da página inicial quando o telefone estiver cadastrado.
- Publicidade continua gerenciada pelo administrador através dos módulos existentes de anunciantes e campanhas.
- Removida a criação de cobranças e a liberação condicionada a pagamento: o aceite do convite libera imediatamente local, data e horário da entrevista.

## Regras comerciais
Cadastro, publicação de vagas, candidaturas, convites, aceite de entrevista e contratação são gratuitos. A única receita planejada é publicidade.

## Compatibilidade
O banco de demonstração foi preservado e migrado com as tabelas `servicos` e `notificacoes`. A tabela legada de cobranças, vazia nesta base, foi mantida no arquivo SQLite original por compatibilidade, mas não há rotas, telas, variáveis de pagamento ou código da aplicação que criem ou processem cobranças.

## Verificações realizadas
- Compilação sintática dos módulos Python (`py_compile`).
- Compilação dos 27 templates Jinja.
- Migração do banco SQLite, `PRAGMA integrity_check = ok` e nenhuma violação de chave estrangeira.
- Contagens de demonstração preservadas: 10 empresas, 25 candidatos, 20 vagas, 50 candidaturas, 4 anunciantes e 4 campanhas.

## Limitação de validação
O ambiente de montagem não tinha Flask/Flask-Limiter instalados e não conseguiu acessar a internet para instalá-los. Por isso, não foi possível executar uma inicialização HTTP real nesta sessão. O `iniciar_emprega_serra.bat` instala as dependências listadas em `requirements.txt` na primeira execução, quando o computador estiver conectado à internet.
