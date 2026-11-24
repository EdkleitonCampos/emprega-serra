import os
import sqlite3
import secrets
import hmac
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlparse
from datetime import date, datetime, timedelta

import click

# Carrega variáveis de um arquivo .env local sem sobrescrever variáveis do sistema.
def carregar_env_local():
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for linha in env_path.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))

carregar_env_local()
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import (
    Flask, render_template, request, abort,
    redirect, url_for, session, flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from admin import admin_bp
from admin_database import buscar_admin_por_email, criar_admin, criar_banco_admin, garantir_admin_inicial
from database import criar_banco, conectar

app = Flask(__name__)

# Limites de requisições para reduzir abuso automatizado. Em produção com
# múltiplos processos, configure RATELIMIT_STORAGE_URI com Redis.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["300 per hour"],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window",
)

# Mantém a sessão válida entre reinicializações locais. Em hospedagem,
# configure SECRET_KEY por variável de ambiente.
app.instance_path = os.path.abspath(os.environ.get("INSTANCE_PATH", app.instance_path))
os.makedirs(app.instance_path, exist_ok=True)
_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    _secret_file = Path(app.instance_path) / "secret_key"
    if not _secret_file.exists():
        _secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
    _secret_key = _secret_file.read_text(encoding="utf-8").strip()
app.secret_key = _secret_key
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0").lower() in {"1", "true", "yes"},
    SESSION_COOKIE_NAME="emprega_serra_session",
    SESSION_COOKIE_PATH="/",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

# Proteção CSRF para todas as operações que alteram dados.
def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

@app.context_processor
def inject_security_helpers():
    return {"csrf_token": csrf_token}

@app.before_request
def protect_state_changing_requests():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("_csrf_token", "")
        if not supplied or not expected or not hmac.compare_digest(supplied, expected):
            abort(400, description="Token de segurança inválido ou expirado. Atualize a página e tente novamente.")

@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; object-src 'none'; "
        "frame-ancestors 'none'; form-action 'self'; "
        "frame-src 'self' https://www.openstreetmap.org; "
        "script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    if session.get("admin_id") or session.get("usuario_id"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    if app.config.get("SESSION_COOKIE_SECURE"):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

criar_banco()
criar_banco_admin()
garantir_admin_inicial()
app.register_blueprint(admin_bp)

