import tkinter as tk
from tkinter import ttk, messagebox

from algorithms import (step_by_step, dda, bresenham_line, bresenham_circle,
                        castle_pitteway, wu_line, measure)
from grid import GridCanvas

MAX_VALUE = 1000

LARGE_LINE = (0, 0, 1000, 600)
LARGE_CIRCLE = (0, 0, 500)

ALGORITHMS = [
    ("Пошаговый алгоритм", step_by_step, "line",
     "Уравнение прямой y = k*x + b, где k = dy/dx, b = y1 - k*x1.\n"
     "Для каждого целого x от x1 до x2 вычисляется y, затем округляется до ближайшего целого.\n"
     "Если отрезок крутой (|dy| > |dx|), роли осей меняются: x = k*y + b, k = dx/dy.\n"
     "На каждом шаге есть умножение и дробные числа - это самый медленный способ."),
    ("ЦДА", dda, "line",
     "L = max(|dx|, |dy|) - число шагов. Приращения: sx = dx/L, sy = dy/L.\n"
     "На каждом шаге: x = x + sx, y = y + sy, пиксель - округлённые x и y.\n"
     "Умножения в цикле нет, только сложение, но числа остаются дробными."),
    ("Брезенхем (отрезок)", bresenham_line, "line",
     "Только целые числа. dx = |x2-x1|, dy = |y2-y1| (у крутого отрезка меняются местами).\n"
     "Начальное d = 2*dy - dx.\n"
     "Если d < 0: шаг только по главной оси, d = d + 2*dy.\n"
     "Если d >= 0: шаг по обеим осям, d = d + 2*(dy - dx).\n"
     "d - ошибка, умноженная на 2*dx: по её знаку видно, к какому из двух пикселей прямая ближе."),
    ("Брезенхем (окружность)", bresenham_circle, "circle",
     "Окружность с центром (xc, yc) и радиусом R. Считается 1/8 окружности (от x = 0 до x = y),\n"
     "остальные 7 точек получаются симметрией: (±x, ±y) и (±y, ±x).\n"
     "Старт: x = 0, y = R, d = 3 - 2*R.\n"
     "Если d < 0: d = d + 4*x + 6 (y не меняется).\n"
     "Иначе: d = d + 4*(x - y) + 10, y уменьшается на 1. Затем x увеличивается на 1.\n"
     "В таблице для выбранной строки подсвечиваются все 8 точек шага."),
    ("Кастл-Питвей", castle_pitteway, "line",
     "Отрезок - это строка из шагов s (прямо) и d (по диагонали): dx-dy шагов s и dy шагов d (dx >= dy).\n"
     "Их нужно расставить как можно равномернее. Для этого используется алгоритм Евклида:\n"
     "пока a != b, из большего числа вычитается меньшее, а шаги склеиваются в блоки m1 и m2.\n"
     "Когда a = b, строка = (m1 + m2 в обратном порядке), повторённая a раз.\n"
     "В цикле рисования ошибка не считается - пиксели строятся по готовой строке.\n"
     "Результат совпадает с Брезенхемом, кроме «ничьих» (прямая ровно посередине между двумя "
     "пикселями): там выбираются разные, но одинаково близкие пиксели."),
    ("Сглаживание (Ву)", wu_line, "line",
     "Для каждого x прямая проходит между двумя пикселями по y: y0 = floor(y) и y0 + 1.\n"
     "Дробная часть f = y - y0. Яркость нижнего пикселя 1 - f, верхнего f (в сумме 1).\n"
     "Чем ближе центр пикселя к прямой, тем темнее пиксель. Яркость показана оттенком и числом.\n"
     "У крутого отрезка роли осей меняются."),
]

