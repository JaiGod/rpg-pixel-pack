"""62 equipment icons (32x32), drawn in a consistent 45-degree icon style."""
import math
import numpy as np

from .core import Canvas, R, rgba
from .palette import OUTLINE, INK


def diag(cv, x0, y0, n, width, ramp, light_first=True, start=0):
    """Bar going up-right from (x0, y0) for n steps, `width` px thick."""
    rr = R(ramp)
    for i in range(start, n):
        for w in range(width):
            if width == 1:
                c = rr[2]
            elif w == 0:
                c = rr[3] if light_first else rr[1]
            elif w == width - 1:
                c = rr[0] if width > 2 else rr[1]
            else:
                c = rr[2]
            cv.px(x0 + i + w, y0 - i, c)


def glow(cv, ramp, density=0.18, seed=1):
    import random
    rnd = random.Random(seed)
    a = cv.alpha
    from .core import _shift
    ring = ~a & (_shift(a, 0, 1) | _shift(a, 0, -1) | _shift(a, 1, 0) | _shift(a, -1, 0))
    ys, xs = np.nonzero(ring)
    for y, x in zip(ys, xs):
        if rnd.random() < density:
            cv.px(x, y, R(ramp)[3])


def sword(blade, guard='gold', grip='leather', fx=None, curved=False, length=17):
    cv = Canvas(32)
    gx, gy = 7, 25
    diag(cv, gx - 3, gy + 3, 4, 2, grip)                   # grip
    cv.rect(gx - 5, gy + 3, gx - 4, gy + 4, R(guard)[2])    # pommel
    cv.px(gx - 5, gy + 3, R(guard)[3])
    for s in range(-3, 4):                                   # crossguard
        cv.px(gx + 1 + s, gy - 0 + s, R(guard)[2 if s < 1 else 1])
        cv.px(gx + 2 + s, gy - 0 + s, R(guard)[1 if s < 1 else 0])
    diag(cv, gx + 2, gy - 2, length, 3, blade)
    tip = gx + 2 + length
    cv.px(tip, gy - 2 - length, R(blade)[3])
    cv.px(tip + 1, gy - 2 - length, R(blade)[2])
    # fuller
    for i in range(2, length - 3):
        cv.px(gx + 3 + i, gy - 2 - i, R(blade)[1] if fx != 'cyber' else R(blade)[3])
    if curved:
        for i in range(length - 6, length):
            cv.px(gx + 5 + i, gy - 2 - i + 1, R(blade)[1])
    cv.outline(OUTLINE)
    if fx:
        glow(cv, {'flame': 'fire', 'shadow': 'magic_purple', 'cyber': 'neon_pink', 'crystal': 'crystal', 'frost': 'ice'}[fx])
    return cv


def axe(head, shaft='wood', double=False, fx=None):
    cv = Canvas(32)
    diag(cv, 5, 28, 22, 2, shaft)
    cx, cy = 20, 10
    blade = cv.mask_poly([(cx - 1, cy - 2), (cx + 4, cy + 3), (cx + 9, cy + 1), (cx + 10, cy + 6), (cx + 6, cy + 11), (cx + 1, cy + 5)])
    if double:
        blade |= cv.mask_poly([(cx - 2, cy - 1), (cx - 7, cy - 6), (cx - 5, cy - 11), (cx, cy - 10), (cx + 3, cy - 3)])
    cv.shade(blade, head, depth=2)
    edge = blade & ~np.roll(blade, -1, axis=1) & ~np.roll(blade, 1, axis=0)
    cv.img[edge] = rgba(R(head)[3])
    cv.outline(OUTLINE)
    if fx:
        glow(cv, fx)
    return cv


