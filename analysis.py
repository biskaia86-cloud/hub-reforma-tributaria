"""Diagnóstico inicial da escolha entre Simples atual e cenário híbrido."""

from __future__ import annotations

import os

CBS_RATE = 0.0943
CURRENT_EFFECTIVE_RATE = 0.06
ENQUADRAMENTO_COMPLETO_DISPONIVEL = os.getenv("ENQUADRAMENTO_COMPLETO_DISPONIVEL", "false").lower() == "true"
IRPJ_RATE = 0.15
IRPJ_ADDITIONAL_RATE = 0.10
CSLL_RATE = 0.09

ANEXO_I = [
    (180_000.00, 0.04, 0.00), (360_000.00, 0.073, 5_940.00),
    (720_000.00, 0.095, 13_860.00), (1_800_000.00, 0.107, 22_500.00),
    (3_600_000.00, 0.143, 87_300.00), (4_800_000.00, 0.19, 378_000.00),
]
ANEXO_II = [
    (180_000.00, 0.045, 0.00), (360_000.00, 0.078, 5_940.00),
    (720_000.00, 0.10, 13_860.00), (1_800_000.00, 0.112, 22_500.00),
    (3_600_000.00, 0.147, 85_500.00), (4_800_000.00, 0.30, 720_000.00),
]
ANEXO_III = [
    (180_000.00, 0.06, 0.00), (360_000.00, 0.112, 9_360.00),
    (720_000.00, 0.135, 17_640.00), (1_800_000.00, 0.16, 35_640.00),
    (3_600_000.00, 0.21, 125_640.00), (4_800_000.00, 0.33, 648_000.00),
]
ANEXO_V = [
    (180_000.00, 0.155, 0.00), (360_000.00, 0.18, 4_500.00),
    (720_000.00, 0.195, 9_900.00), (1_800_000.00, 0.205, 17_100.00),
    (3_600_000.00, 0.23, 62_100.00), (4_800_000.00, 0.305, 540_000.00),
]

ANEXO_POR_ATIVIDADE = {"Comércio": ANEXO_I, "Indústria": ANEXO_II}
ATIVIDADES_SUJEITAS_FATOR_R = {
    "Escritório de Contabilidade", "Saúde", "Tecnologia e Software",
    "Engenharia", "Consultoria e Auditoria", "Publicidade e Marketing",
    "Serviços em Geral",
}
_ANEXO_NOMES = {id(ANEXO_I): "Anexo I", id(ANEXO_II): "Anexo II", id(ANEXO_III): "Anexo III", id(ANEXO_V): "Anexo V"}

# Alíquotas ilustrativas para simulação; não são valores definitivos.
ALIQUOTAS_POR_ANO = {
    2025: 0.009,
    2026: 0.009,
    2027: 0.095,
    2028: 0.095,
    2029: 0.105,
    2030: 0.115,
    2031: 0.125,
    2032: 0.135,
    2033: 0.145,
}


def format_brl(value: float) -> str:
    """Formata valores numéricos no padrão monetário brasileiro."""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def effective_simples_rate(rbt12: float, faixas: list[tuple[float, float, float]]) -> float:
    """Aplica a fórmula da LC 123/2006, art. 18, sobre o RBT12 informado."""
    if rbt12 <= 0:
        return 0.0
    faixa = next((item for item in faixas if rbt12 <= item[0]), faixas[-1])
    limite, aliquota_nominal, parcela_a_deduzir = faixa
    del limite
    return max((rbt12 * aliquota_nominal - parcela_a_deduzir) / rbt12, 0.0)


def resolve_anexo(activity: str, fator_r: float | None) -> list[tuple[float, float, float]]:
    """Resolve o anexo do Simples pela atividade e pelo Fator R aproximado."""
    if activity in ANEXO_POR_ATIVIDADE:
        return ANEXO_POR_ATIVIDADE[activity]
    if activity in ATIVIDADES_SUJEITAS_FATOR_R:
        return ANEXO_III if fator_r is not None and fator_r >= 0.28 else ANEXO_V
    return ANEXO_V


def _faixa_texto(rbt12: float, faixas: list[tuple[float, float, float]]) -> str:
    faixa_index = next((index for index, item in enumerate(faixas) if rbt12 <= item[0]), len(faixas) - 1)
    lower = 0.0 if faixa_index == 0 else faixas[faixa_index - 1][0]
    upper = faixas[faixa_index][0]
    if faixa_index == 0:
        return f"até {format_brl(upper)}"
    return f"{format_brl(lower + 0.01)} a {format_brl(upper)}"


