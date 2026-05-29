import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard Comercial TechNorte",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PALETA CORPORATIVA — AZUL
# ============================================================
COLOR_NAVY      = "#0D2137"
COLOR_PRIMARY   = "#1A3F6F"
COLOR_BLUE      = "#2471A3"
COLOR_MID       = "#2980B9"
COLOR_LIGHT     = "#5DADE2"
COLOR_PALE      = "#AED6F1"
COLOR_NEGATIVE  = "#C0392B"
COLOR_WARNING   = "#D4AC0D"
COLOR_NEUTRAL   = "#1E2A3A"

PALETTE_QUAL = [
    "#1A3F6F", "#2471A3", "#5DADE2", "#0D2137",
    "#7FB3D3", "#154360", "#AED6F1", "#2980B9"
]
SCALE_BLUE = [[0, COLOR_PALE],    [1, COLOR_PRIMARY]]
SCALE_DIV  = [[0, COLOR_NEGATIVE],[0.5, "#1A2535"],  [1, COLOR_BLUE]]
SCALE_SEQ  = "Blues"

# ============================================================
# TEMA OSCURO GLOBAL PARA PLOTLY
# ============================================================
BG_DARK    = "#0E1117"   # fondo exterior del gráfico (igual al de Streamlit dark)
BG_CHART   = "#131720"   # fondo del área de trazado
FONT_LIGHT = "#D0DCF0"   # texto en gráficos
GRID_DARK  = "#1E2A3A"   # líneas de grilla

_tpl = go.layout.Template()
_tpl.layout = go.Layout(
    paper_bgcolor = BG_DARK,
    plot_bgcolor  = BG_CHART,
    font          = dict(color=FONT_LIGHT, family="sans-serif"),
    title         = dict(font=dict(color=FONT_LIGHT, size=14)),
    xaxis = dict(
        gridcolor     = GRID_DARK,
        linecolor     = GRID_DARK,
        zerolinecolor = GRID_DARK,
        tickfont      = dict(color=FONT_LIGHT),
    ),
    yaxis = dict(
        gridcolor     = GRID_DARK,
        linecolor     = GRID_DARK,
        zerolinecolor = GRID_DARK,
        tickfont      = dict(color=FONT_LIGHT),
    ),
    legend = dict(
        bgcolor     = "rgba(13,17,23,0.85)",
        bordercolor = GRID_DARK,
        font        = dict(color=FONT_LIGHT),
    ),
    coloraxis = dict(
        colorbar=dict(
            tickfont = dict(color=FONT_LIGHT),
            title    = dict(font=dict(color=FONT_LIGHT)),
        )
    ),
    geo = dict(
        bgcolor     = BG_DARK,
        lakecolor   = BG_CHART,
        landcolor   = "#1A2535",
        showframe   = False,
        showcoastlines = True,
        coastlinecolor = "#2A3A4A",
    ),
    polar = dict(
        bgcolor     = BG_CHART,
        radialaxis  = dict(gridcolor=GRID_DARK, linecolor=GRID_DARK,
                           tickfont=dict(color=FONT_LIGHT)),
        angularaxis = dict(gridcolor=GRID_DARK, linecolor=GRID_DARK,
                           tickfont=dict(color=FONT_LIGHT)),
    ),
)
pio.templates["dark_corp"] = _tpl
pio.templates.default      = "dark_corp"

# ============================================================
# CARGA DE DATOS CON CACHÉ
# ============================================================
@st.cache_data
def cargar_datos():
    fact      = pd.read_csv("data/fact_ventas.csv",   parse_dates=["fecha"])
    productos = pd.read_csv("data/dim_productos.csv")
    clientes  = pd.read_csv("data/dim_clientes.csv")

    df = fact.merge(productos, on="id_producto", how="left")
    df = df.merge(
        clientes[["id_cliente", "segmento", "tipo_cliente", "nombre_cliente"]],
        on="id_cliente", how="left"
    )
    df["anio_mes"]   = df["fecha"].dt.to_period("M").astype(str)
    df["anio"]       = df["fecha"].dt.year
    df["mes"]        = df["fecha"].dt.month
    df["nombre_mes"] = df["fecha"].dt.strftime("%B")
    df["dia_semana"] = df["fecha"].dt.day_name()
    df["hora"]       = np.random.randint(8, 20, size=len(df))
    return df

df = cargar_datos()

# ============================================================
# SIDEBAR: FILTROS GLOBALES DESPLEGABLES
# ============================================================
st.sidebar.title("Filtros Globales")

fecha_min = df["fecha"].min().date()
fecha_max = df["fecha"].max().date()
rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

paises_disponibles        = sorted(df["pais"].unique())
canales_disponibles       = sorted(df["canal"].unique())
categorias_disponibles    = sorted(df["categoria"].unique())
subcategorias_disponibles = sorted(df["subcategoria"].unique())

with st.sidebar.expander("🌍 País", expanded=False):
    pais_seleccionado = st.multiselect(
        "Países", options=paises_disponibles, default=paises_disponibles,
        label_visibility="collapsed"
    )
with st.sidebar.expander("📡 Canal", expanded=False):
    canal_seleccionado = st.multiselect(
        "Canales", options=canales_disponibles, default=canales_disponibles,
        label_visibility="collapsed"
    )
with st.sidebar.expander("🗂️ Categoría", expanded=False):
    categoria_seleccionada = st.multiselect(
        "Categorías", options=categorias_disponibles, default=categorias_disponibles,
        label_visibility="collapsed"
    )
with st.sidebar.expander("📦 Subcategoría", expanded=False):
    subcategoria_seleccionada = st.multiselect(
        "Subcategorías", options=subcategorias_disponibles, default=subcategorias_disponibles,
        label_visibility="collapsed"
    )

if "filtro_extra" not in st.session_state:
    st.session_state.filtro_extra = None