def spear(head, shaft='wood_light', kind='spear'):
    cv = Canvas(32)
    diag(cv, 3, 29, 21, 2, shaft)
    tx, ty = 23, 8
    if kind == 'spear':
        m = cv.mask_poly([(tx - 2, ty + 2), (tx + 2, ty - 3), (tx + 7, ty - 7), (tx + 3, ty - 2), (tx - 1, ty + 3)])
        m |= cv.mask_poly([(tx - 1, ty + 1), (tx + 6, ty - 6), (tx + 2, ty + 2)])
        cv.shade(m, head)
        cv.rect(tx - 3, ty + 3, tx - 2, ty + 4, R('cloth_red')[2])
    elif kind == 'halberd':
        m = cv.mask_poly([(tx - 1, ty + 1), (tx + 6, ty - 6), (tx + 2, ty + 2)])
        m |= cv.mask_poly([(tx - 4, ty + 2), (tx + 2, ty + 8), (tx + 5, ty + 5), (tx + 1, ty + 1)])
        m |= cv.mask_poly([(tx - 3, ty - 1), (tx - 6, ty - 4), (tx - 1, ty - 2)])
        cv.shade(m, head, depth=2)
    elif kind == 'trident':
        for (ox, oy) in [(-4, -2), (0, 0), (2, 4)]:
            for i in range(6):
                cv.px(tx + ox + i, ty + oy - i, R(head)[2]); cv.px(tx + ox + i + 1, ty + oy - i, R(head)[1])
        diag(cv, tx - 4, ty + 3, 5, 2, head)
    elif kind == 'lance':
        m = cv.mask_poly([(tx - 5, ty + 5), (tx + 7, ty - 7), (tx + 1, ty + 7)])
        cv.shade(m, head)
        guard = cv.mask_ellipse(tx - 5, ty + 6, 3, 3)
        cv.shade(guard, 'gold')
    cv.outline(OUTLINE)
    return cv


