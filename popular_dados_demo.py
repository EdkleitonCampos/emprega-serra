"""Popula o Emprega Serra com dados inteiramente ficticios para demonstracao.

Seguro para executar mais de uma vez: a carga inicial e registrada na tabela
_dados_demo e nao duplica contas, vagas, candidaturas ou campanhas.
"""
import unicodedata
import hashlib
import secrets
try:
    from werkzeug.security import generate_password_hash
except ImportError:
    def generate_password_hash(password, method="pbkdf2:sha256:600000"):
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 600000)
        return f"pbkdf2:sha256:600000${salt}${digest.hex()}"
from database import criar_banco, conectar

SENHA_DEMO = "1234567890"

def slug_email(nome):
    normalizado = unicodedata.normalize("NFKD", nome)
    sem_acentos = "".join(ch for ch in normalizado if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in sem_acentos if ch.isalnum()) + "@gmail.com"

EMPRESAS = [
    ("Sertão Atacarejo", "Marcos Vinícius", "Serra Talhada", "Comércio varejista e atacadista de alimentos e produtos em geral."),
    ("Clínica Vida Plena", "Patrícia Nogueira", "Serra Talhada", "Atendimento integrado em saúde, consultas e exames."),
    ("Grupo São Miguel", "Roberto Almeida", "Serra Talhada", "Serviços administrativos, logística e atendimento ao cliente."),
    ("Construtora Horizonte", "André Luiz", "Serra Talhada", "Construção civil, reformas e obras residenciais e comerciais."),
    ("Supermercado Bom Preço", "Luciana Ferreira", "Serra Talhada", "Supermercado com atendimento à população da região."),
    ("Auto Peças Nordeste", "Rafael Barbosa", "Serra Talhada", "Comércio de peças, acessórios e serviços automotivos."),
    ("Hotel Pajeú", "Camila Santos", "Serra Talhada", "Hospedagem, recepção e serviços de turismo e eventos."),
    ("Farmácia Central", "Juliana Carvalho", "Serra Talhada", "Comércio farmacêutico e atendimento ao público."),
    ("Tech Sertão Soluções", "Felipe Gomes", "Serra Talhada", "Tecnologia, suporte técnico e soluções digitais para empresas."),
    ("Padaria Sabor da Serra", "Eduardo Lima", "Serra Talhada", "Panificação, confeitaria e atendimento no balcão."),
]

CANDIDATOS = [
    ("Carlos Alberto", "Serra Talhada", "Ensino médio completo", "Auxiliar administrativo e atendimento", "Atendimento, informática básica, organização"),
    ("Ana Beatriz", "Serra Talhada", "Ensino superior incompleto", "Recepção e rotinas administrativas", "Excel, atendimento, comunicação"),
    ("João Pedro", "Triunfo", "Ensino médio completo", "Vendas e comércio", "Vendas, negociação, atendimento"),
    ("Maria Eduarda", "Serra Talhada", "Técnico completo", "Técnica de enfermagem", "Cuidados, trabalho em equipe, organização"),
    ("Lucas Gabriel", "São José do Belmonte", "Ensino médio completo", "Estoquista", "Estoque, conferência, agilidade"),
    ("Juliana Alves", "Serra Talhada", "Ensino superior completo", "Assistente financeira", "Excel, financeiro, contas a pagar"),
    ("Pedro Henrique", "Serra Talhada", "Ensino médio completo", "Motorista e entregador", "Direção, pontualidade, logística"),
    ("Beatriz Costa", "Flores", "Ensino médio completo", "Atendente", "Atendimento, caixa, comunicação"),
    ("Rafael Oliveira", "Serra Talhada", "Técnico completo", "Suporte de informática", "Windows, manutenção, redes"),
    ("Gabriela Souza", "Calumbi", "Ensino médio completo", "Auxiliar de produção", "Produção, qualidade, organização"),
    ("Matheus Ferreira", "Serra Talhada", "Ensino superior incompleto", "Marketing e mídias sociais", "Canva, redes sociais, criatividade"),
    ("Larissa Rodrigues", "Afogados da Ingazeira", "Ensino médio completo", "Operadora de caixa", "Caixa, atendimento, matemática"),
    ("Bruno Martins", "Serra Talhada", "Ensino médio completo", "Pedreiro", "Alvenaria, acabamento, obras"),
    ("Camila Ribeiro", "Serra Talhada", "Técnico completo", "Recepcionista", "Recepção, agenda, atendimento"),
    ("Felipe Santos", "Custódia", "Ensino médio completo", "Auxiliar de logística", "Separação, expedição, estoque"),
    ("Isabela Lima", "Serra Talhada", "Ensino superior completo", "Professora", "Educação, planejamento, comunicação"),
    ("André Carvalho", "Triunfo", "Ensino médio completo", "Vendedor", "Vendas, metas, relacionamento"),
    ("Vitória Almeida", "Serra Talhada", "Ensino médio completo", "Auxiliar de serviços gerais", "Limpeza, organização, responsabilidade"),
    ("Gustavo Nunes", "Serra Talhada", "Técnico completo", "Eletricista", "Instalações, manutenção, segurança"),
    ("Letícia Barbosa", "Flores", "Ensino médio completo", "Assistente de RH", "Pacote Office, recrutamento, comunicação"),
    ("Thiago Mendes", "Serra Talhada", "Ensino médio completo", "Mecânico", "Mecânica, diagnóstico, manutenção"),
    ("Amanda Rocha", "São José do Belmonte", "Ensino superior incompleto", "Assistente comercial", "Vendas, atendimento, prospecção"),
    ("Daniel Costa", "Serra Talhada", "Ensino médio completo", "Auxiliar de cozinha", "Cozinha, higiene, trabalho em equipe"),
    ("Nicole Pereira", "Serra Talhada", "Técnico completo", "Técnica em segurança do trabalho", "Segurança, prevenção, documentação"),
    ("Samuel Araujo", "Calumbi", "Ensino médio completo", "Jovem aprendiz administrativo", "Informática, organização, aprendizagem"),
]

