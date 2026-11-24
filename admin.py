from datetime import datetime
import csv
from io import StringIO
from urllib.parse import urlparse
from functools import wraps
from io import BytesIO
from xml.sax.saxutils import escape

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    Response,
    request,
    send_file,
    session,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from werkzeug.security import check_password_hash

from database import conectar
from admin_database import (
    atualizar_senha_admin,
    buscar_admin_por_id,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _relatorio_pdf(nome_arquivo, titulo, cabecalhos, registros, proporcoes_colunas):
    buffer = BytesIO()
    margem = 36
    largura_util = landscape(A4)[0] - 2 * margem
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "AdminReportTitle",
        parent=estilos["Title"],
        alignment=TA_LEFT,
        textColor=colors.HexColor("#101a35"),
        fontName="Helvetica-Bold",
        fontSize=18,
        spaceAfter=5,
    )
    estilo_data = ParagraphStyle(
        "AdminReportDate",
        parent=estilos["Normal"],
        textColor=colors.HexColor("#53617a"),
        fontSize=9,
        spaceAfter=14,
    )
    estilo_celula = ParagraphStyle(
        "AdminReportCell",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        wordWrap="CJK",
    )
    estilo_cabecalho = ParagraphStyle(
        "AdminReportHeader",
        parent=estilo_celula,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    tabela_dados = [
        [Paragraph(escape(str(valor)), estilo_cabecalho) for valor in cabecalhos]
    ]
    for registro in registros:
        tabela_dados.append([
            Paragraph(
                escape(str(valor if valor not in (None, "") else "Nao informado")),
                estilo_celula,
            )
            for valor in registro
        ])

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=margem,
        rightMargin=margem,
        topMargin=36,
        bottomMargin=34,
        title=titulo,
        author="Emprega Serra",
    )
    tabela = Table(
        tabela_dados,
        colWidths=[largura_util * proporcao for proporcao in proporcoes_colunas],
        repeatRows=1,
        hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17264a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#f1f4fa"),
        ]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5dbea")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#53617a"))
        canvas.drawString(margem, 18, "Emprega Serra")
        canvas.drawRightString(landscape(A4)[0] - margem, 18, f"Pagina {doc.page}")
        canvas.restoreState()

    documento.build(
        [
            Paragraph(escape(titulo), estilo_titulo),
            Paragraph(
                "Gerado em " + datetime.now().strftime("%d/%m/%Y %H:%M"),
                estilo_data,
            ),
            tabela,
        ],
        onFirstPage=rodape,
        onLaterPages=rodape,
    )
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome_arquivo,
    )


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login"))
        if session.get("tipo") != "admin":
            abort(403)
        if (
            session.get("admin_trocar_senha")
            and request.endpoint != "admin.trocar_senha"
        ):
            return redirect(url_for("admin.trocar_senha"))
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route("/trocar-senha", methods=["GET", "POST"])
@admin_required
def trocar_senha():
    if not session.get("admin_trocar_senha"):
        return redirect(url_for("admin.dashboard"))

    admin = buscar_admin_por_id(session["admin_id"])
    if not admin:
        session.clear()
        flash("Conta administrativa não encontrada. Entre novamente.")
        return redirect(url_for("login"))

    if request.method == "POST":
        senha_atual = request.form.get("senha_atual", "")
        nova_senha = request.form.get("nova_senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not check_password_hash(admin["senha_hash"], senha_atual):
            flash("A senha temporária está incorreta.")
        elif len(nova_senha) < 12:
            flash("A nova senha precisa ter pelo menos 12 caracteres.")
        elif nova_senha != confirmar_senha:
            flash("As senhas novas não são iguais.")
        elif nova_senha == senha_atual:
            flash("Escolha uma senha diferente da senha temporária.")
        else:
            atualizar_senha_admin(admin["id"], nova_senha)
            session["admin_trocar_senha"] = False
            flash("Senha atualizada. Bem-vindo ao painel administrativo.")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/trocar_senha.html", email=admin["email"])


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
        SELECT e.nome_empresa, u.nome AS responsavel, u.email,
               e.cidade, u.criado_em
        FROM empresas e
        JOIN usuarios u ON u.id = e.usuario_id
        ORDER BY u.criado_em DESC, e.id DESC
        LIMIT 8
    """)
    empresas_recentes = cursor.fetchall()
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
        empresas_recentes=empresas_recentes,
        anuncios=anuncios
    )


@admin_bp.route("/empresas")
@admin_required
def empresas_cadastradas():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT e.nome_empresa, u.nome AS responsavel, u.email,
                   e.telefone, e.cidade, u.criado_em
            FROM empresas e
            JOIN usuarios u ON u.id = e.usuario_id
            ORDER BY u.criado_em DESC, e.id DESC
        """)
        empresas = cursor.fetchall()
    finally:
        conexao.close()

    return render_template("admin/empresas.html", empresas=empresas)


