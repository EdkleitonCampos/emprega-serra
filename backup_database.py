"""Cria backup consistente do SQLite sem interromper o servidor."""
from datetime import datetime
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parent
DB = Path(__import__("os").environ.get("DATABASE_PATH", BASE / "emprega_serra.db"))
DESTINO = BASE / "backups"
DESTINO.mkdir(exist_ok=True)
if not DB.exists():
    raise SystemExit(f"Banco não encontrado: {DB}")

nome = f"emprega_serra_{datetime.now():%Y%m%d_%H%M%S}.db"
saida = DESTINO / nome
with sqlite3.connect(DB) as origem, sqlite3.connect(saida) as destino:
    origem.backup(destino)
    resultado = destino.execute("PRAGMA integrity_check").fetchone()[0]
    if resultado != "ok":
        saida.unlink(missing_ok=True)
        raise SystemExit(f"Falha na integridade do backup: {resultado}")

# Mantém os 30 backups mais recentes.
backups = sorted(DESTINO.glob("emprega_serra_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
for antigo in backups[30:]:
    antigo.unlink(missing_ok=True)
print(f"Backup concluído: {saida}")
