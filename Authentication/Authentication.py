import os
import time
import json
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# =========================
# CREDENCIALES (desde .env, nunca hardcodeadas ni versionadas)
# =========================

load_dotenv(encoding="utf-8-sig")  # utf-8-sig tolera un BOM inicial si existe (Windows suele agregarlo al guardar)

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

        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()

        def capture_request(request):
            nonlocal bearer_token
            auth = request.headers.get("authorization")
            if auth and auth.startswith("Bearer "):
                bearer_token = auth

        page.on("request", capture_request)

        print("Abriendo SIS2...")
        page.goto("https://sis2.cat.com", wait_until="domcontentloaded", timeout=60000)

        _aceptar_cookies_si_aparece(page)
        _autocompletar_login(page)

        timeout_seconds = 60
        start = time.time()

        while True:
            cookies = context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            if bearer_token and "Sis2_Login" in cookie_dict and "Sis2_Refresh" in cookie_dict:
                break

            if time.time() - start > timeout_seconds:
                debug_path = "Authentication/login_debug.png"
                try:
                    print(f"DIAGNOSTICO - URL actual: {page.url}")
                    print(f"DIAGNOSTICO - Titulo de pagina: {page.title()}")
                    print(f"DIAGNOSTICO - Cookies presentes: {list(cookie_dict.keys())}")
                    print(f"DIAGNOSTICO - Bearer capturado: {bearer_token is not None}")
                    page.screenshot(path=debug_path, full_page=True)
                except Exception as diag_error:
                    print(f"DIAGNOSTICO - Error obteniendo diagnostico: {diag_error}")
                browser.close()
                raise TimeoutError(
                    f"No se completó el login en {timeout_seconds}s. "
                    f"Revisa {debug_path} para ver en qué pantalla quedó."
                )

            time.sleep(1)

        print("Login completado")

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

        browser.close()

        return auth_data


def _aceptar_cookies_si_aparece(page, timeout=6000):
    """
    Cierra el banner de consentimiento de cookies (OneTrust) si aparece.
    No es bloqueante: si no aparece, sigue sin hacer nada.
    """
    accept_selectors = [
        "#onetrust-accept-btn-handler",
        "button:has-text('I Accept')",
        "button:has-text('Accept')",
        "button:has-text('Aceptar')",
    ]
    for selector in accept_selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click()
            return
        except Exception:
            continue


def _autocompletar_login(page):
    """
    Llena el formulario de login de Azure AD B2C (usado por SIS2/Caterpillar).
    Es un flujo en dos pantallas: usuario -> Continue -> password -> enviar.
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

    email_field = _esperar_primero(page, email_selectors)
    email_field.fill(SIS2_USERNAME)

    continue_button = _esperar_primero(page, continue_selectors)
    continue_button.click()

    _aceptar_cookies_si_aparece(page)

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
        "Corre obtener_auth(headless=False) para ver el HTML real del formulario."
    )


if __name__ == "__main__":
    obtener_auth(headless=False)