def bow(wood, string='cloth_white', arrow=True, fx=None):
    cv = Canvas(32)
    p0, p1, p2 = (6, 4), (30, 4), (28, 27)
    p0, p2 = (5, 6), (26, 27)
    ctrl = (30, 2)
    pts = []
    for i in range(41):
        t = i / 40
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ctrl[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ctrl[1] + t * t * p2[1]
        pts.append((round(x), round(y)))
    for (x, y) in pts:
        cv.px(x, y, R(wood)[2]); cv.px(x + 1, y + 1, R(wood)[1])
    cv.px(*pts[20], R('leather')[1]); cv.px(pts[20][0] + 1, pts[20][1] + 1, R('leather')[0])
    cv.line(p0[0], p0[1], p2[0], p2[1], R(string)[1])
    if arrow:
        cv.line(6, 26, 24, 8, R('wood_light')[2])
        cv.rect(4, 26, 5, 28, R('cloth_red')[2]); cv.px(6, 28, R('cloth_red')[1])
        cv.px(25, 7, R('steel')[3]); cv.px(24, 7, R('steel')[2]); cv.px(25, 8, R('steel')[2])
    cv.outline(OUTLINE)
    if fx:
        glow(cv, fx)
    return cv


def crossbow(wood, metal='iron', fx=None):
    cv = Canvas(32)
    diag(cv, 4, 28, 20, 3, wood)
    cv.rect(3, 27, 6, 29, R(wood)[1])
    # limbs (perpendicular, near the front)
    for s in range(-9, 10):
        bend = abs(s) // 4
        cv.px(20 + s - bend, 12 + s + bend, R(metal)[2])
        cv.px(21 + s - bend, 12 + s + bend, R(metal)[1])
    cv.line(11, 3, 11 + 0, 3, R(metal)[1])
    cv.line(12, 4, 15, 15, R('cloth_white')[1])
    cv.line(28, 20, 16, 16, R('cloth_white')[1])
    cv.line(13, 17, 25, 5, R('steel')[3])
    cv.px(9, 21, R(metal)[3]); cv.px(10, 22, R(metal)[2])
    cv.outline(OUTLINE)
    if fx:
        glow(cv, fx)
    return cv


def staff(shaft, orb, kind='orb'):
    cv = Canvas(32)
    diag(cv, 3, 29, 20, 2, shaft)
    cx, cy = 24, 7
    if kind == 'orb':
        for s in (-1, 1):
            cv.line(cx - 3, cy + 3, cx - 3 + s * 2, cy - 2 + s * 0, R(shaft)[2])
        m = cv.mask_ellipse(cx + 0.5, cy + 0.5, 3.6, 3.6)
        cv.shade(m, orb)
        cv.px(cx - 1, cy - 1, R(orb)[3])
    elif kind == 'flame':
        m = cv.mask_poly([(cx - 4, cy + 4), (cx - 1, cy - 6), (cx + 1, cy - 1), (cx + 4, cy - 5), (cx + 4, cy + 3), (cx, cy + 6)])
        cv.shade(m, 'fire', base=2)
        cv.shade(cv.mask_ellipse(cx, cy + 2, 2, 2), 'fire', base=3)
    elif kind == 'crystal':
        m = cv.mask_poly([(cx - 1, cy - 7), (cx + 3, cy - 2), (cx + 1, cy + 5), (cx - 3, cy + 1)])
        cv.shade(m, orb)
        cv.line(cx - 1, cy - 6, cx, cy + 3, R(orb)[3])
    elif kind == 'skull':
        m = cv.mask_ellipse(cx + 0.5, cy + 0.5, 4, 3.6)
        cv.shade(m, 'bone')
        cv.rect(cx - 2, cy, cx - 1, cy + 1, INK); cv.rect(cx + 1, cy, cx + 2, cy + 1, INK)
        cv.px(cx - 2, cy, R(orb)[3]); cv.px(cx + 2, cy, R(orb)[3])
        cv.hline(cx - 1, cx + 1, cy + 3, INK)
    elif kind == 'star':
        star = cv.mask_poly([(cx, cy - 6), (cx + 2, cy - 2), (cx + 6, cy - 1), (cx + 3, cy + 2), (cx + 4, cy + 6), (cx, cy + 4), (cx - 4, cy + 6), (cx - 3, cy + 2), (cx - 6, cy - 1), (cx - 2, cy - 2)])
        cv.shade(star, orb)
        ring = cv.mask_ellipse(cx, cy, 8, 3) & ~cv.mask_ellipse(cx, cy, 7, 2)
        cv.img[ring & ~star] = rgba(R('magic_purple')[2])
    cv.outline(OUTLINE)
    glow(cv, orb, 0.12)
    return cv


def wand(shaft, tip, kind='gem'):
    cv = Canvas(32)
    diag(cv, 8, 25, 12, 2, shaft)
    cv.rect(7, 25, 9, 26, R('gold')[2])
    tx, ty = 21, 11
    if kind == 'gem':
        m = cv.mask_poly([(tx, ty - 4), (tx + 3, ty - 1), (tx, ty + 2), (tx - 3, ty - 1)])
        cv.shade(m, tip)
        cv.px(tx - 1, ty - 2, R(tip)[3])
    elif kind == 'star':
        for (dx, dy) in [(0, -3), (0, -2), (0, 2), (0, 3), (-3, 0), (-2, 0), (2, 0), (3, 0), (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            cv.px(tx + dx, ty + dy, R(tip)[3 if abs(dx) + abs(dy) <= 1 else 2])
    elif kind == 'bone':
        cv.shade(cv.mask_ellipse(tx, ty - 1, 2.5, 2.5), 'bone')
        cv.px(tx - 1, ty - 1, INK); cv.px(tx + 1, ty - 1, INK)
    cv.outline(OUTLINE)
    glow(cv, tip, 0.25)
    return cv


def shield(kind, face, rim='iron', emblem=None):
    cv = Canvas(32)
    if kind == 'round':
        m = cv.mask_ellipse(16, 16, 12, 12)
    elif kind == 'buckler':
        m = cv.mask_ellipse(16, 16, 9, 9)
    elif kind == 'kite':
        m = cv.mask_poly([(5, 4), (27, 4), (27, 15), (16, 29), (5, 15)])
    elif kind == 'tower':
        m = cv.mask_rect(6, 3, 25, 28) & ~(cv.mask_rect(6, 3, 6, 3) | cv.mask_rect(25, 3, 25, 3) | cv.mask_rect(6, 28, 6, 28) | cv.mask_rect(25, 28, 25, 28))
    elif kind == 'energy':
        m = cv.mask_poly([(16, 3), (27, 9), (27, 22), (16, 29), (5, 22), (5, 9)])
    cv.shade(m, face, depth=2)
    from .core import _shift
    edge = m & (~_shift(m, 1, 0) | ~_shift(m, -1, 0) | ~_shift(m, 0, 1) | ~_shift(m, 0, -1))
    edge2 = m & ~edge & (~_shift(m & ~edge, 1, 0) | ~_shift(m & ~edge, -1, 0) | ~_shift(m & ~edge, 0, 1) | ~_shift(m & ~edge, 0, -1))
    cv.img[edge | edge2] = rgba(R(rim)[2])
    cv.img[edge & (np.mgrid[0:32, 0:32][0] > 16)] = rgba(R(rim)[1])
    if kind == 'round':
        yy, xx = np.mgrid[0:32, 0:32]
        cv.img[m & ~edge & ~edge2 & (xx % 5 == 0)] = rgba(R(face)[0])
        cv.shade(cv.mask_ellipse(16, 16, 3, 3), rim)
    if kind == 'energy':
        yy, xx = np.mgrid[0:32, 0:32]
        cv.img[m & ~edge & (yy % 3 == 0)] = rgba(R(face)[1])
    if emblem == 'cross':
        cv.rect(14, 7, 17, 23, R('gold')[2]); cv.rect(9, 11, 22, 14, R('gold')[2])
        cv.vline(17, 7, 23, R('gold')[1]); cv.hline(9, 22, 14, R('gold')[1])
    elif emblem == 'lion':
        cv.shade(cv.mask_ellipse(16, 14, 5, 5), 'cloth_red')
        cv.rect(14, 13, 14, 13, INK); cv.rect(17, 13, 17, 13, INK)
    elif emblem == 'boss':
        cv.shade(cv.mask_ellipse(16, 16, 2.5, 2.5), 'gold')
    elif emblem == 'stripe':
        for i in range(0, 25):
            cv.px(4 + i, 4 + i, R('cloth_white')[2]); cv.px(5 + i, 4 + i, R('cloth_white')[1])
        cv.img[~m] = 0
        cv.img[edge | edge2] = rgba(R(rim)[2])
    cv.outline(OUTLINE)
    return cv


def helmet(kind):
    cv = Canvas(32)
    yy, xx = np.mgrid[0:32, 0:32]
    if kind == 'leather_cap':
        m = cv.mask_ellipse(16, 18, 11, 10) & (yy <= 20)
        cv.shade(m, 'leather', depth=2)
        cv.img[m & (yy == 20)] = rgba(R('leather')[0])
        cv.img[m & (abs(xx - 16) < 0.6) & (yy < 19)] = rgba(R('leather')[1])
        cv.rect(4, 19, 27, 21, R('leather')[1])
    elif kind == 'iron_helm':
        m = cv.mask_ellipse(16, 17, 11, 11) & (yy <= 23)
        cv.shade(m, 'iron', depth=2)
        cv.rect(15, 14, 16, 26, R('iron')[2])
        cv.img[m & (yy == 18)] = rgba(R('iron')[3])
        for x in (8, 12, 20, 24):
            cv.px(x, 18, R('iron')[1])
    elif kind == 'knight_helm':
        m = cv.mask_ellipse(16, 16, 11, 12) & (yy <= 27)
        cv.shade(m, 'steel', depth=2)
        cv.rect(6, 14, 26, 15, OUTLINE)
        cv.rect(15, 17, 16, 25, R('steel')[0])
        for y in range(19, 25, 2):
            cv.px(12, y, OUTLINE); cv.px(19, y, OUTLINE)
        p = cv.mask_poly([(15, 6), (17, 6), (22, 0), (19, 0)])
        cv.shade(p, 'cloth_red')
    elif kind == 'horned_helm':
        m = cv.mask_ellipse(16, 20, 10, 9) & (yy <= 22)
        cv.shade(m, 'iron', depth=2)
        cv.rect(6, 21, 25, 23, R('bronze')[2])
        for s in (-1, 1):
            h = cv.mask_poly([(16 + s * 8, 18), (16 + s * 10, 21), (16 + s * 15, 4), (16 + s * 13, 12)])
            cv.shade(h, 'bone')
    elif kind == 'wizard_hat':
        brim = cv.mask_ellipse(16, 25, 14, 4)
        cone = cv.mask_poly([(8, 25), (24, 25), (19, 8), (24, 2), (14, 6)])
        cv.shade(cone, 'cloth_purple', depth=2)
        cv.shade(brim, 'cloth_purple')
        cv.img[cone & (yy >= 21) & (yy <= 22)] = rgba(R('gold')[2])
        cv.shade(cv.mask_ellipse(16, 15, 1.6, 1.6), 'gold')
    elif kind == 'space_helmet':
        m = cv.mask_ellipse(16, 15, 12, 12)
        cv.shade(m, 'tech_light', depth=2)
        v = cv.mask_ellipse(17, 16, 8, 6)
        cv.fill(v, 'glass', 1)
        cv.img[v & (yy < 14)] = rgba(R('glass')[2])
        cv.rect(12, 12, 13, 13, R('glass')[3])
        cv.rect(7, 25, 25, 27, R('cloth_orange')[2])
        cv.px(26, 8, R('ruby')[3])
    cv.outline(OUTLINE)
    return cv


def cape(ramp, trim='gold', tattered=False):
    cv = Canvas(32)
    yy, xx = np.mgrid[0:32, 0:32]
    m = cv.mask_poly([(10, 4), (22, 4), (28, 28), (4, 28)])
    cv.shade(m, ramp, depth=2)
    for x in (9, 14, 19, 23):
        cv.img[m & (abs(xx - x - (yy - 4) * (x - 16) / 24) < 0.7) & (yy > 8)] = rgba(R(ramp)[1])
    if tattered:
        cv.img[(yy >= 26) & ((xx % 4) < 2)] = 0
    collar = cv.mask_ellipse(16, 5, 7, 2.5)
    cv.shade(collar, trim)
    cv.shade(cv.mask_ellipse(16, 6, 2, 2), 'ruby')
    cv.outline(OUTLINE)
    return cv


def armor(kind):
    cv = Canvas(32)
    yy, xx = np.mgrid[0:32, 0:32]
    body = cv.mask_poly([(9, 5), (23, 5), (27, 9), (25, 16), (23, 16), (23, 28), (9, 28), (9, 16), (7, 16), (5, 9)])
    neck = cv.mask_ellipse(16, 5, 4, 3)
    mats = {'leather': ('leather', 'bronze'), 'chainmail': ('iron', 'leather'), 'plate': ('steel', 'gold'),
            'gold': ('gold', 'ruby'), 'robe': ('cloth_blue', 'gold'), 'cyber': ('tech_dark', 'neon_cyan')}
    a, b = mats[kind]
    cv.shade(body, a, depth=2)
    cv.img[neck] = 0
    if kind == 'chainmail':
        cv.img[body & ((xx + yy) % 2 == 0)] = rgba(R(a)[1])
        cv.rect(9, 22, 23, 23, R('leather')[1])
    elif kind == 'leather':
        cv.rect(9, 21, 23, 22, R('leather_dark')[1])
        cv.px(16, 21, R(b)[3])
        for y in (9, 12, 15, 18):
            cv.px(15, y, R(b)[2]); cv.px(17, y, R(b)[2])
        cv.vline(16, 8, 20, R(a)[0])
    elif kind in ('plate', 'gold'):
        for (x0, x1) in ((5, 11), (21, 27)):
            pm = cv.mask_ellipse((x0 + x1) / 2, 10, 4, 3.5)
            cv.shade(pm, a)
        cv.img[body & (yy == 14)] = rgba(R(a)[0])
        cv.img[body & (yy == 20)] = rgba(R(a)[0])
        cv.shade(cv.mask_ellipse(16, 11, 2, 2), b)
    elif kind == 'robe':
        cv.vline(16, 7, 28, R(b)[2]); cv.vline(15, 7, 28, R(b)[1])
        cv.rect(9, 18, 23, 19, R(b)[2])
        cv.img[body & (yy == 28)] = rgba(R(b)[1])
    elif kind == 'cyber':
        cv.img[body & (abs(xx - 16) < 0.6)] = rgba(R(b)[2])
        cv.img[body & (yy == 17)] = rgba(R(b)[2])
        cv.rect(11, 9, 13, 11, R(b)[3]); cv.rect(19, 9, 21, 11, R('neon_pink')[2])
    cv.outline(OUTLINE)
    return cv


EQUIPMENT = [
    # (id, category, name, factory)
    ('sword_wooden', 'swords', 'Wooden Sword', lambda: sword('wood_light', 'wood', 'leather', length=14)),
    ('sword_iron', 'swords', 'Iron Sword', lambda: sword('iron', 'iron', 'leather')),
    ('sword_steel', 'swords', 'Steel Longsword', lambda: sword('steel', 'gold', 'leather_dark', length=18)),
    ('sword_gold', 'swords', 'Golden Blade', lambda: sword('gold', 'ruby', 'cloth_red')),
    ('sword_crystal', 'swords', 'Crystal Edge', lambda: sword('crystal', 'silver', 'cloth_blue', fx='crystal')),
    ('sword_flame', 'swords', 'Flamebrand', lambda: sword('lava', 'bronze', 'leather_dark', fx='flame')),
    ('sword_shadow', 'swords', 'Shadowfang', lambda: sword('shadow', 'amethyst', 'cloth_black', fx='shadow', curved=True)),
    ('sword_cyber', 'swords', 'Neon Katana', lambda: sword('neon_pink', 'tech_dark', 'cloth_black', fx='cyber', length=18)),
    ('axe_hatchet', 'axes', 'Hatchet', lambda: axe('iron', 'wood_light')),
    ('axe_iron', 'axes', 'Iron Axe', lambda: axe('steel', 'wood')),
    ('axe_battle', 'axes', 'Battle Axe', lambda: axe('steel', 'wood_dark', double=True)),
    ('axe_gold', 'axes', 'Golden Axe', lambda: axe('gold', 'wood_dark')),
    ('axe_frost', 'axes', 'Frostbite Axe', lambda: axe('ice', 'steel', fx='ice')),
    ('axe_obsidian', 'axes', 'Obsidian Cleaver', lambda: axe('shadow', 'bronze', double=True, fx='magic_purple')),
    ('spear_wooden', 'spears', 'Hunting Spear', lambda: spear('iron', 'wood_light')),
    ('spear_steel', 'spears', 'Steel Spear', lambda: spear('steel', 'wood')),
    ('spear_halberd', 'spears', 'Halberd', lambda: spear('steel', 'wood_dark', 'halberd')),
    ('spear_trident', 'spears', 'Trident', lambda: spear('gold', 'bronze', 'trident')),
    ('spear_lance', 'spears', 'Crystal Lance', lambda: spear('crystal', 'silver', 'lance')),
    ('bow_short', 'bows', 'Shortbow', lambda: bow('wood')),
    ('bow_long', 'bows', 'Longbow', lambda: bow('wood_dark')),
    ('bow_elven', 'bows', 'Elven Bow', lambda: bow('emerald', 'cloth_white', fx='emerald')),
    ('bow_bone', 'bows', 'Bone Bow', lambda: bow('bone', 'cloth_gray')),
    ('bow_cyber', 'bows', 'Photon Bow', lambda: bow('tech', 'neon_cyan', fx='neon_cyan')),
    ('crossbow_light', 'crossbows', 'Light Crossbow', lambda: crossbow('wood', 'iron')),
    ('crossbow_heavy', 'crossbows', 'Heavy Crossbow', lambda: crossbow('wood_dark', 'steel')),
    ('crossbow_repeater', 'crossbows', 'Repeater', lambda: crossbow('bronze', 'gold')),
    ('crossbow_plasma', 'crossbows', 'Plasma Crossbow', lambda: crossbow('tech', 'neon_green', fx='neon_green')),
    ('staff_oak', 'staves', 'Oak Staff', lambda: staff('wood', 'emerald', 'orb')),
    ('staff_crystal', 'staves', 'Crystal Staff', lambda: staff('silver', 'crystal', 'crystal')),
    ('staff_fire', 'staves', 'Ember Staff', lambda: staff('wood_dark', 'fire', 'flame')),
    ('staff_frost', 'staves', 'Frost Staff', lambda: staff('ice', 'magic_blue', 'orb')),
    ('staff_necro', 'staves', 'Necromancer Staff', lambda: staff('wood_dark', 'poison', 'skull')),
    ('staff_cosmic', 'staves', 'Cosmic Staff', lambda: staff('amethyst', 'gold', 'star')),
    ('wand_oak', 'wands', 'Oak Wand', lambda: wand('wood_light', 'emerald')),
    ('wand_ruby', 'wands', 'Ruby Wand', lambda: wand('wood_dark', 'ruby')),
    ('wand_sapphire', 'wands', 'Sapphire Wand', lambda: wand('silver', 'magic_blue')),
    ('wand_bone', 'wands', 'Bone Wand', lambda: wand('bone', 'poison', 'bone')),
    ('wand_star', 'wands', 'Star Wand', lambda: wand('gold', 'gold', 'star')),
    ('shield_wooden', 'shields', 'Wooden Shield', lambda: shield('round', 'wood', 'iron')),
    ('shield_kite', 'shields', 'Kite Shield', lambda: shield('kite', 'cloth_blue', 'steel', 'cross')),
    ('shield_tower', 'shields', 'Tower Shield', lambda: shield('tower', 'iron', 'steel', 'boss')),
    ('shield_buckler', 'shields', 'Buckler', lambda: shield('buckler', 'steel', 'bronze', 'boss')),
    ('shield_royal', 'shields', 'Royal Shield', lambda: shield('kite', 'gold', 'gold', 'lion')),
    ('shield_energy', 'shields', 'Energy Barrier', lambda: shield('energy', 'neon_cyan', 'tech_light')),
    ('helmet_leather', 'helmets', 'Leather Cap', lambda: helmet('leather_cap')),
    ('helmet_iron', 'helmets', 'Iron Helm', lambda: helmet('iron_helm')),
    ('helmet_knight', 'helmets', 'Knight Helm', lambda: helmet('knight_helm')),
    ('helmet_horned', 'helmets', 'Horned Helm', lambda: helmet('horned_helm')),
    ('helmet_wizard', 'helmets', 'Wizard Hat', lambda: helmet('wizard_hat')),
    ('helmet_space', 'helmets', 'EVA Helmet', lambda: helmet('space_helmet')),
    ('cape_red', 'capes', 'Crimson Cape', lambda: cape('cloth_red')),
    ('cape_blue', 'capes', 'Azure Cape', lambda: cape('cloth_blue', 'silver')),
    ('cape_green', 'capes', 'Ranger Cloak', lambda: cape('cloth_forest', 'bronze')),
    ('cape_royal', 'capes', 'Royal Mantle', lambda: cape('cloth_purple', 'gold')),
    ('cape_shadow', 'capes', 'Shadow Cloak', lambda: cape('shadow', 'amethyst', tattered=True)),
    ('armor_leather', 'armor', 'Leather Armor', lambda: armor('leather')),
    ('armor_chainmail', 'armor', 'Chainmail', lambda: armor('chainmail')),
    ('armor_plate', 'armor', 'Plate Armor', lambda: armor('plate')),
    ('armor_gold', 'armor', 'Gilded Plate', lambda: armor('gold')),
    ('armor_robe', 'armor', 'Mage Robe', lambda: armor('robe')),
    ('armor_cyber', 'armor', 'Cyber Suit', lambda: armor('cyber')),
]

# Equip slot + which character layer/style an icon maps to (used by the Godot equipment demo)
SLOT = {'swords': 'weapon', 'axes': 'weapon', 'spears': 'weapon', 'bows': 'weapon', 'crossbows': 'weapon',
        'staves': 'weapon', 'wands': 'weapon', 'shields': 'offhand', 'helmets': 'head', 'capes': 'cape', 'armor': 'torso'}

VISUAL = {
    'sword_wooden': ('sword', None), 'sword_iron': ('sword', None), 'sword_steel': ('greatsword', None), 'sword_gold': ('sword', None),
    'sword_crystal': ('sword', None), 'sword_flame': ('sword', None), 'sword_shadow': ('cutlass', None), 'sword_cyber': ('katana', None),
    'axe_hatchet': ('axe', None), 'axe_iron': ('axe', None), 'axe_battle': ('axe', None), 'axe_gold': ('axe', None), 'axe_frost': ('axe', None), 'axe_obsidian': ('axe', None),
    'spear_wooden': ('spear', None), 'spear_steel': ('spear', None), 'spear_halberd': ('spear', None), 'spear_trident': ('spear', None), 'spear_lance': ('spear', None),
    'bow_short': ('bow', None), 'bow_long': ('bow', None), 'bow_elven': ('bow', None), 'bow_bone': ('bow', None), 'bow_cyber': ('bow', None),
    'crossbow_light': ('crossbow', None), 'crossbow_heavy': ('crossbow', None), 'crossbow_repeater': ('crossbow', None), 'crossbow_plasma': ('crossbow', None),
    'staff_oak': ('staff', None), 'staff_crystal': ('staff', None), 'staff_fire': ('staff', None), 'staff_frost': ('staff', None), 'staff_necro': ('necro_staff', None), 'staff_cosmic': ('staff', None),
    'wand_oak': ('wand', None), 'wand_ruby': ('wand', None), 'wand_sapphire': ('wand', None), 'wand_bone': ('wand', None), 'wand_star': ('wand', None),
    'shield_wooden': ('round_shield', None), 'shield_kite': ('kite_shield', ['cloth_blue', 'cloth_yellow']), 'shield_tower': ('kite_shield', ['cloth_gray', 'cloth_white']),
    'shield_buckler': ('buckler', None), 'shield_royal': ('kite_shield', ['cloth_yellow', 'cloth_red']), 'shield_energy': ('energy_shield', None),
    'helmet_leather': ('cap', ['cloth_brown', 'cloth_brown']), 'helmet_iron': ('viking_helm', ['cloth_gray', 'cloth_gray']), 'helmet_knight': ('knight_helm', ['cloth_red', 'cloth_red']),
    'helmet_horned': ('viking_helm', ['cloth_gray', 'cloth_gray']), 'helmet_wizard': ('wizard_hat', ['cloth_purple', 'cloth_yellow']), 'helmet_space': ('space_helmet', ['cloth_orange', 'cloth_orange']),
    'cape_red': ('cape', ['cloth_red', 'cloth_yellow']), 'cape_blue': ('cape', ['cloth_blue', 'cloth_white']), 'cape_green': ('cape', ['cloth_forest', 'cloth_brown']),
    'cape_royal': ('cape', ['cloth_purple', 'cloth_yellow']), 'cape_shadow': ('tattered_cape', ['cloth_black', 'cloth_purple']),
    'armor_leather': ('leather', ['cloth_brown', 'cloth_tan']), 'armor_chainmail': ('chainmail', ['cloth_red', 'cloth_black']), 'armor_plate': ('plate', ['cloth_blue', 'cloth_yellow']),
    'armor_gold': ('plate', ['cloth_yellow', 'cloth_red']), 'armor_robe': ('robe', ['cloth_blue', 'cloth_yellow']), 'armor_cyber': ('cyberjacket', ['cloth_black', 'neon_cyan']),
}