VAGAS = [
    (0, "Operador(a) de caixa", "Atendimento no caixa, registro de compras e apoio aos clientes.", "Ensino médio completo; boa comunicação.", "R$ 1.650,00"),
    (0, "Repositor(a) de mercadorias", "Organização de gôndolas, reposição e conferência de produtos.", "Disponibilidade de horário e organização.", "R$ 1.550,00"),
    (1, "Recepcionista", "Recepcionar pacientes, organizar agendas e apoiar a equipe.", "Ensino médio completo e informática básica.", "R$ 1.700,00"),
    (1, "Auxiliar de serviços gerais", "Manter ambientes limpos e organizados.", "Atenção, responsabilidade e pontualidade.", "A combinar"),
    (2, "Assistente administrativo", "Apoiar rotinas administrativas, planilhas e documentos.", "Pacote Office e boa comunicação.", "R$ 1.800,00"),
    (2, "Auxiliar de logística", "Apoiar recebimento, separação e expedição de mercadorias.", "Organização e disposição para atividades operacionais.", "R$ 1.750,00"),
    (3, "Pedreiro", "Executar serviços de alvenaria e acabamento em obras.", "Experiência comprovada na função.", "A combinar"),
    (3, "Servente de obras", "Apoiar profissionais e manter o canteiro organizado.", "Disponibilidade e responsabilidade.", "R$ 1.600,00"),
    (4, "Atendente de supermercado", "Atendimento ao cliente e organização de produtos.", "Ensino médio completo.", "R$ 1.550,00"),
    (4, "Fiscal de loja", "Apoiar prevenção de perdas e organização da loja.", "Atenção e boa comunicação.", "R$ 1.700,00"),
    (5, "Vendedor(a) de autopeças", "Atender clientes e identificar peças e acessórios.", "Conhecimento básico de peças automotivas.", "R$ 1.650,00 + comissão"),
    (5, "Auxiliar de estoque", "Receber, armazenar e separar peças.", "Organização e informática básica.", "R$ 1.600,00"),
    (6, "Recepcionista de hotel", "Realizar check-in, check-out e atendimento aos hóspedes.", "Boa comunicação e disponibilidade de horário.", "R$ 1.700,00"),
    (6, "Camareiro(a)", "Organizar quartos e áreas de hospedagem.", "Capricho e atenção aos detalhes.", "R$ 1.550,00"),
    (7, "Atendente de farmácia", "Atender clientes e apoiar organização da loja.", "Ensino médio completo; experiência desejável.", "R$ 1.650,00"),
    (7, "Auxiliar de estoque farmacêutico", "Conferir validade e organizar produtos.", "Atenção e organização.", "R$ 1.600,00"),
    (8, "Suporte técnico de informática", "Atender chamados e realizar manutenção básica.", "Conhecimento de Windows e redes.", "R$ 2.000,00"),
    (8, "Assistente de mídias sociais", "Apoiar produção de conteúdo e gestão de redes sociais.", "Portfólio ou conhecimento em ferramentas digitais.", "A combinar"),
    (9, "Balconista de padaria", "Atender clientes e organizar produtos de panificação.", "Boa comunicação e higiene.", "R$ 1.550,00"),
    (9, "Auxiliar de padeiro", "Apoiar preparo de massas e produtos.", "Desejável experiência em panificação.", "R$ 1.650,00"),
]

ANUNCIOS = [
    ("Sertão Cursos Profissionalizantes", "Cursos de informática, atendimento e qualificação para o mercado de trabalho.", "https://example.com/sertao-cursos"),
    ("Pajeú Contabilidade", "Serviços contábeis e orientação para MEIs e pequenos negócios da região.", "https://example.com/pajeu-contabilidade"),
    ("Conecta Internet Fibra", "Internet fibra óptica para sua casa e sua empresa. Consulte a cobertura.", "https://example.com/conecta-fibra"),
    ("Ótica Visão do Sertão", "Óculos, armações e atendimento especializado. Conheça a loja.", "https://example.com/otica-visao"),
]


