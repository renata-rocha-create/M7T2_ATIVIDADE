"""
QuantAI — Streamlit App
M7T2 · Zigurat Institute of Technology · Prof. Thomas Takeuchi · Aluna: Renata Rocha
"""

import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from extrator_ifc import extrair_quantitativos
from sinapi_client import buscar_precos_sinapi, info_referencia
from excel_export import gerar_excel_bytes

st.set_page_config(
    page_title="QuantAI — Zigurat",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta Zigurat ────────────────────────────────────────────────────────────
Z_BLUE_DARK  = "#1B3A6B"
Z_BLUE_MED   = "#2E5FA3"
Z_BLUE_LIGHT = "#4A90D9"
Z_BLUE_BG    = "#EBF3FB"
Z_GREEN      = "#00A86B"
Z_GREEN_LT   = "#E8F7F1"
Z_GRAY       = "#3D4451"
Z_GRAY2      = "#6B7280"
Z_BORDER     = "#E0E4EC"
Z_BG         = "#F7F8FA"

CORES_CAT = {
    "Revestimentos": Z_BLUE_MED,
    "Forros":        Z_GREEN,
    "Esquadrias":    Z_BLUE_LIGHT,
    "Louças":        "#5B8DEF",
    "Impermeab.":    "#3A7BD5",
}

# ── CSS — apenas estilos, sem HTML estrutural no sidebar ──────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: #FFFFFF !important;
    border-right: 3px solid {Z_GREEN} !important;
}}

/* Botão primário — azul */
.stButton > button[kind="primary"] {{
    background-color: {Z_BLUE_LIGHT} !important;
    border-color: {Z_BLUE_LIGHT} !important;
    color: white !important;
    font-weight: 600 !important;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: {Z_BLUE_MED} !important;
    border-color: {Z_BLUE_MED} !important;
}}

/* Download button — azul */
.stDownloadButton > button {{
    background-color: {Z_BLUE_LIGHT} !important;
    border-color: {Z_BLUE_LIGHT} !important;
    color: white !important;
    font-weight: 600 !important;
}}
.stDownloadButton > button:hover {{
    background-color: {Z_BLUE_MED} !important;
}}

/* Radio e checkbox — azul */
input[type="radio"] {{ accent-color: {Z_BLUE_LIGHT} !important; }}
input[type="checkbox"] {{ accent-color: {Z_BLUE_LIGHT} !important; }}

/* Tab ativa — azul */
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: {Z_BLUE_LIGHT} !important;
}}
.stTabs [aria-selected="true"] {{
    color: {Z_BLUE_LIGHT} !important;
    font-weight: 600 !important;
}}

/* Métricas */
.metric-row {{ display:flex; gap:12px; margin:12px 0; }}
.metric-box {{
    background:#fff; border:1px solid {Z_BORDER};
    border-radius:8px; padding:14px 18px; flex:1;
    border-top:3px solid {Z_BLUE_LIGHT};
}}
.metric-box.green {{ border-top-color:{Z_GREEN}; }}
.metric-label {{
    font-size:10px; font-weight:700; color:{Z_GRAY2};
    text-transform:uppercase; letter-spacing:.07em; margin-bottom:6px;
}}
.metric-value {{ font-size:22px; font-weight:700; color:{Z_GRAY}; }}
.metric-value.green {{ color:{Z_GREEN}; }}
.metric-unit {{ font-size:11px; color:{Z_GRAY2}; margin-top:2px; }}

/* Badge SINAPI */
.sinapi-badge {{
    background:{Z_BLUE_BG}; color:{Z_BLUE_MED};
    border:1px solid {Z_BLUE_MED};
    border-radius:20px; padding:3px 12px;
    font-size:11px; font-weight:600; display:inline-block;
}}

