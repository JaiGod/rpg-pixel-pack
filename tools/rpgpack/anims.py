"""Environmental animations: horizontal strips of frames."""
import math
import random
import numpy as np

from .core import Canvas, R, rgba, _shift
from .palette import OUTLINE, INK
from .environments import noise_grid
from . import furniture as F

T = 32


def _ol(cv):
    a = cv.img[:, :, 3] == 255
    o = (cv.img[:, :, 3] == 0) & (_shift(a, -1, 0) | _shift(a, 1, 0) | _shift(a, 0, -1) | _shift(a, 0, 1))
    cv.img[o] = rgba(OUTLINE)
    return cv


def liquid(ramp, n=4, kind='water'):
    frames = []
    base = noise_grid(sum(map(ord, ramp)) % 97 + 10, T, 8)
    for f in range(n):
        cv = Canvas(T)
        rr = R(ramp)
        cv.img[:] = rgba(rr[1])
        sh = np.roll(base, f * 8, axis=1)
        cv.img[sh > 0.62] = rgba(rr[2])
        cv.img[sh < 0.28] = rgba(rr[0])
        yy, xx = np.mgrid[0:T, 0:T]
        waves = (np.sin((xx + f * 8) * 2 * np.pi / 32 * 2 + yy * 0.8) > 0.93) & (yy % 8 == (f * 2) % 8)
        cv.img[waves] = rgba(rr[3])
        if kind == 'lava':
            rnd = random.Random(f)
            for i in range(2):
                x, y = (7 + f * 6 + i * 13) % 28 + 2, (5 + i * 17) % 28 + 2
                r = [1, 2, 2.5, 1][f]
                cv.shade(cv.mask_ellipse(x, y, r, r), 'fire', base=2)
        frames.append(cv)
    return frames


def waterfall(n=4):
    frames = []
    for f in range(n):
        cv = Canvas(T, 2 * T)
        yy, xx = np.mgrid[0:2 * T, 0:T]
        rr = R('water')
        cv.img[:] = rgba(rr[1])
        cv.img[((yy - f * 8) % 12 < 3) & ((xx * 7) % 5 < 2)] = rgba(rr[3])
        cv.img[((yy - f * 8 + 6) % 12 < 2) & ((xx * 3) % 7 < 3)] = rgba(rr[2])
        cv.img[xx < 2] = rgba(rr[0]); cv.img[xx > T - 3] = rgba(rr[0])
        foam = yy > 2 * T - 8
        cv.img[foam] = rgba(R('cloth_white')[2])
        cv.img[foam & (((xx + f * 3) % 5) < 2)] = rgba(R('cloth_white')[3])
        frames.append(cv)
    return frames


def flame_shape(cv, cx, by, w, h, f, ramp='fire'):
    rnd = random.Random(f * 3 + int(cx))
    flick = [0, 1, -1, 1, 0, -1][f % 6]
    pts = [(cx - w, by), (cx - w * 0.6, by - h * 0.45 + flick), (cx - w * 0.2, by - h * 0.7), (cx + flick * 0.5, by - h),
           (cx + w * 0.3, by - h * 0.65 - flick), (cx + w * 0.7, by - h * 0.5), (cx + w, by)]
    m = cv.mask_poly(pts) | cv.mask_ellipse(cx, by - h * 0.15, w, h * 0.25)
    cv.fill(m, ramp, 1)
    inner = cv.mask_poly([(cx - w * 0.55, by), (cx - w * 0.2, by - h * 0.5), (cx + flick * 0.3, by - h * 0.7), (cx + w * 0.4, by - h * 0.4), (cx + w * 0.55, by)])
    cv.fill(inner, ramp, 2)
    core = cv.mask_ellipse(cx, by - h * 0.2, w * 0.35, h * 0.22)
    cv.fill(core, ramp, 3)
    # embers
    for i in range(2):
        ex = cx + rnd.randint(-int(w), int(w))
        ey = by - h - 2 - ((f * 3 + i * 5) % 6)
        cv.px(ex, ey, R(ramp)[3 if i else 2])
    return m


def campfire(n=6):
    frames = []
    for f in range(n):
        cv = Canvas(T)
        for (a, b) in [((6, 27), (24, 22)), ((8, 22), (26, 27))]:
            cv.line(a[0], a[1], b[0], b[1], R('wood')[1], width=3)
        for (x, y) in [(5, 27), (27, 27), (16, 29), (9, 29), (23, 29)]:
            cv.shade(cv.mask_ellipse(x, y, 2.5, 1.6), 'stone')
        flame_shape(cv, 16, 25, 7, 18, f)
        frames.append(_ol(cv))
    return frames


