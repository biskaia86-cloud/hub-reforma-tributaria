"""Diagnóstico inicial da escolha entre Simples atual e cenário híbrido."""

from __future__ import annotations

CBS_RATE = 0.0943
CURRENT_EFFECTIVE_RATE = 0.06


def format_brl(value: float) -> str:
    """Formata valores numéricos no padrão monetário brasileiro."""
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

def diagnose(profile: str, activity: str, revenue: float, b2b_percent: int) -> dict:
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
    monthly_revenue = revenue / 12
    current_monthly_tax = monthly_revenue * CURRENT_EFFECTIVE_RATE
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
        "current_effective_rate": CURRENT_EFFECTIVE_RATE,
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
        "caveat": "A alíquota de 9,43% é uma premissa de simulação e ainda não foi definida como alíquota definitiva pelo Governo. Valide CNAE, margem, folha, UF, município e regras vigentes.",
    }