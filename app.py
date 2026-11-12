import os
from datetime import date, datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from database import criar_banco, conectar

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

criar_banco()


def reativar_vagas_pausadas():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE vagas
        SET status = 'aberta', pausa_ate = NULL
        WHERE status = 'pausada'
        AND pausa_ate IS NOT NULL
        AND pausa_ate <= date('now', 'localtime')
    """)
    conexao.commit()
    conexao.close()


@app.route("/")
def home():
    reativar_vagas_pausadas()
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT titulo AS cargo, cidade, salario, descricao
        FROM vagas
        WHERE status = 'aberta'
        ORDER BY id DESC
    """)

    vagas_banco = cursor.fetchall()
    conexao.close()

    vagas = []

    for vaga in vagas_banco:
        vagas.append({
            "cargo": vaga["cargo"],
            "empresa": "Empresa cadastrada",
            "cidade": vaga["cidade"],
            "tipo": "Consulte a empresa",
            "salario": vaga["salario"] or "A combinar",
            "categoria": vaga["descricao"]
        })

    if not vagas:
        vagas = [
            {
                "cargo": "Atendente de loja",
                "empresa": "Comércio Exemplo",
                "cidade": "Serra Talhada - PE",
                "tipo": "Tempo integral",
                "salario": "A combinar",
                "categoria": "Atendimento"
            },
            {
                "cargo": "Auxiliar administrativo",
                "empresa": "Empresa Parceira",
                "cidade": "Serra Talhada - PE",
                "tipo": "Tempo integral",
                "salario": "A combinar",
                "categoria": "Administrativo"
            },
            {
                "cargo": "Vendedor(a)",
                "empresa": "Loja Modelo",
                "cidade": "Serra Talhada - PE",
                "tipo": "Comercial",
                "salario": "Comissão + salário",
                "categoria": "Vendas"
            }
        ]

    return render_template("index.html", vagas=vagas)


# CADASTRO DE CANDIDATO
@app.route("/cadastro/candidato", methods=["GET", "POST"])
def cadastro_candidato():

    if request.method == "POST":
        nome = request.form["nome"].strip()
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]

        cpf = request.form.get("cpf", "").strip()
        telefone = request.form.get("telefone", "").strip()
        cidade = request.form.get("cidade", "").strip()

        if senha != confirmar_senha:
            flash("As senhas não são iguais.")
            return redirect(url_for("cadastro_candidato"))

        if len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.")
            return redirect(url_for("cadastro_candidato"))

        conexao = conectar()
        cursor = conexao.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES (?, ?, ?, 'candidato')
            """, (nome, email, generate_password_hash(senha)))

            usuario_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO candidatos
                (usuario_id, cpf, telefone, cidade)
                VALUES (?, ?, ?, ?)
            """, (usuario_id, cpf or None, telefone, cidade))

            conexao.commit()

            flash("Cadastro realizado com sucesso! Faça seu login.")
            return redirect(url_for("login"))

        except Exception as erro:
            conexao.rollback()
            mensagem = str(erro)

            if "UNIQUE constraint failed: usuarios.email" in mensagem:
                flash("Este e-mail já está cadastrado.")
            elif "UNIQUE constraint failed: candidatos.cpf" in mensagem:
                flash("Este CPF já está cadastrado.")
            else:
                flash("Não foi possível realizar o cadastro. Confira os dados.")

        finally:
            conexao.close()

    return render_template("cadastro_candidato.html")


