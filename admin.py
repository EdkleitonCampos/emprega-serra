import os
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash

from database import conectar

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login"))
        if session.get("tipo") != "admin":
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def garantir_admin_inicial():
    """Cria/promove a conta administrativa somente quando as duas variáveis estão configuradas."""
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    senha = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not senha:
        return
    if len(senha) < 12:
        raise RuntimeError("ADMIN_PASSWORD precisa ter pelo menos 12 caracteres.")

    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        if usuario:
            cursor.execute(
                "UPDATE usuarios SET tipo = 'admin', senha = ? WHERE id = ?",
                (generate_password_hash(senha), usuario["id"])
            )
        else:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'admin')",
                ("Administrador Emprega Serra", email, generate_password_hash(senha))
            )
        conexao.commit()
    finally:
        conexao.close()


@admin_bp.route("/")
@admin_required
def dashboard():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM candidatos")
    total_candidatos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM empresas")
    total_empresas = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM vagas")
    total_vagas = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM candidaturas")
    total_candidaturas = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM anuncios WHERE status = 'ativo'")
    anuncios_ativos = cursor.fetchone()["total"]
    cursor.execute("""
        SELECT id, nome, email, tipo, criado_em
        FROM usuarios ORDER BY id DESC LIMIT 20
    """)
    usuarios = cursor.fetchall()
    cursor.execute("""
        SELECT a.id, a.titulo, a.status, a.posicao, a.inicio, a.fim,
               COALESCE(n.nome, 'Sem anunciante') AS anunciante
        FROM anuncios a LEFT JOIN anunciantes n ON n.id = a.anunciante_id
        ORDER BY a.id DESC LIMIT 10
    """)
    anuncios = cursor.fetchall()
    conexao.close()
    return render_template(
        "admin/dashboard.html",
        total_usuarios=total_usuarios,
        total_candidatos=total_candidatos,
        total_empresas=total_empresas,
        total_vagas=total_vagas,
        total_candidaturas=total_candidaturas,
        anuncios_ativos=anuncios_ativos,
        usuarios=usuarios,
        anuncios=anuncios
    )


@admin_bp.route("/anunciantes", methods=["GET", "POST"])
@admin_required
def anunciantes():
    conexao = conectar()
    cursor = conexao.cursor()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Informe o nome do anunciante.")
        else:
            cursor.execute("""
                INSERT INTO anunciantes (nome, contato, telefone, email)
                VALUES (?, ?, ?, ?)
            """, (
                nome,
                request.form.get("contato", "").strip(),
                request.form.get("telefone", "").strip(),
                request.form.get("email", "").strip().lower()
            ))
            conexao.commit()
            flash("Anunciante cadastrado.")
            conexao.close()
            return redirect(url_for("admin.anunciantes"))
    cursor.execute("SELECT * FROM anunciantes ORDER BY id DESC")
    lista = cursor.fetchall()
    conexao.close()
    return render_template("admin/anunciantes.html", anunciantes=lista)


@admin_bp.route("/anuncios", methods=["GET", "POST"])
@admin_required
def anuncios():
    conexao = conectar()
    cursor = conexao.cursor()
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        anunciante_id = request.form.get("anunciante_id") or None
        posicao = request.form.get("posicao", "lateral")
        if not titulo or posicao not in {"destaque", "lateral", "rodape"}:
            flash("Informe um título e uma posição válida.")
        else:
            cursor.execute("""
                INSERT INTO anuncios
                (anunciante_id, titulo, descricao, imagem_url, link_url, posicao, status, inicio, fim)
                VALUES (?, ?, ?, ?, ?, ?, 'pausado', ?, ?)
            """, (
                anunciante_id, titulo,
                request.form.get("descricao", "").strip(),
                request.form.get("imagem_url", "").strip(),
                request.form.get("link_url", "").strip(),
                posicao,
                request.form.get("inicio") or None,
                request.form.get("fim") or None
            ))
            conexao.commit()
            flash("Anúncio cadastrado como pausado. Revise e ative quando estiver pronto.")
            conexao.close()
            return redirect(url_for("admin.anuncios"))
    cursor.execute("SELECT id, nome FROM anunciantes WHERE ativo = 1 ORDER BY nome")
    anunciantes_lista = cursor.fetchall()
    cursor.execute("""
        SELECT a.*, COALESCE(n.nome, 'Sem anunciante') AS anunciante
        FROM anuncios a LEFT JOIN anunciantes n ON n.id = a.anunciante_id
        ORDER BY a.id DESC
    """)
    lista = cursor.fetchall()
    conexao.close()
    return render_template(
        "admin/anuncios.html",
        anuncios=lista,
        anunciantes=anunciantes_lista
    )


@admin_bp.route("/anuncios/<int:anuncio_id>/status", methods=["POST"])
@admin_required
def status_anuncio(anuncio_id):
    status = request.form.get("status")
    if status not in {"ativo", "pausado", "encerrado"}:
        abort(400)
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("UPDATE anuncios SET status = ? WHERE id = ?", (status, anuncio_id))
    conexao.commit()
    encontrado = cursor.rowcount
    conexao.close()
    flash("Status do anúncio atualizado." if encontrado else "Anúncio não encontrado.")
    return redirect(url_for("admin.anuncios"))


@admin_bp.route("/anuncios/<int:anuncio_id>/excluir", methods=["POST"])
@admin_required
def excluir_anuncio(anuncio_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM anuncios WHERE id = ?", (anuncio_id,))
    conexao.commit()
    encontrado = cursor.rowcount
    conexao.close()
    flash("Anúncio excluído." if encontrado else "Anúncio não encontrado.")
    return redirect(url_for("admin.anuncios"))
