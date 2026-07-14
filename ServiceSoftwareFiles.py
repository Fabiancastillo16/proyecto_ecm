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


def _forzar_relogin():
    """Reautentica una sola vez aunque varios threads lo pidan a la vez."""
    global _session_actual
    with _auth_lock:
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

        # Token vencido a mitad de la corrida -> reautentica una vez y reintenta
        if response.status_code in (401, 403):
            session = _forzar_relogin()
            response = session.get(url, timeout=30)

        print(f"{serial}: STATUS {response.status_code}")

        if response.status_code != 200:
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
      - Si hay config de ADLS (ADLS_STORAGE_ACCOUNT + ADLS_FILESYSTEM),
        descarga el/los CSV que encuentre dentro de ADLS_INPUT_DIRECTORY
        (la carpeta donde cae el resultado de la query) y los concatena.
      - Si no hay config de ADLS (ej. corriendo en tu máquina local),
        usa el Equipos.csv local de siempre.
    """
    file_system_client = _obtener_file_system_client()
    input_directory = os.getenv("ADLS_INPUT_DIRECTORY")

    if file_system_client is None or not input_directory:
        print("Cargando Equipos.csv local...")
        return pd.read_csv("Equipos.csv")

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
        print(f"  Descargando: {path}")
        file_client = file_system_client.get_file_client(path)
        contenido = file_client.download_file().readall()

        import io
        dataframes.append(pd.read_csv(io.BytesIO(contenido)))

    df_equipos = pd.concat(dataframes, ignore_index=True)

    # Por si la query exporta el mismo equipo repetido en más de un archivo
    df_equipos = df_equipos.drop_duplicates(subset=["SerialNumber"])

    print(f"Equipos cargados desde ADLS: {len(df_equipos)}")
    return df_equipos


def subir_a_adls_si_corresponde(local_path: Path):
    """
    Si hay variables de entorno de ADLS configuradas, sube el resultado a
    ADLS_OUTPUT_DIRECTORY. Si no están configuradas (ej. corriendo en tu
    máquina local), no hace nada: el CSV se queda solo en Results/.
    """
    file_system_client = _obtener_file_system_client()
    directory = os.getenv("ADLS_OUTPUT_DIRECTORY", "")

    if file_system_client is None:
        return

    relative_path = f"{directory}/{local_path.name}".strip("/")
    file_client = file_system_client.get_file_client(relative_path)

    with open(local_path, "rb") as f:
        contenido = f.read()

    file_client.upload_data(contenido, overwrite=True)
    print(f"Subido a ADLS: {relative_path}")


def main():
    df_serials = cargar_equipos()
    seriales = df_serials["SerialNumber"].tolist()

    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(consultar_serial, s): s for s in seriales}

        for future in as_completed(futures):
            resultados.extend(future.result())

    df_resultados = pd.DataFrame(resultados)

    output_path = Path("Results/resultado_sis2.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_resultados.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Archivo generado: {output_path} ({len(df_resultados)} filas)")

    subir_a_adls_si_corresponde(output_path)


if __name__ == "__main__":
    main()