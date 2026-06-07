import asyncio
import os
import random
import smtplib
import json
from email.mime.text import MIMEText
import websockets

# A Render automatikusan ad egy PORT környezeti változót, ezt kötelező beolvasni!
PORT = int(os.environ.get("PORT", 55555))
HOST = "0.0.0.0"

# === GMAIL BEÁLLÍTÁSOK ===
KULDO_EMAIL = "fidesz77@gmail.com"
GMAIL_APP_JELSZO = "wplu xhbm vlqt nezs"

# Az online klienseket most egy szótárban tároljuk: websocket_objektum -> felhasználónév
kliensek = {} 
ideiglenes_kodok = {} 
JELSZO_FAJL = "felhasznalok.txt"

def felhasznalok_betoltese():
    adatok = {}
    if os.path.exists(JELSZO_FAJL):
        with open(JELSZO_FAJL, "r", encoding="utf-8") as f:
            for sor in f:
                if ":" in sor:
                    reszek = sor.strip().split(":")
                    if len(reszek) == 3:
                        u, p, e = reszek
                        adatok[u] = {"jelszo": p, "email": e}
    return adatok

def felhasznalok_mentese_mind(adatok):
    with open(JELSZO_FAJL, "w", encoding="utf-8") as f:
        for u, info in adatok.items():
            f.write(f"{u}:{info['jelszo']}:{info['email']}\n")

def email_kuldes(hova, kod):
    try:
        msg = MIMEText(f"A HexaChat regisztrációs kódod: {kod}")
        msg['Subject'] = 'HexaChat Aktiválás'
        msg['From'] = KULDO_EMAIL
        msg['To'] = hova
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as szerver:
            szerver.login(KULDO_EMAIL, GMAIL_APP_JELSZO)
            szerver.send_message(msg)
        print(f"[E-MAIL] Elküldve ide: {hova}")
    except Exception as e:
        print(f"[E-MAIL HIBA] Hiba történt: {e}")

async def online_lista_szetkuldes():
    nevek = ",".join(kliensek.values())
    if kliensek:
        # Minden online embernek elküldjük az új listát
        uzenet = f"ONLINE_LISTA|{nevek}\n"
        await asyncio.gather(*[ws.send(uzenet) for ws in kliensek.keys()], return_exceptions=True)

async def uzenet_szetkuldes(uzenet_szoveg):
    if kliensek:
        uzenet = f"GLOBAL|{uzenet_szoveg}\n"
        await asyncio.gather(*[ws.send(uzenet) for ws in kliensek.keys()], return_exceptions=True)

async def kliens_kezeles(websocket):
    nev = ""
    kliensek[websocket] = "" # Ideiglenesen regisztráljuk a kapcsolatot
    
    try:
        async for adat in websocket:
            reszek = adat.strip().split("|")
            if not reszek or not reszek[0]:
                continue
                
            parancs = reszek[0]
            regisztralt_fiokok = felhasznalok_betoltese()

            if parancs == "KOD_KERES":
                email = reszek[1]
                kod = str(random.randint(100000, 999999))
                ideiglenes_kodok[email] = kod
                # Az e-mail küldést külön szálon futtatjuk, hogy ne akassza meg a szervert
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, email_kuldes, email, kod)
                await websocket.send("OK|Kód elküldve!\n")

            elif parancs == "REGISZTRACIO":
                u, p, e, k = reszek[1], reszek[2], reszek[3], reszek[4]
                if u in regisztralt_fiokok:
                    await websocket.send("HIBA|A név foglalt!\n")
                elif ideiglenes_kodok.get(e) != k:
                    await websocket.send("HIBA|Hibás kód!\n")
                else:
                    regisztralt_fiokok[u] = {"jelszo": p, "email": e}
                    felhasznalok_mentese_mind(regisztralt_fiokok)
                    await websocket.send("OK|Sikeres!\n")

            elif parancs == "BEJELENTKEZES":
                u, p = reszek[1], reszek[2]
                if u in regisztralt_fiokok and regisztralt_fiokok[u]["jelszo"] == p:
                    if u in kliensek.values():
                        await websocket.send("HIBA|Már online!\n")
                    else:
                        await websocket.send("OK|Sikeres\n")
                        nev = u
                        kliensek[websocket] = nev
                        print(f"[BELÉPETT] {nev}")
                        await online_lista_szetkuldes()
                        await uzenet_szetkuldes(f"[RENDSZER] {nev} csatlakozott.")
                else:
                    await websocket.send("HIBA|Hibás adatok!\n")

            elif parancs == "TORLES":
                u, p = reszek[1], reszek[2]
                if u in regisztralt_fiokok and regisztralt_fiokok[u]["jelszo"] == p:
                    del regisztralt_fiokok[u]
                    felhasznalok_mentese_mind(regisztralt_fiokok)
                    await websocket.send("OK|Fiók törölve!\n")
                else:
                    await websocket.send("HIBA|Hibás adatok!\n")

            elif parancs == "PRIVAT":
                if len(reszek) >= 3:
                    _, ki_kapja, tiszta_uzi = reszek[0], reszek[1], reszek[2]
                    # Keresük meg a célszemély websocket kapcsolatát
                    for ws, n in kliensek.items():
                        if n == ki_kapja:
                            await ws.send(f"PRIVAT|{nev}|{tiszta_uzi}\n")
                            break
                    await websocket.send(f"PRIVAT|{ki_kapja}|{tiszta_uzi}\n")
            
            elif nev: # Ha nincs parancs, de be van jelentkezve, akkor az GLOBAL üzenet
                print(f"[GLOBAL] {nev}: {adat}")
                await uzenet_szetkuldes(f"[{nev}]: {adat}")

    except Exception as e:
        print(f"[HIBA] {e}")
    finally:
        if websocket in kliensek:
            old_nev = kliensek[websocket]
            del kliensek[websocket]
            if old_nev:
                print(f"[KILÉPETT] {old_nev}")
                await online_lista_szetkuldes()
                await uzenet_szetkuldes(f"[RENDSZER] {old_nev} kilépett.")

async def main():
    print("==================================================")
    print(f" RENDER WEBSOCKET SZERVER INDUL PORTON: {PORT}  ")
    print("==================================================")
    async with websockets.serve(kliens_kezeles, HOST, PORT):
        await asyncio.Future() # keep-alive folyamatos futás

if __name__ == "__main__":
    asyncio.run(main())
