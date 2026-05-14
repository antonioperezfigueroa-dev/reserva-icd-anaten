# actualización 14 mayo
print("VERSIÓN 14-MAY-2026 11:45 — Script corregido")

import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError

ICD_USER = os.getenv("ICD_USER")
ICD_PASS = os.getenv("ICD_PASS")

URL_LOGIN = "https://reservasicd.ceuta.es/a2SportWeb/login.aspx"
URL_MENU = "https://reservasicd.ceuta.es/a2SportWeb/Menu.aspx"

SERVICIO = "C.D. DIAZ FLOR"
SALA = "SALA CARDIO-FITNESS"

HORARIOS = {
    "Tuesday":  ("Wednesday", "07:00 - 08:00"),
    "Thursday": ("Friday",    "07:00 - 08:00"),
    "Saturday": ("Sunday",    "09:00 - 10:00")
}

# ---------------------------------------------------------
# FORZAR RESERVA PARA MAÑANA (modo automático)
# ---------------------------------------------------------
def obtener_fecha_reserva_forzada():
    fecha = datetime.now() + timedelta(days=1)
    return fecha.strftime("%d/%m/%Y")

def obtener_hora_reserva_forzada():
    manana = (datetime.now() + timedelta(days=1)).strftime("%A")
    for hoy, (dia_obj, hora) in HORARIOS.items():
        if dia_obj == manana:
            return hora
    return "07:00 - 08:00"


# ---------------------------------------------------------
# CLICK ROBUSTO CON REINTENTOS
# ---------------------------------------------------------
def click_con_reintento(page, texto, intentos=3):
    for i in range(intentos):
        try:
            page.get_by_text(texto, exact=False).click(timeout=8000)
            return
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(1)


# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------
def reservar(forzar_manana=True):

    if forzar_manana:
        fecha_reserva = obtener_fecha_reserva_forzada()
        hora_reserva = obtener_hora_reserva_forzada()
    else:
        raise Exception("Modo real desactivado para evitar reservas accidentales.")

    print(f"Fecha objetivo: {fecha_reserva}")
    print(f"Hora objetivo: {hora_reserva}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ❗ CORREGIDO: se elimina timeout del new_context()
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            )
        )

        page = context.new_page()

        try:
            # LOGIN
            print("Entrando al login…")
            page.goto(URL_LOGIN, wait_until="domcontentloaded", timeout=120000)
            page.fill("#txtUsuario", ICD_USER)
            page.fill("#txtPassword", ICD_PASS)
            page.click("#btnEntrar")
            page.wait_for_load_state("networkidle")

            # MENÚ
            print("Abriendo menú…")
            page.goto(URL_MENU, wait_until="domcontentloaded", timeout=120000)

            click_con_reintento(page, "Reserva de instalaciones")

            # SERVICIO
            print("Seleccionando servicio…")
            page.select_option("#ddlCentros", label=SERVICIO)
            time.sleep(1)

            # SALA
            print("Seleccionando sala…")
            click_con_reintento(page, SALA)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # FECHA
            print(f"Seleccionando fecha {fecha_reserva}…")
            page.fill("#txtFecha", fecha_reserva)
            page.keyboard.press("Enter")
            time.sleep(1)

            # HORA
            print(f"Seleccionando hora {hora_reserva}…")
            click_con_reintento(page, hora_reserva)
            time.sleep(1)

            # CHECKBOX
            print("Marcando aceptación del reglamento…")
            page.check("input[type='checkbox']")

            # RESERVAR
            print("Pulsando botón Reservar…")
            click_con_reintento(page, "Reservar")
            time.sleep(2)

            page.screenshot(path="captura_reserva.png")
            print("Reserva realizada correctamente.")

        finally:
            browser.close()


# ---------------------------------------------------------
# BUCLE DE REINTENTOS
# ---------------------------------------------------------
if __name__ == "__main__":
    for i in range(5):
        try:
            print(f"Intento {i+1}/5")
            reservar(forzar_manana=True)
            break
        except Exception as e:
            print("Error:", e)
            if i < 4:
                print("Reintentando en 5 segundos…")
                time.sleep(5)
            else:
                print("No se ha podido completar la reserva tras varios intentos.")
