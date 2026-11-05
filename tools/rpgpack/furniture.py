"""Furniture & props in 3/4 top-down view (top face + front face).

Sizes are multiples of 32. Each entry: (id, category, name, (w, h), draw_fn).
"""
import math
import numpy as np

from .core import Canvas, R, rgba, mix, _shift
from .palette import OUTLINE, INK, EYE_WHITE


def block(cv, x0, y0, x1, y1, top_h, ramp, front=None, grain=False):
    """3/4-view box: top face rows [y0, y0+top_h), front face below."""
    rr = R(ramp)
    fr = R(front or ramp)
    top = cv.mask_rect(x0, y0, x1, y0 + top_h - 1)
    frt = cv.mask_rect(x0, y0 + top_h, x1, y1)
    cv.fill(top, rr, 2)
    cv.hline(x0, x1, y0, rr[3])
    cv.vline(x0, y0, y0 + top_h - 1, rr[3])
    cv.fill(frt, fr, 1)
    cv.hline(x0, x1, y0 + top_h, fr[0])
    cv.vline(x1, y0 + top_h, y1, fr[0])
    if grain:
        yy, xx = np.mgrid[0:cv.h, 0:cv.w]
        cv.img[top & (yy % 3 == 1) & (xx % 7 != 0) & (yy > y0)] = rgba(rr[1])
        cv.img[top & (yy % 3 == 1) & (xx % 7 == 0)] = rgba(rr[2])
    return top, frt


def legs(cv, xs, y0, y1, ramp):
    for x in xs:
        cv.rect(x, y0, x + 1, y1, R(ramp)[1])
        cv.px(x + 1, y1, R(ramp)[0])


def shadow(cv, x0, x1, y):
    for x in range(int(x0), int(x1) + 1):
        if cv.get(x, y)[3] == 0:
            cv.px(x, y, (20, 16, 30, 90))


def done(cv, outline=True):
    if outline:
        a = cv.img[:, :, 3] > 0
        sem = (cv.img[:, :, 3] > 0) & (cv.img[:, :, 3] < 255)
        solid = a & ~sem
        o = ~a & (_shift(solid, -1, 0) | _shift(solid, 1, 0) | _shift(solid, 0, -1) | _shift(solid, 0, 1))
        cv.img[o] = rgba(OUTLINE)
    return cv


# ----------------------------------------------------------------- tables
def table(wood='wood', w=32, h=32, cloth=None, kind='wood', items=None):
    def fn():
        cv = Canvas(w, h)
        x0, x1 = 3, w - 4
        if kind == 'round':
            m = cv.mask_ellipse(w / 2, 14, w / 2 - 4, 8)
            cv.shade(m, wood)
            cv.fill(cv.mask_ellipse(w / 2, 15, w / 2 - 4, 8) & ~m & (np.mgrid[0:h, 0:w][0] > 14), wood, 0)
            cv.rect(w / 2 - 2, 22, w / 2 + 1, 28, R(wood)[1])
            cv.rect(w / 2 - 5, 28, w / 2 + 4, 29, R(wood)[0])
        else:
            legs(cv, [x0 + 1, x1 - 2], 20, h - 4, wood if kind != 'lab' else 'tech')
            block(cv, x0, 8, x1, 19, 9, wood, grain=(kind in ('wood', 'tavern')))
            if kind == 'stone':
                yy, xx = np.mgrid[0:h, 0:w]
                cv.img[cv.mask_rect(x0, 8, x1, 16) & ((xx * 7 + yy * 3) % 11 == 0)] = rgba(R(wood)[1])
            if kind == 'lab':
                cv.rect(x0, 17, x1, 19, R('tech')[1])
                cv.rect(x0 + 2, 18, x0 + 4, 18, R('neon_cyan')[2])
            if kind == 'desk':
                cv.rect(x1 - 9, 17, x1 - 1, 19, R(wood)[0])
                cv.rect(x1 - 9, 20, x1 - 1, h - 5, R(wood)[1])
                cv.hline(x1 - 7, x1 - 3, 23, R('gold')[2])
        if cloth:
            cv.rect(x0 + 3, 9, x1 - 3, 16, R(cloth)[2])
            cv.rect(x0 + 3, 17, x1 - 3, 19, R(cloth)[1])
            cv.hline(x0 + 3, x1 - 3, 9, R(cloth)[3])
        for it in (items or []):
            _tabletop_item(cv, it)
        shadow(cv, x0, x1, h - 3)
        return done(cv)
    return fn


def _tabletop_item(cv, it):
    kind, x, y = it
    if kind == 'mug':
        cv.rect(x, y, x + 2, y + 3, R('wood_light')[2]); cv.hline(x, x + 2, y, R('cloth_white')[3]); cv.px(x + 3, y + 1, R('wood_light')[1])
    elif kind == 'candle':
        cv.rect(x, y, x + 1, y + 3, R('cloth_white')[2]); cv.px(x, y - 1, R('fire')[3]); cv.px(x, y - 2, R('fire')[2])
    elif kind == 'book':
        cv.rect(x, y, x + 4, y + 2, R('cloth_red')[2]); cv.hline(x, x + 4, y + 2, R('cloth_white')[2])
    elif kind == 'plate':
        cv.shade(cv.mask_ellipse(x + 2, y + 1.5, 2.6, 1.6), 'cloth_white')
        cv.px(x + 2, y + 1, R('cloth_orange')[2])
    elif kind == 'flask':
        cv.rect(x, y + 1, x + 2, y + 3, R('neon_green')[2]); cv.px(x + 1, y, R('glass')[3])
    elif kind == 'map':
        cv.rect(x, y, x + 6, y + 3, R('sand')[2]); cv.px(x + 2, y + 1, R('cloth_red')[2]); cv.line(x + 1, y + 2, x + 5, y + 1, R('dirt')[1])


# ----------------------------------------------------------------- beds
def bed(frame='wood', sheet='cloth_red', w=32, h=64, kind='single'):
    def fn():
        cv = Canvas(w, h)
        x0, x1 = 3, w - 4
        if kind == 'pod':
            body = cv.mask_ellipse(w / 2, h / 2, w / 2 - 3, h / 2 - 4)
            cv.shade(body, 'tech_light', depth=2)
            inner = cv.mask_ellipse(w / 2, h / 2 + 2, w / 2 - 7, h / 2 - 10)
            cv.fill(inner, 'tech', 1)
            glass = cv.mask_ellipse(w / 2, h / 2 - 2, w / 2 - 7, h / 2 - 14)
            cv.fill(glass, 'glass', 2)
            cv.img[glass & (np.mgrid[0:h, 0:w][1] < w / 2 - 3)] = rgba(R('glass')[3])
            cv.rect(w / 2 - 3, h - 9, w / 2 + 2, h - 8, R('neon_cyan')[2])
            return done(cv)
        if kind == 'hammock':
            cv.rect(x0, 2, x0 + 1, h - 3, R('wood')[1]); cv.rect(x1 - 1, 2, x1, h - 3, R('wood')[1])
            m = cv.mask_poly([(x0 + 3, 6), (x1 - 3, 6), (x1 - 5, h - 8), (x0 + 5, h - 8)])
            cv.shade(m, sheet)
            yy, xx = np.mgrid[0:h, 0:w]
            cv.img[m & (yy % 4 == 0)] = rgba(R(sheet)[1])
            return done(cv)
        if kind == 'straw':
            m = cv.mask_rect(x0, 8, x1, h - 6)
            cv.shade(m, 'thatch')
            yy, xx = np.mgrid[0:h, 0:w]
            cv.img[m & ((xx * 3 + yy) % 5 == 0)] = rgba(R('thatch')[1])
            cv.shade(cv.mask_rect(x0 + 2, 10, x1 - 2, 16), 'cloth_tan')
            cv.shade(cv.mask_rect(x0 + 1, 22, x1 - 1, h - 8), 'cloth_brown')
            return done(cv)
        # headboard
        block(cv, x0, 2, x1, 12, 3, frame)
        if kind == 'royal':
            for x in (x0, x1 - 2):
                cv.rect(x, 0, x + 2, h - 6, R(frame)[2])
                cv.px(x + 1, 0, R('gold')[3])
        # mattress
        mt = cv.mask_rect(x0 + 1, 12, x1 - 1, h - 8)
        cv.fill(mt, 'cloth_white', 2)
        # pillow(s)
        if w >= 64:
            for px0 in (x0 + 4, w / 2 + 2):
                cv.shade(cv.mask_rect(px0, 14, px0 + w / 2 - 9, 20), 'cloth_white')
        else:
            cv.shade(cv.mask_rect(x0 + 4, 14, x1 - 4, 20), 'cloth_white')
        # blanket
        bl = cv.mask_rect(x0 + 1, 24, x1 - 1, h - 8)
        cv.shade(bl, sheet, depth=2)
        cv.hline(x0 + 1, x1 - 1, 24, R(sheet)[3])
        cv.hline(x0 + 1, x1 - 1, 25, R('cloth_white')[2])
        if kind == 'royal':
            cv.img[bl & (np.mgrid[0:h, 0:w][0] % 6 == 0)] = rgba(R('gold')[2])
        if kind == 'bunk':
            pass
        # footboard
        block(cv, x0, h - 9, x1, h - 4, 2, frame)
        if kind == 'medical':
            cv.rect(x0 + 1, h - 8, x1 - 1, h - 7, R('tech_light')[2])
            for x in (x0 + 1, x1 - 2):
                cv.px(x, h - 3, R('tech')[0])
        shadow(cv, x0, x1, h - 3)
        return done(cv)
    return fn