def limpiar_filtro():
    st.session_state.filtro_extra = None

st.sidebar.button("🧹 Limpiar filtro de gráfico", on_click=limpiar_filtro)

# ============================================================
# APLICACIÓN DE FILTROS
# ============================================================
mask = (
    (df["fecha"].dt.date >= rango_fechas[0]) &
    (df["fecha"].dt.date <= rango_fechas[1]) &
    (df["pais"].isin(pais_seleccionado)) &
    (df["canal"].isin(canal_seleccionado)) &
    (df["categoria"].isin(categoria_seleccionada)) &
    (df["subcategoria"].isin(subcategoria_seleccionada))
)
df_filtrado = df[mask]

if st.session_state.filtro_extra is not None:
    col_fe, val_fe = list(st.session_state.filtro_extra.items())[0]
    if col_fe in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_fe] == val_fe]

# ============================================================
# KPIs GLOBALES
# ============================================================
ventas_totales     = df_filtrado["ingreso"].sum()
utilidad_total     = df_filtrado["margen"].sum()
margen_promedio    = utilidad_total / ventas_totales if ventas_totales > 0 else 0
ticket_promedio    = ventas_totales / df_filtrado["id_venta"].nunique() if df_filtrado["id_venta"].nunique() > 0 else 0
num_transacciones  = df_filtrado["id_venta"].nunique()
descuento_promedio = df_filtrado["descuento_pct"].mean()
productos_distintos = df_filtrado["id_producto"].nunique()

# ============================================================
# ENCABEZADO Y KPIs
# ============================================================
st.title("📊 Dashboard de Desempeño Comercial — TechNorte")
st.markdown("**Audiencia:** Gerentes regionales · Director comercial · Marketing")

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("💰 Ventas Totales",     f"${ventas_totales:,.0f}")
with col2: st.metric("📈 Utilidad Total",     f"${utilidad_total:,.0f}")
with col3: st.metric("📊 Margen Promedio",    f"{margen_promedio:.2%}")
with col4: st.metric("🧾 Ticket Promedio",    f"${ticket_promedio:,.0f}")

col5, col6, col7 = st.columns(3)
with col5: st.metric("📦 Transacciones",       f"{num_transacciones:,}")
with col6: st.metric("🏷️ Descuento Promedio",  f"{descuento_promedio:.2%}")
with col7: st.metric("🛒 Productos Distintos", productos_distintos)

# ============================================================
# PESTAÑAS
# ============================================================
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Contexto",
    "📍 Resumen Ejecutivo",
    "📦 Portafolio y Canales",
    "🌎 Clientes y Geografía",
    "🔬 Análisis Avanzado",
    "🎯 Estrategia Comercial",
    "🔍 Portafolio Avanzado"
])

# ----------------------------------------------------------
# TAB 0: CONTEXTO
# ----------------------------------------------------------
with tab0:
    st.header("Contexto del negocio y descripción de los datos")
    st.subheader("🏢 La empresa")
    st.markdown("""
    **TechNorte** es una cadena de retail de tecnología, electrodomésticos, oficina, audio/video y gaming.
    Opera en **Colombia, México, Perú, Chile y Argentina** a través de tres canales:
    **tienda física, portal online y distribuidores**.
    """)
    st.subheader("🎯 Audiencia y necesidad")
    st.markdown("Dirigido a **gerentes regionales, director comercial y marketing** para monitorear "
                "ventas y rentabilidad y decidir sobre campañas, inventario y recursos.")
    st.subheader("❓ Preguntas de negocio")
    st.markdown("""
    1. ¿Cómo evolucionan las ventas y la rentabilidad en el tiempo?
    2. ¿Qué categorías, marcas y canales generan mayores ingresos y cuáles tienen problemas?
    3. ¿Cómo se concentran geográficamente las ventas y la utilidad?
    4. ¿Qué relación existe entre descuentos y margen?
    5. ¿Qué clientes son los más valiosos y cuáles requieren atención?
    """)
    st.subheader("🗃️ Estructura de los datos")
    st.markdown("""
    Modelo estrella con tres archivos CSV:
    - **fact_ventas.csv**: ~500 k transacciones diarias con métricas calculadas.
    - **dim_productos.csv**: 50 productos con categoría, subcategoría, marca y precio.
    - **dim_clientes.csv**: 1 000 clientes anonimizados con segmento y ubicación.
    """)
    st.info("💡 Usa los filtros desplegables de la barra lateral para segmentar el análisis.")

