import requests
import pandas as pd
import time
import json
from pathlib import Path

from Authentication.auth_sis2 import obtener_auth

# =========================
# CONFIG
# =========================

AUTH_PATH = Path("Authentication/auth.json")


def cargar_auth():

    if not AUTH_PATH.exists():
        print("No existe auth.json. Iniciando autenticación...")
        return obtener_auth()

    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

BASE_URL = "https://sis2.cat.com/api/ws-all/ServiceSoftwareFilesRemoteServices/serialNumber"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/servicesoftwarefileservice-v3+json",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://sis2.cat.com/",
    "Origin": "https://sis2.cat.com"
}

COOKIES = {
    "JSESSIONID": "",
    "Sis2_Login": "",
    "Sis2_Refresh": ""}

# =========================
# SESSION
# =========================

session = requests.Session()

session.headers.update(HEADERS)

session.cookies.update(COOKIES)

# =========================
# READ CSV
# =========================

df_serials = pd.read_csv("Equipos.csv")

# =========================
# RESULTS
# =========================

resultados = []

# =========================
# LOOP
# =========================

for serial in df_serials["SerialNumber"]:

    serial = str(serial).strip()

    print(f"Consultando: {serial}")

    url = f"{BASE_URL}/{serial}?profileId=2"

    try:

        response = session.get(url, timeout=30)

        print("STATUS:", response.status_code)

        if response.status_code != 200:
            resultados.append({
                "serial": serial,
                "status": response.status_code,
                "error": response.text
            })
            continue

        data = response.json()

        ecms = data.get("ecms", [])

        for ecm in ecms:

            installed = ecm.get("installedFiles", {})

            resultados.append({

                "serial": serial,

                "ecm_name":
                    ecm.get("ecmDescription", {}).get("name"),

                "software_part_number":
                    ecm.get("softwarePartNumber"),

                "flash_file":
                    installed.get("latestFileName"),

                "release_date":
                    installed.get("latestFileReleaseDate"),

                "file_size":
                    installed.get("latestFileSizeInBytes"),

                "latest_available":
                    installed.get("latestAvailableFlag"),

                "service_file_id":
                    installed.get("serviceSoftwareFileID")
            })

        # Evita saturar API
        time.sleep(1)

    except Exception as e:

        resultados.append({
            "serial": serial,
            "status": "ERROR",
            "error": str(e)
        })

# =========================
# EXPORT
# =========================

df_resultados = pd.DataFrame(resultados)

df_resultados.to_csv(
    "resultado_sis22443dfdf.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Archivo generado: resultado_sis2.csv2")