/* Header card */
.app-header {{
    background:#fff; border:1px solid {Z_BORDER};
    border-radius:10px; padding:20px 28px;
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:20px;
}}
.app-title {{
    font-size:22px; font-weight:700; color:{Z_BLUE_DARK}; margin:0 0 4px;
}}
.app-sub {{
    font-size:11px; color:{Z_GRAY2};
    letter-spacing:.05em; text-transform:uppercase;
}}
.zig-right {{
    display:flex; align-items:center; gap:10px;
}}
.zig-right-text .zig-name {{
    font-size:17px; font-weight:800; color:{Z_GRAY};
    letter-spacing:.05em; line-height:1;
}}
.zig-right-text .zig-sub {{
    font-size:8px; color:{Z_GRAY2};
    letter-spacing:.12em; text-transform:uppercase;
}}
</style>
""", unsafe_allow_html=True)

# ── SVG logo Zigurat (ícone apenas, sem texto) ────────────────────────────────
# URL pública do logo oficial Zigurat
LOGO_URL = "https://bimforum.org.br/wp-content/uploads/2024/05/ZIGURAT-Logo-1.png"
LOGO_IMG = f'<img src="{LOGO_URL}" height="108" style="display:block">'
# SVG fallback (ícone apenas, sem texto) para o header
LOGO_SVG = LOGO_IMG

# ── Sidebar — usando componentes nativos Streamlit ────────────────────────────
with st.sidebar:
    # Logo oficial Zigurat (imagem com texto incluso)
    st.markdown(
        "<div style='padding:14px 16px 10px'>" + LOGO_SVG + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f"<hr style='border:none;border-top:2px solid {Z_GREEN};margin:8px 0'>",
                unsafe_allow_html=True)

    # Usuário
    st.markdown(f"""
    <div style='background:{Z_BG};border:1px solid {Z_BORDER};border-radius:8px;
                padding:10px 14px;margin-bottom:8px'>
        <div style='font-size:13px;font-weight:600;color:{Z_GRAY}'>Renata Rocha</div>
        <div style='font-size:11px;color:{Z_GRAY2};margin-top:2px'>Arquiteta · Coord. BIM</div>
        <div style='font-size:10px;color:#9BAAB8;margin-top:2px'>M7T2 · Prof. Thomas Takeuchi</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none;border-top:2px solid {Z_GREEN};margin:8px 0'>",
                unsafe_allow_html=True)

    # SINAPI ref
    ref = info_referencia()
    st.markdown(
        f"<div style='font-size:10px;font-weight:700;color:{Z_GRAY2};"
        f"letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px'>"
        f"Referência de Preços</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div style='background:{Z_GREEN_LT};border:1px solid {Z_GREEN};
                border-radius:8px;padding:10px 14px;margin-bottom:12px;
                font-size:11px;color:#0A6B45;line-height:1.7'>
        📌 <strong>Tabela SINAPI embutida</strong><br>
        Fonte: {ref['fonte']}<br>
        Ref.: {ref['mes']}<br>
        <span style='font-size:10px;color:#3A9E78'>{ref['nota']}</span>
    </div>
    """, unsafe_allow_html=True)

    estado = st.selectbox(
        "Estado de referência",
        options=["SP","RJ","MG","RS","PR","SC","BA","GO","DF",
                 "CE","PE","AM","PA","MT","MS","ES","RN","PB",
                 "AL","SE","PI","MA","TO","RO","AC","RR","AP"],
        index=0,
    )
    regime = st.radio(
        "Regime de preços",
        options=["desonerado","nao_desonerado"],
        format_func=lambda x: "Desonerado" if x=="desonerado" else "Não desonerado",
        horizontal=True,
    )

    st.markdown(f"<hr style='border:none;border-top:2px solid {Z_GREEN};margin:8px 0'>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:10px;font-weight:700;color:{Z_GRAY2};"
        f"letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px'>"
        f"Escopo — Arquitetura</div>",
        unsafe_allow_html=True,
    )

    escopo = {
        "revestimentos": st.checkbox("Revestimentos (piso / parede / teto)", value=True),
        "esquadrias":    st.checkbox("Esquadrias (portas e janelas)",          value=True),
        "loucas":        st.checkbox("Louças e metais sanitários",             value=True),
        "rodapes":       st.checkbox("Rodapés e molduras",                     value=False),
        "forros":        st.checkbox("Forros / tetos",                         value=False),
        "impermeab":     st.checkbox("Impermeabilização",                      value=False),
    }

    st.markdown(f"<hr style='border:none;border-top:2px solid {Z_GREEN};margin:8px 0'>",
                unsafe_allow_html=True)
    st.caption(f"SINAPI: {ref['url']}\nIFC: ifcopenshell.org")

# ── Header principal ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
  <div>
    <div class="app-title">QuantAI — Quantificação Arquitetônica BIM</div>
    <div class="app-sub">Extração de quantitativos IFC · Preços SINAPI · M7T2 · Master IA para AEC</div>
  </div>

</div>
""", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Arquivo IFC",
    type=["ifc"],
    help="Exportado do Revit, ArchiCAD ou Vectorworks. Suporta IFC 2x3 e IFC 4.",
    label_visibility="collapsed",
)
c1, c2 = st.columns([3, 1])
with c1:
    if uploaded:
        st.success(f"**{uploaded.name}** — {uploaded.size/1_048_576:.1f} MB carregado")
    else:
        st.info("Arraste um arquivo .ifc para começar · Suporta IFC2X3 e IFC4")
