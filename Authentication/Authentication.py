from zipfile import Path
from playwright.sync_api import sync_playwright
import time
import json

def obtener_auth():
    auth_path = Path("Authentication/auth.json")
    auth_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:

        browser = p.chromium.launch(
        headless=False,
        channel="chrome"
        )
        
        context = browser.new_context()

        page = context.new_page()

        bearer_token = None

        # ==========================================
        # CAPTURAR REQUESTS Y BEARER
        # ==========================================
        def capture_request(request):

            global bearer_token

            headers = request.headers

            auth = headers.get("authorization")

            # Capturar Bearer automáticamente
            if auth and auth.startswith("Bearer "):
                bearer_token = auth

        page.on("request", capture_request)

        # ==========================================
        # ABRIR SIS2
        # ==========================================
        print("Abriendo SIS2...")
        page.goto("https://sis2.cat.com")

        print("Esperando login del usuario...")

        # ==========================================
        # ESPERAR LOGIN COMPLETO
        # ==========================================
        while True:

            cookies = context.cookies()

            cookie_dict = {
                c["name"]: c["value"]
                for c in cookies
            }

            tiene_login = "Sis2_Login" in cookie_dict
            tiene_refresh = "Sis2_Refresh" in cookie_dict

            # Login válido
            if bearer_token and tiene_login and tiene_refresh:
                break

            time.sleep(1)

        print("Login completado")

        # ==========================================
        # MOSTRAR MENSAJE VISUAL
        # ==========================================
        page.set_content("""
        <html>
            <body style="
                font-family: Arial;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
                background:#f5f5f5;
            ">
                <div style="
                    text-align:center;
                    background:white;
                    padding:40px;
                    border-radius:10px;
                    box-shadow:0 0 10px rgba(0,0,0,0.1);
                ">
                    <h1>Login exitoso</h1>

                    <p>
                        Extrayendo información de softwares...
                    </p>

                    <p>
                        La ventana se cerrará automáticamente .
                    </p>
                </div>
            </body>
        </html>
        """)

        # ==========================================
        # CREAR JSON
        # ==========================================
        auth_data = {
            "bearer": bearer_token,
            "cookies": {
                "Sis2_Login": cookie_dict.get("Sis2_Login"),
                "Sis2_Refresh": cookie_dict.get("Sis2_Refresh"),
                "JSESSIONID": cookie_dict.get("JSESSIONID")
            }
        }

        # ==========================================
        # GUARDAR ARCHIVO
        # ==========================================
        with open(auth_path, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=4)

        print("Archivo auth.json creado")

        # Esperar un poco para que el usuario vea el mensaje
        time.sleep(5)

        # ==========================================
        # CERRAR NAVEGADOR
        # ==========================================
        browser.close()

        print("Proceso de autenticación finalizado")

        return auth_data
    
if __name__ == "__main__":
    obtener_auth()