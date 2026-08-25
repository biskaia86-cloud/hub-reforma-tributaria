"""Backup opcional de leads em uma planilha Google Sheets."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from streamlit.errors import StreamlitSecretNotFoundError

LOGGER = logging.getLogger(__name__)
load_dotenv()
SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
SCOPES = [DRIVE_SCOPE, SHEETS_SCOPE]


def _secret_or_env(name: str, default: str = "", secret_key: str | None = None) -> str:
    value = None
    try:
        section = st.secrets["google_sheets"]
        value = section.get(secret_key or name)
        if not value:
            value = st.secrets.get(name)
    except (KeyError, FileNotFoundError, StreamlitSecretNotFoundError):
        LOGGER.debug("Google Sheets secret %s não encontrado; tentando ambiente local.", name)
    return str(value or os.getenv(name, default)).strip()


def _spreadsheet_id() -> str:
    """Aceita o ID puro e também tolera uma URL copiada do navegador."""
    configured = _secret_or_env("GOOGLE_SHEETS_SPREADSHEET_ID", secret_key="spreadsheet_id")
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", configured)
    return match.group(1) if match else configured


def get_sheets_credentials() -> Credentials | None:
    """Obtém credenciais sem fluxo interativo, usando Secrets ou token.json local."""
    client_id = _secret_or_env("GOOGLE_SHEETS_CLIENT_ID", secret_key="client_id")
    client_secret = _secret_or_env("GOOGLE_SHEETS_CLIENT_SECRET", secret_key="client_secret")
    refresh_token = _secret_or_env("GOOGLE_SHEETS_REFRESH_TOKEN", secret_key="refresh_token")
    if client_id and client_secret and refresh_token:
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
    else:
        token_path = Path(os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "token.json"))
        if not token_path.is_absolute():
            token_path = Path(__file__).resolve().parent / token_path
        if not token_path.exists():
            LOGGER.warning("Token local não encontrado: %s", token_path)
            return None
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if credentials.expired and credentials.refresh_token:
        LOGGER.info("Token Google expirado; renovando com refresh token.")
        credentials.refresh(Request())
    return credentials


def append_lead_row(name: str, phone: str, email: str, company: str, created_at: str) -> bool:
    """Adiciona um lead à aba configurada, sem propagar falhas ao aplicativo."""
    spreadsheet_id = _spreadsheet_id()
    tab_name = _secret_or_env("GOOGLE_SHEETS_TAB_NAME", "Leads", secret_key="tab_name") or "Leads"
    if not spreadsheet_id:
        LOGGER.warning("Backup Google Sheets ignorado: GOOGLE_SHEETS_SPREADSHEET_ID não configurado.")
        return False
    try:
        credentials = get_sheets_credentials()
        if credentials is None:
            LOGGER.warning("Backup Google Sheets ignorado: credenciais não configuradas.")
            return False
        build("sheets", "v4", credentials=credentials).spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A:E",
            valueInputOption="USER_ENTERED",
            body={"values": [[name, phone, email, company, created_at]]},
        ).execute()
        return True
    except Exception:
        LOGGER.exception("Falha no backup do lead para Google Sheets; cadastro local preservado.")
        return False


def append_interest_row(name: str, phone: str, email: str, company: str, clicked_at: str) -> bool:
    """Adiciona interesse na aba separada, sem propagar falhas ao aplicativo."""
    spreadsheet_id = _spreadsheet_id()
    tab_name = _secret_or_env(
        "GOOGLE_SHEETS_INTEREST_TAB_NAME",
        "Interesse_Enquadramento",
        secret_key="interest_tab_name",
    ) or "Interesse_Enquadramento"
    if not spreadsheet_id:
        LOGGER.warning("Backup de interesse ignorado: GOOGLE_SHEETS_SPREADSHEET_ID não configurado.")
        return False
    try:
        credentials = get_sheets_credentials()
        if credentials is None:
            LOGGER.warning("Backup de interesse ignorado: credenciais não configuradas.")
            return False
        build("sheets", "v4", credentials=credentials).spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A:E",
            valueInputOption="USER_ENTERED",
            body={"values": [[name, phone, email, company, clicked_at]]},
        ).execute()
        return True
    except Exception:
        LOGGER.exception("Falha no backup do interesse para Google Sheets; registro local preservado.")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = append_lead_row(
        "Teste Local",
        "11999999999",
        "teste@teste.com",
        "Empresa Teste",
        "2026-01-01T00:00:00",
    )
    print("Sucesso" if result else "Falhou - veja o erro acima")