with c2:
    processar = st.button("⚡ Processar IFC", disabled=uploaded is None,
                          type="primary", use_container_width=True)
st.divider()

# ── Sessão ────────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.ref_label = ""
    st.session_state.aviso = ""

# ── Processamento ─────────────────────────────────────────────────────────────
if processar and uploaded:
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name
    with st.spinner("Lendo entidades IFC…"):
        try:
            rows = extrair_quantitativos(tmp_path, escopo)
        except Exception as e:
            st.error(f"Erro ao ler o IFC: {e}")
            Path(tmp_path).unlink(missing_ok=True)
            st.stop()
    Path(tmp_path).unlink(missing_ok=True)
    if not rows:
        st.warning("Nenhum elemento encontrado. Verifique o escopo selecionado.")
        st.stop()
    with st.spinner("Consultando tabela SINAPI…"):
        precos, aviso = buscar_precos_sinapi(rows, "", estado, regime)
    for r in rows:
        r["preco_unit"] = precos.get(str(r["cod"]))
        r["total"] = (r["qtd"] * r["preco_unit"]) if r["preco_unit"] else None
    rl = "Desonerado" if regime == "desonerado" else "Não desonerado"
    st.session_state.df        = pd.DataFrame(rows)
    st.session_state.ref_label = f"SINAPI {ref['mes']} · {estado} · {rl}"
    st.session_state.aviso     = aviso

# ── Resultados ─────────────────────────────────────────────────────────────────
df: pd.DataFrame = st.session_state.df

