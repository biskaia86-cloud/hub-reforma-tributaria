# CENTRAL RT

Aplicação Streamlit com gate de cadastro, diagnóstico inicial da Rota Simples, persistência SQLite, base de conhecimento opcional e exportação em PDF.

## Rodar no VS Code (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`. O banco será criado automaticamente em `data/leads.sqlite3`.

## Configurar o Google Drive

1. Ative a Google Drive API no projeto Google Cloud associado ao arquivo OAuth.
2. Confirme que a conta Google usada no primeiro login tem acesso à pasta `Reforma Tributária`.
3. Na primeira consulta, o navegador abrirá o consentimento OAuth; o token local será salvo em `token.json`.
4. O aplicativo localiza a pasta pelo nome. Para evitar ambiguidades, você pode definir `GOOGLE_DRIVE_FOLDER_ID` no `.env`.
5. Para usar outro arquivo, altere `GOOGLE_DRIVE_CREDENTIALS_PATH`.

O JSON OAuth e o token estão no `.gitignore`. Como o arquivo contém um `client_secret`, não o publique e considere revogar/rotacionar essa credencial caso tenha sido compartilhada fora do ambiente local. O contexto externo, quando usado, é controlado por `SYSTEM_PROMPT` em `rag.py`, aceitando somente `gov.br` e `receita.fazenda.gov.br`.

## Observações de negócio

O diagnóstico é uma triagem educativa baseada principalmente na proporção B2B. Não calcula alíquota efetiva nem substitui uma simulação do contador: faltam, entre outros dados, CNAE, margem, folha, UF, município, monofasia e substituição tributária. A legislação da reforma deve ser conferida nas fontes oficiais vigentes antes de qualquer decisão.