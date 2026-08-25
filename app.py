"""Interface principal do Discovery da Reforma Tributária."""

from __future__ import annotations

import os
import re
import csv
import hmac
from datetime import datetime, timezone
from io import StringIO

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
ENQUADRAMENTO_COMPLETO_DISPONIVEL = os.getenv("ENQUADRAMENTO_COMPLETO_DISPONIVEL", "false").lower() == "true"

from analysis import diagnose, format_brl, project_hybrid_vs_real
from database import get_all_leads, has_active_access, initialize_database, list_interested_leads, register_interest, save_lead
from pdf_report import build_pdf
import payments
from rag import SYSTEM_PROMPT, retrieve_drive_context


st.set_page_config(page_title="CENTRAL RT", page_icon="◈", layout="wide")
initialize_database()

if "access_unlocked" not in st.session_state:
    st.session_state.access_unlocked = False
payment_id = st.query_params.get("payment_id")
if ENQUADRAMENTO_COMPLETO_DISPONIVEL and payment_id and not st.session_state.get("payment_checked"):
    st.session_state.payment_checked = True
    try:
        payment_status = payments.confirm_payment(payment_id)
        st.session_state.payment_message = "approved" if payment_status == "approved" else "pending" if payment_status in {"pending", "in_process"} else "failed"
        if payment_status == "approved":
            st.session_state.access_unlocked = True
    except Exception:
        st.session_state.payment_message = "error"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: #07111f; }
