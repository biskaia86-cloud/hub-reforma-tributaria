---
name: especialista-web-dashboards
description: "Use when designing or improving Streamlit web interfaces, visual identity, data dashboards, KPI cards, charts, responsive layouts, currency formatting, or executive data storytelling."
---

# Especialista em Web Design e Dashboards

## Direção visual

- Priorize interfaces executivas, legíveis e com hierarquia visual clara.
- Use uma paleta intencional de azul, branco e preto, com gradientes discretos e contraste acessível.
- Dê destaque ao nome do produto e ao estado principal da análise.
- Use tipografia expressiva para títulos e uma fonte simples para dados e controles.
- Evite cards aninhados, excesso de decoração, texto explicativo longo e componentes sem função.

## Dados e diagnóstico

- Toda conclusão deve estar ligada a uma métrica ou cálculo visível.
- Exiba premissas, unidades e período de referência junto ao resultado.
- Para valores financeiros no Brasil, apresente `R$ 1.234,56`; preserve os valores numéricos internamente.
- Diferencie claramente fato normativo, premissa de simulação e estimativa.
- Use métricas, tabelas comparativas e gráficos com títulos objetivos.
- Mostre variação absoluta e percentual quando comparar cenários.
- Não use uma alíquota estimada como se fosse definitiva; sinalize a necessidade de validação oficial.

## Streamlit

- Organize o fluxo em etapas curtas: cadastro, coleta, resultado e exportação.
- Use `st.metric` para KPIs, `st.dataframe` ou `st.table` para memória de cálculo e `st.bar_chart`/Altair para comparação.
- Prefira controles nativos com rótulos claros e ajudas curtas.
- Evite HTML inseguro quando um componente nativo resolver o caso; use CSS apenas para identidade e layout.
- Valide cálculos com funções puras antes de renderizar a interface.

## Qualidade

- Teste casos de 0%, 50% e 100% de vendas B2B.
- Teste valores monetários brasileiros com milhares e centavos.
- Confirme que o dashboard não sugere precisão maior que a das premissas.
- Mantenha acessibilidade, responsividade e exportação coerentes com o que aparece na tela.
