# 05 — Glosario de términos técnicos

| Término | Explicación |
|---|---|
| **SIS2** | Portal web de Caterpillar donde se consulta información de servicio de equipos, incluyendo software de ECM |
| **ECM** | Engine Control Module (módulo de control del motor) — el componente electrónico del equipo cuyo software se está consultando |
| **Bearer token** | Un tipo de token de autenticación que se envía en el header HTTP `Authorization: Bearer <token>`. Demuestra que el usuario ya inició sesión, sin tener que reenviar usuario/contraseña en cada request |
| **JWT (JSON Web Token)** | Formato específico de token (usado como bearer token aquí) que codifica información (usuario, fecha de expiración, etc.) de forma verificable |
| **Azure AD B2C** | Servicio de Microsoft para gestionar el login de clientes externos (no empleados) a una aplicación — es lo que usa Cat para el login de SIS2 |
| **SSO (Single Sign-On)** | Un solo login que da acceso a múltiples sistemas relacionados, sin tener que autenticarse de nuevo en cada uno |
| **MFA / 2FA** | Autenticación multifactor / de dos factores — un segundo paso de verificación (código SMS, app autenticadora) además de usuario/contraseña. Esta cuenta específica no lo requiere actualmente |
| **Playwright** | Librería de automatización de navegador (de Microsoft) usada para controlar Chromium programáticamente: abrir páginas, llenar formularios, hacer clic, interceptar requests de red |
| **Headless** | Modo en el que un navegador corre sin interfaz gráfica visible (sin ventana). Necesario para correr en un servidor/contenedor donde no hay pantalla |
| **Selector (CSS selector)** | Una expresión que identifica un elemento específico de una página web (ej. `#password` identifica el elemento con `id="password"`), usada para decirle a Playwright dónde hacer clic o escribir |
| **`ThreadPoolExecutor`** | Herramienta de Python para ejecutar varias funciones "al mismo tiempo" usando threads, ideal para tareas que esperan mucho en red (I/O-bound) como las consultas HTTP de este proyecto |
| **I/O-bound** | Una tarea cuyo tiempo lo consume mayormente esperando algo externo (red, disco), no procesamiento de CPU — por eso los threads de Python funcionan bien aquí a pesar del GIL |
| **Docker** | Tecnología de contenedores: empaqueta una aplicación junto con todo lo que necesita para correr (sistema operativo base, librerías, dependencias) en una unidad portable |
| **Imagen Docker** | El "paquete" construido (inmutable) con el código y sus dependencias, listo para ejecutarse como contenedor en cualquier máquina que tenga Docker |
| **Contenedor** | Una instancia en ejecución de una imagen Docker |
| **Dockerfile** | Archivo de instrucciones que define cómo construir una imagen Docker paso a paso |
| **`.dockerignore`** | Lista de archivos/carpetas que NO se incluyen al construir la imagen Docker (análogo a `.gitignore` pero para Docker) |
| **ACR (Azure Container Registry)** | Repositorio privado en Azure para guardar imágenes Docker, del cual Azure Container Apps puede "bajar" la imagen para ejecutarla |
| **Azure Container Apps Jobs** | Servicio de Azure para correr un contenedor Docker de forma programada (cron) o bajo demanda, sin mantener un servidor corriendo entre ejecuciones |
| **Cron / cron expression** | Notación estándar para expresar "con qué frecuencia" debe correr algo (ej. `0 6 * * *` = todos los días a las 6:00) |
| **ADLS Gen2 (Azure Data Lake Storage Gen2)** | Servicio de almacenamiento de Azure optimizado para grandes volúmenes de datos analíticos, con soporte de carpetas jerárquicas (a diferencia de un storage plano) |
| **Filesystem (en ADLS)** | El equivalente a un "container" o unidad de nivel superior dentro de un storage account de ADLS Gen2, que contiene la estructura de carpetas |
| **Storage account** | El recurso de Azure que aloja uno o más filesystems/containers de almacenamiento |
| **Managed Identity (identidad administrada)** | Una identidad de Azure asignada automáticamente a un recurso (como un Container App), que le permite autenticarse contra otros servicios de Azure sin guardar ninguna contraseña o clave explícita |
| **RBAC (Role-Based Access Control)** | Modelo de permisos de Azure donde se asignan "roles" (ej. "Storage Blob Data Contributor") a una identidad sobre un recurso específico |
| **Access Key (clave de acceso)** | Una clave secreta asociada directamente a un storage account, que da acceso total a sus datos sin pasar por RBAC — alternativa más simple pero de alcance más amplio que Managed Identity |
| **Azure Key Vault** | Servicio de Azure para guardar secretos (contraseñas, claves, certificados) de forma centralizada y auditable |
| **Secreto de Container Apps** | Mecanismo propio de Azure Container Apps para guardar valores sensibles asociados directamente a esa aplicación/job, sin depender de Key Vault |
| **`secretref:`** | Prefijo usado en la configuración de Container Apps para indicar que una variable de entorno debe tomar su valor de un secreto ya definido, en vez de un valor literal |
| **Synapse (Azure Synapse Analytics)** | Servicio de Azure para análisis de datos a gran escala (data warehousing, ETL), parte del stack analítico donde termina consumiéndose el resultado de este proyecto |
| **`.env`** | Archivo de texto plano con pares `VARIABLE=valor`, usado para guardar configuración/credenciales fuera del código fuente. Se lee con la librería `python-dotenv` |
| **`.gitignore`** | Lista de archivos/carpetas que git debe ignorar (no versionar), típicamente usada para excluir secretos y archivos generados |
| **API REST** | Un estilo de interfaz web donde se consultan/modifican datos mediante URLs y métodos HTTP estándar (GET, POST, etc.), devolviendo normalmente JSON |
| **Status code 401 / 403** | Códigos HTTP que indican, respectivamente, "no autenticado" (token inválido o ausente) y "no autorizado" (autenticado pero sin permiso) — en este proyecto, señal de que el token de sesión expiró |
| **Status code 429** | Código HTTP "Too Many Requests" — indica que se está consultando la API con demasiada frecuencia y el servidor está limitando (rate limiting) |
