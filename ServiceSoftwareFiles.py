import os
import time
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd

from Authentication.Authentication import obtener_auth

# =========================
# CONFIG
# =========================

AUTH_PATH = Path("Authentication/auth.json")
BASE_URL = "https://sis2.cat.com/api/ws-all/ServiceSoftwareFilesRemoteServices/serialNumber"

MAX_WORKERS = 8          # ajusta según cuántas consultas simultáneas tolera la API sin bloquearte
REQUEST_DELAY = 0.15     # pequeño respiro entre requests por thread, para no saturar

# Lock para que solo un thread reautentique a la vez si el token expira
_auth_lock = threading.Lock()
_session_actual = None


def cargar_auth(forzar_relogin: bool = False):
    if forzar_relogin or not AUTH_PATH.exists():
        print("No existe auth.json (o se forzó relogin). Iniciando autenticación...")
        return obtener_auth(headless=True)

    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_sesion(auth_data):
    token = auth_data["bearer"]

    headers = {
        "Authorization": token,
        "Accept": "application/servicesoftwarefileservice-v3+json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://sis2.cat.com/",
        "Origin": "https://sis2.cat.com",
    }

    cookies = {
        "JSESSIONID": auth_data["cookies"].get("JSESSIONID", ""),
        "Sis2_Login": auth_data["cookies"].get("Sis2_Login", ""),
        "Sis2_Refresh": auth_data["cookies"].get("Sis2_Refresh", ""),
    }

    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)
    return session


def _obtener_sesion_vigente():
    """Devuelve la sesión actual; si no existe, la crea (con lock para evitar carreras)."""
    global _session_actual
    with _auth_lock:
        if _session_actual is None:
            auth_data = cargar_auth()
            _session_actual = construir_sesion(auth_data)
        return _session_actual


def _forzar_relogin(sesion_que_fallo):
    """
    Reautentica, pero solo si nadie más ya lo hizo mientras este thread
    esperaba el lock. 'sesion_que_fallo' es la sesión que este thread
    intentó usar y le devolvió 401/403 — si _session_actual ya cambió
    (otro thread ya la renovó), reutilizamos esa en vez de loguear de nuevo.
    """
    global _session_actual
    with _auth_lock:
        if _session_actual is not None and _session_actual is not sesion_que_fallo:
            # Otro thread ya renovó la sesión mientras esperábamos el lock
            return _session_actual

        print("Sesión expirada, reautenticando...")
        auth_data = cargar_auth(forzar_relogin=True)
        _session_actual = construir_sesion(auth_data)
        return _session_actual


def consultar_serial(serial):
    serial = str(serial).strip()
    session = _obtener_sesion_vigente()

    url = f"{BASE_URL}/{serial}?profileId=2"

    try:
        response = session.get(url, timeout=30)

        # Token vencido a mitad de la corrida -> reautentica (una sola vez
        # por sesión realmente vencida, no una vez por thread) y reintenta
        if response.status_code in (401, 403):
            session = _forzar_relogin(session)
            response = session.get(url, timeout=30)

        if response.status_code != 200:
            print(f"{serial}: STATUS {response.status_code}")
            return [{
                "serial": serial,
                "status": response.status_code,
                "error": response.text,
            }]

        data = response.json()
        ecms = data.get("ecms", [])
        filas = []

        for ecm in ecms:
            installed = ecm.get("installedFiles", {})
            filas.append({
                "serial": serial,
                "ecm_name": ecm.get("ecmDescription", {}).get("name"),
                "software_part_number": ecm.get("softwarePartNumber"),
                "flash_file": installed.get("latestFileName"),
                "release_date": installed.get("latestFileReleaseDate"),
                "file_size": installed.get("latestFileSizeInBytes"),
                "latest_available": installed.get("latestAvailableFlag"),
                "service_file_id": installed.get("serviceSoftwareFileID"),
            })

        time.sleep(REQUEST_DELAY)
        return filas

    except Exception as e:
        return [{
            "serial": serial,
            "status": "ERROR",
            "error": str(e),
        }]


