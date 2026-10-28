import math
import time

def rnd(v):
    return math.floor(v + 0.5)


def step_by_step(x1, y1, x2, y2, trace=True):
    """Пошаговый алгоритм: считаем y = k*x + b для каждого целого x."""
    pixels = []
    rows = []
    header = ("№", "x", "y (точно)", "пиксель x", "пиксель y")
    dx = x2 - x1
    dy = y2 - y1

    if abs(dx) >= abs(dy):
        # Отрезок пологий - идём по x с шагом 1, y вычисляем по формуле
        k = dy / dx if dx != 0 else 0
        b = y1 - k * x1
        step = 1 if x2 >= x1 else -1
        for i, x in enumerate(range(x1, x2 + step, step)):
            y = k * x + b
            py = rnd(y)
            pixels.append((x, py))
            if trace:
                rows.append(((i, x, f"{y:.3f}", x, py), [(x, py)]))
    else:
        # Отрезок крутой - меняем роли осей, иначе в пикселях были бы разрывы
        k = dx / dy
        b = x1 - k * y1
        step = 1 if y2 >= y1 else -1
        for i, y in enumerate(range(y1, y2 + step, step)):
            x = k * y + b
            px = rnd(x)
            pixels.append((px, y))
            if trace:
                rows.append(((i, f"{x:.3f}", y, px, y), [(px, y)]))
    return pixels, header, rows, []


def dda(x1, y1, x2, y2, trace=True):
    """ЦДА: за один шаг основная координата меняется на 1, вторая - на дробную добавку."""
    pixels = []
    rows = []
    header = ("№", "x (точно)", "y (точно)", "пиксель x", "пиксель y")
    dx = x2 - x1
    dy = y2 - y1

    # Количество шагов равно длине проекции на ту ось, где она больше
    length = max(abs(dx), abs(dy))
    if length == 0:
        sx = 0
        sy = 0
    else:
        sx = dx / length
        sy = dy / length

    x = x1
    y = y1
    for i in range(length + 1):
        px = rnd(x)
        py = rnd(y)
        pixels.append((px, py))
        if trace:
            rows.append(((i, f"{x:.3f}", f"{y:.3f}", px, py), [(px, py)]))
        # Накапливаем приращения (из-за этого к концу набегает небольшая погрешность)
        x += sx
        y += sy
    return pixels, header, rows, []


def bresenham_line(x1, y1, x2, y2, trace=True):
    """Брезенхем для отрезка: только целые числа, решение принимается по знаку d."""
    pixels = []
    rows = []
    header = ("№", "x", "y", "d", "шаг")
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1

    # Для крутых отрезков главная ось - y, поэтому меняем dx и dy местами
    steep = dy > dx
    if steep:
        dx, dy = dy, dx

    # d - ошибка, умноженная на 2*dx, чтобы не использовать дроби
    d = 2 * dy - dx
    x = x1
    y = y1
    for i in range(dx + 1):
        pixels.append((x, y))
        if d >= 0:
            # Отрезок ушёл от прямой больше, чем на пол-пикселя - шагаем по обеим осям
            if trace:
                rows.append(((i, x, y, d, "по диагонали"), [(x, y)]))
            x += sx
            y += sy
            d += 2 * (dy - dx)
        else:
            # Шагаем только по главной оси
            if trace:
                rows.append(((i, x, y, d, "прямо"), [(x, y)]))
            if steep:
                y += sy
            else:
                x += sx
            d += 2 * dy
    return pixels, header, rows, []


def bresenham_circle(xc, yc, r, trace=True):
    """Брезенхем для окружности: считаем только 1/8 окружности, остальное по симметрии."""
    pixels = []
    rows = []
    seen = set()
    header = ("№", "x", "y", "d", "выбор")

    x = 0
    y = r
    d = 3 - 2 * r
    i = 0
    while x <= y:
        # 8 симметричных точек. На осях и диагоналях точки совпадают, дубли не добавляем
        points = [(xc + x, yc + y), (xc - x, yc + y), (xc + x, yc - y), (xc - x, yc - y),
                  (xc + y, yc + x), (xc - y, yc + x), (xc + y, yc - x), (xc - y, yc - x)]
        for p in points:
            if p not in seen:
                seen.add(p)
                pixels.append(p)
        if d < 0:
            if trace:
                rows.append(((i, x, y, d, "y не меняется"), points))
            d += 4 * x + 6
        else:
            if trace:
                rows.append(((i, x, y, d, "y уменьшается на 1"), points))
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
        i += 1
    return pixels, header, rows, []