GRID_HELP = ("Привязка к сетке: пиксель (x, y) - клетка, центр которой имеет целые координаты (x, y). "
             "Линии сетки проходят по полуцелым значениям (x ± 0,5), подписи стоят по центрам клеток. "
             "Красная линия - идеальная фигура, оранжевая рамка - пиксели выбранного шага таблицы. "
             "Колесо мыши - масштаб, перетаскивание - сдвиг.")


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа 3: базовые растровые алгоритмы")

        self.row_pts = {}

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")

        ttk.Label(top, text="Алгоритм:").pack(side="left")
        self.alg_var = tk.StringVar(value=ALGORITHMS[0][0])
        combo = ttk.Combobox(top, textvariable=self.alg_var, state="readonly", width=24,
                             values=[a[0] for a in ALGORITHMS])
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", self.on_algorithm_change)

        self.line_vars = [tk.StringVar(value=v) for v in ("1", "1", "12", "6")]
        self.circle_vars = [tk.StringVar(value=v) for v in ("0", "0", "8")]
        fields = ttk.Frame(top)
        fields.pack(side="left")
        self.line_frame = self.make_fields(fields, ("x1", "y1", "x2", "y2"), self.line_vars)
        self.circle_frame = self.make_fields(fields, ("xc", "yc", "R"), self.circle_vars)
        self.line_frame.pack()

        ttk.Button(top, text="Построить", command=self.build).pack(side="left", padx=6)
        ttk.Button(top, text="Вписать", command=lambda: self.canvas.fit()).pack(side="left")
        ttk.Button(top, text="+", width=3, command=lambda: self.canvas.zoom(1.25)).pack(side="left", padx=(6, 0))
        ttk.Button(top, text="−", width=3, command=lambda: self.canvas.zoom(1 / 1.25)).pack(side="left")
        ttk.Button(top, text="Замер времени", command=self.show_timing).pack(side="left", padx=10)

        main = ttk.Frame(root, padding=(6, 0, 6, 6))
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        self.coord_var = tk.StringVar(value="Курсор: -")
        self.canvas = GridCanvas(left, self.coord_var, width=640, height=520)
        self.canvas.pack(fill="both", expand=True)
        ttk.Label(left, textvariable=self.coord_var).pack(anchor="w")
        ttk.Label(left, text=GRID_HELP, wraplength=620, justify="left").pack(anchor="w", pady=(2, 0))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", padx=(8, 0))
        ttk.Label(right, text="Таблица вычислений (выберите строку - пиксели подсветятся на сетке)").pack(anchor="w")
        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, show="headings", height=11)
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        ttk.Label(right, text="Пояснения").pack(anchor="w", pady=(6, 0))
        text_frame = ttk.Frame(right)
        text_frame.pack(fill="both")
        self.text = tk.Text(text_frame, width=62, height=15, wrap="word", font=("Arial", 10))
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=text_scroll.set)
        self.text.pack(side="left", fill="both")
        text_scroll.pack(side="left", fill="y")
        self.text.config(state="disabled")

        root.bind("<Return>", lambda e: self.build())
        root.after(100, self.build)

    def make_fields(self, parent, names, variables):
        frame = ttk.Frame(parent)
        for name, var in zip(names, variables):
            ttk.Label(frame, text=name + " =").pack(side="left", padx=(6, 1))
            ttk.Entry(frame, textvariable=var, width=6).pack(side="left")
        return frame

    def current(self):
        for item in ALGORITHMS:
            if item[0] == self.alg_var.get():
                return item

    def on_algorithm_change(self, event=None):
        self.line_frame.pack_forget()
        self.circle_frame.pack_forget()
        if self.current()[2] == "line":
            self.line_frame.pack()
        else:
            self.circle_frame.pack()
        self.build()

    def read_ints(self, variables):
        values = []
        for var in variables:
            try:
                value = int(var.get())
            except ValueError:
                messagebox.showerror("Ошибка", f"«{var.get()}» - не целое число")
                return None
            if abs(value) > MAX_VALUE:
                messagebox.showerror("Ошибка", f"Значения должны быть не больше {MAX_VALUE} по модулю")
                return None
            values.append(value)
        return values

    def build(self):
        name, func, kind, description = self.current()
        if kind == "line":
            values = self.read_ints(self.line_vars)
            if values is None:
                return
            shape = ("line",) + tuple(values)
        else:
            values = self.read_ints(self.circle_vars)
            if values is None:
                return
            if values[2] < 0:
                messagebox.showerror("Ошибка", "Радиус не может быть отрицательным")
                return
            shape = ("circle",) + tuple(values)

        pixels, header, rows, notes = func(*values)

        self.canvas.set_data(pixels, shape)
        self.canvas.fit()
        self.fill_table(header, rows)

        result = description + "\n"
        if notes:
            result += "\nХод вычислений:\n" + "\n".join(notes) + "\n"
        result += f"\nВходные данные: {', '.join(str(v) for v in values)}. Получено пикселей: {len(pixels)}."
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", result)
        self.text.config(state="disabled")

    def fill_table(self, header, rows):
        self.tree.delete(*self.tree.get_children())
        self.row_pts = {}
        self.tree["columns"] = list(range(len(header)))
        for i, title in enumerate(header):
            longest = max([len(title)] + [len(str(values[i])) for values, _ in rows])
            width = 40 if title == "№" else 16 + 8 * longest
            self.tree.heading(i, text=title)
            self.tree.column(i, width=width, anchor="center", stretch=False)
        for i, (values, pts) in enumerate(rows):
            self.tree.insert("", "end", iid=str(i), values=values)
            self.row_pts[str(i)] = pts

    def on_row_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.canvas.set_marked(self.row_pts[selected[0]])

    def show_timing(self):
        line = self.read_ints(self.line_vars)
        circle = self.read_ints(self.circle_vars)
        if line is None or circle is None or circle[2] < 0:
            return

        win = tk.Toplevel(self.root)
        win.title("Замер времени работы алгоритмов")
        columns = ("Алгоритм", "Ваш пример, мкс", "Пикселей", "Большой пример, мкс", "Пикселей")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=len(ALGORITHMS))
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=190 if col == "Алгоритм" else 140, anchor="center")
        tree.pack(padx=8, pady=8)

        for name, func, kind, _ in ALGORITHMS:
            small_args = tuple(line) if kind == "line" else tuple(circle)
            large_args = LARGE_LINE if kind == "line" else LARGE_CIRCLE
            small_time = measure(func, small_args, 1000)
            large_time = measure(func, large_args, 20)
            small_count = len(func(*small_args, False)[0])
            large_count = len(func(*large_args, False)[0])
            tree.insert("", "end", values=(name, f"{small_time:.1f}", small_count,
                                           f"{large_time:.1f}", large_count))

        info = (f"Среднее время одного построения (без таблицы и без отрисовки).\n"
                f"Ваш пример: 1000 запусков. Большой пример: отрезок {LARGE_LINE}, "
                f"окружность с центром (0, 0) и R = {LARGE_CIRCLE[2]}: 20 запусков.")
        ttk.Label(win, text=info, justify="left").pack(padx=8, pady=(0, 8), anchor="w")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
