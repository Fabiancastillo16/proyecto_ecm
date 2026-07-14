import os
import time
import json
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# =========================
# CREDENCIALES (desde .env, nunca hardcodeadas ni versionadas)
# =========================

load_dotenv()

SIS2_USERNAME = os.getenv("SIS2_USERNAME")
SIS2_PASSWORD = os.getenv("SIS2_PASSWORD")


def obtener_auth(headless: bool = True):

    if not SIS2_USERNAME or not SIS2_PASSWORD:
        raise RuntimeError(
            "Faltan credenciales. Crea un archivo .env (puedes copiar .env.example) "
            "con SIS2_USERNAME y SIS2_PASSWORD."
        )

    auth_path = Path("Authentication/auth.json")
    auth_path.parent.mkdir(parents=True, exist_ok=True)

    bearer_token = None
    cookie_dict = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # ==========================================
        # CAPTURAR REQUESTS Y BEARER
        # ==========================================
        def capture_request(request):
            nonlocal bearer_token
            auth = request.headers.get("authorization")
            if auth and auth.startswith("Bearer "):
                bearer_token = auth

        page.on("request", capture_request)

        # ==========================================
        # ABRIR SIS2
        # ==========================================
        print("Abriendo SIS2...")
        # "networkidle" se cuelga en sitios con polling/websockets de fondo
        # (muy común). "domcontentloaded" + timeout generoso es más confiable.
        page.goto("https://sis2.cat.com", wait_until="domcontentloaded", timeout=60000)

        # ==========================================
        # LLENAR LOGIN AUTOMÁTICAMENTE
        # ==========================================
        print("Rellenando formulario de login...")
        _autocompletar_login(page)

        # ==========================================
        # ESPERAR LOGIN COMPLETO
        # ==========================================
        print("Esperando confirmación de login...")
        timeout_seconds = 60
        start = time.time()

        while True:
            cookies = context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            tiene_login = "Sis2_Login" in cookie_dict
            tiene_refresh = "Sis2_Refresh" in cookie_dict

            if bearer_token and tiene_login and tiene_refresh:
                break

            if time.time() - start > timeout_seconds:
                debug_path = "Authentication/login_debug.png"
                page.screenshot(path=debug_path)
                browser.close()
                raise TimeoutError(
                    f"No se completó el login en {timeout_seconds}s. "
                    f"Revisa {debug_path} para ver en qué pantalla quedó "
                    "(útil para ajustar los selectores de _autocompletar_login)."
                )

            time.sleep(1)

        print("Login completado")

        # ==========================================
        # CREAR JSON
        # ==========================================
        auth_data = {
            "bearer": bearer_token,
            "cookies": {
                "Sis2_Login": cookie_dict.get("Sis2_Login"),
                "Sis2_Refresh": cookie_dict.get("Sis2_Refresh"),
                "JSESSIONID": cookie_dict.get("JSESSIONID"),
            },
        }

        with open(auth_path, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=4)

        print("Archivo auth.json creado")

        browser.close()
        print("Proceso de autenticación finalizado")

        return auth_data


def _autocompletar_login(page):
    """
    Llena el formulario de login de Azure AD B2C (usado por SIS2/Caterpillar).
    Es un flujo en DOS PASOS:
      1) Pantalla de usuario -> botón "Continue"
      2) Pantalla de password -> botón "Sign in" / "Continue"
    Prueba varios selectores porque las páginas B2C personalizadas a veces
    difieren un poco en nombres de campo (esto es normal en este tipo de login).
    """

    email_selectors = [
        "#signInName",
        "input[type='email']",
        "input[name='email']",
        "input[name='username']",
    ]
    continue_selectors = [
        "#continue",
        "button:has-text('Continue')",
        "button:has-text('Continuar')",
        "input[type='submit']",
        "button[type='submit']",
    ]
    password_selectors = [
        "#password",
        "input[type='password']",
    ]
    submit_selectors = [
        "#next",
        "button:has-text('Sign in')",
        "button:has-text('Iniciar sesión')",
        "button:has-text('Continue')",
        "button[type='submit']",
    ]

    # PASO 1: usuario
    email_field = _esperar_primero(page, email_selectors)
    email_field.fill(SIS2_USERNAME)

    continue_button = _esperar_primero(page, continue_selectors)
    continue_button.click()

    # PASO 2: password (aparece recién después de darle Continue)
    password_field = _esperar_primero(page, password_selectors, timeout=20000)
    password_field.fill(SIS2_PASSWORD)

    submit_button = _esperar_primero(page, submit_selectors)
    submit_button.click()


def _esperar_primero(page, selectors, timeout=15000):
    """Devuelve el primer selector de la lista que efectivamente aparezca."""
    per_selector_timeout = max(timeout // len(selectors), 2000)
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=per_selector_timeout)
            return locator
        except Exception:
            continue
    raise RuntimeError(
        f"No se encontró ningún campo con estos selectores: {selectors}. "
        "Corre obtener_auth(headless=False) una vez y usa el inspector de "
        "Playwright (o clic derecho > Inspeccionar en el navegador) para "
        "ver el id/name real del campo, luego agrégalo a la lista."
    )


if __name__ == "__main__":
    # La primera vez, corre con headless=False para ver el proceso y
    # confirmar que los selectores funcionan en tu pantalla real.
    obtener_auth(headless=False)