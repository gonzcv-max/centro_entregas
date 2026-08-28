"""
Motor de reportes: replica las 6 tablas dinámicas que traía el Excel
original (Resumen Transportista, Resumen Volúmenes Nombre Comercial,
Resumen por Operador, Resumen por Unidad, Resumen Detallado y Resumen
por Producto), usando las mismas fórmulas que tenían definidas como
"campos calculados" en el archivo:

    Diferencia   = SUM(Volumen Descargado) - SUM(Volumen Cargado)
    % Diferencia = IFERROR(Diferencia / SUM(Volumen Cargado), 0)
    Conteo de Viajes = COUNT(No. Bol)

Estas funciones reciben el DataFrame ya limpio de utils.data_manager
(con columnas internas: producto, nombre_comercial, transportista,
unidad, operador, fecha_carga, volumen_cargado, volumen_descargado, ...).
"""

from __future__ import annotations

import pandas as pd


def _agg_base(df: pd.DataFrame, by) -> pd.DataFrame:
    g = df.groupby(by, dropna=False)
    out = g.agg(
        viajes=("no_bol", "count"),
        volumen_cargado=("volumen_cargado", "sum"),
        volumen_descargado=("volumen_descargado", "sum"),
    ).reset_index()
    out["diferencia"] = out["volumen_descargado"] - out["volumen_cargado"]
    out["pct_diferencia"] = (out["diferencia"] / out["volumen_cargado"]).where(
        out["volumen_cargado"] != 0, 0
    )
    return out


def resumen_por_transportista(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_base(df, "transportista")
    out = out.rename(columns={"transportista": "Transportista"})
    return out.sort_values("volumen_cargado", ascending=False).reset_index(drop=True)


def resumen_por_nombre_comercial(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_base(df, "nombre_comercial")
    out = out.rename(columns={"nombre_comercial": "Nombre Comercial"})
    return out.sort_values("volumen_cargado", ascending=False).reset_index(drop=True)


def resumen_por_operador(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_base(df, "operador")
    out = out.rename(columns={"operador": "Operador"})
    return out.sort_values("volumen_cargado", ascending=False).reset_index(drop=True)


def resumen_por_unidad(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_base(df, "unidad")
    out = out.rename(columns={"unidad": "Unidad"})
    return out.sort_values("volumen_cargado", ascending=False).reset_index(drop=True)


def resumen_por_producto(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_base(df, "producto")
    out = out.rename(columns={"producto": "Producto"})
    return out.sort_values("volumen_cargado", ascending=False).reset_index(drop=True)


def resumen_detallado(df: pd.DataFrame) -> pd.DataFrame:
    """Igual que la hoja 'Resumen Detallado' original: agrupado de forma
    anidada por Nombre Comercial > Transportista > Fecha Carga."""
    out = _agg_base(df, ["nombre_comercial", "transportista", "fecha_carga"])
    out = out.rename(
        columns={
            "nombre_comercial": "Nombre Comercial",
            "transportista": "Transportista",
            "fecha_carga": "Fecha Carga",
        }
    )
    return out.sort_values(["Nombre Comercial", "Transportista", "Fecha Carga"]).reset_index(drop=True)


# Nombres "bonitos" de columnas comunes a todos los reportes anteriores
COLUMNAS_REPORTE = {
    "viajes": "Conteo de Viajes",
    "volumen_cargado": "Suma de Volumen Cargado",
    "volumen_descargado": "Suma de Volumen Descargado",
    "diferencia": "Diferencia (Desc. - Carg.)",
    "pct_diferencia": "% de Diferencia",
}


def _renombrar(out: pd.DataFrame) -> pd.DataFrame:
    return out.rename(columns=COLUMNAS_REPORTE)


REPORTES = {
    "Resumen por Producto": resumen_por_producto,
    "Resumen Transportista": resumen_por_transportista,
    "Resumen Volúmenes Nombre Comerc": resumen_por_nombre_comercial,
    "Resumen por Operador": resumen_por_operador,
    "Resumen por Unidad": resumen_por_unidad,
    "Resumen Detallado": resumen_detallado,
}


def generar_todos_los_reportes(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Regresa {nombre_hoja: dataframe_formateado} listo para escribirse
    a Excel o mostrarse en Streamlit."""
    resultado = {}
    for nombre, func in REPORTES.items():
        resultado[nombre] = _renombrar(func(df))
    return resultado
