import math
import tkinter as tk

MIN_SCALE = 3
MAX_SCALE = 120
RULER_LEFT = 38
RULER_BOTTOM = 22

PIXEL_COLOR = (40, 90, 200)


class GridCanvas(tk.Canvas):

    def __init__(self, master, coord_var, **kwargs):
        super().__init__(master, bg="white", highlightthickness=1, highlightbackground="gray", **kwargs)
        self.coord_var = coord_var
        self.scale = 30
        self.ox = 80
        self.oy = 400
        self.pixels = []
        self.shape = None
        self.marked = []
        self.drag = None

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<MouseWheel>", self.on_wheel)
        self.bind("<Button-4>", lambda e: self.zoom(1.2, e.x, e.y))
        self.bind("<Button-5>", lambda e: self.zoom(1 / 1.2, e.x, e.y))
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Motion>", self.on_motion)

    def to_screen(self, x, y):
        return self.ox + x * self.scale, self.oy - y * self.scale

    def to_grid(self, sx, sy):
        return (sx - self.ox) / self.scale, (self.oy - sy) / self.scale


    def zoom(self, factor, cx=None, cy=None):
        if cx is None:
            cx = self.winfo_width() / 2
            cy = self.winfo_height() / 2
        new_scale = min(MAX_SCALE, max(MIN_SCALE, self.scale * factor))
        k = new_scale / self.scale
        # Сдвигаем начало координат так, чтобы точка под курсором осталась на месте
        self.ox = cx - (cx - self.ox) * k
        self.oy = cy - (cy - self.oy) * k
        self.scale = new_scale
        self.redraw()

    def on_wheel(self, event):
        self.zoom(1.2 if event.delta > 0 else 1 / 1.2, event.x, event.y)

    def on_press(self, event):
        self.drag = (event.x, event.y)

    def on_drag(self, event):
        self.ox += event.x - self.drag[0]
        self.oy += event.y - self.drag[1]
        self.drag = (event.x, event.y)
        self.redraw()

    def on_motion(self, event):
        x, y = self.to_grid(event.x, event.y)
        self.coord_var.set(f"Курсор: x = {rnd_int(x)}, y = {rnd_int(y)}")

    def fit(self):
        if self.shape is None:
            return
        if self.shape[0] == "line":
            xs = [self.shape[1], self.shape[3]]
            ys = [self.shape[2], self.shape[4]]
        else:
            _, xc, yc, r = self.shape
            xs = [xc - r, xc + r]
            ys = [yc - r, yc + r]
        min_x, max_x = min(xs + [0]) - 1, max(xs + [0]) + 1
        min_y, max_y = min(ys + [0]) - 1, max(ys + [0]) + 1

        width = max(self.winfo_width() - RULER_LEFT, 100)
        height = max(self.winfo_height() - RULER_BOTTOM, 100)
        self.scale = min(MAX_SCALE, max(MIN_SCALE, min(width / (max_x - min_x + 1), height / (max_y - min_y + 1))))
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        self.ox = RULER_LEFT + width / 2 - mid_x * self.scale
        self.oy = height / 2 + mid_y * self.scale
        self.redraw()

    def set_data(self, pixels, shape):
        self.pixels = pixels
        self.shape = shape
        self.marked = []

    def set_marked(self, points):
        self.marked = points
        self.redraw()


    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        s = self.scale

        left, top = self.to_grid(RULER_LEFT, 0)
        right, bottom = self.to_grid(w, h - RULER_BOTTOM)
        i_min = math.floor(left) - 1
        i_max = math.ceil(right) + 1
        j_min = math.floor(bottom) - 1
        j_max = math.ceil(top) + 1

        for p in self.pixels:
            a = p[2] if len(p) > 2 else 1.0
            sx, sy = self.to_screen(p[0], p[1])
            color = blend(a)
            self.create_rectangle(sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2, fill=color, outline="")
            # У сглаженных пикселей подписываем яркость, если клетка достаточно большая
            if a < 1 and s >= 40:
                self.create_text(sx, sy, text=f"{a:.2f}", font=("Arial", 8), fill="black" if a < 0.6 else "white")

        if s >= 6:
            for i in range(i_min, i_max + 1):
                sx, _ = self.to_screen(i - 0.5, 0)
                self.create_line(sx, 0, sx, h, fill="#d9d9d9")
            for j in range(j_min, j_max + 1):
                _, sy = self.to_screen(0, j - 0.5)
                self.create_line(0, sy, w, sy, fill="#d9d9d9")

        if self.shape is not None:
            if self.shape[0] == "line":
                x1, y1 = self.to_screen(self.shape[1], self.shape[2])
                x2, y2 = self.to_screen(self.shape[3], self.shape[4])
                self.create_line(x1, y1, x2, y2, fill="red", width=1.5)
            else:
                _, xc, yc, r = self.shape
                x1, y1 = self.to_screen(xc - r, yc + r)
                x2, y2 = self.to_screen(xc + r, yc - r)
                self.create_oval(x1, y1, x2, y2, outline="red", width=1.5)

        for x, y in self.marked:
            sx, sy = self.to_screen(x, y)
            self.create_rectangle(sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2, outline="#ff8c00", width=3)

        ax, ay = self.to_screen(0, 0)
        self.create_line(ax, 0, ax, h, fill="black", width=2, arrow=tk.FIRST)
        self.create_line(0, ay, w, ay, fill="black", width=2, arrow=tk.LAST)

        self.create_rectangle(0, 0, RULER_LEFT, h, fill="#f0f0f0", outline="")
        self.create_rectangle(0, h - RULER_BOTTOM, w, h, fill="#f0f0f0", outline="")

        label_step = 1
        for candidate in (1, 2, 5, 10, 20, 50, 100, 200, 500):
            label_step = candidate
            if s * candidate >= 28:
                break

        for i in range(i_min, i_max + 1):
            if i % label_step == 0:
                sx, _ = self.to_screen(i, 0)
                if RULER_LEFT < sx < w:
                    self.create_text(sx, h - RULER_BOTTOM / 2, text=str(i), font=("Arial", 9))
        for j in range(j_min, j_max + 1):
            if j % label_step == 0:
                _, sy = self.to_screen(0, j)
                if 0 < sy < h - RULER_BOTTOM:
                    self.create_text(RULER_LEFT / 2, sy, text=str(j), font=("Arial", 9))

        self.create_text(w - 12, ay - 12 if 12 < ay < h - 30 else h - 36, text="x", font=("Arial", 11, "bold"))
        self.create_text(ax + 12 if RULER_LEFT + 20 < ax < w else RULER_LEFT + 20, 12, text="y", font=("Arial", 11, "bold"))


def blend(a):
    r = round(255 - a * (255 - PIXEL_COLOR[0]))
    g = round(255 - a * (255 - PIXEL_COLOR[1]))
    b = round(255 - a * (255 - PIXEL_COLOR[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def rnd_int(v):
    return math.floor(v + 0.5)
