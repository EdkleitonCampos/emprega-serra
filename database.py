import sqlite3

DATABASE = "emprega_serra.db"


def conectar():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
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

    conexao.commit()
    conexao.close()

    print("Banco de dados criado com sucesso!")


if __name__ == "__main__":
    criar_banco()