# proyecto_ecm

Extrae, para una lista de equipos mineros (números de serie), la versión de
software ECM más reciente publicada por Caterpillar en SIS2, y mantiene un
**historial de cambios** en Azure SQL (`epcat.ecm_cat_software_number`) —
insertando una fila nueva solo cuando el software de un ECM específico cambia
respecto a la última corrida.

Corre de forma 100% desatendida: una VM de Azure se enciende automáticamente
cada madrugada, ejecuta el script, notifica el resultado a Microsoft Teams, y
se apaga sola.

## Documentación

Ver **[docs/00_INDICE.md](docs/00_INDICE.md)** para la documentación técnica
completa. Si vas a modificar el login, la autenticación a SQL, o el Task
Scheduler, lee primero **[docs/06_BITACORA_DECISIONES.md](docs/06_BITACORA_DECISIONES.md)**
— documenta en detalle por qué la arquitectura es la que es.

## Arquitectura (resumen)

```
3:00 AM  Azure enciende la VM (Tasks nativas del blade de la VM)
3:15 AM  Task Scheduler dispara ejecutar_ecm.ps1
         └─ Login automático a SIS2 (Playwright)
         └─ Lee el listado de equipos desde ADLS
         └─ Consulta la API de SIS2 en paralelo (8 threads)
         └─ Compara contra el último estado conocido en Azure SQL
         └─ Inserta solo lo nuevo/cambiado
         └─ Notifica el resultado a Teams (éxito o falla)
4:00 AM  Azure apaga la VM
```

**Nota:** este proyecto tuvo una arquitectura previa basada en Docker + Azure
Container Apps Jobs, abandonada tras confirmar un problema irresoluble de
compatibilidad (el login a SIS2 no se completaba corriendo Chromium headless
dentro de un contenedor Linux). Ver la bitácora para el detalle completo.

## Quick start (local/VM)

```powershell
pip install -r requirements.txt
playwright install chromium

copy .env.example .env   # y completa las credenciales — ver docs/04

python ServiceSoftwareFiles.py
```

## Estructura

```
Authentication/
  Authentication.py     # login automático a SIS2 (Playwright)
ServiceSoftwareFiles.py  # carga equipos, consulta en paralelo, compara e inserta en SQL
ejecutar_ecm.ps1         # invocado por el Task Scheduler; notifica a Teams
Equipos.csv              # lista de entrada de referencia (modo local sin ADLS)
Results/                 # CSV de respaldo + log acumulado de ejecuciones
docs/                    # documentación completa (ver arriba)
```

## Seguridad

- Credenciales de SIS2 y de SQL: `.env` (gitignored). Nunca en el código.
- La contraseña de la cuenta de Windows usada para el auto-login de la VM
  queda guardada en el registro de Windows — trade-off de seguridad
  documentado en `docs/02_ARQUITECTURA_SOLUCION.md`, sección 5.4.

**Pendiente:** el historial de git de este repo contiene un commit antiguo
con un token real expuesto. Purgar con `git filter-repo` antes de compartir
el repo ampliamente (ver `docs/03_MANUAL_USUARIO.md`).