@admin_bp.route("/candidatos")
@admin_required
def candidatos_cadastrados():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT u.nome, u.email, c.telefone, c.cidade,
                   c.escolaridade, u.criado_em
            FROM candidatos c
            JOIN usuarios u ON u.id = c.usuario_id
            ORDER BY u.criado_em DESC, c.id DESC
        """)
        candidatos = cursor.fetchall()
    finally:
        conexao.close()

    return render_template("admin/candidatos.html", candidatos=candidatos)


@admin_bp.route("/exportar/vagas.pdf")
@admin_required
def exportar_vagas_pdf():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT v.titulo, e.nome_empresa, v.cidade, v.salario,
                   v.descricao, v.criado_em
            FROM vagas v
            JOIN empresas e ON e.id = v.empresa_id
            WHERE v.status = 'aberta'
            ORDER BY v.criado_em DESC, v.id DESC
        """)
        vagas = cursor.fetchall()
    finally:
        conexao.close()

    return _relatorio_pdf(
        "vagas-disponiveis.pdf",
        "Vagas disponiveis",
        ["Vaga", "Empresa", "Cidade", "Salario", "Descricao", "Publicada em"],
        [tuple(vaga) for vaga in vagas],
        [0.16, 0.15, 0.12, 0.10, 0.32, 0.15],
    )


@admin_bp.route("/exportar/empresas.pdf")
@admin_required
def exportar_empresas_pdf():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT e.nome_empresa, u.email, e.telefone, e.cidade, u.criado_em
            FROM empresas e
            JOIN usuarios u ON u.id = e.usuario_id
            ORDER BY u.criado_em DESC, e.id DESC
        """)
        empresas = cursor.fetchall()
    finally:
        conexao.close()

    return _relatorio_pdf(
        "relacao-de-empresas.pdf",
        "Empresas cadastradas",
        ["Empresa", "E-mail", "Telefone", "Cidade", "Cadastro em"],
        [tuple(empresa) for empresa in empresas],
        [0.24, 0.28, 0.15, 0.15, 0.18],
    )


@admin_bp.route("/exportar/candidatos.pdf")
@admin_required
def exportar_candidatos_pdf():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT u.nome, u.email, c.telefone, c.cidade, c.escolaridade
            FROM candidatos c
            JOIN usuarios u ON u.id = c.usuario_id
            ORDER BY u.nome COLLATE NOCASE, u.id
        """)
        candidatos = cursor.fetchall()
    finally:
        conexao.close()

    return _relatorio_pdf(
        "relacao-de-candidatos.pdf",
        "Relacao de candidatos cadastrados",
        ["Nome", "E-mail", "Telefone", "Cidade", "Escolaridade"],
        [tuple(candidato) for candidato in candidatos],
        [0.23, 0.28, 0.16, 0.16, 0.17],
    )


