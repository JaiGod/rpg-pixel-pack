"""40 buildings (10 types x 4 variants) in 3/4 top-down view.

Footprints are multiples of 32. Doors sit at the bottom edge; metadata stores
the door tile and collision rectangle for Godot.
"""
import math
import random
import numpy as np

from .core import Canvas, R, rgba, _shift
from .palette import OUTLINE, INK
from . import furniture as F


def _outline(cv):
    a = cv.img[:, :, 3] == 255
    o = (cv.img[:, :, 3] == 0) & (_shift(a, -1, 0) | _shift(a, 1, 0) | _shift(a, 0, -1) | _shift(a, 0, 1))
    cv.img[o] = rgba(OUTLINE)
    return cv


def wall(cv, x0, y0, x1, y1, kind, ramp, seed=0):
    m = cv.mask_rect(x0, y0, x1, y1)
    rr = R(ramp)
    rnd = random.Random(seed)
    yy, xx = np.mgrid[0:cv.h, 0:cv.w]
    if kind == 'planks':
        cv.fill(m, ramp, 1)
        cv.img[m & ((xx - x0) % 6 == 0)] = rgba(rr[0])
        cv.img[m & ((xx - x0) % 6 == 1)] = rgba(rr[2])
    elif kind == 'logs':
        cv.fill(m, ramp, 1)
        cv.img[m & ((yy - y0) % 5 == 0)] = rgba(rr[0])
        cv.img[m & ((yy - y0) % 5 == 1)] = rgba(rr[2])
        for y in range(y0, y1, 5):
            cv.shade(cv.mask_ellipse(x0, y + 2.5, 2, 2.5) | cv.mask_ellipse(x1, y + 2.5, 2, 2.5), 'wood_light')
    elif kind in ('stone', 'brick'):
        cv.fill(m, ramp, 0)
        bh = 6 if kind == 'stone' else 4
        bw = 12 if kind == 'stone' else 8
        for ri, y in enumerate(range(y0, y1 + 1, bh)):
            off = (bw // 2) * (ri % 2)
            for x in range(x0 - off, x1 + 1, bw):
                b = cv.mask_rect(x + 1, y + 1, x + bw - 1, y + bh - 1) & m
                cv.img[b] = rgba(rr[1 if rnd.random() < 0.7 else 2])
                cv.img[b & (yy == y + 1)] = rgba(rr[2])
    elif kind == 'plaster':
        cv.fill(m, ramp, 2)
        for i in range(int((x1 - x0) * (y1 - y0) / 60)):
            cv.px(rnd.randint(x0, x1), rnd.randint(y0, y1), rr[1])
    elif kind == 'timber':
        cv.fill(m, 'plaster', 2)
        tw = R('wood_dark')
        cv.img[m & ((yy == y0) | (yy == y1) | (yy == (y0 + y1) // 2))] = rgba(tw[1])
        for x in range(x0, x1 + 1, 16):
            cv.img[m & (xx == x)] = rgba(tw[1])
            cv.img[m & (xx == x + 1)] = rgba(tw[0])
        for x in range(x0, x1 - 15, 16):
            cv.line(x, (y0 + y1) // 2, x + 15, y0, tw[1])
    elif kind == 'metal':
        cv.fill(m, ramp, 1)
        cv.img[m & ((xx - x0) % 16 == 0)] = rgba(rr[0])
        cv.img[m & ((xx - x0) % 16 == 1)] = rgba(rr[2])
        cv.img[m & ((yy - y0) % 12 == 0)] = rgba(rr[0])
        for y in range(y0 + 3, y1, 12):
            for x in range(x0 + 3, x1, 16):
                cv.px(x, y, rr[3])
    elif kind == 'concrete':
        cv.fill(m, ramp, 1)
        cv.img[m & ((yy - y0) % 16 == 0)] = rgba(rr[0])
        for i in range(int((x1 - x0) * (y1 - y0) / 40)):
            cv.px(rnd.randint(x0, x1), rnd.randint(y0, y1), rr[0 if i % 2 else 2])
    # contact shadow under the roof
    cv.img[m & (yy == y0)] = rgba(rr[0])
    cv.img[m & (yy == y0 + 1)] = rgba(rr[0]) if kind not in ('brick', 'stone') else cv.img[m & (yy == y0 + 1)]
    return m


def roof(cv, x0, y0, x1, y1, ramp, kind='shingle', overhang=3):
    rr = R(ramp)
    yy, xx = np.mgrid[0:cv.h, 0:cv.w]
    if kind == 'hip':
        m = cv.mask_poly([(x0 + 10, y0), (x1 - 10, y0), (x1 + overhang, y1), (x0 - overhang, y1)])
    elif kind in ('gable', 'shingle', 'thatch'):
        m = cv.mask_rect(x0 - overhang, y0, x1 + overhang, y1)
        m &= ~(cv.mask_rect(x0 - overhang, y0, x0 - overhang + 1, y0 + 1) | cv.mask_rect(x1 + overhang - 1, y0, x1 + overhang, y0 + 1))
    elif kind == 'flat':
        m = cv.mask_rect(x0, y0, x1, y1)
        cv.fill(m, ramp, 1)
        cv.img[m & ((yy == y0) | (xx == x0))] = rgba(rr[3])
        cv.img[m & ((yy == y1) | (xx == x1))] = rgba(rr[0])
        inner = cv.mask_rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3)
        cv.fill(inner, ramp, 0)
        cv.img[inner & ((xx + yy) % 6 == 0)] = rgba(rr[1])
        return m
    cv.fill(m, ramp, 1)
    if kind in ('shingle', 'hip', 'gable'):
        for ri, y in enumerate(range(y0, y1 + 1, 4)):
            cv.img[m & (yy == y)] = rgba(rr[0])
            cv.img[m & (yy == y + 1)] = rgba(rr[2])
            off = 3 * (ri % 2)
            cv.img[m & (yy > y) & (yy < y + 4) & ((xx + off) % 6 == 0)] = rgba(rr[0])
    elif kind == 'thatch':
        cv.img[m & ((xx * 3 + yy * 7) % 5 == 0)] = rgba(rr[2])
        cv.img[m & ((xx * 5 + yy * 3) % 7 == 0)] = rgba(rr[0])
        for y in range(y0 + 6, y1, 7):
            cv.img[m & (yy == y)] = rgba(rr[0])
    # ridge + lit left slope / shaded right slope
    cx = (x0 + x1) / 2
    cv.img[m & (yy <= y0 + 1)] = rgba(rr[3])
    cv.img[m & (xx > cx + (x1 - x0) * 0.3) & ((xx + yy) % 2 == 0)] = rgba(rr[0])
    # eave shadow line
    cv.img[m & (yy == y1)] = rgba(rr[0])
    return m


def door(cv, cx, y1, w=10, h=14, ramp='wood_dark', arch=True, kind='wood'):
    x0, x1 = int(cx - w / 2), int(cx + w / 2) - 1
    y0 = y1 - h + 1
    if kind == 'slide':
        m = cv.mask_rect(x0, y0, x1, y1)
        cv.shade(m, 'tech_light')
        cv.vline(int(cx) - 1, y0 + 1, y1, R('tech')[0]); cv.vline(int(cx), y0 + 1, y1, R('tech_light')[3])
        cv.hline(x0, x1, y0, R('neon_cyan')[2])
        return
    frame = cv.mask_rect(x0 - 1, y0 - 1, x1 + 1, y1)
    if arch:
        frame |= cv.mask_ellipse(cx, y0 + 1, w / 2 + 1, 3)
    cv.fill(frame, 'stone', 1)
    m = cv.mask_rect(x0, y0, x1, y1)
    if arch:
        m |= cv.mask_ellipse(cx, y0 + 1, w / 2, 2.4) & (np.mgrid[0:cv.h, 0:cv.w][0] < y0 + 1)
    cv.fill(m, ramp, 1)
    yy, xx = np.mgrid[0:cv.h, 0:cv.w]
    cv.img[m & ((xx - x0) % 3 == 0)] = rgba(R(ramp)[0])
    cv.img[m & ((yy == y0 + 3) | (yy == y1 - 3))] = rgba(R('iron')[1])
    cv.px(x1 - 2, (y0 + y1) // 2, R('gold')[3])
    cv.hline(x0 - 1, x1 + 1, y1, R('stone')[0])


def window(cv, x, y, w=8, h=8, frame='wood', lit=True, shutters=None, kind='square'):
    if kind == 'round':
        m = cv.mask_ellipse(x + w / 2, y + h / 2, w / 2, h / 2)
        cv.fill(m, frame, 1)
        g = cv.mask_ellipse(x + w / 2, y + h / 2, w / 2 - 1, h / 2 - 1)
        cv.fill(g, 'fire' if lit else 'glass', 3 if lit else 1)
        cv.img[g & (np.mgrid[0:cv.h, 0:cv.w][1] == int(x + w / 2))] = rgba(R(frame)[1])
        return
    cv.rect(x - 1, y - 1, x + w, y + h, R(frame)[1])
    g = cv.mask_rect(x, y, x + w - 1, y + h - 1)
    if lit:
        cv.fill(g, 'fire', 3)
        cv.img[g & (np.mgrid[0:cv.h, 0:cv.w][0] >= y + h // 2)] = rgba(R('fire')[2])
    else:
        cv.fill(g, 'glass', 1)
        cv.px(x + 1, y + 1, R('glass')[3]); cv.px(x + 2, y + 1, R('glass')[3])
    if kind == 'square':
        cv.vline(x + w // 2, y, y + h - 1, R(frame)[1]); cv.hline(x, x + w - 1, y + h // 2, R(frame)[1])
    cv.hline(x - 2, x + w + 1, y + h, R(frame)[2])
    if shutters:
        cv.rect(x - 4, y - 1, x - 2, y + h - 1, R(shutters)[2]); cv.rect(x + w + 1, y - 1, x + w + 3, y + h - 1, R(shutters)[1])


def chimney(cv, x, y, h=10, ramp='brick', smoke=True):
    m = cv.mask_rect(x, y, x + 5, y + h)
    cv.fill(m, ramp, 1)
    cv.vline(x, y, y + h, R(ramp)[2]); cv.vline(x + 5, y, y + h, R(ramp)[0])
    cv.rect(x - 1, y, x + 6, y + 1, R('stone')[2])
    if smoke:
        for i, (dx, dy, r) in enumerate([(2, -3, 2), (4, -7, 2.5), (2, -11, 3)]):
            sm = cv.mask_ellipse(x + dx + 0.5, y + dy, r, r * 0.8)
            cv.img[sm & (cv.img[:, :, 3] == 0)] = (220, 220, 230, 150 - i * 30)


def sign(cv, x, y, ramp='wood', icon=None):
    cv.hline(x - 2, x + 10, y - 2, R('iron')[1])
    cv.vline(x, y - 2, y, R('iron')[1]); cv.vline(x + 8, y - 2, y, R('iron')[1])
    m = cv.mask_rect(x - 1, y, x + 9, y + 6)
    cv.shade(m, ramp)
    if icon == 'mug':
        cv.rect(x + 2, y + 2, x + 5, y + 5, R('gold')[2]); cv.px(x + 6, y + 3, R('gold')[1]); cv.hline(x + 2, x + 5, y + 1, R('cloth_white')[3])
    elif icon == 'coin':
        cv.shade(cv.mask_ellipse(x + 4.5, y + 3.5, 2.5, 2.5), 'gold')
    elif icon == 'anvil':
        cv.rect(x + 1, y + 2, x + 7, y + 3, R('iron')[2]); cv.rect(x + 3, y + 4, x + 5, y + 5, R('iron')[1])
    elif icon == 'potion':
        cv.rect(x + 3, y + 3, x + 5, y + 5, R('ruby')[2]); cv.px(x + 4, y + 2, R('glass')[3])


def awning(cv, x0, x1, y, cols=('cloth_red', 'cloth_white')):
    for i, x in enumerate(range(x0, x1, 4)):
        c = R(cols[i % 2])
        cv.rect(x, y, x + 3, y + 5, c[2])
        cv.px(x + 1, y + 6, c[1]); cv.px(x + 2, y + 6, c[1])
        cv.hline(x, x + 3, y + 5, c[1])


def ground_shadow(cv, x0, x1, y):
    for x in range(int(x0), int(x1) + 1):
        for dy in (0, 1):
            if cv.get(x, y + dy)[3] == 0:
                cv.px(x, y + dy, (20, 16, 30, 90 - dy * 40))


# =============================================================================
def small_house(wallk, wallr, roofr, roofk='shingle', lit=True, shutters=None, seed=0):
    def fn():
        W, H = 96, 96
        cv = Canvas(W, H)
        roof(cv, 8, 6, 87, 50, roofr, roofk)
        chimney(cv, 66, 2, 10)
        wall(cv, 10, 51, 85, 88, wallk, wallr, seed)
        door(cv, 48, 88, 12, 18)
        window(cv, 20, 62, 10, 9, lit=lit, shutters=shutters)
        window(cv, 66, 62, 10, 9, lit=lit, shutters=shutters)
        F_flower_box(cv, 19, 72)
        ground_shadow(cv, 8, 88, 89)
        return _outline(cv)
    return fn


def F_flower_box(cv, x, y):
    cv.rect(x, y, x + 12, y + 2, R('wood')[1])
    for i in range(0, 12, 3):
        cv.px(x + 1 + i, y - 1, R(['cloth_red', 'cloth_yellow', 'cloth_pink', 'cloth_white'][i // 3 % 4])[2])
        cv.px(x + 2 + i, y - 1, R('leaf')[2])


def large_house(wallk, wallr, roofr, roofk='shingle', seed=0):
    def fn():
        W, H = 128, 128
        cv = Canvas(W, H)
        roof(cv, 8, 6, 119, 62, roofr, roofk)
        # dormer
        dm = cv.mask_poly([(52, 30), (76, 30), (64, 16)])
        cv.fill(dm, roofr, 2)
        window(cv, 60, 32, 8, 8)
        chimney(cv, 22, 6, 12)
        chimney(cv, 98, 2, 12, smoke=False)
        wall(cv, 10, 63, 117, 120, wallk, wallr, seed)
        cv.hline(10, 117, 90, R('wood_dark')[1])
        door(cv, 64, 120, 14, 22)
        for x in (20, 40, 80, 100):
            window(cv, x, 70, 10, 10, shutters='cloth_green')
            window(cv, x, 98, 10, 10)
        ground_shadow(cv, 8, 120, 121)
        return _outline(cv)
    return fn


def inn(wallr, roofr, seed=0):
    def fn():
        W, H = 160, 128
        cv = Canvas(W, H)
        roof(cv, 8, 4, 151, 58, roofr, 'shingle')
        chimney(cv, 30, 2, 12); chimney(cv, 122, 0, 12)
        wall(cv, 10, 59, 149, 120, 'timber', wallr, seed)
        door(cv, 80, 120, 18, 22, arch=True)
        for x in (18, 40, 108, 130):
            window(cv, x, 68, 12, 10)
            window(cv, x, 98, 12, 10)
        sign(cv, 100, 96, 'wood', 'mug')
        for x in (60, 96):
            cv.rect(x, 113, x + 4, 120, R('wood')[1])   # barrels by the door
            cv.shade(cv.mask_ellipse(x + 2, 112, 3, 1.5), 'wood_light')
        ground_shadow(cv, 8, 152, 121)
        return _outline(cv)
    return fn


def shop(wallk, wallr, roofr, awn, icon, seed=0):
    def fn():
        W, H = 96, 96
        cv = Canvas(W, H)
        roof(cv, 8, 6, 87, 46, roofr, 'shingle')
        wall(cv, 10, 47, 85, 88, wallk, wallr, seed)
        awning(cv, 12, 84, 50, awn)
        # display window
        cv.rect(15, 61, 41, 76, R('wood')[1])
        cv.fill(cv.mask_rect(16, 62, 40, 75), 'glass', 1)
        for (x, c) in [(19, 'ruby'), (25, 'gold'), (31, 'emerald'), (36, 'magic_blue')]:
            cv.shade(cv.mask_ellipse(x, 72, 2, 2.5), c)
        cv.line(17, 64, 22, 62, R('glass')[3])
        door(cv, 66, 88, 12, 18, arch=False)
        sign(cv, 52, 56, 'wood', icon)
        ground_shadow(cv, 8, 88, 89)
        return _outline(cv)
    return fn


def barn(wallr, roofr, silo=True, seed=0):
    def fn():
        W, H = 128, 128
        cv = Canvas(W, H)
        bx1 = 92 if silo else 119
        roof(cv, 8, 10, bx1, 58, roofr, 'shingle')
        wall(cv, 10, 59, bx1 - 2, 120, 'planks', wallr, seed)
        # big doors with white X
        dx0, dx1 = (bx1 + 10) // 2 - 16, (bx1 + 10) // 2 + 15
        cv.fill(cv.mask_rect(dx0, 82, dx1, 120), wallr, 0)
        for (a, b) in ((dx0, (dx0 + dx1) // 2), ((dx0 + dx1) // 2 + 1, dx1)):
            cv.rect(a, 82, b, 84, R('cloth_white')[2]); cv.rect(a, 118, b, 120, R('cloth_white')[2])
            cv.vline(a, 82, 120, R('cloth_white')[2]); cv.vline(b, 82, 120, R('cloth_white')[1])
            cv.line(a, 84, b, 118, R('cloth_white')[2]); cv.line(b, 84, a, 118, R('cloth_white')[2])
        window(cv, (bx1 + 10) // 2 - 5, 64, 10, 10, lit=False, kind='round')
        if silo:
            m = cv.mask_rect(96, 28, 122, 120)
            cv.shade_cyl(m, 'stone_warm')
            dome = cv.mask_ellipse(109, 28, 13.5, 10) & (np.mgrid[0:H, 0:W][0] <= 30)
            cv.shade(dome, roofr)
            for y in range(38, 120, 10):
                cv.img[m & (np.mgrid[0:H, 0:W][0] == y)] = rgba(R('stone_warm')[0])
        # hay outside
        cv.shade(cv.mask_rect(14, 110, 26, 120), 'thatch')
        ground_shadow(cv, 8, 124, 121)
        return _outline(cv)
    return fn


def blacksmith(wallk, wallr, roofr, seed=0):
    def fn():
        W, H = 128, 96
        cv = Canvas(W, H)
        roof(cv, 8, 6, 82, 44, roofr, 'shingle')
        wall(cv, 10, 45, 80, 88, wallk, wallr, seed)
        door(cv, 34, 88, 12, 18)
        window(cv, 56, 56, 10, 9)
        # open-air forge lean-to
        roof(cv, 84, 26, 122, 46, 'roof_slate', 'flat')
        for x in (86, 119):
            cv.rect(x, 47, x + 2, 88, R('wood_dark')[1])
        forge = cv.mask_rect(92, 62, 116, 88)
        F_stone = 'brick'
        cv.shade(forge, F_stone)
        cv.fill(cv.mask_rect(97, 70, 111, 82), 'fire', 2)
        cv.img[cv.mask_rect(97, 70, 111, 82) & (np.mgrid[0:H, 0:W][1] % 3 == 0)] = rgba(R('fire')[3])
        chimney(cv, 101, 16, 46, 'brick')
        an = F.prop('anvil')()
        cv.paste(an, 92, 60) if False else None
        sign(cv, 60, 72, 'wood', 'anvil')
        ground_shadow(cv, 8, 124, 89)
        return _outline(cv)
    return fn


def wizard_tower(stone, roofr, seed=0):
    def fn():
        W, H = 64, 160
        cv = Canvas(W, H)
        yy, xx = np.mgrid[0:H, 0:W]
        body = cv.mask_rect(12, 44, 51, 152) | cv.mask_ellipse(31.5, 152, 20, 5)
        cv.shade_cyl(body, stone)
        for y in range(50, 150, 7):
            off = 4 if (y // 7) % 2 else 0
            cv.img[body & (yy == y)] = rgba(R(stone)[0])
            cv.img[body & (yy > y) & (yy < y + 7) & ((xx + off) % 9 == 0)] = rgba(R(stone)[0])
        # balcony ring
        ring = cv.mask_ellipse(31.5, 46, 24, 6)
        cv.shade(ring, stone)
        cone = cv.mask_poly([(4, 46), (59, 46), (36, 2), (28, 8)])
        cv.shade(cone, roofr, depth=2)
        cv.img[cone & ((yy % 6) == 0)] = rgba(R(roofr)[0])
        star = cv.mask_ellipse(36, 4, 2, 2)
        cv.fill(star, 'gold', 3)
        for y in (64, 92, 120):
            window(cv, 27, y, 9, 11, frame='stone', kind='round')
        door(cv, 31.5, 154, 12, 16, arch=True)
        cv.px(14, 30, R('magic_purple')[3]); cv.px(50, 20, R('magic_blue')[3])
        ground_shadow(cv, 10, 54, 157)
        return _outline(cv)
    return fn


def castle(stone, roofr, banner, seed=0):
    def fn():
        W, H = 192, 192
        cv = Canvas(W, H)
        yy, xx = np.mgrid[0:H, 0:W]
        # keep
        roof(cv, 56, 10, 135, 50, roofr, 'hip')
        wall(cv, 58, 51, 133, 120, 'stone', stone, seed)
        for x in range(58, 134, 8):
            cv.rect(x, 46, x + 4, 50, R(stone)[2])
        # curtain wall
        wall(cv, 8, 112, 183, 184, 'stone', stone, seed + 1)
        for x in range(8, 184, 10):
            cv.rect(x, 104, x + 6, 111, R(stone)[2]); cv.hline(x, x + 6, 104, R(stone)[3])
        # towers
        for tx in (4, 148):
            t = cv.mask_rect(tx, 70, tx + 39, 186)
            cv.shade_cyl(t, stone)
            for y in range(76, 186, 7):
                cv.img[t & (yy == y)] = rgba(R(stone)[0])
            cone = cv.mask_poly([(tx - 4, 72), (tx + 43, 72), (tx + 20, 20)])
            cv.shade(cone, roofr, depth=2)
            cv.img[cone & ((yy % 5) == 0)] = rgba(R(roofr)[0])
            cv.vline(tx + 20, 6, 20, R('wood_dark')[2])
            cv.fill(cv.mask_poly([(tx + 21, 6), (tx + 33, 10), (tx + 21, 14)]), banner, 2)
            window(cv, tx + 16, 100, 7, 12, frame='stone', lit=True, kind='round')
            window(cv, tx + 16, 140, 7, 12, frame='stone', lit=False, kind='round')
        for x in (74, 110):
            window(cv, x, 66, 8, 14, frame='stone')
        # banners on keep
        for x in (66, 118):
            b = cv.mask_poly([(x, 84), (x + 9, 84), (x + 9, 104), (x + 4.5, 100), (x, 104)])
            cv.shade(b, banner)
            cv.shade(cv.mask_ellipse(x + 4.5, 91, 2, 2), 'gold')
        # gate
        gate = cv.mask_rect(80, 140, 111, 184) | cv.mask_ellipse(95.5, 140, 16, 10)
        cv.fill(gate, 'stone_dark', 0)
        port = gate & ~cv.mask_rect(80, 182, 111, 184)
        cv.img[port & ((xx % 4 == 0) | (yy % 5 == 0))] = rgba(R('iron')[1])
        cv.img[cv.mask_ellipse(95.5, 140, 18, 12) & ~cv.mask_ellipse(95.5, 140, 16, 10) & (yy < 150)] = rgba(R(stone)[3])
        ground_shadow(cv, 2, 190, 187)
        return _outline(cv)
    return fn


def habitat(shell, accent, seed=0):
    def fn():
        W, H = 128, 96
        cv = Canvas(W, H)
        yy, xx = np.mgrid[0:H, 0:W]
        base = cv.mask_rect(6, 54, 121, 88)
        cv.shade(base, 'tech')
        cv.img[base & (yy == 70)] = rgba(R('warning')[2])
        cv.img[base & (yy == 70) & (xx % 8 < 4)] = rgba(R('tech_dark')[1])
        dome = cv.mask_ellipse(64, 56, 54, 46) & (yy <= 56)
        cv.shade(dome, shell, depth=2)
        # panel seams
        for a in range(-80, 81, 20):
            r = math.radians(a)
            cv.line(64, 12, 64 + math.sin(r) * 54, 56, R(shell)[0])
        for ry in (24, 40):
            ring = cv.mask_ellipse(64, 56, 54 * (56 - ry) / 44 + 6, 56 - ry) & ~cv.mask_ellipse(64, 56, 54 * (56 - ry) / 44 + 5, 56 - ry - 1) & dome
            cv.img[ring] = rgba(R(shell)[0])
        win = cv.mask_ellipse(64, 34, 22, 12) & dome
        cv.fill(win, 'glass', 1)
        cv.img[win & (yy < 30)] = rgba(R('glass')[2])
        cv.line(48, 30, 56, 26, R('glass')[3])
        # airlock
        door(cv, 64, 88, 16, 20, kind='slide')
        for x in (20, 100):
            cv.rect(x, 76, x + 6, 82, R(accent)[2]); cv.px(x + 3, 79, R(accent)[3])
        cv.vline(104, 2, 20, R('tech')[2]); cv.shade(cv.mask_ellipse(104, 4, 6, 2.5), 'tech_light')
        cv.px(104, 0, R('ruby')[3])
        ground_shadow(cv, 6, 122, 89)
        return _outline(cv)
    return fn


def apartment(body, neon, seed=0, floors=8):
    def fn():
        W, H = 96, 192
        cv = Canvas(W, H)
        yy, xx = np.mgrid[0:H, 0:W]
        roof(cv, 6, 10, 89, 26, 'tech_dark', 'flat')
        wall(cv, 6, 27, 89, 184, 'concrete', body, seed)
        rnd = random.Random(seed)
        fh = (184 - 46) // floors
        for f in range(floors):
            y = 32 + f * fh
            for x in range(12, 84, 14):
                lit = rnd.random() < 0.6
                g = cv.mask_rect(x, y, x + 9, y + fh - 8)
                cv.fill(g, 'fire' if lit else 'glass', 3 if lit else 0)
                if lit and rnd.random() < 0.35:
                    cv.fill(g, neon, 2)
                cv.hline(x - 1, x + 10, y + fh - 7, R('tech')[2])
        # neon strips + sign
        cv.vline(7, 27, 184, R(neon)[3]); cv.vline(88, 27, 184, R(neon)[2])
        sg = cv.mask_rect(26, 150, 69, 160)
        cv.fill(sg, 'tech_dark', 0)
        for x in range(29, 67):
            if (x // 3) % 2 == 0:
                cv.px(x, 154, R(neon)[3]); cv.px(x, 155, R(neon)[2])
        door(cv, 48, 184, 16, 18, kind='slide')
        # rooftop
        cv.vline(20, 0, 10, R('tech')[2]); cv.px(20, 0, R('ruby')[3])
        cv.shade(cv.mask_rect(60, 2, 78, 10), 'tech')
        for x in range(62, 78, 3):
            cv.vline(x, 3, 9, R('tech_dark')[1])
        ground_shadow(cv, 6, 90, 185)
        return _outline(cv)
    return fn


BUILDINGS = [
    # small houses
    ('house_small_cottage', 'small_houses', 'Cottage', small_house('planks', 'wood', 'roof_red', shutters='cloth_green', seed=1)),
    ('house_small_thatch', 'small_houses', 'Thatched Hut', small_house('timber', 'plaster', 'thatch', 'thatch', seed=2)),
    ('house_small_stone', 'small_houses', 'Stone Cottage', small_house('stone', 'cobble', 'roof_slate', seed=3)),
    ('house_small_log', 'small_houses', 'Log Cabin', small_house('logs', 'wood', 'roof_green', lit=False, seed=4)),
    # large houses
    ('house_large_manor', 'large_houses', 'Manor', large_house('brick', 'brick', 'roof_slate', seed=5)),
    ('house_large_townhouse', 'large_houses', 'Townhouse', large_house('timber', 'plaster', 'roof_red', seed=6)),
    ('house_large_villa', 'large_houses', 'Villa', large_house('plaster', 'sandstone', 'roof_red', 'hip', seed=7)),
    ('house_large_lodge', 'large_houses', 'Hunting Lodge', large_house('logs', 'wood_dark', 'roof_green', seed=8)),
    # inns
    ('inn_tavern', 'inns', 'The Prancing Boar', inn('plaster', 'roof_red', 1)),
    ('inn_lodge', 'inns', 'Traveler\'s Rest', inn('plaster', 'roof_slate', 2)),
    ('inn_mountain', 'inns', 'Frostpeak Inn', inn('plaster', 'roof_blue', 3)),
    ('inn_harbor', 'inns', 'Harbor Inn', inn('plaster', 'roof_green', 4)),
    # shops
    ('shop_general', 'shops', 'General Store', shop('planks', 'wood_light', 'roof_red', ('cloth_red', 'cloth_white'), 'coin', 1)),
    ('shop_potion', 'shops', 'Potion Shop', shop('timber', 'plaster', 'roof_blue', ('cloth_purple', 'cloth_white'), 'potion', 2)),
    ('shop_armory', 'shops', 'Armory', shop('stone', 'stone', 'roof_slate', ('cloth_navy', 'cloth_yellow'), 'anvil', 3)),
    ('shop_bakery', 'shops', 'Bakery', shop('plaster', 'plaster', 'roof_red', ('cloth_green', 'cloth_white'), 'coin', 4)),
    # farms
    ('farm_red_barn', 'farms', 'Red Barn & Silo', barn('roof_red', 'roof_slate', True, 1)),
    ('farm_barn', 'farms', 'Barn', barn('wood', 'roof_red', False, 2)),
    ('farm_stable', 'farms', 'Stable', barn('wood_dark', 'thatch', False, 3)),
    ('farm_granary', 'farms', 'Granary', barn('wood_light', 'roof_green', True, 4)),
    # blacksmiths
    ('blacksmith_forge', 'blacksmiths', 'Village Forge', blacksmith('stone', 'stone', 'roof_slate', 1)),
    ('blacksmith_timber', 'blacksmiths', 'Smithy', blacksmith('timber', 'plaster', 'roof_red', 2)),
    ('blacksmith_dwarven', 'blacksmiths', 'Dwarven Forge', blacksmith('brick', 'stone_dark', 'roof_slate', 3)),
    ('blacksmith_frontier', 'blacksmiths', 'Frontier Smith', blacksmith('planks', 'wood', 'thatch', 4)),
    # wizard towers
    ('tower_arcane', 'wizard_towers', 'Arcane Tower', wizard_tower('stone', 'cloth_purple', 1)),
    ('tower_frost', 'wizard_towers', 'Frost Spire', wizard_tower('ice', 'roof_blue', 2)),
    ('tower_dark', 'wizard_towers', 'Dark Tower', wizard_tower('stone_dark', 'cloth_crimson', 3)),
    ('tower_druid', 'wizard_towers', 'Druid Tower', wizard_tower('stone_warm', 'roof_green', 4)),
    # castles
    ('castle_royal', 'castles', 'Royal Castle', castle('stone', 'roof_blue', 'cloth_blue', 1)),
    ('castle_dark', 'castles', 'Dark Citadel', castle('stone_dark', 'cloth_black', 'cloth_crimson', 2)),
    ('castle_desert', 'castles', 'Desert Palace', castle('sandstone', 'gold', 'cloth_red', 3)),
    ('castle_frost', 'castles', 'Frost Keep', castle('snow', 'roof_slate', 'cloth_teal', 4)),
    # space habitats
    ('habitat_dome', 'space_habitats', 'Hab Dome', habitat('tech_light', 'neon_cyan', 1)),
    ('habitat_greenhouse', 'space_habitats', 'Greenhouse Dome', habitat('glass', 'neon_green', 2)),
    ('habitat_mining', 'space_habitats', 'Mining Outpost', habitat('warning', 'ruby', 3)),
    ('habitat_research', 'space_habitats', 'Research Module', habitat('cloth_white', 'neon_cyan', 4)),
    # futuristic apartments
    ('apartment_neon', 'futuristic_apartments', 'Neon Tower', apartment('tech', 'neon_pink', 1)),
    ('apartment_corp', 'futuristic_apartments', 'Corporate Block', apartment('tech_light', 'neon_cyan', 2, 9)),
    ('apartment_slum', 'futuristic_apartments', 'Stack Housing', apartment('stone_dark', 'warning', 3, 7)),
    ('apartment_luxury', 'futuristic_apartments', 'Skyline Residences', apartment('cloth_navy', 'neon_green', 4, 9)),
]
