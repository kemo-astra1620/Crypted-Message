import base64
import json
import secrets
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP_NAME = "fsociety-message-crypted"
STORE = Path.home() / ".fsociety-message-crypted"
STORE.mkdir(exist_ok=True)
INBOX_FILE = STORE / "saved_packets.json"
LEGACY_INBOX_FILE = Path.home() / ".crypted_chat_desktop" / "saved_packets.json"

def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * ((4 - len(text) % 4) % 4))

def derive_key(password: str, salt: bytes, iterations: int = 600_000) -> bytes:
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)

def encrypt_message(message: str, password: str) -> str:
    # AES-GCM via cryptography. The packet includes salt and nonce, never the password.
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, message.encode("utf-8"), b"crypted-chat-v1")
    return "CC1." + ".".join((b64e(salt), b64e(nonce), b64e(ciphertext)))

def decrypt_message(packet: str, password: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    parts = packet.strip().split(".")
    if len(parts) != 4 or parts[0] != "CC1":
        raise ValueError("Paket biçimi tanınmadı. CC1. ile başlayan paketin tamamını yapıştır.")
    salt, nonce, ciphertext = b64d(parts[1]), b64d(parts[2]), b64d(parts[3])
    if len(salt) != 16 or len(nonce) != 12:
        raise ValueError("Paket geçersiz veya eksik.")
    key = derive_key(password, salt)
    try:
        plain = AESGCM(key).decrypt(nonce, ciphertext, b"crypted-chat-v1")
    except Exception as exc:
        raise ValueError("Şifre çözülemedi. Anahtar yanlış olabilir veya mesaj değiştirilmiş olabilir.") from exc
    return plain.decode("utf-8")

def load_packets():
    for source in (INBOX_FILE, LEGACY_INBOX_FILE):
        try:
            data = json.loads(source.read_text("utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []

def save_packets(items):
    INBOX_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("920x700")
        self.minsize(720, 580)
        self.configure(bg="#000000")
        self.packet = ""
        self._style()
        self._build()
        self.bind_all("<Control-a>", self.select_all, add="+")
        self.bind_all("<Control-A>", self.select_all, add="+")
        self.refresh_inbox()

    def select_all(self, event):
        widget = event.widget
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
            widget.mark_set("insert", "1.0")
            widget.see("insert")
            return "break"
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.selection_range(0, "end")
            widget.icursor("end")
            return "break"
        if isinstance(widget, tk.Listbox):
            widget.selection_set(0, "end")
            return "break"
        return None

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#000000")
        style.configure("Panel.TFrame", background="#000000")
        style.configure("TLabel", background="#000000", foreground="#f0f0f0", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#f4f2ff")
        style.configure("Sub.TLabel", foreground="#9ca5c2")
        style.configure("Panel.TLabel", background="#000000", foreground="#f0f0f0")
        style.configure("PanelSub.TLabel", background="#000000", foreground="#9ca5c2")
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10), background="#171717", foreground="#f0f0f0")
        style.map("TButton", background=[("active", "#292929")], foreground=[("active", "#ffffff")])
        style.configure("Accent.TButton", background="#7165ee", foreground="white")
        style.map("Accent.TButton", background=[("active", "#8a80ff")])
        style.configure("TNotebook", background="#000000", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), background="#111111", foreground="#aeb5d1")
        style.map("TNotebook.Tab", background=[("selected", "#29264c")], foreground=[("selected", "#ffffff")])

    def _build(self):
        outer = ttk.Frame(self, padding=22)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 18))
        logo = tk.Label(header, text="F", font=("Segoe UI", 19, "bold"), fg="white", bg="#262626", width=2, height=1)
        logo.pack(side="left", padx=(0, 12))
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text="fsociety-message-crypted", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Mesajlarını yerel olarak şifrele ve çöz", style="Sub.TLabel").pack(anchor="w", pady=(2, 0))
        self.status = ttk.Label(header, text="● YEREL ŞİFRELEME", foreground="#65e0aa")
        self.status.pack(side="right", anchor="n", pady=8)

        self.nb = ttk.Notebook(outer)
        self.nb.pack(fill="both", expand=True)
        self.encrypt_tab = ttk.Frame(self.nb, padding=18)
        self.decrypt_tab = ttk.Frame(self.nb, padding=18)
        self.inbox_tab = ttk.Frame(self.nb, padding=18)
        self.info_tab = ttk.Frame(self.nb, padding=18)
        self.nb.add(self.encrypt_tab, text="  Şifrele  ")
        self.nb.add(self.decrypt_tab, text="  Şifre çöz  ")
        self.nb.add(self.inbox_tab, text="  Kayıtlı paketler  ")
        self.nb.add(self.info_tab, text="  Güvenlik  ")
        self._build_encrypt()
        self._build_decrypt()
        self._build_inbox()
        self._build_info()
        ttk.Label(outer, text="Ctrl+A etkin metin alanındaki tüm içeriği seçer. Mesajlar internet üzerinden gönderilmez; şifreli paketi ayrı bir kanaldan paylaş.", style="Sub.TLabel").pack(anchor="w", pady=(12, 0))

    def label(self, parent, text, panel=False):
        return ttk.Label(parent, text=text, style="Panel.TLabel" if panel else "TLabel")

    def make_text(self, parent, height=6):
        box = tk.Text(parent, height=height, wrap="word", bg="#000000", fg="#e8e8e8",
                      insertbackground="#ffffff", selectbackground="#454545", relief="flat",
                      highlightthickness=1, highlightbackground="#2b2b2b", padx=11, pady=10,
                      font=("Consolas", 10))
        return box

    def _build_encrypt(self):
        tab = self.encrypt_tab
        ttk.Label(tab, text="Yeni şifreli mesaj", style="Title.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Mesajı yaz, bir parola belirle ve şifreli paketi arkadaşına gönder.", style="Sub.TLabel").pack(anchor="w", pady=(4, 15))
        ttk.Label(tab, text="Mesajın").pack(anchor="w", pady=(0, 6))
        self.plain_in = self.make_text(tab, 6)
        self.plain_in.pack(fill="x", pady=(0, 13))
        ttk.Label(tab, text="Paylaşılan parola (en az 8 karakter önerilir)").pack(anchor="w", pady=(0, 6))
        row = ttk.Frame(tab); row.pack(fill="x", pady=(0, 14))
        self.pass_in = ttk.Entry(row, show="•")
        self.pass_in.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Göster / gizle", command=lambda: self.toggle_password(self.pass_in)).pack(side="left", padx=(8, 0))
        actions = ttk.Frame(tab); actions.pack(fill="x", pady=(0, 12))
        ttk.Button(actions, text="⟡  Mesajı şifrele", style="Accent.TButton", command=self.do_encrypt).pack(side="left")
        ttk.Button(actions, text="Temizle", command=self.clear_encrypt).pack(side="left", padx=8)
        ttk.Label(tab, text="Şifreli paket (bunu kopyalayıp gönder; parolayı ayrı kanaldan paylaş)").pack(anchor="w", pady=(5, 6))
        self.packet_out = self.make_text(tab, 5)
        self.packet_out.pack(fill="both", expand=True)
        buttons = ttk.Frame(tab); buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Paketi kopyala", command=lambda: self.copy_text(self.packet_out)).pack(side="left")
        ttk.Button(buttons, text="Kayıtlı paketlere ekle", command=self.save_current_packet).pack(side="left", padx=8)
        self.enc_note = ttk.Label(tab, text="", style="Sub.TLabel")
        self.enc_note.pack(anchor="w", pady=(8, 0))

    def _build_decrypt(self):
        tab = self.decrypt_tab
        ttk.Label(tab, text="Şifreli mesajı çöz", style="Title.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Arkadaşının gönderdiği paketi ve sana ayrı ilettiği parolayı gir.", style="Sub.TLabel").pack(anchor="w", pady=(4, 15))
        ttk.Label(tab, text="Şifreli paket").pack(anchor="w", pady=(0, 6))
        self.packet_in = self.make_text(tab, 7); self.packet_in.pack(fill="x", pady=(0, 13))
        ttk.Label(tab, text="Parola").pack(anchor="w", pady=(0, 6))
        row = ttk.Frame(tab); row.pack(fill="x", pady=(0, 14))
        self.pass_out = ttk.Entry(row, show="•"); self.pass_out.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Göster / gizle", command=lambda: self.toggle_password(self.pass_out)).pack(side="left", padx=(8, 0))
        ttk.Button(tab, text="⌁  Şifreyi çöz", style="Accent.TButton", command=self.do_decrypt).pack(anchor="w", pady=(0, 14))
        ttk.Label(tab, text="Çözülen mesaj").pack(anchor="w", pady=(0, 6))
        self.plain_out = self.make_text(tab, 8); self.plain_out.pack(fill="both", expand=True)
        ttk.Button(tab, text="Mesajı kopyala", command=lambda: self.copy_text(self.plain_out)).pack(anchor="w", pady=(10, 0))

    def _build_inbox(self):
        tab = self.inbox_tab
        top = ttk.Frame(tab); top.pack(fill="x")
        ttk.Label(top, text="Kayıtlı şifreli paketler", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Yenile", command=self.refresh_inbox).pack(side="right")
        ttk.Label(tab, text="Paketler bu bilgisayardaki kullanıcı klasöründe saklanır.", style="Sub.TLabel").pack(anchor="w", pady=(5, 14))
        self.inbox_list = tk.Listbox(tab, bg="#000000", fg="#e3e6ff", selectbackground="#5148a8",
                                     relief="flat", highlightthickness=1, highlightbackground="#2b2b2b",
                                     font=("Segoe UI", 10), activestyle="none")
        self.inbox_list.pack(fill="both", expand=True)
        row = ttk.Frame(tab); row.pack(fill="x", pady=(12, 0))
        ttk.Button(row, text="Seçileni şifre çözmeye aktar", style="Accent.TButton", command=self.load_selected).pack(side="left")
        ttk.Button(row, text="Seçileni sil", command=self.delete_selected).pack(side="left", padx=8)
        ttk.Button(row, text="Dışarıdan paket aç", command=self.import_packet).pack(side="right")

    def _build_info(self):
        tab = self.info_tab
        ttk.Label(tab, text="Güvenlik ve kullanım", style="Title.TLabel").pack(anchor="w", pady=(0, 12))
        content = (
            "Nasıl kullanılır\n"
            "1. Şifrele sekmesinde mesajı ve ortak parolayı yaz.\n"
            "2. Şifreli paketi kopyalayıp arkadaşına gönder.\n"
            "3. Parolayı aynı mesajın içinde değil, farklı ve güvenli bir kanaldan paylaş.\n"
            "4. Arkadaşın Şifre çöz sekmesine paketi ve parolayı yapıştırır.\n\n"
            "Teknik ayrıntılar\n"
            "• AES-GCM 256-bit şifreleme (cryptography kitaplığı)\n"
            "• PBKDF2-HMAC-SHA256 ile 600.000 iterasyonda anahtar türetme\n"
            "• Her mesaj için rastgele salt ve nonce\n"
            "• Paket, parola içermez; yanlış parola veya değiştirilmiş pakette doğrulama başarısız olur.\n\n"
            "Önemli sınırlar\n"
            "• Bu program paketi internet üzerinden kendiliğinden göndermez; sen bir mesajlaşma uygulaması/e-posta üzerinden paylaşırsın.\n"
            "• Bu prototipte kimlik doğrulama ve otomatik anahtar değişimi yoktur. Parolayı gerçekten gönderen kişiyle güvenli biçimde doğrula.\n"
            "• Hassas/çok önemli yazışmalar için üretim ürünü gibi değerlendirme; bağımsız güvenlik incelemesi gerekir.\n"
            "• Parolayı unutursan mesaj kurtarılamaz."
        )
        box = self.make_text(tab, 20); box.pack(fill="both", expand=True)
        box.insert("1.0", content); box.configure(state="disabled")

    def toggle_password(self, entry):
        entry.configure(show="" if entry.cget("show") else "•")

    def do_encrypt(self):
        message = self.plain_in.get("1.0", "end-1c")
        password = self.pass_in.get()
        if not message.strip():
            messagebox.showwarning("Mesaj eksik", "Önce şifrelemek istediğin mesajı yaz.")
            return
        if len(password) < 8:
            messagebox.showwarning("Parola kısa", "En az 8 karakterli, tahmin edilmesi zor bir parola kullan.")
            return
        try:
            self.packet = encrypt_message(message, password)
            self.packet_out.delete("1.0", "end")
            self.packet_out.insert("1.0", self.packet)
            self.enc_note.configure(text="Şifreleme tamamlandı. Parola pakete dahil edilmedi.")
        except ImportError:
            messagebox.showerror("Eksik bileşen", "Şifreleme kitaplığı kurulu değil.\n\nKomut satırında şunu çalıştır:\npython -m pip install cryptography")
        except Exception as exc:
            messagebox.showerror("Hata", f"Şifreleme başarısız oldu: {exc}")

    def do_decrypt(self):
        packet = self.packet_in.get("1.0", "end-1c").strip()
        password = self.pass_out.get()
        if not packet or not password:
            messagebox.showwarning("Bilgi eksik", "Şifreli paketi ve parolayı gir.")
            return
        try:
            plain = decrypt_message(packet, password)
            self.plain_out.delete("1.0", "end")
            self.plain_out.insert("1.0", plain)
        except ImportError:
            messagebox.showerror("Eksik bileşen", "Şifreleme kitaplığı kurulu değil.\n\nKomut satırında şunu çalıştır:\npython -m pip install cryptography")
        except Exception as exc:
            messagebox.showerror("Şifre çözülemedi", str(exc))

    def clear_encrypt(self):
        self.plain_in.delete("1.0", "end")
        self.pass_in.delete(0, "end")
        self.packet_out.delete("1.0", "end")
        self.packet = ""
        self.enc_note.configure(text="")

    def copy_text(self, widget):
        text = widget.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showinfo("Boş", "Kopyalanacak metin yok.")
            return
        self.clipboard_clear(); self.clipboard_append(text); self.update()
        messagebox.showinfo("Kopyalandı", "Metin panoya kopyalandı.")

    def save_current_packet(self):
        packet = self.packet_out.get("1.0", "end-1c").strip()
        if not packet:
            messagebox.showinfo("Paket yok", "Önce bir mesajı şifrele.")
            return
        items = load_packets()
        items.insert(0, {"label": f"Paket · {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}", "packet": packet})
        save_packets(items[:200])
        self.refresh_inbox()
        messagebox.showinfo("Kaydedildi", "Şifreli paket bu bilgisayara kaydedildi.")

    def refresh_inbox(self):
        self.items = load_packets()
        if not hasattr(self, "inbox_list"):
            return
        self.inbox_list.delete(0, "end")
        for item in self.items:
            self.inbox_list.insert("end", item.get("label", "Şifreli paket"))

    def load_selected(self):
        sel = self.inbox_list.curselection()
        if not sel:
            messagebox.showinfo("Seçim yok", "Önce listeden bir paket seç.")
            return
        packet = self.items[sel[0]].get("packet", "")
        self.packet_in.delete("1.0", "end"); self.packet_in.insert("1.0", packet)
        self.nb.select(self.decrypt_tab)

    def delete_selected(self):
        sel = self.inbox_list.curselection()
        if not sel:
            messagebox.showinfo("Seçim yok", "Önce listeden bir paket seç.")
            return
        if messagebox.askyesno("Paketi sil", "Seçili şifreli paket silinsin mi?"):
            del self.items[sel[0]]
            save_packets(self.items)
            self.refresh_inbox()

    def import_packet(self):
        path = filedialog.askopenfilename(title="Şifreli paket dosyası seç", filetypes=[("Metin dosyaları", "*.txt"), ("Tüm dosyalar", "*.*")])
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8").strip()
            self.packet_in.delete("1.0", "end"); self.packet_in.insert("1.0", text)
            self.nb.select(self.decrypt_tab)
        except Exception as exc:
            messagebox.showerror("Dosya açılamadı", str(exc))

if __name__ == "__main__":
    App().mainloop()