# ----------------------------------------------------------------- seating
def chair(wood='wood', seat=None, kind='chair'):
    def fn():
        cv = Canvas(32, 32)
        if kind == 'stool':
            legs(cv, [11, 19], 18, 28, wood)
            m = cv.mask_ellipse(16, 15, 7, 4)
            cv.shade(m, wood)
            cv.rect(9, 16, 22, 18, R(wood)[0])
            cv.fill(cv.mask_ellipse(16, 15, 7, 4) & ~cv.mask_ellipse(16, 14, 7, 4), wood, 1)
        elif kind == 'bench':
            cv2 = Canvas(64, 32)
            legs(cv2, [6, 55], 20, 28, wood)
            block(cv2, 3, 13, 60, 20, 5, wood, grain=True)
            return done(cv2)
        elif kind == 'throne':
            block(cv, 6, 1, 25, 16, 3, 'gold')
            cv.shade(cv.mask_rect(9, 4, 22, 14), seat)
            cv.px(15, 2, R('ruby')[3]); cv.px(16, 2, R('ruby')[2])
            block(cv, 5, 15, 26, 28, 5, 'gold')
            cv.shade(cv.mask_rect(8, 16, 23, 19), seat)
            for x in (4, 25):
                cv.rect(x, 12, x + 2, 22, R('gold')[1])
        elif kind == 'armchair':
            block(cv, 5, 4, 26, 16, 3, seat)
            block(cv, 4, 14, 27, 27, 6, seat)
            for x in (3, 24):
                block(cv, x, 11, x + 4, 25, 3, seat)
            legs(cv, [6, 24], 27, 29, 'wood_dark')
        elif kind == 'office':
            block(cv, 9, 3, 22, 15, 2, 'cloth_black')
            block(cv, 8, 14, 23, 20, 4, 'cloth_black')
            cv.rect(15, 21, 16, 25, R('tech')[2])
            cv.hline(9, 22, 26, R('tech')[1]); cv.px(9, 27, R('tech_dark')[1]); cv.px(22, 27, R('tech_dark')[1]); cv.px(15, 27, R('tech_dark')[1])
        elif kind == 'scifi':
            m = cv.mask_ellipse(16, 12, 8, 9) & (np.mgrid[0:32, 0:32][0] < 17)
            cv.shade(m, 'tech_light')
            block(cv, 7, 15, 24, 22, 4, 'tech_light')
            cv.hline(9, 22, 19, R('neon_cyan')[2])
            cv.rect(14, 23, 17, 27, R('tech')[1]); cv.rect(10, 27, 21, 28, R('tech')[0])
        else:
            legs(cv, [9, 21], 19, 28, wood)
            block(cv, 8, 3, 23, 12, 2, wood)
            cv.rect(10, 6, 21, 11, R(wood)[0])
            for x in (12, 15, 18):
                cv.rect(x, 5, x + 1, 11, R(wood)[2])
            block(cv, 7, 13, 24, 19, 4, wood)
            if seat:
                cv.shade(cv.mask_rect(8, 13, 23, 16), seat)
        shadow(cv, 6, 25, 29)
        return done(cv)
    return fn


