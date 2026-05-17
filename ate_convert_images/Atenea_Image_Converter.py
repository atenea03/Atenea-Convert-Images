import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

# ==========================================================
# PALETA
# ==========================================================
BG_BASE      = "#1a1a1a"
BG_PANEL     = "#232323"
BG_ELEVATED  = "#2c2c2c"
BG_ACTIVE    = "#383838"
BORDER       = "#3a3a3a"
TEXT_PRIMARY = "#f0f0f0"
TEXT_MUTED   = "#888888"
TEXT_GOLD    = "#F5A800"
BTN_HOVER    = "#3a3a3a"
WHITE        = "#ffffff"

# ==========================================================
# FORMATOS
# ==========================================================
FORMATOS_ENTRADA = ["All formats", "PNG", "JPG", "WEBP", "BMP", "TIFF"]
FORMATOS_SALIDA  = ["WEBP", "PNG", "JPG", "BMP", "TIFF"]

EXT_MAP = {
    "PNG":         [".png"],
    "JPG":         [".jpg", ".jpeg"],
    "WEBP":        [".webp"],
    "BMP":         [".bmp"],
    "TIFF":        [".tiff", ".tif"],
    "All formats": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"],
}
PIL_FORMAT = {
    "PNG": "PNG", "JPG": "JPEG", "WEBP": "WEBP", "BMP": "BMP", "TIFF": "TIFF",
}

# ==========================================================
# CONVERSIÓN
# ==========================================================
def convertir_imagenes(entradas, carpeta_salida, fmt_salida, calidad,
                       cb_prog, cb_log, cb_fin):
    os.makedirs(carpeta_salida, exist_ok=True)
    total = len(entradas)
    ok = errores = 0

    for i, ruta in enumerate(entradas):
        nombre  = os.path.basename(ruta)
        base    = os.path.splitext(nombre)[0]
        ext_out = EXT_MAP[fmt_salida][0]
        dest    = os.path.join(carpeta_salida, base + ext_out)
        try:
            img = Image.open(ruta)
            if fmt_salida in ("JPG", "BMP"):
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                else:
                    img = img.convert("RGB")
            elif fmt_salida == "PNG":
                img = img.convert("RGBA")
            elif fmt_salida == "TIFF":
                if img.mode not in ("RGB", "RGBA", "L"):
                    img = img.convert("RGB")

            if fmt_salida in ("WEBP", "JPG"):
                img.save(dest, PIL_FORMAT[fmt_salida], quality=calidad)
            else:
                img.save(dest, PIL_FORMAT[fmt_salida])

            ok += 1
            cb_log(f"  ✓  {nombre}  →  {base + ext_out}\n")
        except Exception as e:
            errores += 1
            cb_log(f"  ✗  {nombre}: {e}\n")

        cb_prog(i + 1, total)

    cb_fin(ok, errores)


