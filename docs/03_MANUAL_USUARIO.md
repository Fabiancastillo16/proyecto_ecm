# 03 — Manual de usuario

Guía práctica para operar el proyecto: qué instalar, cómo correrlo, cómo
cambiar cualquier configuración, y qué hacer si algo falla.

---

## 1. Requisitos de software

| Programa | Para qué | Notas |
|---|---|---|
| **Python 3.10+** | Correr el proyecto localmente sin Docker | En Windows sin permisos de administrador, puedes instalarlo en modo usuario o usar una versión ya instalada por IT |
| **pip** | Instalar dependencias de Python | Viene con Python |
| **Docker Desktop** | Construir y correr la imagen del proyecto en contenedor | Necesita el backend de WSL2 en Windows (viene activado por defecto en instalaciones recientes) |
| **Azure CLI (`az`)** | Desplegar y administrar recursos en Azure | Si no tienes permisos de administrador, instálalo con `pip install azure-cli` (ver sección 9.6) |
| **VS Code** (o cualquier editor) | Editar el código del proyecto | Cualquier editor de texto sirve, VS Code es solo la recomendación |
| **Git** | Clonar/actualizar el repositorio, control de versiones | — |

## 2. Primeros pasos (configuración inicial)

1. Clona o descarga el repositorio en tu máquina.
2. Copia `.env.example` como `.env` (mismo folder, quitando el `.example`
   del nombre):
   ```powershell
   copy .env.example .env
   ```
3. Abre `.env` y reemplaza los valores de ejemplo por tus credenciales
   reales de SIS2:
   ```
   SIS2_USERNAME=tu_usuario_real
   SIS2_PASSWORD=tu_password_real
   ```
4. Instala las dependencias de Python:
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

**Importante:** `.env` nunca se sube a git (está en `.gitignore`). Cada
persona que use el proyecto en su propia máquina necesita crear su propio
`.env` con sus propias credenciales.

## 3. Ejecutar localmente (sin Docker)

Primera vez (para confirmar visualmente que el login automático funciona):

```powershell
python Authentication/Authentication.py
```

Este script está configurado para correr con `headless=False` cuando se
ejecuta directamente, así que vas a ver el navegador abrirse, llenarse
solo, y cerrarse al terminar. Si todo sale bien, queda creado
`Authentication/auth.json`.

Corridas normales (ya validado que el login funciona):

```powershell
python ServiceSoftwareFiles.py
```

Esto usa `headless=True` internamente (sin ventana), reutiliza el
`auth.json` si sigue vigente, consulta todos los equipos en paralelo, y
genera `Results/resultado_sis2.csv`.

## 4. Ejecutar localmente con Docker

Útil para probar exactamente el mismo entorno que correrá en la nube,
antes de desplegar.

```powershell
docker build -t proyecto-ecm .
docker run --rm --env-file .env --shm-size=1gb -v "${PWD}\Results:/app/Results" proyecto-ecm
```

- `--shm-size=1gb`: evita que Chromium falle por memoria compartida
  insuficiente (el límite default de Docker, 64 MB, no alcanza).
- `-v "${PWD}\Results:/app/Results"`: conecta la carpeta `Results` de tu PC
  con la del contenedor, para que el CSV generado quede en tu disco (sin
  esto, se pierde al terminar el contenedor por el flag `--rm`).

## 5. Cómo cambiar variables y rutas

Ver `04_VARIABLES_Y_CONFIGURACION.md` para la tabla completa de todas las
variables. Resumen de dónde se cambia cada cosa:

| Quiero cambiar... | En local (`.env`) | En la nube (Container Apps) |
|---|---|---|
| Usuario/contraseña de SIS2 | Edita `.env` | `az containerapp job update --secrets "sis2-password=NUEVO_VALOR"` |
| Ruta del listado de equipos en ADLS | No aplica (usa `Equipos.csv` local) | Cambia `ADLS_INPUT_DIRECTORY` con `az containerapp job update --set-env-vars` |
| Ruta de salida del reporte en ADLS | No aplica (usa `Results/` local) | Cambia `ADLS_OUTPUT_DIRECTORY` igual que arriba |
| Nivel de paralelismo (`MAX_WORKERS`) | Edita la constante en `ServiceSoftwareFiles.py` | Igual — es parte del código, requiere rebuild (ver sección 6) |
| Frecuencia de ejecución (cron) | No aplica | `az containerapp job update --cron-expression "..."` |

Ejemplo completo para cambiar una variable de entorno sin secretos:

```powershell
az containerapp job update `
  --name job-sis2-extraccion `
  --resource-group dv-bigdataikc-rg `
  --set-env-vars "ADLS_INPUT_DIRECTORY=data/ECM Report Project/OtraCarpeta"
```

## 6. Cómo modificar el código y reflejarlo en la nube

Un contenedor Docker es una imagen inmutable — no hay forma de "editar
directo" lo que corre en Azure. El flujo siempre es:

1. Edita el archivo `.py` correspondiente en tu editor.
2. Prueba localmente primero (sección 3), para no gastar tiempo de
   despliegue en algo que ni siquiera corre bien en tu máquina.
3. Reconstruye la imagen:
   ```powershell
   docker build -t proyecto-ecm .
   ```
4. (Opcional pero recomendado) valida con Docker local (sección 4) antes
   de subir.
5. Sube la imagen al registro:
   ```powershell
   docker tag proyecto-ecm acrbigdataikc.azurecr.io/proyecto-ecm:latest
   docker push acrbigdataikc.azurecr.io/proyecto-ecm:latest
   ```
6. Actualiza el job para que use la imagen nueva:
   ```powershell
   az containerapp job update --name job-sis2-extraccion --resource-group dv-bigdataikc-rg --image acrbigdataikc.azurecr.io/proyecto-ecm:latest
   ```

**Qué SÍ se refleja solo, sin este ciclo** (viven fuera de la imagen):
- El contenido del archivo de equipos en ADLS.
- Las credenciales (son secretos del Container App, no del código).
- La frecuencia del cron.

## 7. Ver logs y resultados de una ejecución en la nube

```powershell
# Ver ejecuciones recientes del job
az containerapp job execution list --name job-sis2-extraccion --resource-group dv-bigdataikc-rg -o table

# Ver logs de la ejecución (streaming)
az containerapp job logs show --name job-sis2-extraccion --resource-group dv-bigdataikc-rg

# Disparar una ejecución manual (fuera del horario del cron)
az containerapp job start --name job-sis2-extraccion --resource-group dv-bigdataikc-rg
```

El CSV de resultado queda en ADLS, en la ruta definida por
`ADLS_OUTPUT_DIRECTORY` (por defecto, `data/ECM Report Project/`) —
visible desde el Portal de Azure (Storage Browser) o desde Synapse/Power BI
como cualquier otro archivo del data lake.

## 8. Ver la configuración actual del job

```powershell
# Variables de entorno configuradas
az containerapp job show --name job-sis2-extraccion --resource-group dv-bigdataikc-rg --query "properties.template.containers[0].env" -o table

# Nombres de los secretos configurados (no muestra los valores, Azure nunca los expone una vez guardados)
az containerapp job show --name job-sis2-extraccion --resource-group dv-bigdataikc-rg --query "properties.configuration.secrets" -o table
```

## 9. Problemas comunes y solución

### 9.1 — `Page.goto: Timeout 30000ms exceeded`

**Causa:** se usaba `wait_until="networkidle"`, que nunca se cumple si el
sitio mantiene tráfico de fondo (analytics, polling). **Ya corregido** en
el código actual (`wait_until="domcontentloaded"`, timeout 60s). Si
reaparece, puede ser un problema real de red/proxy corporativo — prueba
abrir `https://sis2.cat.com` manualmente desde la misma máquina/red.

### 9.2 — `RuntimeError: No se encontró ningún campo con estos selectores...`

**Causa más común:** Cat cambió algo en la página de login (nuevo `id` de
campo, paso adicional). **Cómo diagnosticar:**

1. Corre `python Authentication/Authentication.py` (usa `headless=False`
   por defecto al ejecutarlo directo).
2. Cuando se trabe, clic derecho → Inspeccionar sobre el campo que no se
   encontró, y anota su `id`/`name` real.
3. Agrega ese selector a la lista correspondiente en
   `_autocompletar_login()` (`email_selectors`, `continue_selectors`,
   `password_selectors`, o `submit_selectors`).
4. Si el error queda documentado con una captura, revisa también
   `Authentication/login_debug.png` (se genera automáticamente si el
   proceso completo tarda más de 60s).

### 9.3 — El login es de dos pasos, no de uno

SIS2 usa Azure AD B2C con **usuario + botón "Continue" primero, password
después**. Ya está contemplado en el código actual. Si Cat cambiara esto a
un solo paso, habría que simplificar `_autocompletar_login` quitando la
espera intermedia del botón "Continue".

### 9.4 — `BrowserType.launch: Chromium distribution 'chrome' is not found`

**Causa:** el código especificaba `channel="chrome"` (el Chrome real de
Windows), pero la imagen Docker de Playwright solo trae Chromium sin
marca. **Ya corregido**: se quitó el parámetro `channel` de
`p.chromium.launch(...)`.

