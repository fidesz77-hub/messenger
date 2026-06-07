import socket
import threading
import tkinter as tk
from tkinter import messagebox
import urllib.request
import sys
import os

SZERVER_IP = "127.0.0.1" 
PORT = 55555
AKTUALIS_VERZIO = "4.0"

VERZIO_URL = "https://raw.githubusercontent.com/hegedus/messenger/main/verzio.txt"
KOD_URL = "https://raw.githubusercontent.com/hegedus/messenger/main/messenger_kliens.py"

NYELVEK = {
    "magyar": {
        "title": "Bejelentkezés", "reg_title": "Regisztráció", "user": "Felhasználónév:", "pass": "Jelszó:",
        "email": "E-mail cím:", "code": "E-mailre kapott kód:", "btn_login": "Bejelentkezés",
        "btn_reg_link": "Nincs még fiókom", "btn_back": "Vissza", "btn_send_code": "Kód küldése",
        "btn_create": "Fiók létrehozása", "btn_delete": "Fiók törlése", "update_avail": "Új verzió! Frissítés",
        "err_fields": "Minden mezőt ki kell tölteni!", "err_conn": "Szerver nem elérhető!", "online_users": "Emberek:", 
        "search": "Keresés...", "btn_world_chat": "Online Chat (Világ)", "global_title": "VILÁG CHAT", "private_title": "Privát chat vele: "
    },
    "angol": {
        "title": "Login", "reg_title": "Registration", "user": "Username:", "pass": "Password:",
        "email": "Email:", "code": "Code:", "btn_login": "Login",
        "btn_reg_link": "No account?", "btn_back": "Back", "btn_send_code": "Send Code",
        "btn_create": "Register", "btn_delete": "Delete Account", "update_avail": "New version! Update",
        "err_fields": "Fill all fields!", "err_conn": "Server unreachable!", "online_users": "People:", 
        "search": "Search...", "btn_world_chat": "Online Chat (World)", "global_title": "WORLD CHAT", "private_title": "Private chat with: "
    },
    "amerikai": {
        "title": "Sign In", "reg_title": "Sign Up", "user": "Username:", "pass": "Password:",
        "email": "Email:", "code": "Code:", "btn_login": "Sign In",
        "btn_reg_link": "Create account", "btn_back": "Back", "btn_send_code": "Get Code",
        "btn_create": "Sign Up", "btn_delete": "Delete Account", "update_avail": "Update Available!",
        "err_fields": "Fields required!", "err_conn": "Connection failed!", "online_users": "Users:", 
        "search": "Search user...", "btn_world_chat": "Online Chat (Global)", "global_title": "GLOBAL CHAT", "private_title": "Direct message: "
    },
    "sved": {
        "title": "Logga in", "reg_title": "Registrering", "user": "Användarnamn:", "pass": "Lösenord:",
        "email": "E-post:", "code": "Kod:", "btn_login": "Logga in",
        "btn_reg_link": "Inget konto?", "btn_back": "Tillbaka", "btn_send_code": "Skicka kod",
        "btn_create": "Registrera", "btn_delete": "Ta bort konto", "update_avail": "Uppdatera nu!",
        "err_fields": "Fyll i alla fält!", "err_conn": "Serverfel!", "online_users": "Användare:", 
        "search": "Sök...", "btn_world_chat": "Online Chat (Värld)", "global_title": "VÄRLDSCHAT", "private_title": "Privat chatt med: "
    },
    "japan": {
        "title": "ログイン", "reg_title": "新規登録", "user": "ユーザー名:", "pass": "パスワード:",
        "email": "メール:", "code": "コード:", "btn_login": "ログイン",
        "btn_reg_link": "アカウントなし", "btn_back": "戻る", "btn_send_code": "送信",
        "btn_create": "登録する", "btn_delete": "削除する", "update_avail": "更新あり！",
        "err_fields": "入力してください！", "err_conn": "接続失敗！", "online_users": "ユーザー一覧:", 
        "search": "検索...", "btn_world_chat": "オンラインチャット (世界)", "global_title": "ワールドチャット", "private_title": "個別チャット: "
    },
    "orosz": {
        "title": "Вход", "reg_title": "Регистрация", "user": "Имя:", "pass": "Пароль:",
        "email": "Почта:", "code": "Код:", "btn_login": "Войти",
        "btn_reg_link": "Нет аккаунта?", "btn_back": "Назад", "btn_send_code": "Код",
        "btn_create": "Создать", "btn_delete": "Удалить", "update_avail": "Обновить!",
        "err_fields": "Заполните поля!", "err_conn": "Ошибка сервера!", "online_users": "Пользователи:", 
        "search": "Поиск...", "btn_world_chat": "Онлайн Чат (Мир)", "global_title": "ОБЩИЙ ЧАТ", "private_title": "Личный чат с: "
    }
}