# ----------------------------------------------------------
# TAB 1: RESUMEN EJECUTIVO
# ----------------------------------------------------------
with tab1:
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("Evolución mensual de Ingresos y Margen")
        evolucion = df_filtrado.groupby("anio_mes").agg(
            ingresos=("ingreso","sum"), margen=("margen","sum")
        ).reset_index()
        evolucion["margen_pct"] = evolucion["margen"] / evolucion["ingresos"]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=evolucion["anio_mes"], y=evolucion["ingresos"],
                             name="Ingresos", marker_color=COLOR_PRIMARY, yaxis="y1"))
        fig.add_trace(go.Scatter(x=evolucion["anio_mes"], y=evolucion["margen_pct"],
                                 name="Margen %", line=dict(color=COLOR_LIGHT, width=2),
                                 mode="lines+markers", yaxis="y2"))
        fig.update_layout(
            title="Ingresos y Margen % mensual", xaxis_title="Mes",
            yaxis=dict(title="Ingresos"),
            yaxis2=dict(title="Margen %", overlaying="y", side="right", tickformat=".2%"),
            legend=dict(x=0.01, y=0.99), height=400
        )
        st.plotly_chart(fig, width='stretch')

    with col_der:
        st.subheader("Distribución geográfica de Ventas")
        ventas_pais = df_filtrado.groupby("pais")["ingreso"].sum().reset_index()
        _iso3 = {"Colombia":"COL","México":"MEX","Perú":"PER","Chile":"CHL","Argentina":"ARG"}
        ventas_pais["iso3"] = ventas_pais["pais"].map(_iso3)
        fig_map = px.choropleth(
            ventas_pais, locations="iso3", locationmode="ISO-3",
            color="ingreso", color_continuous_scale=SCALE_BLUE,
            hover_name="pais",
            title="Ventas por país", labels={"ingreso": "Ingresos USD"}
        )
        fig_map.update_geos(
            showcountries=True, countrycolor="#2A3A4A",
            fitbounds="locations",
            bgcolor=BG_DARK, landcolor="#1A2535",
            showocean=True, oceancolor="#0A1520",
            showlakes=False
        )
        st.plotly_chart(fig_map, width='stretch')

        pais_click = st.selectbox(
            "Filtrar por país:", ["Todos"] + list(paises_disponibles), key="pais_sel"
        )
        st.session_state.filtro_extra = (
            {"pais": pais_click} if pais_click != "Todos" else None
        )

    st.subheader("Composición de ventas por categoría (Treemap)")
    treemap_data = df_filtrado.groupby("categoria")["ingreso"].sum().reset_index()
    fig_treemap = px.treemap(
        treemap_data, path=["categoria"], values="ingreso",
        color="ingreso", color_continuous_scale=SCALE_BLUE,
        title="Ventas por categoría"
    )
    st.plotly_chart(fig_treemap, width='stretch')

    cat_click = st.selectbox(
        "Filtrar por categoría:", ["Todas"] + list(categorias_disponibles), key="cat_sel"
    )
    st.session_state.filtro_extra = (
        {"categoria": cat_click} if cat_click != "Todas" else None
    )

# ----------------------------------------------------------
# TAB 2: PORTAFOLIO Y CANALES
# ----------------------------------------------------------
with tab2:
    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("Top Subcategorías por Ingreso")
        top_sub = (df_filtrado.groupby("subcategoria")["ingreso"].sum()
                   .reset_index().sort_values("ingreso", ascending=True).tail(15))
        fig_barras = px.bar(
            top_sub, x="ingreso", y="subcategoria", orientation="h",
            color="ingreso", color_continuous_scale=SCALE_BLUE,
            title="Ingresos por subcategoría (Top 15)"
        )
        st.plotly_chart(fig_barras, width='stretch')
        sub_click = st.selectbox(
            "Filtrar por subcategoría:", ["Todas"] + list(subcategorias_disponibles), key="sub_sel"
        )
        st.session_state.filtro_extra = (
            {"subcategoria": sub_click} if sub_click != "Todas" else None
        )

    with col_b:
        st.subheader("Margen por Canal y Categoría (Heatmap)")
        heatmap_data  = df_filtrado.groupby(["canal","categoria"])["margen_pct"].mean().reset_index()
        heatmap_pivot = heatmap_data.pivot(index="canal", columns="categoria", values="margen_pct")
        fig_heat = px.imshow(
            heatmap_pivot, text_auto=".2%",
            color_continuous_scale=SCALE_DIV,
            title="Margen % promedio por Canal y Categoría"
        )
        st.plotly_chart(fig_heat, width='stretch')

    st.subheader("Relación Descuento vs Margen (Scatter)")
    fig_scatter = px.scatter(
        df_filtrado, x="descuento_pct", y="margen_pct",
        size="ingreso", color="categoria",
        hover_data=["subcategoria","canal"],
        title="Descuento vs Margen (tamaño = ventas)",
        color_discrete_sequence=PALETTE_QUAL
    )
    fig_scatter.add_hline(y=0, line_dash="dash", line_color=COLOR_NEGATIVE)
    st.plotly_chart(fig_scatter, width='stretch')

    st.subheader("Ventas por Categoría y Canal")
    ventas_cat_canal = df_filtrado.groupby(["categoria","canal"])["ingreso"].sum().reset_index()
    fig_stacked = px.bar(
        ventas_cat_canal, x="categoria", y="ingreso", color="canal",
        title="Ingresos por categoría y canal", barmode="stack",
        color_discrete_sequence=[COLOR_PRIMARY, COLOR_BLUE, COLOR_LIGHT]
    )
    st.plotly_chart(fig_stacked, width='stretch')

# ----------------------------------------------------------
# TAB 3: CLIENTES Y GEOGRAFÍA
# ----------------------------------------------------------
with tab3:
    col_cli1, col_cli2 = st.columns([1, 1])

    with col_cli1:
        st.subheader("Top 10 Clientes por Ventas")
        top_clientes = (
            df_filtrado.groupby("nombre_cliente")
            .agg(ventas=("ingreso","sum"), utilidad=("margen","sum"))
            .reset_index().sort_values("ventas", ascending=False).head(10)
        )
        fig_top = px.bar(
            top_clientes, x="ventas", y="nombre_cliente", orientation="h",
            color="utilidad",
            color_continuous_scale=[[0,COLOR_NEGATIVE],[0.5,COLOR_PALE],[1,COLOR_PRIMARY]],
            title="Top 10 clientes (color = utilidad)"
        )
        st.plotly_chart(fig_top, width='stretch')

    with col_cli2:
        st.subheader("Concentración geográfica")
        geo_data = df_filtrado.groupby("pais").agg(
            ventas=("ingreso","sum"), utilidad=("margen","sum")
        ).reset_index()
        _iso3 = {"Colombia":"COL","México":"MEX","Perú":"PER","Chile":"CHL","Argentina":"ARG"}
        geo_data["iso3"] = geo_data["pais"].map(_iso3)
        fig_geo = px.scatter_geo(
            geo_data, locations="iso3", locationmode="ISO-3",
            size="ventas", color="utilidad",
            hover_name="pais",
            color_continuous_scale=SCALE_DIV,
            title="Tamaño = Ventas · Color = Utilidad", projection="natural earth"
        )
        fig_geo.update_geos(
            bgcolor=BG_DARK, landcolor="#1A2535",
            showocean=True, oceancolor="#0A1520",
            showcountries=True, countrycolor="#2A3A4A"
        )
        st.plotly_chart(fig_geo, width='stretch')

    st.subheader("Resumen por País")
    tabla_pais = df_filtrado.groupby("pais").agg(
        Ventas=("ingreso","sum"),
        Utilidad=("margen","sum"),
        Margen_Porc=("margen_pct","mean"),
        Clientes_Unicos=("id_cliente","nunique")
    ).reset_index()
    st.dataframe(
        tabla_pais.style
        .background_gradient(subset=["Ventas"],   cmap="Blues")
        .background_gradient(subset=["Utilidad"], cmap="Blues")
        .format({"Ventas":"${:,.0f}","Utilidad":"${:,.0f}","Margen_Porc":"{:.2%}"}),
        width='stretch'
    )

