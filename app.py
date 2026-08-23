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
.stApp { background: linear-gradient(135deg, #f7faff 0%, #ffffff 47%, #eaf2ff 100%); }
.hero { padding: 2.7rem 0 1.4rem; border-bottom: 1px solid #cdd9e9; }
.brand { color: #07111f; font-family: 'Space Grotesk', sans-serif; font-size: 3.5rem; font-weight: 700; letter-spacing: -.05em; }
.eyebrow { color: #175cd3; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.result { padding: 1.25rem 1.4rem; border-left: 6px solid; background: rgba(255,255,255,.86); border-radius: 8px; box-shadow: 0 8px 28px rgba(15, 47, 92, .08); }
.source-note { color: #53657c; font-size: .78rem; border-left: 2px solid #8da9cf; padding-left: .7rem; }
.section-label { color: #175cd3; font-weight: 700; font-size: .82rem; letter-spacing: .08em; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


def show_header() -> None:
    st.markdown('<div class="hero"><div class="eyebrow">Hub de inteligência tributária</div><div class="brand">CENTRAL RT</div><h1>Decisões mais claras para a Reforma Tributária.</h1><p>Diagnóstico executivo para entender o impacto do Simples híbrido na sua operação.</p></div>', unsafe_allow_html=True)


def lead_gate() -> bool:
    st.subheader("Comece pelo seu cadastro")
    st.caption("Seus dados ficam armazenados localmente para liberar o diagnóstico.")
    with st.form("lead_form"):
        name = st.text_input("Nome *")
        phone = st.text_input("Telefone *", placeholder="(11) 99999-9999")
        email = st.text_input("E-mail corporativo *")
        company = st.text_input("Nome da empresa *")
        submitted = st.form_submit_button("Liberar Rota Simples", type="primary")
    if submitted:
        if not all(value.strip() for value in (name, phone, email, company)) or not valid_email(email):
            st.error("Preencha todos os campos com um e-mail válido.")
        else:
            st.session_state.lead = {"name": name, "phone": phone, "corporate_email": email, "company_name": company}
            st.session_state.lead_id = save_lead(name, phone, email, company)
            st.rerun()
    return "lead" in st.session_state


def diagnosis_form() -> None:
    st.subheader("Diagnóstico Rota Simples")
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
            if revenue < 0:
                raise ValueError
        except ValueError:
            st.error("Informe o faturamento no formato R$ 1.250.000,00.")
            return
        answers = {"profile": profile, "activity": activity, "revenue": revenue, "b2b_percent": b2b_percent}
        st.session_state.answers = answers
        st.session_state.diagnosis = diagnose(**answers)
        st.session_state.rag = retrieve_drive_context(f"{activity} Simples IBS CBS crédito PJ")
        st.rerun()


def show_result() -> None:
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
    st.subheader("Simulação mensal")
    st.caption("Modelo ilustrativo: aplica uma taxa efetiva atual de 6% como premissa e adiciona CBS de 9,43% no cenário híbrido. Não representa uma alíquota legal definitiva.")
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
    rag = st.session_state.rag
    with st.expander("Base consultada e premissas"):
        st.caption("A consulta utiliza a base normativa configurada e, quando necessário, somente fontes oficiais: gov.br e receita.fazenda.gov.br.")
        st.text(rag.context[:2500])
    pdf = build_pdf(st.session_state.lead, st.session_state.answers, diagnosis, diagnosis["normative_source"])
    st.download_button("Baixar Relatório Rota Simples (PDF)", pdf, "relatorio-rota-simples.pdf", "application/pdf", type="secondary")


show_header()
if "lead" not in st.session_state:
    lead_gate()
elif "diagnosis" not in st.session_state:
    diagnosis_form()
else:
    show_result()
    if st.button("Refazer diagnóstico"):
        st.session_state.pop("diagnosis")
        st.session_state.pop("answers")
        st.rerun()