def popular_dados_demo():
    criar_banco()
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS _dados_demo (chave TEXT PRIMARY KEY, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        if cursor.execute("SELECT 1 FROM _dados_demo WHERE chave = 'carga_inicial_2_0_2'").fetchone():
            print("Dados demonstrativos ja foram cadastrados; nenhuma duplicacao realizada.")
            return

        senha_hash = generate_password_hash(SENHA_DEMO, method="pbkdf2:sha256:600000")
        empresas_ids = []
        for nome_empresa, responsavel, cidade, descricao in EMPRESAS:
            email = slug_email(nome_empresa)
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            existente = cursor.fetchone()
            if existente:
                usuario_id = existente["id"]
            else:
                cursor.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'empresa')", (responsavel, email, senha_hash))
                usuario_id = cursor.lastrowid
            cursor.execute("SELECT id FROM empresas WHERE usuario_id = ?", (usuario_id,))
            empresa = cursor.fetchone()
            if empresa:
                empresa_id = empresa["id"]
            else:
                cursor.execute("INSERT INTO empresas (usuario_id, nome_empresa, telefone, cidade, descricao) VALUES (?, ?, ?, ?, ?)", (usuario_id, nome_empresa, "(87) 99999-0000", cidade, descricao))
                empresa_id = cursor.lastrowid
            empresas_ids.append(empresa_id)

        candidatos_ids = []
        for nome, cidade, escolaridade, experiencia, habilidades in CANDIDATOS:
            email = slug_email(nome)
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            existente = cursor.fetchone()
            if existente:
                usuario_id = existente["id"]
            else:
                cursor.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'candidato')", (nome, email, senha_hash))
                usuario_id = cursor.lastrowid
            cursor.execute("SELECT id FROM candidatos WHERE usuario_id = ?", (usuario_id,))
            candidato = cursor.fetchone()
            if candidato:
                candidato_id = candidato["id"]
            else:
                cursor.execute("INSERT INTO candidatos (usuario_id, telefone, cidade, escolaridade, experiencia, habilidades, objetivo_profissional, resumo_profissional) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (usuario_id, "(87) 98888-0000", cidade, escolaridade, experiencia, habilidades, "Conquistar uma oportunidade profissional e contribuir com a equipe.", f"Profissional em busca de oportunidade na área de {experiencia.lower()} com foco em responsabilidade e aprendizado."))
                candidato_id = cursor.lastrowid
            candidatos_ids.append(candidato_id)

        vagas_ids = []
        for empresa_idx, titulo, descricao, requisitos, salario in VAGAS:
            empresa_id = empresas_ids[empresa_idx]
            cursor.execute("SELECT id FROM vagas WHERE empresa_id = ? AND titulo = ?", (empresa_id, titulo))
            vaga = cursor.fetchone()
            if vaga:
                vaga_id = vaga["id"]
            else:
                cursor.execute("INSERT INTO vagas (empresa_id, titulo, descricao, requisitos, cidade, salario, status) VALUES (?, ?, ?, ?, 'Serra Talhada', ?, 'aberta')", (empresa_id, titulo, descricao, requisitos, salario))
                vaga_id = cursor.lastrowid
            vagas_ids.append(vaga_id)

        for idx, candidato_id in enumerate(candidatos_ids):
            for vaga_idx in ((idx * 3) % len(vagas_ids), (idx * 3 + 7) % len(vagas_ids)):
                vaga_id = vagas_ids[vaga_idx]
                status = "entrevista" if idx % 6 == 0 else ("aprovada" if idx % 11 == 0 else "enviada")
                resposta = "pendente" if status == "entrevista" else None
                cursor.execute("INSERT OR IGNORE INTO candidaturas (vaga_id, candidato_id, status, resposta_entrevista) VALUES (?, ?, ?, ?)", (vaga_id, candidato_id, status, resposta))

        for nome, descricao, link in ANUNCIOS:
            cursor.execute("SELECT id FROM anunciantes WHERE nome = ?", (nome,))
            anunciante = cursor.fetchone()
            if anunciante:
                anunciante_id = anunciante["id"]
            else:
                slug = slug_email(nome).split('@', 1)[0]
                cursor.execute("INSERT INTO anunciantes (nome, contato, telefone, email, ativo) VALUES (?, ?, ?, ?, 1)", (nome, "Equipe comercial (fictícia)", "(87) 97777-0000", slug + "@gmail.com"))
                anunciante_id = cursor.lastrowid
            cursor.execute("SELECT id FROM anuncios WHERE titulo = ? AND anunciante_id = ?", (nome, anunciante_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO anuncios (anunciante_id, titulo, descricao, link_url, posicao, status) VALUES (?, ?, ?, ?, 'destaque', 'ativo')", (anunciante_id, nome, descricao, link))

        cursor.execute("INSERT INTO _dados_demo (chave) VALUES ('carga_inicial_2_0_2')")
        conexao.commit()
        print("Carga demonstrativa concluida: 10 empresas, 25 candidatos, 20 vagas, candidaturas e 4 campanhas de publicidade.")
        print("Senha das contas demonstrativas: 1234567890")
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


if __name__ == "__main__":
    popular_dados_demo()
