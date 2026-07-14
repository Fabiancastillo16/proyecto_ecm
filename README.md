# proyecto_ecm

Extrae, para una lista de equipos (números de serie), la versión de software
ECM más reciente publicada por Caterpillar en SIS2, y consolida el resultado
en un CSV para reporte. El login a SIS2 se automatiza (usuario/contraseña
desde variables de entorno) y las consultas a la API se hacen en paralelo.

## Documentación

- [`docs/ANALISIS_PROYECTO.md`](docs/ANALISIS_PROYECTO.md) — objetivo,
  componentes, e historial de problemas encontrados y resueltos.
- [`docs/ARQUITECTURA_CLOUD.md`](docs/ARQUITECTURA_CLOUD.md) — arquitectura
  propuesta en Azure (Container Apps Jobs) y guía de despliegue paso a paso.
- [`docs/OPERACION_TROUBLESHOOTING.md`](docs/OPERACION_TROUBLESHOOTING.md) —
  cómo correr el proyecto y qué hacer si algo falla.

## Quick start (local)

```bash
pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # y coloca tus credenciales reales

python Authentication/Authentication.py   # primera vez, headless=False
python ServiceSoftwareFiles.py            # corridas normales
```

## Estructura

```
Authentication/
  Authentication.py   # login automático a SIS2 (Playwright)
ServiceSoftwareFiles.py # consultas paralelas a la API + export CSV
Equipos.csv             # lista de entrada (números de serie)
Results/                # CSV de salida
Dockerfile               # imagen para despliegue en Azure Container Apps Jobs
docs/                    # documentación (ver arriba)
```

## Seguridad

- Las credenciales viven en `.env` (local, gitignored) o en Azure Key Vault
  (nube, inyectadas como variables de entorno). Nunca en el código ni en git.
- `Authentication/auth.json` (token + cookies generados en cada login)
  también está en `.gitignore`.