def _obtener_file_system_client():
    """
    Crea el cliente de ADLS reutilizable (mismo storage account para lectura
    del listado de equipos y escritura del resultado). Devuelve None si no
    hay configuración de ADLS (ej. corriendo en local).
    """
    storage_account = os.getenv("ADLS_STORAGE_ACCOUNT")
    filesystem = os.getenv("ADLS_FILESYSTEM")
    account_key = os.getenv("ADLS_ACCOUNT_KEY")

    if not storage_account or not filesystem:
        return None

    from azure.storage.filedatalake import DataLakeServiceClient

    if account_key:
        credential = account_key
    else:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()

    service_client = DataLakeServiceClient(
        account_url=f"https://{storage_account}.dfs.core.windows.net",
        credential=credential,
    )
    return service_client.get_file_system_client(filesystem)


def cargar_equipos():
    """
    Carga la lista de equipos a consultar.
      - Si hay config de ADLS (ADLS_STORAGE_ACCOUNT + ADLS_FILESYSTEM):
          - Si ADLS_INPUT_FILENAME está definida, descarga EXACTAMENTE ese
            archivo (ruta = ADLS_INPUT_DIRECTORY/ADLS_INPUT_FILENAME) y
            nada más. Es el modo recomendado para producción.
          - Si ADLS_INPUT_FILENAME NO está definida, busca todos los .csv
            dentro de ADLS_INPUT_DIRECTORY, valida que cada uno tenga la
            columna 'SerialNumber' antes de incluirlo (descarta con
            advertencia los que no la tengan), y concatena+deduplica.
      - Si no hay config de ADLS (ej. corriendo en tu máquina local), usa
        el Equipos.csv local de siempre.
    """
    file_system_client = _obtener_file_system_client()
    input_directory = os.getenv("ADLS_INPUT_DIRECTORY")
    input_filename = os.getenv("ADLS_INPUT_FILENAME")

    if file_system_client is None or not input_directory:
        print("Cargando Equipos.csv local...")
        return pd.read_csv("Equipos.csv")

    import io

    if input_filename:
        relative_path = f"{input_directory}/{input_filename}".strip("/")
        print(f"Descargando archivo de equipos (ruta fija): {relative_path}")
        file_client = file_system_client.get_file_client(relative_path)
        contenido = file_client.download_file().readall()
        df_equipos = pd.read_csv(io.BytesIO(contenido))

        if "SerialNumber" not in df_equipos.columns:
            raise ValueError(
                f"'{relative_path}' no tiene una columna 'SerialNumber'. "
                "Revisa que ADLS_INPUT_FILENAME apunte al archivo correcto."
            )

        print(f"Equipos cargados desde ADLS: {len(df_equipos)}")
        return df_equipos

    print(f"Buscando archivos de equipos en ADLS: {input_directory}")

    paths = file_system_client.get_paths(path=input_directory)
    archivos_csv = [
        p.name for p in paths
        if not p.is_directory and p.name.lower().endswith(".csv")
    ]

    if not archivos_csv:
        raise FileNotFoundError(
            f"No se encontró ningún .csv dentro de '{input_directory}' en ADLS."
        )

    dataframes = []
    for path in archivos_csv:
        file_client = file_system_client.get_file_client(path)
        contenido = file_client.download_file().readall()
        df = pd.read_csv(io.BytesIO(contenido))

        if "SerialNumber" not in df.columns:
            print(
                f"  ADVERTENCIA: se descarta '{path}' — no tiene columna "
                "'SerialNumber' (no parece ser un archivo de equipos)."
            )
            continue

        print(f"  Descargando: {path} ({len(df)} filas)")
        dataframes.append(df)

    if not dataframes:
        raise ValueError(
            f"Había .csv en '{input_directory}', pero ninguno tiene columna "
            "'SerialNumber' — no hay ningún archivo válido de equipos."
        )

    df_equipos = pd.concat(dataframes, ignore_index=True)
    df_equipos = df_equipos.drop_duplicates(subset=["SerialNumber"])

    print(f"Equipos cargados desde ADLS: {len(df_equipos)}")
    return df_equipos