def torch(n=4, wall=True):
    frames = []
    for f in range(n):
        cv = Canvas(T)
        if wall:
            cv.rect(14, 18, 17, 28, R('wood')[1]); cv.vline(17, 18, 28, R('wood')[0])
            cv.rect(12, 16, 19, 18, R('iron')[2])
            cv.rect(11, 22, 20, 23, R('iron')[1])
        else:
            cv.rect(15, 16, 16, 30, R('iron')[1])
            cv.shade(cv.mask_poly([(10, 12), (21, 12), (19, 17), (12, 17)]), 'iron')
        flame_shape(cv, 15.5, 16 if wall else 13, 4, 12, f)
        glow = cv.mask_ellipse(15.5, 10, 10 + (f % 2), 10 + (f % 2)) & ~cv.alpha
        cv.img[glow] = (252, 200, 90, 40)
        frames.append(_ol(cv))
    return frames


def brazier(n=4):
    frames = []
    for f in range(n):
        cv = Canvas(T, 2 * T)
        cv.shade(cv.mask_poly([(6, 30), (25, 30), (21, 40), (10, 40)]), 'iron')
        cv.rect(14, 40, 17, 58, R('iron')[1])
        cv.rect(8, 58, 23, 61, R('iron')[0])
        flame_shape(cv, 15.5, 30, 9, 22, f, 'magic_blue' if False else 'fire')
        frames.append(_ol(cv))
    return frames


def door_anim(kind, n=4):
    frames = []
    for f in range(n):
        if kind == 'wood':
            cv = Canvas(T, 2 * T)
            frame = cv.mask_rect(2, 6, 29, 63)
            cv.fill(frame, 'stone', 1)
            cv.fill(cv.mask_rect(5, 10, 26, 63), 'stone_dark', 0)
            open_w = [22, 15, 8, 3][f]
            dm = cv.mask_rect(5, 10, 5 + open_w - 1, 63)
            cv.fill(dm, 'wood', 1)
            yy, xx = np.mgrid[0:2 * T, 0:T]
            cv.img[dm & ((xx - 5) % 4 == 0)] = rgba(R('wood')[0])
            cv.img[dm & ((yy == 18) | (yy == 52))] = rgba(R('iron')[1])
            if open_w > 6:
                cv.px(5 + open_w - 3, 37, R('gold')[3])
        elif kind == 'gate':
            cv = Canvas(2 * T, 2 * T)
            cv.fill(cv.mask_rect(0, 0, 63, 63), 'stone', 1)
            cv.fill(cv.mask_rect(8, 8, 55, 63) | cv.mask_ellipse(31.5, 10, 24, 8), 'stone_dark', 0)
            lift = [0, 14, 30, 48][f]
            yy, xx = np.mgrid[0:2 * T, 0:2 * T]
            port = (cv.mask_rect(8, 4, 55, 63 - lift)) & ((xx % 6 == 0) | (yy % 7 == 0)) & (cv.mask_rect(8, 8, 55, 63) | cv.mask_ellipse(31.5, 10, 24, 8))
            cv.img[port] = rgba(R('iron')[1])
            cv.img[port & (xx % 6 == 0) & (yy == 63 - lift)] = rgba(R('iron')[3])
        else:  # sliding sci-fi door
            cv = Canvas(T, 2 * T)
            cv.fill(cv.mask_rect(1, 4, 30, 63), 'tech', 1)
            cv.fill(cv.mask_rect(4, 8, 27, 63), 'tech_dark', 0)
            gap = [0, 4, 8, 11][f]
            for (x0, x1) in ((4, 15 - gap), (16 + gap, 27)):
                if x1 >= x0:
                    m = cv.mask_rect(x0, 8, x1, 63)
                    cv.shade(m, 'tech_light')
                    cv.img[m & (np.mgrid[0:2 * T, 0:T][0] == 30)] = rgba(R('warning')[2])
            cv.hline(4, 27, 6, R('neon_green' if f == 3 else 'ruby')[3])
        frames.append(_ol(cv))
    return frames


