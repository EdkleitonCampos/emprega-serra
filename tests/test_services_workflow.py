from contextlib import closing

from tests.support import (
    WorkflowTestCase,
    conectar,
    csrf_token,
    login,
    register_candidate,
)


class ServicesWorkflowTests(WorkflowTestCase):
    def test_service_publish_search_and_delete(self):
        response = self.client.post(
            "/servicos",
            data={
                "csrf_token": csrf_token(self.client, "/servicos"),
                "titulo": "Serviço temporário de teste",
                "categoria": "Autônomo",
                "descricao": "Atendimento pontual em Serra Talhada.",
                "cidade": "Serra Talhada",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))

        email, password, response = register_candidate(self.client)
        self.emails.append(email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(login(self.client, email, password).status_code, 302)

        response = self.client.post(
            "/servicos",
            data={
                "csrf_token": csrf_token(self.client, "/servicos"),
                "titulo": "Serviço temporário de teste",
                "categoria": "Autônomo",
                "descricao": "Atendimento pontual em Serra Talhada.",
                "cidade": "Serra Talhada",
                "whatsapp": "5587999999999",
            },
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.get("/servicos?q=temporário&cidade=Serra")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Serviço temporário de teste", response.data.decode())

        with closing(conectar()) as connection:
            service = connection.execute(
                "SELECT id FROM servicos WHERE titulo = ?",
                ("Serviço temporário de teste",),
            ).fetchone()
        self.assertIsNotNone(service)

        response = self.client.post(
            f"/servicos/{service['id']}/excluir",
            data={"csrf_token": csrf_token(self.client, "/servicos")},
        )
        self.assertEqual(response.status_code, 302)
        with closing(conectar()) as connection:
            self.assertIsNone(
                connection.execute(
                    "SELECT id FROM servicos WHERE id = ?", (service["id"],)
                ).fetchone()
            )
