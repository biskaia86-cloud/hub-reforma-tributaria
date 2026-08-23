"""Integração opcional com a pasta Reforma Tributária do Google Drive."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


OFFICIAL_DOMAINS = ("gov.br", "receita.fazenda.gov.br")
SYSTEM_PROMPT = """Você é um analista tributário brasileiro. Use primeiro o contexto da base fornecida.
Se precisar cruzar informações externas, consulte exclusivamente gov.br e receita.fazenda.gov.br.
Não use, cite ou recomende qualquer outro domínio. Separe fatos, premissas e estimativas.
Explique o resultado em linguagem simples e não dê parecer jurídico vinculante.
"""


@dataclass
class RetrievalResult:
    context: str
    source: str
    configured: bool


def retrieve_drive_context(query: str) -> RetrievalResult:
    """Busca documentos com GoogleDriveLoader quando as credenciais estão configuradas."""
    project_root = Path(__file__).resolve().parent
    credentials = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials.json.json")
    credentials_path = Path(credentials)
    if not credentials_path.is_absolute():
        credentials_path = project_root / credentials_path
    token_path = Path(os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "token.json"))
    if not token_path.is_absolute():
        token_path = project_root / token_path
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    folder_name = os.getenv("GOOGLE_DRIVE_FOLDER_NAME", "Reforma Tributária")
    if not credentials_path.exists():
        return RetrievalResult(
            context=f"Arquivo de credenciais não encontrado: {credentials_path.name}.",
            source="Base local / integração pendente",
            configured=False,
        )

    try:
        from langchain_community.document_loaders import GoogleDriveLoader
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
        if token_path.exists():
            from google.oauth2.credentials import Credentials

            credentials_object = Credentials.from_authorized_user_file(str(token_path), scopes)
        else:
            credentials_object = flow.run_local_server(port=0)
            token_path.write_text(credentials_object.to_json(), encoding="utf-8")

        if not folder_id:
            drive = build("drive", "v3", credentials=credentials_object)
            response = drive.files().list(
                q=(
                    "mimeType = 'application/vnd.google-apps.folder' "
                    f"and name = '{folder_name.replace(chr(39), chr(92) + chr(39))}' "
                    "and trashed = false"
                ),
                spaces="drive",
                fields="files(id, name)",
                pageSize=10,
            ).execute()
            folders = response.get("files", [])
            if not folders:
                return RetrievalResult(
                    context=f"Nenhuma pasta chamada '{folder_name}' foi encontrada no Google Drive.",
                    source="Google Drive",
                    configured=True,
                )
            folder_id = folders[0]["id"]

        loader = GoogleDriveLoader(
            folder_id=folder_id,
            recursive=True,
            credentials_path=str(credentials_path),
            token_path=str(token_path),
        )
        documents = loader.load()
        terms = {term.lower() for term in query.split() if len(term) > 3}
        ranked = sorted(
            documents,
            key=lambda document: sum(term in document.page_content.lower() for term in terms),
            reverse=True,
        )
        context = "\n\n".join(document.page_content[:5000] for document in ranked[:4])
        return RetrievalResult(context=context or "Nenhum documento relevante encontrado.", source="Google Drive", configured=True)
    except Exception as error:
        return RetrievalResult(
            context=f"Não foi possível carregar o Google Drive nesta execução: {error}",
            source="Google Drive indisponível",
            configured=True,
        )