def couch(fabric, w=64):
    def fn():
        cv = Canvas(w, 32)
        block(cv, 3, 4, w - 4, 16, 3, fabric)
        block(cv, 2, 14, w - 3, 26, 5, fabric)
        for x in (1, w - 7):
            block(cv, x, 10, x + 5, 25, 3, fabric)
        cv.vline(w // 2, 14, 18, R(fabric)[0])
        cv.shade(cv.mask_rect(9, 8, 17, 14), 'cloth_yellow')
        legs(cv, [5, w - 7], 26, 28, 'wood_dark')
        shadow(cv, 2, w - 3, 29)
        return done(cv)
    return fn


# ----------------------------------------------------------------- storage
def shelf(wood='wood', kind='books', h=64):
    def fn():
        cv = Canvas(32, h)
        x0, x1 = 3, 28
        block(cv, x0, 2, x1, h - 4, 3, wood)
        inner = cv.mask_rect(x0 + 2, 6, x1 - 2, h - 7)
        cv.fill(inner, wood, 0)
        rows = list(range(6, h - 7, 11 if h > 32 else 9))
        import random
        rnd = random.Random(sum(map(ord, kind)))
        for ry in rows:
            sy = ry + 9 if h > 32 else ry + 7
            if sy > h - 7:
                break
            cv.hline(x0 + 2, x1 - 2, sy, R(wood)[2])
            cv.hline(x0 + 2, x1 - 2, sy + 1, R(wood)[1])
            x = x0 + 3
            while x < x1 - 3:
                if kind == 'books':
                    bw = rnd.choice([1, 2, 2])
                    bh = rnd.choice([6, 7, 8])
                    col = rnd.choice(['cloth_red', 'cloth_blue', 'cloth_green', 'cloth_brown', 'cloth_purple', 'cloth_yellow', 'cloth_teal'])
                    cv.rect(x, sy - bh, x + bw, sy - 1, R(col)[2])
                    cv.vline(x + bw, sy - bh, sy - 1, R(col)[1])
                    cv.px(x, sy - bh + 2, R('gold')[2])
                    x += bw + 1
                elif kind == 'potions':
                    col = rnd.choice(['ruby', 'magic_blue', 'poison', 'magic_purple', 'gold'])
                    cv.rect(x, sy - 4, x + 2, sy - 1, R(col)[2]); cv.px(x, sy - 4, R(col)[3])
                    cv.px(x + 1, sy - 5, R('glass')[3]); cv.px(x + 1, sy - 6, R('wood')[2])
                    x += 4
                elif kind == 'pantry':
                    c = rnd.choice(['jar', 'sack', 'cheese'])
                    if c == 'jar':
                        cv.rect(x, sy - 5, x + 3, sy - 1, R('glass')[2]); cv.rect(x, sy - 3, x + 3, sy - 1, R('cloth_orange')[2]); cv.hline(x, x + 3, sy - 6, R('cloth_red')[2])
                    elif c == 'sack':
                        cv.shade(cv.mask_ellipse(x + 2, sy - 3, 2.5, 3), 'cloth_tan')
                    else:
                        cv.rect(x, sy - 3, x + 3, sy - 1, R('cloth_yellow')[2]); cv.px(x + 1, sy - 2, R('cloth_yellow')[0])
                    x += 5
                elif kind == 'servers':
                    cv.rect(x, sy - 7, x1 - 4, sy - 1, R('tech_dark')[1])
                    for lx in range(x + 1, x1 - 5, 2):
                        cv.px(lx, sy - 5, R(rnd.choice(['neon_green', 'neon_cyan', 'ruby']))[3 if rnd.random() < .5 else 1])
                    cv.hline(x + 1, x1 - 5, sy - 3, R('tech')[2])
                    break
                elif kind == 'display':
                    col = rnd.choice(['ruby', 'emerald', 'crystal', 'gold'])
                    cv.shade(cv.mask_ellipse(x + 2, sy - 3, 2, 2.5), col)
                    x += 6
        if kind == 'display':
            gl = cv.mask_rect(x0 + 2, 6, x1 - 2, h - 7)
            cv.img[gl & ((np.mgrid[0:h, 0:32][1] + np.mgrid[0:h, 0:32][0]) % 9 == 0)] = rgba(R('glass')[3])
        shadow(cv, x0, x1, h - 3)
        return done(cv)
    return fn


def rack(kind='weapons'):
    def fn():
        cv = Canvas(32, 32)
        if kind == 'weapons':
            block(cv, 3, 4, 28, 8, 2, 'wood')
            legs(cv, [4, 26], 8, 27, 'wood')
            cv.hline(3, 28, 24, R('wood')[1])
            for i, (col, x) in enumerate([('steel', 8), ('iron', 13), ('steel', 18), ('wood_light', 23)]):
                cv.vline(x, 3, 25, R(col)[2]); cv.vline(x + 1, 3, 25, R(col)[1])
                cv.hline(x - 1, x + 2, 18 if i < 3 else 6, R('gold')[1])
        else:  # armor stand
            cv.rect(15, 6, 16, 27, R('wood')[1])
            cv.rect(10, 27, 21, 28, R('wood')[0])
            body = cv.mask_poly([(9, 8), (22, 8), (21, 20), (10, 20)])
            cv.shade(body, 'steel', depth=2)
            cv.shade(cv.mask_ellipse(16, 5, 4, 4), 'steel')
            cv.hline(12, 19, 5, OUTLINE)
            for x0 in (6, 22):
                cv.shade(cv.mask_ellipse(x0 + 2, 9, 3, 2.5), 'steel')
        shadow(cv, 6, 25, 29)
        return done(cv)
    return fn


def wardrobe(wood, h=64, kind='wardrobe'):
    def fn():
        cv = Canvas(32, h)
        block(cv, 2, 3, 29, h - 4, 4, wood)
        if kind == 'wardrobe':
            cv.vline(15, 8, h - 6, R(wood)[0]); cv.vline(16, 8, h - 6, R(wood)[2])
            cv.rect(13, h // 2, 13, h // 2 + 2, R('gold')[2]); cv.rect(18, h // 2, 18, h // 2 + 2, R('gold')[2])
            for x0, x1 in ((5, 12), (19, 26)):
                cv.rect(x0, 11, x1, h // 2 - 4, R(wood)[0]); cv.rect(x0, h // 2 + 5, x1, h - 9, R(wood)[0])
        else:  # dresser / fridge / locker
            n = 3
            for i in range(n):
                y = 9 + i * ((h - 14) // n)
                cv.hline(4, 27, y, R(wood)[0])
                cv.rect(14, y + 3, 17, y + 3, R('gold' if kind == 'dresser' else 'tech_light')[2])
            if kind == 'dresser':
                cv.shade(cv.mask_ellipse(9, 4, 3, 2), 'cloth_white')
        shadow(cv, 2, 29, h - 3)
        return done(cv)
    return fn


def crate(kind='wood'):
    def fn():
        cv = Canvas(32, 32)
        if kind == 'stack':
            for (x, y) in [(2, 14), (15, 14), (8, 2)]:
                block(cv, x, y, x + 14, y + 14, 5, 'wood')
                cv.line(x + 1, y + 6, x + 13, y + 13, R('wood')[0])
            shadow(cv, 2, 29, 29)
            return done(cv)
        ramp = {'wood': 'wood', 'reinforced': 'wood_dark', 'apples': 'wood_light', 'tech': 'tech', 'cargo': 'cloth_orange', 'fish': 'wood'}[kind]
        top, frt = block(cv, 4, 6, 27, 27, 8, ramp, grain=(kind in ('wood', 'apples', 'fish')))
        if kind in ('wood', 'reinforced', 'apples', 'fish'):
            cv.line(5, 15, 26, 26, R(ramp)[0]); cv.line(5, 16, 26, 27, R(ramp)[2])
            cv.rect(4, 14, 27, 14, R(ramp)[0])
            if kind == 'reinforced':
                for (x, y) in [(4, 14), (26, 14), (4, 26), (26, 26)]:
                    cv.rect(x - 0, y - 1, x + 1, y, R('iron')[2])
                cv.hline(4, 27, 20, R('iron')[1])
        if kind in ('apples', 'fish'):
            yy, xx = np.mgrid[0:32, 0:32]
            for (ax, ay) in [(8, 9), (12, 8), (16, 10), (20, 8), (24, 10), (10, 11), (18, 11), (22, 12)]:
                if kind == 'apples':
                    cv.shade(cv.mask_ellipse(ax, ay, 2, 1.8), 'cloth_red')
                else:
                    cv.shade(cv.mask_ellipse(ax, ay, 2.5, 1.2), 'silver')
                    cv.px(ax + 2, ay, R('silver')[1])
        if kind == 'tech':
            cv.rect(6, 18, 25, 19, R('warning')[2])
            cv.rect(13, 21, 18, 24, R('tech_dark')[1]); cv.px(15, 22, R('neon_green')[3])
            cv.hline(5, 26, 7, R('tech_light')[2])
        if kind == 'cargo':
            for x in range(6, 26, 3):
                cv.vline(x, 15, 26, R(ramp)[0])
            cv.rect(8, 8, 23, 11, R('cloth_white')[2])
        shadow(cv, 4, 27, 29)
        return done(cv)
    return fn


def barrel(kind='wood'):
    def fn():
        cv = Canvas(32, 32)
        if kind == 'keg':
            body = cv.mask_ellipse(16, 18, 12, 8)
            cv.shade_cyl(body, 'wood', axis='y')
            for x in (8, 23):
                cv.img[body & (abs(np.mgrid[0:32, 0:32][1] - x) < 1)] = rgba(R('iron')[1])
            end = cv.mask_ellipse(27, 18, 2.5, 7)
            cv.shade(end, 'wood_light')
            cv.rect(28, 17, 30, 18, R('bronze')[2])
            legs(cv, [8, 22], 25, 28, 'wood_dark')
            shadow(cv, 5, 27, 29)
            return done(cv)
        ramp = {'wood': 'wood', 'water': 'wood', 'oil': 'cloth_blue', 'toxic': 'warning', 'open': 'wood_light', 'fire': 'iron'}[kind]
        body = cv.mask_rect(7, 9, 24, 27) | cv.mask_ellipse(15.5, 27, 9, 2.5)
        body &= ~(cv.mask_rect(7, 9, 7, 11) | cv.mask_rect(24, 9, 24, 11) | cv.mask_rect(7, 26, 7, 28) | cv.mask_rect(24, 26, 24, 28))
        body |= cv.mask_rect(6, 13, 25, 23)
        cv.shade_cyl(body, ramp)
        top = cv.mask_ellipse(15.5, 9, 8.5, 3)
        cv.fill(top, ramp, 2)
        cv.img[top & ~cv.mask_ellipse(15.5, 9, 7, 2.2)] = rgba(R(ramp)[3])
        if kind in ('wood', 'water', 'open'):
            for y in (12, 23):
                cv.img[body & (np.mgrid[0:32, 0:32][0] == y)] = rgba(R('iron')[1])
                cv.img[body & (np.mgrid[0:32, 0:32][0] == y + 1)] = rgba(R('iron')[0])
        else:
            for y in (14, 21):
                cv.img[body & (np.mgrid[0:32, 0:32][0] == y)] = rgba(R(ramp)[0])
        inner = cv.mask_ellipse(15.5, 9, 7, 2.2)
        if kind == 'water':
            cv.fill(inner, 'water', 2); cv.px(12, 9, R('water')[3])
        elif kind == 'open':
            cv.fill(inner, 'wood_dark', 0)
            for (x, y) in [(12, 7), (16, 8), (19, 7)]:
                cv.shade(cv.mask_ellipse(x, y, 2, 1.6), 'poison')
        elif kind == 'toxic':
            cv.fill(inner, 'tech_dark', 1)
            cv.shade(cv.mask_ellipse(15.5, 18, 3, 3), 'cloth_black')
            cv.px(15, 18, R('warning')[3])
            cv.px(9, 27, R('poison')[3]); cv.px(10, 28, R('poison')[2])
        elif kind == 'oil':
            cv.fill(inner, 'tech', 1)
            cv.rect(10, 17, 21, 19, R('cloth_white')[2])
        elif kind == 'fire':
            cv.fill(inner, 'fire', 1)
            fl = cv.mask_poly([(9, 9), (12, 1), (14, 6), (16, 0), (18, 5), (21, 2), (23, 9)])
            cv.shade(fl, 'fire', base=2)
        shadow(cv, 6, 25, 30)
        return done(cv)
    return fn


# ----------------------------------------------------------------- tech
def computer(kind='crt'):
    def fn():
        w = 64 if kind in ('holo_desk', 'workstation') else 32
        cv = Canvas(w, 32)
        if kind == 'crt':
            legs(cv, [5, 25], 20, 28, 'wood')
            block(cv, 3, 14, 28, 20, 4, 'wood')
            block(cv, 8, 3, 23, 15, 3, 'cloth_tan')
            cv.fill(cv.mask_rect(10, 7, 21, 13), 'screen', 1)
            cv.hline(11, 17, 9, R('screen')[3]); cv.hline(11, 15, 11, R('screen')[2])
            cv.rect(7, 16, 18, 17, R('cloth_tan')[1])
        elif kind == 'terminal':
            block(cv, 5, 2, 26, 28, 4, 'tech')
            cv.fill(cv.mask_rect(8, 8, 23, 17), 'screen', 1)
            for i, y in enumerate((10, 12, 14)):
                cv.hline(9, 9 + [12, 8, 10][i], y, R('screen')[3 if i == 0 else 2])
            cv.rect(8, 20, 23, 24, R('tech_dark')[1])
            for x in range(9, 23, 2):
                cv.px(x, 21, R('tech_light')[2]); cv.px(x, 23, R('tech_light')[1])
        elif kind == 'laptop':
            legs(cv, [5, 25], 20, 28, 'wood_dark')
            block(cv, 3, 14, 28, 20, 4, 'wood_dark')
            block(cv, 9, 6, 22, 14, 1, 'tech_light')
            cv.fill(cv.mask_rect(10, 7, 21, 13), 'glass', 2)
            cv.rect(9, 15, 22, 17, R('tech_light')[1])
            cv.shade(cv.mask_ellipse(25, 15, 1.5, 1.2), 'cloth_white')
        elif kind == 'retro':
            block(cv, 4, 8, 27, 27, 5, 'cloth_tan')
            cv.fill(cv.mask_rect(7, 14, 18, 24), 'tech_dark', 0)
            cv.hline(8, 14, 16, R('neon_green')[2]); cv.hline(8, 12, 18, R('neon_green')[1])
            cv.rect(21, 15, 25, 16, R('cloth_tan')[0]); cv.rect(21, 19, 25, 20, R('cloth_tan')[0])
            cv.px(24, 23, R('ruby')[3])
        elif kind == 'holo_desk':
            legs(cv, [6, 56], 22, 28, 'tech')
            block(cv, 3, 14, 60, 22, 5, 'tech_light')
            cv.hline(4, 59, 20, R('neon_cyan')[2])
            holo = cv.mask_poly([(14, 15), (50, 15), (46, 3), (18, 3)])
            yy, xx = np.mgrid[0:32, 0:64]
            cv.img[holo & ((yy % 2 == 0) | (xx % 6 == 0))] = (90, 220, 240, 150)
            cv.hline(22, 40, 6, R('neon_cyan')[3]); cv.hline(22, 34, 9, R('neon_cyan')[3])
        elif kind == 'workstation':
            legs(cv, [5, 57], 22, 28, 'tech')
            block(cv, 3, 15, 60, 22, 5, 'tech')
            for x0 in (6, 24, 42):
                block(cv, x0, 3, x0 + 15, 14, 2, 'tech_dark')
                cv.fill(cv.mask_rect(x0 + 2, 6, x0 + 13, 12), 'screen', 1)
                cv.hline(x0 + 3, x0 + 10, 8, R('screen')[3])
            cv.rect(20, 17, 42, 19, R('tech_dark')[1])
        shadow(cv, 3, w - 4, 30)
        return done(cv)
    return fn


def console(kind='control'):
    def fn():
        w = 64 if kind in ('control', 'nav') else 32
        h = 64 if kind == 'hologram' else 32
        cv = Canvas(w, h)
        yy, xx = np.mgrid[0:h, 0:w]
        if kind in ('control', 'nav'):
            body = cv.mask_poly([(4, 10), (w - 5, 10), (w - 3, 27), (2, 27)])
            cv.shade(body, 'tech', depth=2)
            panel = cv.mask_poly([(6, 11), (w - 7, 11), (w - 5, 19), (4, 19)])
            cv.fill(panel, 'tech_dark', 1)
            import random
            rnd = random.Random(1 if kind == 'control' else 2)
            for x in range(8, w - 8, 3):
                cv.px(x, 13, R(rnd.choice(['ruby', 'neon_green', 'warning', 'neon_cyan']))[3])
                cv.px(x + 1, 16, R(rnd.choice(['ruby', 'neon_green', 'warning', 'neon_cyan']))[2])
            if kind == 'nav':
                cv.fill(cv.mask_ellipse(w / 2, 6, 10, 4), 'screen', 1)
                cv.img[cv.mask_ellipse(w / 2, 6, 10, 4) & ((xx + yy) % 4 == 0)] = rgba(R('screen')[3])
            else:
                for x0 in (10, 28, 44):
                    cv.fill(cv.mask_rect(x0, 2, x0 + 10, 9), 'screen', 1)
                    cv.hline(x0 + 1, x0 + 7, 4, R('screen')[3])
                    cv.rect(x0 + 4, 9, x0 + 6, 10, R('tech')[0])
        elif kind == 'reactor':
            base = cv.mask_ellipse(16, 25, 12, 5)
            cv.shade(base, 'tech_dark')
            core = cv.mask_rect(10, 4, 21, 25)
            cv.shade_cyl(core, 'glass')
            inner = cv.mask_rect(13, 6, 18, 23)
            cv.fill(inner, 'neon_cyan', 2)
            cv.img[inner & (yy % 4 == 0)] = rgba(R('neon_cyan')[3])
            for y in (4, 14, 24):
                cv.hline(9, 22, y, R('tech')[2])
        elif kind == 'wall_panel':
            block(cv, 4, 3, 27, 27, 2, 'tech_light')
            cv.fill(cv.mask_rect(7, 7, 24, 14), 'screen', 1)
            cv.line(8, 12, 12, 9, R('screen')[3]); cv.line(12, 9, 16, 11, R('screen')[3]); cv.line(16, 11, 22, 8, R('screen')[3])
            for i, c in enumerate(['ruby', 'warning', 'neon_green']):
                cv.rect(8 + i * 5, 18, 10 + i * 5, 20, R(c)[2])
            cv.rect(8, 23, 23, 24, R('tech')[1])
        elif kind == 'hologram':
            base = cv.mask_ellipse(16, 56, 11, 4)
            cv.shade(base, 'tech')
            cv.fill(cv.mask_ellipse(16, 55, 7, 2), 'neon_cyan', 3)
            beam = cv.mask_poly([(9, 55), (23, 55), (28, 10), (4, 10)])
            cv.img[beam & ((yy % 3) == 0)] = (90, 220, 240, 110)
            planet = cv.mask_ellipse(16, 22, 8, 8)
            cv.img[planet] = (110, 230, 250, 200)
            cv.img[planet & ((xx + yy) % 5 == 0)] = (200, 250, 255, 230)
            ring = cv.mask_ellipse(16, 22, 13, 3) & ~cv.mask_ellipse(16, 22, 11, 2) & ~(planet & (yy < 22))
            cv.img[ring] = (150, 240, 255, 210)
        elif kind == 'comms':
            block(cv, 5, 10, 26, 28, 4, 'tech')
            cv.fill(cv.mask_rect(8, 15, 23, 21), 'screen', 1)
            for x in range(9, 23, 2):
                hgt = int(2 + 2 * abs(math.sin(x)))
                cv.vline(x, 20 - hgt, 20, R('screen')[3])
            cv.vline(22, 1, 10, R('tech_light')[2]); cv.px(22, 0, R('ruby')[3])
            cv.shade(cv.mask_ellipse(12, 7, 4, 2), 'tech_light')
        shadow(cv, 2, w - 3, h - 2)
        return done(cv)
    return fn


# ----------------------------------------------------------------- decorations
def plant(pot='cloth_orange', kind='bush'):
    def fn():
        cv = Canvas(32, 32)
        potm = cv.mask_poly([(10, 19), (21, 19), (20, 28), (11, 28)])
        cv.shade_cyl(potm, pot)
        cv.hline(9, 22, 19, R(pot)[3]); cv.hline(9, 22, 20, R(pot)[2])
        cv.fill(cv.mask_rect(11, 18, 20, 18), 'dirt', 0)
        if kind == 'bush':
            for (x, y, r) in [(16, 11, 6), (11, 14, 4), (21, 14, 4), (16, 7, 4)]:
                cv.shade(cv.mask_ellipse(x, y, r, r), 'leaf')
        elif kind == 'flower':
            for (x, y) in [(13, 11), (19, 9), (16, 14)]:
                cv.line(16, 18, x, y, R('leaf')[2])
            for (x, y, c) in [(13, 10, 'cloth_pink'), (19, 8, 'cloth_yellow'), (16, 13, 'cloth_red')]:
                cv.shade(cv.mask_ellipse(x, y, 2.4, 2.4), c)
                cv.px(x, y, R('cloth_yellow')[3])
        elif kind == 'cactus':
            cv.shade_cyl(cv.mask_rect(13, 4, 18, 18), 'grass')
            cv.shade_cyl(cv.mask_rect(8, 9, 11, 14), 'grass'); cv.rect(10, 13, 13, 14, R('grass')[1])
            cv.shade_cyl(cv.mask_rect(20, 7, 23, 12), 'grass'); cv.rect(18, 11, 21, 12, R('grass')[1])
            cv.px(15, 3, R('cloth_pink')[3])
        elif kind == 'fern':
            for a in range(-60, 61, 30):
                r = math.radians(a - 90)
                cv.line(16, 18, 16 + math.cos(r) * 11, 18 + math.sin(r) * 11, R('grass')[2], width=2)
        elif kind == 'alien':
            for i, (x, y) in enumerate([(12, 6), (16, 3), (20, 7)]):
                cv.line(16, 18, x, y, R('amethyst')[2], width=2)
                cv.shade(cv.mask_ellipse(x, y, 2.2, 2.2), 'neon_cyan')
        shadow(cv, 10, 21, 29)
        return done(cv)
    return fn


def rug(a, b, w=64, h=32, kind='rect'):
    def fn():
        cv = Canvas(w, h)
        yy, xx = np.mgrid[0:h, 0:w]
        if kind == 'round':
            m = cv.mask_ellipse(w / 2, h / 2, w / 2 - 2, h / 2 - 2)
        else:
            m = cv.mask_rect(2, 2, w - 3, h - 3)
        cv.fill(m, a, 1)
        inner = cv.mask_ellipse(w / 2, h / 2, w / 2 - 6, h / 2 - 6) if kind == 'round' else cv.mask_rect(5, 5, w - 6, h - 6)
        cv.fill(inner, a, 2)
        border = m & ~(cv.mask_ellipse(w / 2, h / 2, w / 2 - 4, h / 2 - 4) if kind == 'round' else cv.mask_rect(4, 4, w - 5, h - 5))
        cv.fill(border, b, 2)
        if kind == 'rect':
            diamond = (abs(xx - w / 2) / (w / 2 - 10) + abs(yy - h / 2) / (h / 2 - 8)) <= 1
            cv.img[diamond & inner] = rgba(R(b)[1])
            cv.img[diamond & inner & ((xx + yy) % 4 == 0)] = rgba(R(a)[3])
            for x in range(2, w - 2, 2):
                cv.px(x, 1, R(b)[1]); cv.px(x, h - 2, R(b)[1])
        elif kind == 'stripes':
            cv.img[inner & (yy % 6 < 2)] = rgba(R(b)[1])
        elif kind == 'round':
            cv.img[cv.mask_ellipse(w / 2, h / 2, 6, 4)] = rgba(R(b)[2])
        elif kind == 'fur':
            cv.img[m & ((xx * 3 + yy * 5) % 7 == 0)] = rgba(R(a)[3])
        return cv
    return fn


def wall_decor(kind, col='cloth_red'):
    def fn():
        cv = Canvas(32, 32)
        if kind == 'painting':
            block(cv, 4, 6, 27, 25, 1, 'gold')
            art = cv.mask_rect(6, 8, 25, 23)
            cv.fill(art, 'cloth_blue', 2)
            cv.fill(art & cv.mask_rect(6, 17, 25, 23), 'grass', 2)
            cv.shade(cv.mask_ellipse(20, 11, 2, 2), 'cloth_yellow')
            cv.fill(cv.mask_poly([(8, 18), (13, 11), (18, 18)]), 'stone', 2)
        elif kind == 'portrait':
            block(cv, 7, 3, 24, 28, 1, 'wood_dark')
            cv.fill(cv.mask_rect(9, 5, 22, 26), 'cloth_crimson', 0)
            cv.shade(cv.mask_ellipse(15.5, 12, 4, 4.5), 'skin_light')
            cv.shade(cv.mask_rect(10, 18, 21, 26), col)
            cv.px(14, 12, INK); cv.px(17, 12, INK)
        elif kind == 'banner':
            cv.hline(5, 26, 3, R('wood')[1]); cv.hline(5, 26, 4, R('wood')[0])
            m = cv.mask_poly([(8, 4), (23, 4), (23, 27), (15.5, 23), (8, 27)])
            cv.shade(m, col, depth=2)
            cv.shade(cv.mask_ellipse(15.5, 13, 3.5, 3.5), 'gold')
            cv.px(15, 13, R(col)[0])
        elif kind == 'clock':
            cv.shade(cv.mask_ellipse(16, 15, 10, 10), 'wood')
            cv.fill(cv.mask_ellipse(16, 15, 8, 8), 'cloth_white', 2)
            cv.line(16, 15, 16, 9, INK); cv.line(16, 15, 20, 15, INK)
            for a in range(0, 360, 90):
                cv.px(16 + math.cos(math.radians(a)) * 7, 15 + math.sin(math.radians(a)) * 7, INK)
        elif kind == 'mirror':
            cv.shade(cv.mask_ellipse(16, 15, 9, 12), 'gold')
            gl = cv.mask_ellipse(16, 15, 7, 10)
            cv.fill(gl, 'glass', 2)
            cv.line(11, 12, 14, 7, R('glass')[3]); cv.line(12, 16, 17, 9, R('glass')[3])
        elif kind == 'trophy':
            cv.shade(cv.mask_poly([(10, 6), (22, 6), (20, 24), (12, 24)]), 'wood_dark')
            head = cv.mask_ellipse(16, 13, 5, 5)
            cv.shade(head, 'cloth_brown')
            for s in (-1, 1):
                cv.line(16 + s * 4, 10, 16 + s * 10, 2, R('bone')[2]); cv.line(16 + s * 7, 6, 16 + s * 9, 7, R('bone')[2])
            cv.px(14, 13, INK); cv.px(18, 13, INK)
        elif kind == 'window':
            block(cv, 5, 4, 26, 26, 2, 'wood')
            gl = cv.mask_rect(7, 7, 24, 24)
            cv.fill(gl, 'glass', 2)
            cv.vline(15, 7, 24, R('wood')[1]); cv.hline(7, 24, 15, R('wood')[1])
            cv.line(9, 13, 13, 9, R('glass')[3])
        elif kind == 'neon_sign':
            block(cv, 2, 8, 29, 24, 1, 'tech_dark')
            for x in range(5, 27):
                if (x // 3) % 2 == 0:
                    cv.px(x, 12, R(col)[3]); cv.px(x, 13, R(col)[2])
            cv.hline(6, 25, 18, R('neon_cyan')[3]); cv.hline(6, 25, 19, R('neon_cyan')[2])
        return done(cv)
    return fn


def prop(kind):
    def fn():
        w, h = {'grandfather_clock': (32, 64), 'fireplace': (64, 64), 'stove': (32, 32), 'statue': (32, 64),
                'pillar': (32, 64), 'fountain': (64, 64), 'specimen_tank': (32, 64), 'vending': (32, 64),
                'arcade': (32, 64), 'piano': (64, 32), 'bookstack': (32, 32), 'telescope': (32, 64),
                'lamp_post': (32, 64), 'floor_lamp': (32, 64), 'coat_rack': (32, 64)}.get(kind, (32, 32))
        cv = Canvas(w, h)
        yy, xx = np.mgrid[0:h, 0:w]
        if kind == 'chest':
            block(cv, 5, 9, 26, 26, 7, 'wood')
            cv.rect(5, 15, 26, 16, R('gold')[1]); cv.rect(14, 15, 17, 19, R('gold')[2]); cv.px(15, 17, INK)
            cv.vline(9, 9, 26, R('gold')[1]); cv.vline(22, 9, 26, R('gold')[1])
        elif kind == 'gold_chest':
            block(cv, 5, 9, 26, 26, 7, 'gold')
            cv.rect(5, 15, 26, 16, R('ruby')[1]); cv.rect(14, 15, 17, 19, R('ruby')[2])
            for x in (8, 12, 20): cv.px(x, 10, R('gold')[3])
        elif kind == 'locker':
            block(cv, 5, 9, 26, 26, 7, 'tech')
            cv.rect(5, 15, 26, 16, R('warning')[2]); cv.rect(13, 18, 18, 21, R('tech_dark')[1]); cv.px(15, 19, R('neon_green')[3])
        elif kind == 'candelabra':
            cv.rect(15, 10, 16, 26, R('gold')[2]); cv.rect(11, 26, 20, 28, R('gold')[1])
            cv.line(9, 12, 22, 12, R('gold')[1])
            for x in (9, 15, 21):
                cv.rect(x, 6, x + 1, 11, R('cloth_white')[2]); cv.px(x, 5, R('fire')[3]); cv.px(x, 4, R('fire')[2])
        elif kind == 'candles':
            for (x, hh) in [(10, 8), (15, 11), (20, 6)]:
                cv.rect(x, 26 - hh, x + 2, 26, R('cloth_white')[2]); cv.px(x + 1, 25 - hh, R('fire')[3]); cv.px(x + 1, 24 - hh, R('fire')[2])
            cv.fill(cv.mask_ellipse(16, 27, 9, 2), 'cloth_white', 1)
        elif kind == 'vase':
            m = cv.mask_ellipse(16, 20, 7, 8) | cv.mask_rect(13, 6, 18, 14)
            cv.shade_cyl(m, 'cloth_blue')
            cv.img[m & (yy == 17)] = rgba(R('cloth_white')[2])
            cv.hline(12, 19, 6, R('cloth_blue')[3])
        elif kind == 'amphora':
            m = cv.mask_ellipse(16, 18, 8, 9) | cv.mask_rect(13, 4, 18, 10)
            cv.shade_cyl(m, 'cloth_orange')
            cv.img[m & (yy % 5 == 0)] = rgba(R('cloth_black')[2])
            for s in (-1, 1):
                cv.line(16 + s * 3, 6, 16 + s * 7, 11, R('cloth_orange')[1])
        elif kind == 'stove':
            block(cv, 4, 6, 27, 28, 8, 'iron')
            for x in (9, 20):
                cv.fill(cv.mask_ellipse(x, 10, 3.5, 2), 'tech_dark', 1)
            cv.fill(cv.mask_rect(8, 17, 23, 25), 'tech_dark', 0)
            cv.fill(cv.mask_rect(10, 20, 21, 24), 'fire', 2)
            cv.img[cv.mask_rect(10, 20, 21, 24) & (xx % 2 == 0)] = rgba(R('fire')[3])
        elif kind == 'fireplace':
            block(cv, 2, 4, 61, 60, 4, 'brick')
            cv.img[cv.mask_rect(2, 8, 61, 60) & ((yy % 6 == 0) | (((xx + (yy // 6) * 5) % 10 == 0)))] = rgba(R('brick')[0])
            cv.fill(cv.mask_rect(14, 26, 49, 60), 'stone_dark', 0)
            cv.fill(cv.mask_ellipse(31.5, 26, 18, 8) & (yy < 26), 'stone_dark', 0)
            block(cv, 0, 18, 63, 23, 3, 'stone')
            for i, x in enumerate((22, 28, 34, 40)):
                cv.rect(x - 4, 55, x + 4, 57, R('wood')[1])
            fl = cv.mask_poly([(18, 56), (24, 38), (28, 46), (32, 32), (36, 46), (40, 40), (46, 56)])
            cv.shade(fl, 'fire', base=2)
            cv.fill(cv.mask_poly([(25, 56), (30, 44), (34, 50), (38, 56)]), 'fire', 3)
        elif kind == 'anvil':
            m = cv.mask_poly([(4, 10), (27, 10), (27, 14), (21, 16), (20, 21), (24, 26), (8, 26), (12, 21), (11, 16), (4, 13)])
            cv.shade(m, 'iron', depth=2)
            cv.hline(4, 27, 10, R('iron')[3])
            block(cv, 8, 25, 23, 29, 2, 'wood_dark')
        elif kind == 'cauldron':
            m = cv.mask_ellipse(16, 20, 11, 8)
            cv.shade(m, 'stone_dark', depth=2)
            cv.fill(cv.mask_ellipse(16, 14, 10, 3), 'poison', 2)
            cv.img[cv.mask_ellipse(16, 14, 10, 3) & ((xx + yy) % 4 == 0)] = rgba(R('poison')[3])
            for (x, y) in [(12, 9), (18, 6), (15, 3)]:
                cv.shade(cv.mask_ellipse(x, y, 1.6, 1.6), 'poison')
            for x in (8, 23):
                cv.rect(x, 26, x + 1, 29, R('stone_dark')[1])
        elif kind == 'sack':
            m = cv.mask_ellipse(16, 20, 9, 9) | cv.mask_poly([(12, 12), (20, 12), (18, 7), (14, 7)])
            cv.shade(m, 'cloth_tan', depth=2)
            cv.hline(13, 19, 11, R('leather')[1])
            cv.rect(12, 18, 19, 22, R('cloth_tan')[1]); cv.px(14, 19, R('cloth_brown')[1]); cv.px(17, 19, R('cloth_brown')[1])
        elif kind == 'grain_sacks':
            for (x, y) in [(10, 21), (22, 21), (16, 12)]:
                m = cv.mask_ellipse(x, y, 7, 6)
                cv.shade(m, 'cloth_tan')
        elif kind == 'hay':
            block(cv, 3, 8, 28, 27, 8, 'thatch')
            cv.img[cv.mask_rect(3, 8, 28, 27) & ((xx * 2 + yy * 3) % 5 == 0)] = rgba(R('thatch')[1])
            cv.vline(10, 8, 27, R('leather')[1]); cv.vline(21, 8, 27, R('leather')[1])
        elif kind == 'firewood':
            for row in range(3):
                for i in range(4 - row % 2):
                    x = 6 + i * 6 + (3 if row % 2 else 0); y = 24 - row * 6
                    cv.shade(cv.mask_ellipse(x, y, 3, 3), 'wood')
                    cv.fill(cv.mask_ellipse(x, y, 1.6, 1.6), 'wood_light', 2)
        elif kind == 'grandfather_clock':
            block(cv, 7, 2, 24, 60, 3, 'wood_dark')
            cv.fill(cv.mask_ellipse(15.5, 13, 6, 6), 'cloth_white', 2)
            cv.line(15, 13, 15, 9, INK); cv.line(15, 13, 18, 13, INK)
            gl = cv.mask_rect(10, 24, 21, 52)
            cv.fill(gl, 'wood_dark', 0)
            cv.vline(15, 25, 44, R('gold')[2]); cv.shade(cv.mask_ellipse(15.5, 46, 3, 3), 'gold')
        elif kind == 'statue':
            block(cv, 6, 48, 25, 61, 4, 'stone')
            body = cv.mask_ellipse(15.5, 12, 5, 5) | cv.mask_poly([(9, 18), (22, 18), (24, 48), (7, 48)])
            cv.shade(body, 'stone_warm', depth=2)
            cv.line(22, 20, 27, 8, R('stone_warm')[1], width=2)
        elif kind == 'pillar':
            block(cv, 4, 2, 27, 8, 3, 'stone')
            cv.shade_cyl(cv.mask_rect(8, 9, 23, 54), 'stone')
            cv.img[cv.mask_rect(8, 9, 23, 54) & (xx % 4 == 0)] = rgba(R('stone')[1])
            block(cv, 4, 54, 27, 61, 3, 'stone')
        elif kind == 'fountain':
            basin = cv.mask_ellipse(32, 46, 28, 14)
            cv.shade(basin, 'stone', depth=2)
            water = cv.mask_ellipse(32, 44, 24, 10)
            cv.fill(water, 'water', 2)
            cv.img[water & ((xx + yy * 2) % 7 == 0)] = rgba(R('water')[3])
            cv.shade_cyl(cv.mask_rect(28, 14, 35, 44), 'stone')
            bowl = cv.mask_ellipse(32, 16, 10, 4)
            cv.shade(bowl, 'stone')
            cv.fill(cv.mask_ellipse(32, 15, 8, 2.5), 'water', 2)
            for s in (-1, 1):
                for i in range(10):
                    cv.px(32 + s * (8 + i * 1.2), 16 + i * i * 0.25, R('water')[3])
            cv.vline(32, 4, 13, R('water')[3]); cv.vline(31, 6, 13, R('water')[2])
        elif kind == 'specimen_tank':
            block(cv, 5, 54, 26, 61, 3, 'tech')
            gl = cv.mask_rect(7, 8, 24, 53)
            cv.fill(gl, 'neon_green', 1)
            cv.img[gl & (yy % 5 == 0) & (xx % 3 == 0)] = rgba(R('neon_green')[3])
            cv.shade(cv.mask_ellipse(15.5, 26, 5, 6) | cv.mask_rect(13, 30, 18, 42), 'amethyst')
            cv.px(14, 25, R('ruby')[3]); cv.px(17, 25, R('ruby')[3])
            cv.vline(8, 9, 52, R('glass')[3])
            block(cv, 5, 2, 26, 8, 3, 'tech')
        elif kind == 'vending':
            block(cv, 4, 4, 27, 61, 3, 'cloth_red')
            gl = cv.mask_rect(7, 10, 19, 44)
            cv.fill(gl, 'glass', 1)
            import random
            rnd = random.Random(3)
            for y in range(13, 44, 7):
                for x in range(8, 19, 4):
                    cv.rect(x, y, x + 2, y + 3, R(rnd.choice(['cloth_yellow', 'cloth_blue', 'cloth_green', 'cloth_orange']))[2])
            cv.rect(21, 14, 25, 30, R('tech_dark')[1]); cv.px(23, 16, R('neon_green')[3])
            cv.rect(8, 49, 19, 55, R('tech_dark')[0])
        elif kind == 'arcade':
            block(cv, 5, 4, 26, 61, 3, 'cloth_purple')
            cv.fill(cv.mask_rect(8, 10, 23, 24), 'tech_dark', 0)
            cv.hline(10, 15, 14, R('neon_pink')[3]); cv.rect(17, 18, 19, 20, R('neon_cyan')[3]); cv.px(12, 20, R('warning')[3])
            block(cv, 4, 28, 27, 34, 3, 'cloth_purple')
            cv.rect(9, 29, 10, 30, R('ruby')[3]); cv.rect(17, 30, 18, 30, R('neon_cyan')[3]); cv.rect(21, 30, 22, 30, R('warning')[3])
            cv.fill(cv.mask_rect(7, 4, 24, 8), 'neon_pink', 2)
        elif kind == 'tv':
            block(cv, 3, 20, 28, 28, 3, 'wood_dark')
            block(cv, 4, 4, 27, 20, 1, 'cloth_black')
            cv.fill(cv.mask_rect(6, 6, 25, 18), 'glass', 1)
            cv.line(8, 10, 12, 7, R('glass')[3])
        elif kind == 'piano':
            block(cv, 2, 3, 61, 27, 10, 'cloth_black')
            keys = cv.mask_rect(6, 14, 57, 18)
            cv.fill(keys, 'cloth_white', 3)
            cv.img[keys & (xx % 3 == 0)] = rgba(R('cloth_white')[1])
            cv.img[cv.mask_rect(6, 14, 57, 15) & (xx % 6 < 2) & (xx % 6 >= 0) & (xx % 3 != 0)] = rgba(R('cloth_black')[0])
        elif kind == 'globe':
            cv.rect(15, 21, 16, 26, R('wood')[1]); cv.rect(10, 26, 21, 28, R('wood')[0])
            g = cv.mask_ellipse(16, 13, 8, 8)
            cv.fill(g, 'water', 2)
            cv.fill(g & ((cv.mask_ellipse(13, 10, 4, 3)) | cv.mask_ellipse(19, 16, 3, 4)), 'grass', 2)
            ring = cv.mask_ellipse(16, 13, 10, 10) & ~cv.mask_ellipse(16, 13, 9, 9) & (xx < 17)
            cv.img[ring] = rgba(R('gold')[2])
        elif kind == 'telescope':
            for (a, b) in [((16, 40), (8, 60)), ((16, 40), (24, 60)), ((16, 40), (16, 61))]:
                cv.line(a[0], a[1], b[0], b[1], R('wood')[1])
            tube = Canvas(w, h)
            tube.line(6, 46, 26, 12, R('bronze')[2], width=4)
            cv.paste(tube)
            cv.shade(cv.mask_ellipse(26, 13, 3.5, 3.5), 'gold')
        elif kind == 'lamp_post':
            cv.shade_cyl(cv.mask_rect(14, 14, 17, 58), 'iron')
            block(cv, 10, 57, 21, 61, 2, 'iron')
            head = cv.mask_rect(10, 4, 21, 14)
            cv.fill(head, 'fire', 3)
            cv.img[head & ((xx == 10) | (xx == 21) | (yy == 4) | (yy == 14) | (xx == 15))] = rgba(R('iron')[1])
            cv.fill(cv.mask_poly([(9, 4), (22, 4), (15.5, 0)]), 'iron', 1)
        elif kind == 'floor_lamp':
            cv.vline(15, 18, 58, R('gold')[1]); cv.vline(16, 18, 58, R('gold')[2])
            cv.fill(cv.mask_ellipse(16, 60, 6, 2), 'gold', 1)
            shade_m = cv.mask_poly([(10, 6), (21, 6), (25, 18), (6, 18)])
            cv.shade(shade_m, 'cloth_yellow')
            cv.img[shade_m & (yy == 17)] = rgba(R('cloth_yellow')[3])
        elif kind == 'neon_lamp':
            cv.vline(15, 8, 26, R('tech')[1])
            cv.fill(cv.mask_rect(13, 6, 18, 24), 'neon_pink', 2)
            cv.img[cv.mask_rect(15, 6, 16, 24)] = rgba(R('neon_pink')[3])
            block(cv, 10, 24, 21, 28, 2, 'tech_dark')
        elif kind == 'coat_rack':
            cv.vline(15, 6, 58, R('wood')[2]); cv.vline(16, 6, 58, R('wood')[1])
            for s in (-1, 1):
                cv.line(16, 8, 16 + s * 6, 5, R('wood')[1])
            cv.shade(cv.mask_poly([(18, 9), (24, 9), (25, 30), (17, 30)]), 'cloth_brown')
            cv.shade(cv.mask_ellipse(10, 9, 5, 2), 'cloth_red')
            cv.fill(cv.mask_ellipse(16, 60, 7, 2), 'wood', 1)
        elif kind == 'trash_bin':
            m = cv.mask_rect(9, 10, 22, 28)
            cv.shade_cyl(m, 'tech')
            cv.img[m & (xx % 3 == 0)] = rgba(R('tech')[0])
            cv.fill(cv.mask_ellipse(15.5, 10, 7, 2.5), 'tech_light', 2)
        elif kind == 'bookstack':
            import random
            rnd = random.Random(9)
            y = 27
            for i in range(5):
                bw = rnd.randint(14, 20); x0 = 16 - bw // 2 + rnd.randint(-2, 2)
                col = rnd.choice(['cloth_red', 'cloth_blue', 'cloth_green', 'cloth_brown', 'cloth_purple'])
                block(cv, x0, y - 4, x0 + bw, y, 2, col)
                cv.hline(x0 + 1, x0 + bw - 1, y - 1, R('cloth_white')[2])
                y -= 4
        elif kind == 'scroll_table':
            legs(cv, [6, 24], 19, 28, 'wood')
            block(cv, 4, 9, 27, 19, 7, 'wood')
            cv.fill(cv.mask_rect(8, 10, 22, 14), 'sand', 2)
            cv.line(10, 12, 20, 11, R('dirt')[1])
            cv.px(24, 11, R('cloth_black')[2]); cv.px(24, 10, R('cloth_white')[3])
        elif kind == 'well':
            base = cv.mask_ellipse(16, 22, 13, 8)
            cv.shade(base, 'cobble', depth=2)
            cv.fill(cv.mask_ellipse(16, 19, 9, 4), 'water_deep', 1)
            for x in (4, 26):
                cv.rect(x, 2, x + 1, 20, R('wood')[1])
            cv.fill(cv.mask_poly([(1, 4), (30, 4), (16, -4)]), 'roof_red', 2)
            cv.hline(5, 26, 7, R('wood')[0])
        shadow(cv, 4, w - 5, h - 2)
        return done(cv)
    return fn


FURNITURE = [
    # tables (9)
    ('table_wood', 'tables', 'Wooden Table', (32, 32), table('wood', items=[('mug', 9, 10), ('candle', 20, 11)])),
    ('table_round', 'tables', 'Round Table', (32, 32), table('wood_light', kind='round')),
    ('table_long', 'tables', 'Long Dining Table', (64, 32), table('wood', 64, cloth='cloth_white', items=[('plate', 10, 11), ('plate', 28, 11), ('plate', 46, 11), ('candle', 38, 11)])),
    ('table_tavern', 'tables', 'Tavern Table', (64, 32), table('wood_dark', 64, kind='tavern', items=[('mug', 12, 10), ('mug', 22, 12), ('mug', 44, 10)])),
    ('table_stone', 'tables', 'Stone Table', (32, 32), table('stone', kind='stone')),
    ('table_desk', 'tables', 'Writing Desk', (64, 32), table('wood', 64, kind='desk', items=[('book', 8, 10), ('candle', 20, 10), ('map', 30, 10)])),
    ('table_lab', 'tables', 'Lab Bench', (64, 32), table('tech_light', 64, kind='lab', items=[('flask', 10, 10), ('flask', 16, 11), ('flask', 40, 10)])),
    ('table_alchemy', 'tables', 'Alchemy Table', (32, 32), table('wood_dark', items=[('flask', 9, 10), ('book', 17, 11)])),
    ('table_banquet', 'tables', 'Royal Banquet Table', (64, 32), table('wood_dark', 64, cloth='cloth_crimson', items=[('plate', 12, 11), ('candle', 31, 10), ('plate', 44, 11)])),
    # beds (8)
    ('bed_single_red', 'beds', 'Single Bed (Red)', (32, 64), bed('wood', 'cloth_red')),
    ('bed_single_blue', 'beds', 'Single Bed (Blue)', (32, 64), bed('wood_light', 'cloth_blue')),
    ('bed_single_green', 'beds', 'Single Bed (Green)', (32, 64), bed('wood_dark', 'cloth_green')),
    ('bed_double', 'beds', 'Double Bed', (64, 64), bed('wood', 'cloth_teal', w=64)),
    ('bed_royal', 'beds', 'Royal Canopy Bed', (64, 64), bed('wood_dark', 'cloth_purple', w=64, kind='royal')),
    ('bed_straw', 'beds', 'Straw Bed', (32, 64), bed(kind='straw')),
    ('bed_medical', 'beds', 'Medical Bed', (32, 64), bed('tech_light', 'cloth_teal', kind='medical')),
    ('bed_cryopod', 'beds', 'Cryo Sleep Pod', (32, 64), bed(kind='pod')),
    ('bed_hammock', 'beds', 'Hammock', (32, 64), bed(sheet='cloth_tan', kind='hammock')),
    # seating (10)
    ('chair_wood', 'chairs', 'Wooden Chair', (32, 32), chair('wood')),
    ('chair_cushion', 'chairs', 'Cushioned Chair', (32, 32), chair('wood_dark', 'cloth_red')),
    ('chair_stool', 'chairs', 'Stool', (32, 32), chair('wood_light', kind='stool')),
    ('chair_bench', 'chairs', 'Bench', (64, 32), chair('wood', kind='bench')),
    ('chair_throne', 'chairs', 'Throne', (32, 32), chair(seat='cloth_crimson', kind='throne')),
    ('chair_armchair', 'chairs', 'Armchair', (32, 32), chair(seat='cloth_green', kind='armchair')),
    ('chair_office', 'chairs', 'Office Chair', (32, 32), chair(kind='office')),
    ('chair_scifi', 'chairs', 'Bridge Seat', (32, 32), chair(kind='scifi')),
    ('couch_red', 'chairs', 'Sofa (Red)', (64, 32), couch('cloth_red')),
    ('couch_blue', 'chairs', 'Sofa (Navy)', (64, 32), couch('cloth_navy')),
    # shelves & storage (12)
    ('shelf_books', 'shelves', 'Bookshelf', (32, 64), shelf('wood', 'books')),
    ('shelf_books_dark', 'shelves', 'Library Shelf', (32, 64), shelf('wood_dark', 'books')),
    ('shelf_potions', 'shelves', 'Potion Shelf', (32, 64), shelf('wood_dark', 'potions')),
    ('shelf_pantry', 'shelves', 'Pantry Shelf', (32, 64), shelf('wood_light', 'pantry')),
    ('shelf_display', 'shelves', 'Display Case', (32, 64), shelf('gold', 'display')),
    ('shelf_server', 'shelves', 'Server Rack', (32, 64), shelf('tech', 'servers')),
    ('shelf_low_books', 'shelves', 'Low Bookcase', (32, 32), shelf('wood', 'books', h=32)),
    ('rack_weapons', 'shelves', 'Weapon Rack', (32, 32), rack('weapons')),
    ('rack_armor', 'shelves', 'Armor Stand', (32, 32), rack('armor')),
    ('wardrobe_wood', 'shelves', 'Wardrobe', (32, 64), wardrobe('wood')),
    ('dresser_wood', 'shelves', 'Dresser', (32, 32), wardrobe('wood_light', h=32, kind='dresser')),
    ('fridge_scifi', 'shelves', 'Cryo Fridge', (32, 64), wardrobe('tech_light', kind='fridge')),
    # crates (6)
    ('crate_wood', 'crates', 'Wooden Crate', (32, 32), crate('wood')),
    ('crate_reinforced', 'crates', 'Reinforced Crate', (32, 32), crate('reinforced')),
    ('crate_apples', 'crates', 'Apple Crate', (32, 32), crate('apples')),
    ('crate_fish', 'crates', 'Fish Crate', (32, 32), crate('fish')),
    ('crate_tech', 'crates', 'Supply Crate', (32, 32), crate('tech')),
    ('crate_cargo', 'crates', 'Cargo Container', (32, 32), crate('cargo')),
    ('crate_stack', 'crates', 'Crate Stack', (32, 32), crate('stack')),
    # barrels (7)
    ('barrel_wood', 'barrels', 'Barrel', (32, 32), barrel('wood')),
    ('barrel_water', 'barrels', 'Water Barrel', (32, 32), barrel('water')),
    ('barrel_open', 'barrels', 'Pickle Barrel', (32, 32), barrel('open')),
    ('barrel_keg', 'barrels', 'Ale Keg', (32, 32), barrel('keg')),
    ('barrel_oil', 'barrels', 'Oil Drum', (32, 32), barrel('oil')),
    ('barrel_toxic', 'barrels', 'Toxic Barrel', (32, 32), barrel('toxic')),
    ('barrel_fire', 'barrels', 'Burning Drum', (32, 32), barrel('fire')),
    # computers (6)
    ('computer_crt', 'computers', 'CRT Computer Desk', (32, 32), computer('crt')),
    ('computer_terminal', 'computers', 'Data Terminal', (32, 32), computer('terminal')),
    ('computer_laptop', 'computers', 'Laptop Desk', (32, 32), computer('laptop')),
    ('computer_retro', 'computers', 'Retro Computer', (32, 32), computer('retro')),
    ('computer_holo_desk', 'computers', 'Holo Desk', (64, 32), computer('holo_desk')),
    ('computer_workstation', 'computers', 'Triple-Screen Workstation', (64, 32), computer('workstation')),
    # consoles (6)
    ('console_control', 'consoles', 'Control Console', (64, 32), console('control')),
    ('console_nav', 'consoles', 'Navigation Console', (64, 32), console('nav')),
    ('console_reactor', 'consoles', 'Reactor Core', (32, 32), console('reactor')),
    ('console_wall_panel', 'consoles', 'Wall Panel', (32, 32), console('wall_panel')),
    ('console_hologram', 'consoles', 'Hologram Projector', (32, 64), console('hologram')),
    ('console_comms', 'consoles', 'Comms Array', (32, 32), console('comms')),
    # decorations (52)
    ('plant_bush', 'decorations', 'Potted Bush', (32, 32), plant('cloth_orange', 'bush')),
    ('plant_flowers', 'decorations', 'Flower Pot', (32, 32), plant('cloth_blue', 'flower')),
    ('plant_cactus', 'decorations', 'Potted Cactus', (32, 32), plant('sandstone', 'cactus')),
    ('plant_fern', 'decorations', 'Fern', (32, 32), plant('stone', 'fern')),
    ('plant_alien', 'decorations', 'Alien Plant', (32, 32), plant('tech_light', 'alien')),
    ('rug_red', 'decorations', 'Red Carpet', (64, 32), rug('cloth_red', 'cloth_yellow')),
    ('rug_blue', 'decorations', 'Blue Rug', (64, 32), rug('cloth_blue', 'cloth_white', kind='stripes')),
    ('rug_round', 'decorations', 'Round Rug', (64, 32), rug('cloth_green', 'cloth_tan', kind='round')),
    ('rug_fur', 'decorations', 'Fur Rug', (64, 32), rug('cloth_brown', 'cloth_tan', kind='fur')),
    ('rug_royal', 'decorations', 'Royal Runner', (64, 32), rug('cloth_purple', 'gold')),
    ('painting_landscape', 'decorations', 'Landscape Painting', (32, 32), wall_decor('painting')),
    ('painting_portrait', 'decorations', 'Portrait', (32, 32), wall_decor('portrait', 'cloth_blue')),
    ('banner_red', 'decorations', 'Red Banner', (32, 32), wall_decor('banner', 'cloth_red')),
    ('banner_blue', 'decorations', 'Blue Banner', (32, 32), wall_decor('banner', 'cloth_blue')),
    ('banner_green', 'decorations', 'Green Banner', (32, 32), wall_decor('banner', 'cloth_green')),
    ('wall_clock', 'decorations', 'Wall Clock', (32, 32), wall_decor('clock')),
    ('wall_mirror', 'decorations', 'Mirror', (32, 32), wall_decor('mirror')),
    ('wall_trophy', 'decorations', 'Antler Trophy', (32, 32), wall_decor('trophy')),
    ('wall_window', 'decorations', 'Window', (32, 32), wall_decor('window')),
    ('wall_neon_sign', 'decorations', 'Neon Sign', (32, 32), wall_decor('neon_sign', 'neon_pink')),
    ('chest_wood', 'decorations', 'Wooden Chest', (32, 32), prop('chest')),
    ('chest_gold', 'decorations', 'Treasure Chest', (32, 32), prop('gold_chest')),
    ('chest_locker', 'decorations', 'Tech Locker', (32, 32), prop('locker')),
    ('candelabra', 'decorations', 'Candelabra', (32, 32), prop('candelabra')),
    ('candles', 'decorations', 'Candle Cluster', (32, 32), prop('candles')),
    ('vase_blue', 'decorations', 'Porcelain Vase', (32, 32), prop('vase')),
    ('vase_amphora', 'decorations', 'Amphora', (32, 32), prop('amphora')),
    ('stove_iron', 'decorations', 'Iron Stove', (32, 32), prop('stove')),
    ('fireplace', 'decorations', 'Fireplace', (64, 64), prop('fireplace')),
    ('anvil', 'decorations', 'Anvil', (32, 32), prop('anvil')),
    ('cauldron', 'decorations', 'Cauldron', (32, 32), prop('cauldron')),
    ('sack', 'decorations', 'Sack', (32, 32), prop('sack')),
    ('grain_sacks', 'decorations', 'Grain Sacks', (32, 32), prop('grain_sacks')),
    ('hay_bale', 'decorations', 'Hay Bale', (32, 32), prop('hay')),
    ('firewood', 'decorations', 'Firewood Pile', (32, 32), prop('firewood')),
    ('grandfather_clock', 'decorations', 'Grandfather Clock', (32, 64), prop('grandfather_clock')),
    ('statue_hero', 'decorations', 'Hero Statue', (32, 64), prop('statue')),
    ('pillar_stone', 'decorations', 'Stone Pillar', (32, 64), prop('pillar')),
    ('fountain', 'decorations', 'Fountain', (64, 64), prop('fountain')),
    ('specimen_tank', 'decorations', 'Specimen Tank', (32, 64), prop('specimen_tank')),
    ('vending_machine', 'decorations', 'Vending Machine', (32, 64), prop('vending')),
    ('arcade_cabinet', 'decorations', 'Arcade Cabinet', (32, 64), prop('arcade')),
    ('tv_set', 'decorations', 'TV Set', (32, 32), prop('tv')),
    ('piano', 'decorations', 'Piano', (64, 32), prop('piano')),
    ('globe', 'decorations', 'Globe', (32, 32), prop('globe')),
    ('telescope', 'decorations', 'Telescope', (32, 64), prop('telescope')),
    ('lamp_post', 'decorations', 'Street Lamp', (32, 64), prop('lamp_post')),
    ('floor_lamp', 'decorations', 'Floor Lamp', (32, 64), prop('floor_lamp')),
    ('neon_lamp', 'decorations', 'Neon Lamp', (32, 32), prop('neon_lamp')),
    ('coat_rack', 'decorations', 'Coat Rack', (32, 64), prop('coat_rack')),
    ('trash_bin', 'decorations', 'Trash Bin', (32, 32), prop('trash_bin')),
    ('book_stack', 'decorations', 'Book Stack', (32, 32), prop('bookstack')),
    ('scroll_table', 'decorations', 'Scroll Table', (32, 32), prop('scroll_table')),
    ('well', 'decorations', 'Well', (32, 32), prop('well')),
]
