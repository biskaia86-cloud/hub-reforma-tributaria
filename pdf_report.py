"""Geração do relatório PDF para download."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(lead: dict, answers: dict, diagnosis: dict, source: str, projection: dict | None = None) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    navy = colors.Color(10 / 255, 37 / 255, 64 / 255)
    blue = colors.Color(23 / 255, 92 / 255, 211 / 255)
    cyan = colors.Color(32 / 255, 184 / 255, 213 / 255)
    slate = colors.Color(18 / 255, 56 / 255, 102 / 255)
    client_gray = colors.Color(245 / 255, 245 / 255, 245 / 255)
    ink = colors.Color(29 / 255, 41 / 255, 57 / 255)
    muted = colors.Color(83 / 255, 101 / 255, 124 / 255)
    white = colors.white

    styles.add(ParagraphStyle(name="HeaderKicker", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.Color(139 / 255, 211 / 255, 1), spaceAfter=3))
    styles.add(ParagraphStyle(name="HeaderTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=white))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=navy, spaceBefore=5, spaceAfter=8))
    styles.add(ParagraphStyle(name="Label", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=muted, spaceAfter=3))
    styles.add(ParagraphStyle(name="Value", parent=styles["BodyText"], fontName="Helvetica", fontSize=11, leading=14, textColor=ink))
    styles.add(ParagraphStyle(name="CardLabel", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.Color(185 / 255, 234 / 255, 244 / 255)))
    styles.add(ParagraphStyle(name="CardValue", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=white))
    styles.add(ParagraphStyle(name="ConclusionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=cyan, spaceAfter=8))
    styles.add(ParagraphStyle(name="ConclusionHeading", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=white, spaceAfter=6))
    styles.add(ParagraphStyle(name="ConclusionText", parent=styles["BodyText"], fontName="Helvetica", fontSize=11, leading=15, textColor=white))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=muted))

    def safe(value: object) -> str:
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def draw_footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.Color(248 / 255, 250 / 255, 252 / 255))
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canvas.setFillColor(navy)
        canvas.rect(0, A4[1] - 1.4 * cm, A4[0], 1.4 * cm, stroke=0, fill=1)
        canvas.setStrokeColor(cyan)
        canvas.setLineWidth(2.5)
        canvas.line(1.6 * cm, 1.15 * cm, A4[0] - 1.6 * cm, 1.15 * cm)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(muted)
        canvas.drawCentredString(A4[0] / 2, .72 * cm, "Gerado pela Central da Reforma Tributária | Rota Simples")
        canvas.restoreState()

    header = Table([[Paragraph("DIAGNÓSTICO EXECUTIVO", styles["HeaderKicker"])], [Paragraph("Reforma Tributária - Rota Simples", styles["HeaderTitle"])]], colWidths=[17.8 * cm], rowHeights=[.45 * cm, .9 * cm])
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), navy), ("LINEBELOW", (0, 0), (-1, 0), 3, cyan), ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    client_rows = [[Paragraph("CLIENTE", styles["Label"]), Paragraph("CONTATO", styles["Label"])], [Paragraph(safe(lead["company_name"]), styles["Value"]), Paragraph(safe(lead["name"]), styles["Value"])], [Paragraph("ATIVIDADE", styles["Label"]), Paragraph("PERFIL DE VENDA", styles["Label"])], [Paragraph(safe(answers["activity"]), styles["Value"]), Paragraph(safe(answers["profile"]), styles["Value"])]]
    client = Table(client_rows, colWidths=[8.9 * cm, 8.9 * cm], rowHeights=[.45 * cm, .7 * cm, .45 * cm, .7 * cm])
    client.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), client_gray), ("BOX", (0, 0), (-1, -1), 1, colors.Color(215 / 255, 215 / 255, 215 / 255)), ("INNERGRID", (0, 0), (-1, -1), .5, white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12)]))
    cards = Table([[Paragraph("FATURAMENTO EM 12 MESES", styles["CardLabel"]), Paragraph("VENDAS PARA PJ (B2B)", styles["CardLabel"])], [Paragraph(f'<b>R$ {answers["revenue"]:,.2f}</b>', styles["CardValue"]), Paragraph(f'<b>{answers["b2b_percent"]}%</b>', styles["CardValue"])]], colWidths=[8.9 * cm, 8.9 * cm], rowHeights=[.5 * cm, 1 * cm])
    cards.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), navy), ("BACKGROUND", (1, 0), (1, -1), blue), ("BOX", (0, 0), (-1, -1), 1.2, cyan), ("LINEBEFORE", (1, 0), (1, -1), 1.2, cyan), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    conclusion = Table([[Paragraph("CONCLUSÃO | SIMPLES HÍBRIDO", styles["ConclusionTitle"])], [Paragraph(safe(diagnosis["recommendation"]), styles["ConclusionHeading"])], [Paragraph(safe(diagnosis["summary"]), styles["ConclusionText"])], [Paragraph(safe(diagnosis["authority_summary"]), styles["ConclusionText"])]], colWidths=[17.8 * cm])
    conclusion.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), slate), ("LINEBEFORE", (0, 0), (0, -1), 6, cyan), ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    impact_rows = [
        [Paragraph("RELEVÂNCIA ESTIMADA DO CRÉDITO", styles["Label"]), Paragraph(f'{diagnosis["estimated_credit_relevance"]}%', styles["Value"])],
        [Paragraph("ANEXO UTILIZADO", styles["Label"]), Paragraph(safe(diagnosis["anexo_utilizado"]), styles["Value"])],
        [Paragraph("FAIXA RBT12", styles["Label"]), Paragraph(safe(diagnosis["faixa_rbt12"]), styles["Value"])],
        [Paragraph("CENÁRIO ATUAL ESTIMADO", styles["Label"]), Paragraph(f'R$ {diagnosis["current_monthly_tax"]:,.2f}', styles["Value"])],
        [Paragraph("CENÁRIO HÍBRIDO SIMULADO", styles["Label"]), Paragraph(f'R$ {diagnosis["hybrid_monthly_tax"]:,.2f}', styles["Value"])],
        [Paragraph("DIFERENÇA ESTIMADA (SIMULAÇÃO)", styles["Label"]), Paragraph(f'R$ {diagnosis["tax_increase"]:,.2f} ({diagnosis["tax_increase_percent"]:.1f}%)', styles["Value"])],
    ]
    impact = Table(impact_rows, colWidths=[8.9 * cm, 8.9 * cm])
    impact.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), white), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, colors.Color(238 / 255, 244 / 255, 255 / 255)]), ("LINEBELOW", (0, 0), (-1, -1), .6, colors.Color(183 / 255, 203 / 255, 226 / 255)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story = [header, Spacer(1, .45 * cm), Paragraph("Dados do cliente", styles["SectionTitle"]), client, Spacer(1, .4 * cm), cards, Spacer(1, .5 * cm), conclusion, Spacer(1, .4 * cm), Paragraph("Indicadores de impacto", styles["SectionTitle"]), impact, Spacer(1, .2 * cm), Paragraph("Este valor compara dois cenários possíveis e não representa uma cobrança automática. A alíquota do CBS ainda não foi definida em caráter definitivo e a reforma está em transição gradual até 2033.", styles["SmallMuted"])]
    if projection is not None:
        projection_rows = [[Paragraph("ANO", styles["Label"]), Paragraph("HÍBRIDO", styles["Label"]), Paragraph("LUCRO REAL", styles["Label"]), Paragraph("DIFERENÇA", styles["Label"]), Paragraph("MELHOR", styles["Label"])]]
        for row in projection["anos"]:
            projection_rows.append([str(row["ano"]), f'R$ {row["carga_hibrido"]:,.2f}', f'R$ {row["carga_real"]:,.2f}', f'R$ {row["diferenca"]:,.2f}', row["regime_mais_vantajoso"]])
        projection_table = Table(projection_rows, colWidths=[1.7 * cm, 3.8 * cm, 3.8 * cm, 3.8 * cm, 4.7 * cm], repeatRows=1)
        projection_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, colors.Color(238 / 255, 244 / 255, 255 / 255)]), ("GRID", (0, 0), (-1, -1), .4, colors.Color(183 / 255, 203 / 255, 226 / 255)), ("FONTSIZE", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        crossover = projection["crossover_year"]
        highlight = f"Ano de virada: {crossover}." if crossover else "Não houve ano de virada no período simulado."
        story.extend([Spacer(1, .4 * cm), Paragraph("Rota Simples - Enquadramento completo", styles["SectionTitle"]), projection_table, Spacer(1, .2 * cm), Paragraph(safe(f'{highlight} Economia acumulada estimada: R$ {projection["economia_acumulada_periodo"]:,.2f}.'), styles["SmallMuted"])])
    story.extend([Spacer(1, .3 * cm), Paragraph(f'Base normativa: {safe(source)}.', styles["SmallMuted"]), Paragraph(safe(diagnosis["caveat"]), styles["SmallMuted"])])
    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()