# =========================
# SALIDA: Azure SQL (epcat.ecm_cat_software_number)
# =========================

SQL_SERVER = os.getenv("SQL_SERVER", "prexternalcatsource.database.windows.net")
SQL_DATABASE = os.getenv("SQL_DATABASE", "DA_External_Sources")
SQL_SCHEMA = "epcat"
SQL_TABLE = "ecm_cat_software_number"

# Campos que definen si "cambió algo" para un mismo ECM (ver CLAVE_ECM
# más abajo para cómo se identifica "el mismo ECM" entre corridas)
CAMPOS_COMPARABLES = [
    "software_part_number",
    "release_date",
    "file_size",
    "latest_available",
    "service_file_id",
]


def _clave_ecm(fila_o_row, es_row_sql=False):
    """
    Identifica de forma única a un ECM físico dentro de un mismo equipo.
    Un equipo puede tener más de un ECM con el mismo 'ecm_name' (ej. dos
    módulos "ENGINE" distintos) — por eso 'ecm_name' solo no alcanza como
    clave, y se agrega 'flash_file' (el archivo base identifica al
    componente físico, distinto entre esos dos ECMs aunque compartan
    nombre).
    """
    if es_row_sql:
        return (fila_o_row.serial, fila_o_row.ecm_name, fila_o_row.flash_file)
    return (fila_o_row.get("serial"), fila_o_row.get("ecm_name"), fila_o_row.get("flash_file"))


def _sql_habilitado():
    """SQL_SERVER/SQL_DATABASE ya tienen default de producción, así que
    esto siempre es True salvo que alguien los desactive explícitamente
    con SQL_OUTPUT_DISABLED=1 (útil para correr solo en modo local/CSV)."""
    return os.getenv("SQL_OUTPUT_DISABLED") != "1"


def obtener_conexion_sql():
    """
    Conecta a Azure SQL usando un login SQL tradicional (usuario/contraseña),
    definido en SQL_USERNAME/SQL_PASSWORD (.env). Se eligió este método en
    vez de identidad administrada porque el servidor SQL no tiene el
    permiso "Directory Readers" necesario para validar tokens de Azure AD
    (requiere un Global Administrator de Azure AD para asignarlo, y no fue
    posible obtenerlo en el corto plazo — ver docs para el detalle).
    """
    import pyodbc

    sql_username = os.getenv("SQL_USERNAME")
    sql_password = os.getenv("SQL_PASSWORD")

    if not sql_username or not sql_password:
        raise RuntimeError(
            "Faltan credenciales de SQL. Define SQL_USERNAME y SQL_PASSWORD en tu .env."
        )

    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};"
        f"UID={sql_username};PWD={sql_password};"
    )
    return pyodbc.connect(conn_str)


def asegurar_tabla_sql(conn):
    """Crea la tabla de historial de cambios si todavía no existe."""
    cursor = conn.cursor()
    cursor.execute(f"""
        IF NOT EXISTS (
            SELECT 1 FROM sys.tables t
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = '{SQL_SCHEMA}' AND t.name = '{SQL_TABLE}'
        )
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{SQL_SCHEMA}')
                EXEC('CREATE SCHEMA {SQL_SCHEMA}');

            CREATE TABLE {SQL_SCHEMA}.{SQL_TABLE} (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                serial NVARCHAR(50) NOT NULL,
                ecm_name NVARCHAR(200) NULL,
                software_part_number NVARCHAR(100) NULL,
                flash_file NVARCHAR(200) NULL,
                release_date NVARCHAR(50) NULL,
                file_size BIGINT NULL,
                latest_available NVARCHAR(20) NULL,
                service_file_id NVARCHAR(100) NULL,
                fecha_corrida DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            );

            CREATE INDEX IX_{SQL_TABLE}_serial_ecm
                ON {SQL_SCHEMA}.{SQL_TABLE} (serial, ecm_name, flash_file, fecha_corrida DESC);
        END
    """)
    conn.commit()