### 9.5 — `Executable doesn't exist at .../chrome-headless-shell...` + aviso de "Please update docker image"

**Causa:** desajuste entre la versión de `playwright` instalada por pip
(`requirements.txt` sin versión fija instala siempre la última) y los
binarios de Chromium que trae la imagen base de Docker. **Ya corregido**:
`requirements.txt` fija `playwright==1.48.0`, exactamente la misma versión
que la imagen base `mcr.microsoft.com/playwright/python:v1.48.0-jammy`. Si
en el futuro se actualiza la imagen base a otra versión, hay que actualizar
también el pin de `playwright` en `requirements.txt` para que coincidan.

### 9.6 — `az` no reconocido como comando (`CommandNotFoundException`)

**Causa:** Azure CLI no está instalado, o está instalado pero su carpeta
no está en el `PATH` de Windows.

**Si no tienes permisos de administrador para instalar el MSI oficial:**

```powershell
pip install azure-cli
```

Esto instala Azure CLI como paquete de Python (en modo usuario, sin
admin). El ejecutable queda en una carpeta tipo
`...\AppData\Roaming\Python\Python3XX\Scripts\az.bat`, que puede no estar
en el `PATH`. Para agregarla:

```powershell
# Verifica dónde quedó instalado
dir "C:\Users\TU_USUARIO\AppData\Roaming\Python\Python312\Scripts\az*"

# Agrega esa carpeta al PATH de tu usuario (permanente, sin admin)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\TU_USUARIO\AppData\Roaming\Python\Python312\Scripts", "User")
```

Cierra y abre una PowerShell **nueva** después de este último comando —
recién ahí toma efecto.

### 9.7 — No tengo permisos para asignar roles en Azure (`az role assignment create` falla)

Ver la sección 5 de `02_ARQUITECTURA_SOLUCION.md` — se resuelve usando la
clave de acceso del storage account (`ADLS_ACCOUNT_KEY`) en vez de
identidad administrada + RBAC. Si en cambio te falla el paso de **leer**
la clave (`az storage account keys list`), ese sí sería un permiso mínimo
a pedirle a IT ("dame el valor de key1 del storage account X"), mucho más
acotado que pedir capacidad de asignar roles.

### 9.8 — El resultado en ADLS no se actualiza tras cambiar el listado de equipos

Verifica:
1. Que el archivo nuevo efectivamente esté en
   `data/ECM Report Project/Equipos/` (la ruta exacta de
   `ADLS_INPUT_DIRECTORY`) y que tenga extensión `.csv`.
2. Que tenga una columna llamada exactamente `SerialNumber` (case-sensitive).
3. Que el job efectivamente haya corrido después de que el archivo se
   actualizó (revisa `az containerapp job execution list` para ver la
   hora de la última ejecución vs. la hora de modificación del archivo).

### 9.9 — Docker Desktop no arranca / "Cannot connect to the Docker daemon"

Confirma que Docker Desktop esté corriendo (ícono de la ballena en la
barra de tareas, sin el círculo rojo de error). Si acabas de instalarlo,
puede pedir reiniciar Windows para activar WSL2.

## 10. Preguntas frecuentes

**¿Puedo correr esto sin Docker en la nube, solo con Python directo en una
VM?** Sí, técnicamente — pero perderías la reproducibilidad del entorno
(versión exacta de Chromium, dependencias del sistema) y la facilidad de
Container Apps Jobs para programar la ejecución sin mantener un servidor
corriendo todo el tiempo.

**¿Qué pasa si el CSV de equipos en ADLS está vacío o no existe?** El
código lanza `FileNotFoundError` explícitamente en vez de consultar una
lista vacía silenciosamente — revisa los logs del job para confirmar la
ruta exacta que buscó.

**¿Puedo cambiar la hora de ejecución sin redeploy?** Sí —
`az containerapp job update --cron-expression "..."` no requiere tocar el
código ni la imagen.

**¿Qué pasa si Cat invalida la sesión mientras el job está corriendo?** El
código detecta 401/403 y reautentica automáticamente una vez, sin
interrumpir el resto de la corrida (ver `_forzar_relogin` en
`01_ANALISIS_TECNICO.md`).

**¿Necesito Key Vault para este proyecto?** No en el flujo actual — los
secretos viven en el store propio de Container Apps. Key Vault
(`dv-bigdataikc-kv`) está disponible en tu entorno pero no forma parte del
runtime de este job específico (ver la decisión documentada en
`02_ARQUITECTURA_SOLUCION.md`, sección 5).
