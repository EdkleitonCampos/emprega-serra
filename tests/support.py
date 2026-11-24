import os
import shutil
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_test_directory = tempfile.TemporaryDirectory(prefix="emprega-serra-tests-")
_test_root = Path(_test_directory.name)
shutil.copy2(PROJECT_ROOT / "emprega_serra.db", _test_root / "emprega_serra.db")
os.environ["DATABASE_PATH"] = str(_test_root / "emprega_serra.db")
os.environ["ADMIN_DATABASE_PATH"] = str(_test_root / "admin.sqlite3")
os.environ["INSTANCE_PATH"] = str(_test_root / "instance")
os.environ["RATELIMIT_STORAGE_URI"] = "memory://"
os.environ.pop("SUPPORT_WHATSAPP", None)

from app import app, limiter
from database import conectar

app.config.update(TESTING=True)


def csrf_token(client, page="/login"):
    client.get(page)
    with client.session_transaction() as session:
        return session["_csrf_token"]


def register_candidate(client):
    email = f"candidate-{uuid4().hex}@test.invalid"
    password = "TestPassword#123"
    response = client.post(
        "/cadastro/candidato",
        data={
            "csrf_token": csrf_token(client, "/cadastro/candidato"),
            "nome": "Candidato de teste",
            "email": email,
            "senha": password,
            "confirmar_senha": password,
            "cidade": "Serra Talhada",
        },
    )
    return email, password, response


def register_company(client):
    email = f"company-{uuid4().hex}@test.invalid"
    password = "TestPassword#123"
    response = client.post(
        "/cadastro/empresa",
        data={
            "csrf_token": csrf_token(client, "/cadastro/empresa"),
            "nome": "Responsável de teste",
            "email": email,
            "nome_empresa": "Empresa de teste",
            "cidade": "Serra Talhada",
            "senha": password,
            "confirmar_senha": password,
        },
    )
    return email, password, response


def login(client, email, password):
    return client.post(
        "/login",
        data={
            "csrf_token": csrf_token(client),
            "email": email,
            "senha": password,
        },
    )


class WorkflowTestCase(unittest.TestCase):
    def setUp(self):
        limiter.reset()
        self.client = app.test_client()
        self.emails = []

    def tearDown(self):
        connection = conectar()
        try:
            for email in self.emails:
                user = connection.execute(
                    "SELECT id FROM usuarios WHERE email = ?", (email,)
                ).fetchone()
                if not user:
                    continue
                user_id = user["id"]
                connection.execute(
                    "DELETE FROM candidaturas WHERE candidato_id IN "
                    "(SELECT id FROM candidatos WHERE usuario_id = ?) "
                    "OR vaga_id IN (SELECT id FROM vagas WHERE empresa_id IN "
                    "(SELECT id FROM empresas WHERE usuario_id = ?))",
                    (user_id, user_id),
                )
                connection.execute(
                    "DELETE FROM servicos WHERE usuario_id = ?", (user_id,)
                )
                connection.execute(
                    "DELETE FROM vagas WHERE empresa_id IN "
                    "(SELECT id FROM empresas WHERE usuario_id = ?)",
                    (user_id,),
                )
                connection.execute("DELETE FROM notificacoes WHERE usuario_id = ?", (user_id,))
                connection.execute("DELETE FROM candidatos WHERE usuario_id = ?", (user_id,))
                connection.execute("DELETE FROM empresas WHERE usuario_id = ?", (user_id,))
                connection.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            connection.commit()
        finally:
            connection.close()