# CADASTRO DE EMPRESA
@app.route("/cadastro/empresa", methods=["GET", "POST"])
def cadastro_empresa():

    if request.method == "POST":
        nome = request.form["nome"].strip()
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]

        nome_empresa = request.form["nome_empresa"].strip()
        cnpj = request.form.get("cnpj", "").strip()
        telefone = request.form.get("telefone", "").strip()
        cidade = request.form.get("cidade", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if senha != confirmar_senha:
            flash("As senhas não são iguais.")
            return redirect(url_for("cadastro_empresa"))

        if len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.")
            return redirect(url_for("cadastro_empresa"))

        conexao = conectar()
        cursor = conexao.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES (?, ?, ?, 'empresa')
            """, (nome, email, generate_password_hash(senha)))

            usuario_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO empresas
                (usuario_id, nome_empresa, cnpj, telefone, cidade, descricao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario_id, nome_empresa, cnpj or None,
                  telefone, cidade, descricao))

            conexao.commit()

            flash("Empresa cadastrada com sucesso! Faça seu login.")
            return redirect(url_for("login"))

        except Exception:
            conexao.rollback()
            flash("Não foi possível cadastrar. Verifique se o e-mail ou CNPJ já estão cadastrados.")

        finally:
            conexao.close()

    return render_template("cadastro_empresa.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email,)
        )

        usuario = cursor.fetchone()
        conexao.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["tipo"] = usuario["tipo"]

            return redirect(url_for("painel"))

        flash("E-mail ou senha incorretos.")

    return render_template("login.html")



# PAINEL PRINCIPAL
@app.route("/painel")
def painel():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    # ÁREA DO CANDIDATO
    if session["tipo"] == "candidato":
        return render_template(
            "painel.html",
            nome=session["nome"],
            tipo="candidato"
        )

    # ÁREA DA EMPRESA
    reativar_vagas_pausadas()
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM empresas
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    empresa = cursor.fetchone()

    if not empresa:
        conexao.close()
        flash("Cadastro da empresa não encontrado.")
        return redirect(url_for("sair"))

    cursor.execute("""
        SELECT
            v.*,
            COUNT(c.id) AS total_candidatos
        FROM vagas v
        LEFT JOIN candidaturas c ON c.vaga_id = v.id
        WHERE v.empresa_id = ?
        GROUP BY v.id
        ORDER BY v.id DESC
    """, (empresa["id"],))

    vagas = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status = 'aberta' THEN 1 ELSE 0 END), 0) AS abertas
        FROM vagas
        WHERE empresa_id = ?
    """, (empresa["id"],))

    resumo_vagas = cursor.fetchone()
    total_vagas = resumo_vagas["total"]
    vagas_abertas = resumo_vagas["abertas"]

    cursor.execute("""
        SELECT
            COUNT(c.id) AS total,
            COALESCE(SUM(CASE WHEN c.status = 'entrevista' THEN 1 ELSE 0 END), 0) AS entrevistas,
            COALESCE(SUM(CASE WHEN c.status = 'selecao_finalizada' THEN 1 ELSE 0 END), 0) AS selecoes_finalizadas
        FROM candidaturas c
        INNER JOIN vagas v ON v.id = c.vaga_id
        WHERE v.empresa_id = ?
    """, (empresa["id"],))

    resumo_candidaturas = cursor.fetchone()
    total_candidaturas = resumo_candidaturas["total"]
    total_entrevistas = resumo_candidaturas["entrevistas"]
    total_selecoes_finalizadas = resumo_candidaturas["selecoes_finalizadas"]

    cursor.execute("""
        SELECT
            candidaturas.id AS candidatura_id,
            u.nome AS candidato_nome,
            u.email AS candidato_email,
            c.telefone AS candidato_telefone,
            v.titulo AS vaga_titulo,
            candidaturas.status AS candidatura_status,
            candidaturas.criado_em AS candidatura_criada_em
        FROM candidaturas
        INNER JOIN candidatos c ON c.id = candidaturas.candidato_id
        INNER JOIN usuarios u ON u.id = c.usuario_id
        INNER JOIN vagas v ON v.id = candidaturas.vaga_id
        WHERE v.empresa_id = ?
        ORDER BY candidaturas.id DESC
    """, (empresa["id"],))

    candidatos = cursor.fetchall()

    conexao.close()

    return render_template(
        "painel.html",
        nome=session["nome"],
        tipo="empresa",
        empresa=empresa,
        vagas=vagas,
        total_vagas=total_vagas,
        vagas_abertas=vagas_abertas,
        total_candidaturas=total_candidaturas,
        total_entrevistas=total_entrevistas,
        total_selecoes_finalizadas=total_selecoes_finalizadas,
        candidatos=candidatos
    )


# CADASTRAR NOVA VAGA
@app.route("/empresa/vaga/nova", methods=["GET", "POST"])
def nova_vaga():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id FROM empresas
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    empresa = cursor.fetchone()

    if not empresa:
        conexao.close()
        flash("Empresa não encontrada.")
        return redirect(url_for("painel"))

    if request.method == "POST":

        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        requisitos = request.form.get("requisitos", "").strip()
        cidade = request.form.get("cidade", "").strip()
        salario = request.form.get("salario", "").strip()

        if not titulo or not descricao or not cidade:
            conexao.close()
            flash("Preencha o cargo, a descrição e a cidade.")
            return redirect(url_for("nova_vaga"))

        cursor.execute("""
            INSERT INTO vagas
            (empresa_id, titulo, descricao, requisitos, cidade, salario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            empresa["id"],
            titulo,
            descricao,
            requisitos,
            cidade,
            salario
        ))

        conexao.commit()
        conexao.close()

        flash("Vaga publicada com sucesso!")
        return redirect(url_for("painel"))

    conexao.close()

    return render_template("nova_vaga.html")


# EDITAR VAGA
@app.route("/empresa/vaga/editar/<int:vaga_id>", methods=["GET", "POST"])
def editar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id FROM empresas
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    empresa = cursor.fetchone()

    if not empresa:
        conexao.close()
        return redirect(url_for("painel"))

    cursor.execute("""
        SELECT * FROM vagas
        WHERE id = ? AND empresa_id = ?
    """, (vaga_id, empresa["id"]))

    vaga = cursor.fetchone()

    if not vaga:
        conexao.close()
        flash("Vaga não encontrada.")
        return redirect(url_for("painel"))

    if request.method == "POST":

        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        requisitos = request.form.get("requisitos", "").strip()
        cidade = request.form.get("cidade", "").strip()
        salario = request.form.get("salario", "").strip()
        status = request.form.get("status", "")
        status_permitidos = {"aberta", "finalizada", "cancelada", "em_analise", "pausada"}

        if not titulo or not descricao or not cidade:
            conexao.close()
            flash("Preencha o cargo, a descrição e a cidade.")
            return redirect(url_for("editar_vaga", vaga_id=vaga_id))

        if status not in status_permitidos:
            conexao.close()
            flash("Selecione um status válido para a vaga.")
            return redirect(url_for("editar_vaga", vaga_id=vaga_id))

        cursor.execute("""
            UPDATE vagas
            SET titulo = ?, descricao = ?, requisitos = ?,
                cidade = ?, salario = ?, status = ?,
                pausa_ate = CASE WHEN ? = 'pausada' THEN pausa_ate ELSE NULL END
            WHERE id = ? AND empresa_id = ?
        """, (
            titulo, descricao, requisitos,
            cidade, salario, status, status, vaga_id, empresa["id"]
        ))

        conexao.commit()
        conexao.close()

        flash("Vaga e status atualizados com sucesso!")
        return redirect(url_for("painel") + "#minhas-vagas")

    conexao.close()

    return render_template("editar_vaga.html", vaga=vaga)


# ENCERRAR VAGA
@app.route("/empresa/vaga/encerrar/<int:vaga_id>", methods=["POST"])
def encerrar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        return redirect(url_for("painel") + "#minhas-vagas")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE vagas
        SET status = 'finalizada', pausa_ate = NULL
        WHERE id = ?
        AND empresa_id = (
            SELECT id FROM empresas WHERE usuario_id = ?
        )
    """, (vaga_id, session["usuario_id"]))

    conexao.commit()

    if cursor.rowcount:
        flash("Vaga finalizada com sucesso!")
    else:
        flash("Não foi possível localizar essa vaga.")

    conexao.close()

    return redirect(url_for("painel") + "#minhas-vagas")


