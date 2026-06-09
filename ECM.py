import requests
import pandas as pd
import time

# =========================
# CONFIG
# =========================

TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjREWFlYTk9BbThmeC0zU2w2UUxEbTlFbGZ2R0c3amd3U0ZheDdyOWVLY2siLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI3YzdjNDUzMy0wOTkzLTRjODUtYjM2OC0zOTlkMTU1NDc2Y2QiLCJpc3MiOiJodHRwczovL3NpZ25pbi5jYXQuY29tL3RmcC80ZjBmMTlkMC1mNDRjLTRhMDMtYjhjYi1hYjMyN2JkMmIxMmIvYjJjXzFhX3AyX3YxX3NpZ25pbl9wcm9kL3YyLjAvIiwiZXhwIjoxNzc5MDM2MDcxLCJuYmYiOjE3NzkwMzI0NzEsImNsaWVudF9pZCI6IjdjN2M0NTMzLTA5OTMtNGM4NS1iMzY4LTM5OWQxNTU0NzZjZCIsImNhdGFmbHRuY2xhc3MiOiJETFIiLCJjYXRsb2dpbmlkIjoicjEyMGZjNDIiLCJjYXRyZWNpZCI6IlBTUC0wMDBCRUU3OSIsImNhdGFmbHRuY29kZSI6IjAwNSIsImNvdW50cnkiOiJDTCIsImVtYWlsX2FkZHJlc3MiOiJGYWJpYW4uQ2FzdGlsbG9AZmlubmluZy5jb20iLCJzdWIiOiIwNmQ2ZDFmYy03NjExLTQ0ZDYtYjVmZS0wYTMzNzQ0NmFmYTMiLCJuYW1lIjoiRmFiaWFuIENhc3RpbGxvIiwiZ2l2ZW5fbmFtZSI6IkZhYmlhbiIsImZhbWlseV9uYW1lIjoiQ2FzdGlsbG8iLCJjb21wYW55IjoiRklOTklORyBDSElMRSIsImNhdGN1cGlkIjoiOTk4OTc0NjEyMCIsInByZWZlcnJlZExhbmd1YWdlIjoiZXMiLCJjYXRhZmx0bm9yZ2NvZGUiOiJSMTIwIiwiY2F0dG9wbGV2ZWxvcmdjb2RlIjoiUjEyMCIsInRpZCI6IjRmMGYxOWQwLWY0NGMtNGEwMy1iOGNiLWFiMzI3YmQyYjEyYiIsInRmcCI6IkIyQ18xQV9QMl9WMV9TaWduSW5fUHJvZCIsImxhbmd1YWdlIjoiZXMiLCJhenAiOiI3YzdjNDUzMy0wOTkzLTRjODUtYjM2OC0zOTlkMTU1NDc2Y2QiLCJ2ZXIiOiIxLjAiLCJpYXQiOjE3NzkwMzI0NzF9.UCoV255v0uX1J0O0RFCi61VEunkzb7bFX2CX8Zl9KLYhFLWf-HmYIpaQqM3kWjpk639VbUMiclW4xcYCCBJYh1iPwbt-vO8UnmJQYGIkC-x5MoGW6xROHPOoIPIPb5U4XjnhLL85nUJCH8oVhuHNykwnA2HF4Xo93kQPQCA15cOsWQlRduRh3q3_KwAEjh7qfrudrct2TWZmx0_OdiX9OzbRToDHJpoLKdoVW3WHxl2mI1BiiVBrYBabHH6l9fgF4iTYQJ5xZi4jelxttJB3A8gW4w5Wx8-yPd10nSP4N_q9oTu3-4S76u2GN0-pW4DpEtfQw2x-L2B1AEwZfDMW1Q"

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
    "resultado_sis2.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Archivo generado: resultado_sis2.csv")