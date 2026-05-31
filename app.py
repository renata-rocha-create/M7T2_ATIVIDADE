"""
QuantAI — Streamlit App
=======================
Quantificação arquitetônica BIM com preços SINAPI em tempo real.

M7T2 · Zigurat Institute of Technology · Prof. Thomas Takeuchi
Aluna: Renata Rocha

Execução:
    streamlit run app.py

Dependências:
    pip install streamlit ifcopenshell plotly openpyxl requests pandas
"""

import io
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from extrator_ifc import extrair_quantitativos
from sinapi_client import buscar_precos_sinapi
from excel_export import gerar_excel_bytes

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantAI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta Zigurat ────────────────────────────────────────────────────────────
AZUL_DARK  = "#00427A"
AZUL_MED   = "#185FA5"
TEAL       = "#0F6E56"
AMBER      = "#854F0B"

CORES_CAT = {
    "Revestimentos": AZUL_MED,
    "Forros":        TEAL,
    "Esquadrias":    "#993C1D",
    "Louças":        AMBER,
    "Impermeab.":    "#534AB7",
}

# ── CSS customizado ────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #f8f7f4; }
[data-testid="stSidebar"] .stMarkdown h3 { color: #00427A; font-size: 13px; }
.metric-card {
    background: #f1f0eb; border-radius: 8px;
    padding: 12px 16px; text-align: center;
}
.metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: .05em; }
.metric-value { font-size: 26px; font-weight: 600; color: #1a1a18; }
.metric-unit  { font-size: 12px; color: #5f5e5a; margin-top: 2px; }
.sinapi-badge {
    background: #E1F5EE; color: #085041;
    border-radius: 20px; padding: 3px 10px;
    font-size: 11px; font-weight: 600;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>
        <div style='background:{AZUL_DARK};border-radius:8px;padding:6px 8px;
                    color:white;font-size:18px;line-height:1'>🏛️</div>
        <div>
            <div style='font-size:18px;font-weight:700;color:{AZUL_DARK}'>QuantAI</div>
            <div style='font-size:10px;color:#888;letter-spacing:.05em'>ZIGURAT INSTITUTE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#fff;border:0.5px solid #e0dfd8;border-radius:8px;
                padding:10px 12px;margin:8px 0'>
        <div style='font-size:13px;font-weight:600;color:#1a1a18'>Renata Rocha</div>
        <div style='font-size:11px;color:#888'>Arquiteta · Coord. BIM</div>
        <div style='font-size:10px;color:#aaa;margin-top:2px'>M7T2 · Prof. Thomas Takeuchi</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Configurações SINAPI")

    api_key = st.text_input(
        "API Key — Orçamentador",
        type="password",
        placeholder="Obtenha em orcamentador.com.br/api",
        help="Plano gratuito disponível. A chave fica apenas na sua sessão.",
    )

    estado = st.selectbox(
        "Estado de referência",
        options=["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "DF",
                 "CE", "PE", "AM", "PA", "MT", "MS", "ES", "RN", "PB",
                 "AL", "SE", "PI", "MA", "TO", "RO", "AC", "RR", "AP"],
        index=0,
    )

    regime = st.radio(
        "Regime de preços",
        options=["desonerado", "nao_desonerado"],
        format_func=lambda x: "Desonerado" if x == "desonerado" else "Não desonerado",
        horizontal=True,
    )

    st.divider()

    st.markdown("### Escopo — Arquitetura")
    escopo = {
        "revestimentos": st.checkbox("Revestimentos (piso / parede / teto)", value=True),
        "esquadrias":    st.checkbox("Esquadrias (portas e janelas)",          value=True),
        "loucas":        st.checkbox("Louças e metais sanitários",             value=True),
        "rodapes":       st.checkbox("Rodapés e molduras",                     value=False),
        "forros":        st.checkbox("Forros / tetos",                         value=False),
        "impermeab":     st.checkbox("Impermeabilização",                      value=False),
    }

    st.divider()
    st.caption("API SINAPI: orcamentador.com.br/api  \nIFC: ifcopenshell.org")

# ── Corpo principal ───────────────────────────────────────────────────────────
st.markdown(f"## <span style='color:{AZUL_DARK}'>QuantAI</span> — Quantificação Arquitetônica BIM", unsafe_allow_html=True)
st.caption("Extração de quantitativos de arquivo IFC com preços SINAPI em tempo real · M7T2 · Zigurat Institute of Technology")

# ── Upload IFC ────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Arquivo IFC",
    type=["ifc"],
    help="Exportado do Revit, ArchiCAD ou Vectorworks. Suporta IFC 2x3 e IFC 4.",
    label_visibility="collapsed",
)

col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    if uploaded:
        st.success(f"**{uploaded.name}** — {uploaded.size / 1_048_576:.1f} MB carregado")
    else:
        st.info("Arraste um arquivo .ifc para começar")

with col_up2:
    processar = st.button(
        "⚡ Processar IFC",
        disabled=uploaded is None,
        type="primary",
        use_container_width=True,
    )

st.divider()

# ── Processamento ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.ref_sinapi = ""

if processar and uploaded:
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    with st.spinner("Lendo entidades IFC..."):
        try:
            rows = extrair_quantitativos(tmp_path, escopo)
        except Exception as e:
            st.error(f"Erro ao ler o IFC: {e}")
            st.stop()

    if not rows:
        st.warning("Nenhum elemento de arquitetura encontrado no modelo. Verifique o escopo selecionado.")
        st.stop()

    if api_key:
        with st.spinner(f"Consultando SINAPI · {estado} · {regime}..."):
            precos = buscar_precos_sinapi(rows, api_key, estado, regime)
        ref = f"SINAPI · {estado} · {regime.replace('_', ' ').title()}"
    else:
        precos = {}
        ref = "Sem integração SINAPI (API Key não informada)"
        st.warning("API Key não informada — tabela gerada sem valores de custo. Configure na barra lateral.")

    for r in rows:
        r["preco_unit"] = precos.get(r["cod"])
        r["total"] = (r["qtd"] * r["preco_unit"]) if r["preco_unit"] else None

    st.session_state.df = pd.DataFrame(rows)
    st.session_state.ref_sinapi = ref
    Path(tmp_path).unlink(missing_ok=True)

# ── Resultados ─────────────────────────────────────────────────────────────────
df: pd.DataFrame = st.session_state.df

if df is not None and not df.empty:
    ref_sinapi = st.session_state.ref_sinapi

    # ── Métricas resumo ───────────────────────────────────────────────────────
    total_custo  = df["total"].sum() if "total" in df.columns else 0
    total_itens  = len(df)
    total_area   = df.loc[df["un"] == "m2", "qtd"].sum()
    n_pavimentos = df["pav"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Itens extraídos", total_itens, help="Total de linhas de quantitativo")
    with c2:
        st.metric("Área total (m²)", f"{total_area:,.1f}".replace(",", "."))
    with c3:
        st.metric("Pavimentos", n_pavimentos)
    with c4:
        if total_custo:
            st.metric("Custo estimado", f"R$ {total_custo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.metric("Custo estimado", "—")

    st.markdown(
        f'<span class="sinapi-badge">📌 {ref_sinapi}</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Quantitativos", "📊 Gráfico por categoria",
        "🗺️ Mapa de calor por pavimento", "📥 Exportar Excel",
    ])

    # ── Tab 1: Tabela ─────────────────────────────────────────────────────────
    with tab1:
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1:
            cats = ["Todas"] + sorted(df["cat"].unique().tolist())
            cat_sel = st.selectbox("Categoria", cats)
        with col_f2:
            pavs = ["Todos"] + sorted(df["pav"].unique().tolist())
            pav_sel = st.selectbox("Pavimento", pavs)
        with col_f3:
            busca = st.text_input("Buscar item", placeholder="ex: cerâmico")

        df_view = df.copy()
        if cat_sel != "Todas":
            df_view = df_view[df_view["cat"] == cat_sel]
        if pav_sel != "Todos":
            df_view = df_view[df_view["pav"] == pav_sel]
        if busca:
            df_view = df_view[df_view["item"].str.contains(busca, case=False)]

        df_show = df_view[[
            "cod", "item", "ifc", "pav", "cat", "un", "qtd", "preco_unit", "total"
        ]].copy()
        df_show.columns = [
            "Cód. SINAPI", "Elemento", "Entidade IFC", "Pavimento",
            "Categoria", "Unidade", "Quantidade", "Preço unit. (R$)", "Total (R$)",
        ]
        df_show["Quantidade"]       = df_show["Quantidade"].map(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_show["Preço unit. (R$)"] = df_show["Preço unit. (R$)"].map(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "—"
        )
        df_show["Total (R$)"] = df_show["Total (R$)"].map(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "—"
        )

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Quantidade":       st.column_config.TextColumn(width="small"),
                "Preço unit. (R$)": st.column_config.TextColumn(width="medium"),
                "Total (R$)":       st.column_config.TextColumn(width="medium"),
            },
        )

        total_filt = df_view["total"].sum() if "total" in df_view.columns else 0
        if total_filt:
            st.markdown(
                f"**Total filtrado: R$ {total_filt:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
                unsafe_allow_html=False,
            )

    # ── Tab 2: Gráfico por categoria ───────────────────────────────────────────
    with tab2:
        df_cat = (
            df.groupby("cat")
            .agg(total_custo=("total", "sum"), total_itens=("item", "count"))
            .reset_index()
            .sort_values("total_custo", ascending=True)
        )
        df_cat["cor"] = df_cat["cat"].map(lambda c: CORES_CAT.get(c, "#888780"))

        if df_cat["total_custo"].sum() > 0:
            fig_bar = go.Figure(go.Bar(
                y=df_cat["cat"],
                x=df_cat["total_custo"],
                orientation="h",
                marker_color=df_cat["cor"].tolist(),
                text=df_cat["total_custo"].map(
                    lambda v: f"R$ {v:,.0f}".replace(",", ".")
                ),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            ))
            fig_bar.update_layout(
                title="Custo estimado por categoria (R$)",
                xaxis_title="Total (R$)",
                yaxis_title=None,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Arial", size=12),
                margin=dict(l=20, r=80, t=50, b=30),
                height=max(250, 60 * len(df_cat)),
                showlegend=False,
            )
            fig_bar.update_xaxes(showgrid=True, gridcolor="#f0efe8", zeroline=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Integre a API Key SINAPI para visualizar valores por categoria.")

        st.markdown("#### Itens por categoria")
        fig_pie = px.pie(
            df_cat,
            values="total_itens",
            names="cat",
            color="cat",
            color_discrete_map=CORES_CAT,
            hole=0.45,
        )
        fig_pie.update_traces(textposition="outside", textinfo="label+percent")
        fig_pie.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Tab 3: Mapa de calor por pavimento ─────────────────────────────────────
    with tab3:
        st.markdown("#### Quantidade por pavimento e categoria")
        pivot_qtd = (
            df.pivot_table(
                index="pav", columns="cat",
                values="qtd", aggfunc="sum", fill_value=0,
            )
        )
        fig_heat_qtd = go.Figure(go.Heatmap(
            z=pivot_qtd.values,
            x=pivot_qtd.columns.tolist(),
            y=pivot_qtd.index.tolist(),
            colorscale=[[0, "#E6F1FB"], [0.5, AZUL_MED], [1, AZUL_DARK]],
            text=pivot_qtd.values.round(1),
            texttemplate="%{text}",
            hovertemplate="Pav: %{y}<br>Cat: %{x}<br>Qtd: %{z:.1f}<extra></extra>",
            colorbar=dict(title="Qtd."),
        ))
        fig_heat_qtd.update_layout(
            xaxis_title="Categoria",
            yaxis_title="Pavimento",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Arial", size=12),
            margin=dict(l=20, r=20, t=30, b=30),
            height=max(280, 70 * len(pivot_qtd)),
        )
        st.plotly_chart(fig_heat_qtd, use_container_width=True)

        if df["total"].notna().any():
            st.markdown("#### Custo estimado por pavimento e categoria (R$)")
            pivot_custo = (
                df.pivot_table(
                    index="pav", columns="cat",
                    values="total", aggfunc="sum", fill_value=0,
                )
            )
            fig_heat_custo = go.Figure(go.Heatmap(
                z=pivot_custo.values,
                x=pivot_custo.columns.tolist(),
                y=pivot_custo.index.tolist(),
                colorscale=[[0, "#E1F5EE"], [0.5, TEAL], [1, "#04342C"]],
                text=pivot_custo.values,
                texttemplate="R$ %{text:,.0f}",
                hovertemplate="Pav: %{y}<br>Cat: %{x}<br>R$ %{z:,.2f}<extra></extra>",
                colorbar=dict(title="R$"),
            ))
            fig_heat_custo.update_layout(
                xaxis_title="Categoria",
                yaxis_title="Pavimento",
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Arial", size=12),
                margin=dict(l=20, r=20, t=30, b=30),
                height=max(280, 70 * len(pivot_custo)),
            )
            st.plotly_chart(fig_heat_custo, use_container_width=True)

    # ── Tab 4: Exportar Excel ──────────────────────────────────────────────────
    with tab4:
        st.markdown(f"""
        O arquivo Excel gerado contém **3 abas**:
        - **Quantitativos** — tabela completa com Cód. SINAPI, elemento, pavimento, unidade, quantidade, preço e total
        - **Resumo por Categoria** — agrupamento com % de custo
        - **Critérios Adotados** — critérios de medição, mapeamento IFC e referências normativas

        Referência de preços: `{ref_sinapi}`
        """)

        excel_bytes = gerar_excel_bytes(df.to_dict("records"), estado, regime)

        st.download_button(
            label="⬇️ Baixar QuantAI_Quantitativos.xlsx",
            data=excel_bytes,
            file_name="QuantAI_Quantitativos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )

        st.info(
            "💡 O arquivo é gerado dinamicamente com os dados do processamento atual. "
            "Rode novamente o processamento se quiser atualizar os preços SINAPI.",
            icon="💡",
        )

else:
    # Estado inicial — instruções
    st.markdown(f"""
    <div style='background:#f8f7f4;border:1px solid #e0dfd8;border-radius:12px;
                padding:32px;text-align:center;color:#888'>
        <div style='font-size:40px;margin-bottom:12px'>🏛️</div>
        <div style='font-size:18px;font-weight:600;color:{AZUL_DARK};margin-bottom:8px'>
            Como usar o QuantAI
        </div>
        <div style='font-size:14px;line-height:1.8;max-width:500px;margin:0 auto'>
            1. Configure sua <b>API Key SINAPI</b> na barra lateral<br>
            2. Selecione o <b>estado</b> e o <b>regime de preços</b><br>
            3. Marque o <b>escopo</b> desejado (arquitetura)<br>
            4. Faça upload do arquivo <b>.ifc</b><br>
            5. Clique em <b>Processar IFC</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
