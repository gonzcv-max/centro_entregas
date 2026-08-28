"""
Base de Datos — altas, bajas y cambios sobre la Base Datos Entregas del
archivo activo del centro.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import data_manager as dm
from utils import github_sync as gh

st.set_page_config(page_title="Base de Datos", page_icon="📋", layout="wide")
st.title("📋 Base de Datos de Entregas")

centros = dm.list_centros()
if not centros:
    st.warning("No hay archivos en el centro todavía. Ve a la página principal para subir uno.")
    st.stop()

actual = st.session_state.get("centro_activo", centros[0])
seleccionado = st.selectbox("Archivo del centro", centros, index=centros.index(actual) if actual in centros else 0)
st.session_state["centro_activo"] = seleccionado

# Se recarga desde disco solo si cambiamos de archivo o aún no se ha cargado
if st.session_state.get("_bd_archivo_cargado") != seleccionado:
    st.session_state["bd_df"] = dm.load_centro(seleccionado)
    st.session_state["_bd_archivo_cargado"] = seleccionado

df = st.session_state["bd_df"]

st.caption(
    "Agrega filas nuevas (altas), bórralas (bajas) o edita cualquier celda "
    "(cambios) directamente en la tabla. Los campos Diferencia, Sobrante, "
    "Merma, % de Diferencia y Estatus se recalculan solos."
)

# columnas que se pueden editar directamente; las calculadas quedan de solo lectura
CALCULADAS = {"diferencia", "sobrante", "merma", "pct_diferencia", "estatus"}

column_config = {
    "id": None,  # se oculta
    "fecha_carga": st.column_config.DateColumn("Fecha Carga", format="DD/MM/YYYY"),
    "volumen_cargado": st.column_config.NumberColumn("Volumen Cargado", format="%.0f"),
    "volumen_descargado": st.column_config.NumberColumn("Volumen Descargado", format="%.0f"),
    "capacidad_unidad": st.column_config.NumberColumn("Capacidad Unidad", format="%.0f"),
    "diferencia": st.column_config.NumberColumn("Diferencia", format="%.0f", disabled=True),
    "sobrante": st.column_config.NumberColumn("Sobrante", format="%.0f", disabled=True),
    "merma": st.column_config.NumberColumn("Merma", format="%.0f", disabled=True),
    "pct_diferencia": st.column_config.NumberColumn("% Diferencia", format="percent", disabled=True),
    "estatus": st.column_config.TextColumn("Estatus", disabled=True),
    "no_bol": st.column_config.NumberColumn("No. Bol", format="%d"),
}
for c, label in dm.COLUMN_LABELS.items():
    column_config.setdefault(c, label)

editado = st.data_editor(
    df,
    column_config=column_config,
    num_rows="dynamic",
    width="stretch",
    height=520,
    key="editor_base_datos",
)

col_a, col_b, col_c = st.columns([1, 1, 2])

with col_a:
    if st.button("💾 Guardar cambios", type="primary", width="stretch"):
        limpio = editado.drop(columns=["id"], errors="ignore").reset_index(drop=True)
        errores = dm.validar_dataframe(limpio)
        if errores:
            st.error("No se guardó nada. Corrige lo siguiente:")
            for e in errores:
                st.write(f"- {e}")
        else:
            avisos = dm.advertencias_dataframe(limpio)
            if avisos:
                with st.expander(f"⚠️ {len(avisos)} advertencia(s) — se guardó de todas formas"):
                    for a in avisos:
                        st.write(f"- {a}")

            recalculado = dm.recalcular(limpio)
            dm.guardar_centro(seleccionado, recalculado)
            st.session_state["bd_df"] = dm.load_centro(seleccionado)

            if gh.esta_configurado():
                data_bytes = dm.to_excel_bytes(recalculado)
                ok, msg = gh.subir_cambios(
                    f"data/{seleccionado}", data_bytes,
                    f"Actualiza {seleccionado} desde la app"
                )
                (st.success if ok else st.warning)(msg)

            st.success(f"Cambios guardados en '{seleccionado}'.")
            st.rerun()

with col_b:
    if st.button("↩️ Descartar cambios", width="stretch"):
        st.session_state["bd_df"] = dm.load_centro(seleccionado)
        st.rerun()

with col_c:
    st.download_button(
        "⬇️ Descargar Excel actualizado",
        data=dm.to_excel_bytes(editado.drop(columns=["id"], errors="ignore")),
        file_name=seleccionado,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

st.caption(
    "Tip: para dar de **alta** un registro, usa el '+' al final de la tabla. "
    "Para dar de **baja**, selecciona la fila (checkbox a la izquierda) y presiona la tecla Supr/Delete. "
    "Cualquier celda se puede editar con doble clic."
)