# ----------------------------------------------------------
# TAB 4: ANÁLISIS AVANZADO
# ----------------------------------------------------------
with tab4:
    st.subheader("Distribución del Margen por Categoría")
    fig_box = px.box(
        df_filtrado, x="categoria", y="margen_pct", color="categoria",
        title="Boxplot de Margen % por Categoría",
        color_discrete_sequence=PALETTE_QUAL
    )
    fig_box.add_hline(y=0, line_dash="dash", line_color=COLOR_NEGATIVE)
    st.plotly_chart(fig_box, width='stretch')

    st.subheader("Clientes: Ventas vs Margen")
    clientes_agg = df_filtrado.groupby("nombre_cliente").agg(
        ventas=("ingreso","sum"), margen=("margen","sum"), num_pedidos=("id_venta","nunique")
    ).reset_index()
    fig_clientes = px.scatter(
        clientes_agg, x="ventas", y="margen", size="num_pedidos",
        hover_name="nombre_cliente", color="margen",
        color_continuous_scale=[[0,COLOR_NEGATIVE],[0.5,COLOR_PALE],[1,COLOR_PRIMARY]],
        title="Clientes: Ventas vs Margen (tamaño = pedidos)"
    )
    fig_clientes.add_hline(y=0, line_dash="dash", line_color=COLOR_NEGATIVE)
    st.plotly_chart(fig_clientes, width='stretch')

    st.subheader("Evolución del Descuento Promedio")
    desc_mes = df_filtrado.groupby("anio_mes")["descuento_pct"].mean().reset_index()
    fig_desc = px.line(
        desc_mes, x="anio_mes", y="descuento_pct", markers=True,
        title="Descuento promedio mensual",
        color_discrete_sequence=[COLOR_WARNING]
    )
    fig_desc.update_layout(yaxis=dict(tickformat=".1%"))
    st.plotly_chart(fig_desc, width='stretch')

    st.subheader("Mapa de Calor: Ventas por Día de la Semana y Canal")
    heat_dia   = df_filtrado.groupby(["dia_semana","canal"])["ingreso"].sum().reset_index()
    heat_pivot = heat_dia.pivot(index="dia_semana", columns="canal", values="ingreso")
    dias_orden = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat_pivot = heat_pivot.reindex(dias_orden)
    fig_dia = px.imshow(
        heat_pivot, text_auto=".2s",
        color_continuous_scale=SCALE_SEQ,
        title="Ingresos por día de la semana y canal"
    )
    st.plotly_chart(fig_dia, width='stretch')

