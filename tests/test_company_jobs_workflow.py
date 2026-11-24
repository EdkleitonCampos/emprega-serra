from contextlib import closing

from tests.support import (
    WorkflowTestCase,
    conectar,
    csrf_token,
    login,
    register_candidate,
    register_company,
)


class CompanyJobsWorkflowTests(WorkflowTestCase):
    def test_company_publishes_vacancy_and_candidate_applies(self):
        company_client = self.app_client()
        response = company_client.get("/empresa/vaga/nova")
        self.assertEqual(response.status_code, 302)

        company_email, password, response = register_company(company_client)
        self.emails.append(company_email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(login(company_client, company_email, password).status_code, 302)
        self.assertEqual(company_client.get("/painel_empresarial").status_code, 200)

        response = company_client.post(
            "/empresa/vaga/nova",
            data={
                "csrf_token": csrf_token(company_client, "/empresa/vaga/nova"),
                "titulo": "Vaga temporária de teste",
                "descricao": "Oportunidade criada pelo teste automatizado.",
                "requisitos": "Disponibilidade",
                "cidade": "Serra Talhada",
                "salario": "",
            },
        )
        self.assertEqual(response.status_code, 302)

        with closing(conectar()) as connection:
            vacancy = connection.execute(
                "SELECT id FROM vagas WHERE titulo = ?",
                ("Vaga temporária de teste",),
            ).fetchone()
        self.assertIsNotNone(vacancy)

        candidate_client = self.app_client()
        candidate_email, candidate_password, response = register_candidate(candidate_client)
        self.emails.append(candidate_email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(login(candidate_client, candidate_email, candidate_password).status_code, 302)
        self.assertEqual(
            candidate_client.post(
                f"/candidatar/{vacancy['id']}",
                data={"csrf_token": csrf_token(candidate_client)},
            ).status_code,
            302,
        )

        with closing(conectar()) as connection:
            application = connection.execute(
                "SELECT candidaturas.id, candidaturas.status FROM candidaturas "
                "JOIN candidatos ON candidatos.id = candidaturas.candidato_id "
                "JOIN usuarios ON usuarios.id = candidatos.usuario_id "
                "WHERE candidaturas.vaga_id = ? AND usuarios.email = ?",
                (vacancy["id"], candidate_email),
            ).fetchone()
        self.assertIsNotNone(application)
        self.assertEqual(application["status"], "enviada")
        self.assertIn("Vaga temporária de teste", self.client.get("/").data.decode())

        response = company_client.post(
            "/empresa/enviar-convites",
            data={
                "csrf_token": csrf_token(company_client),
                "candidatura_ids": str(application["id"]),
                "local": "Entrevista remota",
                "data": "2026-12-01",
                "horario": "10:00",
            },
        )
        self.assertEqual(response.status_code, 302)

        with closing(conectar()) as connection:
            invitation = connection.execute(
                "SELECT status, resposta_entrevista FROM candidaturas WHERE id = ?",
                (application["id"],),
            ).fetchone()
            candidate_notice = connection.execute(
                "SELECT COUNT(*) FROM notificacoes WHERE usuario_id = "
                "(SELECT id FROM usuarios WHERE email = ?) AND titulo = 'Novo convite de entrevista'",
                (candidate_email,),
            ).fetchone()[0]
        self.assertEqual(invitation["status"], "entrevista")
        self.assertEqual(invitation["resposta_entrevista"], "pendente")
        self.assertEqual(candidate_notice, 1)

        response = candidate_client.post(
            f"/candidato/candidatura/{application['id']}/responder-entrevista",
            data={
                "csrf_token": csrf_token(candidate_client),
                "resposta": "aceita",
            },
        )
        self.assertEqual(response.status_code, 302)

        with closing(conectar()) as connection:
            accepted = connection.execute(
                "SELECT resposta_entrevista FROM candidaturas WHERE id = ?",
                (application["id"],),
            ).fetchone()
            company_notice = connection.execute(
                "SELECT COUNT(*) FROM notificacoes WHERE usuario_id = "
                "(SELECT id FROM usuarios WHERE email = ?) AND titulo = 'Entrevista aceita'",
                (company_email,),
            ).fetchone()[0]
        self.assertEqual(accepted["resposta_entrevista"], "aceita")
        self.assertEqual(company_notice, 1)

    def app_client(self):
        from tests.support import app

        return app.test_client()