def portal(kind, n=8):
    frames = []
    ramp = 'magic_purple' if kind == 'magic' else 'neon_cyan'
    for f in range(n):
        cv = Canvas(2 * T, 2 * T)
        yy, xx = np.mgrid[0:2 * T, 0:2 * T]
        if kind == 'magic':
            for (x, y) in [(10, 52), (53, 52)]:
                cv.shade(cv.mask_rect(x - 4, 14, x + 3, 58), 'stone')
            cv.shade(cv.mask_rect(4, 56, 59, 61), 'stone')
            arch = cv.mask_ellipse(31.5, 34, 22, 26) & ~cv.mask_ellipse(31.5, 34, 18, 22)
            cv.shade(arch, 'stone', depth=2)
            for i in range(5):
                a = math.radians(-160 + i * 35)
                cv.px(31.5 + math.cos(a) * 20, 34 + math.sin(a) * 24, R('magic_purple')[3 if (f + i) % 2 else 2])
        else:
            ring = cv.mask_ellipse(31.5, 32, 26, 26) & ~cv.mask_ellipse(31.5, 32, 21, 21)
            cv.shade(ring, 'tech_light', depth=2)
            for i in range(8):
                a = math.radians(i * 45 + f * 11.25)
                cv.rect(31.5 + math.cos(a) * 23.5 - 1, 32 + math.sin(a) * 23.5 - 1, 31.5 + math.cos(a) * 23.5, 32 + math.sin(a) * 23.5, R('neon_cyan')[3])
        inner = cv.mask_ellipse(31.5, 34 if kind == 'magic' else 32, 18 if kind == 'magic' else 21, 22 if kind == 'magic' else 21)
        ang = np.arctan2(yy - 32, xx - 31.5)
        rad = np.hypot(xx - 31.5, yy - 32)
        swirl = np.sin(ang * 3 + rad * 0.35 - f * (2 * math.pi / n))
        rr = R(ramp)
        lvl = np.where(swirl > 0.5, 3, np.where(swirl > -0.1, 2, np.where(swirl > -0.6, 1, 0)))
        for i in range(4):
            cv.img[inner & (lvl == i)] = rgba(rr[i])
        cv.img[inner & (rad < 4)] = rgba((255, 255, 255))
        frames.append(_ol(cv))
    return frames


def chest_open(n=4):
    frames = []
    for f in range(n):
        cv = Canvas(T)
        F.block(cv, 5, 15, 26, 27, 2, 'wood')
        cv.rect(14, 17, 17, 20, R('gold')[2])
        lid_h = [7, 5, 2, 0][f]
        if f > 0:
            cv.fill(cv.mask_rect(6, 15, 25, 16), 'wood_dark', 0)
            for x in range(8, 24, 3):
                cv.px(x, 15, R('gold')[3 if (x + f) % 2 else 2])
        if lid_h:
            F.block(cv, 5, 15 - lid_h - (2 if f else 0), 26, 15 - (2 if f else 0) + (0 if f else 0), max(1, lid_h - 2), 'wood')
        if f >= 2:
            for i in range(3):
                cv.px(10 + i * 6, 10 - f * 2 + i, R('gold')[3])
        frames.append(_ol(cv))
    return frames


def crystal(n=4):
    frames = []
    for f in range(n):
        cv = Canvas(T)
        for (x, hgt, wd) in [(10, 16, 4), (21, 13, 3), (16, 24, 5)]:
            m = cv.mask_poly([(x - wd, 30), (x + wd, 30), (x + wd, 30 - hgt + 5), (x, 30 - hgt), (x - wd, 30 - hgt + 5)])
            cv.shade(m, 'crystal', depth=2, base=1 + (1 if f == 2 else 0))
        sp = [(9, 10), (22, 12), (16, 4), (13, 18)][f]
        for (dx, dy) in [(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)]:
            cv.px(sp[0] + dx, sp[1] + dy, R('crystal')[3])
        frames.append(_ol(cv))
    return frames


def flag(n=4, ramp='cloth_red'):
    frames = []
    for f in range(n):
        cv = Canvas(T, 2 * T)
        cv.rect(6, 4, 7, 62, R('wood')[1]); cv.px(6, 3, R('gold')[3]); cv.px(7, 3, R('gold')[2])
        yy, xx = np.mgrid[0:2 * T, 0:T]
        wave = np.sin(xx * 0.45 - f * math.pi / 2) * 2
        m = (xx >= 8) & (xx <= 28) & (yy >= 6 + wave) & (yy <= 20 + wave)
        cv.fill(m, ramp, 1)
        cv.img[m & (np.sin(xx * 0.45 - f * math.pi / 2 + 1.2) > 0.4)] = rgba(R(ramp)[2])
        cv.img[m & (np.sin(xx * 0.45 - f * math.pi / 2 + 1.2) < -0.6)] = rgba(R(ramp)[0])
        frames.append(_ol(cv))
    return frames


