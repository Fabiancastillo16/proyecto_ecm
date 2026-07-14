# Arquitectura en la nube (Azure Container Apps Jobs)

## Por qué Container Apps Jobs y no otra opción

El paso crítico de este proyecto (`Authentication.py`) necesita lanzar un
Chromium real vía Playwright. Eso descarta opciones con sandbox restringido:

| Opción | Problema para este caso |
|---|---|
| Azure Functions (Consumption) | Sandbox sin dependencias del sistema para Chromium, timeout de 5 min |
| Azure Automation Runbook | Sandbox de Python restringido, sin soporte de browser |
| Azure Functions (Premium/Docker) | Funciona, pero es forzar un caso de uso para el que Functions no está pensado |
| **Container Apps Jobs** | Contenedor Docker completo, sin restricciones de dependencias, con trigger cron nativo |
| Databricks Job (alternativa) | También viable si se prefiere mantener todo dentro del stack de Databricks ya existente, vía init script instalando dependencias de Chromium |

Este documento cubre el camino de **Container Apps Jobs**, por ser el ajuste
más directo (un job programado = exactamente lo que este proceso necesita).

## Componentes

- **Azure Container Registry (ACR):** guarda la imagen Docker del proyecto.
- **Azure Container Apps Job:** ejecuta la imagen con un trigger programado
  (cron), sin servidor corriendo entre ejecuciones (se paga solo por el
  tiempo que corre).
- **Azure Key Vault:** guarda `SIS2_USERNAME` y `SIS2_PASSWORD`. Container
  Apps las inyecta como variables de entorno en tiempo de ejecución — el
  código no cambia respecto a la versión local con `.env`.
- **Identidad administrada (Managed Identity):** el Container App Job la usa
  para autenticarse contra Key Vault y contra ADLS, sin ningún secreto
  adicional embebido.
- **ADLS Gen2:** destino del CSV de resultado, para que quede disponible a
  Synapse/Power BI igual que tus otros pipelines.

## Flujo

1. El trigger cron dispara la ejecución del job en el horario configurado.
2. El contenedor arranca, la identidad administrada obtiene las credenciales
   desde Key Vault (como variables de entorno) y el token de acceso a ADLS.
3. `Authentication.py` corre en modo headless, hace login y guarda el token.
4. `ServiceSoftwareFiles.py` consulta en paralelo todos los seriales.
5. El CSV resultante se sube a ADLS Gen2 (función
   `subir_a_adls_si_corresponde`, ya integrada en el script — si las
   variables `ADLS_STORAGE_ACCOUNT` / `ADLS_FILESYSTEM` no están definidas,
   simplemente no hace nada, así que el mismo código sirve para local y nube).
6. El contenedor termina y se libera (no queda nada corriendo entre ejecuciones).

## Pasos de despliegue

Asumiendo que ya tienes un grupo de recursos (`rg-mining-finsa` en el ejemplo)
y quieres desplegar en la región `eastus2` (ajusta a tu región real):

### 1. Crear el Container Registry y subir la imagen

```bash
az acr create --resource-group rg-mining-finsa --name acrminingfinsa --sku Basic

az acr login --name acrminingfinsa

docker build -t acrminingfinsa.azurecr.io/proyecto-ecm:latest .
docker push acrminingfinsa.azurecr.io/proyecto-ecm:latest
```

### 2. Crear el Key Vault y guardar las credenciales

```bash
az keyvault create --resource-group rg-mining-finsa --name kv-mining-finsa --location eastus2

az keyvault secret set --vault-name kv-mining-finsa --name sis2-username --value "TU_USUARIO"
az keyvault secret set --vault-name kv-mining-finsa --name sis2-password --value "TU_PASSWORD"
```

### 3. Crear el entorno de Container Apps (si no existe uno ya)

```bash
az containerapp env create \
  --name env-mining-finsa \
  --resource-group rg-mining-finsa \
  --location eastus2
```

### 4. Crear el Container Apps Job con identidad administrada

```bash
az containerapp job create \
  --name job-sis2-extraccion \
  --resource-group rg-mining-finsa \
  --environment env-mining-finsa \
  --trigger-type Schedule \
  --cron-expression "0 6 * * *" \
  --replica-timeout 1800 \
  --image acrminingfinsa.azurecr.io/proyecto-ecm:latest \
  --cpu 1.0 --memory 2Gi \
  --registry-server acrminingfinsa.azurecr.io \
  --mi-system-assigned \
  --env-vars \
    "SIS2_USERNAME=secretref:sis2-username" \
    "SIS2_PASSWORD=secretref:sis2-password" \
    "ADLS_STORAGE_ACCOUNT=tuadls" \
    "ADLS_FILESYSTEM=raw" \
    "ADLS_DIRECTORY=sis2"
```

`--cron-expression "0 6 * * *"` = todos los días a las 6:00. Ajusta según tu
necesidad real de frecuencia.

### 5. Dar permisos a la identidad administrada

La identidad administrada creada con `--mi-system-assigned` necesita permiso
para leer del Key Vault y escribir en ADLS:

```bash
# Obtener el principal ID de la identidad del job
PRINCIPAL_ID=$(az containerapp job show \
  --name job-sis2-extraccion --resource-group rg-mining-finsa \
  --query identity.principalId -o tsv)

# Permiso de lectura de secretos en Key Vault
az keyvault set-policy \
  --name kv-mining-finsa \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

# Permiso de escritura en el storage account (ADLS Gen2)
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/TU_SUBSCRIPTION_ID/resourceGroups/rg-mining-finsa/providers/Microsoft.Storage/storageAccounts/tuadls"
```

### 6. Ejecutar manualmente una vez para validar

```bash
az containerapp job start --name job-sis2-extraccion --resource-group rg-mining-finsa
```

Revisa los logs en Azure Portal (Container Apps Job → Execution history →
Logs) o vía CLI:

```bash
az containerapp job logs show --name job-sis2-extraccion --resource-group rg-mining-finsa
```

## Notas de seguridad

- Las credenciales nunca quedan en la imagen Docker ni en el repo: viven
  solo en Key Vault y se inyectan en tiempo de ejecución.
- `.dockerignore` excluye explícitamente `.env` y `Authentication/auth.json`
  para que ni por error terminen dentro de la imagen.
- El `auth.json` generado en cada ejecución vive solo dentro del contenedor
  efímero — desaparece cuando el job termina, no hay archivo persistente que
  proteger en la nube (a diferencia del entorno local).

## Alternativa: Databricks Job

Si prefieres no introducir un recurso nuevo y mantener todo dentro de
Databricks (donde ya tienes secret scopes de Key Vault configurados):

1. Notebook o job con un **init script** de cluster que instale las
   dependencias de sistema de Chromium (`playwright install-deps chromium`
   más `playwright install chromium`).
2. Leer `SIS2_USERNAME` / `SIS2_PASSWORD` desde el secret scope existente
   (`dbutils.secrets.get(...)`) en vez de `.env`.
3. Escribir el resultado directo a una tabla Delta o a ADLS con `dbutils.fs`
   en vez de `azure-storage-file-datalake`.

Es más "casero" (todo en un solo lugar que ya conoces) pero cada corrida
paga por un cluster completo, más caro por ejecución que un Container Apps
Job para una tarea de este tamaño.
