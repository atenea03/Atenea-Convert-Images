import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk


# ==========================================================
# FORMATOS SOPORTADOS
# ==========================================================
FORMATOS_ENTRADA = ["Todos", "PNG", "JPG", "WEBP", "BMP", "TIFF"]
FORMATOS_SALIDA  = ["WEBP", "PNG", "JPG", "BMP", "TIFF"]

EXT_MAP = {
    "PNG":  [".png"],
    "JPG":  [".jpg", ".jpeg"],
    "WEBP": [".webp"],
    "BMP":  [".bmp"],
    "TIFF": [".tiff", ".tif"],
    "Todos": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"],
}

PIL_FORMAT = {
    "PNG":  "PNG",
    "JPG":  "JPEG",
    "WEBP": "WEBP",
    "BMP":  "BMP",
    "TIFF": "TIFF",
}


# ==========================================================
# FUNCIÓN DE CONVERSIÓN
# ==========================================================
def convertir_imagenes(entradas, carpeta_salida, fmt_salida, calidad, callback_progreso, callback_log, callback_fin):
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    total = len(entradas)
    ok = 0
    errores = 0

    for i, ruta_entrada in enumerate(entradas):
        nombre_archivo = os.path.basename(ruta_entrada)
        nombre_base = os.path.splitext(nombre_archivo)[0]
        ext_salida = EXT_MAP[fmt_salida][0]
        ruta_salida = os.path.join(carpeta_salida, nombre_base + ext_salida)

        try:
            img = Image.open(ruta_entrada)

            # Gestión de transparencia: JPG y BMP no soportan alpha
            if fmt_salida in ("JPG", "BMP"):
                if img.mode in ("RGBA", "LA", "P"):
                    fondo = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    if img.mode in ("RGBA", "LA"):
                        fondo.paste(img, mask=img.split()[-1])
                    img = fondo
                else:
                    img = img.convert("RGB")
            elif fmt_salida == "PNG":
                img = img.convert("RGBA")
            elif fmt_salida == "TIFF":
                if img.mode not in ("RGB", "RGBA", "L"):
                    img = img.convert("RGB")

            # Guardar
            if fmt_salida in ("WEBP", "JPG"):
                img.save(ruta_salida, PIL_FORMAT[fmt_salida], quality=calidad)
            else:
                img.save(ruta_salida, PIL_FORMAT[fmt_salida])

            ok += 1
            callback_log(f"✅  {nombre_archivo}  →  {nombre_base + ext_salida}\n")

        except Exception as e:
            errores += 1
            callback_log(f"⚠️  Error con {nombre_archivo}: {e}\n")

        callback_progreso((i + 1) / total)

    callback_fin(ok, errores)


