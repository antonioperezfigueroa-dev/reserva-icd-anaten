import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

ICD_USER = os.getenv("ICD_USER")
ICD_PASS = os.getenv("ICD_PASS")

URL_LOGIN = "https://reservasicd.ceuta.es/a2SportWeb/login.aspx"
URL_MENU = "https://reservasicd.ceuta.es/a2SportWeb/Menu.aspx"

SERVICIO = "C.D. DIAZ FLOR"
SALA = "SALA CARDIO-FITNESS"

# Horarios según día
HORARIOS = {
    "Tuesday":  ("Wednesday", "07:00 - 08:00"),
    "Thursday": ("Friday",    "07:00 - 08:00"),
    "Saturday": ("Sunday",    "09:00 - 10:00")
}

def obtener_fecha_reserva():
    hoy = datetime.now().strftime("%A")
    if hoy not in HORARIOS:
        raise Exception("Hoy no toca reservar.")
    dia_objetivo, _ = HORARIOS[hoy]
    dias_semana = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    idx_hoy = dias_semana.index(hoy)
    idx_obj = dias_semana.index(dia_objetivo)
    dias_despues = (idx_obj - idx_hoy) % 7
    fecha = datetime.now() + timedelta(days=dias_despues)
    return fecha.strftime("%d/%m/%Y")

def obtener_hora_reserva():
    hoy = datetime.now().strftime("%A")
    return HORARIOS[hoy][1]

def reservar():
    fecha_reserva = obtener_fecha_reserva()
    hora_reserva = obtener_hora_reserva()

    print(f"Fecha objetivo: {fecha_reserva}")
    print(f"Hora objetivo: {hora_reserva}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # LOGIN
        print("Entrando al login…")
        page.goto(URL_LOGIN)
        page.fill("#txtUsuario", ICD_USER)
        page.fill("#txtPassword", ICD_PASS)
        page.click("#btnEntrar")
        page.wait_for_load_state("networkidle")

        # MENÚ → RESERVA DE INSTALACIONES
        print("Abriendo menú…")
        page.goto(URL_MENU)
        page.wait_for_load_state("networkidle")

        page.click("text=Reserva de instalaciones")
        page.wait_for_load_state("networkidle")

        # FILTRO DE SERVICIO
        print("Seleccionando servicio…")
        page.select_option("#ddlCentros", label=SERVICIO)
        time.sleep(1)

        # SELECCIONAR SALA
        print("Seleccionando sala…")
        page.click(f"text={SALA}")
        page.wait_for_load_state("networkidle")

        # SELECCIONAR FECHA
        print(f"Seleccionando fecha {fecha_reserva}…")
        page.fill("#txtFecha", fecha_reserva)
        page.keyboard.press("Enter")
        time.sleep(1)

        # SELECCIONAR HORA
        print(f"Seleccionando hora {hora_reserva}…")
        page.click(f"text={hora_reserva}")

        # CONFIRMAR
        print("Confirmando reserva…")
        page.click("text=Confirmar")
        time.sleep(2)

        page.screenshot(path="captura_reserva.png")
        print("Reserva realizada correctamente.")

        browser.close()


if __name__ == "__main__":
    for i in range(5):
        try:
            print(f"Intento {i+1}/5")
            reservar()
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(