@admin_bp.route("/exportar/candidatos-aprovados.pdf")
@admin_required
def exportar_candidatos_aprovados_pdf():
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT u.nome, u.email, c.telefone, c.cidade, v.titulo,
                   e.nome_empresa, c.escolaridade, candidaturas.criado_em
            FROM candidaturas
            JOIN candidatos c ON c.id = candidaturas.candidato_id
            JOIN usuarios u ON u.id = c.usuario_id
            JOIN vagas v ON v.id = candidaturas.vaga_id
            JOIN empresas e ON e.id = v.empresa_id
            WHERE lower(candidaturas.status) IN ('aprovada', 'aprovado')
            ORDER BY e.nome_empresa COLLATE NOCASE, v.titulo COLLATE NOCASE,
                     u.nome COLLATE NOCASE
        """)
        candidatos = cursor.fetchall()
    finally:
        conexao.close()

    return _relatorio_pdf(
        "candidatos-aprovados-por-empresas.pdf",
        "Candidatos aprovados por empresas",
        [
            "Candidato",
            "E-mail",
            "Telefone",
            "Cidade",
            "Vaga",
            "Empresa",
            "Escolaridade",
            "Data da candidatura",
        ],
        [tuple(candidato) for candidato in candidatos],
        [0.14, 0.18, 0.11, 0.10, 0.16, 0.15, 0.08, 0.08],
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
        imagem_url = request.form.get("imagem_url", "").strip()
        link_url = request.form.get("link_url", "").strip()
        def url_http_segura(valor):
            if not valor:
                return True
            partes = urlparse(valor)
            return partes.scheme in {"http", "https"} and bool(partes.netloc)
        if not titulo or posicao not in {"destaque", "lateral", "rodape"}:
            flash("Informe um título e uma posição válida.")
        elif not url_http_segura(imagem_url) or not url_http_segura(link_url):
            flash("Os endereços de imagem e destino devem começar com http:// ou https://.")
        else:
            cursor.execute("""
                INSERT INTO anuncios
                (anunciante_id, titulo, descricao, imagem_url, link_url, posicao, status, inicio, fim)
                VALUES (?, ?, ?, ?, ?, ?, 'pausado', ?, ?)
            """, (
                anunciante_id, titulo,
                request.form.get("descricao", "").strip(),
                imagem_url,
                link_url,
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


# ==========================================================
# GERENCIAMENTO DE USUÁRIOS E VAGAS (CRUD + FILTROS)
# ==========================================================

@admin_bp.route("/usuarios")
@admin_required
def usuarios():
    termo = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "").strip()
    conexao = conectar()
    try:
        sql = """
            SELECT u.id, u.nome, u.email, u.tipo, u.criado_em
            FROM usuarios u
            WHERE (? = '' OR u.nome LIKE ? OR u.email LIKE ?)
              AND (? = '' OR u.tipo = ?)
            ORDER BY u.id DESC
            LIMIT 500
        """
        like = f"%{termo}%"
        lista = conexao.execute(sql, (termo, like, like, tipo, tipo)).fetchall()
    finally:
        conexao.close()
    return render_template("admin/usuarios.html", usuarios=lista, q=termo, tipo=tipo)


@admin_bp.route("/usuarios/<int:usuario_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_usuario(usuario_id):
    conexao = conectar()
    try:
        usuario = conexao.execute(
            "SELECT id, nome, email, tipo FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        if not usuario:
            flash("Usuário não encontrado.")
            return redirect(url_for("admin.usuarios"))

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            email = request.form.get("email", "").strip().lower()
            if not nome or not email or "@" not in email:
                flash("Informe nome e e-mail válidos.")
            else:
                try:
                    conexao.execute(
                        "UPDATE usuarios SET nome = ?, email = ? WHERE id = ?",
                        (nome, email, usuario_id),
                    )
                    conexao.commit()
                    flash("Usuário atualizado com sucesso.")
                    return redirect(url_for("admin.usuarios"))
                except Exception:
                    conexao.rollback()
                    flash("Não foi possível atualizar. Verifique se o e-mail já está em uso.")
    finally:
        conexao.close()
    return render_template("admin/editar_usuario.html", usuario=usuario)


@admin_bp.route("/usuarios/<int:usuario_id>/excluir", methods=["POST"])
@admin_required
def excluir_usuario(usuario_id):
    conexao = conectar()
    try:
        usuario = conexao.execute(
            "SELECT id, tipo FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if not usuario:
            flash("Usuário não encontrado.")
            return redirect(url_for("admin.usuarios"))

        if usuario["tipo"] == "candidato":
            candidato = conexao.execute(
                "SELECT id FROM candidatos WHERE usuario_id = ?", (usuario_id,)
            ).fetchone()
            if candidato:
                conexao.execute(
                    "DELETE FROM candidaturas WHERE candidato_id = ?", (candidato["id"],)
                )
                conexao.execute(
                    "DELETE FROM candidatos WHERE id = ?", (candidato["id"],)
                )
        elif usuario["tipo"] == "empresa":
            empresa = conexao.execute(
                "SELECT id FROM empresas WHERE usuario_id = ?", (usuario_id,)
            ).fetchone()
            if empresa:
                vaga_ids = [
                    row["id"] for row in conexao.execute(
                        "SELECT id FROM vagas WHERE empresa_id = ?", (empresa["id"],)
                    ).fetchall()
                ]
                if vaga_ids:
                    placeholders = ",".join("?" for _ in vaga_ids)
                    conexao.execute(
                        f"DELETE FROM candidaturas WHERE vaga_id IN ({placeholders})",
                        vaga_ids,
                    )
                    conexao.execute(
                        f"DELETE FROM vagas WHERE id IN ({placeholders})",
                        vaga_ids,
                    )
                conexao.execute("DELETE FROM empresas WHERE id = ?", (empresa["id"],))

        conexao.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conexao.commit()
        flash("Usuário e registros relacionados excluídos.")
    except Exception:
        conexao.rollback()
        flash("Não foi possível excluir o usuário. Nenhum dado foi removido.")
    finally:
        conexao.close()
    return redirect(url_for("admin.usuarios"))


@admin_bp.route("/vagas")
@admin_required
def vagas_gerenciar():
    termo = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    conexao = conectar()
    try:
        like = f"%{termo}%"
        lista = conexao.execute("""
            SELECT v.id, v.titulo, v.cidade, v.status, v.criado_em,
                   e.nome_empresa
            FROM vagas v
            JOIN empresas e ON e.id = v.empresa_id
            WHERE (? = '' OR v.titulo LIKE ? OR e.nome_empresa LIKE ? OR v.cidade LIKE ?)
              AND (? = '' OR v.status = ?)
            ORDER BY v.id DESC
            LIMIT 500
        """, (termo, like, like, like, status, status)).fetchall()
    finally:
        conexao.close()
    return render_template("admin/vagas.html", vagas=lista, q=termo, status=status)


@admin_bp.route("/vagas/<int:vaga_id>/excluir", methods=["POST"])
@admin_required
def excluir_vaga_admin(vaga_id):
    conexao = conectar()
    try:
        conexao.execute("DELETE FROM candidaturas WHERE vaga_id = ?", (vaga_id,))
        cursor = conexao.execute("DELETE FROM vagas WHERE id = ?", (vaga_id,))
        conexao.commit()
        flash("Vaga e candidaturas relacionadas excluídas." if cursor.rowcount else "Vaga não encontrada.")
    except Exception:
        conexao.rollback()
        flash("Não foi possível excluir a vaga.")
    finally:
        conexao.close()
    return redirect(url_for("admin.vagas_gerenciar"))


def _csv_response(nome_arquivo, cabecalhos, linhas):
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(cabecalhos)
    def proteger_formula(valor):
        if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + valor
        return valor
    writer.writerows([[proteger_formula(valor) for valor in linha] for linha in linhas])
    conteudo = "\ufeff" + buffer.getvalue()
    return Response(
        conteudo,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@admin_bp.route("/exportar/usuarios.csv")
@admin_required
def exportar_usuarios_csv():
    termo = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "").strip()
    like = f"%{termo}%"
    conexao = conectar()
    try:
        rows = conexao.execute("""
            SELECT id, nome, email, tipo, criado_em FROM usuarios
            WHERE (? = '' OR nome LIKE ? OR email LIKE ?)
              AND (? = '' OR tipo = ?)
            ORDER BY id DESC
        """, (termo, like, like, tipo, tipo)).fetchall()
    finally:
        conexao.close()
    return _csv_response("usuarios-emprega-serra.csv",
                         ["ID", "Nome", "E-mail", "Tipo", "Cadastro"],
                         [tuple(row) for row in rows])


@admin_bp.route("/exportar/vagas.csv")
@admin_required
def exportar_vagas_csv():
    termo = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    like = f"%{termo}%"
    conexao = conectar()
    try:
        rows = conexao.execute("""
            SELECT v.id, v.titulo, e.nome_empresa, v.cidade, v.salario, v.status, v.criado_em
            FROM vagas v JOIN empresas e ON e.id = v.empresa_id
            WHERE (? = '' OR v.titulo LIKE ? OR e.nome_empresa LIKE ? OR v.cidade LIKE ?)
              AND (? = '' OR v.status = ?)
            ORDER BY v.id DESC
        """, (termo, like, like, like, status, status)).fetchall()
    finally:
        conexao.close()
    return _csv_response("vagas-emprega-serra.csv",
                         ["ID", "Vaga", "Empresa", "Cidade", "Salário", "Status", "Cadastro"],
                         [tuple(row) for row in rows])


@admin_bp.route("/exportar/empresas.csv")
@admin_required
def exportar_empresas_csv():
    conexao = conectar()
    try:
        rows = conexao.execute("""
            SELECT e.nome_empresa, u.nome, u.email, e.telefone, e.cidade, u.criado_em
            FROM empresas e JOIN usuarios u ON u.id = e.usuario_id
            ORDER BY e.id DESC
        """).fetchall()
    finally:
        conexao.close()
    return _csv_response("empresas-emprega-serra.csv",
                         ["Empresa", "Responsável", "E-mail", "Telefone", "Cidade", "Cadastro"],
                         [tuple(row) for row in rows])


@admin_bp.route("/exportar/candidatos.csv")
@admin_required
def exportar_candidatos_csv():
    conexao = conectar()
    try:
        rows = conexao.execute("""
            SELECT u.nome, u.email, c.telefone, c.cidade, c.escolaridade, u.criado_em
            FROM candidatos c JOIN usuarios u ON u.id = c.usuario_id
            ORDER BY u.id DESC
        """).fetchall()
    finally:
        conexao.close()
    return _csv_response("candidatos-emprega-serra.csv",
                         ["Nome", "E-mail", "Telefone", "Cidade", "Escolaridade", "Cadastro"],
                         [tuple(row) for row in rows])
