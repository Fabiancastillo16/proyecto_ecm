# proyecto_ecm

Extrae, para una lista de equipos mineros (números de serie), la versión de
software ECM más reciente publicada por Caterpillar en SIS2, y consolida el
resultado en un CSV. El login a SIS2 se automatiza y las consultas a la API
se hacen en paralelo. Corre localmente (desarrollo) o de forma programada y
desatendida en Azure (producción).

## Documentación

Ver **[docs/00_INDICE.md](docs/00_INDICE.md)** para la documentación técnica
completa: análisis del proyecto, arquitectura de la solución, manual de
usuario, referencia de variables, y glosario.

## Quick start (local)

```bash
pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # y coloca tus credenciales reales

python Authentication/Authentication.py   # primera vez, valida el login visualmente
python ServiceSoftwareFiles.py            # corridas normales
```

## Estructura

```
Authentication/
  Authentication.py       # login automático a SIS2 (Playwright, 2 pasos B2C)
ServiceSoftwareFiles.py    # carga equipos, consulta en paralelo, exporta CSV
Equipos.csv                # lista de entrada de referencia (modo local)
Results/                   # CSV de salida (modo local)
Dockerfile                 # imagen para Azure Container Apps Jobs
requirements.txt / requirements-cloud.txt
docs/                      # documentación completa (ver arriba)
```

## Seguridad

- Credenciales de SIS2: `.env` local (gitignored) o secretos de Azure
  Container Apps en la nube. Nunca en el código.
- `Authentication/auth.json` (token generado en cada login): gitignored.
- Ver `docs/02_ARQUITECTURA_SOLUCION.md` sección 5 para el modelo de
  autenticación a ADLS y sus trade-offs.

**Pendiente:** el historial de git de este repo contiene un commit antiguo
con un token real expuesto. Purgar con `git filter-repo` antes de compartir
el repo ampliamente (ver `docs/03_MANUAL_USUARIO.md`).
