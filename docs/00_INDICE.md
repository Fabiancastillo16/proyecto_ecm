# Índice de documentación — proyecto_ecm

Documentación técnica completa del proyecto. Orden de lectura sugerido si
es tu primera vez con el proyecto:

1. **[01_ANALISIS_TECNICO.md](01_ANALISIS_TECNICO.md)** — Qué hace el
   proyecto, con qué tecnologías está construido, explicación función por
   función del código, diagramas de flujo de datos, e historial completo
   de problemas encontrados y resueltos durante el desarrollo.

2. **[02_ARQUITECTURA_SOLUCION.md](02_ARQUITECTURA_SOLUCION.md)** — Cómo
   está desplegada la solución: arquitectura local vs. nube, por qué se
   eligió Azure Container Apps Jobs, diagramas de despliegue, el modelo de
   seguridad (y por qué se usa clave de storage en vez de identidad
   administrada), y la guía de despliegue paso a paso con los comandos
   `az cli` reales de este proyecto.

3. **[03_MANUAL_USUARIO.md](03_MANUAL_USUARIO.md)** — Guía práctica de
   operación: requisitos de software, cómo correr el proyecto en local o
   con Docker, cómo cambiar cualquier configuración, cómo modificar el
   código y reflejarlo en la nube, y solución a cada problema real que
   surgió durante el desarrollo (con el mensaje de error exacto de
   referencia).

4. **[04_VARIABLES_Y_CONFIGURACION.md](04_VARIABLES_Y_CONFIGURACION.md)**
   — Tabla de referencia rápida: cada variable de entorno, secreto,
   constante de código, y ruta de archivo, con su descripción, dónde se
   define, y si es obligatoria.

5. **[05_GLOSARIO.md](05_GLOSARIO.md)** — Definición de cada término
   técnico usado en los documentos anteriores (SIS2, ADLS, RBAC, Container
   Apps, etc.), para que ningún concepto quede sin explicar.

## Si buscas algo puntual

| Quiero... | Ve a |
|---|---|
| Entender qué hace el proyecto en general | `01_ANALISIS_TECNICO.md`, sección 1-2 |
| Entender una función específica del código | `01_ANALISIS_TECNICO.md`, sección 5 |
| Ver por qué se tomó una decisión de arquitectura | `02_ARQUITECTURA_SOLUCION.md`, sección 2 y 5 |
| Desplegar el proyecto desde cero | `02_ARQUITECTURA_SOLUCION.md`, sección 6 |
| Correr el proyecto en tu máquina | `03_MANUAL_USUARIO.md`, sección 2-4 |
| Cambiar una credencial, ruta, o variable | `03_MANUAL_USUARIO.md`, sección 5, y `04_VARIABLES_Y_CONFIGURACION.md` |
| Resolver un error que te está saliendo | `03_MANUAL_USUARIO.md`, sección 9 |
| Saber qué significa un término técnico | `05_GLOSARIO.md` |
