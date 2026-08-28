"""
Persistencia opcional a GitHub.

Streamlit Community Cloud usa un sistema de archivos EFÍMERO: si guardas un
cambio en data/archivo.xlsx y el contenedor se reinicia (se duerme la app,
se hace un nuevo deploy, etc.), ese cambio se pierde porque el contenedor
se vuelve a crear desde el último commit en GitHub.

Para que los cambios del "centro" sobrevivan, esta app puede -si se le
configuran credenciales- hacer commit automático del Excel actualizado
directo al repositorio cada vez que alguien guarda cambios.

Configuración (en .streamlit/secrets.toml o en "Secrets" de Streamlit Cloud):

    GITHUB_TOKEN  = "ghp_xxxxx"        # Personal Access Token con permiso 'repo'
    GITHUB_REPO   = "usuario/repo"
    GITHUB_BRANCH = "main"

Si estas llaves no existen, la función `esta_configurado()` regresa False
y la app simplemente no intenta sincronizar (los cambios sólo viven
mientras el contenedor actual siga corriendo, y siempre se puede descargar
el Excel manualmente).
"""

from __future__ import annotations

import streamlit as st


def esta_configurado() -> bool:
    try:
        return bool(
            st.secrets.get("GITHUB_TOKEN")
            and st.secrets.get("GITHUB_REPO")
        )
    except Exception:  # noqa: BLE001 - st.secrets lanza si no hay secrets.toml
        return False


def subir_cambios(path_relativo: str, contenido: bytes, mensaje: str) -> tuple[bool, str]:
    """Sube/actualiza un archivo binario en el repo configurado.

    Regresa (ok, mensaje_para_mostrar).
    """
    if not esta_configurado():
        return False, "GitHub no está configurado (falta GITHUB_TOKEN / GITHUB_REPO en secrets)."

    try:
        from github import Github, InputGitAuthor  # PyGithub
    except ImportError:
        return False, "Falta instalar PyGithub (agrega 'PyGithub' a requirements.txt)."

    try:
        gh = Github(st.secrets["GITHUB_TOKEN"])
        repo = gh.get_repo(st.secrets["GITHUB_REPO"])
        branch = st.secrets.get("GITHUB_BRANCH", "main")

        try:
            existing = repo.get_contents(path_relativo, ref=branch)
            repo.update_file(
                path_relativo, mensaje, contenido, existing.sha, branch=branch
            )
        except Exception:
            # no existía todavía -> lo creamos
            repo.create_file(path_relativo, mensaje, contenido, branch=branch)

        return True, f"Cambios sincronizados a GitHub ({st.secrets['GITHUB_REPO']}@{branch})."
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo sincronizar a GitHub: {exc}"
