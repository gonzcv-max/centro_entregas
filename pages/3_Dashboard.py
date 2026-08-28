"""
Dashboard — filtros libres (producto, transportista, operador, unidad,
fecha) + gráficas y KPIs, para explorar la base más allá de los 6 reportes
fijos.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils import data_manager as dm

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
st.title("📈 Dashboard")

centros = dm.list_centros()
if not centros:
    st.warning("No hay archivos en el centro todavía. Ve a la página principal para subir uno.")
    st.stop()

actual = st.session_state.get("centro_activo", centros[0])
seleccionado = st.selectbox("Archivo del centro", centros, index=centros.index(actual) if actual in centros else 0)
st.session_state["centro_activo"] = seleccionado

df = dm.load_centro(seleccionado)

# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #

with st.expander("Filtros", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    productos = c1.multiselect("Producto", sorted(df["producto"].dropna().unique()))
    transportistas = c2.multiselect("Transportista", sorted(df["transportista"].dropna().unique()))
    operadores = c3.multiselect("Operador", sorted(df["operador"].dropna().unique()))
    unidades = c4.multiselect("Unidad", sorted(df["unidad"].dropna().unique()))

    fechas_validas = df["fecha_carga"].dropna()
    if not fechas_validas.empty:
        fmin, fmax = fechas_validas.min().date(), fechas_validas.max().date()
        rango = st.date_input("Rango de Fecha Carga", value=(fmin, fmax), min_value=fmin, max_value=fmax)
    else:
        rango = None

filtrado = df.copy()
if productos:
    filtrado = filtrado[filtrado["producto"].isin(productos)]
if transportistas:
    filtrado = filtrado[filtrado["transportista"].isin(transportistas)]
if operadores:
    filtrado = filtrado[filtrado["operador"].isin(operadores)]
if unidades:
    filtrado = filtrado[filtrado["unidad"].isin(unidades)]
if isinstance(rango, tuple) and len(rango) == 2:
    desde, hasta = rango
    filtrado = filtrado[(filtrado["fecha_carga"].dt.date >= desde) & (filtrado["fecha_carga"].dt.date <= hasta)]

st.caption(f"{len(filtrado):,} de {len(df):,} registros con los filtros actuales.")
st.divider()

# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #

cargado = filtrado["volumen_cargado"].sum()
descargado = filtrado["volumen_descargado"].sum()
diferencia = filtrado["diferencia"].sum()
pct = (diferencia / cargado) if cargado else 0
viajes = len(filtrado)
pendientes = (filtrado["estatus"] == "Pendiente de descarga").sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Viajes", f"{viajes:,}")
k2.metric("Volumen cargado", f"{cargado:,.0f} L")
k3.metric("Volumen descargado", f"{descargado:,.0f} L")
k4.metric("Diferencia neta", f"{diferencia:,.0f} L", delta=f"{pct:.2%}")
k5.metric("Pendientes de descarga", f"{pendientes:,}")

st.divider()

# --------------------------------------------------------------------------- #
# Gráficas
# --------------------------------------------------------------------------- #

g1, g2 = st.columns(2)

with g1:
    st.subheader("Volumen cargado vs. descargado por producto")
    por_producto = (
        filtrado.groupby("producto", dropna=False)[["volumen_cargado", "volumen_descargado"]]
        .sum()
        .reset_index()
        .melt(id_vars="producto", var_name="tipo", value_name="volumen")
    )
    fig = px.bar(por_producto, x="producto", y="volumen", color="tipo", barmode="group")
    st.plotly_chart(fig, width="stretch")

with g2:
    st.subheader("Diferencia (merma/sobrante) por transportista")
    por_transportista = (
        filtrado.groupby("transportista", dropna=False)["diferencia"].sum().reset_index()
        .sort_values("diferencia")
    )
    fig = px.bar(
        por_transportista, x="diferencia", y="transportista", orientation="h",
        color="diferencia", color_continuous_scale="RdYlGn",
    )
    st.plotly_chart(fig, width="stretch")

g3, g4 = st.columns(2)

with g3:
    st.subheader("Volumen cargado a lo largo del tiempo")
    if filtrado["fecha_carga"].notna().any():
        por_dia = (
            filtrado.dropna(subset=["fecha_carga"])
            .groupby(filtrado["fecha_carga"].dt.to_period("W").dt.start_time)[["volumen_cargado", "volumen_descargado"]]
            .sum()
            .reset_index()
        )
        fig = px.line(por_dia, x="fecha_carga", y=["volumen_cargado", "volumen_descargado"], markers=True)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No hay fechas válidas en los datos filtrados.")

with g4:
    st.subheader("Viajes por operador (top 15)")
    por_operador = (
        filtrado.groupby("operador", dropna=False)["no_bol"].count().reset_index(name="viajes")
        .sort_values("viajes", ascending=False).head(15)
    )
    fig = px.bar(por_operador, x="viajes", y="operador", orientation="h")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

st.divider()
with st.expander("Ver tabla filtrada"):
    st.dataframe(filtrado.drop(columns=["id"]), width="stretch", height=400)