def _normalizar_para_comparar(valor):
    """
    Convierte un valor a su representación de texto para comparar de forma
    consistente, sin importar si llegó como bool/int/str desde la API o
    como texto desde SQL (ej. NVARCHAR siempre vuelve como str, mientras
    que la API puede entregar True/False como bool real) — sin esto, se
    generaban falsos positivos de "cambio" en casi cada corrida.
    """
    if valor is None:
        return None
    return str(valor)


def cargar_ultimo_estado_sql(conn):
    """
    Devuelve un diccionario {(serial, ecm_name, flash_file): (campos
    comparables...)} con el último estado conocido de cada ECM físico,
    para poder detectar qué cambió en esta corrida.
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT serial, ecm_name, software_part_number, flash_file,
               release_date, file_size, latest_available, service_file_id
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY serial, ecm_name, flash_file
                       ORDER BY fecha_corrida DESC
                   ) AS rn
            FROM {SQL_SCHEMA}.{SQL_TABLE}
        ) t
        WHERE rn = 1
    """)

    estado = {}
    for row in cursor.fetchall():
        clave = _clave_ecm(row, es_row_sql=True)
        estado[clave] = tuple(
            _normalizar_para_comparar(getattr(row, campo)) for campo in CAMPOS_COMPARABLES
        )

    return estado


def guardar_cambios_en_sql(filas):
    """
    Compara 'filas' (resultados exitosos de esta corrida) contra el último
    estado conocido en SQL, e inserta SOLO las que son nuevas o cambiaron.
    Las filas de error (sin ecm_name, ver consultar_serial) no se guardan
    aquí — solo quedan en la consola de esta corrida.
    """
    if not _sql_habilitado():
        return

    conn = obtener_conexion_sql()
    try:
        asegurar_tabla_sql(conn)
        ultimo_estado = cargar_ultimo_estado_sql(conn)

        filas_a_insertar = []
        for fila in filas:
            if "ecm_name" not in fila:
                continue  # es una fila de error, no de resultado real

            clave = _clave_ecm(fila)
            valores_actuales = tuple(
                _normalizar_para_comparar(fila.get(campo)) for campo in CAMPOS_COMPARABLES
            )

            if ultimo_estado.get(clave) != valores_actuales:
                filas_a_insertar.append(fila)

        if not filas_a_insertar:
            print("Sin cambios respecto al último estado conocido en SQL.")
            return

        cursor = conn.cursor()
        cursor.fast_executemany = True
        cursor.executemany(
            f"""
            INSERT INTO {SQL_SCHEMA}.{SQL_TABLE}
                (serial, ecm_name, software_part_number, flash_file,
                 release_date, file_size, latest_available, service_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f["serial"], f.get("ecm_name"), f.get("software_part_number"),
                    f.get("flash_file"), f.get("release_date"), f.get("file_size"),
                    f.get("latest_available"), f.get("service_file_id"),
                )
                for f in filas_a_insertar
            ],
        )
        conn.commit()
        print(f"Insertadas {len(filas_a_insertar)} filas nuevas/cambiadas en "
              f"{SQL_SCHEMA}.{SQL_TABLE}")
    finally:
        conn.close()


def main():
    df_serials = cargar_equipos()
    seriales = df_serials["SerialNumber"].tolist()

    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(consultar_serial, s): s for s in seriales}

        for future in as_completed(futures):
            resultados.extend(future.result())

    df_resultados = pd.DataFrame(resultados)

    errores = df_resultados["status"].notna().sum() if "status" in df_resultados.columns else 0
    exitosos = len(df_resultados) - errores
    print(f"Consultas: {exitosos} filas exitosas, {errores} con error")

    if len(df_resultados) > 0 and exitosos == 0:
        print("ERROR: ninguna consulta fue exitosa (posible falla de autenticación o de red).")
        import sys
        sys.exit(1)

    # Respaldo local de cada corrida (útil para debug), el destino
    # definitivo del resultado es la tabla SQL (ver guardar_cambios_en_sql)
    output_path = Path("Results/resultado_sis2.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_resultados.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Archivo generado: {output_path} ({len(df_resultados)} filas)")

    guardar_cambios_en_sql(resultados)


if __name__ == "__main__":
    main()