# ==========================================================
# INTERFAZ
# ==========================================================
class AteneaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atenea Image Converter")
        self.geometry("620x700")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.selected_files = []

        self._set_icon()
        self._build_ui()

    # ----------------------------------------------------------
    def _set_icon(self):
        ico_path = self.resource("logo.ico")
        png_path = self.resource("logo.png")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        if os.path.exists(png_path):
            try:
                img = Image.open(png_path)
                logo_tk = ImageTk.PhotoImage(img)
                self.iconphoto(True, logo_tk)
            except Exception:
                pass

    # ----------------------------------------------------------
    def _build_ui(self):
        # --- Logo + Título ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(pady=(20, 5))

        logo_path = self.resource("logo.png")
        if os.path.exists(logo_path):
            try:
                logo_img = ctk.CTkImage(Image.open(logo_path), size=(52, 52))
                ctk.CTkLabel(top_frame, image=logo_img, text="").pack(side="left", padx=(0, 12))
            except Exception:
                pass

        ctk.CTkLabel(
            top_frame,
            text="Atenea Image Converter",
            font=("Segoe UI", 22, "bold"),
            text_color="#F5A800",
        ).pack(side="left")

        # --- INPUT ---
        ctk.CTkLabel(self, text="📂  Input — folder or images:", font=("Segoe UI", 13)).pack(pady=(18, 2))

        self.entry_in = ctk.CTkEntry(self, width=420, placeholder_text="Select a folder or files…")
        self.entry_in.pack()

        btn_row1 = ctk.CTkFrame(self, fg_color="transparent")
        btn_row1.pack(pady=6)
        ctk.CTkButton(btn_row1, text="📁  Select folder", width=190, command=self.select_folder).pack(side="left", padx=6)
        ctk.CTkButton(btn_row1, text="🖼  Select files", width=190, command=self.select_files).pack(side="left", padx=6)

        # --- OUTPUT ---
        ctk.CTkLabel(self, text="📁  Output folder:", font=("Segoe UI", 13)).pack(pady=(14, 2))

        self.entry_out = ctk.CTkEntry(self, width=420, placeholder_text="Select output folder…")
        self.entry_out.insert(0, "converted")
        self.entry_out.pack()

        ctk.CTkButton(self, text="Select folder", width=190, command=self.select_out).pack(pady=6)

        # --- FORMATOS ---
        fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        fmt_frame.pack(pady=(14, 4))

        ctk.CTkLabel(fmt_frame, text="From:", font=("Segoe UI", 13)).grid(row=0, column=0, padx=(0, 8))
        self.fmt_entrada = ctk.CTkOptionMenu(fmt_frame, values=FORMATOS_ENTRADA, width=130)
        self.fmt_entrada.set("Todos")
        self.fmt_entrada.grid(row=0, column=1, padx=(0, 24))

        ctk.CTkLabel(fmt_frame, text="To:", font=("Segoe UI", 13)).grid(row=0, column=2, padx=(0, 8))
        self.fmt_salida = ctk.CTkOptionMenu(
            fmt_frame, values=FORMATOS_SALIDA, width=130,
            command=self._on_format_change
        )
        self.fmt_salida.set("WEBP")
        self.fmt_salida.grid(row=0, column=3)

        # --- CALIDAD ---
        self.quality_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.quality_frame.pack(pady=(10, 0))

        self.quality_label = ctk.CTkLabel(
            self.quality_frame, text="Quality: 85", font=("Segoe UI", 13)
        )
        self.quality_label.pack(side="left", padx=(0, 12))

        self.quality_slider = ctk.CTkSlider(
            self.quality_frame, from_=1, to=100, number_of_steps=99,
            width=220, command=self._on_quality_change
        )
        self.quality_slider.set(85)
        self.quality_slider.pack(side="left")

        # --- CONVERT BUTTON ---
        self.btn_convert = ctk.CTkButton(
            self,
            text="Convert",
            font=("Segoe UI", 16, "bold"),
            fg_color="#F5A800",
            hover_color="#C98A00",
            text_color="#1a1a1a",
            height=44,
            width=210,
            corner_radius=10,
            command=self.start_convert,
        )
        self.btn_convert.pack(pady=20)

        # --- PROGRESS BAR ---
        self.progress_bar = ctk.CTkProgressBar(self, width=460, height=14, corner_radius=7)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 6))

        self.progress_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color="#aaaaaa")
        self.progress_label.pack()

        # --- LOG ---
        self.log_box = ctk.CTkTextbox(self, width=560, height=130, font=("Consolas", 11))
        self.log_box.pack(pady=(10, 0))
        self.log_box.configure(state="disabled")

        # --- FOOTER ---
        ctk.CTkLabel(
            self,
            text="© 2026 Atenea Store Tools",
            text_color="#F5A800",
            font=("Segoe UI", 10),
        ).pack(side="bottom", pady=10)

    # ----------------------------------------------------------
    def _on_quality_change(self, val):
        self.quality_label.configure(text=f"Quality: {int(val)}")

    def _on_format_change(self, fmt):
        # Ocultar slider si el formato no usa calidad
        if fmt in ("WEBP", "JPG"):
            self.quality_frame.pack(pady=(10, 0))
        else:
            self.quality_frame.pack_forget()

    # ----------------------------------------------------------
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_files = []
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, folder)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"), ("All files", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, f"{len(files)} files selected")

    def select_out(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, folder)

    # ----------------------------------------------------------
    def _get_entradas(self):
        fmt_in = self.fmt_entrada.get()
        extensiones = EXT_MAP[fmt_in]

        if self.selected_files:
            return [f for f in self.selected_files if os.path.splitext(f)[1].lower() in extensiones]

        carpeta = self.entry_in.get().strip()
        if not carpeta or not os.path.isdir(carpeta):
            return []
        return [
            os.path.join(carpeta, f)
            for f in os.listdir(carpeta)
            if os.path.splitext(f)[1].lower() in extensiones
        ]

    # ----------------------------------------------------------
    def start_convert(self):
        carpeta_salida = self.entry_out.get().strip()
        fmt_salida = self.fmt_salida.get()
        calidad = int(self.quality_slider.get())

        entradas = self._get_entradas()

        if not entradas:
            messagebox.showerror("Error", "No se encontraron imágenes con el formato seleccionado.")
            return
        if not carpeta_salida:
            messagebox.showerror("Error", "Debes seleccionar una carpeta de salida.")
            return

        # Reset UI
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"0 / {len(entradas)}")
        self._log_clear()
        self.btn_convert.configure(state="disabled", text="Converting…")

        threading.Thread(
            target=convertir_imagenes,
            args=(entradas, carpeta_salida, fmt_salida, calidad,
                  self._cb_progreso, self._cb_log, self._cb_fin),
            daemon=True
        ).start()

    # ----------------------------------------------------------
    # Callbacks thread-safe usando after()
    def _cb_progreso(self, valor):
        self.after(0, lambda: self.progress_bar.set(valor))
        total = len(self._get_entradas()) or 1
        done = int(valor * total)
        self.after(0, lambda: self.progress_label.configure(text=f"{done} / {total}"))

    def _cb_log(self, texto):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", texto)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _write)

    def _cb_fin(self, ok, errores):
        def _done():
            self.btn_convert.configure(state="normal", text="Convert")
            msg = f"✅  Completed:  {ok} converted"
            if errores:
                msg += f"   ⚠️  {errores} errors"
            messagebox.showinfo("Done", msg)
        self.after(0, _done)

    def _log_clear(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # ----------------------------------------------------------
    def resource(self, path):
        try:
            base = sys._MEIPASS
        except Exception:
            base = os.path.abspath(".")
        return os.path.join(base, path)


# ==========================================================
# EJECUCIÓN
# ==========================================================
if __name__ == "__main__":
    app = AteneaApp()
    app.mainloop()