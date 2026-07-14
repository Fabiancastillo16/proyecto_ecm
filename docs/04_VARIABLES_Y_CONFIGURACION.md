# 04 — Variables y configuración

Referencia exacta de cada variable de entorno, secreto, y ruta de archivo
que usa el proyecto: qué hace, dónde se define, y si es obligatoria.

---

## 1. Variables de entorno / secretos

| Variable | Obligatoria | Dónde se define (local) | Dónde se define (nube) | Ejemplo | Descripción |
|---|---|---|---|---|---|
| `SIS2_USERNAME` | Sí | `.env` | Secreto de Container Apps (`sis2-username`) | `r120fc42` | Usuario para el login automático en SIS2 |
| `SIS2_PASSWORD` | Sí | `.env` | Secreto de Container Apps (`sis2-password`) | `********` | Contraseña para el login automático |
| `ADLS_STORAGE_ACCOUNT` | No* | No se define (modo local no usa ADLS) | Variable de entorno | `dvbigdataikc2dlkacc` | Nombre del storage account de ADLS Gen2 |
| `ADLS_FILESYSTEM` | No* | No se define | Variable de entorno | `dvbigdataikc2dlkfs` | Nombre del filesystem/container dentro del storage account |
| `ADLS_INPUT_DIRECTORY` | No* | No se define | Variable de entorno | `data/ECM Report Project/Equipos` | Carpeta donde el proyecto busca los `.csv` con la lista de equipos a consultar |
| `ADLS_OUTPUT_DIRECTORY` | No* | No se define | Variable de entorno | `data/ECM Report Project` | Carpeta donde el proyecto sube el CSV de resultado |
| `ADLS_ACCOUNT_KEY` | No** | No se define | Secreto de Container Apps (`adls-key`) | `********` | Clave de acceso del storage account, para autenticar sin identidad administrada (ver `02_ARQUITECTURA_SOLUCION.md`, sección 5) |

\* Si `ADLS_STORAGE_ACCOUNT` o `ADLS_FILESYSTEM` no están definidas, el
proyecto opera en "modo local": lee `Equipos.csv` del repo y escribe en
`Results/resultado_sis2.csv`, ignorando `ADLS_INPUT_DIRECTORY` y
`ADLS_OUTPUT_DIRECTORY` aunque estén definidas.

\** Si `ADLS_ACCOUNT_KEY` no está definida pero sí las variables de storage
account/filesystem, el código intenta autenticar con identidad administrada
(`DefaultAzureCredential`) en su lugar — ver sección 5 de
`02_ARQUITECTURA_SOLUCION.md` para cuándo usar cada modo.

## 2. Constantes de código (requieren rebuild para cambiar)

Estas no son variables de entorno — son valores fijos dentro de
`ServiceSoftwareFiles.py`. Cambiarlas implica editar el código y volver a
construir/subir la imagen (ver Manual de Usuario, sección 6).

| Constante | Archivo | Valor actual | Qué controla |
|---|---|---|---|
| `MAX_WORKERS` | `ServiceSoftwareFiles.py` | `8` | Cantidad de consultas simultáneas a la API de SIS2. Súbelo con cuidado (riesgo de 429/bloqueo); bájalo si ves errores de rate limit |
| `REQUEST_DELAY` | `ServiceSoftwareFiles.py` | `0.15` (segundos) | Pequeña pausa entre requests de cada thread, para no saturar la API |
| `BASE_URL` | `ServiceSoftwareFiles.py` | `https://sis2.cat.com/api/ws-all/ServiceSoftwareFilesRemoteServices/serialNumber` | Endpoint de la API que se consulta. Solo cambiaría si Cat modifica su API |
| `AUTH_PATH` | `ServiceSoftwareFiles.py` | `Authentication/auth.json` | Ruta donde se guarda/lee el token de sesión |

## 3. Rutas de archivos (modo local)

| Archivo | Ruta | Descripción |
|---|---|---|
| Entrada (equipos a consultar) | `Equipos.csv` (raíz del repo) | Columna requerida: `SerialNumber` |
| Credenciales | `.env` (raíz del repo, gitignored) | Ver `.env.example` para el formato |
| Token de sesión generado | `Authentication/auth.json` (gitignored) | Se regenera automáticamente si no existe o expiró |
| Captura de depuración (si falla el login) | `Authentication/login_debug.png` (gitignored) | Solo se genera si el login tarda más de 60s sin completar |
| Resultado | `Results/resultado_sis2.csv` | Se sobreescribe en cada corrida |

## 4. Rutas de archivos (modo nube — ADLS Gen2)

Dentro del storage account `dvbigdataikc2dlkacc`, filesystem
`dvbigdataikc2dlkfs`:

```
data/
└── ECM Report Project/
    ├── Equipos/
    │   └── *.csv          ← ADLS_INPUT_DIRECTORY (uno o más archivos, generados por una query externa)
    └── resultado_sis2.csv ← ADLS_OUTPUT_DIRECTORY (nombre = mismo nombre del archivo local)
```

**Nota:** si en `ADLS_INPUT_DIRECTORY` hay más de un `.csv`, el proyecto
los descarga todos, los concatena, y quita duplicados por la columna
`SerialNumber` — así que no hay problema si la query externa genera
archivos particionados o versiones incrementales, siempre que todos
compartan esa columna.

## 5. Comandos rápidos para modificar configuración en la nube

```powershell
# Cambiar una variable de entorno (no secreta)
az containerapp job update --name job-sis2-extraccion --resource-group dv-bigdataikc-rg `
  --set-env-vars "ADLS_INPUT_DIRECTORY=data/ECM Report Project/Equipos"

# Cambiar un secreto (usuario, password, o la clave de ADLS)
az containerapp job update --name job-sis2-extraccion --resource-group dv-bigdataikc-rg `
  --secrets "sis2-password=NUEVA_PASSWORD"

# Cambiar la frecuencia del cron
az containerapp job update --name job-sis2-extraccion --resource-group dv-bigdataikc-rg `
  --cron-expression "0 */6 * * *"

# Ver la configuración actual completa
az containerapp job show --name job-sis2-extraccion --resource-group dv-bigdataikc-rg -o json
```
