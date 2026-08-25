"""Persistência local dos leads capturados pela aplicação."""

from __future__ import annotations

import sqlite3
import logging
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("data") / "leads.sqlite3"
LOGGER = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                corporate_email TEXT NOT NULL,
                company_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        initialize_access_table(connection)
        initialize_interest_table(connection)


def initialize_access_table(connection: sqlite3.Connection | None = None) -> None:
    """Cria a tabela de acessos pagos, aceitando uma conexão para uso interno."""
    if connection is not None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS access_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                email TEXT NOT NULL,
                payment_id TEXT,
                payment_provider TEXT NOT NULL DEFAULT 'mercado_pago',
                status TEXT NOT NULL DEFAULT 'pending',
                amount_cents INTEGER,
                granted_at TEXT,
                valid_until TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
            """
        )
        return
    with _connect() as new_connection:
        initialize_access_table(new_connection)


def create_pending_access(email: str, payment_id: str, amount_cents: int, lead_id: int | None = None) -> None:
    initialize_access_table()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO access_grants (lead_id, email, payment_id, amount_cents) VALUES (?, ?, ?, ?)",
            (lead_id, email.strip().lower(), payment_id, amount_cents),
        )


def approve_access(payment_id: str, days_valid: int = 30) -> bool:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    valid_until = now + timedelta(days=days_valid)
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE access_grants SET status = 'approved', granted_at = ?, valid_until = ? WHERE payment_id = ?",
            (now.isoformat(), valid_until.isoformat(), str(payment_id)),
        )
        return cursor.rowcount > 0


def has_active_access(email: str) -> bool:
    from datetime import datetime, timezone

    with _connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM access_grants WHERE lower(email) = lower(?) AND status = 'approved' AND valid_until >= ? LIMIT 1",
            (email.strip(), datetime.now(timezone.utc).isoformat()),
        ).fetchone()
    return row is not None


def initialize_interest_table(connection: sqlite3.Connection | None = None) -> None:
    """Cria a tabela de interesses com unicidade por lead e funcionalidade."""
    if connection is None:
        with _connect() as new_connection:
            initialize_interest_table(new_connection)
        return
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_interest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            feature TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (lead_id, feature),
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
        """
    )


def register_interest(lead_id: int, feature: str = "enquadramento_completo") -> None:
    """Registra interesse uma única vez para cada lead e funcionalidade."""
    initialize_interest_table()
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO feature_interest (lead_id, feature) VALUES (?, ?)",
            (lead_id, feature),
        )


def list_interested_leads(feature: str = "enquadramento_completo") -> list[dict]:
    """Lista apenas leads que manifestaram interesse explícito nesta funcionalidade.

    Intencionalmente não equivale a todos os leads e não deve ser usada como
    proxy da base geral de cadastros do diagnóstico gratuito.
    """
    initialize_database()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT leads.name, leads.phone, leads.corporate_email,
                   leads.company_name, feature_interest.created_at AS clicked_at
            FROM feature_interest
            INNER JOIN leads ON leads.id = feature_interest.lead_id
            WHERE feature_interest.feature = ?
            ORDER BY feature_interest.created_at DESC
            """,
            (feature,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_lead(name: str, phone: str, corporate_email: str, company_name: str) -> int:
    initialize_database()
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (name, phone, corporate_email, company_name)
            VALUES (?, ?, ?, ?)
            """
            , (name.strip(), phone.strip(), corporate_email.strip(), company_name.strip()),
        )
        lead_id = int(cursor.lastrowid)

    try:
        from sheets_backup import append_lead_row

        backup_ok = append_lead_row(name, phone, corporate_email, company_name, datetime.utcnow().isoformat())
        if not backup_ok:
            LOGGER.warning("Lead %s salvo no SQLite, mas não foi enviado ao Google Sheets.", lead_id)
    except Exception:
        # O SQLite local é a fonte primária; Sheets nunca pode bloquear o cadastro.
        LOGGER.exception("Falha no backup do lead; cadastro local preservado.")
    return lead_id


def get_all_leads() -> list[sqlite3.Row]:
    """Retorna os leads locais para exportação manual de contingência."""
    initialize_database()
    with _connect() as connection:
        return connection.execute(
            "SELECT id, name, phone, corporate_email, company_name, created_at FROM leads ORDER BY id"
        ).fetchall()