def project_hybrid_vs_real(
    revenue: float,
    cmv: float,
    despesas_operacionais: float,
    folha_pagamento: float,
    margem_lucro_estimada: float,
    crescimento_anual_estimado: float,
    anos=range(2025, 2034),
) -> dict:
    """Compara cargas anuais em uma simulação simplificada e testável."""
    rows = []
    hybrid_total = 0.0
    real_total = 0.0
    current_revenue = revenue
    for year in anos:
        credit_base = max(cmv + despesas_operacionais, 0.0)
        hybrid = max(current_revenue * ALIQUOTAS_POR_ANO.get(year, CBS_RATE) - credit_base * ALIQUOTAS_POR_ANO.get(year, CBS_RATE), 0.0)
        estimated_profit = max(current_revenue * margem_lucro_estimada - folha_pagamento, 0.0)
        irpj = estimated_profit * IRPJ_RATE
        additional_irpj = max(estimated_profit - 20_000 * 12, 0.0) * IRPJ_ADDITIONAL_RATE
        csll = estimated_profit * CSLL_RATE
        real = irpj + additional_irpj + csll
        difference = hybrid - real
        rows.append({
            "ano": year,
            "carga_hibrido": hybrid,
            "carga_real": real,
            "diferenca": difference,
            "regime_mais_vantajoso": "Híbrido" if difference <= 0 else "Lucro Real",
        })
        hybrid_total += hybrid
        real_total += real
        current_revenue *= 1 + crescimento_anual_estimado

    crossover_year = next((row["ano"] for row in rows if row["carga_real"] < row["carga_hibrido"]), None)
    return {
        "anos": rows,
        "crossover_year": crossover_year,
        "economia_acumulada_periodo": hybrid_total - real_total,
    }

def diagnose(
    profile: str,
    activity: str,
    revenue: float,
    b2b_percent: int,
    fator_r: float | None = None,
    fator_r_informado: str = "Não sei",
    aliquota_manual: float | None = None,
) -> dict:
    """Produz uma triagem executiva, sem substituir simulação tributária formal."""
    high_b2b = b2b_percent >= 50
    very_high_b2b = b2b_percent >= 70
    if very_high_b2b:
        recommendation = "O cenário híbrido merece prioridade"
        status = "favorável"
        color = "#16794b"
        summary = "A maior parte das suas vendas vai para empresas, que tendem a valorizar o crédito de IBS/CBS."
    elif high_b2b:
        recommendation = "Compare os dois cenários com seu contador"
        status = "atenção"
        color = "#b56b00"
        summary = "Existe potencial no híbrido, mas preço, margem e perfil dos seus clientes podem mudar o resultado."
    else:
        recommendation = "O Simples atual tende a ser mais simples"
        status = "conservador"
        color = "#a33b3b"
        summary = "Como poucas vendas são para empresas, o benefício de gerar crédito pode ser menor."

    estimated_credit_relevance = min(b2b_percent + (15 if activity in {"Indústria", "Comércio"} else 0), 100)
    anexo = resolve_anexo(activity, fator_r)
    anexo_nome = _ANEXO_NOMES.get(id(anexo), "Anexo V")
    calculated_rate = effective_simples_rate(revenue, anexo)
    aliquota_informada_manualmente = aliquota_manual is not None
    current_effective_rate = aliquota_manual if aliquota_informada_manualmente else calculated_rate
    monthly_revenue = revenue / 12
    current_monthly_tax = monthly_revenue * current_effective_rate
    hybrid_cbs = monthly_revenue * CBS_RATE
    hybrid_monthly_tax = current_monthly_tax + hybrid_cbs
    tax_increase = hybrid_monthly_tax - current_monthly_tax
    tax_increase_percent = (tax_increase / current_monthly_tax * 100) if current_monthly_tax else 0
    authority_summary = (
        f"Com {b2b_percent}% das vendas destinadas a PJ, o crédito pode influenciar a negociação comercial. "
        f"Na simulação, a CBS destacada seria de {format_brl(hybrid_cbs)} por mês sobre o faturamento médio."
    )
    return {
        "recommendation": recommendation,
        "status": status,
        "color": color,
        "summary": summary,
        "estimated_credit_relevance": estimated_credit_relevance,
        "monthly_revenue": monthly_revenue,
        "current_effective_rate": current_effective_rate,
        "anexo_utilizado": anexo_nome,
        "fator_r_informado": fator_r_informado,
        "aliquota_informada_manualmente": aliquota_informada_manualmente,
        "faixa_rbt12": _faixa_texto(revenue, anexo),
        "rbt12_acima_limite_simples": revenue > 4_800_000,
        "cbs_rate": CBS_RATE,
        "current_monthly_tax": current_monthly_tax,
        "hybrid_cbs": hybrid_cbs,
        "hybrid_monthly_tax": hybrid_monthly_tax,
        "tax_increase": tax_increase,
        "tax_increase_percent": tax_increase_percent,
        "authority_summary": authority_summary,
        "normative_source": "EC 132/2023 e LC 214/2025 (referência normativa da Reforma Tributária)",
        "profile": profile,
        "activity": activity,
        "revenue": revenue,
        "b2b_percent": b2b_percent,
        "caveat": "A carga atual segue a fórmula oficial da LC 123/2006, art. 18, mas depende dos dados informados, especialmente Fator R e alíquota manual. Acima de R$ 4,8 milhões de RBT12, a taxa da última faixa é apenas uma aproximação, pois a empresa sairia do Simples. A CBS de 9,43% é uma premissa de simulação; confirme tudo com seu contador antes de decidir.",
    }


if __name__ == "__main__":
    print(effective_simples_rate(180_000, ANEXO_I))
    print(effective_simples_rate(360_000, ANEXO_I))