"""Рендер кадров 05–07 для раздела «Следы».

Запуск из папки tools:  python render_traces.py ../assets
Нужны numpy и Pillow. Сохраняет PNG; для сайта они конвертированы в WebP.
"""
import sys, time
import numpy as np
from voxel import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "../assets"
which = sys.argv[2] if len(sys.argv) > 2 else "abc"


def base_world(seed, X=112, Y=64, Z=112, lo=26, amp=8, scale=28):
    rng = np.random.default_rng(seed)
    W = np.zeros((X, Y, Z), np.uint8)
    H = lo + value_noise(rng, X, Z, scale) * amp
    return rng, W, H


def scatter_trees(W, H, rng, n, avoid, leaves_p=1.0, water_level=None):
    X, Y, Z = W.shape
    placed = 0
    for _ in range(n * 20):
        x, z = rng.integers(3, X - 3, 2)
        if avoid(x, z):
            continue
        y = int(H[x, z]) + 1
        if W[x, y - 1, z] != GRASS:
            continue
        tree(W, x, y, z, rng, leaves=rng.random() < leaves_p)
        placed += 1
        if placed >= n:
            break


# ---------------- A: туннель 2x2 в скале
def scene_a():
    rng, W, H = base_world(11, lo=27, amp=3)
    X, Y, Z = W.shape
    H = np.round(H)
    n2 = value_noise(np.random.default_rng(3), X, Z, 7)
    fill_terrain(W, H)
    base = int(H[56, 50])
    # каменная скала: отвесная стена у z=56 с неровным верхом
    for x in range(X):
        for z in range(56, Z):
            top = base + 7 + int(n2[x, z] * 4) + min((z - 56) // 3, 4)
            front = 56 + int(n2[x, 56] * 3)
            if z < front:
                continue
            W[x, 20:top, z] = STONE
            W[x, top - 1, z] = DIRT
            W[x, top, z] = GRASS
            H[x, z] = top
    gy = base + 1
    W[55:57, gy:gy + 2, 50:80] = AIR
    W[55:57, gy - 1, 56:80] = STONE
    scatter_trees(W, H, rng, 40, lambda x, z: (40 < x < 72 and 36 < z < 62))
    cam = (52.8, gy + 1.62, 45.5)
    return W, cam, 13.0, 7.0, (13, 46)


# ---------------- B: песчаная пирамида в воде
def scene_b():
    rng, W, H = base_world(23, lo=26, amp=10, scale=30)
    X, Y, Z = W.shape
    wl = 30
    yy, xx = np.mgrid[0:X, 0:Z]
    lake = np.exp(-(((yy - 56) / 26) ** 2 + ((xx - 62) / 20) ** 2))
    H = H - lake * 12
    H = np.round(H)
    fill_terrain(W, H, water_level=wl)
    # пирамида
    cx, cz = 56, 64
    bottom = int(H[cx, cz]) + 1
    size = wl + 4 - bottom
    for i in range(size + 1):
        r = size - i
        y = bottom + i
        W[cx - r:cx + r + 1, y, cz - r:cz + r + 1] = SAND
    scatter_trees(W, H, rng, 40, lambda x, z: z < 46 and 30 < x < 85, water_level=wl)
    cam = (49.5, wl + 2.62, 44.0)
    # берег под камерой
    W[50:62, wl - 1:wl + 1, 40:47] = SAND
    W[50:62, wl + 1, 40:47] = AIR
    return W, cam, 18.0, -6.0, (12, 40)


# ---------------- C: деревья без листьев
def scene_c():
    rng, W, H = base_world(5, lo=27, amp=5, scale=34)
    H = np.round(H)
    fill_terrain(W, H)
    X, Y, Z = W.shape
    # обычные деревья по краям
    scatter_trees(W, H, rng, 60, lambda x, z: 42 < x < 72 and 40 < z < 100 or z < 47)
    # роща голых стволов в центре
    spots = [(50, 56, 5), (57, 60, 6), (62, 55, 4), (53, 66, 6), (65, 64, 5), (59, 72, 5), (48, 76, 6), (68, 79, 4), (55, 84, 6), (61, 90, 5), (45, 63, 4)]
    for x, z, hgt in spots:
        y = int(H[x, z]) + 1
        tree(W, x, y, z, rng, height=hgt, leaves=False)
    cam = (56.5, int(H[56, 46]) + 2.62, 46.0)
    return W, cam, -3.0, 2.0, (12, 44)


def hud(img):
    # прицел
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    w, h = img.size
    cx, cy = w // 2, h // 2
    d.rectangle([cx - 9, cy - 1, cx + 9, cy + 1], fill=(235, 235, 235))
    d.rectangle([cx - 1, cy - 9, cx + 1, cy + 9], fill=(235, 235, 235))
    return img


for key, fn, name in (("a", scene_a, "trace-tunnel"), ("b", scene_b, "trace-pyramid"), ("c", scene_c, "trace-bare-trees")):
    if key not in which:
        continue
    t0 = time.time()
    W, cam, yaw, pitch, fog = fn()
    img = render(W, cam, yaw, pitch, fog=fog)
    img = hud(img)
    img.save(f"{OUT}/{name}.png")
    img.save(f"{OUT}/{name}.webp", quality=86)
    print(name, round(time.time() - t0, 1), "s")