def email_valido(valor):
    return bool(valor and len(valor) <= 160 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", valor))




@app.cli.command("create-admin")
@click.argument("email")
def create_admin_command(email):
    senha = click.prompt(
        "Senha temporária do administrador",
        hide_input=True,
        confirmation_prompt=True
    )
    try:
        criar_admin(email, senha)
    except ValueError as erro:
        raise click.ClickException(str(erro)) from erro
    except sqlite3.IntegrityError as erro:
        raise click.ClickException("Já existe um administrador com esse e-mail.") from erro
    click.echo("Administrador criado. A senha deverá ser trocada no primeiro acesso.")


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
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT v.id, v.titulo AS cargo, v.cidade, v.salario,
                   v.descricao, e.nome_empresa AS empresa, e.telefone AS telefone_empresa
            FROM vagas v
            INNER JOIN empresas e ON e.id = v.empresa_id
            WHERE v.status = 'aberta'
            ORDER BY v.id DESC
            LIMIT 12
        """)
        vagas = cursor.fetchall()
        vagas = [dict(v) | {"whatsapp": re.sub(r"\D", "", v["telefone_empresa"] or "")} for v in vagas]

        cursor.execute("""
            SELECT a.id, a.titulo, a.descricao, a.imagem_url, a.link_url, a.posicao
            FROM anuncios a
            LEFT JOIN anunciantes n ON n.id = a.anunciante_id
            WHERE a.status = 'ativo'
              AND (a.inicio IS NULL OR a.inicio <= date('now', 'localtime'))
              AND (a.fim IS NULL OR a.fim >= date('now', 'localtime'))
              AND (a.anunciante_id IS NULL OR n.ativo = 1)
            ORDER BY CASE a.posicao
                WHEN 'destaque' THEN 0 WHEN 'lateral' THEN 1 ELSE 2 END,
                a.id DESC
        """)
        anuncios = cursor.fetchall()
        anuncios = [
            dict(anuncio) | {
                "imagem_url": anuncio["imagem_url"] if _url_http_segura(anuncio["imagem_url"]) else "",
                "link_url": anuncio["link_url"] if _url_http_segura(anuncio["link_url"]) else "",
            }
            for anuncio in anuncios
        ]
    finally:
        conexao.close()

    return render_template(
        "index.html",
        vagas=vagas,
        anuncios=anuncios,
        suporte_whatsapp=numero_whatsapp_suporte(),
    )


def _url_http_segura(valor):
    if not valor:
        return True
    partes = urlparse(valor)
    return partes.scheme in {"http", "https"} and bool(partes.netloc)


def numero_whatsapp_suporte():
    valor = os.environ.get("SUPPORT_WHATSAPP", "")
    numero = re.sub(r"\D", "", valor)
    if not numero:
        return ""
    if len(numero) in {10, 11}:
        numero = f"55{numero}"
    if not numero.startswith("55") or len(numero) not in {12, 13}:
        app.logger.warning(
            "SUPPORT_WHATSAPP inválido; o link de atendimento ficará oculto."
        )
        return ""
    return numero


# CADASTRO DE CANDIDATO
@app.route("/cadastro/candidato", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def cadastro_candidato():

    if request.method == "POST":
        nome = request.form["nome"].strip()
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]

        cpf = request.form.get("cpf", "").strip()
        telefone = request.form.get("telefone", "").strip()
        cidade = request.form.get("cidade", "").strip()

        if not nome or len(nome) > 120 or not email_valido(email):
            flash("Informe nome e e-mail válidos.")
            return redirect(url_for("cadastro_candidato"))
        if len(senha) > 128 or len(cpf) > 20 or len(telefone) > 40 or len(cidade) > 100:
            flash("Um ou mais campos excedem o tamanho permitido.")
            return redirect(url_for("cadastro_candidato"))

        if senha != confirmar_senha:
            flash("As senhas não são iguais.")
            return redirect(url_for("cadastro_candidato"))

        if len(senha) < 10:
            flash("A senha precisa ter pelo menos 10 caracteres.")
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
@limiter.limit("5 per hour", methods=["POST"])
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

        if not nome or not nome_empresa or len(nome) > 120 or len(nome_empresa) > 160 or not email_valido(email):
            flash("Informe nome, empresa e e-mail válidos.")
            return redirect(url_for("cadastro_empresa"))
        if len(senha) > 128 or len(cnpj) > 24 or len(telefone) > 40 or len(cidade) > 100 or len(descricao) > 2000:
            flash("Um ou mais campos excedem o tamanho permitido.")
            return redirect(url_for("cadastro_empresa"))

        if senha != confirmar_senha:
            flash("As senhas não são iguais.")
            return redirect(url_for("cadastro_empresa"))

        if len(senha) < 10:
            flash("A senha precisa ter pelo menos 10 caracteres.")
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
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        senha = request.form["senha"]

        admin = buscar_admin_por_email(email)
        if admin:
            if check_password_hash(admin["senha_hash"], senha):
                session.clear()
                session["_csrf_token"] = secrets.token_urlsafe(32)
                session.permanent = True
                session["admin_id"] = admin["id"]
                session["nome"] = admin["email"]
                session["tipo"] = "admin"
                session["admin_trocar_senha"] = bool(admin["trocar_senha"])
                destino = (
                    "admin.trocar_senha"
                    if admin["trocar_senha"]
                    else "admin.dashboard"
                )
                return redirect(url_for(destino))

            flash("E-mail ou senha incorretos.")
            return render_template("login.html")

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email,)
        )

        usuario = cursor.fetchone()
        conexao.close()

        if (
            usuario
            and usuario["tipo"] in {"candidato", "empresa"}
            and check_password_hash(usuario["senha"], senha)
        ):
            session.clear()
            session["_csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["tipo"] = usuario["tipo"]

            return redirect(url_for("painel_empresarial"))

        flash("E-mail ou senha incorretos.")

    return render_template("login.html")



# Alias compatível com os links dos templates antigos e atuais.
@app.route("/painel")
def painel():
    return redirect(url_for("painel_empresarial"))


# PAINEL PRINCIPAL
@app.route("/painel_empresarial")
def painel_empresarial():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session.get("tipo") not in {"candidato", "empresa"}:
        session.clear()
        return redirect(url_for("login"))

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
                c.id AS candidatura_id,
                c.status,
                c.resposta_entrevista,
                c.entrevista_local, c.entrevista_data, c.entrevista_horario,
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
        cursor.execute("SELECT id, titulo, mensagem, link, lida, criado_em FROM notificacoes WHERE usuario_id=? ORDER BY id DESC LIMIT 20", (session["usuario_id"],))
        notificacoes = cursor.fetchall()

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
            "candidato/painel_candidato.html",
            nome=session["nome"],
            tipo="candidato",
            total_candidaturas=total_candidaturas,
            em_analise=em_analise,
            aprovadas=aprovadas,
            candidaturas=candidaturas,
            notificacoes=notificacoes
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
            c.id AS candidato_id, c.escolaridade, c.experiencia, c.habilidades, c.cursos, c.resumo_profissional, c.objetivo_profissional,
            u.nome AS candidato_nome,
            u.email AS candidato_email,
            c.telefone AS candidato_telefone,
            v.titulo AS vaga_titulo,
            candidaturas.status AS candidatura_status,
            candidaturas.resposta_entrevista AS resposta_entrevista,
            candidaturas.entrevista_local, candidaturas.entrevista_data, candidaturas.entrevista_horario,
            candidaturas.criado_em AS candidatura_criada_em
        FROM candidaturas
        INNER JOIN candidatos c ON c.id = candidaturas.candidato_id
        INNER JOIN usuarios u ON u.id = c.usuario_id
        INNER JOIN vagas v ON v.id = candidaturas.vaga_id
        WHERE v.empresa_id = ?
        ORDER BY candidaturas.id DESC
    """, (empresa["id"],))

    candidatos = cursor.fetchall()
    cursor.execute("SELECT id, titulo, mensagem, link, lida, criado_em FROM notificacoes WHERE usuario_id=? ORDER BY id DESC LIMIT 20", (session["usuario_id"],))
    notificacoes = cursor.fetchall()

    conexao.close()

    return render_template(
        "painel_empresarial.html",
        nome=session["nome"],
        tipo="empresa",
        empresa=empresa,
        vagas=vagas,
        total_vagas=total_vagas,
        vagas_abertas=vagas_abertas,
        total_candidaturas=total_candidaturas,
        total_entrevistas=total_entrevistas,
        total_selecoes_finalizadas=total_selecoes_finalizadas,
        candidatos=candidatos,
        notificacoes=notificacoes
    )



