# Análisis del proyecto: proyecto_ecm

## Objetivo

Extraer, para una lista de equipos (números de serie), la versión de software
ECM más reciente publicada por Caterpillar en SIS2, y dejar el resultado
consolidado en un CSV para reporte.

## Por qué existe este proyecto

SIS2 no expone una API pública con credenciales de aplicación (API key /
client secret): el acceso es vía sesión de usuario (SSO Azure AD B2C de Cat).
Este proyecto automatiza esa sesión (login) para poder luego usar el token
resultante y consultar el endpoint REST interno de forma programática, en vez
de hacerlo a mano equipo por equipo desde el navegador.

## Componentes

| Archivo | Responsabilidad |
|---|---|
| `Authentication/Authentication.py` | Abre un Chromium (Playwright), llena el login de Azure AD B2C, captura el bearer token y las cookies de sesión, y las guarda en `Authentication/auth.json`. |
| `ServiceSoftwareFiles.py` | Carga `auth.json`, consulta en paralelo el endpoint de SIS2 para cada serial en `Equipos.csv`, y exporta `Results/resultado_sis2.csv`. Si detecta un 401/403 a mitad de la corrida, reautentica una sola vez y continúa. |
| `Equipos.csv` | Lista de entrada: números de serie a consultar. |
| `Results/resultado_sis2.csv` | Salida: nombre de ECM, part number, archivo flash más reciente, fecha, tamaño, etc. por equipo. |

## Historial de problemas encontrados y resueltos

Este proyecto pasó por varias iteraciones de depuración real, documentadas
aquí para no repetir el mismo diagnóstico si algo se rompe de nuevo:

1. **Credencial real expuesta en git.** El archivo `Authentication/auth.json`
   (con un bearer token JWT y cookies de sesión reales) estaba commiteado en
   el repositorio público. Se corrigió agregándolo a `.gitignore`, pero
   **sigue en el historial de git** hasta que se purgue con `git filter-repo`
   o similar (ver sección "Pendientes").

2. **Import roto / variable no definida (`ECM.py`).** Existía un script
   duplicado que importaba un módulo inexistente (`auth_sis2`) y usaba una
   variable `TOKEN` nunca definida. Se eliminó por ser una versión vieja y
   rota; `ServiceSoftwareFiles.py` es la versión correcta y vigente.

3. **Login no automatizado.** Originalmente el usuario debía loguearse a
   mano en la ventana de Chromium que abre Playwright. Se automatizó
   llenando usuario/contraseña desde variables de entorno (`.env`, nunca
   commiteado), sin necesidad de MFA (confirmado que esta cuenta no lo usa).

4. **Timeout en `page.goto(..., wait_until="networkidle")`.** SIS2 mantiene
   actividad de red de fondo (analytics/polling) que nunca deja la red
   "quieta", por lo que Playwright nunca consideraba la página cargada y
   fallaba a los 30s sin haber intentado el login. Se cambió a
   `wait_until="domcontentloaded"` con timeout de 60s.

5. **Login en dos pasos (Azure AD B2C).** El formulario no es un solo paso:
   primero usuario + botón "Continue", y solo en la pantalla siguiente
   aparece el campo de password. El script fallaba buscando `#password`
   porque nunca se había hecho clic en "Continue". Se corrigió
   secuenciando explícitamente: llenar usuario → clic en continuar → esperar
   pantalla de password → llenar password → clic en enviar.

6. **Rendimiento.** Las consultas eran secuenciales (una por una, con
   `time.sleep(1)` entre cada una). Se paralelizó con `ThreadPoolExecutor`
   (I/O-bound, así que threads son suficientes sin necesitar `asyncio`), con
   cuidado especial de que si el token expira a mitad de la corrida, solo un
   thread reautentique (lock), no todos a la vez.

## Estado actual

El flujo local funciona de punta a punta: login automático sin intervención
manual, consultas en paralelo, y CSV de salida. La siguiente fase (cubierta
en `ARQUITECTURA_CLOUD.md`) es llevar esto a un recurso de Azure programado,
sin depender de que alguien lo ejecute manualmente desde su máquina.

## Pendientes

- **Purgar el token histórico del repositorio git** (sigue en commits viejos
  aunque ya no esté en el archivo actual). Requiere reescribir el historial
  con `git filter-repo`, coordinado con quien haya clonado el repo.
- Definir política de rotación: si Cat invalida sesiones tras cierto tiempo
  de inactividad, el job en la nube debe re-loguearse solo (ya lo hace, ver
  `_forzar_relogin` en `ServiceSoftwareFiles.py`), pero conviene monitorear
  cuántas veces ocurre por corrida como señal de salud.
