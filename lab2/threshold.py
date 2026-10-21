import numpy as np


def to_gray(img):
    """Перевод в градации серого (яркость по формуле ITU-R BT.601)."""
    if img.ndim == 2:
        return img
    r = img[:, :, 0].astype(np.float64)
    g = img[:, :, 1].astype(np.float64)
    b = img[:, :, 2].astype(np.float64)
    return np.round(0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)


def histogram(gray):
    return np.bincount(gray.ravel(), minlength=256)


def otsu_threshold(gray):
    """Метод Оцу: порог, максимизирующий межклассовую дисперсию."""
    p = histogram(gray) / gray.size
    levels = np.arange(256)
    mu_total = (levels * p).sum()

    best_t = 0
    best_var = -1.0
    w0 = 0.0       # доля пикселей фона (яркость <= t)
    mu_sum = 0.0   # накопленная сумма i * p[i] для фона

    for t in range(256):
        w0 += p[t]
        mu_sum += t * p[t]
        # Пока один из классов пуст, дисперсию считать нельзя
        if w0 <= 0 or w0 >= 1:
            continue
        mu0 = mu_sum / w0
        mu1 = (mu_total - mu_sum) / (1 - w0)
        var_between = w0 * (1 - w0) * (mu0 - mu1) ** 2
        if var_between > best_var:
            best_var = var_between
            best_t = t
    return best_t


def iterative_threshold(gray, eps=0.5):
    """Итерационный метод (Ридлер-Калвард).

    Начальный порог - средняя яркость. На каждом шаге считаем средние
    яркости двух классов и берем их полусумму как новый порог.
    """
    hist = histogram(gray)
    levels = np.arange(256)
    t = gray.mean()

    while True:
        k = int(t) + 1
        n1 = hist[:k].sum()
        n2 = hist[k:].sum()
        # Если один из классов пуст (однотонное изображение), уточнять нечего
        if n1 == 0 or n2 == 0:
            break
        m1 = (hist[:k] * levels[:k]).sum() / n1
        m2 = (hist[k:] * levels[k:]).sum() / n2
        new_t = (m1 + m2) / 2
        if abs(new_t - t) < eps:
            t = new_t
            break
        t = new_t
    return int(t)


def binarize(gray, t):
    return np.where(gray > t, 255, 0).astype(np.uint8)