# ==========================================================
# APP
# ==========================================================
class AteneaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Atenea Image Converter")
        self.configure(fg_color=BG_BASE)

        # ── Tamaño relativo a la pantalla ───────────────────
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        win_w = max(480, min(int(sw * 0.38), 820))
        win_h = max(580, min(int(sh * 0.80), 980))
        cx = (sw - win_w) // 2
        cy = (sh - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{cx}+{cy}")
        self.minsize(480, 580)
        self.resizable(True, True)

        # Escala tipográfica basada en resolución
        # 1080p → escala 1.0 | 1440p → 1.15 | 4K → 1.45
        self._sc = max(0.85, min(sw / 1920, 1.6))

        self.selected_files = []
        self._total = 0
        self._active_fmt = "WEBP"

        self._set_icon()
        self._build_ui()

    # ── escala ───────────────────────────────────────────────
    def _fs(self, size):
        """Devuelve tamaño de fuente escalado."""
        return max(8, int(size * self._sc))

    def _pad(self, base):
        """Escala un valor de padding."""
        return max(4, int(base * self._sc))

    def _h(self, base):
        """Escala altura de widget."""
        return max(28, int(base * self._sc))

    # ── ICONO ────────────────────────────────────────────────
    def _set_icon(self):
        for path, method in [
            (self._res("logo.ico"), "bitmap"),
            (self._res("logo.png"), "photo"),
        ]:
            if not os.path.exists(path):
                continue
            try:
                if method == "bitmap":
                    self.iconbitmap(path)
                else:
                    self.iconphoto(True, ImageTk.PhotoImage(Image.open(path)))
            except Exception:
                pass

    # ── UI ───────────────────────────────────────────────────
    def _build_ui(self):
        p = self._pad   # atajo padding
        h = self._h     # atajo altura
        fs = self._fs   # atajo fuente

        scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_BASE,
            scrollbar_button_color=BG_ELEVATED,
            scrollbar_button_hover_color=BTN_HOVER,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        # ── HEADER ──────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=p(24), pady=(p(18), p(4)))

        logo_path = self._res("logo.png")
        logo_size = h(48)
        if os.path.exists(logo_path):
            try:
                li = ctk.CTkImage(Image.open(logo_path),
                                  size=(logo_size, logo_size))
                ctk.CTkLabel(header, image=li, text="").pack(
                    side="left", padx=(0, p(12)))
            except Exception:
                pass

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="Atenea Image Converter",
                     font=("Segoe UI Semibold", fs(20)),
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Atenea Store Tools  ·  V2026",
                     font=("Segoe UI", fs(11)),
                     text_color=TEXT_GOLD).pack(anchor="w")

        # ── INPUT ────────────────────────────────────────────
        self._divider(scroll)
        self._label(scroll, "INPUT")

        self.entry_in = ctk.CTkEntry(
            scroll, height=h(36), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            placeholder_text="Select a folder or files…",
            placeholder_text_color=TEXT_MUTED,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(12)),
        )
        self.entry_in.pack(fill="x", padx=p(24), pady=(0, p(6)))

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=p(24))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        self._grid_btn(btn_row, "Folder", self.select_folder, 0)
        self._grid_btn(btn_row, "Files",  self.select_files,  1)

        # ── FILTER BY FORMAT ────────────────────────────────
        self._divider(scroll)
        self._label(scroll, "FILTER BY FORMAT")

        self.fmt_entrada = ctk.CTkOptionMenu(
            scroll, values=FORMATOS_ENTRADA,
            height=h(36), corner_radius=8,
            fg_color=BG_PANEL, button_color=BG_ELEVATED,
            button_hover_color=BTN_HOVER, text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_PANEL, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BG_ELEVATED,
            font=("Segoe UI", fs(12)),
            dropdown_font=("Segoe UI", fs(12)),
        )
        self.fmt_entrada.set("All formats")
        self.fmt_entrada.pack(fill="x", padx=p(24))

        # ── OUTPUT FOLDER ────────────────────────────────────
        self._divider(scroll)
        self._label(scroll, "OUTPUT FOLDER")

        out_row = ctk.CTkFrame(scroll, fg_color="transparent")
        out_row.pack(fill="x", padx=p(24))
        out_row.columnconfigure(0, weight=1)

        self.entry_out = ctk.CTkEntry(
            out_row, height=h(36), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(12)),
        )
        self.entry_out.insert(0, "converted")
        self.entry_out.grid(row=0, column=0, sticky="ew", padx=(0, p(8)))

        ctk.CTkButton(
            out_row, text="…",
            width=h(36), height=h(36), corner_radius=8,
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(14)),
            border_width=1, border_color=BORDER,
            command=self.select_out,
        ).grid(row=0, column=1)

        # ── TARGET FORMAT ────────────────────────────────────
        self._divider(scroll)
        self._label(scroll, "TARGET FORMAT")

        self.fmt_buttons = {}
        fmt_row = ctk.CTkFrame(scroll, fg_color="transparent")
        fmt_row.pack(fill="x", padx=p(24))
        for i, fmt in enumerate(FORMATOS_SALIDA):
            fmt_row.columnconfigure(i, weight=1)
        for i, fmt in enumerate(FORMATOS_SALIDA):
            active = (fmt == "WEBP")
            btn = ctk.CTkButton(
                fmt_row, text=fmt,
                height=h(34), corner_radius=8,
                fg_color=BG_ACTIVE if active else BG_ELEVATED,
                hover_color=BTN_HOVER,
                text_color=WHITE if active else TEXT_PRIMARY,
                border_width=1,
                border_color="#555555" if active else BORDER,
                font=("Segoe UI", fs(12)),
                command=lambda f=fmt: self._select_fmt(f),
            )
            pad_r = p(6) if i < len(FORMATOS_SALIDA) - 1 else 0
            btn.grid(row=0, column=i, sticky="ew", padx=(0, pad_r))
            self.fmt_buttons[fmt] = btn

        # ── QUALITY ──────────────────────────────────────────
        self._divider(scroll)

        self.q_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.q_container.pack(fill="x", padx=p(24))

        q_head = ctk.CTkFrame(self.q_container, fg_color="transparent")
        q_head.pack(fill="x")
        ctk.CTkLabel(q_head, text="QUALITY",
                     font=("Segoe UI", fs(9), "bold"),
                     text_color=TEXT_MUTED).pack(side="left")
        self.quality_val = ctk.CTkLabel(q_head, text="85",
                                         font=("Segoe UI", fs(9), "bold"),
                                         text_color=TEXT_PRIMARY)
        self.quality_val.pack(side="right")

        self.quality_slider = ctk.CTkSlider(
            self.q_container, from_=1, to=100, number_of_steps=99,
            fg_color=BG_ELEVATED, progress_color=BG_ACTIVE,
            button_color=TEXT_PRIMARY, button_hover_color=WHITE,
            command=self._on_quality,
        )
        self.quality_slider.set(85)
        self.quality_slider.pack(fill="x", pady=(p(4), 0))

        # ── STATUS BAR ───────────────────────────────────────
        self._divider(scroll)

        status_row = ctk.CTkFrame(scroll, fg_color="transparent")
        status_row.pack(fill="x", padx=p(24), pady=(p(2), p(4)))

        ctk.CTkLabel(status_row, text="·",
                     font=("Segoe UI", fs(14)),
                     text_color=TEXT_MUTED).pack(side="left")
        self.status_text = ctk.CTkLabel(status_row, text="Ready",
                                         font=("Segoe UI", fs(10)),
                                         text_color=TEXT_MUTED)
        self.status_text.pack(side="left", padx=(p(4), 0))
        self.counter_label = ctk.CTkLabel(status_row, text="0 / 0",
                                           font=("Segoe UI", fs(10)),
                                           text_color=TEXT_MUTED)
        self.counter_label.pack(side="right")

        # ── LOG ──────────────────────────────────────────────
        self.log_box = ctk.CTkTextbox(
            scroll,
            height=h(120),
            corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            text_color=TEXT_MUTED,
            font=("Consolas", fs(11)),
            scrollbar_button_color=BG_ELEVATED,
        )
        self.log_box.pack(fill="x", padx=p(24), pady=(0, p(6)))
        self.log_box.configure(state="normal")
        self.log_box.insert("end", "  —  Waiting for input…\n")
        self.log_box.configure(state="disabled")

        # ── PROGRESS ─────────────────────────────────────────
        self.progress_bar = ctk.CTkProgressBar(
            scroll, height=3, corner_radius=2,
            fg_color=BG_ELEVATED, progress_color=TEXT_PRIMARY,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=p(24), pady=(0, p(8)))

        # ── CONVERT BUTTON ───────────────────────────────────
        self.btn_convert = ctk.CTkButton(
            scroll, text="Convert images",
            font=("Segoe UI Semibold", fs(14)),
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            height=h(48), corner_radius=8,
            command=self.start_convert,
        )
        self.btn_convert.pack(fill="x", padx=p(24), pady=(0, p(4)))

        # ── FOOTER ───────────────────────────────────────────
        ctk.CTkLabel(scroll, text="© 2026  Atenea Store Tools",
                     font=("Segoe UI", fs(9)),
                     text_color=TEXT_MUTED).pack(pady=(p(2), p(12)))

    # ── HELPERS ──────────────────────────────────────────────
    def _divider(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=self._pad(24), pady=(self._pad(6), self._pad(6)))

    def _label(self, parent, text):
        ctk.CTkLabel(parent, text=text,
                     font=("Segoe UI", self._fs(9), "bold"),
                     text_color=TEXT_MUTED).pack(
            anchor="w", padx=self._pad(24), pady=(0, self._pad(4)))

    def _grid_btn(self, parent, text, command, col):
        pad_r = self._pad(6) if col == 0 else 0
        ctk.CTkButton(
            parent, text=text,
            height=self._h(36), corner_radius=8,
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            font=("Segoe UI", self._fs(12)),
            command=command,
        ).grid(row=0, column=col, sticky="ew", padx=(0, pad_r))

    # ── FORMAT BUTTONS ───────────────────────────────────────
    def _select_fmt(self, fmt):
        for f, btn in self.fmt_buttons.items():
            if f == fmt:
                btn.configure(fg_color=BG_ACTIVE, text_color=WHITE,
                               border_color="#555555")
            else:
                btn.configure(fg_color=BG_ELEVATED, text_color=TEXT_PRIMARY,
                               border_color=BORDER)
        self._active_fmt = fmt

        if fmt in ("WEBP", "JPG"):
            self.q_container.pack(fill="x", padx=self._pad(24))
        else:
            self.q_container.pack_forget()

    def _on_quality(self, val):
        self.quality_val.configure(text=str(int(val)))

    # ── FILE SELECTION ───────────────────────────────────────
    def select_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.selected_files = []
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, f)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),
                       ("All files", "*.*")],
        )
        if files:
            self.selected_files = list(files)
            n = len(files)
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, f"{n} file{'s' if n != 1 else ''} selected")

    def select_out(self):
        f = filedialog.askdirectory()
        if f:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, f)

    # ── CONVERSIÓN ───────────────────────────────────────────
    def _get_entradas(self):
        exts = EXT_MAP[self.fmt_entrada.get()]
        if self.selected_files:
            return [f for f in self.selected_files
                    if os.path.splitext(f)[1].lower() in exts]
        carpeta = self.entry_in.get().strip()
        if not carpeta or not os.path.isdir(carpeta):
            return []
        return [os.path.join(carpeta, f) for f in os.listdir(carpeta)
                if os.path.splitext(f)[1].lower() in exts]

    def start_convert(self):
        out     = self.entry_out.get().strip()
        fmt     = self._active_fmt
        calidad = int(self.quality_slider.get())
        files   = self._get_entradas()

        if not files:
            messagebox.showerror("No images found",
                "No images found with the selected format.")
            return
        if not out:
            messagebox.showerror("Missing output",
                "Please select an output folder.")
            return

        self._total = len(files)
        self.progress_bar.set(0)
        self.counter_label.configure(text=f"0 / {self._total}")
        self._log_clear()
        self.status_text.configure(text="Converting…", text_color=TEXT_PRIMARY)
        self.btn_convert.configure(state="disabled", text="Converting…")

        threading.Thread(
            target=convertir_imagenes,
            args=(files, out, fmt, calidad,
                  self._cb_prog, self._cb_log, self._cb_fin),
            daemon=True,
        ).start()

    # ── CALLBACKS ────────────────────────────────────────────
    def _cb_prog(self, done, total):
        self.after(0, lambda: self.progress_bar.set(done / total))
        self.after(0, lambda: self.counter_label.configure(
            text=f"{done} / {total}"))

    def _cb_log(self, texto):
        def _w():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", texto)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _w)

    def _cb_fin(self, ok, errores):
        def _d():
            self.btn_convert.configure(state="normal", text="Convert images")
            self.status_text.configure(text="Done", text_color=TEXT_GOLD)
            msg = f"Converted:  {ok} image{'s' if ok != 1 else ''}"
            if errores:
                msg += f"\nErrors:  {errores}"
            messagebox.showinfo("Done", msg)
        self.after(0, _d)

    def _log_clear(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _res(self, path):
        try:
            base = sys._MEIPASS
        except Exception:
            base = os.path.abspath(".")
        return os.path.join(base, path)


if __name__ == "__main__":
    app = AteneaApp()
    app.mainloop()
