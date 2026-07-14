# Imagen oficial de Playwright para Python: ya trae Chromium + todas las
# dependencias del sistema instaladas. Evita compilar/instalar eso a mano.
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Dependencias de Python primero (mejor cacheo de capas Docker)
COPY requirements.txt requirements-cloud.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cloud.txt

# Código del proyecto
COPY Authentication ./Authentication
COPY ServiceSoftwareFiles.py Equipos.csv ./

# Carpeta de resultados (se sube a ADLS si las env vars están configuradas,
# pero igual queda un respaldo local dentro del contenedor)
RUN mkdir -p Results

# No se copia .env: en la nube las credenciales llegan como variables de
# entorno inyectadas por Container Apps Jobs desde Key Vault, no desde archivo.

CMD ["python", "ServiceSoftwareFiles.py"]
