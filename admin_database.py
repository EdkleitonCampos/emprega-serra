import os
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


def _default_admin_database_path():
    if os.name == "nt":
        data_directory = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
    else:
        data_directory = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )
    return data_directory / "EmpregaSerra" / "admin_users.sqlite3"


ADMIN_DATABASE_PATH = Path(
    os.environ.get("ADMIN_DATABASE_PATH", _default_admin_database_path())
)


def conectar_admin():
    ADMIN_DATABASE_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    conexao = sqlite3.connect(ADMIN_DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco_admin():
    conexao = conectar_admin()
    try:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                senha_hash TEXT NOT NULL,
                trocar_senha INTEGER NOT NULL DEFAULT 1,
                criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conexao.commit()
    finally:
        conexao.close()

    if os.name != "nt":
        ADMIN_DATABASE_PATH.parent.chmod(0o700)
        ADMIN_DATABASE_PATH.chmod(0o600)


def buscar_admin_por_email(email):
    conexao = conectar_admin()
    try:
        return conexao.execute(
            "SELECT id, email, senha_hash, trocar_senha "
            "FROM administradores WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()
    finally:
        conexao.close()


def buscar_admin_por_id(admin_id):
    conexao = conectar_admin()
    try:
        return conexao.execute(
            "SELECT id, email, senha_hash, trocar_senha "
            "FROM administradores WHERE id = ?",
            (admin_id,)
        ).fetchone()
    finally:
        conexao.close()


def criar_admin(email, senha):
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("Informe um e-mail válido.")
    if len(senha) < 8:
        raise ValueError("A senha temporária precisa ter pelo menos 8 caracteres.")

    conexao = conectar_admin()
    try:
        cursor = conexao.execute(
            "INSERT INTO administradores (email, senha_hash, trocar_senha) "
            "VALUES (?, ?, 1)",
            (email, generate_password_hash(senha, method="pbkdf2:sha256:600000"))
        )
        conexao.commit()
        return cursor.lastrowid
    finally:
        conexao.close()


def atualizar_senha_admin(admin_id, senha):
    conexao = conectar_admin()
    try:
        cursor = conexao.execute(
            "UPDATE administradores "
            "SET senha_hash = ?, trocar_senha = 0 "
            "WHERE id = ?",
            (generate_password_hash(senha, method="pbkdf2:sha256:600000"), admin_id)
        )
        if cursor.rowcount != 1:
            raise LookupError("Conta administrativa não encontrada.")
        conexao.commit()
    finally:
        conexao.close()


def garantir_admin_inicial():
    """Cria um administrador temporário na primeira execução da instalação-demo."""
    email = "admin@empregaserra.com"
    senha_temporaria = "Admin@1234567890"
    conexao = conectar_admin()
    try:
        total = conexao.execute("SELECT COUNT(*) FROM administradores").fetchone()[0]
        if total == 0:
            conexao.execute(
                "INSERT INTO administradores (email, senha_hash, trocar_senha) VALUES (?, ?, 1)",
                (email, generate_password_hash(senha_temporaria, method="pbkdf2:sha256:600000"))
            )
            conexao.commit()
            print("Administrador inicial criado: admin@empregaserra.com (troca de senha obrigatória no primeiro acesso).")
    finally:
        conexao.close()