def coin(n=6):
    frames = []
    widths = [5, 4, 2, 1, 2, 4]
    for f in range(n):
        cv = Canvas(T)
        w = widths[f]
        m = cv.mask_ellipse(15.5, 16, w + 0.5, 6)
        cv.shade(m, 'gold')
        if w >= 4:
            cv.vline(15, 13, 18, R('gold')[1])
        frames.append(_ol(cv))
    return frames


def smoke(n=6):
    frames = []
    for f in range(n):
        cv = Canvas(T)
        for i in range(3):
            r = 2 + f * 0.8 + i * 0.5
            cy = 26 - f * 3 - i * 3
            a = max(40, 200 - f * 30)
            m = cv.mask_ellipse(12 + i * 4 + (f % 2), cy, r, r * 0.85)
            cv.img[m] = (210, 210, 222, a)
            cv.img[m & cv.mask_ellipse(11 + i * 4, cy - 1, r * 0.6, r * 0.5)] = (240, 240, 248, a)
        frames.append(cv)
    return frames


def windmill(n=4):
    frames = []
    for f in range(n):
        cv = Canvas(2 * T, 3 * T)
        body = cv.mask_poly([(18, 92), (45, 92), (40, 34), (23, 34)])
        cv.shade(body, 'plaster', depth=2)
        roofm = cv.mask_poly([(18, 36), (45, 36), (31.5, 18)])
        cv.shade(roofm, 'roof_red')
        cv.fill(cv.mask_rect(28, 78, 35, 92), 'wood_dark', 1)
        cx, cy = 31.5, 34
        for k in range(4):
            a = math.radians(k * 90 + f * 22.5)
            bl = Canvas(2 * T, 3 * T)
            bl.line(cx, cy, cx + math.cos(a) * 28, cy + math.sin(a) * 28, R('wood')[1], width=2)
            pa = a + math.radians(12)
            sail = bl.mask_poly([(cx + math.cos(a) * 8, cy + math.sin(a) * 8), (cx + math.cos(a) * 27, cy + math.sin(a) * 27),
                                 (cx + math.cos(pa) * 26, cy + math.sin(pa) * 26), (cx + math.cos(pa) * 9, cy + math.sin(pa) * 9)])
            bl.fill(sail, 'cloth_white', 2)
            cv.paste(bl)
        cv.shade(cv.mask_ellipse(cx, cy, 2.5, 2.5), 'wood')
        frames.append(_ol(cv))
    return frames


ANIMATIONS = [
    # id, category, name, fps, loop, factory
    ('water', 'water', 'Water Tile', 6, True, lambda: liquid('water')),
    ('water_deep', 'water', 'Deep Water Tile', 5, True, lambda: liquid('water_deep')),
    ('swamp_water', 'water', 'Swamp Water Tile', 4, True, lambda: liquid('swamp_water')),
    ('lava', 'water', 'Lava Tile', 5, True, lambda: liquid('lava', kind='lava')),
    ('waterfall', 'water', 'Waterfall', 8, True, lambda: waterfall()),
    ('campfire', 'fire', 'Campfire', 10, True, lambda: campfire()),
    ('torch_wall', 'torches', 'Wall Torch', 8, True, lambda: torch(wall=True)),
    ('torch_stand', 'torches', 'Standing Torch', 8, True, lambda: torch(wall=False)),
    ('brazier', 'fire', 'Brazier', 8, True, lambda: brazier()),
    ('door_wood', 'doors', 'Wooden Door', 10, False, lambda: door_anim('wood')),
    ('door_gate', 'doors', 'Castle Portcullis', 8, False, lambda: door_anim('gate')),
    ('door_scifi', 'doors', 'Sliding Airlock', 12, False, lambda: door_anim('slide')),
    ('portal_magic', 'portals', 'Arcane Portal', 10, True, lambda: portal('magic')),
    ('portal_scifi', 'portals', 'Warp Gate', 12, True, lambda: portal('scifi')),
    ('chest_open', 'props', 'Chest Opening', 10, False, lambda: chest_open()),
    ('crystal_glow', 'props', 'Glowing Crystals', 6, True, lambda: crystal()),
    ('flag_red', 'props', 'Waving Flag (Red)', 8, True, lambda: flag(ramp='cloth_red')),
    ('flag_blue', 'props', 'Waving Flag (Blue)', 8, True, lambda: flag(ramp='cloth_blue')),
    ('coin_spin', 'pickups', 'Spinning Coin', 10, True, lambda: coin()),
    ('smoke_puff', 'effects', 'Smoke Puff', 10, False, lambda: smoke()),
    ('windmill', 'props', 'Windmill', 6, True, lambda: windmill()),
]
