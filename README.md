# Centro de Entregas y Mermas

App en Streamlit para dar de alta, editar, dar de baja y consultar los
registros de entrega/recepción y mermas de producto que antes vivían
solo en Excel — y para tener varios Excel (uno por semestre, planta o
sucursal) reunidos en un mismo "centro".

## Qué hace

- **Home / Centro**: elige con qué Excel trabajar, o sube uno nuevo al centro.
- **Base de Datos**: tabla editable (altas, bajas y cambios) sobre la hoja
  `Base Datos Entregas`. Diferencia, Sobrante, Merma, % de Diferencia y
  Estatus se recalculan automáticamente. Se puede guardar y/o descargar el
  Excel actualizado en cualquier momento.
- **Reportes**: recrea los 6 reportes que traía el Excel original
  (Resumen por Producto, por Transportista, por Nombre Comercial, por
  Operador, por Unidad y el Detallado), filtrables por rango de fecha.
- **Dashboard**: filtros libres (producto, transportista, operador, unidad,
  fecha) con KPIs y gráficas.

Cada archivo del centro vive en la carpeta `data/`. El repo ya incluye
`data/H2_2026_Ejemplo.xlsx` con tu archivo actual como punto de partida.

## Correr en tu computadora

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`.

## Subir a GitHub

```bash
git init
git add .
git commit -m "Centro de Entregas y Mermas"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
git push -u origin main
```

## Publicar en Streamlit Community Cloud (streamlit.app)

1. Entra a [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.
2. "New app" → elige el repo y la rama `main` → archivo principal `app.py`.
3. Deploy. En unos minutos tendrás una URL tipo `https://<tu-app>.streamlit.app`.

## ⚠️ Importante: persistencia de los cambios

Streamlit Community Cloud usa un **sistema de archivos efímero**: cuando el
contenedor de tu app se reinicia (se "duerme" por inactividad, haces un
nuevo deploy, etc.), vuelve a crearse desde el último commit en GitHub. Eso
significa que un cambio guardado en `data/archivo.xlsx` **sólo vive
mientras el contenedor actual siga corriendo** — si se reinicia, se pierde,
a menos que actives una de estas dos opciones:

### Opción A — Descargar y volver a subir (más simple)

Después de editar, usa el botón "⬇️ Descargar Excel actualizado" y guarda
el archivo tú mismo. Si necesitas que el cambio quede en el repo, vuelve a
subirlo desde la Home ("2. o sube uno nuevo") o haz commit manual a GitHub.

### Opción B — Guardado automático a GitHub (recomendado para uso en equipo)

La app puede hacer commit del Excel actualizado directo al repositorio
cada vez que alguien presiona "Guardar cambios", así los cambios sobreviven
cualquier reinicio.

1. Crea un [Personal Access Token](https://github.com/settings/tokens) de
   GitHub con permiso `repo` (o "Contents: Read and write" si usas un
   fine-grained token).
2. En Streamlit Cloud: abre tu app → **Settings → Secrets** y pega:

   ```toml
   GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
   GITHUB_REPO = "tu-usuario/tu-repo"
   GITHUB_BRANCH = "main"
   ```

   (En local, copia `.streamlit/secrets.toml.example` a
   `.streamlit/secrets.toml` y llena los mismos valores — ese archivo
   nunca se sube a GitHub, ya está en `.gitignore`.)
3. Listo: cada "Guardar cambios" en la Base de Datos hará commit
   automático de `data/<archivo>.xlsx` al repo.

## Estructura del proyecto

```
app.py                          # Home / selector del centro
pages/
  1_📋_Base_de_Datos.py         # altas, bajas, cambios
  2_📊_Reportes.py              # los 6 reportes originales, filtrables por fecha
  3_📈_Dashboard.py             # filtros libres + gráficas + KPIs
utils/
  data_manager.py               # carga/guarda Excel, validaciones, "centro" multi-archivo
  reports.py                    # replica las fórmulas de las 6 tablas dinámicas originales
  github_sync.py                # persistencia opcional a GitHub
data/                           # aquí viven los Excel del centro (se pueden agregar más)
.streamlit/
  config.toml                   # tema visual
  secrets.toml.example          # plantilla de configuración de GitHub
```

## Agregar más archivos al centro

Cada Excel que subas desde la Home debe tener una hoja llamada
`Base Datos Entregas` con estas columnas (los nombres se limpian
automáticamente, no importan mayúsculas/espacios extra):

`No. Bol, Producto, Nombre Comercial, Compartida, Fecha Carga,
Transportista, Unidad, Capacidad Unidad, Volumen Cargado,
Volumen Descargado, Operador, Terminal de Carga`

Las columnas de Sobrante, Merma y % de Diferencia se recalculan solas —
no hace falta traerlas ya resueltas.
