"""Простой воксельный рендерер в духе Minecraft Alpha (собственные процедурные текстуры)."""
import numpy as np
from PIL import Image

AIR, GRASS, DIRT, STONE, SAND, WATER, LOG, LEAVES, GRAVEL = range(9)


def _noise_tex(rng, base, amp, size=16):
    n = rng.uniform(-amp, amp, (size, size, 1))
    return np.clip(np.array(base)[None, None, :] + n, 0, 1)


def make_textures(seed=7):
    rng = np.random.default_rng(seed)
    T = {}
    # каждая текстура: dict face-> (16,16,3), alpha (16,16)
    grass_top = _noise_tex(rng, (0.40, 0.66, 0.24), 0.07)
    m = rng.random((16, 16)) < 0.25
    grass_top[m] *= 0.85
    dirt = _noise_tex(rng, (0.53, 0.38, 0.26), 0.05)
    m = rng.random((16, 16)) < 0.18
    dirt[m] = dirt[m] * 0.75
    m = rng.random((16, 16)) < 0.08
    dirt[m] = np.clip(dirt[m] * 1.25, 0, 1)
    grass_side = dirt.copy()
    edge = 3 + rng.integers(0, 3, 16)
    for x in range(16):
        grass_side[: edge[x], x] = grass_top[: edge[x], x] * 0.95
    stone = _noise_tex(rng, (0.50, 0.50, 0.50), 0.05)
    for _ in range(9):
        cx, cy = rng.integers(0, 16, 2)
        stone[cy, cx:cx + rng.integers(2, 5)] *= 0.72
    sand = _noise_tex(rng, (0.86, 0.81, 0.60), 0.04)
    gravel = _noise_tex(rng, (0.52, 0.48, 0.46), 0.12)
    water = _noise_tex(rng, (0.17, 0.30, 0.78), 0.03)
    log_side = np.zeros((16, 16, 3))
    for x in range(16):
        shade = 0.85 + 0.25 * rng.random()
        log_side[:, x] = np.array((0.40, 0.31, 0.19)) * shade
    log_side += rng.uniform(-0.03, 0.03, (16, 16, 1))
    log_top = np.zeros((16, 16, 3))
    yy, xx = np.mgrid[0:16, 0:16]
    r = np.maximum(abs(xx - 7.5), abs(yy - 7.5))
    ring = (np.floor(r) % 2 == 0)
    log_top[:] = (0.68, 0.55, 0.33)
    log_top[ring] = (0.60, 0.48, 0.28)
    log_top[r > 6.5] = log_side[r > 6.5]
    leaves = _noise_tex(rng, (0.22, 0.55, 0.14), 0.09)
    m = rng.random((16, 16)) < 0.3
    leaves[m] *= 0.7
    leaves_a = (rng.random((16, 16)) > 0.18).astype(float)

    one = np.ones((16, 16))
    def blk(top, side, bottom, a=one):
        return {"top": np.clip(top, 0, 1), "side": np.clip(side, 0, 1),
                "bottom": np.clip(bottom, 0, 1), "a": a}
    T[GRASS] = blk(grass_top, grass_side, dirt)
    T[DIRT] = blk(dirt, dirt, dirt)
    T[STONE] = blk(stone, stone, stone)
    T[SAND] = blk(sand, sand, sand)
    T[GRAVEL] = blk(gravel, gravel, gravel)
    T[WATER] = blk(water, water, water)
    T[LOG] = blk(log_top, log_side, log_top)
    T[LEAVES] = blk(leaves, leaves, leaves, leaves_a)
    return T


