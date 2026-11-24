from contextlib import closing

from werkzeug.security import check_password_hash

from tests.support import (
    WorkflowTestCase,
    conectar,
    csrf_token,
    login,
    register_candidate,
)


class CandidateWorkflowTests(WorkflowTestCase):
    def test_registration_login_and_profile_update(self):
        response = self.client.get("/meu-perfil")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))

        email, password, response = register_candidate(self.client)
        self.emails.append(email)
        self.assertEqual(response.status_code, 302)

        response = login(self.client, email, "incorrect-password")
        self.assertEqual(response.status_code, 200)
        self.assertIn("E-mail ou senha incorretos".encode(), response.data)

        response = login(self.client, email, password)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/painel_empresarial").status_code, 200)
        self.assertEqual(self.client.get("/curriculo").status_code, 200)
        self.assertEqual(self.client.get("/buscar-vagas").status_code, 200)

        response = self.client.post(
            "/meu-perfil",
            data={
                "csrf_token": csrf_token(self.client, "/meu-perfil"),
                "telefone": "87900000000",
                "cidade": "Serra Talhada",
                "escolaridade": "Superior",
                "experiencia": "Experiência de teste",
                "habilidades": "Atendimento",
                "objetivo_profissional": "Primeiro emprego",
                "resumo_profissional": "Perfil de teste",
                "cursos": "Curso de teste",
            },
        )
        self.assertEqual(response.status_code, 302)

        with closing(conectar()) as connection:
            saved_user = connection.execute(
                "SELECT senha FROM usuarios WHERE email = ?",
                (email,),
            ).fetchone()
            profile = connection.execute(
                "SELECT cidade, escolaridade, habilidades FROM candidatos "
                "JOIN usuarios ON usuarios.id = candidatos.usuario_id "
                "WHERE usuarios.email = ?",
                (email,),
            ).fetchone()
        self.assertNotEqual(saved_user["senha"], password)
        self.assertTrue(check_password_hash(saved_user["senha"], password))
        self.assertEqual(profile["cidade"], "Serra Talhada")
        self.assertEqual(profile["escolaridade"], "Superior")
        self.assertEqual(profile["habilidades"], "Atendimento")