# ----------------------------------------------------------
# TAB 5: ESTRATEGIA COMERCIAL
# ----------------------------------------------------------
with tab5:
    st.header("🎯 Estrategia Comercial")

    col_yoy, col_wf = st.columns([3, 2])

    with col_yoy:
        st.subheader("Comparativo Año a Año (YoY)")
        nombres_meses = ["Ene","Feb","Mar","Abr","May","Jun",
                         "Jul","Ago","Sep","Oct","Nov","Dic"]
        yoy = df_filtrado.groupby(["anio","mes"])["ingreso"].sum().reset_index()
        anios_disponibles = sorted(yoy["anio"].unique())
        colores_anio = [COLOR_PRIMARY, COLOR_LIGHT, COLOR_BLUE]

        fig_yoy = go.Figure()
        for i, anio in enumerate(anios_disponibles):
            datos_anio = yoy[yoy["anio"] == anio].sort_values("mes")
            fig_yoy.add_trace(go.Bar(
                x=datos_anio["mes"], y=datos_anio["ingreso"],
                name=str(anio), marker_color=colores_anio[i % len(colores_anio)]
            ))
        fig_yoy.update_layout(
            barmode="group",
            xaxis=dict(tickmode="array", tickvals=list(range(1,13)), ticktext=nombres_meses),
            yaxis_title="Ingresos USD",
            title="Ingresos mensuales por año",
            legend=dict(orientation="h", x=0, y=1.12), height=380
        )
        st.plotly_chart(fig_yoy, width='stretch')

        if len(anios_disponibles) == 2:
            pivot_yoy = yoy.pivot(index="mes", columns="anio", values="ingreso").reset_index()
            pivot_yoy.columns = ["mes"] + [str(a) for a in anios_disponibles]
            col_a1, col_a2 = str(anios_disponibles[0]), str(anios_disponibles[1])
            pivot_yoy["crecimiento"] = (pivot_yoy[col_a2] - pivot_yoy[col_a1]) / pivot_yoy[col_a1]
            fig_crec = go.Figure(go.Bar(
                x=pivot_yoy["mes"], y=pivot_yoy["crecimiento"],
                marker_color=[COLOR_BLUE if v >= 0 else COLOR_NEGATIVE
                              for v in pivot_yoy["crecimiento"]],
                text=[f"{v:.1%}" for v in pivot_yoy["crecimiento"]],
                textposition="outside"
            ))
            fig_crec.add_hline(y=0, line_dash="dot", line_color=FONT_LIGHT, opacity=0.4)
            fig_crec.update_layout(
                xaxis=dict(tickmode="array", tickvals=list(range(1,13)), ticktext=nombres_meses),
                yaxis=dict(tickformat=".0%"),
                title=f"Crecimiento % mensual ({col_a1} → {col_a2})", height=280
            )
            st.plotly_chart(fig_crec, width='stretch')

    with col_wf:
        st.subheader("Puente Ingreso → Utilidad")
        ingreso_bruto_sum   = (df_filtrado["precio_unitario"] * df_filtrado["cantidad"]).sum()
        descuento_monto_sum = ingreso_bruto_sum - df_filtrado["ingreso"].sum()
        costo_total_sum     = df_filtrado["costo_total"].sum()
        utilidad_neta       = df_filtrado["margen"].sum()

        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","total"],
            x=["Ingreso<br>Bruto","Descuentos<br>Aplicados","Costo de<br>Ventas","Utilidad<br>Neta"],
            y=[ingreso_bruto_sum, -descuento_monto_sum, -costo_total_sum, utilidad_neta],
            text=[f"${ingreso_bruto_sum/1e6:.1f}M", f"-${descuento_monto_sum/1e6:.1f}M",
                  f"-${costo_total_sum/1e6:.1f}M",  f"${utilidad_neta/1e6:.1f}M"],
            textposition="outside",
            increasing=dict(marker=dict(color=COLOR_BLUE)),
            decreasing=dict(marker=dict(color=COLOR_NEGATIVE)),
            totals=dict(marker=dict(color=COLOR_PRIMARY)),
            connector=dict(line=dict(color=COLOR_NEUTRAL, width=2))
        ))
        fig_wf.update_layout(
            title="Descomposición del Resultado (USD)",
            yaxis_title="USD", height=700, showlegend=False
        )
        st.plotly_chart(fig_wf, width='stretch')

    st.markdown("---")

    st.subheader("Análisis de Pareto — Concentración 80/20")
    pareto_por = st.radio(
        "Analizar por:", ["Productos","Clientes"], horizontal=True, key="pareto_tipo"
    )
    if pareto_por == "Productos":
        pareto_df = df_filtrado.groupby("nombre_producto")["ingreso"].sum().reset_index()
        pareto_df.columns = ["nombre","ingreso"]
        titulo_pareto, etiqueta = "Concentración de Ingresos por Producto", "productos"
    else:
        pareto_df = df_filtrado.groupby("nombre_cliente")["ingreso"].sum().reset_index()
        pareto_df.columns = ["nombre","ingreso"]
        titulo_pareto, etiqueta = "Concentración de Ingresos por Cliente", "clientes"

    pareto_df = pareto_df.sort_values("ingreso", ascending=False).reset_index(drop=True)
    pareto_df["cumsum_pct"] = pareto_df["ingreso"].cumsum() / pareto_df["ingreso"].sum()
    pareto_df["rank"] = range(1, len(pareto_df)+1)
    n_80 = int((pareto_df["cumsum_pct"] < 0.80).sum()) + 1
    st.info(f"📌 El **{n_80/len(pareto_df):.1%}** de los {etiqueta} genera el **80 %** de los ingresos "
            f"({n_80} de {len(pareto_df)}).")

    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
    fig_pareto.add_trace(
        go.Bar(x=pareto_df["rank"], y=pareto_df["ingreso"],
               name="Ingreso", marker_color=COLOR_PRIMARY, opacity=0.85),
        secondary_y=False
    )
    fig_pareto.add_trace(
        go.Scatter(x=pareto_df["rank"], y=pareto_df["cumsum_pct"],
                   name="% Acumulado", line=dict(color=COLOR_LIGHT, width=2)),
        secondary_y=True
    )
    fig_pareto.add_hline(y=0.80, line_dash="dash", line_color=COLOR_WARNING,
                         annotation_text="80 %", secondary_y=True)
    fig_pareto.add_vline(x=n_80, line_dash="dash", line_color=COLOR_WARNING,
                         annotation_text=f"Top {n_80}")
    fig_pareto.update_layout(
        title=titulo_pareto, xaxis_title=f"Ranking de {pareto_por}", height=420,
        paper_bgcolor=BG_DARK, plot_bgcolor=BG_CHART
    )
    fig_pareto.update_yaxes(title_text="Ingresos USD", secondary_y=False)
    fig_pareto.update_yaxes(title_text="% Acumulado", tickformat=".0%",
                            range=[0,1.05], secondary_y=True)
    st.plotly_chart(fig_pareto, width='stretch')

    st.markdown("---")

    col_promo, col_rfm_col = st.columns([1, 1])

    with col_promo:
        st.subheader("Efectividad de Promociones")
        promo_resumen = df_filtrado.groupby("es_promocion").agg(
            ingresos=("ingreso","sum"), margen_pct=("margen_pct","mean"),
            transacciones=("id_venta","nunique"), ticket_prom=("ingreso","mean")
        ).reset_index()
        promo_resumen["tipo"] = promo_resumen["es_promocion"].map(
            {True:"Con Promoción", False:"Sin Promoción"}
        )

        fig_promo_kpi = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Margen % Promedio","Ticket Promedio (USD)"]
        )
        for _, row in promo_resumen.iterrows():
            color_b = COLOR_WARNING if row["es_promocion"] else COLOR_PRIMARY
            fig_promo_kpi.add_trace(
                go.Bar(name=row["tipo"], x=[row["tipo"]], y=[row["margen_pct"]],
                       marker_color=color_b, showlegend=False), row=1, col=1)
            fig_promo_kpi.add_trace(
                go.Bar(name=row["tipo"], x=[row["tipo"]], y=[row["ticket_prom"]],
                       marker_color=color_b, showlegend=False), row=1, col=2)
        fig_promo_kpi.update_yaxes(tickformat=".2%", row=1, col=1)
        fig_promo_kpi.update_layout(
            height=320, title="Impacto general de las promociones",
            paper_bgcolor=BG_DARK, plot_bgcolor=BG_CHART
        )
        st.plotly_chart(fig_promo_kpi, width='stretch')

        erosion = df_filtrado.groupby(["categoria","es_promocion"])["margen_pct"].mean().reset_index()
        erosion["tipo"] = erosion["es_promocion"].map({True:"Con Promo", False:"Sin Promo"})
        fig_erosion = px.bar(
            erosion, x="categoria", y="margen_pct", color="tipo", barmode="group",
            color_discrete_map={"Con Promo":COLOR_WARNING,"Sin Promo":COLOR_PRIMARY},
            title="Erosión de Margen por Categoría",
            labels={"margen_pct":"Margen %","categoria":""}
        )
        fig_erosion.update_yaxes(tickformat=".2%")
        fig_erosion.update_layout(height=340, legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig_erosion, width='stretch')

    with col_rfm_col:
        st.subheader("Segmentación RFM de Clientes")
        fecha_ref = df_filtrado["fecha"].max()
        rfm = df_filtrado.groupby("nombre_cliente").agg(
            recencia=("fecha",   lambda x: (fecha_ref - x.max()).days),
            frecuencia=("id_venta","nunique"),
            monetario=("ingreso","sum")
        ).reset_index()

        for col_rfm_name, labels in [
            ("r_score",[5,4,3,2,1]),
            ("f_score",[1,2,3,4,5]),
            ("m_score",[1,2,3,4,5]),
        ]:
            src = ("recencia" if col_rfm_name=="r_score"
                   else "frecuencia" if col_rfm_name=="f_score" else "monetario")
            try:
                rfm[col_rfm_name] = pd.qcut(
                    rfm[src].rank(method="first"), 5,
                    labels=labels, duplicates="drop"
                ).astype(int)
            except Exception:
                rfm[col_rfm_name] = 3

        def segmentar_rfm(row):
            r, f = row["r_score"], row["f_score"]
            if   r>=4 and f>=4: return "Champions"
            elif r>=3 and f>=3: return "Leales"
            elif r>=4 and f<=2: return "Nuevos"
            elif r<=2 and f>=3: return "En Riesgo"
            elif r<=2 and f<=2: return "Perdidos"
            else:               return "Potenciales"

        rfm["segmento"] = rfm.apply(segmentar_rfm, axis=1)
        colores_rfm = {
            "Champions":   COLOR_NAVY,
            "Leales":      COLOR_PRIMARY,
            "Potenciales": COLOR_BLUE,
            "Nuevos":      COLOR_LIGHT,
            "En Riesgo":   COLOR_WARNING,
            "Perdidos":    COLOR_NEGATIVE,
        }

        fig_rfm_scatter = px.scatter(
            rfm, x="recencia", y="frecuencia",
            size="monetario", color="segmento",
            color_discrete_map=colores_rfm,
            hover_name="nombre_cliente",
            hover_data={"monetario":":,.0f","recencia":True,"frecuencia":True},
            title="Mapa RFM: Recencia vs Frecuencia",
            labels={"recencia":"Días desde última compra (↓ mejor)",
                    "frecuencia":"N° de transacciones (↑ mejor)"}
        )
        fig_rfm_scatter.update_layout(height=340, legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig_rfm_scatter, width='stretch')

        seg_dist = (rfm.groupby("segmento")
                    .agg(clientes=("nombre_cliente","count"), monetario_total=("monetario","sum"))
                    .reset_index().sort_values("monetario_total", ascending=False))
        fig_seg = px.bar(
            seg_dist, x="segmento", y="monetario_total",
            color="segmento", color_discrete_map=colores_rfm,
            text="clientes",
            title="Ingresos por Segmento RFM",
            labels={"monetario_total":"Ingresos USD","segmento":""}
        )
        fig_seg.update_traces(texttemplate="%{text} clientes", textposition="outside")
        fig_seg.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_seg, width='stretch')

