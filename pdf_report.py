"""Geração do relatório PDF para download."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def build_pdf(lead: dict, answers: dict, diagnosis: dict, source: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Relatório Rota Simples", styles["Title"]),
        Paragraph("CENTRAL RT | Rota Simples", styles["Heading2"]),
        Spacer(1, 0.5 * cm),
    ]
    rows = [
        ["Empresa", lead["company_name"]],
        ["Contato", f'{lead["name"]} | {lead["corporate_email"]} | {lead["phone"]}'],
        ["Perfil de venda", answers["profile"]],
        ["Atividade", answers["activity"]],
        ["Faturamento em 12 meses", f'R$ {answers["revenue"]:,.2f}'],
        ["Vendas para PJ", f'{answers["b2b_percent"]}%'],
    ]
    table = Table(rows, colWidths=[5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef4f1")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d5ce")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([table, Spacer(1, 0.6 * cm), Paragraph("Diagnóstico", styles["Heading2"]),
                  Paragraph(diagnosis["recommendation"], styles["Heading3"]),
                  Paragraph(diagnosis["summary"], styles["BodyText"]),
                  Paragraph(diagnosis["authority_summary"], styles["BodyText"]), Spacer(1, 0.3 * cm),
                  Paragraph(f'Relevância estimada do crédito: {diagnosis["estimated_credit_relevance"]}%', styles["BodyText"]),
                  Paragraph(f'Cenário atual estimado: R$ {diagnosis["current_monthly_tax"]:,.2f}', styles["BodyText"]),
                  Paragraph(f'Cenário híbrido simulado: R$ {diagnosis["hybrid_monthly_tax"]:,.2f}', styles["BodyText"]),
                  Paragraph(f'Aumento simulado: R$ {diagnosis["tax_increase"]:,.2f} ({diagnosis["tax_increase_percent"]:.1f}%)', styles["BodyText"]),
                  Paragraph(f'Base normativa: {diagnosis["normative_source"]}', styles["BodyText"]), Spacer(1, 0.4 * cm),
                  Paragraph(diagnosis["caveat"], styles["BodyText"])])
    document.build(story)
    return buffer.getvalue()