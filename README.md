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

## Backup de cadastros (Google Sheets)

O SQLite local continua sendo a fonte primária, mas cada lead também pode ser copiado para uma planilha Google Sheets como camada de redundância enquanto a migração para um banco externo definitivo, como Postgres, não é feita.

1. Crie uma planilha com uma aba `Leads` e o cabeçalho `Nome, Telefone, E-mail, Empresa, Data`.
2. Copie o ID da planilha (o trecho entre `/d/` e `/edit` na URL) para `GOOGLE_SHEETS_SPREADSHEET_ID` e, se necessário, altere `GOOGLE_SHEETS_TAB_NAME`.
3. Localmente, execute uma vez `python scripts/gerar_token_sheets.py`. O token compartilhado inclui `drive.readonly` e `spreadsheets`.
4. Copie os valores impressos de `client_id`, `client_secret` e `refresh_token` para Settings > Secrets do app no Streamlit Community Cloud:

```toml
[google_sheets]
client_id = "..."
client_secret = "..."
refresh_token = "..."
```

Nunca commite esses valores no repositório. No Cloud, configure também `GOOGLE_SHEETS_SPREADSHEET_ID` e `GOOGLE_SHEETS_TAB_NAME` nos secrets/configuração do app. Se Sheets estiver fora do ar ou sem configuração, o aviso é registrado e o cadastro local continua normalmente. O token OAuth usado pelo Drive precisa ser regenerado com `scripts/gerar_token_sheets.py` para incluir o escopo de Sheets.

No desenvolvimento local, `.env.example` é apenas um modelo: copie-o para `.env` e preencha os valores antes de executar o app (`Copy-Item .env.example .env`). O código aceita tanto o ID puro quanto a URL completa da planilha.

## Consultar interesse no Enquadramento completo

Configure `ADMIN_EXPORT_TOKEN` e acesse o app com `?admin=1`; informe a senha na tela administrativa para consultar a lista e baixar `Exportar interesse (CSV)`. Os interesses também são enviados separadamente para a aba `Interesse_Enquadramento` da planilha de backup, sem misturá-los à aba geral `Leads`.

## Pagamentos (Rota Simples - Enquadramento completo)

Após o diagnóstico gratuito, o usuário pode comprar o desbloqueio mensal avulso por cartão ou Pix via Mercado Pago. Configure no `.env` as credenciais de teste ou produção (`MERCADOPAGO_ACCESS_TOKEN` e `MERCADOPAGO_PUBLIC_KEY`) e defina `APP_URL` com a URL pública do aplicativo; em ambiente local, o padrão é `http://localhost:8501`.

O app confirma o pagamento no retorno do navegador e libera a projeção 2025-2033 quando o status é aprovado. Para produção, recomenda-se evoluir para confirmação por Webhook Mercado Pago Webhooks v2 em endpoint dedicado, sem depender apenas do retorno do usuário.

A monetização do Enquadramento completo está temporariamente desativada (`ENQUADRAMENTO_COMPLETO_DISPONIVEL=false`); a tela mostra uma captação de interesse no lugar do checkout até a etapa de pagamento ser finalizada.

## Observações de negócio

O diagnóstico é uma triagem educativa baseada principalmente na proporção B2B. A projeção paga usa premissas de simulação para CBS/IBS, margem, CMV, despesas e crescimento; não calcula uma obrigação tributária definitiva nem substitui uma simulação do contador. Faltam, entre outros dados, CNAE, UF, município, monofasia e substituição tributária. A legislação da reforma deve ser conferida nas fontes oficiais vigentes antes de qualquer decisão.