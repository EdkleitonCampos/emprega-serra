from contextlib import closing
from uuid import uuid4

from admin_database import criar_admin
from tests.support import WorkflowTestCase, app, conectar, csrf_token


class AdminWorkflowTests(WorkflowTestCase):
    def test_admin_changes_temporary_password_and_opens_dashboard(self):
        client = app.test_client()
        email = f"admin-{uuid4().hex}@test.invalid"
        temporary_password = "TempPassword#123"
        new_password = "NewAdminPassword#123"
        criar_admin(email, temporary_password)

        self.assertEqual(client.get("/admin/").status_code, 302)
        response = client.post(
            "/login",
            data={
                "csrf_token": csrf_token(client),
                "email": email,
                "senha": temporary_password,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/admin/trocar-senha"))

        response = client.post(
            "/admin/trocar-senha",
            data={
                "csrf_token": csrf_token(client, "/admin/trocar-senha"),
                "senha_atual": temporary_password,
                "nova_senha": new_password,
                "confirmar_senha": new_password,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/admin/"))
        self.assertEqual(client.get("/admin/").status_code, 200)
        self.assertEqual(client.get("/admin/anunciantes").status_code, 200)
        self.assertEqual(client.get("/admin/anuncios").status_code, 200)

        response = client.post(
            "/admin/anunciantes",
            data={
                "csrf_token": csrf_token(client, "/admin/anunciantes"),
                "nome": "Anunciante de teste",
                "contato": "Contato de teste",
                "telefone": "",
                "email": "ads@test.invalid",
            },
        )
        self.assertEqual(response.status_code, 302)
        with closing(conectar()) as connection:
            advertiser = connection.execute(
                "SELECT id FROM anunciantes WHERE nome = ?",
                ("Anunciante de teste",),
            ).fetchone()
        self.assertIsNotNone(advertiser)

        response = client.post(
            "/admin/anuncios",
            data={
                "csrf_token": csrf_token(client, "/admin/anuncios"),
                "anunciante_id": str(advertiser["id"]),
                "titulo": "Campanha de teste",
                "descricao": "Campanha criada no banco temporário.",
                "posicao": "destaque",
                "link_url": "https://example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        with closing(conectar()) as connection:
            announcement = connection.execute(
                "SELECT id, status FROM anuncios WHERE titulo = ?",
                ("Campanha de teste",),
            ).fetchone()
        self.assertEqual(announcement["status"], "pausado")

        response = client.post(
            f"/admin/anuncios/{announcement['id']}/status",
            data={
                "csrf_token": csrf_token(client, "/admin/anuncios"),
                "status": "ativo",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("Campanha de teste", client.get("/").data.decode())
