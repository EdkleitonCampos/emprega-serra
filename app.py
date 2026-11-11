import os

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from database import criar_banco, conectar

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

criar_banco()


@app.route("/")
def home():
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
    
    # ÁREA DO CANDIDATO
    if session["tipo"] == "candidato":

        conexao = conectar()
        cursor = conexao.cursor()

        # Buscar cadastro do candidato
        cursor.execute("""
            SELECT id
            FROM candidatos
            WHERE usuario_id = ?
        """, (session["usuario_id"],))

        candidato = cursor.fetchone()

        if not candidato:
            conexao.close()
            flash("Cadastro do candidato não encontrado.")
            return redirect(url_for("sair"))

        # Buscar candidaturas e informações das vagas
        cursor.execute("""
            SELECT
                c.status,
                c.criado_em,
                v.titulo,
                e.nome_empresa AS empresa
            FROM candidaturas c
            INNER JOIN vagas v ON v.id = c.vaga_id
            INNER JOIN empresas e ON e.id = v.empresa_id
            WHERE c.candidato_id = ?
            ORDER BY c.id DESC
        """, (candidato["id"],))

        candidaturas = cursor.fetchall()

        conexao.close()

        # Calcular estatísticas
        total_candidaturas = len(candidaturas)

        em_analise = 0
        aprovadas = 0

        for candidatura in candidaturas:

            status = (candidatura["status"] or "").lower().strip()
            status = status.replace(" ", "_").replace("á", "a")

            if status in ("em_analise", "analise"):
                em_analise += 1

            elif status in ("aprovada", "aprovado"):
                aprovadas += 1

        return render_template(
            "candidato/painel.html",
            nome=session["nome"],
            tipo="candidato",
            total_candidaturas=total_candidaturas,
            em_analise=em_analise,
            aprovadas=aprovadas,
            candidaturas=candidaturas
        )


    # ÁREA DA EMPRESA
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome_empresa
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
        SELECT COUNT(*) AS total
        FROM vagas
        WHERE empresa_id = ?
    """, (empresa["id"],))

    total_vagas = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(c.id) AS total
        FROM candidaturas c
        INNER JOIN vagas v ON v.id = c.vaga_id
        WHERE v.empresa_id = ?
    """, (empresa["id"],))

    total_candidaturas = cursor.fetchone()["total"]

    conexao.close()

    return render_template(
        "painel.html",
        nome=session["nome"],
        tipo="empresa",
        empresa=empresa,
        vagas=vagas,
        total_vagas=total_vagas,
        total_candidaturas=total_candidaturas
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

        if not titulo or not descricao or not cidade:
            conexao.close()
            flash("Preencha o cargo, a descrição e a cidade.")
            return redirect(url_for("editar_vaga", vaga_id=vaga_id))

        cursor.execute("""
            UPDATE vagas
            SET titulo = ?, descricao = ?, requisitos = ?,
                cidade = ?, salario = ?
            WHERE id = ? AND empresa_id = ?
        """, (
            titulo, descricao, requisitos,
            cidade, salario, vaga_id, empresa["id"]
        ))

        conexao.commit()
        conexao.close()

        flash("Vaga atualizada com sucesso!")
        return redirect(url_for("painel"))

    conexao.close()

    return render_template("editar_vaga.html", vaga=vaga)


# ENCERRAR VAGA
@app.route("/empresa/vaga/encerrar/<int:vaga_id>", methods=["POST"])
def encerrar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE vagas
        SET status = 'encerrada'
        WHERE id = ?
        AND empresa_id = (
            SELECT id FROM empresas WHERE usuario_id = ?
        )
    """, (vaga_id, session["usuario_id"]))

    conexao.commit()

    if cursor.rowcount:
        flash("Vaga encerrada com sucesso!")
    else:
        flash("Não foi possível localizar essa vaga.")

    conexao.close()

    return redirect(url_for("painel"))



# SAIR
@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)