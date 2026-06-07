import socket
import threading
import os
import random
import smtplib
from email.mime.text import MIMEText

HOST = '0.0.0.0'
PORT = 55555

# === VALÓDI E-MAIL KÜLDÉS (A te adataid) ===
KULDO_EMAIL = "fidesz77@gmail.com"
GMAIL_APP_JELSZO = "wplu xhbm vlqt nezs" # Ide jön a 16 betűs app jelszavad!

kliensek = {} 
kapcsolatok_forditva = {} 
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
        print(f"[E-MAIL HIBA] Konzolos kód: {kod} (Hiba: {e})")

def online_lista_szetkuldes():
    nevek = ",".join(kliensek.values())
    for kapcsolat in kliensek.keys():
        try:
            kapcsolat.sendall(f"ONLINE_LISTA|{nevek}\n".encode('utf-8'))
        except: pass

def uzenet_szetkuldes(uzenet_szoveg):
    for kapcsolat in kliensek.keys():
        try:
            kapcsolat.sendall(f"GLOBAL|{uzenet_szoveg}\n".encode('utf-8'))
        except: pass

def kliens_kezeles(kapcsolat, cim):
    bejelentkezo_fazis = True
    nev = ""
    maradek = ""

    try:
        while bejelentkezo_fazis:
            adat = kapcsolat.recv(1024).decode('utf-8')
            if not adat: return
            
            reszek = adat.strip().split("|")
            parancs = reszek[0]
            regisztralt_fiokok = felhasznalok_betoltese()

            if parancs == "KOD_KERES":
                email = reszek[1]
                kod = str(random.randint(100000, 999999))
                ideiglenes_kodok[email] = kod
                threading.Thread(target=email_kuldes, args=(email, kod), daemon=True).start()
                kapcsolat.sendall("OK|Kód elküldve!\n".encode('utf-8'))

            elif parancs == "REGISZTRACIO":
                u, p, e, k = reszek[1], reszek[2], reszek[3], reszek[4]
                if u in regisztralt_fiokok:
                    kapcsolat.sendall("HIBA|A név foglalt!\n".encode('utf-8'))
                elif ideiglenes_kodok.get(e) != k:
                    kapcsolat.sendall("HIBA|Hibás kód!\n".encode('utf-8'))
                else:
                    regisztralt_fiokok[u] = {"jelszo": p, "email": e}
                    felhasznalok_mentese_mind(regisztralt_fiokok)
                    kapcsolat.sendall("OK|Sikeres!\n".encode('utf-8'))

            elif parancs == "BEJELENTKEZES":
                u, p = reszek[1], reszek[2]
                if u in regisztralt_fiokok and regisztralt_fiokok[u]["jelszo"] == p:
                    if u in kliensek.values():
                        kapcsolat.sendall("HIBA|Már online!\n".encode('utf-8'))
                    else:
                        kapcsolat.sendall("OK|Sikeres\n".encode('utf-8'))
                        bejelentkezo_fazis = False
                        nev = u
                        kliensek[kapcsolat] = nev
                        kapcsolatok_forditva[nev] = kapcsolat
                        print(f"[BELÉPETT] {nev}")
                        online_lista_szetkuldes()
                        uzenet_szetkuldes(f"[RENDSZER] {nev} csatlakozott.")
                else:
                    kapcsolat.sendall("HIBA|Hibás adatok!\n".encode('utf-8'))

            elif parancs == "TORLES":
                u, p = reszek[1], reszek[2]
                if u in regisztralt_fiokok and regisztralt_fiokok[u]["jelszo"] == p:
                    del regisztralt_fiokok[u]
                    felhasznalok_mentese_mind(regisztralt_fiokok)
                    kapcsolat.sendall("OK|Fiók törölve!\n".encode('utf-8'))
                else:
                    kapcsolat.sendall("HIBA|Hibás adatok!\n".encode('utf-8'))

        # --- CHAT FÁZIS ---
        while True:
            adat = kapcsolat.recv(1024)
            if not adat: break
            
            maradek += adat.decode('utf-8')
            while "\n" in maradek:
                sor, maradek = maradek.split("\n", 1)
                if not sor: continue
                
                if sor.startswith("PRIVAT|"):
                    _, ki_kapja, tiszta_uzi = sor.split("|", 2)
                    if ki_kapja in kapcsolatok_forditva:
                        kapcsolatok_forditva[ki_kapja].sendall(f"PRIVAT|{nev}|{tiszta_uzi}\n".encode('utf-8'))
                        kapcsolat.sendall(f"PRIVAT|{ki_kapja}|{tiszta_uzi}\n".encode('utf-8'))
                else:
                    print(f"[GLOBAL] {nev}: {sor}")
                    uzenet_szetkuldes(f"[{nev}]: {sor}")

    except: pass
    finally:
        if kapcsolat in kliensek:
            print(f"[KILÉPETT] {nev}")
            del kliensek[kapcsolat]
            if nev in kapcsolatok_forditva: del kapcsolatok_forditva[nev]
            online_lista_szetkuldes()
            uzenet_szetkuldes(f"[RENDSZER] {nev} kilépett.")
        try: kapcsolat.close()
        except: pass

if __name__ == "__main__":
    szerver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    szerver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    szerver.bind((HOST, PORT))
    szerver.listen()
    print("==================================================")
    print(" SZERVER FUT - PRIVÁT CHAT + KERESŐ AKTIVÁLVA     ")
    print("==================================================")
    while True:
        kapcs, cim = szerver.accept()
        threading.Thread(target=kliens_kezeles, args=(kapcs, cim), daemon=True).start()