class ChatKliens:
    def __init__(self, root):
        self.root = root
        self.root.title(f"HexaChat v{AKTUALIS_VERZIO}")
        self.root.geometry("700x550")
        
        self.kapcsolat = None
        self.aktiv_nyelv = "magyar"
        self.felhasznalonev = ""
        self.minden_online_felhasznalo = [] 
        
        # Chat memóriák (hogy ne vesszen el az üzenet, ha váltasz a szobák között)
        self.aktualis_szoba = "GLOBAL" # "GLOBAL" vagy egy felhasználónév
        self.global_chat_tortenet = ""
        self.privat_chat_tortenetek = {} # {felhasznalonev: "szöveg"}
        
        self.bejelentkezo_kepernyo()
        self.frissites_ellenorzes()

    def n(self, kulcs): return NYELVEK[self.aktiv_nyelv][kulcs]

    def frissites_ellenorzes(self):
        try:
            valasz = urllib.request.urlopen(VERZIO_URL, timeout=2)
            legujabb = valasz.read().decode('utf-8').strip()
            if legujabb != AKTUALIS_VERZIO:
                tk.Button(self.root, text=f"⚠️ {self.n('update_avail')} (v{legujabb})", bg="red", fg="white", command=self.program_frissitese).pack(fill=tk.X, side=tk.TOP)
        except: pass

    def program_frissitese(self):
        try:
            uj_kod = urllib.request.urlopen(KOD_URL).read()
            with open(os.path.basename(__file__), "wb") as f: f.write(uj_kod)
            messagebox.showinfo("HexaChat", "Frissítve! Újraindítás...")
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e: messagebox.showerror("Hiba", str(e))

    def nyelv_valtas(self, uj_nyelv, tipus):
        self.aktiv_nyelv = uj_nyelv
        if tipus == "LOGIN": self.bejelentkezo_kepernyo()
        else: self.regisztracios_kepernyo()

    def nyelv_valaszto_panel(self, tipus):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        for c, ny in [("HU","magyar"), ("EN","angol"), ("US","amerikai"), ("SE","sved"), ("JP","japan"), ("RU","orosz")]:
            bg = "yellow" if self.aktiv_nyelv == ny else "lightgray"
            tk.Button(frame, text=c, bg=bg, font=("Arial", 8), command=lambda n=ny: self.nyelv_valtas(n, tipus)).pack(side=tk.LEFT, padx=2)

    def bejelentkezo_kepernyo(self):
        self.tisztitas()
        self.nyelv_valaszto_panel("LOGIN")
        tk.Label(self.root, text=self.n("title").upper(), font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self.root, text=self.n("user")).pack()
        self.nev_input = tk.Entry(self.root, font=("Arial", 12)); self.nev_input.pack()
        tk.Label(self.root, text=self.n("pass")).pack()
        self.jelszo_input = tk.Entry(self.root, font=("Arial", 12), show="*"); self.jelszo_input.pack()
        tk.Button(self.root, text=self.n("btn_login"), bg="lightgreen", font=("Arial", 12), command=self.szerver_bejelentkezes).pack(pady=10)
        tk.Button(self.root, text=self.n("btn_delete"), bg="red", fg="white", command=self.szerver_fiok_torles).pack()
        tk.Button(self.root, text=self.n("btn_reg_link"), fg="blue", bd=0, command=self.regisztracios_kepernyo).pack(pady=10)

    def regisztracios_kepernyo(self):
        self.tisztitas()
        self.nyelv_valaszto_panel("REG")
        tk.Label(self.root, text=self.n("reg_title").upper(), font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(self.root, text=self.n("user")).pack()
        self.nev_input = tk.Entry(self.root, font=("Arial", 12)); self.nev_input.pack()
        tk.Label(self.root, text=self.n("pass")).pack()
        self.jelszo_input = tk.Entry(self.root, font=("Arial", 12), show="*"); self.jelszo_input.pack()
        tk.Label(self.root, text=self.n("email")).pack()
        self.email_input = tk.Entry(self.root, font=("Arial", 12)); self.email_input.pack()
        tk.Button(self.root, text=self.n("btn_send_code"), bg="orange", command=self.szerver_kod_keres).pack(pady=3)
        tk.Label(self.root, text=self.n("code")).pack()
        self.kod_input = tk.Entry(self.root, font=("Arial", 12)); self.kod_input.pack()
        tk.Button(self.root, text=self.n("btn_create"), bg="lightblue", font=("Arial", 12), command=self.szerver_regisztracio).pack(pady=10)
        tk.Button(self.root, text=self.n("btn_back"), fg="blue", bd=0, command=self.bejelentkezo_kepernyo).pack()

    def kapcsolodas(self):
        try:
            if not self.kapcsolat:
                self.kapcsolat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.kapcsolat.connect((SZERVER_IP, PORT))
            return True
        except: messagebox.showerror("Hiba", self.n("err_conn")); return False

    def szerver_kod_keres(self):
        e = self.email_input.get().strip()
        if e and self.kapcsolodas(): self.kapcsolat.sendall(f"KOD_KERES|{e}\n".encode('utf-8'))

    def szerver_regisztracio(self):
        u, p, e, k = self.nev_input.get().strip(), self.jelszo_input.get().strip(), self.email_input.get().strip(), self.kod_input.get().strip()
        if not u or not p or not e or not k: return
        if self.kapcsolodas():
            self.kapcsolat.sendall(f"REGISZTRACIO|{u}|{p}|{e}|{k}\n".encode('utf-8'))
            v = self.kapcsolat.recv(1024).decode('utf-8').strip().split("|")
            if v[0] == "OK": self.kapcsolat.close(); self.kapcsolat = None; self.bejelentkezo_kepernyo()
            else: messagebox.showerror("Hiba", v[1])

    def szerver_bejelentkezes(self):
        u, p = self.nev_input.get().strip(), self.jelszo_input.get().strip()
        if not u or not p: return
        if self.kapcsolodas():
            self.kapcsolat.sendall(f"BEJELENTKEZES|{u}|{p}\n".encode('utf-8'))
            v = self.kapcsolat.recv(1024).decode('utf-8').strip().split("|")
            if v[0] == "OK": self.felhasznalonev = u; self.chat_kepernyo()
            else: messagebox.showerror("Hiba", v[1]); self.kapcsolat.close(); self.kapcsolat = None

    def szerver_fiok_torles(self):
        u, p = self.nev_input.get().strip(), self.jelszo_input.get().strip()
        if u and p and self.kapcsolodas():
            self.kapcsolat.sendall(f"TORLES|{u}|{p}\n".encode('utf-8'))
            v = self.kapcsolat.recv(1024).decode('utf-8').strip().split("|")
            messagebox.showinfo("Szerver", v[1]); self.kapcsolat.close(); self.kapcsolat = None; self.bejelentkezo_kepernyo()

    def chat_kepernyo(self):
        self.tisztitas()
        
        bal_frame = tk.Frame(self.root)
        bal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        jobb_frame = tk.Frame(self.root, width=200, bg="lightgray")
        jobb_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Chat szoba címe (jelzi, hogy épp hol vagyunk)
        self.szoba_cimke = tk.Label(bal_frame, text=self.n("global_title"), font=("Arial", 12, "bold"), fg="darkblue")
        self.szoba_cimke.pack(anchor=tk.W, pady=2)

        # Fő Chat ablak (Ez mutatja a világot vagy a privátot is!)
        self.uzenetek_doboz = tk.Text(bal_frame, font=("Arial", 10), state=tk.DISABLED)
        self.uzenetek_doboz.pack(fill=tk.BOTH, expand=True)
        
        self.uzenet_beviteli = tk.Entry(bal_frame, font=("Arial", 12))
        self.uzenet_beviteli.pack(fill=tk.X, pady=5)
        self.uzenet_beviteli.bind("<Return>", lambda e: self.uzenet_kuldes())
        tk.Button(bal_frame, text="Send / Küldés", bg="lightblue", command=self.uzenet_kuldes).pack(anchor=tk.E)

        # Jobb oldal: "Online Chat" fő gomb, kereső és lista
        self.vilag_chat_gomb = tk.Button(jobb_frame, text=self.n("btn_world_chat"), bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.vissza_a_vilag_chatbe)
        self.vilag_chat_gomb.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(jobb_frame, text=self.n("online_users"), bg="lightgray", font=("Arial", 9, "bold")).pack(pady=2)
        
        self.kereso_var = tk.StringVar()
        self.kereso_var.trace_add("write", self.felhasznalok_szurese)
        self.kereso_mezo = tk.Entry(jobb_frame, textvariable=self.kereso_var, font=("Arial", 10))
        self.kereso_mezo.insert(0, self.n("search"))
        self.kereso_mezo.bind("<FocusIn>", lambda e: self.kereso_mezo.delete(0, tk.END) if self.kereso_mezo.get() == self.n("search") else None)
        self.kereso_mezo.pack(fill=tk.X, padx=5, pady=2)

        self.felhasznalo_lista = tk.Listbox(jobb_frame, font=("Arial", 10), bg="#f0f0f0")
        self.felhasznalo_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Szupergyors kattintás kezelő: egyszeri kattintásra azonnal szobát vált!
        self.felhasznalo_lista.bind("<<ListboxSelect>>", self.felhasznalora_kattintottak)

        threading.Thread(target=self.uzenetek_fogadasa, daemon=True).start()
        self.szoba_frissites()

    def uzenet_kuldes(self):
        u = self.uzenet_beviteli.get().strip()
        if u and self.kapcsolat:
            try: 
                if self.aktualis_szoba == "GLOBAL":
                    self.kapcsolat.sendall(f"{u}\n".encode('utf-8'))
                else:
                    # Privát küldési formátum a szervernek: PRIVAT|ki_kapja|üzenet
                    self.kapcsolat.sendall(f"PRIVAT|{self.aktualis_szoba}|{u}\n".encode('utf-8'))
                self.uzenet_beviteli.delete(0, tk.END)
            except: pass

    def felhasznalok_szurese(self, *args):
        szoveg = self.kereso_var.get().lower()
        self.felhasznalo_lista.delete(0, tk.END)
        if szoveg == self.n("search").lower(): return
        for nev in self.minden_online_felhasznalo:
            if szoveg in nev.lower(): self.felhasznalo_lista.insert(tk.END, nev)

    def felhasznalora_kattintottak(self, event):
        szekcio = self.felhasznalo_lista.curselection()
        if not szekcio: return
        valasztott_nev = self.felhasznalo_lista.get(szekcio)
        if valasztott_nev == self.felhasznalonev: return # Magunkkal nem beszélünk privátban
        
        self.aktualis_szoba = valasztott_nev
        self.szoba_frissites()

    def vissza_a_vilag_chatbe(self):
        self.aktualis_szoba = "GLOBAL"
        self.szoba_frissites()

    def szoba_frissites(self):
        # Frissíti a fejlécet és átváltja a szövegdoboz tartalmát az adott szobára
        self.uzenetek_doboz.config(state=tk.NORMAL)
        self.uzenetek_doboz.delete("1.0", tk.END)
        
        if self.aktualis_szoba == "GLOBAL":
            self.szoba_cimke.config(text=f"🌐 {self.n('global_title')}", fg="darkblue")
            self.uzenetek_doboz.insert(tk.END, self.global_chat_tortenet)
        else:
            self.szoba_cimke.config(text=f"🔒 {self.n('private_title')}{self.aktualis_szoba}", fg="darkorange")
            tortenet = self.privat_chat_tortenetek.get(self.aktualis_szoba, "")
            self.uzenetek_doboz.insert(tk.END, tortenet)
            
        self.uzenetek_doboz.config(state=tk.DISABLED)
        self.uzenetek_doboz.see(tk.END)

    def uzenetek_fogadasa(self):
        maradek = ""
        while True:
            try:
                adat = self.kapcsolat.recv(1024)
                if not adat: break
                maradek += adat.decode('utf-8')
                
                while "\n" in maradek:
                    sor, maradek = maradek.split("\n", 1)
                    if not sor: continue
                    
                    if sor.startswith("ONLINE_LISTA|"):
                        nevek = sor.split("|")[1].split(",")
                        self.minden_online_felhasznalo = [n for n in nevek if n]
                        self.root.after(10, self.lista_frissites)
                        
                    elif sor.startswith("GLOBAL|"):
                        uzi = sor.split("|")[1] + "\n"
                        self.global_chat_tortenet += uzi
                        if self.aktualis_szoba == "GLOBAL":
                            self.root.after(10, lambda u=uzi: self.uzenet_hozzaadas(u))
                            
                    elif sor.startswith("PRIVAT|"):
                        _, kitol, uzi = sor.split("|", 2)
                        # Megállapítjuk, hogy kivel folyik a beszélgetés története (küldő vagy fogadó)
                        partner = kitol if kitol != self.felhasznalonev else sor.split("|")[1]
                        
                        teljes_uzi = f"[{kitol}]: {uzi}\n"
                        if partner not in self.privat_chat_tortenetek:
                            self.privat_chat_tortenetek[partner] = ""
                        self.privat_chat_tortenetek[partner] += teljes_uzi
                        
                        if self.aktualis_szoba == partner:
                            self.root.after(10, lambda u=teljes_uzi: self.uzenet_hozzaadas(u))
            except: break

    def lista_frissites(self):
        if self.kereso_mezo.get() == self.n("search") or self.kereso_var.get() == "":
            self.felhasznalo_lista.delete(0, tk.END)
            for n in self.minden_online_felhasznalo: self.felhasznalo_lista.insert(tk.END, n)

    def uzenet_hozzaadas(self, uzi):
        self.uzenetek_doboz.config(state=tk.NORMAL)
        self.uzenetek_doboz.insert(tk.END, uzi)
        self.uzenetek_doboz.config(state=tk.DISABLED)
        self.uzenetek_doboz.see(tk.END)

    def tisztitas(self):
        for w in self.root.winfo_children(): w.destroy()

if __name__ == "__main__":
    root = tk.Tk(); app = ChatKliens(root); root.mainloop()