# ----------------------------------------------------------
# TAB 6: PORTAFOLIO AVANZADO
# ----------------------------------------------------------
with tab6:
    st.header("🔍 Portafolio Avanzado")

    col_abc, col_banda = st.columns([1, 1])

    with col_abc:
        st.subheader("Clasificación ABC de Productos")
        abc_df = (df_filtrado.groupby("nombre_producto")["ingreso"].sum()
                  .reset_index().sort_values("ingreso", ascending=False).reset_index(drop=True))
        abc_df["cumsum_pct"] = abc_df["ingreso"].cumsum() / abc_df["ingreso"].sum()

        def clasificar_abc(pct):
            if pct <= 0.80: return "A — Críticos (80%)"
            elif pct <= 0.95: return "B — Importantes (15%)"
            else:             return "C — Marginales (5%)"

        abc_df["clase"] = abc_df["cumsum_pct"].apply(clasificar_abc)
        abc_df["rank"]  = range(1, len(abc_df)+1)

        fig_abc = px.bar(
            abc_df, x="rank", y="ingreso", color="clase",
            color_discrete_map={
                "A — Críticos (80%)":    COLOR_PRIMARY,
                "B — Importantes (15%)": COLOR_BLUE,
                "C — Marginales (5%)":   COLOR_PALE,
            },
            title="Clasificación ABC por Ingreso",
            labels={"rank":"Ranking Producto","ingreso":"Ingresos USD","clase":"Clase"},
        )
        fig_abc.update_layout(height=380, legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig_abc, width='stretch')

        resumen_abc = abc_df.groupby("clase").agg(
            productos=("nombre_producto","count"), ingresos=("ingreso","sum")
        ).reset_index()
        resumen_abc["% Ingresos"]  = resumen_abc["ingresos"] / resumen_abc["ingresos"].sum()
        resumen_abc["% Productos"] = resumen_abc["productos"] / resumen_abc["productos"].sum()
        st.dataframe(
            resumen_abc
            .rename(columns={"clase":"Clase","productos":"Productos","ingresos":"Ingresos USD"})
            .style
            .format({"Ingresos USD":"${:,.0f}","% Ingresos":"{:.1%}","% Productos":"{:.1%}"})
            .background_gradient(subset=["Ingresos USD"], cmap="Blues"),
            width='stretch'
        )

    with col_banda:
        st.subheader("Rendimiento por Banda de Precio")
        banda_df = df_filtrado.groupby("banda_precio").agg(
            ingresos=("ingreso","sum"), margen_pct=("margen_pct","mean"),
            transacciones=("id_venta","nunique"), ticket=("ingreso","mean"),
        ).reset_index()
        banda_df["banda_precio"] = pd.Categorical(
            banda_df["banda_precio"], categories=["Bajo","Medio","Alto"], ordered=True
        )
        banda_df = banda_df.sort_values("banda_precio")

        fig_banda = make_subplots(
            rows=2, cols=2,
            subplot_titles=["Ingresos Totales","Margen % Promedio","N° Transacciones","Ticket Promedio"]
        )
        colores_banda = [COLOR_PALE, COLOR_BLUE, COLOR_PRIMARY]
        for col_name, es_pct, fila, columna in [
            ("ingresos",False,1,1), ("margen_pct",True,1,2),
            ("transacciones",False,2,1), ("ticket",False,2,2)
        ]:
            fig_banda.add_trace(
                go.Bar(x=banda_df["banda_precio"].astype(str), y=banda_df[col_name],
                       marker_color=colores_banda, showlegend=False,
                       text=[f"{v:.1%}" if es_pct else f"${v:,.0f}" for v in banda_df[col_name]],
                       textposition="outside"),
                row=fila, col=columna
            )
            if es_pct:
                fig_banda.update_yaxes(tickformat=".1%", row=fila, col=columna)
        fig_banda.update_layout(
            height=500, title="KPIs por Banda de Precio",
            paper_bgcolor=BG_DARK, plot_bgcolor=BG_CHART
        )
        st.plotly_chart(fig_banda, width='stretch')

    st.markdown("---")

    st.subheader("Ingresos por Cohorte Mensual")
    st.caption(
        "Cada fila es una cohorte de clientes según su mes de primera compra. "
        "Los valores muestran el **ingreso promedio por cliente** ese mes. "
        "El color más oscuro indica mayor gasto — útil para comparar el valor generado "
        "por cada cohorte a lo largo del tiempo y detectar estacionalidad."
    )

    # Cohorte = mes de primera transacción (strftime evita el bug de Plotly con Period)
    primera_compra = (
        df_filtrado.groupby("id_cliente")["fecha"].min()
        .reset_index().rename(columns={"fecha": "primera_fecha"})
    )
    primera_compra["cohorte"] = primera_compra["primera_fecha"].dt.strftime("%Y-%m")

    cohort_df = df_filtrado.merge(primera_compra[["id_cliente","cohorte"]], on="id_cliente")
    cohort_df["periodo_mes"] = cohort_df["fecha"].dt.strftime("%Y-%m")

    # Calcular índice de período (0 = mes de primera compra)
    cohort_df["cohorte_dt"] = pd.to_datetime(cohort_df["cohorte"])
    cohort_df["periodo_dt"] = pd.to_datetime(cohort_df["periodo_mes"])
    cohort_df["periodo_idx"] = (
        (cohort_df["periodo_dt"].dt.year  - cohort_df["cohorte_dt"].dt.year) * 12
        + (cohort_df["periodo_dt"].dt.month - cohort_df["cohorte_dt"].dt.month)
    )

    # Ingreso promedio por cliente de cada cohorte en cada período
    cohort_rev = (
        cohort_df.groupby(["cohorte","periodo_idx"])
        .agg(ingresos=("ingreso","sum"), clientes=("id_cliente","nunique"))
        .reset_index()
    )
    cohort_rev["ingreso_per_cliente"] = (cohort_rev["ingresos"] / cohort_rev["clientes"]).round(0)

    cohort_pivot = cohort_rev.pivot(
        index="cohorte", columns="periodo_idx", values="ingreso_per_cliente"
    )
    max_periodo = min(11, cohort_pivot.columns.max())
    cohort_pivot = cohort_pivot.loc[:, :max_periodo]
    cohort_pivot.columns = [f"Mes {i}" for i in cohort_pivot.columns]
    cohort_pivot.index.name = "Cohorte"

    fig_cohort = px.imshow(
        cohort_pivot,
        text_auto=".0f",
        color_continuous_scale=SCALE_BLUE,
        title="Ingreso Promedio por Cliente según Cohorte (USD)",
        labels={"x":"Meses desde primera compra","y":"Cohorte","color":"USD / cliente"}
    )
    fig_cohort.update_layout(height=520)
    st.plotly_chart(fig_cohort, width='stretch')

    st.markdown("---")

    col_radar, col_ciudad = st.columns([1, 1])

    with col_radar:
        st.subheader("Radar Comparativo por Marca")

        marcas_agg = df_filtrado.groupby("marca").agg(
            ventas=("ingreso","sum"), margen_pct=("margen_pct","mean"),
            descuento_prom=("descuento_pct","mean"),
            cantidad=("cantidad","sum"), clientes_unicos=("id_cliente","nunique"),
        ).reset_index()

        top_n_marcas = st.slider("Marcas a comparar:", 3, 10, 6, key="radar_n")
        top_marcas   = marcas_agg.nlargest(top_n_marcas, "ventas").copy().reset_index(drop=True)

        for d in ["ventas","margen_pct","cantidad","clientes_unicos"]:
            mn, mx = top_marcas[d].min(), top_marcas[d].max()
            top_marcas[f"{d}_norm"] = ((top_marcas[d]-mn)/(mx-mn)*100) if mx > mn else 50
        mn, mx = top_marcas["descuento_prom"].min(), top_marcas["descuento_prom"].max()
        top_marcas["descuento_norm"] = (
            (1-(top_marcas["descuento_prom"]-mn)/(mx-mn))*100 if mx > mn else 50
        )

        cats_radar = ["Ventas","Margen %","Vol. Unidades","Clientes Únicos","Bajo Descuento"]
        norm_cols  = ["ventas_norm","margen_pct_norm","cantidad_norm",
                      "clientes_unicos_norm","descuento_norm"]

        # Paleta azul-cian con máximo contraste entre tonos
        RADAR_COLORS = [
            "#00D4FF",  # cian brillante
            "#1E90FF",  # dodger blue
            "#0047AB",  # cobalt blue
            "#00BFFF",  # deep sky blue
            "#6495ED",  # cornflower blue
            "#4169E1",  # royal blue
            "#87CEEB",  # sky blue
            "#00CED1",  # dark turquoise
            "#5F9EA0",  # cadet blue
            "#B0E0E6",  # powder blue
        ]

        def hex_rgba(hex_c, alpha):
            h = hex_c.lstrip("#")
            r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
            return f"rgba({r},{g},{b},{alpha})"

        # Selectbox para destacar una marca (simula fade-out del resto)
        lista_marcas = ["Todas"] + list(top_marcas["marca"])
        marca_foco = st.selectbox(
            "Destacar marca:", lista_marcas, key="radar_foco",
            help="Selecciona una marca para resaltarla y opacifar las demás"
        )

        fig_radar = go.Figure()
        for i, marca_row in top_marcas.iterrows():
            es_foco = (marca_foco == "Todas" or marca_row["marca"] == marca_foco)
            color_hex = RADAR_COLORS[i % len(RADAR_COLORS)]
            fill_alpha = 0.40 if es_foco else 0.04
            line_w     = 3    if es_foco else 1
            line_color = color_hex if es_foco else hex_rgba(color_hex, 0.20)

            valores = [marca_row[c] for c in norm_cols] + [marca_row[norm_cols[0]]]
            fig_radar.add_trace(go.Scatterpolar(
                r=valores,
                theta=cats_radar + [cats_radar[0]],
                fill="toself",
                name=marca_row["marca"],
                line=dict(color=line_color, width=line_w),
                fillcolor=hex_rgba(color_hex, fill_alpha),
            ))

        fig_radar.update_layout(
            polar=dict(
                bgcolor=BG_CHART,
                radialaxis=dict(visible=True, range=[0,100],
                                gridcolor=GRID_DARK, linecolor=GRID_DARK,
                                tickfont=dict(color=FONT_LIGHT)),
                angularaxis=dict(gridcolor=GRID_DARK, linecolor=GRID_DARK,
                                 tickfont=dict(color=FONT_LIGHT))
            ),
            title="Comparativo multidimensional de Marcas (0–100 normalizado)",
            legend=dict(orientation="h", y=-0.20, font=dict(color=FONT_LIGHT)),
            height=560
        )
        st.plotly_chart(fig_radar, width='stretch')

    with col_ciudad:
        st.subheader("Top Ciudades por Desempeño")
        ciudad_df = df_filtrado.groupby("ciudad").agg(
            ingresos=("ingreso","sum"), margen_pct=("margen_pct","mean"),
        ).reset_index()

        top_n_ciu = st.slider("Ciudades:", 5, 20, 10, key="ciudad_n")
        top_ciudades = ciudad_df.nlargest(top_n_ciu, "ingresos").sort_values(
            "ingresos", ascending=True
        )

        # Normalizar margen a 0–1 manualmente para usar el rango completo del colorscale
        top_ciudades = top_ciudades.copy()
        m_min = top_ciudades["margen_pct"].min()
        m_max = top_ciudades["margen_pct"].max()
        if m_max > m_min:
            top_ciudades["margen_norm"] = (
                (top_ciudades["margen_pct"] - m_min) / (m_max - m_min)
            )
        else:
            top_ciudades["margen_norm"] = 0.5

        # Etiquetas reales del colorbar en 5 puntos del rango
        n_ticks   = 5
        tick_vals = [i / (n_ticks - 1) for i in range(n_ticks)]
        tick_text = [f"{m_min + t * (m_max - m_min):.2%}" for t in tick_vals]

        fig_ciudad = go.Figure()
        fig_ciudad.add_trace(go.Bar(
            y=top_ciudades["ciudad"],
            x=top_ciudades["ingresos"],
            orientation="h",
            marker=dict(
                # Usar valores normalizados → garantiza que se use todo el espectro
                color=top_ciudades["margen_norm"],
                cmin=0.0,
                cmax=1.0,
                colorscale=[
                    [0.00, "#D6EAF8"],   # azul muy pálido → margen más bajo
                    [0.25, "#85C1E9"],   # azul claro
                    [0.55, "#2471A3"],   # azul medio
                    [1.00, "#0D2137"],   # navy oscuro     → margen más alto
                ],
                colorbar=dict(
                    title="Margen %",
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    tickfont=dict(color=FONT_LIGHT),
                    title_font=dict(color=FONT_LIGHT),
                    thickness=14,
                ),
                showscale=True,
            ),
            text=[f"${v/1e3:.0f}K  |  {m:.2%}"
                  for v, m in zip(top_ciudades["ingresos"], top_ciudades["margen_pct"])],
            textposition="outside",
            textfont=dict(color=FONT_LIGHT),
        ))
        fig_ciudad.update_layout(
            title="Ingresos por Ciudad (color = Margen %)",
            xaxis_title="Ingresos USD",
            height=560, margin=dict(r=90)
        )
        st.plotly_chart(fig_ciudad, width='stretch')
