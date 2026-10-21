import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageTk

from filters import median_filter
from threshold import to_gray, histogram, otsu_threshold, iterative_threshold, binarize

PANEL_SIZE = 380   # размер области показа каждого изображения
HIST_H = 130       # высота области гистограммы
MAX_SIDE = 1000    # большие изображения уменьшаем, иначе медианный фильтр будет слишком долгим


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа 2: пороговая обработка и медианный фильтр")

        self.image = None          # текущее исходное изображение (numpy, uint8)
        self.photos = [None] * 3   # ссылки на PhotoImage, иначе tkinter их удалит

        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")

        ttk.Button(top, text="Открыть изображение", command=self.open_image).pack(side="left")

        ttk.Label(top, text="   Окно медианы:").pack(side="left")
        self.size_var = tk.StringVar(value="3")
        ttk.Combobox(top, textvariable=self.size_var, values=["3", "5", "7", "9"],
                     width=3, state="readonly").pack(side="left", padx=4)
        ttk.Button(top, text="Медианный фильтр", command=self.apply_median).pack(side="left")

        ttk.Button(top, text="Глобальный порог (Оцу и итерационный)",
                   command=self.apply_threshold).pack(side="left", padx=12)
        ttk.Button(top, text="Результат фильтра -> исходное",
                   command=self.result_to_source).pack(side="left")

        panels = ttk.Frame(root, padding=8)
        panels.pack()
        self.titles = []
        self.labels = []
        self.hists = []
        for i in range(3):
            frame = ttk.Frame(panels)
            frame.grid(row=0, column=i, padx=6)
            title = ttk.Label(frame, text="")
            title.pack()
            # Рамка фиксированного размера, чтобы окно не "прыгало" при смене изображений
            box = ttk.Frame(frame, width=PANEL_SIZE, height=PANEL_SIZE)
            box.pack_propagate(False)
            box.pack()
            label = ttk.Label(box)
            label.pack(expand=True)
            hist = tk.Canvas(frame, width=PANEL_SIZE, height=HIST_H, bg="white",
                             highlightthickness=1, highlightbackground="gray")
            hist.pack(pady=(6, 0))
            self.titles.append(title)
            self.labels.append(label)
            self.hists.append(hist)
        self.set_title(0, "Исходное")

        self.result = None  # последний результат медианного фильтра

    def set_title(self, i, text):
        self.titles[i].config(text=text)

    def show(self, i, arr):
        mode = "L" if arr.ndim == 2 else "RGB"
        pil = Image.fromarray(arr, mode)
        pil.thumbnail((PANEL_SIZE, PANEL_SIZE))
        self.photos[i] = ImageTk.PhotoImage(pil)
        self.labels[i].config(image=self.photos[i])

    def draw_hist(self, i, gray, t=None):
        """Гистограмма яркости под панелью i; если задан порог t, рисуем его красной линией."""
        canvas = self.hists[i]
        canvas.delete("all")
        # Логарифмический масштаб: иначе пики шума "соль и перец" (0 и 255)
        # делают остальную гистограмму почти незаметной
        h = np.log1p(histogram(gray))
        top = h.max()
        bar_w = PANEL_SIZE / 256
        base = HIST_H - 18
        for level in range(256):
            height = h[level] / top * (base - 12)
            x0 = level * bar_w
            canvas.create_rectangle(x0, base - height, x0 + bar_w, base, fill="#555555", outline="")
        canvas.create_text(2, HIST_H - 2, text="0", anchor="sw")
        canvas.create_text(PANEL_SIZE - 2, HIST_H - 2, text="255", anchor="se")
        canvas.create_text(PANEL_SIZE // 2, HIST_H - 2, text="яркость (лог. шкала)", anchor="s")
        if t is not None:
            x = t * bar_w
            canvas.create_line(x, 0, x, base, fill="red", width=2)
            if x > PANEL_SIZE - 60:
                canvas.create_text(x - 4, 2, text=f"T={t}", anchor="ne", fill="red")
            else:
                canvas.create_text(x + 4, 2, text=f"T={t}", anchor="nw", fill="red")

    def clear(self, i):
        self.photos[i] = None
        self.labels[i].config(image="")
        self.hists[i].delete("all")
        self.set_title(i, "")

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            pil = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            return
        pil.thumbnail((MAX_SIDE, MAX_SIDE))
        self.image = np.array(pil)
        self.result = None
        self.show(0, self.image)
        self.draw_hist(0, to_gray(self.image))
        self.set_title(0, "Исходное")
        self.clear(1)
        self.clear(2)

    def check_image(self):
        if self.image is None:
            messagebox.showinfo("Нет изображения", "Сначала откройте изображение")
            return False
        return True

    def apply_median(self):
        if not self.check_image():
            return
        size = int(self.size_var.get())
        self.root.config(cursor="watch")
        self.root.update()
        self.result = median_filter(self.image, size)
        self.root.config(cursor="")
        self.show(1, self.result)
        self.draw_hist(1, to_gray(self.result))
        self.set_title(1, f"Медианный фильтр {size}x{size}")
        self.clear(2)

    def apply_threshold(self):
        if not self.check_image():
            return
        gray = to_gray(self.image)
        t_otsu = otsu_threshold(gray)
        t_iter = iterative_threshold(gray)
        self.show(1, binarize(gray, t_otsu))
        self.draw_hist(1, gray, t_otsu)
        self.set_title(1, f"Оцу, T = {t_otsu}")
        self.show(2, binarize(gray, t_iter))
        self.draw_hist(2, gray, t_iter)
        self.set_title(2, f"Итерационный, T = {t_iter}")
        self.draw_hist(0, gray)

    def result_to_source(self):
        # Позволяет сначала убрать шум медианой, а затем применить пороговую обработку
        if self.result is None:
            messagebox.showinfo("Нет результата", "Сначала примените медианный фильтр")
            return
        self.image = self.result
        self.result = None
        self.show(0, self.image)
        self.draw_hist(0, to_gray(self.image))
        self.set_title(0, "Исходное (после фильтра)")
        self.clear(1)
        self.clear(2)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