# ATUALIZAR STATUS DA VAGA
@app.route("/empresa/vaga/status/<int:vaga_id>", methods=["POST"])
def atualizar_status_vaga(vaga_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel"))

    status = request.form.get("status", "")
    status_permitidos = {"aberta", "finalizada", "cancelada", "em_analise", "pausada"}
    if status not in status_permitidos:
        flash("Status de vaga inválido.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE vagas
        SET status = ?, pausa_ate = CASE WHEN ? = 'pausada' THEN pausa_ate ELSE NULL END
        WHERE id = ?
        AND empresa_id = (
            SELECT id FROM empresas WHERE usuario_id = ?
        )
    """, (status, status, vaga_id, session["usuario_id"]))
    conexao.commit()

    if cursor.rowcount:
        flash("Status da vaga atualizado com sucesso.")
    else:
        flash("Não foi possível localizar essa vaga.")

    conexao.close()
    return redirect(url_for("painel") + "#minhas-vagas")


# PAUSAR VAGA
@app.route("/empresa/vaga/pausar/<int:vaga_id>", methods=["POST"])
def pausar_vaga(vaga_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel") + "#minhas-vagas")

    pausa_ate = request.form.get("pausa_ate", "").strip()
    if pausa_ate:
        try:
            data_reabertura = datetime.strptime(pausa_ate, "%Y-%m-%d").date()
        except ValueError:
            flash("Selecione uma data válida para reabrir a vaga.")
            return redirect(url_for("painel") + "#minhas-vagas")

        if data_reabertura <= date.today():
            flash("A data de reabertura precisa ser futura.")
            return redirect(url_for("painel") + "#minhas-vagas")
    else:
        data_reabertura = None

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE vagas
        SET status = 'pausada', pausa_ate = ?
        WHERE id = ?
        AND status = 'aberta'
        AND empresa_id = (
            SELECT id FROM empresas WHERE usuario_id = ?
        )
    """, (
        data_reabertura.isoformat() if data_reabertura else None,
        vaga_id,
        session["usuario_id"]
    ))
    conexao.commit()

    if cursor.rowcount:
        if data_reabertura:
            flash(f"Vaga pausada até {data_reabertura.strftime('%d/%m/%Y')}.")
        else:
            flash("Vaga pausada por tempo indeterminado.")
    else:
        flash("Não foi possível pausar essa vaga. Verifique se ela ainda está aberta.")

    conexao.close()
    return redirect(url_for("painel") + "#minhas-vagas")


# ATUALIZAR ETAPA DA CANDIDATURA
@app.route("/empresa/candidatura/status/<int:candidatura_id>", methods=["POST"])
def atualizar_status_candidatura(candidatura_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel"))

    status = request.form.get("status", "")
    status_permitidos = {"enviada", "entrevista", "selecao_finalizada"}
    if status not in status_permitidos:
        flash("Etapa de candidatura inválida.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE candidaturas
        SET status = ?
        WHERE id = ?
        AND vaga_id IN (
            SELECT id FROM vagas
            WHERE empresa_id = (
                SELECT id FROM empresas WHERE usuario_id = ?
            )
        )
    """, (status, candidatura_id, session["usuario_id"]))
    conexao.commit()

    if cursor.rowcount:
        flash("Etapa do candidato atualizada com sucesso.")
    else:
        flash("Não foi possível localizar essa candidatura.")

    conexao.close()
    return redirect(url_for("painel") + "#candidatos")



# SAIR
@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)