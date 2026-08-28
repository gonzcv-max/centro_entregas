"""
Centro de Entregas y Mermas — Home

Portada del "centro": permite elegir con qué archivo Excel se va a trabajar
(cada archivo es una base independiente, por ejemplo un semestre o una
sucursal distinta), subir uno nuevo al centro, y ver un vistazo rápido de
sus KPIs antes de entrar a Base de Datos o Reportes.
"""

from __future__ import annotations

import streamlit as st

from utils import data_manager as dm
from utils import github_sync as gh

st.set_page_config(
    page_title="Centro de Entregas y Mermas",
    page_icon="🚛",
    layout="wide",
)

st.title("🚛 Centro de Entregas y Mermas")
st.caption(
    "Un solo lugar para dar de alta, editar y consultar los registros de "
    "entrega/recepción y mermas de producto de todos tus archivos Excel."
)

if not gh.esta_configurado():
    st.info(
        "ℹ️ La sincronización automática a GitHub no está configurada todavía. "
        "La app funciona igual, pero los cambios solo persisten mientras esta "
        "sesión siga corriendo — descarga el Excel cuando termines de editar, "
        "o revisa el README para activar el guardado automático a GitHub.",
        icon="ℹ️",
    )

st.divider()

# --------------------------------------------------------------------------- #
# Selección del archivo activo del centro
# --------------------------------------------------------------------------- #

centros = dm.list_centros()

col_sel, col_upload = st.columns([2, 1])

with col_sel:
    st.subheader("1. Elige el archivo con el que quieres trabajar")
    if centros:
        actual = st.session_state.get("centro_activo")
        index = centros.index(actual) if actual in centros else 0
        seleccionado = st.selectbox(
            "Archivos disponibles en el centro",
            centros,
            index=index,
            label_visibility="collapsed",
        )
        st.session_state["centro_activo"] = seleccionado
    else:
        st.warning("Todavía no hay ningún archivo en el centro. Sube uno con el panel de la derecha →")
        seleccionado = None

with col_upload:
    st.subheader("2. o sube uno nuevo")
    nuevo = st.file_uploader("Agregar Excel al centro", type=["xlsx"], label_visibility="collapsed")
    if nuevo is not None:
        try:
            nombre_final = dm.guardar_nuevo_centro(nuevo.name, nuevo.getvalue())
            st.success(f"'{nombre_final}' agregado al centro.")
            st.session_state["centro_activo"] = nombre_final
            st.rerun()
        except dm.CentroError as e:
            st.error(str(e))

st.divider()

# --------------------------------------------------------------------------- #
# Vistazo rápido del archivo activo
# --------------------------------------------------------------------------- #

if seleccionado:
    try:
        df = dm.load_centro(seleccionado)
    except dm.CentroError as e:
        st.error(str(e))
        st.stop()

    st.subheader(f"Vistazo rápido — {seleccionado}")

    total_viajes = len(df)
    total_cargado = df["volumen_cargado"].sum()
    total_descargado = df["volumen_descargado"].sum()
    diferencia_total = df["diferencia"].sum()
    pendientes = (df["estatus"] == "Pendiente de descarga").sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Viajes", f"{total_viajes:,}")
    c2.metric("Volumen cargado", f"{total_cargado:,.0f} L")
    c3.metric("Volumen descargado", f"{total_descargado:,.0f} L")
    c4.metric("Diferencia neta", f"{diferencia_total:,.0f} L")
    c5.metric("Pendientes de descarga", f"{pendientes:,}")

    if df["fecha_carga"].notna().any():
        st.caption(
            f"Rango de fechas: {df['fecha_carga'].min():%d/%m/%Y} — "
            f"{df['fecha_carga'].max():%d/%m/%Y}"
        )

    st.dataframe(df.drop(columns=["id"]).head(20), width="stretch", height=350)

    st.page_link("pages/1_📋_Base_de_Datos.py", label="➡️ Ir a Base de Datos (altas / bajas / cambios)")
    st.page_link("pages/2_📊_Reportes.py", label="➡️ Ir a Reportes")
    st.page_link("pages/3_📈_Dashboard.py", label="➡️ Ir a Dashboard")