.stApp { background: radial-gradient(circle at 90% 5%, rgba(23,92,211,.13), transparent 32rem), linear-gradient(135deg, #f7faff 0%, #ffffff 47%, #eaf2ff 100%); }
/* Esconder o cabeçalho inteiro */
[data-testid="stHeader"] { display: none !important; }
/* Esconder a barra de ferramentas (Menu e ícone do GitHub) */
[data-testid="stToolbar"] { display: none !important; }
/* Esconder o rodapé (Made with Streamlit) */
[data-testid="stFooter"] { display: none !important; }
/* Esconder o botão de Deploy */
.stDeployButton { display: none !important; }
.hero { padding: 2.7rem 1.2rem 2.4rem; margin: 1rem 0 2rem; border: 1px solid #cdd9e9; border-radius: 18px; background: linear-gradient(115deg, #07111f 0%, #123866 62%, #175cd3 100%); box-shadow: 0 18px 42px rgba(15, 47, 92, .16); text-align: center; overflow: hidden; }
.brand { color: #ffffff; font-family: 'Space Grotesk', sans-serif; font-size: clamp(.85rem, 4vw, 2.5rem); font-weight: 700; letter-spacing: -.06em; line-height: 1.1; white-space: nowrap; }
.hero h2 { color: #8bd3ff; font-family: 'Space Grotesk', sans-serif; font-size: clamp(1.25rem, 2.6vw, 2rem); margin: 1rem 0 .45rem; }
.hero p { color: #dbeafe; font-size: 1.05rem; max-width: 760px; margin: 0; }
.result { padding: 1.25rem 1.4rem; border-left: 6px solid; background: rgba(255,255,255,.9); border-radius: 8px; box-shadow: 0 8px 28px rgba(15, 47, 92, .08); }
.source-note { color: #53657c; font-size: .78rem; border-left: 2px solid #8da9cf; padding-left: .7rem; }
.section-label { color: #175cd3; font-weight: 700; font-size: .82rem; letter-spacing: .08em; text-transform: uppercase; }
div.stButton > button, div.stFormSubmitButton > button { border: 0; border-radius: 999px; background: #175cd3; color: #ffffff; font-weight: 700; min-height: 2.8rem; padding: 0 1.4rem; box-shadow: 0 8px 18px rgba(23,92,211,.22); transition: transform .18s ease, background .18s ease, box-shadow .18s ease; }
div.stButton > button:hover, div.stFormSubmitButton > button:hover { background: #0f4bb8; color: #ffffff; transform: translateY(-2px); box-shadow: 0 12px 24px rgba(23,92,211,.3); }
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea { border-radius: 10px; border-color: #cdd9e9; background: #f7faff; }
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: #175cd3; box-shadow: 0 0 0 1px #175cd3; }
div[data-testid="stMetric"] { padding: 1rem; border: 1px solid #d8e3f0; border-radius: 12px; background: rgba(255,255,255,.72); }
.showcase { padding: 2rem 2.2rem; border: 1px solid #cdd9e9; border-radius: 16px; background: rgba(255,255,255,.88); box-shadow: 0 14px 32px rgba(15,47,92,.10); }
.showcase h2 { color: #07111f; margin: 0 0 .7rem; }
.showcase p { color: #53657c; font-size: 1.05rem; line-height: 1.65; }
@media (max-width: 640px) { .hero { padding: 2rem 1.4rem; } }
</style>
""", unsafe_allow_html=True)


def valid_email(value: str) -> bool:
    pattern = r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.(?:com\.br|net\.br|org\.br|gov\.br|edu\.br|com|org|net|edu|gov|io|ai|app|dev|co\.uk|de|fr|es|it|pt|us)"
    return bool(re.fullmatch(pattern, value.strip()))


def valid_phone(value: str) -> bool:
    phone = value.strip()
    if re.fullmatch(r"\d{10,11}", phone):
        return True
    if not re.fullmatch(r"(?:\(\d{2}\)\s?)?\d{4,5}-?\d{4}", phone):
        return False
    return len(re.sub(r"\D", "", phone)) in (10, 11)


def validate_lead(name: str, phone: str, email: str, company: str) -> str | None:
    if not name.strip():
        return "Por favor, informe seu nome."
    if not company.strip():
        return "Por favor, informe o nome da empresa."
    if not valid_email(email):
        return "Por favor, insira um e-mail válido."
    if not valid_phone(phone):
        return "O telefone deve conter o DDD e o número correto."
    return None


def show_header() -> None:
    st.markdown('<div class="hero"><div class="brand">CENTRAL DA REFORMA TRIBUTARIA</div><h2>Entenda o próximo movimento do Simples Nacional.</h2><p>Um diagnóstico executivo para antecipar impactos, créditos e decisões na transição para o modelo híbrido.</p></div>', unsafe_allow_html=True)


def _csv_download(rows: list[dict], keys: list[str], headers: list[str], filename: str, label: str) -> None:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows([[row.get(key, "") for key in keys] for row in rows])
    st.download_button(label, output.getvalue().encode("utf-8-sig"), filename, "text/csv")


def admin_export() -> None:
    """Exibe a tela administrativa protegida por parâmetro e token configurado."""
    if st.query_params.get("admin") != "1":
        return
    st.subheader("Área administrativa")
    expected_token = os.getenv("ADMIN_EXPORT_TOKEN", "").strip()
    provided_token = st.text_input("Senha administrativa", type="password")
    if not expected_token or not hmac.compare_digest(provided_token, expected_token):
        st.info("Informe o token administrativo configurado para consultar os dados.")
        return

    leads = [dict(row) for row in get_all_leads()]
    _csv_download(leads, ["id", "name", "phone", "corporate_email", "company_name", "created_at"], ["ID", "Nome", "Telefone", "E-mail", "Empresa", "Data"], "leads-locais.csv", "Exportar leads locais (CSV)")
    interested = list_interested_leads()
    st.metric("Pessoas interessadas", f"{len(interested)} pessoas pediram para ser avisadas sobre o Enquadramento completo")
    st.dataframe(interested, hide_index=True, use_container_width=True)
    _csv_download(interested, ["name", "phone", "corporate_email", "company_name", "clicked_at"], ["Nome", "Telefone", "E-mail", "Empresa", "Data do clique"], "interesse-enquadramento.csv", "Exportar interesse (CSV)")


def showcase() -> None:
    st.divider()
    st.markdown('<div class="showcase"><h2>🧭 Rota Simples</h2><p>Descubra agora o impacto real da Reforma Tributária no seu negócio. Responda a 4 perguntas e descubra se migrar para o Simples Híbrido é a estratégia mais lucrativa para a sua empresa.</p></div>', unsafe_allow_html=True)
    if st.button("Começar Diagnóstico Gratuito", type="primary", use_container_width=True):
        st.session_state.screen = "lead"
        st.rerun()


def has_paid_access() -> bool:
    lead = st.session_state.get("lead")
    return bool(st.session_state.get("access_unlocked") or (lead and has_active_access(lead["corporate_email"])))


def parse_brl(value: str, default: float = 0.0) -> float:
    if not value.strip():
        return default
    return float(value.strip().replace("R$", "").replace(".", "").replace(",", ".").strip())


def lead_gate() -> bool:
    st.divider()
    st.subheader("Comece pelo seu cadastro")
    with st.form("lead_form"):
        first_row_left, first_row_right = st.columns(2)
        name = first_row_left.text_input("Nome *")
        email = first_row_right.text_input("E-mail corporativo *")
        second_row_left, second_row_right = st.columns(2)
        phone = second_row_left.text_input("Telefone *", placeholder="(11) 99999-9999")
        company = second_row_right.text_input("Nome da empresa *")
        submitted = st.form_submit_button("Liberar Rota Simples", type="primary")
    if submitted:
        validation_error = validate_lead(name, phone, email, company)
        if validation_error:
            st.error(validation_error)
        else:
            st.session_state.lead = {"name": name, "phone": phone, "corporate_email": email, "company_name": company}
            st.session_state.lead_id = save_lead(name, phone, email, company)
            st.session_state.show_access_toast = True
            st.session_state.screen = "diagnosis"
            st.rerun()
    return "lead" in st.session_state


def diagnosis_form() -> None:
    st.divider()
    st.subheader("Diagnóstico Rota Simples")
    if st.session_state.pop("show_access_toast", False):
        st.toast("Acesso liberado!")
    with st.form("diagnosis_form"):
        profile = st.selectbox("Você vende para", ["Pessoa Física (PF)", "Pessoa Jurídica (PJ)", "Ambas"])
        activity = st.selectbox("Ramo de atividade", ["Comércio", "Indústria", "Escritório de Contabilidade", "Saúde", "Tecnologia e Software", "Engenharia", "Consultoria e Auditoria", "Publicidade e Marketing", "Serviços em Geral"])
        revenue_text = st.text_input("Faturamento nos últimos 12 meses", value="R$ 0,00", help="Digite no padrão brasileiro, por exemplo: R$ 1.250.000,00")
        b2b_percent = st.slider("Percentual de vendas para PJ", 0, 100, 50, format="%d%%")
        fator_r_informado = st.radio(
            "Sua folha de pagamento (com encargos) passa de aproximadamente 28% do seu faturamento?",
            ["Sim", "Não", "Não sei"],
            horizontal=True,
        )
        aliquota_manual_text = st.text_input(
            "Se você já sabe sua alíquota efetiva atual (informada pelo seu contador), digite aqui (%)",
            value="",
            help="Opcional. Exemplo: 6,50",
        )
        with st.expander("Projeção avançada (Enquadramento completo)"):
            cmv_text = st.text_input("CMV anual", value="R$ 0,00")
            expenses_text = st.text_input("Despesas operacionais anuais", value="R$ 0,00")
            payroll_text = st.text_input("Folha de pagamento anual", value="R$ 0,00")
            profit_margin = st.number_input("Margem de lucro estimada", min_value=0.0, max_value=1.0, value=0.15, step=0.01, format="%.2f", help="Informe 0,15 para 15%.")
            annual_growth = st.number_input("Crescimento anual estimado", min_value=-1.0, max_value=5.0, value=0.05, step=0.01, format="%.2f", help="Informe 0,05 para 5%.")
        submitted = st.form_submit_button("Gerar meu diagnóstico", type="primary")
    if submitted:
        try:
            normalized_revenue = revenue_text.strip().replace("R$", "").replace(".", "").replace(",", ".").strip()
            revenue = float(normalized_revenue)
            if revenue <= 0:
                st.warning("O faturamento informado deve ser maior que zero para prosseguirmos com a análise.")
                return
        except ValueError:
            st.error("Informe o faturamento no formato R$ 1.250.000,00.")
            return
        fator_r = {"Sim": 0.30, "Não": 0.20, "Não sei": None}[fator_r_informado]
        try:
            aliquota_manual = parse_brl(aliquota_manual_text) / 100 if aliquota_manual_text.strip() else None
            if aliquota_manual is not None and not 0 <= aliquota_manual <= 1:
                raise ValueError
        except ValueError:
            st.error("Informe a alíquota manual como percentual, por exemplo: 6,50.")
            return
        try:
            advanced = {"cmv": parse_brl(cmv_text), "despesas_operacionais": parse_brl(expenses_text), "folha_pagamento": parse_brl(payroll_text), "margem_lucro_estimada": profit_margin, "crescimento_anual_estimado": annual_growth}
        except ValueError:
            st.error("Informe os valores avançados no formato R$ 1.250,00.")
            return
        answers = {"profile": profile, "activity": activity, "revenue": revenue, "b2b_percent": b2b_percent, **advanced}
        st.session_state.answers = answers
        st.session_state.diagnosis = diagnose(
            profile=profile,
            activity=activity,
            revenue=revenue,
            b2b_percent=b2b_percent,
            fator_r=fator_r,
            fator_r_informado=fator_r_informado,
            aliquota_manual=aliquota_manual,
        )
        st.session_state.rag = retrieve_drive_context(f"{activity} Simples IBS CBS crédito PJ")
        st.rerun()


def show_result() -> None:
    st.divider()
    diagnosis = st.session_state.diagnosis
    st.markdown(f'<div class="result" style="border-color:{diagnosis["color"]}"><h2>{diagnosis["recommendation"]}</h2><p>{diagnosis["summary"]}</p></div>', unsafe_allow_html=True)
    first, second, third = st.columns(3)
    first.metric("Vendas para PJ", f'{diagnosis["b2b_percent"]}%')
    second.metric("Relevância do crédito", f'{diagnosis["estimated_credit_relevance"]}%')
    third.metric("Faturamento médio mensal", format_brl(diagnosis["monthly_revenue"]))
    st.progress(diagnosis["estimated_credit_relevance"] / 100, text="Sinal de potencial de crédito na cadeia")
    st.markdown(f'<p class="source-note"><strong>Base normativa:</strong> {diagnosis["normative_source"]}. A alíquota definitiva ainda não foi definida pelo Governo.</p>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Leitura executiva</div>', unsafe_allow_html=True)
    st.write(diagnosis["authority_summary"])
    with st.expander("Entenda o cálculo"):
        st.caption("A carga atual usa a fórmula progressiva do Simples Nacional. O cenário híbrido adiciona CBS de 9,43% como premissa ilustrativa, não como alíquota legal definitiva.")
        st.write("A leitura combina faturamento médio mensal, percentual de vendas para PJ e uma estimativa de relevância de créditos na cadeia.")
    precision = "alta (alíquota informada por você)" if diagnosis["aliquota_informada_manualmente"] else "estimada"
    st.info(f'Precisão: {precision}')
    fator_texto = "com Fator R acima de 28%" if diagnosis["fator_r_informado"] == "Sim" else "com Fator R abaixo de 28%" if diagnosis["fator_r_informado"] == "Não" else "com Fator R não informado (premissa conservadora)"
    aliquota_texto = "alíquota informada por você" if diagnosis["aliquota_informada_manualmente"] else "alíquota estimada pela faixa"
    st.caption(f'Cálculo baseado no {diagnosis["anexo_utilizado"]} do Simples Nacional, faixa de {diagnosis["faixa_rbt12"]}, {fator_texto}, usando {aliquota_texto}.')
    if diagnosis["rbt12_acima_limite_simples"]:
        st.warning("Seu RBT12 está acima de R$ 4,8 milhões. A última faixa foi usada apenas como aproximação; confirme o regime tributário com seu contador.")
    st.subheader("Simulação mensal")
    current_tax = diagnosis["current_monthly_tax"]
    hybrid_tax = diagnosis["hybrid_monthly_tax"]
    calc_left, calc_right = st.columns(2)
    calc_left.caption("HOJE (baseado no seu faturamento)")
    calc_right.caption("CENÁRIO SIMULADO (não é uma cobrança)")
    calc_left.metric("Cenário atual", format_brl(current_tax), f'{diagnosis["current_effective_rate"] * 100:.2f}% do faturamento médio')
    calc_right.metric("Cenário híbrido simulado", format_brl(hybrid_tax), f'+{format_brl(diagnosis["tax_increase"])}', delta_color="inverse")
    st.dataframe({
        "Componente": ["Faturamento médio mensal", "Carga atual estimada", "CBS no híbrido", "Total híbrido simulado"],
        "Atual": [format_brl(diagnosis["monthly_revenue"]), format_brl(current_tax), "-", format_brl(current_tax)],
        "Híbrido": [format_brl(diagnosis["monthly_revenue"]), format_brl(current_tax), format_brl(diagnosis["hybrid_cbs"]), format_brl(hybrid_tax)],
    }, hide_index=True, use_container_width=True)
    st.subheader("Dashboard de impacto")
    chart_data = {"Cenário atual": current_tax, "Cenário híbrido": hybrid_tax}
    st.bar_chart(chart_data, horizontal=True, color="#175cd3")
    st.metric("Diferença estimada entre os cenários (simulação)", format_brl(diagnosis["tax_increase"]), f'{diagnosis["tax_increase_percent"]:.1f}%')
    st.warning("Este valor compara dois cenários possíveis e não representa uma cobrança automática. A alíquota do CBS ainda não foi definida em caráter definitivo, a reforma está em transição gradual até 2033, e migrar para o híbrido depende de uma opção/enquadramento — não acontece sozinho.")
    with st.expander("Por que este número pode não se confirmar"):
        st.write("A reforma é gradual, e os efeitos plenos só valem a partir de 2033.")
        st.write("A empresa não é automaticamente migrada para o híbrido; isso depende de opção ou enquadramento.")
        st.write("O valor simulado não desconta eventual crédito de CBS/IBS sobre compras e insumos, que na prática reduziria a diferença.")
    st.caption(diagnosis["caveat"])
    projection = None
    if not ENQUADRAMENTO_COMPLETO_DISPONIVEL:
        st.markdown('<div class="showcase"><h2>Rota Simples - Enquadramento completo</h2><p>Em breve: descubra até quando vale ficar no Híbrido e a partir de que ano migrar para o Lucro Real passa a compensar. Estamos com essa funcionalidade em construção.</p></div>', unsafe_allow_html=True)
        lead_email = st.session_state.lead["corporate_email"]
        st.text_input("E-mail para ser avisado", value=lead_email, disabled=True)
        if st.button("Quero ser avisado"):
            clicked_at = datetime.now(timezone.utc).isoformat()
            register_interest(st.session_state.lead_id)
            try:
                from sheets_backup import append_interest_row

                lead = st.session_state.lead
                append_interest_row(
                    lead["name"], lead["phone"], lead["corporate_email"],
                    lead["company_name"], clicked_at,
                )
            except Exception:
                pass
            st.success("Você será avisado assim que estiver disponível!")
    elif has_paid_access():
        answers = st.session_state.answers
        projection = project_hybrid_vs_real(answers["revenue"], answers["cmv"], answers["despesas_operacionais"], answers["folha_pagamento"], answers["margem_lucro_estimada"], answers["crescimento_anual_estimado"])
        st.subheader("Rota Simples - Enquadramento completo")
        st.dataframe(projection["anos"], hide_index=True, use_container_width=True)
        st.line_chart({"Híbrido": [row["carga_hibrido"] for row in projection["anos"]], "Lucro Real": [row["carga_real"] for row in projection["anos"]]})
        if projection["crossover_year"]:
            st.success(f'Ano de virada estimado: {projection["crossover_year"]}. Economia acumulada estimada: {format_brl(projection["economia_acumulada_periodo"])}.')
        else:
            st.info("Não há ponto de virada estimado no período simulado.")
    else:
        st.markdown('<div class="showcase"><h2>Rota Simples - Enquadramento completo</h2><p>Desbloqueie a projeção de 2025 a 2033, o ponto de virada para o Lucro Real e a economia estimada para o seu negócio.</p></div>', unsafe_allow_html=True)
        st.write(f"Acesso mensal: **{format_brl(payments.PRODUCT_PRICE)}**")
        if st.button("Desbloquear agora (cartão ou Pix)", type="primary"):
            try:
                checkout = payments.create_checkout_preference(st.session_state.lead["corporate_email"], st.session_state.lead_id)
                st.session_state.checkout_url = checkout["checkout_url"]
            except Exception as error:
                st.error(f"Não foi possível iniciar o pagamento agora. Tente novamente. ({error})")
        if st.session_state.get("checkout_url"):
            st.link_button("Ir para o checkout Mercado Pago", st.session_state.checkout_url, use_container_width=True)
    payment_message = st.session_state.pop("payment_message", None)
    if payment_message == "approved":
        st.success("Pagamento aprovado! Seu Enquadramento completo já está liberado.")
    elif payment_message == "pending":
        st.info("Pagamento pendente. Atualize esta página após a aprovação para liberar o enquadramento completo.")
    elif payment_message in {"failed", "error"}:
        st.warning("Não foi possível confirmar o pagamento. Tente novamente ou verifique o status no Mercado Pago.")
    pdf = build_pdf(st.session_state.lead, st.session_state.answers, diagnosis, diagnosis["normative_source"], projection)
    st.download_button("Baixar Relatório Rota Simples (PDF)", pdf, "relatorio-rota-simples.pdf", "application/pdf", type="secondary")


if "screen" not in st.session_state:
    st.session_state.screen = "showcase"

show_header()
admin_export()
if st.session_state.screen == "showcase":
    showcase()
elif st.session_state.screen == "lead":
    lead_gate()
elif "diagnosis" not in st.session_state:
    diagnosis_form()
else:
    show_result()
    if st.button("Refazer diagnóstico"):
        st.session_state.pop("diagnosis")
        st.session_state.pop("answers")
        st.session_state.screen = "diagnosis"
        st.rerun()