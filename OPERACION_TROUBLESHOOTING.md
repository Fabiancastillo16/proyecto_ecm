# Guía operativa y troubleshooting

## Correr en local

1. `pip install -r requirements.txt`
2. `playwright install chromium` (una sola vez, instala el navegador)
3. Copia `.env.example` como `.env` y coloca tus credenciales reales.
4. Primera vez: `python Authentication/Authentication.py` (corre con
   `headless=False`, para ver el navegador y confirmar que el login
   automático funciona en tu pantalla).
5. Corridas normales: `python ServiceSoftwareFiles.py` (usa `headless=True`
   internamente, detecta si ya existe `auth.json` vigente, y si no,
   reautentica solo).

## Problemas ya resueltos (referencia rápida)

### `Page.goto: Timeout 30000ms exceeded`

**Causa:** `wait_until="networkidle"` nunca se cumple si el sitio mantiene
tráfico de fondo (analytics, polling). **Solución ya aplicada:**
`wait_until="domcontentloaded"` con `timeout=60000`. Si vuelve a pasar,
sube el timeout o revisa si hay un problema real de red/proxy corporativo.

### `RuntimeError: No se encontró ningún campo con estos selectores...`

**Causa más común:** Cat cambió algo en la página de login, o el flujo tiene
un paso adicional no contemplado (ej. una pantalla intermedia de
verificación). **Cómo diagnosticar:**

1. Corre `obtener_auth(headless=False)` para ver el navegador en vivo.
2. Cuando se trabe, clic derecho → Inspeccionar sobre el campo que no
   se encontró, y revisa su `id` o `name` real.
3. Agrega ese selector a la lista correspondiente en
   `_autocompletar_login` (`email_selectors`, `continue_selectors`,
   `password_selectors`, o `submit_selectors`).

### Login en dos pasos vs. un paso

SIS2 usa Azure AD B2C con un flujo de **dos pantallas**: usuario + botón
"Continue" primero, password + botón de envío después. Si Cat cambiara esto
a un solo paso (usuario y password en la misma pantalla), habría que
simplificar `_autocompletar_login` para no esperar el clic de "Continue"
entre medio.

### Token expira a mitad de una corrida larga

`ServiceSoftwareFiles.py` ya maneja esto: si una consulta devuelve 401/403,
reautentica una sola vez (con lock, aunque varios threads lo detecten a la
vez) y continúa desde donde iba. Si ves reautenticaciones muy frecuentes en
los logs, es señal de que la sesión dura menos de lo esperado — vale la pena
medir cuánto dura un token típico y ajustar la frecuencia del cron acorde.

### Ajustar el nivel de paralelismo

`MAX_WORKERS` en `ServiceSoftwareFiles.py` (por defecto 8). Si ves códigos
429 (rate limit) o bloqueos, bájalo a 4-5. Si la API responde bien y quieres
ir más rápido, puedes subir a 15-20 — pero súbelo de a poco y observa,
no hay un número "correcto" universal, depende de lo que SIS2 tolere.

## Correr en la nube (Container Apps Jobs)

Ver `ARQUITECTURA_CLOUD.md` para el despliegue completo. Para diagnosticar
una ejecución que falló en la nube:

```bash
az containerapp job logs show --name job-sis2-extraccion --resource-group rg-mining-finsa
```

Si falla específicamente en el paso de login (y no en red/despliegue), el
diagnóstico es el mismo que en local: el problema casi siempre es un cambio
en los selectores de la página de Cat. Como el contenedor corre headless por
diseño, no puedes "ver" el navegador ahí — para depurar, reproduce el mismo
`auth.json`/error corriendo el proyecto en tu máquina local con
`headless=False` primero, y una vez arreglado el selector, reconstruye y
sube la imagen Docker.

## Checklist antes de cada despliegue

- [ ] `.env` y `Authentication/auth.json` NO están trackeados en git
      (`git status` no debe mostrarlos).
- [ ] La imagen Docker se probó localmente (`docker build . && docker run
      --env-file .env proyecto-ecm`) antes de subir a ACR.
- [ ] Las variables `ADLS_STORAGE_ACCOUNT` / `ADLS_FILESYSTEM` están
      correctas si esperas que suba a ADLS (si no las necesitas, no las
      definas — el script simplemente no sube nada).
- [ ] La identidad administrada tiene los permisos de Key Vault y storage
      asignados (ver `ARQUITECTURA_CLOUD.md`, paso 5).
