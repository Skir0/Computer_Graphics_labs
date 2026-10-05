import tkinter as tk
from tkinter import ttk, colorchooser
import colorsys


class ColorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа №1: Цветовые модели")
        self.geometry("860x650")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self._configure_styles()
        self._is_updating = False

        self.r = 128
        self.g = 64
        self.b = 192

        self._create_widgets()
        self._update_all_from_rgb()

    def _configure_styles(self):
        self.style.configure("TLabelFrame", padding=10, relief="solid")
        self.style.configure("TLabelFrame.Label", font=("Segoe UI", 10, "bold"), foreground="#333333")
        self.style.configure("Badge.TLabel", font=("Consolas", 8), foreground="#666666")

    @staticmethod
    def rgb_to_cmyk(r, g, b):
        r_n, g_n, b_n = r / 255.0, g / 255.0, b / 255.0
        k = 1.0 - max(r_n, g_n, b_n)
        if k == 1.0:
            return 0, 0, 0, 100
        c = (1.0 - r_n - k) / (1.0 - k) * 100.0
        m = (1.0 - g_n - k) / (1.0 - k) * 100.0
        y = (1.0 - b_n - k) / (1.0 - k) * 100.0
        return int(round(c)), int(round(m)), int(round(y)), int(round(k * 100.0))

    @staticmethod
    def cmyk_to_rgb(c, m, y, k):
        c_n, m_n, y_n, k_n = c / 100.0, m / 100.0, y / 100.0, k / 100.0
        r = int(round(255.0 * (1.0 - c_n) * (1.0 - k_n)))
        g = int(round(255.0 * (1.0 - m_n) * (1.0 - k_n)))
        b = int(round(255.0 * (1.0 - y_n) * (1.0 - k_n)))
        return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))

    @staticmethod
    def rgb_to_hsv(r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        return int(round(h * 360.0)), int(round(s * 100.0)), int(round(v * 100.0))

    @staticmethod
    def hsv_to_rgb(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
        return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))

    def _create_widgets(self):
        grid_frame = ttk.Frame(self, padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        grid_frame.columnconfigure(0, weight=1, uniform="col")
        grid_frame.columnconfigure(1, weight=1, uniform="col")
        grid_frame.rowconfigure(0, weight=1, uniform="row")
        grid_frame.rowconfigure(1, weight=1, uniform="row")

        top_left_frame = ttk.LabelFrame(grid_frame, text="Предпросмотр и выбор", padding=10)
        top_left_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.color_box = tk.Canvas(top_left_frame, height=65, relief="ridge", bd=2)
        self.color_box.pack(fill=tk.X, pady=(0, 10))

        self.canvas_text = self.color_box.create_text(0, 0, text="#8040C0", font=("Consolas", 14, "bold"), anchor="center")
        self.color_box.bind("<Configure>", self._center_canvas_text)

        ctrl_frame = ttk.Frame(top_left_frame)
        ctrl_frame.pack(fill=tk.X)

        btn_palette = ttk.Button(ctrl_frame, text="Системная палитра", command=self._pick_color)
        btn_palette.pack(fill=tk.X, pady=2)

        hex_row = ttk.Frame(ctrl_frame)
        hex_row.pack(fill=tk.X, pady=2)

        self.hex_label = ttk.Label(hex_row, text="HEX: #8040C0", font=("Consolas", 11, "bold"))
        self.hex_label.pack(side=tk.LEFT, padx=(0, 5))

        btn_copy = ttk.Button(hex_row, text="📋", width=3, command=self._copy_hex)
        btn_copy.pack(side=tk.LEFT)

        self.toast_label = ttk.Label(ctrl_frame, text="", font=("Segoe UI", 8), foreground="green")
        self.toast_label.pack(anchor=tk.W)

        self.controls = {}

        self.controls['RGB'] = self._create_card(
            grid_frame, "Модель RGB", "RGB", 0, 1,
            [("R", 0, 255), ("G", 0, 255), ("B", 0, 255)]
        )

        self.controls['CMYK'] = self._create_card(
            grid_frame, "Модель CMYK", "CMYK", 1, 0,
            [("C (%)", 0, 100), ("M (%)", 0, 100), ("Y (%)", 0, 100), ("K (%)", 0, 100)]
        )

        self.controls['HSV'] = self._create_card(
            grid_frame, "Модель HSV", "HSV", 1, 1,
            [("H (°)", 0, 360), ("S (%)", 0, 100), ("V (%)", 0, 100)]
        )

    def _center_canvas_text(self, event):
        x = event.width / 2
        y = event.height / 2
        self.color_box.coords(self.canvas_text, x, y)

    def _create_card(self, parent, title, model_name, row, col, channels):
        card = ttk.LabelFrame(parent, text=title, padding=10)
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

        block_data = {}
        for idx, (name, min_v, max_v) in enumerate(channels):
            lbl = ttk.Label(card, text=f"{name}:", font=("Segoe UI", 9, "bold"), width=7)
            lbl.grid(row=idx, column=0, sticky=tk.W, padx=(2, 0), pady=6)

            slider = ttk.Scale(
                card, from_=min_v, to=max_v, orient=tk.HORIZONTAL,
                command=lambda val, m=model_name, ch=name: self._on_slider_change(m, ch)
            )
            slider.grid(row=idx, column=1, sticky="ew", padx=5, pady=6)

            spinbox = ttk.Spinbox(
                card, from_=min_v, to=max_v, increment=1, width=5,
                command=lambda m=model_name, ch=name: self._on_spinbox_change(m, ch)
            )
            spinbox.grid(row=idx, column=2, padx=(0, 2), pady=6)

            spinbox.bind("<Return>", lambda ev, m=model_name, ch=name: self._on_spinbox_change(m, ch))
            spinbox.bind("<FocusOut>", lambda ev, m=model_name, ch=name: self._on_spinbox_change(m, ch))

            badge = ttk.Label(card, text=f"[{min_v}..{max_v}]", style="Badge.TLabel")
            badge.grid(row=idx, column=3, padx=(2, 0))

            block_data[name] = {
                'slider': slider,
                'spinbox': spinbox,
                'bounds': (min_v, max_v)
            }

        card.columnconfigure(1, weight=1)
        return block_data

    def _copy_hex(self):
        hex_val = f"#{int(self.r):02X}{int(self.g):02X}{int(self.b):02X}"
        self.clipboard_clear()
        self.clipboard_append(hex_val)

        self.toast_label.config(text="✓ Скопировано!")
        self.after(1800, lambda: self.toast_label.config(text=""))

    def _on_slider_change(self, model_name, ch_name):
        if self._is_updating:
            return

        data = self.controls[model_name][ch_name]
        val = int(round(data['slider'].get()))

        self._is_updating = True
        data['spinbox'].delete(0, tk.END)
        data['spinbox'].insert(0, str(val))
        self._is_updating = False

        self._recalc_and_update(model_name)

    def _on_spinbox_change(self, model_name, ch_name):
        if self._is_updating:
            return

        data = self.controls[model_name][ch_name]
        min_v, max_v = data['bounds']

        try:
            val = int(round(float(data['spinbox'].get())))
        except ValueError:
            val = int(round(data['slider'].get()))

        val = max(min_v, min(max_v, val))

        self._is_updating = True
        data['spinbox'].delete(0, tk.END)
        data['spinbox'].insert(0, str(val))
        data['slider'].set(val)
        self._is_updating = False

        self._recalc_and_update(model_name)

    def _recalc_and_update(self, source_model):
        vals = []
        for ch_name, data in self.controls[source_model].items():
            vals.append(int(round(data['slider'].get())))

        if source_model == 'RGB':
            self.r, self.g, self.b = vals
        elif source_model == 'CMYK':
            c, m, y, k = vals
            self.r, self.g, self.b = self.cmyk_to_rgb(c, m, y, k)
        elif source_model == 'HSV':
            h, s, v = vals
            self.r, self.g, self.b = self.hsv_to_rgb(h, s, v)

        self._update_all_from_rgb(skip_model=source_model)

    def _pick_color(self):
        r_int, g_int, b_int = int(self.r), int(self.g), int(self.b)
        color = colorchooser.askcolor(color=f"#{r_int:02x}{g_int:02x}{b_int:02x}", title="Выбор цвета")
        if color[0]:
            self.r, self.g, self.b = [int(c) for c in color[0]]
            self._update_all_from_rgb()

    def _update_all_from_rgb(self, skip_model=None):
        self._is_updating = True

        r_int, g_int, b_int = int(self.r), int(self.g), int(self.b)
        hex_color = f"#{r_int:02X}{g_int:02X}{b_int:02X}"

        self.color_box.config(bg=hex_color)

        luminance = 0.299 * r_int + 0.587 * g_int + 0.114 * b_int
        text_color = "#000000" if luminance > 128 else "#FFFFFF"

        self.color_box.itemconfig(self.canvas_text, text=hex_color, fill=text_color)
        self.hex_label.config(text=f"HEX: {hex_color}")

        if skip_model != 'RGB':
            self._set_controls('RGB', [('R', r_int), ('G', g_int), ('B', b_int)])

        if skip_model != 'CMYK':
            c, m, y, k = self.rgb_to_cmyk(r_int, g_int, b_int)
            self._set_controls('CMYK', [('C (%)', c), ('M (%)', m), ('Y (%)', y), ('K (%)', k)])

        if skip_model != 'HSV':
            h, s, v = self.rgb_to_hsv(r_int, g_int, b_int)
            self._set_controls('HSV', [('H (°)', h), ('S (%)', s), ('V (%)', v)])

        self._is_updating = False

    def _set_controls(self, model_name, values):
        for ch_name, val in values:
            target_key = next((k for k in self.controls[model_name] if k.upper().startswith(ch_name[0].upper())), None)
            if target_key:
                ch = self.controls[model_name][target_key]
                int_val = int(round(val))
                ch['slider'].set(int_val)
                ch['spinbox'].delete(0, tk.END)
                ch['spinbox'].insert(0, str(int_val))


if __name__ == "__main__":
    app = ColorApp()
    app.mainloop()