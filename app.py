"""Interface principal do Discovery da Reforma Tributária."""

from __future__ import annotations

import re

import streamlit as st
from dotenv import load_dotenv

from analysis import diagnose, format_brl
from database import initialize_database, save_lead
from pdf_report import build_pdf
from rag import SYSTEM_PROMPT, retrieve_drive_context


st.set_page_config(page_title="CENTRAL RT", page_icon="◈", layout="wide")
load_dotenv()
initialize_database()

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


def showcase() -> None:
    st.divider()
    st.markdown('<div class="showcase"><h2>🧭 Rota Simples</h2><p>Descubra agora o impacto real da Reforma Tributária no seu negócio. Responda a 4 perguntas e descubra se migrar para o Simples Híbrido é a estratégia mais lucrativa para a sua empresa.</p></div>', unsafe_allow_html=True)
    if st.button("Começar Diagnóstico Gratuito", type="primary", use_container_width=True):
        st.session_state.screen = "lead"
        st.rerun()


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
        answers = {"profile": profile, "activity": activity, "revenue": revenue, "b2b_percent": b2b_percent}
        st.session_state.answers = answers
        st.session_state.diagnosis = diagnose(**answers)
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
        st.caption("Modelo ilustrativo: aplica uma taxa efetiva atual de 6% como premissa e adiciona CBS de 9,43% no cenário híbrido. Não representa uma alíquota legal definitiva.")
        st.write("A leitura combina faturamento médio mensal, percentual de vendas para PJ e uma estimativa de relevância de créditos na cadeia.")
    st.subheader("Simulação mensal")
    current_tax = diagnosis["current_monthly_tax"]
    hybrid_tax = diagnosis["hybrid_monthly_tax"]
    calc_left, calc_right = st.columns(2)
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
    st.metric("Aumento simulado da carga", format_brl(diagnosis["tax_increase"]), f'{diagnosis["tax_increase_percent"]:.1f}%')
    st.caption(diagnosis["caveat"])
    pdf = build_pdf(st.session_state.lead, st.session_state.answers, diagnosis, diagnosis["normative_source"])
    st.download_button("Baixar Relatório Rota Simples (PDF)", pdf, "relatorio-rota-simples.pdf", "application/pdf", type="secondary")


if "screen" not in st.session_state:
    st.session_state.screen = "showcase"

show_header()
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