def render(W, cam, yaw, pitch, w=1000, h=540, fov=70, fog=(14, 46),
           fogcol=(0.78, 0.85, 0.97), skytop=(0.55, 0.70, 1.0), seed=7,
           max_steps=260, occl=0.42):
    T = make_textures(seed)
    # таблица текстур: [id, face(0 top,1 side,2 bottom), 16,16, 4]
    tex = np.zeros((9, 3, 16, 16, 4))
    for bid, d in T.items():
        for fi, f in enumerate(("top", "side", "bottom")):
            tex[bid, fi, :, :, :3] = d[f]
            tex[bid, fi, :, :, 3] = d["a"]
    X, Y, Z = W.shape
    solid = (W != AIR) & (W != WATER)
    # высота верхнего непрозрачного блока для «небесного» освещения
    ys = np.arange(Y)[None, :, None]
    top = np.where(solid.any(axis=1), (solid * ys).max(axis=1), -1)
    # распространение света как в Minecraft: 15 под открытым небом, -1 за каждый шаг
    air = ~solid
    L = np.where(air & (ys > top[:, None, :]), 15, 0).astype(np.int16)
    for _ in range(15):
        P = np.pad(L, 1, constant_values=0)
        nmax = np.maximum.reduce([P[2:, 1:-1, 1:-1], P[:-2, 1:-1, 1:-1], P[1:-1, 2:, 1:-1],
                                  P[1:-1, :-2, 1:-1], P[1:-1, 1:-1, 2:], P[1:-1, 1:-1, :-2]])
        L = np.where(air, np.maximum(L, nmax - 1), 0)
    lut = 0.72 ** (15 - np.arange(16))
    lut = np.maximum(lut, 0.06)

    fogcol = np.array(fogcol); skytop = np.array(skytop)
    aspect = w / h
    th = np.tan(np.radians(fov) / 2)
    px = (np.arange(w) + 0.5) / w * 2 - 1
    py = 1 - (np.arange(h) + 0.5) / h * 2
    PX, PY = np.meshgrid(px * th * aspect, py * th)
    cy, sy = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    cp, sp = np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    fwd = np.array([sy * cp, sp, cy * cp])
    right = np.array([cy, 0, -sy])
    up = np.cross(fwd, right)
    D = fwd[None, None] + PX[..., None] * right + PY[..., None] * up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    D = D.reshape(-1, 3)
    N = D.shape[0]
    O = np.tile(np.array(cam, float), (N, 1))

    cell = np.floor(O).astype(int)
    step = np.sign(D).astype(int)
    step[step == 0] = 1
    with np.errstate(divide="ignore"):
        tdelta = np.abs(1.0 / D)
    nxt = cell + (step > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        tmax = (nxt - O) / D
    tmax[~np.isfinite(tmax)] = np.inf
    tdelta[~np.isfinite(tdelta)] = np.inf

    # небо
    sky_t = np.clip(D[:, 1] * 2.2, 0, 1)[:, None]
    color = fogcol * (1 - sky_t) + skytop * sky_t
    result = color.copy()
    done = np.zeros(N, bool)
    wacc = np.zeros((N, 3)); wwt = np.zeros(N); inwater = np.zeros(N, bool)
    idx_all = np.arange(N)
    for _ in range(max_steps):
        act = idx_all[~done]
        if act.size == 0:
            break
        tm = tmax[act]
        ax = np.argmin(tm, axis=1)
        t = tm[np.arange(act.size), ax]
        c = cell[act]
        c[np.arange(act.size), ax] += step[act, ax]
        cell[act] = c
        tmax[act, ax] += tdelta[act, ax]
        oob = (c[:, 0] < 0) | (c[:, 0] >= X) | (c[:, 1] < 0) | (c[:, 1] >= Y) | (c[:, 2] < 0) | (c[:, 2] >= Z) | (t > fog[1] + 4)
        done[act[oob]] = True
        ok = ~oob
        act, c, ax, t = act[ok], c[ok], ax[ok], t[ok]
        b = W[c[:, 0], c[:, 1], c[:, 2]]
        hit = b != AIR
        act, c, ax, t, b = act[hit], c[hit], ax[hit], t[hit], b[hit]
        if act.size == 0:
            continue
        p = O[act] + D[act] * t[:, None]
        sgn = step[act, ax]
        face = np.where(ax == 1, np.where(sgn < 0, 0, 2), 1)
        fr = p - np.floor(p)
        u = np.where(ax == 0, fr[:, 2], fr[:, 0])
        v = np.where(ax == 1, fr[:, 2], 1 - fr[:, 1])
        tu = np.clip((u * 16).astype(int), 0, 15)
        tv = np.clip((v * 16).astype(int), 0, 15)
        texel = tex[b, face, tv, tu]
        transparent = texel[:, 3] < 0.5
        # освещение граней как в ранних версиях
        bright = np.where(ax == 1, np.where(sgn < 0, 1.0, 0.5), np.where(ax == 0, 0.8, 0.62))
        nb = c.copy(); nb[np.arange(act.size), ax] -= sgn
        nb = np.clip(nb, 0, [X - 1, Y - 1, Z - 1])
        light = bright * lut[L[nb[:, 0], nb[:, 1], nb[:, 2]]]
        col = texel[:, :3] * light[:, None]
        f = np.clip((t - fog[0]) / (fog[1] - fog[0]), 0, 1)[:, None]
        col = col * (1 - f) + fogcol * f
        isw = b == WATER
        # вода: полупрозрачная, учитываем первую поверхность
        wfirst = isw & ~inwater[act]
        wa = act[wfirst]
        wacc[wa] = col[wfirst]; wwt[wa] = 0.8; inwater[wa] = True
        final = ~isw & ~transparent
        fa = act[final]
        result[fa] = col[final]
        done[fa] = True
        # вода заканчивается, если вышли из неё (не важно для сцены)
    # для лучей без попадания — небо с туманом
    result = result * (1 - wwt[:, None]) + wacc * wwt[:, None]
    img = (np.clip(result, 0, 1).reshape(h, w, 3) * 255).astype(np.uint8)
    return Image.fromarray(img)


# ------------------------------------------------------------------ мир

def value_noise(rng, X, Z, scale, octaves=3):
    out = np.zeros((X, Z))
    amp = 1.0; tot = 0
    for o in range(octaves):
        s = scale / (2 ** o)
        gx, gz = int(X / s) + 2, int(Z / s) + 2
        g = rng.random((gx, gz))
        xs = np.arange(X) / s; zs = np.arange(Z) / s
        x0 = xs.astype(int); z0 = zs.astype(int)
        fx = xs - x0; fz = zs - z0
        fx = fx * fx * (3 - 2 * fx); fz = fz * fz * (3 - 2 * fz)
        a = g[x0][:, z0]; bb = g[x0 + 1][:, z0]; cc = g[x0][:, z0 + 1]; dd = g[x0 + 1][:, z0 + 1]
        v = (a * (1 - fx)[:, None] + bb * fx[:, None]) * (1 - fz)[None] + (cc * (1 - fx)[:, None] + dd * fx[:, None]) * fz[None]
        out += v * amp; tot += amp; amp *= 0.5
    return out / tot


def fill_terrain(W, H, water_level=None):
    X, Y, Z = W.shape
    for x in range(X):
        for z in range(Z):
            hgt = int(H[x, z])
            W[x, :max(hgt - 3, 0), z] = STONE
            W[x, max(hgt - 3, 0):hgt, z] = DIRT
            if water_level is not None and hgt < water_level + 1:
                W[x, max(hgt - 2, 0):hgt + 1, z] = SAND
                W[x, hgt + 1:water_level + 1, z] = WATER
            else:
                W[x, hgt, z] = GRASS


def tree(W, x, y, z, rng, height=None, leaves=True):
    X, Y, Z = W.shape
    hgt = height or int(rng.integers(4, 7))
    if leaves:
        top = y + hgt
        for dy in range(-2, 2):
            r = 2 if dy < 0 else 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if abs(dx) == r and abs(dz) == r and (dy == 1 or rng.random() < 0.5):
                        continue
                    xx, yy, zz = x + dx, top + dy, z + dz
                    if 0 <= xx < X and 0 <= yy < Y and 0 <= zz < Z and W[xx, yy, zz] == AIR:
                        W[xx, yy, zz] = LEAVES
    for i in range(hgt):
        if y + i < Y:
            W[x, y + i, z] = LOG
