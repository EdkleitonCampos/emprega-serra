# Emprega Serra 3.0.2

## Identidade visual e experiência
- Consolidação da identidade Sertão contemporâneo com verde mandacaru, areia, terracota e amarelo-sol.
- Nova camada de acabamento visual aplicada globalmente às páginas públicas, formulários, painéis de candidato e empresa e administração.
- Hero da página inicial com fotografia real de Serra Talhada, contraste reforçado e busca responsiva.
- Cartões, formulários, tabelas, botões, estados de foco e layouts móveis padronizados.
- Texto de apresentação da página inicial atualizado para destacar a proposta regional.
- Texto de cursos ajustado para não sugerir parceria institucional não confirmada.
- Metadados de descrição e cor do navegador atualizados.

## Integridade do produto
- Funcionalidades de cadastro, autenticação, vagas, candidaturas, convites, serviços, cursos, mapa, publicidade e administração preservadas.
- Banco demonstrativo original preservado; o banco de administradores e a chave de sessão local não são distribuídos no pacote limpo.
- Documentação, versão e roteiro de apresentação atualizados.

## Verificações
- Compilação dos módulos Python: aprovada.
- Compilação sintática dos templates Jinja: aprovada.
- Integridade do SQLite e chaves estrangeiras: aprovadas.
- Testes automatizados de fluxos administrativos, candidato, empresa/vagas e serviços: 4 aprovados.
- Rotas públicas principais verificadas com o cliente de testes do Flask.
- Não foi realizada inspeção visual em navegador nesta etapa de empacotamento.