# MEU PERFIL DO CANDIDATO
@app.route("/meu-perfil", methods=["GET", "POST"])
def meu_perfil():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "candidato":
        flash("Acesso permitido somente para candidatos.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM candidatos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    candidato = cursor.fetchone()

    if not candidato:
        conexao.close()
        flash("Cadastro do candidato não encontrado.")
        return redirect(url_for("painel"))

    if request.method == "POST":

        telefone = request.form.get("telefone", "").strip()
        cidade = request.form.get("cidade", "").strip()
        escolaridade = request.form.get("escolaridade", "").strip()
        experiencia = request.form.get("experiencia", "").strip()
        habilidades = request.form.get("habilidades", "").strip()

        objetivo_profissional = request.form.get(
            "objetivo_profissional", ""
        ).strip()

        resumo_profissional = request.form.get(
            "resumo_profissional", ""
        ).strip()

        cursos = request.form.get("cursos", "").strip()

        cursor.execute("""
            UPDATE candidatos
            SET telefone = ?,
                cidade = ?,
                escolaridade = ?,
                experiencia = ?,
                habilidades = ?,
                objetivo_profissional = ?,
                resumo_profissional = ?,
                cursos = ?
            WHERE usuario_id = ?
        """, (
            telefone,
            cidade,
            escolaridade,
            experiencia,
            habilidades,
            objetivo_profissional,
            resumo_profissional,
            cursos,
            session["usuario_id"]
        ))

        conexao.commit()
        conexao.close()

        flash("Perfil atualizado com sucesso!")
        return redirect(url_for("meu_perfil"))

    conexao.close()

    return render_template(
        "candidato/meu_perfil.html",
        nome=session["nome"],
        candidato=candidato
    )




# CURRÍCULO DO CANDIDATO
@app.route("/curriculo")
def curriculo():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "candidato":
        flash("Acesso permitido somente para candidatos.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM candidatos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    candidato = cursor.fetchone()
    conexao.close()

    if not candidato:
        flash("Cadastro do candidato não encontrado.")
        return redirect(url_for("painel"))

    return render_template(
        "candidato/curriculo.html",
        candidato=candidato,
        codigo=f"EMP-{candidato['id']:06d}"
    )

# ==========================================
# ÁREA DO CANDIDATO — BUSCAR VAGAS
# ==========================================

@app.route("/buscar-vagas")
def buscar_vagas():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "candidato":
        flash("Acesso permitido somente para candidatos.")
        return redirect(url_for("painel"))

    pesquisa = request.args.get("q", "").strip()
    cidade = request.args.get("cidade", "").strip()

    conexao = conectar()
    cursor = conexao.cursor()

    sql = """
        SELECT
            v.id,
            v.titulo,
            v.descricao,
            v.requisitos,
            v.cidade,
            v.salario,
            v.criado_em,
            e.nome_empresa
        FROM vagas v
        INNER JOIN empresas e ON e.id = v.empresa_id
        WHERE v.status = 'aberta'
    """

    parametros = []

    if pesquisa:
        sql += """
            AND (
                v.titulo LIKE ?
                OR v.descricao LIKE ?
                OR v.requisitos LIKE ?
            )
        """

        termo = f"%{pesquisa}%"

        parametros.extend([termo, termo, termo])

    if cidade:
        sql += " AND v.cidade LIKE ?"
        parametros.append(f"%{cidade}%")

    sql += " ORDER BY v.id DESC"

    cursor.execute(sql, parametros)

    vagas = cursor.fetchall()

    conexao.close()

    return render_template(
        "candidato/buscar_vagas.html",
        nome=session["nome"],
        vagas=vagas,
        pesquisa=pesquisa,
        cidade=cidade
    )


# ==========================================
# DETALHES DA VAGA
# ==========================================

@app.route("/vaga/<int:vaga_id>")
def detalhes_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "candidato":
        flash("Acesso permitido somente para candidatos.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            v.*,
            e.nome_empresa,
            e.cidade AS cidade_empresa,
            e.descricao AS descricao_empresa
        FROM vagas v
        INNER JOIN empresas e ON e.id = v.empresa_id
        WHERE v.id = ? AND v.status = 'aberta'
    """, (vaga_id,))

    vaga = cursor.fetchone()

    if not vaga:
        conexao.close()
        flash("Esta vaga não está mais disponível.")
        return redirect(url_for("buscar_vagas"))

    cursor.execute("""
        SELECT c.id
        FROM candidaturas c
        INNER JOIN candidatos ca ON ca.id = c.candidato_id
        WHERE c.vaga_id = ?
        AND ca.usuario_id = ?
    """, (vaga_id, session["usuario_id"]))

    candidatura = cursor.fetchone()

    conexao.close()

    return render_template(
        "candidato/detalhes_vaga.html",
        nome=session["nome"],
        vaga=vaga,
        candidatura=candidatura
    )


# ==========================================
# CANDIDATAR-SE A UMA VAGA
# ==========================================

@app.route("/candidatar/<int:vaga_id>", methods=["POST"])
def candidatar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "candidato":
        flash("Acesso permitido somente para candidatos.")
        return redirect(url_for("painel"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id
        FROM candidatos
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    candidato = cursor.fetchone()

    if not candidato:
        conexao.close()
        flash("Cadastro do candidato não encontrado.")
        return redirect(url_for("painel"))

    cursor.execute("""
        SELECT id
        FROM vagas
        WHERE id = ? AND status = 'aberta'
    """, (vaga_id,))

    vaga = cursor.fetchone()

    if not vaga:
        conexao.close()
        flash("Esta vaga não está mais disponível.")
        return redirect(url_for("buscar_vagas"))

    cursor.execute("""
        SELECT id
        FROM candidaturas
        WHERE vaga_id = ? AND candidato_id = ?
    """, (vaga_id, candidato["id"]))

    candidatura_existente = cursor.fetchone()

    if candidatura_existente:
        conexao.close()
        flash("Você já se candidatou a esta vaga.")
        return redirect(url_for("detalhes_vaga", vaga_id=vaga_id))

    cursor.execute("""
        INSERT INTO candidaturas (vaga_id, candidato_id)
        VALUES (?, ?)
    """, (vaga_id, candidato["id"]))

    conexao.commit()
    conexao.close()

    flash("Sua candidatura foi enviada com sucesso!")

    return redirect(url_for("painel"))



# CADASTRAR NOVA VAGA
@app.route("/empresa/vaga/nova", methods=["GET", "POST"])
def nova_vaga():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel_empresarial"))

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
        return redirect(url_for("painel_empresarial"))

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
        return redirect(url_for("painel_empresarial"))

    conexao.close()

    return render_template("nova_vaga.html")


# EDITAR VAGA
@app.route("/empresa/vaga/editar/<int:vaga_id>", methods=["GET", "POST"])
def editar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        return redirect(url_for("painel_empresarial"))

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id FROM empresas
        WHERE usuario_id = ?
    """, (session["usuario_id"],))

    empresa = cursor.fetchone()

    if not empresa:
        conexao.close()
        return redirect(url_for("painel_empresarial"))

    cursor.execute("""
        SELECT * FROM vagas
        WHERE id = ? AND empresa_id = ?
    """, (vaga_id, empresa["id"]))

    vaga = cursor.fetchone()

    if not vaga:
        conexao.close()
        flash("Vaga não encontrada.")
        return redirect(url_for("painel_empresarial"))

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
        return redirect(url_for("painel_empresarial") + "#minhas-vagas")

    conexao.close()

    return render_template("editar_vaga.html", vaga=vaga)


# ENCERRAR VAGA
@app.route("/empresa/vaga/encerrar/<int:vaga_id>", methods=["POST"])
def encerrar_vaga(vaga_id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        return redirect(url_for("painel_empresarial") + "#minhas-vagas")

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

    return redirect(url_for("painel_empresarial") + "#minhas-vagas")


# ATUALIZAR STATUS DA VAGA
@app.route("/empresa/vaga/status/<int:vaga_id>", methods=["POST"])
def atualizar_status_vaga(vaga_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel_empresarial"))

    status = request.form.get("status", "")
    status_permitidos = {"aberta", "finalizada", "cancelada", "em_analise", "pausada"}
    if status not in status_permitidos:
        flash("Status de vaga inválido.")
        return redirect(url_for("painel_empresarial"))

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
    return redirect(url_for("painel_empresarial") + "#minhas-vagas")


# PAUSAR VAGA
@app.route("/empresa/vaga/pausar/<int:vaga_id>", methods=["POST"])
def pausar_vaga(vaga_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel_empresarial") + "#minhas-vagas")

    pausa_ate = request.form.get("pausa_ate", "").strip()
    if pausa_ate:
        try:
            data_reabertura = datetime.strptime(pausa_ate, "%Y-%m-%d").date()
        except ValueError:
            flash("Selecione uma data válida para reabrir a vaga.")
            return redirect(url_for("painel_empresarial") + "#minhas-vagas")

        if data_reabertura <= date.today():
            flash("A data de reabertura precisa ser futura.")
            return redirect(url_for("painel_empresarial") + "#minhas-vagas")
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
    return redirect(url_for("painel_empresarial") + "#minhas-vagas")


# RESPOSTA DO CANDIDATO AO CONVITE DE ENTREVISTA
@app.route("/candidato/candidatura/<int:candidatura_id>/responder-entrevista", methods=["POST"])
def responder_convite_entrevista(candidatura_id):
    if "usuario_id" not in session or session.get("tipo") != "candidato":
        flash("Entre na sua conta de candidato para responder ao convite.")
        return redirect(url_for("login"))

    resposta = (request.form.get("resposta") or "").strip().lower()
    if resposta not in {"aceita", "recusada"}:
        flash("Resposta inválida. Escolha aceitar ou recusar o convite.")
        return redirect(url_for("painel_empresarial") + "#minhas-vagas")

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM candidatos WHERE usuario_id = ?", (session["usuario_id"],))
    candidato = cursor.fetchone()
    if not candidato:
        conexao.close()
        flash("Perfil de candidato não encontrado.")
        return redirect(url_for("painel_empresarial"))

    cursor.execute("""
        UPDATE candidaturas
        SET resposta_entrevista = ?
        WHERE id = ?
          AND candidato_id = ?
          AND status = 'entrevista'
          AND COALESCE(resposta_entrevista, 'pendente') = 'pendente'
    """, (resposta, candidatura_id, candidato["id"]))
    atualizadas = cursor.rowcount
    if atualizadas and resposta == "aceita":
        cursor.execute("""INSERT INTO notificacoes (usuario_id, titulo, mensagem, link)
            SELECT e.usuario_id, 'Entrevista aceita', 'O candidato aceitou o convite. Consulte os detalhes no painel da empresa.', '/painel_empresarial#candidatos'
            FROM candidaturas c JOIN vagas v ON v.id=c.vaga_id JOIN empresas e ON e.id=v.empresa_id WHERE c.id=?""", (candidatura_id,))
    conexao.commit()
    conexao.close()

    if atualizadas:
        flash("Convite aceito! Os dados completos da entrevista já estão disponíveis no seu painel." if resposta == "aceita" else "Você recusou o convite de entrevista.")
    else:
        flash("Esse convite não está disponível ou já recebeu uma resposta.")
    return redirect(url_for("painel_empresarial") + "#minhas-vagas")


# CURRÍCULO DO CANDIDATO — acesso restrito à empresa responsável pela candidatura
@app.route("/empresa/curriculo/<int:candidatura_id>")
def visualizar_curriculo_candidato(candidatura_id):
    if session.get("tipo") != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("login"))
    con = conectar(); cur = con.cursor()
    cur.execute("""SELECT u.nome, ca.escolaridade, ca.experiencia, ca.habilidades, ca.cursos,
        ca.objetivo_profissional, ca.resumo_profissional, v.titulo
        FROM candidaturas ca2 JOIN candidatos ca ON ca.id=ca2.candidato_id
        JOIN usuarios u ON u.id=ca.usuario_id JOIN vagas v ON v.id=ca2.vaga_id
        JOIN empresas e ON e.id=v.empresa_id
        WHERE ca2.id=? AND e.usuario_id=?""", (candidatura_id, session["usuario_id"]))
    curriculo = cur.fetchone(); con.close()
    if not curriculo:
        abort(404)
    return render_template("empresa_curriculo.html", curriculo=curriculo)


def enviar_email_convite(destinatario, nome, empresa, vaga):
    """Envia aviso por SMTP quando as variáveis SMTP estiverem configuradas."""
    host=os.environ.get("SMTP_HOST"); user=os.environ.get("SMTP_USER"); password=os.environ.get("SMTP_PASSWORD")
    if not all([host, user, password, destinatario]):
        return False
    msg=EmailMessage(); msg["Subject"]="Você recebeu um convite de entrevista — Emprega Serra"
    msg["From"]=os.environ.get("SMTP_FROM", user); msg["To"]=destinatario
    msg.set_content(f"Olá, {nome}!\n\n{empresa} enviou um convite para entrevista referente à vaga {vaga}. Entre na sua conta do Emprega Serra para responder ao convite e consultar gratuitamente os dados da entrevista.\n\nO Emprega Serra não cobra por candidaturas, convites ou entrevistas.")
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.starttls(); smtp.login(user,password); smtp.send_message(msg)
    return True


@app.route("/empresa/enviar-convites", methods=["POST"])
def enviar_convites_em_lote():
    if session.get("tipo") != "empresa":
        return redirect(url_for("login"))
    ids=request.form.getlist("candidatura_ids")
    local=(request.form.get("local") or "").strip(); data=(request.form.get("data") or "").strip(); horario=(request.form.get("horario") or "").strip()
    if not ids or not local or not data or not horario:
        flash("Selecione candidatos e informe local, data e horário."); return redirect(url_for("painel_empresarial")+"#candidatos")
    con=conectar(); cur=con.cursor(); enviados=0; emails=0
    cur.execute("SELECT id,nome_empresa FROM empresas WHERE usuario_id=?", (session["usuario_id"],)); emp=cur.fetchone()
    for cid in ids:
        cur.execute("""UPDATE candidaturas SET status='entrevista', resposta_entrevista='pendente',
            entrevista_local=?, entrevista_data=?, entrevista_horario=?
            WHERE id=? AND vaga_id IN (SELECT id FROM vagas WHERE empresa_id=?)""", (local,data,horario,cid,emp["id"]))
        if cur.rowcount:
            enviados+=1
            cur.execute("""SELECT u.email,u.nome,v.titulo FROM candidaturas c JOIN candidatos ca ON ca.id=c.candidato_id
                JOIN usuarios u ON u.id=ca.usuario_id JOIN vagas v ON v.id=c.vaga_id WHERE c.id=?""", (cid,))
            dest=cur.fetchone()
            if dest:
                cur.execute("INSERT INTO notificacoes (usuario_id, titulo, mensagem, link) SELECT ca.usuario_id, 'Novo convite de entrevista', ?, '/painel_empresarial#minhas-vagas' FROM candidaturas c JOIN candidatos ca ON ca.id=c.candidato_id WHERE c.id=?", (f"{emp['nome_empresa']} convidou você para entrevista na vaga {dest['titulo']}. Responda no seu painel.", cid))
            try:
                if dest and enviar_email_convite(dest["email"],dest["nome"],emp["nome_empresa"],dest["titulo"]): emails+=1
            except Exception:
                app.logger.exception("Falha ao enviar e-mail de convite")
    con.commit(); con.close()
    flash(f"{enviados} convite(s) enviado(s). Avisos por e-mail enviados: {emails}. Notificações internas já estão disponíveis no painel dos candidatos.")
    return redirect(url_for("painel_empresarial")+"#candidatos")



# ATUALIZAR ETAPA DA CANDIDATURA
@app.route("/empresa/candidatura/status/<int:candidatura_id>", methods=["POST"])
def atualizar_status_candidatura(candidatura_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if session["tipo"] != "empresa":
        flash("Acesso permitido somente para empresas.")
        return redirect(url_for("painel_empresarial"))

    status = request.form.get("status", "")
    status_permitidos = {
        "enviada",
        "entrevista",
        "aprovada",
        "aprovado",
        "reprovada",
        "selecao_finalizada",
    }
    if status not in status_permitidos:
        flash("Etapa de candidatura inválida.")
        return redirect(url_for("painel_empresarial"))

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE candidaturas
        SET
            resposta_entrevista = CASE
                WHEN ? = 'entrevista' AND status <> 'entrevista' THEN 'pendente'
                WHEN ? = 'entrevista' THEN COALESCE(resposta_entrevista, 'pendente')
                ELSE NULL
            END,
            status = ?
        WHERE id = ?
        AND vaga_id IN (
            SELECT id FROM vagas
            WHERE empresa_id = (
                SELECT id FROM empresas WHERE usuario_id = ?
            )
        )
    """, (status, status, status, candidatura_id, session["usuario_id"]))
    conexao.commit()

    if cursor.rowcount:
        flash("Etapa do candidato atualizada com sucesso.")
    else:
        flash("Não foi possível localizar essa candidatura.")

    conexao.close()
    return redirect(url_for("painel_empresarial") + "#candidatos")




@app.route("/servicos", methods=["GET", "POST"])
def servicos():
    if request.method == "POST":
        if not session.get("usuario_id") or session.get("tipo") not in {"candidato", "empresa"}:
            flash("Entre como profissional ou empresa para anunciar um serviço gratuitamente.")
            return redirect(url_for("login"))
        titulo=(request.form.get("titulo") or "").strip()[:100]
        categoria=(request.form.get("categoria") or "").strip()[:60]
        descricao=(request.form.get("descricao") or "").strip()[:1200]
        cidade=(request.form.get("cidade") or "").strip()[:80]
        whatsapp=re.sub(r"\D", "", request.form.get("whatsapp") or "")[:20]
        if not all([titulo,categoria,descricao,cidade]):
            flash("Preencha título, categoria, descrição e cidade.")
        else:
            con=conectar(); con.execute("INSERT INTO servicos (usuario_id,titulo,categoria,descricao,cidade,whatsapp) VALUES (?,?,?,?,?,?)", (session["usuario_id"],titulo,categoria,descricao,cidade,whatsapp)); con.commit(); con.close()
            flash("Seu serviço foi publicado gratuitamente!")
        return redirect(url_for("servicos"))
    con=conectar(); cur=con.cursor()
    termo=(request.args.get("q") or "").strip()[:80]
    cidade=(request.args.get("cidade") or "").strip()[:80]
    sql="SELECT s.*,u.nome AS anunciante FROM servicos s JOIN usuarios u ON u.id=s.usuario_id WHERE s.status='ativo'"
    params=[]
    if termo: sql += " AND (s.titulo LIKE ? OR s.categoria LIKE ? OR s.descricao LIKE ?)"; params += [f"%{termo}%"]*3
    if cidade: sql += " AND s.cidade LIKE ?"; params.append(f"%{cidade}%")
    cur.execute(sql+" ORDER BY s.id DESC LIMIT 100",params); itens=cur.fetchall(); con.close()
    return render_template("servicos.html", servicos=itens, termo=termo, cidade=cidade)


@app.route("/servicos/<int:servico_id>/excluir", methods=["POST"])
def excluir_servico(servico_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    con=conectar(); cur=con.cursor()
    cur.execute("DELETE FROM servicos WHERE id=? AND usuario_id=?",(servico_id,session["usuario_id"]))
    con.commit(); apagado=cur.rowcount; con.close()
    flash("Serviço removido." if apagado else "Não foi possível remover esse serviço.")
    return redirect(url_for("servicos"))


@app.route("/cursos")
def cursos():
    catalogo=[
        {"nome":"Escola Virtual Fundação Bradesco","tema":"Informática, administração, desenvolvimento pessoal e tecnologia","url":"https://www.ev.org.br/","selo":"Cursos gratuitos"},
        {"nome":"Sebrae — Cursos online","tema":"Empreendedorismo, gestão, vendas, finanças e pequenos negócios","url":"https://sebrae.com.br/sites/PortalSebrae/cursosonline","selo":"Empreendedorismo"},
        {"nome":"Escola Virtual de Governo","tema":"Gestão, atendimento, comunicação, tecnologia e setor público","url":"https://www.escolavirtual.gov.br/","selo":"Formação online"},
        {"nome":"Escola do Trabalhador 4.0","tema":"Competências digitais e preparação para o mercado de trabalho","url":"https://ead.escoladotrabalhador40.com.br/","selo":"Competências digitais"},
    ]
    return render_template("cursos.html", cursos=catalogo)


@app.route("/mapa")
def mapa_regional():
    con=conectar(); cur=con.cursor()
    cur.execute("SELECT cidade, COUNT(*) AS total FROM vagas WHERE status='aberta' GROUP BY cidade ORDER BY total DESC, cidade")
    cidades=cur.fetchall(); con.close()
    return render_template("mapa.html", cidades=cidades)


@app.route("/notificacoes/<int:notificacao_id>/lida", methods=["POST"])
def marcar_notificacao_lida(notificacao_id):
    if not session.get("usuario_id"):
        return redirect(url_for("login"))
    con=conectar(); con.execute("UPDATE notificacoes SET lida=1 WHERE id=? AND usuario_id=?",(notificacao_id,session["usuario_id"])); con.commit(); con.close()
    return redirect(url_for("painel_empresarial")+"#notificacoes")


# SAIR
@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    modo_debug = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=modo_debug,
    )