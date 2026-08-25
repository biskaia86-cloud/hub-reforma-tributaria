"""Gera token OAuth compartilhado para Google Drive e Google Sheets."""

from __future__ import annotations

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]
ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS_PATH = ROOT / "credentials.json.json"
TOKEN_PATH = ROOT / "token.json"


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    credentials = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    client_config = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    client = client_config.get("installed") or client_config.get("web") or {}
    print("[google_sheets]")
    print(f'client_id = "{client.get("client_id", "")}"')
    print(f'client_secret = "{client.get("client_secret", "")}"')
    print(f'refresh_token = "{credentials.refresh_token or ""}"')
    print(f"Token salvo em: {TOKEN_PATH}")


if __name__ == "__main__":
    main()