if df is not None and not df.empty:
    ref_label = st.session_state.ref_label
    if st.session_state.aviso:
        st.info(f"ℹ️ {st.session_state.aviso}")

    total_custo  = df["total"].sum() if "total" in df else 0
    total_itens  = len(df)
    total_area   = df.loc[df["un"]=="m2","qtd"].sum()
    n_pavimentos = df["pav"].nunique()

    def fmt_br(x, prefix=""):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return "—"
        return f"{prefix}{x:,.2f}".replace(",","X").replace(".",",").replace("X",".")

    custo_fmt   = fmt_br(total_custo, "R$ ") if total_custo else "—"
    custo_class = "green" if total_custo else ""

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box">
        <div class="metric-label">Itens extraídos</div>
        <div class="metric-value">{total_itens}</div>
        <div class="metric-unit">elementos</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Área total</div>
        <div class="metric-value">{fmt_br(total_area)}</div>
        <div class="metric-unit">m²</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Pavimentos</div>
        <div class="metric-value">{n_pavimentos}</div>
        <div class="metric-unit">andares lidos</div>
      </div>
      <div class="metric-box {custo_class}">
        <div class="metric-label">Custo estimado</div>
        <div class="metric-value {custo_class}">{custo_fmt}</div>
        <div class="metric-unit">referência SINAPI</div>
      </div>
    </div>
    <span class="sinapi-badge">📌 {ref_label}</span>
    """, unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Quantitativos",
        "📊 Gráfico por categoria",
        "🗺️ Mapa de calor por pavimento",
        "📥 Exportar Excel",
    ])

    with tab1:
        cf1, cf2, cf3 = st.columns([2, 2, 2])
        with cf1:
            cats    = ["Todas"] + sorted(df["cat"].unique().tolist())
            cat_sel = st.selectbox("Categoria", cats)
        with cf2:
            pavs    = ["Todos"] + sorted(df["pav"].unique().tolist())
            pav_sel = st.selectbox("Pavimento", pavs)
        with cf3:
            busca = st.text_input("Buscar item", placeholder="ex: cerâmico")

        dv = df.copy()
        if cat_sel != "Todas": dv = dv[dv["cat"]==cat_sel]
        if pav_sel != "Todos": dv = dv[dv["pav"]==pav_sel]
        if busca:              dv = dv[dv["item"].str.contains(busca, case=False, na=False)]

        ds = dv[["cod","item","ifc","pav","cat","un","qtd","preco_unit","total"]].copy()
        ds.columns = ["Cód. SINAPI","Elemento","Entidade IFC","Pavimento",
                      "Categoria","Unidade","Quantidade","Preço unit. (R$)","Total (R$)"]
        ds["Quantidade"]       = ds["Quantidade"].map(fmt_br)
        ds["Preço unit. (R$)"] = ds["Preço unit. (R$)"].map(lambda x: fmt_br(x, "R$ "))
        ds["Total (R$)"]       = ds["Total (R$)"].map(lambda x: fmt_br(x, "R$ "))
        ds["Unidade"]          = ds["Unidade"].str.replace("m2", "m²", regex=False)
        st.dataframe(ds, use_container_width=True, hide_index=True)

        tf = dv["total"].sum()
        if tf:
            st.markdown(f"**Total filtrado: {fmt_br(tf, 'R$ ')}**")

    with tab2:
        dc = (df.groupby("cat")
              .agg(total_custo=("total","sum"), total_itens=("item","count"))
              .reset_index().sort_values("total_custo", ascending=True))
        dc["cor"] = dc["cat"].map(lambda c: CORES_CAT.get(c, "#888780"))

        if dc["total_custo"].sum() > 0:
            fig = go.Figure(go.Bar(
                y=dc["cat"], x=dc["total_custo"], orientation="h",
                marker_color=dc["cor"].tolist(),
                text=dc["total_custo"].map(lambda v: f"R$ {v:,.0f}".replace(",",".")),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
            ))
            fig.update_layout(
                title="Custo estimado por categoria (R$)",
                xaxis_title="Total (R$)", yaxis_title=None,
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter, sans-serif", size=12),
                margin=dict(l=20,r=80,t=50,b=30),
                height=max(250,60*len(dc)), showlegend=False,
            )
            fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Área total = 0 — verifique os parâmetros de quantidade no modelo IFC.")

        fig2 = px.pie(dc, values="total_itens", names="cat",
                      color="cat", color_discrete_map=CORES_CAT, hole=0.42)
        fig2.update_traces(textposition="outside", textinfo="label+percent")
        fig2.update_layout(showlegend=False, margin=dict(l=20,r=20,t=20,b=20),
                           height=340, paper_bgcolor="white",
                           font=dict(family="Inter, sans-serif"))
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("#### Quantidade por pavimento e categoria")
        pq = df.pivot_table(index="pav", columns="cat", values="qtd",
                            aggfunc="sum", fill_value=0)
        fh = go.Figure(go.Heatmap(
            z=pq.values, x=pq.columns.tolist(), y=pq.index.tolist(),
            colorscale=[[0,Z_BLUE_BG],[0.5,Z_BLUE_LIGHT],[1,Z_BLUE_DARK]],
            text=pq.values.round(1), texttemplate="%{text}",
            hovertemplate="Pav: %{y}<br>Cat: %{x}<br>Qtd: %{z:.1f}<extra></extra>",
            colorbar=dict(title="Qtd."),
        ))
        fh.update_layout(
            xaxis_title="Categoria", yaxis_title="Pavimento",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter, sans-serif", size=12),
            margin=dict(l=20,r=20,t=30,b=30), height=max(280,70*len(pq)),
        )
        st.plotly_chart(fh, use_container_width=True)

        if df["total"].notna().any():
            st.markdown("#### Custo por pavimento e categoria (R$)")
            pc = df.pivot_table(index="pav", columns="cat", values="total",
                                aggfunc="sum", fill_value=0)
            fh2 = go.Figure(go.Heatmap(
                z=pc.values, x=pc.columns.tolist(), y=pc.index.tolist(),
                colorscale=[[0,Z_GREEN_LT],[0.5,Z_GREEN],[1,Z_BLUE_DARK]],
                text=pc.values, texttemplate="R$ %{text:,.0f}",
                hovertemplate="Pav: %{y}<br>Cat: %{x}<br>R$ %{z:,.2f}<extra></extra>",
                colorbar=dict(title="R$"),
            ))
            fh2.update_layout(
                xaxis_title="Categoria", yaxis_title="Pavimento",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter, sans-serif", size=12),
                margin=dict(l=20,r=20,t=30,b=30), height=max(280,70*len(pc)),
            )
            st.plotly_chart(fh2, use_container_width=True)

    with tab4:
        st.markdown(f"""
        O arquivo Excel contém **3 abas**:
        - **Quantitativos** — Cód. SINAPI, elemento, pavimento, unidade, quantidade, preço e total
        - **Resumo por Categoria** — agrupamento com % de custo
        - **Critérios Adotados** — critérios de medição, mapeamento IFC e referências normativas

        Referência: `{ref_label}`
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

else:
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;padding:20px 0 10px'>"
            "<h3 style='color:#1B3A6B;margin-bottom:16px'>Como usar o QuantAI</h3>"
            "</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("**1.** Selecione o **estado** e o **regime de preços** na barra lateral")
        with c2:
            st.info("**2.** Marque o **escopo** desejado e faça upload do arquivo **.ifc**")
        with c3:
            st.info("**3.** Clique em **⚡ Processar IFC** para extrair os quantitativos")