def castle_pitteway(x1, y1, x2, y2, trace=True):
    """Кастл-Питвей: последовательность шагов строится алгоритмом Евклида, без вычисления ошибки.

    Шаг бывает двух видов: s - прямо (меняется только главная координата),
    d - по диагонали (меняются обе). Нужно расставить dx-dy шагов s и dy шагов d так,
    чтобы они чередовались как можно равномернее.
    """
    pixels = []
    rows = []
    notes = []
    header = ("№", "шаг", "x", "y")
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1
    steep = dy > dx
    if steep:
        dx, dy = dy, dx

    a = dx - dy   # сколько шагов "прямо"
    b = dy        # сколько шагов "по диагонали"
    m1 = "s"
    m2 = "d"
    if dx == 0:
        word = ""
    elif b == 0:
        word = "s" * dx
    elif a == 0:
        word = "d" * dx
    else:
        notes.append(f"Начало: a = dx-dy = {a} (шагов s), b = dy = {b} (шагов d), m1 = '{m1}', m2 = '{m2}'")
        # Вычитаем меньшее число из большего (как в алгоритме Евклида)
        # и "склеиваем" шаги в более длинные блоки
        while a != b:
            if a > b:
                a -= b
                m2 = m1 + m2[::-1]
            else:
                b -= a
                m1 = m2 + m1[::-1]
            notes.append(f"a = {a}, b = {b}, m1 = '{m1}', m2 = '{m2}'")
        # Когда a == b, блок "m1 + перевёрнутый m2" повторяется a раз
        word = (m1 + m2[::-1]) * a
        notes.append(f"a = b = {a}: итоговая строка = ('{m1}' + '{m2[::-1]}') * {a} = '{word}'")

    x = x1
    y = y1
    pixels.append((x, y))
    if trace:
        rows.append(((0, "старт", x, y), [(x, y)]))
    for i, move in enumerate(word, 1):
        if move == "d":
            x += sx
            y += sy
        elif steep:
            y += sy
        else:
            x += sx
        pixels.append((x, y))
        if trace:
            rows.append(((i, "по диагонали" if move == "d" else "прямо", x, y), [(x, y)]))
    return pixels, header, rows, notes


def wu_line(x1, y1, x2, y2, trace=True):
    """Сглаживание (Ву): яркость двух соседних пикселей зависит от расстояния до идеальной прямой."""
    pixels = []
    rows = []
    header = ("№", "главная ось", "вторая (точно)", "пиксель 1 (яркость)", "пиксель 2 (яркость)")

    # Приводим к случаю "пологий отрезок слева направо"
    steep = abs(y2 - y1) > abs(x2 - x1)
    if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

    dx = x2 - x1
    dy = y2 - y1
    k = dy / dx if dx != 0 else 0

    for i, x in enumerate(range(x1, x2 + 1)):
        y = y1 + k * (x - x1)
        y0 = math.floor(y)
        frac = y - y0   # на сколько прямая сдвинута от центра нижнего пикселя
        a1 = 1 - frac   # чем ближе прямая к пикселю, тем он ярче
        a2 = frac
        cur = []
        # Пиксели с нулевой яркостью (когда прямая точно в центре) не рисуем
        if a1 > 1e-9:
            cur.append((y0, a1))
        if a2 > 1e-9:
            cur.append((y0 + 1, a2))
        pts = []
        for py, a in cur:
            # Если меняли оси местами, возвращаем координаты обратно
            p = (py, x, a) if steep else (x, py, a)
            pixels.append(p)
            pts.append(p[:2])
        if trace:
            text = ["", ""]
            for j, (py, a) in enumerate(cur):
                text[j] = f"y={py} ({a:.2f})"
            rows.append(((i, x, f"{y:.3f}", text[0], text[1]), pts))
    return pixels, header, rows, []


def measure(func, args, repeats):
    """Среднее время одного запуска алгоритма в микросекундах (без построения таблицы)."""
    start = time.perf_counter()
    for _ in range(repeats):
        func(*args, False)
    return (time.perf_counter() - start) / repeats * 1e6
