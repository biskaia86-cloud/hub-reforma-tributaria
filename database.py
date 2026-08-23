"""Persistência local dos leads capturados pela aplicação."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("data") / "leads.sqlite3"


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
        return int(cursor.lastrowid)