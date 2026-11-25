import os
import sqlite3

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "emprega_serra.db")
)


def conectar():
    conexao = sqlite3.connect(DATABASE, timeout=15)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.execute("PRAGMA busy_timeout = 15000")
    return conexao


def criar_banco():
    conexao = conectar()
    cursor = conexao.cursor()

    # Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Dados dos candidatos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            cidade TEXT,
            escolaridade TEXT,
            experiencia TEXT,
            habilidades TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)


    # Novos campos para o currículo dos candidatos
    cursor.execute("PRAGMA table_info(candidatos)")
    colunas = [coluna["name"] for coluna in cursor.fetchall()]

    if "objetivo_profissional" not in colunas:
        cursor.execute("""
            ALTER TABLE candidatos
            ADD COLUMN objetivo_profissional TEXT
        """)

    if "resumo_profissional" not in colunas:
        cursor.execute("""
            ALTER TABLE candidatos
            ADD COLUMN resumo_profissional TEXT
        """)

    if "cursos" not in colunas:
        cursor.execute("""
            ALTER TABLE candidatos
            ADD COLUMN cursos TEXT
        """)


    # Dados das empresas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome_empresa TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            cidade TEXT,
            descricao TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # Vagas de emprego
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            requisitos TEXT,
            cidade TEXT NOT NULL,
            salario TEXT,
            status TEXT DEFAULT 'aberta',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    """)

    cursor.execute("PRAGMA table_info(vagas)")
    colunas_vagas = {coluna["name"] for coluna in cursor.fetchall()}
    if "pausa_ate" not in colunas_vagas:
        cursor.execute("ALTER TABLE vagas ADD COLUMN pausa_ate DATE")

    # Candidaturas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidaturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vaga_id INTEGER NOT NULL,
            candidato_id INTEGER NOT NULL,
            status TEXT DEFAULT 'enviada',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vaga_id) REFERENCES vagas(id),
            FOREIGN KEY (candidato_id) REFERENCES candidatos(id),
            UNIQUE(vaga_id, candidato_id)
        )
    """)

    # Resposta do candidato ao convite de entrevista. Campo adicionado por
    # migração compatível: não apaga nem altera candidaturas existentes.
    cursor.execute("PRAGMA table_info(candidaturas)")
    colunas_candidaturas = {coluna["name"] for coluna in cursor.fetchall()}
    if "resposta_entrevista" not in colunas_candidaturas:
        cursor.execute("ALTER TABLE candidaturas ADD COLUMN resposta_entrevista TEXT")

    # Dados do convite de entrevista. Campos antigos de cobrança são mantidos apenas por compatibilidade com bancos anteriores.
    cursor.execute("PRAGMA table_info(candidaturas)")
    cols = {r["name"] for r in cursor.fetchall()}
    for nome, tipo in [("entrevista_local", "TEXT"), ("entrevista_data", "TEXT"), ("entrevista_horario", "TEXT"), ("notificado_em", "TEXT")]:
        if nome not in cols:
            cursor.execute(f"ALTER TABLE candidaturas ADD COLUMN {nome} {tipo}")



    # Anunciantes e campanhas publicitárias gerenciadas pela administração
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anunciantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            contato TEXT,
            telefone TEXT,
            email TEXT,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes_publicidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            responsavel TEXT NOT NULL,
            segmento TEXT,
            cidade TEXT NOT NULL,
            telefone TEXT NOT NULL,
            email TEXT NOT NULL,
            instagram TEXT,
            formato TEXT,
            periodo TEXT,
            mensagem TEXT,
            logo_arquivo TEXT,
            banner_arquivo TEXT,
            status TEXT NOT NULL DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anunciante_id INTEGER,
            titulo TEXT NOT NULL,
            descricao TEXT,
            imagem_url TEXT,
            link_url TEXT,
            posicao TEXT NOT NULL DEFAULT 'lateral',
            status TEXT NOT NULL DEFAULT 'pausado',
            inicio DATE,
            fim DATE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anunciante_id) REFERENCES anunciantes(id)
        )
    """)

    # Serviços locais publicados por empresas e profissionais (pessoas físicas).
    cursor.execute("""CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT NOT NULL,
        cidade TEXT NOT NULL,
        whatsapp TEXT,
        status TEXT NOT NULL DEFAULT 'ativo',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )""")

    # Notificações internas vinculadas à conta do usuário.
    cursor.execute("""CREATE TABLE IF NOT EXISTS notificacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        link TEXT,
        lida INTEGER NOT NULL DEFAULT 0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )""")

    # Índices para acelerar os filtros e consultas mais usados.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidatos_usuario ON candidatos(usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_empresas_usuario ON empresas(usuario_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vagas_empresa_status ON vagas(empresa_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vagas_cidade_status ON vagas(cidade, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidaturas_candidato ON candidaturas(candidato_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidaturas_vaga_status ON candidaturas(vaga_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anuncios_status_periodo ON anuncios(status, inicio, fim)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_servicos_status_cidade ON servicos(status, cidade)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario ON notificacoes(usuario_id, lida)")

    conexao.commit()
    conexao.close()

    print("Banco de dados criado ou atualizado com sucesso!")


if __name__ == "__main__":
    criar_banco()