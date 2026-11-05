"""11 biome tilesets (32x32 tiles) + biome props.

Atlas layout (8 columns x 4 rows = 256 x 128 px):
  row 0: cols 0-3 base ground variants, cols 4-7 decorated ground variants
  rows 1-2: 16 corner-matched transition tiles (base -> secondary terrain),
            index = TL*8 + TR*4 + BL*2 + BR   (1 = secondary terrain at that corner)
  row 3: cols 0-3 secondary terrain variants, cols 4-7 solid obstacle tiles
"""
import math
import random
import numpy as np

from .core import Canvas, R, rgba, mix, _shift
from .palette import OUTLINE, INK
from . import furniture as F

T = 32


def noise_grid(seed, n=32, scale=8, octaves=2):
    """Tile-periodic value noise (seamless across 32px tile edges)."""
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sc = max(2, scale // (2 ** o))
        G = n // sc
        rnd = np.random.default_rng(seed * 7 + o)
        g = rnd.random((G, G))
        ys, xs = np.mgrid[0:n, 0:n] / sc
        x0, y0 = xs.astype(int), ys.astype(int)
        fx, fy = xs - x0, ys - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        x1, y1 = (x0 + 1) % G, (y0 + 1) % G
        x0, y0 = x0 % G, y0 % G
        a = g[y0, x0] * (1 - fx) + g[y0, x1] * fx
        b = g[y1, x0] * (1 - fx) + g[y1, x1] * fx
        out += (a * (1 - fy) + b * fy) * amp
        tot += amp
        amp *= 0.45
    return out / tot


# ------------------------------------------------------------------ surfaces
def surface(kind, ramp, seed):
    """Fill a 32x32 tile with a seamless-ish textured surface."""
    cv = Canvas(T)
    rr = R(ramp)
    rnd = random.Random(seed)
    yy, xx = np.mgrid[0:T, 0:T]
    if kind in ('grass', 'sand', 'snow', 'dirt', 'mud', 'regolith', 'swamp'):
        n = noise_grid(sum(map(ord, str(ramp))) % 997, T, 8)  # shared periodic macro pattern -> seamless
        lvl = np.where(n < 0.33, 0, np.where(n < 0.72, 1, 2))
        base = np.full((T, T), 1)
        base[lvl == 0] = 1
        cv.img[:] = rgba(rr[1])
        cv.img[lvl == 2] = rgba(rr[2])
        # texture marks
        for i in range(14 if kind == 'grass' else 9):
            x, y = rnd.randrange(T), rnd.randrange(T)
            if kind == 'grass':
                cv.px(x, y, rr[2]); cv.px(x, y - 1, rr[3]); cv.px(x + 1, y + 1, rr[0])
            elif kind == 'sand':
                cv.px(x, y, rr[2] if i % 2 else rr[0])
                if i % 3 == 0:
                    cv.hline(x, x + 3, y, rr[2])
            elif kind == 'snow':
                cv.px(x, y, rr[3] if i % 2 else rr[0])
            elif kind == 'regolith':
                if i % 4 == 0:
                    m = cv.mask_ellipse(x, y, 2.5, 1.6)
                    cv.paint(m, rr[0]); cv.px(x - 1, y - 1, rr[2])
                else:
                    cv.px(x, y, rr[0])
            else:
                cv.px(x, y, rr[0] if i % 2 else rr[2])
    elif kind == 'cobble':
        cv.img[:] = rgba(rr[0])
        rows = [0, 8, 16, 24]
        for ri, y0 in enumerate(rows):
            off = (ri % 2) * 5
            x = -off
            while x < T:
                w = rnd.choice([8, 9, 10])
                m = cv.mask_rect(x + 1, y0 + 1, x + w - 1, y0 + 7)
                m &= ~(cv.mask_rect(x + 1, y0 + 1, x + 1, y0 + 1) | cv.mask_rect(x + w - 1, y0 + 7, x + w - 1, y0 + 7))
                cv.shade(m, ramp)
                x += w
    elif kind in ('flagstone', 'dungeon'):
        cv.img[:] = rgba(rr[0])
        for (x0, y0, x1, y1) in [(0, 0, 15, 15), (16, 0, 31, 15), (0, 16, 15, 31), (16, 16, 31, 31)]:
            m = cv.mask_rect(x0 + 1, y0 + 1, x1, y1)
            cv.shade(m, ramp)
            if rnd.random() < 0.5:
                cx, cy = rnd.randint(x0 + 3, x1 - 3), rnd.randint(y0 + 3, y1 - 3)
                cv.line(cx, cy, cx + rnd.randint(-3, 3), cy + rnd.randint(2, 4), rr[0])
        if kind == 'dungeon':
            for i in range(4):
                cv.px(rnd.randrange(T), rnd.randrange(T), R('swamp')[2])
    elif kind == 'planks':
        cv.img[:] = rgba(rr[1])
        for y0 in range(0, T, 8):
            cv.hline(0, T - 1, y0, rr[0])
            cv.hline(0, T - 1, y0 + 1, rr[2])
            cut = (y0 * 7 + seed * 5) % T
            cv.vline(cut, y0, y0 + 7, rr[0])
            for k in range(3):
                cv.px(rnd.randrange(T), y0 + rnd.randint(3, 6), rr[0])
    elif kind == 'metal':
        cv.img[:] = rgba(rr[1])
        for (x0, y0) in [(0, 0), (16, 0), (0, 16), (16, 16)]:
            cv.hline(x0, x0 + 15, y0, rr[3]); cv.vline(x0, y0, y0 + 15, rr[2])
            cv.hline(x0, x0 + 15, y0 + 15, rr[0]); cv.vline(x0 + 15, y0, y0 + 15, rr[0])
            for (dx, dy) in [(2, 2), (13, 2), (2, 13), (13, 13)]:
                cv.px(x0 + dx, y0 + dy, rr[3])
        if seed % 3 == 1:
            cv.rect(6, 6, 25, 25, rr[0]); cv.rect(7, 7, 24, 24, rr[1])
            for y in range(9, 24, 3):
                cv.hline(9, 22, y, rr[0])
    elif kind == 'asphalt':
        cv.img[:] = rgba(rr[1])
        for i in range(30):
            cv.px(rnd.randrange(T), rnd.randrange(T), rr[0] if i % 2 else rr[2])
    elif kind == 'lab':
        cv.img[:] = rgba(rr[2])
        for x0 in (0, 16):
            for y0 in (0, 16):
                cv.hline(x0, x0 + 15, y0, rr[1]); cv.vline(x0, y0, y0 + 15, rr[1])
                cv.px(x0 + 1, y0 + 1, rr[3])
    elif kind == 'carpet':
        cv.img[:] = rgba(rr[1])
        cv.img[((xx + yy) % 8 == 0) | ((xx - yy) % 8 == 0)] = rgba(rr[2])
    elif kind in ('water', 'swamp_water', 'lava', 'ice', 'void'):
        cv.img[:] = rgba(rr[1])
        n = noise_grid(sum(map(ord, str(ramp))) % 997 + 10, T, 8)
        cv.img[n > 0.62] = rgba(rr[2])
        cv.img[n < 0.25] = rgba(rr[0])
        for i in range(5):
            x, y = rnd.randrange(T - 4), rnd.randrange(T)
            cv.hline(x, x + rnd.randint(2, 4), y, rr[3] if kind != 'void' else rr[2])
        if kind == 'void':
            cv.img[:] = rgba((14, 10, 22))
            for i in range(6):
                cv.px(rnd.randrange(T), rnd.randrange(T), R('magic_purple')[0])
    elif kind == 'neon_walk':
        cv.img[:] = rgba(rr[1])
        cv.hline(0, T - 1, 0, R('neon_cyan')[1]); cv.hline(0, T - 1, 15, rr[0]); cv.vline(15, 0, 31, rr[0])
        cv.hline(0, T - 1, 16, rr[2]); cv.vline(16, 0, 31, rr[2])
    elif kind == 'hazard':
        cv.img[:] = rgba(R('tech')[1])
        cv.img[((xx + yy) // 4) % 2 == 0] = rgba(R('warning')[2])
    elif kind == 'red_carpet':
        cv.img[:] = rgba(R('cloth_red')[1])
        cv.img[(yy % 4 == 0)] = rgba(R('cloth_red')[2])
    return cv


def decorate(cv, kind, seed):
    rnd = random.Random(seed * 13 + 1)
    if kind == 'flowers':
        for i in range(4):
            x, y = rnd.randint(3, 28), rnd.randint(3, 28)
            c = R(rnd.choice(['cloth_red', 'cloth_yellow', 'cloth_white', 'cloth_pink', 'cloth_purple']))
            for (dx, dy) in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                cv.px(x + dx, y + dy, c[2])
            cv.px(x, y, R('cloth_yellow')[3])
    elif kind == 'tallgrass':
        for i in range(5):
            x, y = rnd.randint(2, 29), rnd.randint(6, 30)
            g = R('grass')
            for k, dx in enumerate((-1, 0, 1)):
                cv.line(x, y, x + dx * 2, y - 4 - (k % 2), g[2 + (k % 2)])
    elif kind == 'pebbles':
        for i in range(5):
            x, y = rnd.randint(2, 29), rnd.randint(2, 29)
            cv.shade(cv.mask_ellipse(x, y, 1.6, 1.2), 'stone')
    elif kind == 'leaves':
        for i in range(8):
            x, y = rnd.randint(1, 30), rnd.randint(1, 30)
            c = R(rnd.choice(['leaf_autumn', 'leaf']))
            cv.px(x, y, c[2]); cv.px(x + 1, y, c[1])
    elif kind == 'mushrooms':
        for i in range(3):
            x, y = rnd.randint(4, 27), rnd.randint(6, 27)
            cv.rect(x, y, x, y + 2, R('bone')[2])
            cv.shade(cv.mask_ellipse(x + 0.5, y - 0.5, 2.2, 1.4), 'cloth_red')
            cv.px(x - 1, y - 1, R('cloth_white')[3])
    elif kind == 'bones':
        x, y = rnd.randint(6, 22), rnd.randint(8, 24)
        cv.line(x, y, x + 6, y + 2, R('bone')[2]); cv.px(x - 1, y, R('bone')[3]); cv.px(x + 7, y + 2, R('bone')[3])
        cv.shade(cv.mask_ellipse(x + 10, y - 3, 2.5, 2.2), 'bone')
        cv.px(x + 9, y - 3, INK)
    elif kind == 'snowdrift':
        for i in range(3):
            x, y = rnd.randint(4, 27), rnd.randint(4, 27)
            cv.shade(cv.mask_ellipse(x, y, 4, 1.8), 'snow')
    elif kind == 'cracks':
        for i in range(2):
            x, y = rnd.randint(4, 26), rnd.randint(4, 26)
            for k in range(5):
                nx, ny = x + rnd.randint(-2, 2), y + rnd.randint(1, 2)
                cv.line(x, y, nx, ny, R('stone_dark')[0]); x, y = nx, ny
    elif kind == 'moss':
        for i in range(10):
            cv.px(rnd.randrange(32), rnd.randrange(32), R('grass')[rnd.choice([1, 2])])
    elif kind == 'lilypads':
        for i in range(2):
            x, y = rnd.randint(6, 25), rnd.randint(6, 25)
            m = cv.mask_ellipse(x, y, 3.5, 2.5) & ~cv.mask_poly([(x, y), (x + 4, y - 2), (x + 4, y)])
            cv.shade(m, 'leaf')
            if i == 0:
                cv.px(x - 1, y - 1, R('cloth_pink')[3])
    elif kind == 'craters':
        x, y = rnd.randint(8, 23), rnd.randint(8, 23)
        cv.shade(cv.mask_ellipse(x, y, 5, 3), 'stone', light=False)
        cv.fill(cv.mask_ellipse(x + 0.5, y + 0.5, 3.5, 2), 'stone', 0)
    elif kind == 'bolts':
        for (x, y) in [(8, 8), (24, 8), (8, 24), (24, 24)]:
            cv.px(x, y, R('tech_light')[3])
    elif kind == 'puddle':
        cv.fill(cv.mask_ellipse(16, 18, 7, 3), 'water', 1)
        cv.hline(12, 16, 17, R('neon_pink')[2])
    elif kind == 'vent':
        cv.rect(8, 8, 23, 23, R('tech_dark')[0])
        for y in range(10, 23, 3):
            cv.hline(10, 21, y, R('tech')[2])
    elif kind == 'manhole':
        cv.shade(cv.mask_ellipse(16, 16, 9, 7), 'iron')
        cv.img[cv.mask_ellipse(16, 16, 9, 7) & (np.mgrid[0:32, 0:32][0] % 3 == 0)] = rgba(R('iron')[0])
    elif kind == 'lines':
        for x in range(2, 30, 8):
            cv.rect(x, 15, x + 4, 16, R('warning')[3])
    elif kind == 'rubble':
        for i in range(4):
            x, y = rnd.randint(3, 28), rnd.randint(3, 28)
            m = cv.mask_poly([(x, y), (x + 3, y - 1), (x + 4, y + 2), (x + 1, y + 3)])
            cv.shade(m, 'stone')
    return cv


def transition(base_kind, base_ramp, sec_kind, sec_ramp, corners, seed, edge='shadow'):
    """Corner-matched tile. corners = (tl, tr, bl, br) with 1 = secondary."""
    b = surface(base_kind, base_ramp, seed)
    s = surface(sec_kind, sec_ramp, seed + 100)
    tl, tr, bl, br = corners

    def mask_at(P):
        yy, xx = np.mgrid[-P:T + P, -P:T + P]
        u, v = np.clip((xx + 0.5) / T, 0, 1), np.clip((yy + 0.5) / T, 0, 1)
        val = tl * (1 - u) * (1 - v) + tr * u * (1 - v) + bl * (1 - u) * v + br * u * v
        # periodic wobble -> identical on shared tile edges
        wob = (np.sin(2 * np.pi * xx / 16) * np.cos(2 * np.pi * yy / 16) * 0.07
               + np.sin(2 * np.pi * (xx + yy) / 32) * 0.05)
        return (val + wob) > 0.5
    P = 2
    mp = mask_at(P)
    inner_p = mp & (~_shift(mp, -1, 0) | ~_shift(mp, 1, 0) | ~_shift(mp, 0, -1) | ~_shift(mp, 0, 1))
    outer_p = ~mp & (_shift(mp, -1, 0) | _shift(mp, 1, 0) | _shift(mp, 0, -1) | _shift(mp, 0, 1))
    m, inner, outer = mp[P:-P, P:-P], inner_p[P:-P, P:-P], outer_p[P:-P, P:-P]
    out = b.copy()
    out.img[m] = s.img[m]
    sr, br_ = R(sec_ramp), R(base_ramp)
    if edge == 'shadow':   # secondary is lower (water, path dug in)
        out.img[inner] = rgba(sr[0])
        out.img[outer] = rgba(br_[3] if sec_kind in ('water', 'swamp_water', 'lava', 'ice', 'void') else br_[0])
        if sec_kind in ('water', 'swamp_water', 'lava'):
            foam = m & _shift(inner, -1, 0) & ~inner
            out.img[foam] = rgba(sr[3])
    else:
        out.img[inner] = rgba(sr[2])
        out.img[outer] = rgba(br_[0])
    return out


def obstacle(kind, seed):
    cv = Canvas(T)
    rnd = random.Random(seed)
    if kind == 'rock':
        m = cv.mask_ellipse(16, 18, 11, 9)
        cv.shade(m, 'stone', depth=2)
        cv.line(10, 14, 15, 18, R('stone')[0])
    elif kind == 'bush':
        for (x, y, r) in [(11, 18, 7), (21, 18, 7), (16, 13, 7)]:
            cv.shade(cv.mask_ellipse(x, y, r, r - 1), 'leaf')
        for i in range(3):
            cv.px(rnd.randint(9, 23), rnd.randint(11, 20), R('cloth_red')[2])
    elif kind == 'fence':
        for x in (4, 26):
            cv.rect(x, 8, x + 2, 28, R('wood')[1]); cv.px(x, 8, R('wood')[3])
        cv.rect(0, 13, 31, 15, R('wood')[2]); cv.rect(0, 21, 31, 23, R('wood')[2])
        cv.hline(0, 31, 15, R('wood')[0]); cv.hline(0, 31, 23, R('wood')[0])
    elif kind == 'stump':
        m = cv.mask_rect(9, 14, 22, 26) | cv.mask_ellipse(15.5, 26, 7, 2.5)
        cv.shade_cyl(m, 'wood')
        cv.fill(cv.mask_ellipse(15.5, 14, 6.5, 3), 'wood_light', 2)
        cv.img[cv.mask_ellipse(15.5, 14, 3.5, 1.5) & ~cv.mask_ellipse(15.5, 14, 2.5, 0.8)] = rgba(R('wood_light')[1])
    elif kind == 'log':
        m = cv.mask_rect(3, 14, 28, 23)
        cv.shade(m, 'wood')
        cv.fill(cv.mask_ellipse(28, 18.5, 2.5, 4.5), 'wood_light', 2)
        cv.img[m & (np.mgrid[0:32, 0:32][0] % 3 == 0)] = rgba(R('wood')[0])
    elif kind == 'cactus':
        cv.shade_cyl(cv.mask_rect(13, 4, 18, 28), 'grass')
        cv.shade_cyl(cv.mask_rect(6, 10, 9, 18), 'grass'); cv.rect(8, 17, 13, 19, R('grass')[1])
        cv.shade_cyl(cv.mask_rect(22, 8, 25, 15), 'grass'); cv.rect(18, 14, 23, 16, R('grass')[1])
    elif kind == 'boulder_sand':
        m = cv.mask_ellipse(16, 19, 12, 9)
        cv.shade(m, 'sandstone', depth=2)
        cv.hline(8, 22, 18, R('sandstone')[1])
    elif kind == 'reeds':
        for i in range(7):
            x = 6 + i * 3
            hgt = rnd.randint(14, 22)
            cv.line(x, 28, x + rnd.randint(-2, 2), 28 - hgt, R('grass_dry')[2])
            if i % 2:
                cv.rect(x - 1 + 0, 28 - hgt, x, 28 - hgt + 3, R('wood')[1])
    elif kind == 'ice_block':
        cv.shade(cv.mask_poly([(6, 10), (26, 8), (28, 26), (4, 27)]), 'ice', depth=2)
        cv.line(10, 12, 14, 20, R('ice')[3])
    elif kind == 'snow_rock':
        m = cv.mask_ellipse(16, 18, 11, 9)
        cv.shade(m, 'stone', depth=2)
        cv.fill(cv.mask_ellipse(15, 13, 9, 4) & m, 'snow', 3)
    elif kind == 'wall_stone':
        cv.img[:] = rgba(R('stone_dark')[0])
        for y0 in range(0, T, 8):
            off = 8 if (y0 // 8) % 2 else 0
            for x0 in range(-off, T, 16):
                cv.shade(cv.mask_rect(x0 + 1, y0 + 1, x0 + 15, y0 + 7), 'stone_dark')
    elif kind == 'wall_castle':
        cv.img[:] = rgba(R('stone')[0])
        for y0 in range(0, T, 8):
            off = 8 if (y0 // 8) % 2 else 0
            for x0 in range(-off, T, 16):
                cv.shade(cv.mask_rect(x0 + 1, y0 + 1, x0 + 15, y0 + 7), 'stone')
    elif kind == 'pillar_broken':
        cv.shade_cyl(cv.mask_rect(9, 10, 22, 28), 'stone_warm')
        cv.fill(cv.mask_poly([(9, 10), (22, 10), (22, 6), (18, 9), (14, 4), (9, 8)]), 'stone_warm', 2)
        cv.img[cv.mask_rect(9, 10, 22, 28) & (np.mgrid[0:32, 0:32][1] % 4 == 1)] = rgba(R('stone_warm')[1])
        cv.px(12, 20, R('grass')[2]); cv.px(13, 21, R('grass')[1]); cv.px(20, 24, R('grass')[2])
    elif kind == 'pit':
        cv.img[:] = rgba((14, 10, 22))
        cv.hline(0, 31, 0, R('stone_dark')[2]); cv.hline(0, 31, 1, R('stone_dark')[1])
    elif kind == 'crate_tech':
        return F.crate('tech')()
    elif kind == 'barrel':
        return F.barrel('wood')()
    elif kind == 'barrier':
        cv.rect(2, 12, 29, 20, R('warning')[2])
        for x in range(2, 30, 6):
            cv.rect(x, 12, x + 2, 20, R('cloth_black')[2])
        cv.rect(4, 20, 6, 28, R('tech')[1]); cv.rect(25, 20, 27, 28, R('tech')[1])
    elif kind == 'pipe':
        cv.shade_cyl(cv.mask_rect(0, 12, 31, 19), 'tech_light', axis='y')
        for x in (6, 22):
            cv.rect(x, 10, x + 2, 21, R('tech')[1])
    elif kind == 'hydrant':
        cv.shade_cyl(cv.mask_rect(12, 10, 19, 27), 'cloth_red')
        cv.fill(cv.mask_ellipse(15.5, 10, 4.5, 2.5), 'cloth_red', 2)
        cv.rect(9, 16, 22, 18, R('cloth_red')[1])
    elif kind == 'bollard':
        cv.shade_cyl(cv.mask_rect(12, 8, 19, 27), 'tech')
        cv.rect(12, 11, 19, 12, R('neon_cyan')[3])
    elif kind == 'solar':
        cv.shade(cv.mask_poly([(4, 8), (28, 8), (30, 20), (2, 20)]), 'glass')
        yy, xx = np.mgrid[0:32, 0:32]
        cv.img[cv.mask_poly([(4, 8), (28, 8), (30, 20), (2, 20)]) & ((xx % 6 == 0) | (yy == 14))] = rgba(R('tech')[2])
        cv.rect(15, 21, 16, 28, R('tech')[1])
    elif kind == 'moon_rock':
        m = cv.mask_ellipse(16, 19, 11, 8)
        cv.shade(m, 'stone_warm', depth=2)
        cv.fill(cv.mask_ellipse(12, 17, 2, 1.4), 'stone_warm', 0)
    elif kind == 'bones_pile':
        decorate(cv, 'bones', seed); decorate(cv, 'bones', seed + 3)
        cv.img[cv.img[:, :, 3] == 0] = 0
    if kind not in ('wall_stone', 'wall_castle', 'pit'):
        a = cv.alpha
        o = ~a & (_shift(a, -1, 0) | _shift(a, 1, 0) | _shift(a, 0, -1) | _shift(a, 0, 1))
        cv.img[o] = rgba(OUTLINE)
    return cv


BIOMES = [
    # id, name, (base kind, ramp, label), (secondary kind, ramp, label, edge), decorations, obstacles
    ('village', 'Medieval Village', ('grass', 'grass', 'Grass'), ('cobble', 'cobble', 'Cobblestone', 'raise'), ['flowers', 'tallgrass', 'flowers', 'pebbles'], ['bush', 'fence', 'rock', 'barrel']),
    ('forest', 'Forest', ('grass', 'leaf', 'Forest Floor'), ('dirt', 'dirt', 'Dirt Path', 'shadow'), ['leaves', 'mushrooms', 'tallgrass', 'leaves'], ['stump', 'log', 'bush', 'rock']),
    ('desert', 'Desert', ('sand', 'sand', 'Sand'), ('sand', 'sandstone', 'Hardpan', 'raise'), ['pebbles', 'bones', 'pebbles', 'cracks'], ['cactus', 'boulder_sand', 'bones_pile', 'boulder_sand']),
    ('swamp', 'Swamp', ('swamp', 'swamp', 'Bog'), ('swamp_water', 'swamp_water', 'Murky Water', 'shadow'), ['mushrooms', 'moss', 'tallgrass', 'moss'], ['reeds', 'log', 'stump', 'reeds']),
    ('snow', 'Snow Biome', ('snow', 'snow', 'Snow'), ('ice', 'ice', 'Frozen Lake', 'shadow'), ['snowdrift', 'pebbles', 'snowdrift', 'snowdrift'], ['snow_rock', 'ice_block', 'snow_rock', 'ice_block']),
    ('dungeon', 'Dungeon', ('dungeon', 'stone_dark', 'Dungeon Floor'), ('void', 'shadow', 'Abyss', 'shadow'), ['cracks', 'bones', 'moss', 'rubble'], ['wall_stone', 'bones_pile', 'pit', 'barrel']),
    ('castle', 'Castle', ('flagstone', 'stone', 'Flagstone'), ('red_carpet', 'cloth_red', 'Royal Carpet', 'raise'), ['cracks', 'pebbles', 'cracks', 'moss'], ['wall_castle', 'barrel', 'rock', 'wall_castle']),
    ('ruins', 'Ancient Ruins', ('grass', 'grass_dry', 'Wild Grass'), ('flagstone', 'stone_warm', 'Ruined Tiles', 'raise'), ['rubble', 'moss', 'tallgrass', 'rubble'], ['pillar_broken', 'rock', 'bush', 'pillar_broken']),
    ('space_colony', 'Space Colony', ('regolith', 'stone_warm', 'Regolith'), ('metal', 'tech', 'Hab Plating', 'raise'), ['craters', 'pebbles', 'craters', 'bolts'], ['moon_rock', 'solar', 'crate_tech', 'moon_rock']),
    ('research_lab', 'Research Lab', ('lab', 'tech_light', 'Lab Tile'), ('hazard', 'warning', 'Hazard Zone', 'raise'), ['vent', 'bolts', 'cracks', 'vent'], ['barrier', 'pipe', 'crate_tech', 'barrier']),
    ('cyber_city', 'Cyber City', ('asphalt', 'stone_dark', 'Asphalt'), ('neon_walk', 'tech', 'Neon Sidewalk', 'raise'), ['puddle', 'manhole', 'lines', 'cracks'], ['hydrant', 'bollard', 'barrier', 'barrel']),
]

CORNERS = [((i >> 3) & 1, (i >> 2) & 1, (i >> 1) & 1, i & 1) for i in range(16)]


def build_tileset(biome):
    bid, name, (bk, br, bl), (sk, sr, sl, edge), decos, obst = biome
    atlas = Canvas(8 * T, 4 * T)
    seed0 = sum(map(ord, bid))
    for i in range(4):
        atlas.paste(surface(bk, br, seed0 + i), i * T, 0)
        t = surface(bk, br, seed0 + i)
        decorate(t, decos[i], seed0 + i)
        atlas.paste(t, (4 + i) * T, 0)
    for idx, c in enumerate(CORNERS):
        if sum(c) == 0:
            tile = surface(bk, br, seed0)
        elif sum(c) == 4:
            tile = surface(sk, sr, seed0 + 100)
        else:
            tile = transition(bk, br, sk, sr, c, seed0, edge)
        atlas.paste(tile, (idx % 8) * T, (1 + idx // 8) * T)
    for i in range(4):
        atlas.paste(surface(sk, sr, seed0 + 100 + i * 7), i * T, 3 * T)
        ob = Canvas(T)
        ob.paste(surface(bk, br, seed0 + i)) if obst[i] not in ('wall_stone', 'wall_castle', 'pit') else None
        ob.paste(obstacle(obst[i], seed0 + i))
        atlas.paste(ob, (4 + i) * T, 3 * T)
    return atlas


# ------------------------------------------------------------------ biome props
def tree(kind, seed=0):
    def fn():
        if kind in ('oak', 'autumn', 'big', 'dead', 'palm', 'willow', 'cherry'):
            w, h = 64, 64
        else:
            w, h = 32, 64
        cv = Canvas(w, h)
        rnd = random.Random(seed)
        cx = w / 2
        if kind == 'palm':
            trunk = Canvas(w, h)
            for i in range(30):
                x = cx - 4 + math.sin(i / 10) * 4
                trunk.rect(x, 60 - i * 1.5, x + 3, 61 - i * 1.5, R('wood_light')[2 if i % 3 else 1])
            cv.paste(trunk)
            for a in (-150, -110, -70, -30, 10, 200):
                r = math.radians(a)
                leaf = Canvas(w, h)
                ex, ey = cx + math.cos(r) * 20, 16 + math.sin(r) * 8 + 8
                leaf.line(cx, 16, ex, ey, R('leaf')[2], width=3)
                leaf.line(cx, 17, ex, ey + 2, R('leaf')[1], width=2)
                cv.paste(leaf)
            for (x, y) in [(cx - 3, 18), (cx + 1, 19)]:
                cv.shade(cv.mask_ellipse(x, y, 2, 2), 'wood')
        elif kind == 'dead':
            br = Canvas(w, h)
            br.line(cx, 62, cx, 22, R('wood_dark')[1], width=4)
            for (a, b, c, d) in [(cx, 34, cx - 14, 20), (cx, 30, cx + 15, 14), (cx - 8, 26, cx - 12, 10), (cx + 6, 22, cx + 4, 6), (cx + 10, 18, cx + 20, 18)]:
                br.line(a, b, c, d, R('wood_dark')[2], width=2)
            cv.paste(br)
            cv.fill(cv.mask_rect(cx - 2, 26, cx + 1, 62), 'wood_dark', 1)
        elif kind in ('pine', 'snowpine'):
            cv.rect(cx - 2, 50, cx + 1, 62, R('wood')[1]); cv.vline(cx + 1, 50, 62, R('wood')[0])
            for i, (y, r) in enumerate([(46, 14), (36, 12), (26, 9), (16, 6)]):
                m = cv.mask_poly([(cx - r, y + 6), (cx + r, y + 6), (cx, y - 10)])
                cv.shade(m, 'pine', depth=2)
                if kind == 'snowpine':
                    cv.fill(m & cv.mask_poly([(cx - r + 3, y + 1), (cx + r - 5, y), (cx, y - 10)]), 'snow', 3)
        elif kind == 'mushroom_giant':
            cv.shade_cyl(cv.mask_rect(cx - 3, 30, cx + 2, 62), 'bone')
            cap = cv.mask_ellipse(cx, 26, 15, 11) & (np.mgrid[0:h, 0:w][0] < 32)
            cv.shade(cap, 'cloth_red', depth=2)
            for (x, y) in [(cx - 7, 21), (cx + 4, 19), (cx - 1, 27), (cx + 9, 26)]:
                cv.shade(cv.mask_ellipse(x, y, 2, 1.6), 'cloth_white')
        elif kind == 'crystal':
            for (x, hgt, wd) in [(cx - 6, 34, 5), (cx + 5, 26, 4), (cx, 48, 6)]:
                m = cv.mask_poly([(x - wd, 62), (x + wd, 62), (x + wd, 62 - hgt + 8), (x, 62 - hgt), (x - wd, 62 - hgt + 8)])
                cv.shade(m, 'crystal', depth=2)
                cv.line(x - 1, 62 - hgt + 3, x - 1, 60, R('crystal')[3])
        elif kind == 'cyber_tree':
            cv.shade_cyl(cv.mask_rect(cx - 2, 20, cx + 1, 62), 'tech')
            for i, y in enumerate(range(10, 44, 8)):
                cv.fill(cv.mask_ellipse(cx, y, 10 - i, 3), 'neon_pink' if i % 2 else 'neon_cyan', 2)
                cv.hline(cx - 6 + i, cx + 5 - i, y, R('neon_pink' if i % 2 else 'neon_cyan')[3])
        elif kind == 'antenna':
            cv.line(cx - 8, 62, cx, 10, R('tech')[2]); cv.line(cx + 8, 62, cx, 10, R('tech')[2])
            for y in range(20, 60, 8):
                cv.hline(cx - (y - 10) / 6.5, cx + (y - 10) / 6.5, y, R('tech')[1])
            dish = cv.mask_ellipse(cx, 12, 9, 4)
            cv.shade(dish, 'tech_light')
            cv.px(cx, 4, R('ruby')[3]); cv.vline(cx, 5, 10, R('tech')[2])
        else:
            pal = {'oak': 'leaf', 'autumn': 'leaf_autumn', 'big': 'leaf', 'willow': 'grass', 'cherry': 'cloth_pink'}[kind]
            trunk = cv.mask_poly([(cx - 5, 62), (cx + 5, 62), (cx + 3, 34), (cx - 3, 34)])
            cv.shade_cyl(trunk, 'wood')
            cv.px(cx - 6, 62, R('wood')[1]); cv.px(cx + 5, 62, R('wood')[0])
            blobs = [(cx, 22, 18, 15), (cx - 10, 30, 10, 9), (cx + 11, 30, 10, 9), (cx - 6, 14, 10, 9), (cx + 7, 13, 10, 9)]
            canopy = cv.empty_mask()
            for (x, y, rx, ry) in blobs:
                canopy |= cv.mask_ellipse(x, y, rx, ry)
            cv.shade(canopy, pal, depth=2)
            # leaf clusters texture
            for (x, y, rx, ry) in blobs:
                hl = cv.mask_ellipse(x - rx * 0.3, y - ry * 0.35, rx * 0.45, ry * 0.35) & canopy
                cv.img[hl] = rgba(R(pal)[2])
            for i in range(26):
                x, y = rnd.randint(int(cx - 22), int(cx + 22)), rnd.randint(6, 40)
                if canopy[y, x]:
                    cv.px(x, y, R(pal)[3 if y < 22 else 0])
            if kind == 'willow':
                for x in range(int(cx - 22), int(cx + 22), 3):
                    cv.line(x, 30, x + 1, 46 + (x % 5), R('grass')[1])
            if kind == 'oak':
                for (x, y) in [(cx - 9, 25), (cx + 8, 20), (cx + 2, 32)]:
                    cv.shade(cv.mask_ellipse(x, y, 1.6, 1.6), 'cloth_red')
        a = cv.alpha
        o = ~a & (_shift(a, -1, 0) | _shift(a, 1, 0) | _shift(a, 0, -1) | _shift(a, 0, 1))
        cv.img[o] = rgba(OUTLINE)
        # ground shadow
        sh = cv.mask_ellipse(cx, h - 2, w * 0.3 if w > 32 else 9, 2.2) & ~cv.alpha
        cv.img[sh] = (20, 16, 30, 90)
        return cv
    return fn


BIOME_PROPS = [
    ('tree_oak', 'village', 'Oak Tree', (64, 64), tree('oak', 1)),
    ('tree_cherry', 'village', 'Cherry Blossom', (64, 64), tree('cherry', 2)),
    ('well', 'village', 'Village Well', (32, 32), F.prop('well')),
    ('lamp_post', 'village', 'Street Lamp', (32, 64), F.prop('lamp_post')),
    ('tree_big', 'forest', 'Ancient Tree', (64, 64), tree('big', 3)),
    ('tree_autumn', 'forest', 'Autumn Tree', (64, 64), tree('autumn', 4)),
    ('tree_pine', 'forest', 'Pine Tree', (32, 64), tree('pine', 5)),
    ('mushroom_giant', 'forest', 'Giant Mushroom', (32, 64), tree('mushroom_giant', 6)),
    ('tree_palm', 'desert', 'Palm Tree', (64, 64), tree('palm', 7)),
    ('tree_dead', 'swamp', 'Dead Tree', (64, 64), tree('dead', 8)),
    ('tree_willow', 'swamp', 'Swamp Willow', (64, 64), tree('willow', 9)),
    ('tree_snowpine', 'snow', 'Snowy Pine', (32, 64), tree('snowpine', 10)),
    ('crystal_cluster', 'dungeon', 'Crystal Cluster', (32, 64), tree('crystal', 11)),
    ('statue_ruin', 'ruins', 'Weathered Statue', (32, 64), F.prop('statue')),
    ('pillar_ruin', 'ruins', 'Ancient Pillar', (32, 64), F.prop('pillar')),
    ('antenna', 'space_colony', 'Comms Antenna', (32, 64), tree('antenna', 12)),
    ('specimen_tank', 'research_lab', 'Specimen Tank', (32, 64), F.prop('specimen_tank')),
    ('cyber_tree', 'cyber_city', 'Holo Tree', (32, 64), tree('cyber_tree', 13)),
    ('vending_machine', 'cyber_city', 'Vending Machine', (32, 64), F.prop('vending')),
    ('fountain', 'castle', 'Courtyard Fountain', (64, 64), F.prop('fountain')),
]
