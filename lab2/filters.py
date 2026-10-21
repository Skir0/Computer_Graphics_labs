import numpy as np


def median_filter(img, size):
    """Медианный фильтр (порядковая статистика) с квадратным окном size x size.

    Работает с полутоновыми (H, W) и цветными (H, W, 3) изображениями,
    цветные обрабатываются независимо по каждому каналу.
    """
    if img.ndim == 3:
        result = np.empty_like(img)
        for c in range(img.shape[2]):
            result[:, :, c] = median_filter(img[:, :, c], size)
        return result

    h, w = img.shape
    r = size // 2

    # Края дополняем повторением граничных пикселей, чтобы окно всегда было полным
    padded = np.pad(img, r, mode="edge")

    # Вместо цикла по каждому пикселю собираем size*size сдвинутых копий изображения:
    # stack[:, y, x] - это все значения окна вокруг пикселя (y, x)
    stack = np.empty((size * size, h, w), dtype=img.dtype)
    k = 0
    for dy in range(size):
        for dx in range(size):
            stack[k] = padded[dy:dy + h, dx:dx + w]
            k += 1

    # Сортируем значения окна и берем средний элемент - это и есть медиана
    stack.sort(axis=0)
    return stack[size * size // 2]
