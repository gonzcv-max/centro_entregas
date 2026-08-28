"""
Reportes — recrea los 6 reportes que traía el Excel original (antes como
tablas dinámicas vacías), calculados en vivo y filtrables por fecha.
"""

from __future__ import annotations

import streamlit as st

from utils import data_manager as dm
from utils import reports as rpt

st.set_page_config(page_title="Reportes", page_icon="📊", layout="wide")
st.title("📊 Reportes")

centros = dm.list_centros()
if not centros:
    st.warning("No hay archivos en el centro todavía. Ve a la página principal para subir uno.")
    st.stop()

actual = st.session_state.get("centro_activo", centros[0])
seleccionado = st.selectbox("Archivo del centro", centros, index=centros.index(actual) if actual in centros else 0)
st.session_state["centro_activo"] = seleccionado

df = dm.load_centro(seleccionado)

# --------------------------------------------------------------------------- #
# Filtro de fechas (los reportes por fecha eran justo lo que traían las
# hojas de ejemplo del Excel original)
# --------------------------------------------------------------------------- #

fechas_validas = df["fecha_carga"].dropna()
if not fechas_validas.empty:
    fmin, fmax = fechas_validas.min().date(), fechas_validas.max().date()
    rango = st.date_input("Rango de Fecha Carga", value=(fmin, fmax), min_value=fmin, max_value=fmax)
    if isinstance(rango, tuple) and len(rango) == 2:
        desde, hasta = rango
        en_rango = (df["fecha_carga"].dt.date >= desde) & (df["fecha_carga"].dt.date <= hasta)
        df = df[en_rango]

st.caption(f"{len(df):,} registros en el rango seleccionado.")
st.divider()

reportes = rpt.generar_todos_los_reportes(df)

tabs = st.tabs(list(reportes.keys()))
for tab, (nombre, tabla) in zip(tabs, reportes.items()):
    with tab:
        st.subheader(nombre)
        st.dataframe(tabla, width="stretch", height=420)
        st.download_button(
            f"⬇️ Descargar '{nombre}' (CSV)",
            data=tabla.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{nombre}.csv",
            mime="text/csv",
            key=f"dl_{nombre}",
        )

st.divider()
st.download_button(
    "⬇️ Descargar Excel del rango filtrado (Base + los 6 reportes)",
    data=dm.to_excel_bytes(df),
    file_name=f"reportes_{seleccionado}",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
