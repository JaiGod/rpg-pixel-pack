"""76 monsters.

Humanoid monsters (skeletons, goblins, orcs, humanoid robots & aliens) reuse the
character pose system, so they get the full 3-direction character sheet.
Creatures use the monster sheet: 5 rows (idle 4, move 4, attack 4, hurt 2,
death 5) x 5 columns, facing RIGHT.
"""
import math
import random
import numpy as np

from . import characters as C
from .core import Canvas, R, key_map, rgba, mix, _shift
from .palette import OUTLINE, INK, EYE_WHITE

MON_ANIMS = [('idle', 4, 6, True), ('move', 4, 8, True), ('attack', 4, 10, False),
             ('hurt', 2, 8, False), ('death', 5, 8, False)]


def anim_table():
    return [dict(name=a, row=i, frames=n, fps=fps, loop=lp) for i, (a, n, fps, lp) in enumerate(MON_ANIMS)]


# =============================================================================
# Frame parameter driver
# =============================================================================
def frame_params(anim, f):
    t = dict(phase=0.0, bob=0, lunge=0.0, hurt=False, mouth=False, dx=0, flap=0.0, cast=False)
    if anim == 'idle':
        t['phase'] = f / 4
        t['bob'] = [0, 0, 1, 1][f]
        t['flap'] = math.sin(2 * math.pi * f / 4)
    elif anim == 'move':
        t['phase'] = f / 4
        t['bob'] = [0, -1, 0, -1][f]
        t['flap'] = math.sin(2 * math.pi * f / 4)
        t['walk'] = True
    elif anim == 'attack':
        t['lunge'] = [-0.6, 0.4, 1.0, 0.3][f]
        t['mouth'] = f in (1, 2)
        t['cast'] = f == 2
        t['dx'] = [-1, 1, 2, 1][f]
        t['flap'] = [1, -1, 0.5, 0][f]
    elif anim == 'hurt':
        t['hurt'] = True
        t['dx'] = [-2, -1][f]
        t['flap'] = 1
    return t


def render_creature(fn, size, seed=0):
    rows = []
    for (anim, n, fps, lp) in MON_ANIMS:
        row = []
        for f in range(n):
            if anim == 'death':
                row.append(death_frame(fn, size, f, seed))
            else:
                cv = Canvas(size)
                fn(cv, frame_params(anim, f))
                cv.outline(OUTLINE)
                row.append(cv)
        rows.append(row)
    s = Canvas(5 * size, len(MON_ANIMS) * size)
    for ry, row in enumerate(rows):
        for cx, fr in enumerate(row):
            s.paste(fr, cx * size, ry * size)
    return s


def death_frame(fn, size, f, seed):
    cv = Canvas(size)
    t = frame_params('hurt', 0)
    t['dx'] = 0
    fn(cv, t)
    cv.outline(OUTLINE)
    rnd = random.Random(seed * 31 + 7)
    a = cv.alpha
    ys, xs = np.nonzero(a)
    k = size / 32
    if f >= 1:
        # squash toward the ground
        sq = Canvas(size)
        if len(ys):
            bottom = ys.max()
            src = cv.img.copy()
            for y in range(size):
                sy = int(bottom - (bottom - y) / (0.85 if f == 1 else 0.7))
                if 0 <= sy < size:
                    sq.img[y] = src[sy]
        cv = sq
    if f >= 2:
        frac = {2: 0.35, 3: 0.75, 4: 1.0}[f]
        a = cv.alpha
        ys, xs = np.nonzero(a)
        for y, x in zip(ys, xs):
            if rnd.random() < frac:
                cv.img[y, x] = 0
        # smoke puffs
        if len(ys):
            cx, cy = xs.mean(), ys.mean()
        else:
            cx, cy = size / 2, size * 0.7
        smoke = R('cloth_white')
        puffs = {2: 3, 3: 5, 4: 4}[f]
        for i in range(puffs):
            px = cx + rnd.uniform(-8, 8) * k
            py = cy + rnd.uniform(-6, 4) * k - (f - 2) * 3 * k
            r = (2.5 if f < 4 else 1.6) * k + rnd.random() * k
            m = cv.mask_ellipse(px, py, r, r)
            cv.shade(m, 'cloth_white' if f < 4 else 'cloth_gray', light=True)
        if f == 4:
            cv.img[cv.alpha] = np.where(np.arange(1)[0] == 0, cv.img[cv.alpha], 0)
    return cv


# =============================================================================
# helpers
# =============================================================================
def eye(cv, x, y, big=False, hurt=False, glow=None, look=1):
    x, y = int(x), int(y)
    if hurt:
        cv.px(x, y, INK); cv.px(x + 1, y + 1, INK); cv.px(x + 1, y, INK if False else cv.get(x + 1, y)[:3] if cv.get(x + 1, y)[3] else INK)
        cv.px(x, y + 1, INK)
        return
    if glow:
        g = R(glow)
        cv.px(x, y, g[3]); cv.px(x + 1, y, g[2])
        if big:
            cv.px(x, y + 1, g[2]); cv.px(x + 1, y + 1, g[1])
        return
    if big:
        cv.rect(x, y, x + 1, y + 2, EYE_WHITE)
        cv.px(x + (1 if look > 0 else 0), y + 1, INK); cv.px(x + (1 if look > 0 else 0), y + 2, INK)
    else:
        cv.px(x, y, INK); cv.px(x, y + 1, INK)


# =============================================================================
# SLIMES
# =============================================================================
def slime(ramp, deco=None, k=1.0, eyes_glow=None, sheen=True):
    def fn(cv, t):
        S = cv.w
        base = S - 2 * k
        squash = {0: 0, 1: 0.6, 2: -0.4, 3: 0.3}
        sq = 0.0
        if t.get('walk'):
            sq = [0.5, -0.6, 0.5, -0.6][int(t['phase'] * 4) % 4]
        elif t['lunge']:
            sq = -t['lunge'] * 0.7
        else:
            sq = [0, 0.2, 0.5, 0.2][int(t['phase'] * 4) % 4]
        if t['hurt']:
            sq = 0.8
        rx = 11 * k * (1 + 0.12 * sq)
        ry = 9 * k * (1 - 0.15 * sq)
        lift = 3 * k if (t.get('walk') and sq < 0) else 0
        if t['lunge'] > 0.5:
            lift = 2 * k
        cx = S / 2 + t['dx'] * k + t['lunge'] * 2 * k
        cy = base - ry - lift
        body = cv.mask_ellipse(cx, cy + 2 * k, rx, ry + 2 * k) & (np.mgrid[0:S, 0:S][0] <= base - lift)
        top = cv.mask_ellipse(cx, cy - ry * 0.2, rx * 0.8, ry * 0.9)
        body |= top
        cv.shade(body, ramp, depth=2)
        # inner core glow
        core = cv.mask_ellipse(cx - 2 * k, cy + 2 * k, rx * 0.45, ry * 0.35) & body
        cv.img[core & (cv.img[:, :, 3] > 0)] = rgba(R(ramp)[2])
        if sheen:
            cv.rect(cx - rx * 0.55, cy - ry * 0.55, cx - rx * 0.55 + 1 * k, cy - ry * 0.55 + 1 * k, R(ramp)[3])
            cv.px(cx - rx * 0.55 + 2 * k, cy - ry * 0.7, R(ramp)[3])
        ey = cy - 1 * k
        ex = cx + 1 * k
        if k > 1.5:
            for dx in (-5, 3):
                if t['hurt']:
                    cv.line(ex + dx * k, ey, ex + dx * k + 3, ey + 3, INK); cv.line(ex + dx * k + 3, ey, ex + dx * k, ey + 3, INK)
                else:
                    cv.rect(ex + dx * k, ey, ex + dx * k + 2, ey + 4, EYE_WHITE)
                    cv.rect(ex + dx * k + 1, ey + 1, ex + dx * k + 2, ey + 4, INK)
        else:
            eye(cv, ex - 3, ey, big=True, hurt=t['hurt'], glow=eyes_glow)
            eye(cv, ex + 2, ey, big=True, hurt=t['hurt'], glow=eyes_glow)
        if t['mouth']:
            cv.rect(ex - 1 * k, ey + 4 * k, ex + 1 * k, ey + 5 * k, INK)
        if deco == 'crown':
            cy0 = cy - ry - 1 * k
            crown = cv.mask_poly([(cx - 5 * k, cy0 + 3 * k), (cx + 5 * k, cy0 + 3 * k), (cx + 5 * k, cy0 - 3 * k),
                                  (cx + 2.5 * k, cy0), (cx, cy0 - 4 * k), (cx - 2.5 * k, cy0), (cx - 5 * k, cy0 - 3 * k)])
            cv.shade(crown, 'gold')
            cv.px(cx, cy0, R('ruby')[3])
        elif deco == 'horns':
            for sx in (-1, 1):
                h = cv.mask_poly([(cx + sx * 5 * k, cy - ry * 0.7), (cx + sx * 8 * k, cy - ry * 0.4), (cx + sx * 9 * k, cy - ry - 3 * k)])
                cv.shade(h, 'bone')
        elif deco == 'spikes':
            for i in range(-2, 3):
                sx = cx + i * 4 * k
                sp = cv.mask_poly([(sx - 1.5 * k, cy - ry * 0.75), (sx + 1.5 * k, cy - ry * 0.75), (sx, cy - ry - 3 * k)])
                cv.shade(sp, ramp)
        elif deco == 'leaf':
            lf = cv.mask_ellipse(cx + 2 * k, cy - ry - 1 * k, 2.5 * k, 1.5 * k)
            cv.shade(lf, 'leaf')
            cv.px(cx, cy - ry, R('wood')[2])
        elif deco == 'bubble':
            for (ox, oy, r) in [(-7, -9, 1.5), (8, -6, 1.2), (5, -12, 1)]:
                cv.paint(cv.mask_ellipse(cx + ox * k, cy + oy * k, r * k + 0.6, r * k + 0.6) & ~body, R(ramp)[3])
        elif deco == 'flame':
            fl = cv.mask_poly([(cx - 3 * k, cy - ry + 1), (cx + 3 * k, cy - ry + 1), (cx + 1 * k, cy - ry - 5 * k + (t['bob']))])
            cv.shade(fl, 'fire')
    return fn


# =============================================================================
# WINGED / FLYING
# =============================================================================
def whelp(ramp, belly='sand', k=1.0, horn='bone', breath='fire', frost=False):
    """Small dragon, side view facing right."""
    def fn(cv, t):
        S = cv.w
        bob = t['bob'] * k + (math.sin(t['phase'] * 2 * math.pi) * 1.5 * k if not t.get('walk') else 0)
        cx = S * 0.45 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        cy = S * 0.58 + bob
        # tail
        tail = Canvas(S)
        pts = [(cx - 4 * k, cy + 2 * k), (cx - 9 * k, cy + 4 * k), (cx - 12 * k, cy + 2 * k + math.sin(t['phase'] * 6.28) * k), (cx - 13 * k, cy - 1 * k)]
        for (a, b) in zip(pts, pts[1:]):
            tail.line(a[0], a[1], b[0], b[1], R(ramp)[1], width=max(1, int(2 * k)))
        tail.px(pts[-1][0] - 1, pts[-1][1] - 1, R(ramp)[2])
        tip = cv.mask_poly([(pts[-1][0], pts[-1][1] - 2 * k), (pts[-1][0] - 3 * k, pts[-1][1] - 3 * k), (pts[-1][0] - 1 * k, pts[-1][1] + 1 * k)])
        tail.shade(tip, ramp)
        cv.paste(tail)
        # far wing
        flap = t['flap']
        def wing(ox, dark):
            wy = cy - 5 * k
            tipy = wy - (7 + 5 * flap) * k
            wm = cv.mask_poly([(cx + ox - 2 * k, wy), (cx + ox + 4 * k, wy), (cx + ox + 1 * k, tipy), (cx + ox - 6 * k, tipy + 3 * k), (cx + ox - 7 * k, wy - 1 * k)])
            mem = 'shadow' if dark else ramp
            cv.shade(wm, ramp if not dark else ramp, base=0 if dark else 1)
            # membrane ribs
            cv.line(cx + ox + 1 * k, tipy, cx + ox - 1 * k, wy, R(ramp)[0])
            cv.line(cx + ox - 6 * k, tipy + 3 * k, cx + ox - 2 * k, wy, R(ramp)[0])
        wing(-2 * k, True)
        # legs
        for i, lx in enumerate((cx - 3 * k, cx + 3 * k)):
            step = 0
            if t.get('walk'):
                step = (1 if (int(t['phase'] * 4) + i) % 2 else -1) * k
            leg = cv.mask_rect(lx + step, cy + 3 * k, lx + step + 1 * k + 0.5, cy + 7 * k)
            cv.shade(leg, ramp, base=1 if i else 0)
            cv.px(lx + step + 2 * k, cy + 7 * k, R('bone')[2])
        # body
        body = cv.mask_ellipse(cx, cy + 1 * k, 6.5 * k, 5 * k)
        cv.shade(body, ramp, depth=2)
        bel = cv.mask_ellipse(cx + 1 * k, cy + 3.5 * k, 4.5 * k, 2.2 * k) & body
        cv.shade(bel, belly)
        cv.img[bel & (np.mgrid[0:S, 0:S][0] % 2 == 0)] = rgba(R(belly)[1])
        # neck + head
        hx = cx + 6 * k + max(t['lunge'], 0) * 2 * k
        hy = cy - 5 * k
        neck = Canvas(S)
        neck.line(cx + 3 * k, cy - 1 * k, hx - 1 * k, hy + 1 * k, R(ramp)[1], width=max(2, int(3 * k)))
        cv.paste(neck)
        head = cv.mask_ellipse(hx + 1 * k, hy, 4 * k, 3.2 * k)
        snout = cv.mask_rect(hx + 2 * k, hy - 0.5 * k, hx + 6.5 * k, hy + 2 * k)
        cv.shade(head | snout, ramp)
        if t['mouth']:
            cv.rect(hx + 3 * k, hy + 1.5 * k, hx + 7 * k, hy + 2.5 * k, R('ruby')[0])
            jaw = cv.mask_rect(hx + 2 * k, hy + 3 * k, hx + 5.5 * k, hy + 3.5 * k + 0.5)
            cv.shade(jaw, ramp)
            if t['cast'] or t['lunge'] >= 1:
                for i in range(5):
                    bx = hx + (8 + i * 2.2) * k
                    r = (1.2 + i * 0.5) * k
                    m = cv.mask_ellipse(bx, hy + 2 * k + math.sin(i) * k, r, r * 0.8)
                    cv.shade(m, breath)
        cv.px(hx + 6 * k, hy, INK)  # nostril
        eye(cv, hx + 1 * k, hy - 1 * k, hurt=t['hurt'], glow=None)
        # horns
        h1 = cv.mask_poly([(hx - 1 * k, hy - 2 * k), (hx + 1 * k, hy - 2.5 * k), (hx - 4 * k, hy - 6 * k)])
        cv.shade(h1, horn)
        # near wing
        wing(1 * k, False)
        if frost:
            cv.img[body & (np.mgrid[0:S, 0:S][1] % 4 == 0) & (np.mgrid[0:S, 0:S][0] % 3 == 0)] = rgba(R('ice')[3])
    return fn


def bat(ramp, k=1.0, eyecol='ruby'):
    def fn(cv, t):
        S = cv.w
        cx = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 3 * k
        cy = S * 0.45 + t['bob'] * 2 * k + math.sin(t['phase'] * 6.28) * 2 * k
        flap = t['flap']
        for sx in (-1, 1):
            tipy = cy - 6 * k * flap
            w = cv.mask_poly([(cx, cy - 1 * k), (cx + sx * 4 * k, cy - 3 * k - 2 * flap * k), (cx + sx * 12 * k, tipy - 2 * k),
                              (cx + sx * 10 * k, tipy + 3 * k), (cx + sx * 7 * k, cy + 1 * k), (cx + sx * 4 * k, cy + 3 * k)])
            cv.shade(w, ramp, base=0 if sx < 0 else 1)
        body = cv.mask_ellipse(cx, cy + 1 * k, 4 * k, 4.5 * k)
        cv.shade(body, ramp)
        for sx in (-1, 1):
            ear = cv.mask_poly([(cx + sx * 1 * k, cy - 2 * k), (cx + sx * 3.5 * k, cy - 3 * k), (cx + sx * 3 * k, cy - 7 * k)])
            cv.shade(ear, ramp)
        eye(cv, cx - 2 * k, cy, glow=None if t['hurt'] else eyecol, hurt=t['hurt'])
        eye(cv, cx + 1 * k, cy, glow=None if t['hurt'] else eyecol, hurt=t['hurt'])
        if t['mouth']:
            cv.px(cx - 1 * k, cy + 3 * k, EYE_WHITE); cv.px(cx + 1 * k, cy + 3 * k, EYE_WHITE)
            cv.px(cx, cy + 3 * k, R('ruby')[0])
    return fn


def floater(ramp, k=1.0, face='hood', eyecol='magic_blue', accessory=None, hands='bone'):
    """Wraith / specter / lich: floating cloak."""
    def fn(cv, t):
        S = cv.w
        yy, xx = np.mgrid[0:S, 0:S]
        bob = math.sin(t['phase'] * 6.28) * 1.5 * k + t['bob'] * k
        cx = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        top = S * 0.18 + bob
        bot = S * 0.88 + bob
        body = cv.mask_poly([(cx - 4 * k, top + 4 * k), (cx + 4 * k, top + 4 * k), (cx + 9 * k, bot), (cx - 9 * k, bot)])
        # wavy tattered hem
        wave = ((np.sin(xx * 0.9 / k + t['phase'] * 6.28) * 1.6 * k + bot - 1.5 * k) < yy)
        body &= ~wave
        cv.shade(body, ramp, depth=2)
        cv.img[body & ((xx + int(t['phase'] * 4)) % max(3, int(3 * k)) == 0) & (yy > top + 8 * k)] = rgba(R(ramp)[0])
        # hood / head
        hood = cv.mask_ellipse(cx, top + 4 * k, 6 * k, 6 * k)
        cv.shade(hood, ramp)
        inner = cv.mask_ellipse(cx + 1.5 * k, top + 5 * k, 4 * k, 4.2 * k)
        if face == 'skull':
            cv.shade(inner, 'bone')
            cv.rect(cx - 0.5 * k, top + 4 * k, cx + 0.5 * k, top + 5 * k, INK)
            cv.rect(cx + 2 * k, top + 4 * k, cx + 3 * k, top + 5 * k, INK)
            if not t['hurt']:
                cv.px(cx, top + 4 * k, R(eyecol)[3]); cv.px(cx + 2.5 * k, top + 4 * k, R(eyecol)[3])
            cv.hline(cx, cx + 3 * k, top + 7 * k, INK)
        else:
            cv.fill(inner, 'shadow', 0)
            if not t['hurt']:
                cv.rect(cx, top + 4 * k, cx + 0.5 * k, top + 5 * k, R(eyecol)[3])
                cv.rect(cx + 3 * k, top + 4 * k, cx + 3.5 * k, top + 5 * k, R(eyecol)[3])
            else:
                cv.hline(cx, cx + 1 * k, top + 5 * k, R(eyecol)[1]); cv.hline(cx + 3 * k, cx + 4 * k, top + 5 * k, R(eyecol)[1])
        # arms
        reach = (t['lunge'] if t['lunge'] > 0 else 0) * 4 * k
        arm = Canvas(S)
        arm.line(cx + 2 * k, top + 10 * k, cx + 7 * k + reach, top + 12 * k - reach * 0.5, R(ramp)[1], width=max(2, int(2 * k)))
        cv.paste(arm)
        hand = cv.mask_ellipse(cx + 8 * k + reach, top + 12 * k - reach * 0.5, 1.6 * k, 1.6 * k)
        cv.shade(hand, hands)
        if accessory == 'crown':
            cr = cv.mask_poly([(cx - 5 * k, top - 0 * k), (cx + 5 * k, top), (cx + 5 * k, top - 4 * k), (cx + 2.5 * k, top - 1.5 * k), (cx, top - 5 * k), (cx - 2.5 * k, top - 1.5 * k), (cx - 5 * k, top - 4 * k)])
            cv.shade(cr, 'gold')
            cv.px(cx, top - 2 * k, R('emerald')[3])
        if accessory == 'staff' or accessory == 'crown':
            sx = cx + 8 * k + reach
            sl = Canvas(S)
            sl.line(sx, top + 2 * k, sx, bot - 2 * k, R('wood_dark')[2], width=max(1, int(k)))
            cv.paste(sl)
            orb = cv.mask_ellipse(sx + 0.5, top + 1 * k, 2 * k, 2 * k)
            cv.shade(orb, eyecol)
            cv.shade(hand, hands)
        if accessory == 'scythe':
            sx = cx + 8 * k + reach
            sl = Canvas(S)
            sl.line(sx, top - 1 * k, sx - 2 * k, bot - 3 * k, R('wood_dark')[2])
            for i in range(7):
                sl.px(sx - i * k, top - 1 * k + (i * i) / 10 * k, R('steel')[2])
            cv.paste(sl)
        if t['cast']:
            for i in range(6):
                a = i * 1.05
                cv.px(cx + 9 * k + math.cos(a) * 3 * k, top + 9 * k + math.sin(a) * 3 * k, R(eyecol)[3])
    return fn


def eye_beast(ramp, iris='ruby', k=1.0, tentacles=4):
    def fn(cv, t):
        S = cv.w
        bob = math.sin(t['phase'] * 6.28) * 1.5 * k
        cx, cy = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 2 * k, S * 0.45 + bob
        for i in range(tentacles):
            x0 = cx + (i - (tentacles - 1) / 2) * 3 * k
            tl = Canvas(S)
            pts = [(x0, cy + 5 * k)]
            for j in range(1, 4):
                pts.append((x0 + math.sin(t['phase'] * 6.28 + i + j) * 1.5 * k, cy + (5 + j * 3) * k))
            for a, b in zip(pts, pts[1:]):
                tl.line(a[0], a[1], b[0], b[1], R(ramp)[1 if i % 2 else 0])
            cv.paste(tl)
        orb = cv.mask_ellipse(cx, cy, 8 * k, 7.5 * k)
        cv.shade(orb, ramp, depth=2)
        sclera = cv.mask_ellipse(cx + 1.5 * k, cy, 5 * k, 4.5 * k if not t['hurt'] else 1 * k)
        cv.fill(sclera, 'cloth_white', 2)
        if not t['hurt']:
            ir = cv.mask_ellipse(cx + 2.5 * k + (1 * k if t['lunge'] > 0 else 0), cy, 2.6 * k, 3 * k)
            cv.shade(ir, iris)
            cv.rect(cx + 2.5 * k, cy - 1 * k, cx + 3 * k, cy + 1 * k, INK)
            cv.px(cx + 1 * k, cy - 2 * k, EYE_WHITE)
        lid = cv.mask_ellipse(cx + 1.5 * k, cy - 3.5 * k, 5.5 * k, 1.2 * k) & orb
        cv.fill(lid, ramp, 0)
        if t['cast']:
            cv.line(cx + 7 * k, cy, S - 1, cy, R(iris)[3])
            cv.line(cx + 7 * k, cy + 1, S - 1, cy + 1, R(iris)[2])
    return fn


def wisp(ramp, k=1.0):
    def fn(cv, t):
        S = cv.w
        bob = math.sin(t['phase'] * 6.28) * 2 * k
        cx, cy = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 3 * k, S * 0.55 + bob
        flick = int(t['phase'] * 4) % 2
        fl = cv.mask_poly([(cx - 5 * k, cy + 1 * k), (cx - 3 * k, cy - 6 * k - flick * k), (cx - 1 * k, cy - 3 * k), (cx + 1 * k, cy - 10 * k + flick * k),
                           (cx + 3 * k, cy - 4 * k), (cx + 5 * k, cy - 7 * k), (cx + 6 * k, cy + 1 * k)])
        fl |= cv.mask_ellipse(cx + 0.5, cy + 1 * k, 6 * k, 5 * k)
        cv.shade(fl, ramp, base=2)
        core = cv.mask_ellipse(cx + 0.5, cy + 1 * k, 3 * k, 3 * k)
        cv.fill(core, ramp, 3)
        eye(cv, cx - 2 * k, cy, hurt=t['hurt'])
        eye(cv, cx + 2 * k, cy, hurt=t['hurt'])
        for i in range(3):
            cv.px(cx - 6 * k + i * 5 * k, cy + 7 * k + (i + flick) % 2 * k, R(ramp)[3])
    return fn


# =============================================================================
# GROUND CREATURES
# =============================================================================
def quadruped(ramp, k=1.0, kind='hound', eyecol=None, mane=None):
    def fn(cv, t):
        S = cv.w
        walk = t.get('walk')
        ph = t['phase'] * 6.28
        cx = S * 0.48 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        cy = S * 0.6 + t['bob'] * k
        # tail
        tl = Canvas(S)
        tl.line(cx - 7 * k, cy - 1 * k, cx - 11 * k, cy - 4 * k + math.sin(ph) * k, R(ramp)[1], width=max(1, int(1.5 * k)))
        cv.paste(tl)
        # legs: far pair darker
        for i, (lx, far) in enumerate([(-5, True), (4, True), (-4, False), (5, False)]):
            sw = math.sin(ph + (0 if i % 2 == 0 else math.pi)) * 2 * k if walk else 0
            if t['lunge'] > 0.5:
                sw = 2 * k if lx > 0 else -2 * k
            x = cx + lx * k
            leg = Canvas(S)
            leg.line(x, cy + 2 * k, x + sw, cy + 7 * k, R(ramp)[0 if far else 1], width=max(1, int(1.5 * k)))
            cv.paste(leg)
        body = cv.mask_ellipse(cx, cy, 8 * k, 4.5 * k)
        cv.shade(body, ramp, depth=2)
        if mane:
            mm = cv.mask_ellipse(cx + 4 * k, cy - 2 * k, 4 * k, 4 * k)
            cv.shade(mm, mane)
        hx, hy = cx + 8 * k + max(t['lunge'], 0) * 2 * k, cy - 4 * k
        head = cv.mask_ellipse(hx, hy, 3.5 * k, 3 * k)
        if kind == 'hound':
            head |= cv.mask_rect(hx + 1 * k, hy, hx + 5 * k, hy + 2 * k)
            ear = cv.mask_poly([(hx - 2 * k, hy - 2 * k), (hx, hy - 2 * k), (hx - 2 * k, hy - 6 * k)])
            cv.shade(ear, ramp)
        elif kind == 'boar':
            head |= cv.mask_rect(hx + 1 * k, hy - 1 * k, hx + 4 * k, hy + 2.5 * k)
        cv.shade(head, ramp)
        if kind == 'boar':
            cv.px(hx + 3 * k, hy + 3 * k, R('bone')[3]); cv.px(hx + 3 * k, hy + 2 * k, R('bone')[2])
        cv.px(hx + 4.5 * k, hy, INK)
        eye(cv, hx, hy - 1 * k, glow=eyecol if not t['hurt'] else None, hurt=t['hurt'])
        if t['mouth']:
            cv.hline(hx + 1 * k, hx + 5 * k, hy + 2 * k, R('ruby')[0])
            cv.px(hx + 2 * k, hy + 1 * k, EYE_WHITE); cv.px(hx + 4 * k, hy + 1 * k, EYE_WHITE)
    return fn


def crawler(ramp, k=1.0, legs=8, eyecol='ruby', shell=None):
    """Spider / bug / void crawler."""
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        walk = t.get('walk')
        cx = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        cy = S * 0.62 + t['bob'] * k
        n = legs // 2
        for side in (0, 1):
            for i in range(n):
                lx = cx + (i - (n - 1) / 2) * 3.2 * k
                sw = math.sin(ph + i * 1.7 + side) * 1.5 * k if walk else 0
                knee = (lx + (i - (n - 1) / 2) * 1.5 * k, cy - 4 * k - side * k)
                foot = (lx + (i - (n - 1) / 2) * 2.5 * k + sw, cy + 5 * k)
                lg = Canvas(S)
                col = R(ramp)[0 if side == 0 else 1]
                lg.line(lx, cy, knee[0], knee[1], col)
                lg.line(knee[0], knee[1], foot[0], foot[1], col)
                cv.paste(lg)
        abdomen = cv.mask_ellipse(cx - 3 * k, cy - 1 * k, 6 * k, 4.5 * k)
        cv.shade(abdomen, shell or ramp, depth=2)
        if shell:
            yy, xx = np.mgrid[0:S, 0:S]
            cv.img[abdomen & (abs(xx - (cx - 3 * k)) < 0.6)] = rgba(R(shell)[0])
        head = cv.mask_ellipse(cx + 4 * k, cy, 3.5 * k, 3 * k)
        cv.shade(head, ramp)
        for i in range(2):
            eye(cv, cx + (4 + i * 2) * k, cy - 1 * k, glow=eyecol if not t['hurt'] else None, hurt=t['hurt'])
        if t['mouth']:
            cv.line(cx + 7 * k, cy + 1 * k, cx + 9 * k, cy + 3 * k, R('bone')[2])
            cv.line(cx + 7 * k, cy + 2 * k, cx + 8 * k, cy + 4 * k, R('bone')[1])
    return fn


def jelly(ramp, k=1.0):
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        cx = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        cy = S * 0.38 + math.sin(ph) * 2 * k
        for i in range(5):
            x0 = cx + (i - 2) * 2.5 * k
            tl = Canvas(S)
            pts = [(x0, cy + 3 * k)] + [(x0 + math.sin(ph + i + j * 0.8) * 1.5 * k, cy + (3 + j * 3) * k) for j in range(1, 5)]
            for a, b in zip(pts, pts[1:]):
                tl.line(a[0], a[1], b[0], b[1], R(ramp)[2 if i % 2 else 1])
            cv.paste(tl)
        dome = cv.mask_ellipse(cx, cy + 2 * k, 8 * k, 7 * k) & (np.mgrid[0:S, 0:S][0] <= cy + 3 * k)
        cv.shade(dome, ramp, base=2)
        inner = cv.mask_ellipse(cx, cy, 4 * k, 3 * k)
        cv.fill(inner, ramp, 1)
        eye(cv, cx - 2 * k, cy - 1 * k, glow=None, hurt=t['hurt'])
        eye(cv, cx + 2 * k, cy - 1 * k, glow=None, hurt=t['hurt'])
        if t['cast']:
            for i in range(4):
                cv.px(cx + (i - 1.5) * 4 * k, cy + 16 * k, R('neon_cyan')[3])
    return fn


def drone(ramp, k=1.0, eyecol='ruby', kind='drone'):
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        cx = S / 2 + t['dx'] * k + max(t['lunge'], 0) * 2 * k
        hover = math.sin(ph) * 1.5 * k
        if kind == 'drone':
            cy = S * 0.45 + hover
            for sx in (-1, 1):
                arm = cv.mask_rect(cx + sx * 4 * k - (1 if sx < 0 else 0) * 4 * k, cy - 3 * k, cx + sx * 4 * k + (0 if sx < 0 else 4 * k), cy - 2 * k)
                cv.fill(arm, 'tech', 1)
                rx = cx + sx * 8 * k
                blade = (int(t['phase'] * 8) % 2)
                cv.hline(rx - (3 if blade else 1) * k, rx + (3 if blade else 1) * k, cy - 5 * k, R('tech_light')[2])
                cv.vline(rx, cy - 5 * k, cy - 3 * k, R('tech')[1])
            body = cv.mask_ellipse(cx, cy, 6 * k, 4 * k)
            cv.shade(body, ramp, depth=2)
            lens = cv.mask_ellipse(cx + 2 * k, cy + 0.5 * k, 2.2 * k, 2.2 * k)
            cv.fill(lens, 'tech_dark', 1)
            if not t['hurt']:
                cv.rect(cx + 2 * k, cy, cx + 2.5 * k, cy + 0.5 * k, R(eyecol)[3])
            if t['cast']:
                cv.line(cx + 4 * k, cy + 1 * k, S - 1, cy + 6 * k, R(eyecol)[3])
        elif kind == 'sphere':
            cy = S * 0.6
            roll = int(t['phase'] * 4)
            body = cv.mask_ellipse(cx, cy, 7 * k, 7 * k)
            cv.shade(body, ramp, depth=2)
            yy, xx = np.mgrid[0:S, 0:S]
            band = body & (abs(yy - cy) < 1 * k)
            cv.fill(band, 'tech_dark', 1)
            cv.img[body & ((xx + roll * 2) % int(5 * k) == 0) & (abs(yy - cy) > 2 * k)] = rgba(R(ramp)[0])
            if not t['hurt']:
                cv.rect(cx + 3 * k, cy - 3 * k, cx + 4 * k, cy - 2 * k, R(eyecol)[3])
            cv.vline(cx - 2 * k, cy - 11 * k, cy - 7 * k, R('tech')[2])
            cv.px(cx - 2 * k, cy - 12 * k, R(eyecol)[3 if int(t['phase'] * 4) % 2 else 1])
        elif kind == 'turret':
            cy = S * 0.62
            base = cv.mask_poly([(cx - 8 * k, S - 3 * k), (cx + 8 * k, S - 3 * k), (cx + 5 * k, cy + 2 * k), (cx - 5 * k, cy + 2 * k)])
            cv.shade(base, 'tech_dark')
            head = cv.mask_ellipse(cx, cy - 1 * k, 5.5 * k, 4.5 * k)
            cv.shade(head, ramp, depth=2)
            rec = -1 * k if t['cast'] else 0
            barrel = cv.mask_rect(cx + 3 * k + rec, cy - 2 * k, cx + 12 * k + rec, cy - 0 * k)
            cv.shade(barrel, 'tech')
            cv.rect(cx + 12 * k + rec, cy - 2 * k, cx + 12 * k + rec, cy, R('tech_dark')[0])
            if not t['hurt']:
                cv.px(cx + 1 * k, cy - 3 * k, R(eyecol)[3])
            if t['cast']:
                mf = cv.mask_ellipse(cx + 14 * k, cy - 1 * k, 2.2 * k, 2 * k)
                cv.shade(mf, 'fire', base=2)
    return fn


def golem(ramp, k=1.0, core='crystal', moss=False):
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        walk = t.get('walk')
        cx = S / 2 + t['dx'] * k
        by = t['bob'] * k
        # legs
        for i, lx in enumerate((-5, 3)):
            lift = (2 * k if (int(t['phase'] * 4) + i) % 2 else 0) if walk else 0
            leg = cv.mask_rect(cx + lx * k, S * 0.72 + by - lift, cx + (lx + 4) * k, S - 2 * k - lift)
            cv.shade(leg, ramp, base=0 if i == 0 else 1)
        torso = cv.mask_poly([(cx - 9 * k, S * 0.32 + by), (cx + 9 * k, S * 0.32 + by), (cx + 7 * k, S * 0.75 + by), (cx - 7 * k, S * 0.75 + by)])
        cv.shade(torso, ramp, depth=2)
        yy, xx = np.mgrid[0:S, 0:S]
        cracks = torso & (((xx * 3 + yy * 2) % int(11 * k) == 0) | ((xx - yy * 2) % int(13 * k) == 0))
        cv.img[cracks] = rgba(R(ramp)[0])
        c = cv.mask_ellipse(cx, S * 0.5 + by, 2.5 * k, 2.5 * k)
        cv.shade(c, core, base=2)
        head = cv.mask_rect(cx - 3 * k, S * 0.18 + by, cx + 4 * k, S * 0.33 + by)
        cv.shade(head, ramp)
        if not t['hurt']:
            cv.rect(cx + 1 * k, S * 0.24 + by, cx + 3 * k, S * 0.26 + by, R(core)[3])
        # arms
        reach = max(t['lunge'], 0) * 3 * k
        raise_ = (6 * k if t['lunge'] < 0 else 0)
        for i, (ax, far) in enumerate([(-11, True), (6, False)]):
            ay = S * 0.36 + by - (raise_ if not far else 0)
            arm = cv.mask_rect(cx + ax * k + (reach if not far else 0), ay, cx + (ax + 4) * k + (reach if not far else 0), ay + 14 * k)
            cv.shade(arm, ramp, base=0 if far else 1)
            fist = cv.mask_rect(cx + (ax - 0.5) * k + (reach if not far else 0), ay + 13 * k, cx + (ax + 4.5) * k + (reach if not far else 0), ay + 17 * k)
            cv.shade(fist, ramp, base=0 if far else 1)
        if moss:
            cv.img[(torso | head) & (yy < S * 0.36 + by) & ((xx + yy) % 3 == 0)] = rgba(R('grass')[2])
    return fn


def brain(ramp, k=1.0):
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        cx, cy = S / 2 + t['dx'] * k, S * 0.42 + math.sin(ph) * 2 * k
        for i in range(6):
            a = -0.3 + i * 0.75
            tl = Canvas(S)
            pts = [(cx + math.cos(a) * 6 * k, cy + 6 * k)] + [(cx + math.cos(a) * (6 + j * 2.5) * k + math.sin(ph + i + j) * 2 * k, cy + (6 + j * 4) * k) for j in range(1, 5)]
            for p0, p1 in zip(pts, pts[1:]):
                tl.line(p0[0], p0[1], p1[0], p1[1], R('neon_pink')[1 if i % 2 else 0], width=max(1, int(k)))
            cv.paste(tl)
        b = cv.mask_ellipse(cx, cy, 13 * k, 10 * k)
        cv.shade(b, ramp, depth=2)
        yy, xx = np.mgrid[0:S, 0:S]
        folds = b & (np.sin(xx / (2 * k)) * np.cos(yy / (1.6 * k)) > 0.55)
        cv.img[folds] = rgba(R(ramp)[0])
        cv.img[b & (abs(xx - cx) < 0.6 * k)] = rgba(R(ramp)[0])
        e = cv.mask_ellipse(cx + 3 * k, cy + 3 * k, 4 * k, 3 * k if not t['hurt'] else 0.8 * k)
        cv.fill(e, 'cloth_white', 2)
        if not t['hurt']:
            cv.shade(cv.mask_ellipse(cx + 4 * k, cy + 3 * k, 1.8 * k, 2.2 * k), 'neon_green')
            cv.rect(cx + 4 * k, cy + 2 * k, cx + 4 * k + 1, cy + 4 * k, INK)
        if t['cast'] or t['lunge'] > 0.3:
            for r in (15, 18):
                ring = cv.mask_ellipse(cx, cy, r * k, r * 0.8 * k) & ~cv.mask_ellipse(cx, cy, r * k - 1, r * 0.8 * k - 1)
                cv.img[ring & ((xx + yy) % 3 == 0)] = rgba(R('neon_pink')[3])
    return fn


def mech(ramp, k=1.0, eyecol='ruby'):
    def fn(cv, t):
        S = cv.w
        walk = t.get('walk')
        cx = S / 2 + t['dx'] * k
        by = t['bob'] * k
        for i, lx in enumerate((-7, 4)):
            lift = (2 * k if (int(t['phase'] * 4) + i) % 2 else 0) if walk else 0
            thigh = Canvas(S)
            thigh.line(cx + lx * k, S * 0.55 + by, cx + (lx - 3) * k, S * 0.75 - lift, R('tech')[1 if i else 0], width=int(3 * k))
            thigh.line(cx + (lx - 3) * k, S * 0.75 - lift, cx + (lx + 1) * k, S - 5 * k - lift, R('tech')[1 if i else 0], width=int(3 * k))
            cv.paste(thigh)
            foot = cv.mask_rect(cx + (lx - 2) * k, S - 4 * k - lift, cx + (lx + 5) * k, S - 2 * k - lift)
            cv.shade(foot, 'tech_dark')
        hull = cv.mask_poly([(cx - 12 * k, S * 0.28 + by), (cx + 10 * k, S * 0.25 + by), (cx + 13 * k, S * 0.42 + by), (cx + 8 * k, S * 0.58 + by), (cx - 10 * k, S * 0.58 + by)])
        cv.shade(hull, ramp, depth=2)
        yy, xx = np.mgrid[0:S, 0:S]
        cv.img[hull & (yy == int(S * 0.45 + by))] = rgba(R('warning')[2])
        cv.img[hull & (yy == int(S * 0.45 + by)) & (xx % int(4 * k) < 2 * k)] = rgba(R('tech_dark')[1])
        cockpit = cv.mask_ellipse(cx + 7 * k, S * 0.34 + by, 4 * k, 2.5 * k) & hull
        cv.fill(cockpit, 'glass', 2)
        if not t['hurt']:
            cv.rect(cx + 9 * k, S * 0.33 + by, cx + 10 * k, S * 0.35 + by, R(eyecol)[3])
        # cannons
        rec = -2 * k if t['cast'] else 0
        gun = cv.mask_rect(cx - 2 * k + rec, S * 0.5 + by, cx + 16 * k + rec, S * 0.54 + by)
        cv.shade(gun, 'tech')
        if t['cast']:
            mf = cv.mask_ellipse(cx + 18 * k, S * 0.52 + by, 3 * k, 2.5 * k)
            cv.shade(mf, 'fire', base=2)
        pod = cv.mask_rect(cx - 9 * k, S * 0.16 + by, cx - 2 * k, S * 0.27 + by)
        cv.shade(pod, 'tech')
        for i in range(3):
            cv.px(cx - 8 * k + i * 2 * k, S * 0.2 + by, R('ruby')[2])
    return fn


def wyrm(ramp, belly, k=1.0, breath='ice', frost=True):
    def fn(cv, t):
        S = cv.w
        ph = t['phase'] * 6.28
        cx = S / 2 + t['dx'] * k
        # serpentine body as chain of circles
        segs = []
        for i in range(12):
            x = cx - 15 * k + i * 2.1 * k
            y = S * 0.66 + math.sin(ph + i * 0.7) * 3 * k - (i > 7) * (i - 7) * 3 * k
            r = (3.5 + min(i, 8) * 0.25) * k
            segs.append((x, y, r))
        for (x, y, r) in segs[:-1]:
            m = cv.mask_ellipse(x, y, r, r)
            cv.shade(m, ramp)
            bel = cv.mask_ellipse(x, y + r * 0.6, r * 0.8, r * 0.4)
            cv.fill(bel & m, belly, 2)
            if frost:
                sp = cv.mask_poly([(x - 1 * k, y - r + 1), (x + 1 * k, y - r + 1), (x, y - r - 3 * k)])
                cv.shade(sp, 'ice')
        hx, hy, hr = segs[-1]
        hx += max(t['lunge'], 0) * 3 * k
        hy -= 3 * k
        head = cv.mask_ellipse(hx, hy, 5 * k, 4 * k) | cv.mask_rect(hx, hy - 1 * k, hx + 7 * k, hy + 3 * k)
        cv.shade(head, ramp)
        for hh in range(2):
            horn = cv.mask_poly([(hx - 2 * k + hh * 2 * k, hy - 3 * k), (hx + hh * 2 * k, hy - 3 * k), (hx - 5 * k + hh * 2 * k, hy - 7 * k)])
            cv.shade(horn, 'bone')
        eye(cv, hx + 2 * k, hy - 1 * k, glow='neon_cyan' if not t['hurt'] else None, hurt=t['hurt'], big=True)
        if t['mouth']:
            cv.rect(hx + 3 * k, hy + 2 * k, hx + 8 * k, hy + 3 * k, R('ruby')[0])
            jaw = cv.mask_rect(hx + 1 * k, hy + 4 * k, hx + 8 * k, hy + 5 * k)
            cv.shade(jaw, ramp)
        if t['cast']:
            for i in range(6):
                m = cv.mask_ellipse(hx + (9 + i * 2) * k, hy + 3 * k, (1.5 + i * 0.4) * k, (1.2 + i * 0.4) * k)
                cv.shade(m, breath, base=2)
    return fn


# =============================================================================
# HUMANOID MONSTERS (character-system based)
# =============================================================================
def monster_body(kind, ramp):
    def fn(p):
        p2 = _upright(p)
        cv = C.draw_body(p2, ramp, outline=False)
        _features(cv, p2, kind, ramp)
        cv.outline(OUTLINE)
        return C._maybe_lie(cv, p)
    return fn


def _upright(p):
    import copy
    q = copy.copy(p)
    q.lie = False
    return q


def _features(cv, p, kind, ramp):
    cx, cy = C.head_center(p)
    rr = R(ramp)
    by = p.by + p.crouch
    ey = int(cy + 0.5)
    yy, xx = np.mgrid[0:32, 0:32]
    face = p.dir != 'up'
    eyes = ([int(cx) - 3, int(cx) + 2] if p.dir == 'down' else [int(cx) + 4]) if face else []
    if kind == 'skeleton':
        # sockets
        for ex in eyes:
            cv.rect(ex - (1 if p.dir == 'down' and ex < cx else 0), ey - 1, ex + (1 if p.dir == 'down' and ex > cx else 0), ey + 1, INK)
            if p.eyes == 'open':
                cv.px(ex, ey, R('magic_blue')[3])
        if face:
            mx = int(cx) - 1 if p.dir == 'down' else int(cx) + 3
            for i in range(3):
                cv.px(mx + i, ey + 4, INK if i % 2 == 0 else rr[1])
        # ribs
        if p.dir != 'side':
            for r in (18, 20):
                cv.img[(cv.img[:, :, 3] > 0) & (yy == r + by) & (abs(xx - 15.5 - p.bx) > 0.6) & (abs(xx - 15.5 - p.bx) < 4)] = rgba(INK)
            cv.img[(yy >= 17 + by) & (yy <= 23 + by) & (abs(xx - 15.5 - p.bx) < 0.6)] = rgba(rr[2])
        else:
            for r in (18, 20):
                cv.img[(cv.img[:, :, 3] > 0) & (yy == r + by) & (xx >= 14 + p.bx) & (xx <= 18 + p.bx)] = rgba(INK)
        # gaps between limbs bones: darken waist
        cv.img[(cv.img[:, :, 3] > 0) & (yy == 22 + by) & (abs(xx - 15.5 - p.bx) < 4)] = rgba(rr[0])
    elif kind in ('goblin', 'orc'):
        big = kind == 'orc'
        if p.dir != 'side':
            for sx in (-1, 1):
                ex0 = cx + sx * 6.5 - 0.5
                ear = cv.mask_poly([(ex0, cy - 1), (ex0, cy + 2), (ex0 + sx * (4 if not big else 2.5), cy - 3)])
                cv.shade(ear, ramp)
        else:
            ear = cv.mask_poly([(cx - 3, cy - 1), (cx - 1, cy + 1), (cx - 6, cy - 3)])
            cv.shade(ear, ramp)
        if face:
            for ex in eyes:
                cv.px(ex, ey, R('warning')[3] if kind == 'goblin' else R('ruby')[2])
            if big:
                tx = [int(cx) - 2, int(cx) + 1] if p.dir == 'down' else [int(cx) + 4]
                for x in tx:
                    cv.px(x, ey + 3, R('bone')[3]); cv.px(x, ey + 2, R('bone')[2])
                cv.img[(cv.img[:, :, 3] > 0) & (yy == ey - 1) & (abs(xx - cx) < 4) & (yy < ey) & False] = 0
                # heavy brow
                for ex in eyes:
                    cv.px(ex, ey - 1, rr[0]); cv.px(ex + (1 if p.dir == 'down' and ex > cx else -1 if p.dir == 'down' else 1), ey - 1, rr[0])
            else:
                nx = int(cx) if p.dir == 'down' else int(cx) + 6
                cv.px(nx - (1 if p.dir == 'down' else 0), ey + 2, rr[0])
                mx = int(cx) - 1 if p.dir == 'down' else int(cx) + 3
                cv.hline(mx, mx + 2, ey + 3, INK)
                cv.px(mx + 2, ey + 2 + 0, EYE_WHITE) if p.dir == 'down' else None
    elif kind == 'robot':
        # square head plate + visor
        hm = cv.mask_ellipse(cx, cy, 6.5, 6)
        cv.img[hm] = 0
        head = cv.mask_rect(cx - 6, cy - 5, cx + 5, cy + 5)
        cv.shade(head, ramp, depth=2)
        if face:
            if p.dir == 'down':
                visor = cv.mask_rect(cx - 5, ey - 1, cx + 4, ey + 1)
            else:
                visor = cv.mask_rect(cx + 1, ey - 1, cx + 5, ey + 1)
            cv.fill(visor, 'tech_dark', 1)
            if p.eyes == 'open':
                cv.img[visor & (yy == ey)] = rgba(R('ruby')[3] if ramp != 'tech_light' else R('neon_cyan')[3])
        cv.vline(int(cx) - 1, int(cy) - 8, int(cy) - 6, R('tech')[2])
        cv.px(int(cx) - 1, int(cy) - 9, R('ruby')[3])
        if p.dir != 'up':
            cv.img[(cv.img[:, :, 3] > 0) & (yy == 19 + by) & (abs(xx - 15.5 - p.bx) < 3) & (xx > 0)] = rgba(R('neon_cyan')[2])
        # joints
        cv.img[(cv.img[:, :, 3] > 0) & (yy == 26) & (yy > 0)] = rgba(rr[0])
    elif kind == 'alien':
        hm = cv.mask_ellipse(cx, cy - 1, 7.5, 7)
        cv.shade(hm, ramp, depth=2)
        if face:
            for ex in eyes:
                if p.eyes == 'open':
                    e = cv.mask_ellipse(ex + 0.5 + (0.5 if (p.dir == 'down' and ex > cx) else -0.5 if p.dir == 'down' else 0.5), ey, 1.8, 2.2)
                    cv.fill(e, 'cloth_black', 1)
                    cv.px(ex, ey - 1, R('cloth_black')[3])
                else:
                    cv.hline(ex - 1, ex + 1, ey + 1, INK)
    elif kind == 'reptile':
        if face:
            for ex in eyes:
                cv.px(ex, ey, R('warning')[3]); cv.px(ex, ey + 1, INK)
            if p.dir == 'side':
                snout = cv.mask_rect(cx + 5, cy + 1, cx + 8, cy + 3)
                cv.shade(snout, ramp)
                cv.px(cx + 7, cy + 1, INK)
        crest = cv.mask_rect(cx - 1, cy - 9, cx, cy - 5) if p.dir != 'side' else cv.mask_rect(cx - 4, cy - 8, cx + 1, cy - 6)
        cv.shade(crest, 'cloth_orange')
        cv.img[(cv.img[:, :, 3] > 0) & ((xx + yy) % 3 == 0) & (yy > cy + 5)] = rgba(rr[1])
    elif kind == 'insect':
        if face:
            for ex in eyes:
                e = cv.mask_rect(ex - 1, ey - 1, ex + 1, ey + 1)
                cv.fill(e, 'emerald', 2)
                cv.px(ex, ey - 1, R('emerald')[3])
            mx = int(cx) if p.dir == 'down' else int(cx) + 5
            cv.px(mx - 2, ey + 3, rr[0]); cv.px(mx + 1, ey + 3, rr[0])
        for sx in ((-1, 1) if p.dir != 'side' else (0,)):
            ax = cx + sx * 3 - (1 if p.dir == 'side' else 0)
            cv.line(ax, cy - 5, ax + sx * 2 + (2 if p.dir == 'side' else 0), cy - 10, rr[1])


HUMANOID_MONSTERS = [
    # id, family, name, body kind, skin ramp, layers [(kind, style, P, S)], weapon, offhand
    ('skeleton_warrior', 'Skeletons', 'Skeleton Warrior', 'skeleton', 'bone', [('legs', 'shorts', 'cloth_brown', 'leather')], 'sword', 'round_shield'),
    ('skeleton_archer', 'Skeletons', 'Skeleton Archer', 'skeleton', 'bone', [('legs', 'shorts', 'cloth_forest', 'leather'), ('head', 'hood', 'cloth_forest', 'cloth_forest')], 'bow', None),
    ('skeleton_mage', 'Skeletons', 'Skeleton Mage', 'skeleton', 'bone', [('torso', 'robe', 'cloth_purple', 'cloth_black'), ('legs', 'robe', 'leather', 'leather'), ('head', 'wizard_hat', 'cloth_purple', 'cloth_black')], 'staff', None),
    ('skeleton_knight', 'Skeletons', 'Skeleton Knight', 'skeleton', 'bone', [('torso', 'chainmail', 'cloth_crimson', 'cloth_black'), ('legs', 'greaves', 'cloth_black', 'cloth_black'), ('head', 'viking_helm', 'cloth_gray', 'cloth_gray')], 'greatsword', 'kite_shield'),
    ('skeleton_pirate', 'Skeletons', 'Skeleton Pirate', 'skeleton', 'bone', [('legs', 'pants', 'cloth_navy', 'leather'), ('head', 'tricorn', 'cloth_black', 'cloth_black')], 'cutlass', None),
    ('skeleton_miner', 'Skeletons', 'Skeleton Miner', 'skeleton', 'bone', [('legs', 'shorts', 'cloth_brown', 'leather'), ('head', 'cap', 'cloth_yellow', 'cloth_gray')], 'pickaxe', 'lantern'),
    ('skeleton_lancer', 'Skeletons', 'Skeleton Lancer', 'skeleton', 'bone', [('legs', 'shorts', 'cloth_red', 'leather'), ('head', 'knight_helm', 'cloth_red', 'cloth_red')], 'spear', 'buckler'),
    ('skeleton_necro', 'Skeletons', 'Bone Priest', 'skeleton', 'bone', [('torso', 'robe', 'cloth_black', 'cloth_green'), ('legs', 'robe', 'leather', 'leather'), ('head', 'necro_cowl', 'cloth_black', 'poison')], 'necro_staff', None),

    ('goblin_grunt', 'Goblins', 'Goblin Grunt', 'goblin', 'grass', [('torso', 'tunic', 'cloth_brown', 'cloth_tan'), ('legs', 'shorts', 'cloth_brown', 'leather')], 'dagger', None),
    ('goblin_archer', 'Goblins', 'Goblin Archer', 'goblin', 'grass', [('torso', 'leather', 'cloth_forest', 'cloth_brown'), ('legs', 'pants', 'cloth_forest', 'leather')], 'bow', None),
    ('goblin_shaman', 'Goblins', 'Goblin Shaman', 'goblin', 'grass_dry', [('torso', 'robe', 'cloth_red', 'bone'), ('legs', 'robe', 'leather', 'leather'), ('head', 'necro_cowl', 'cloth_red', 'cloth_yellow')], 'staff', None),
    ('goblin_bomber', 'Goblins', 'Goblin Tinker', 'goblin', 'grass', [('torso', 'overalls', 'cloth_brown', 'cloth_gray'), ('legs', 'pants', 'cloth_brown', 'leather'), ('head', 'goggles', 'cloth_gray', 'cloth_gray')], 'wrench', None),
    ('goblin_rider', 'Goblins', 'Goblin Raider', 'goblin', 'leaf', [('torso', 'leather', 'cloth_red', 'cloth_brown'), ('legs', 'boots', 'cloth_brown', 'leather')], 'spear', 'buckler'),
    ('goblin_thief', 'Goblins', 'Goblin Thief', 'goblin', 'grass', [('torso', 'hooded_cloak', 'cloth_gray', 'cloth_black'), ('legs', 'pants', 'cloth_black', 'leather')], 'dagger', None),
    ('goblin_chief', 'Goblins', 'Goblin Chief', 'goblin', 'leaf', [('torso', 'plate', 'cloth_red', 'cloth_yellow'), ('legs', 'boots', 'cloth_red', 'leather'), ('head', 'circlet', 'cloth_red', 'ruby')], 'axe', None),
    ('goblin_pirate', 'Goblins', 'Goblin Buccaneer', 'goblin', 'grass_dry', [('torso', 'vest', 'cloth_red', 'cloth_white'), ('legs', 'shorts', 'cloth_navy', 'leather'), ('head', 'bandana', 'cloth_red', 'cloth_red')], 'cutlass', None),

    ('orc_brute', 'Orcs', 'Orc Brute', 'orc', 'cloth_forest', [('torso', 'leather', 'cloth_brown', 'cloth_brown'), ('legs', 'pants', 'cloth_brown', 'leather')], 'axe', None),
    ('orc_berserker', 'Orcs', 'Orc Berserker', 'orc', 'cloth_green', [('legs', 'shorts', 'cloth_red', 'leather'), ('head', 'bandana', 'cloth_red', 'cloth_red')], 'greatsword', None),
    ('orc_warrior', 'Orcs', 'Orc Warrior', 'orc', 'cloth_forest', [('torso', 'chainmail', 'cloth_red', 'cloth_black'), ('legs', 'greaves', 'cloth_black', 'cloth_black'), ('head', 'viking_helm', 'cloth_gray', 'cloth_gray')], 'axe', 'round_shield'),
    ('orc_shaman', 'Orcs', 'Orc Shaman', 'orc', 'swamp', [('torso', 'robe', 'cloth_brown', 'bone'), ('legs', 'robe', 'leather', 'leather'), ('head', 'necro_cowl', 'cloth_brown', 'cloth_red')], 'necro_staff', None),
    ('orc_hunter', 'Orcs', 'Orc Hunter', 'orc', 'cloth_green', [('torso', 'leather', 'cloth_forest', 'cloth_brown'), ('legs', 'boots', 'cloth_forest', 'leather')], 'crossbow', None),
    ('orc_warlord', 'Orcs', 'Orc Warlord', 'orc', 'cloth_forest', [('torso', 'plate', 'cloth_black', 'cloth_red'), ('legs', 'greaves', 'cloth_black', 'cloth_black'), ('head', 'knight_helm', 'cloth_red', 'cloth_red'), ('cape', 'tattered_cape', 'cloth_red', 'cloth_black')], 'hammer', None),
    ('orc_pikeman', 'Orcs', 'Orc Pikeman', 'orc', 'swamp', [('torso', 'tunic', 'cloth_black', 'cloth_red'), ('legs', 'boots', 'cloth_black', 'leather')], 'spear', 'kite_shield'),
    ('orc_smith', 'Orcs', 'Orc Smith', 'orc', 'cloth_green', [('torso', 'overalls', 'cloth_brown', 'cloth_gray'), ('legs', 'boots', 'cloth_brown', 'leather_dark')], 'hammer', None),

    ('robot_security', 'Robots', 'Security Droid', 'robot', 'tech', [('legs', 'suit', 'cloth_gray', 'ruby')], 'blaster', 'energy_shield'),
    ('robot_worker', 'Robots', 'Worker Bot', 'robot', 'warning', [('legs', 'suit', 'cloth_yellow', 'neon_cyan')], 'wrench', None),
    ('robot_android', 'Robots', 'Android', 'robot', 'tech_light', [('torso', 'spacesuit', 'cloth_blue', 'cloth_navy'), ('legs', 'suit', 'cloth_blue', 'neon_cyan')], 'katana', None),
    ('robot_assault', 'Robots', 'Assault Mech-Trooper', 'robot', 'tech_dark', [('torso', 'plate', 'cloth_red', 'cloth_black'), ('legs', 'greaves', 'cloth_black', 'cloth_black')], 'blaster', None),

    ('alien_grey', 'Aliens', 'Grey', 'alien', 'tech_light', [('torso', 'spacesuit', 'cloth_purple', 'cloth_black'), ('legs', 'suit', 'cloth_purple', 'neon_green')], 'scanner', None),
    ('alien_reptilian', 'Aliens', 'Reptilian Trooper', 'reptile', 'emerald', [('torso', 'plate', 'cloth_black', 'neon_green'), ('legs', 'greaves', 'cloth_black', 'cloth_black')], 'blaster', None),
    ('alien_insectoid', 'Aliens', 'Insectoid Soldier', 'insect', 'poison', [('torso', 'chainmail', 'cloth_black', 'cloth_black'), ('legs', 'greaves', 'cloth_black', 'cloth_black')], 'spear', None),
    ('alien_psion', 'Aliens', 'Psion', 'alien', 'amethyst', [('torso', 'robe', 'cloth_black', 'neon_pink'), ('legs', 'robe', 'tech', 'tech')], 'wand', None),
]

CREATURES = [
    # id, family, name, size, factory
    ('slime_green', 'Slimes', 'Green Slime', 32, lambda: slime('grass')),
    ('slime_blue', 'Slimes', 'Blue Slime', 32, lambda: slime('water')),
    ('slime_fire', 'Slimes', 'Magma Slime', 32, lambda: slime('lava', 'flame')),
    ('slime_ice', 'Slimes', 'Frost Slime', 32, lambda: slime('ice', 'spikes')),
    ('slime_poison', 'Slimes', 'Toxic Slime', 32, lambda: slime('poison', 'bubble')),
    ('slime_metal', 'Slimes', 'Metal Slime', 32, lambda: slime('silver')),
    ('slime_gold', 'Slimes', 'Gold Slime', 32, lambda: slime('gold')),
    ('slime_shadow', 'Slimes', 'Shadow Slime', 32, lambda: slime('shadow', None, eyes_glow='ruby')),
    ('slime_crystal', 'Slimes', 'Crystal Slime', 32, lambda: slime('crystal', 'spikes')),
    ('slime_forest', 'Slimes', 'Sprout Slime', 32, lambda: slime('leaf', 'leaf')),
    ('slime_demon', 'Slimes', 'Demon Slime', 32, lambda: slime('ruby', 'horns')),
    ('slime_arcane', 'Slimes', 'Arcane Slime', 32, lambda: slime('magic_purple', 'bubble')),

    ('dragon_red', 'Dragons', 'Red Whelp', 32, lambda: whelp('cloth_red', 'sand', breath='fire')),
    ('dragon_green', 'Dragons', 'Forest Whelp', 32, lambda: whelp('leaf', 'grass_dry', breath='poison')),
    ('dragon_blue', 'Dragons', 'Storm Whelp', 32, lambda: whelp('cloth_blue', 'ice', breath='neon_cyan')),
    ('dragon_frost', 'Dragons', 'Frost Whelp', 32, lambda: whelp('ice', 'snow', breath='ice', frost=True)),
    ('dragon_gold', 'Dragons', 'Gold Whelp', 32, lambda: whelp('gold', 'sand', horn='bronze', breath='fire')),
    ('dragon_shadow', 'Dragons', 'Shadow Whelp', 32, lambda: whelp('shadow', 'amethyst', breath='magic_purple')),
    ('dragon_bone', 'Dragons', 'Bone Whelp', 32, lambda: whelp('bone', 'stone', horn='stone_dark', breath='poison')),
    ('dragon_amethyst', 'Dragons', 'Amethyst Whelp', 32, lambda: whelp('amethyst', 'neon_pink', breath='magic_purple')),

    ('robot_drone', 'Robots', 'Recon Drone', 32, lambda: drone('tech', kind='drone')),
    ('robot_sphere', 'Robots', 'Roller Bot', 32, lambda: drone('tech_light', kind='sphere', eyecol='neon_cyan')),
    ('robot_turret', 'Robots', 'Sentry Turret', 32, lambda: drone('tech', kind='turret')),
    ('robot_spider', 'Robots', 'Spider Bot', 32, lambda: crawler('tech', legs=6, eyecol='ruby', shell='tech_light')),

    ('alien_blob', 'Aliens', 'Xeno Blob', 32, lambda: slime('neon_green', 'spikes', eyes_glow='ruby')),
    ('alien_crawler', 'Aliens', 'Xeno Crawler', 32, lambda: crawler('amethyst', legs=8, eyecol='neon_green')),
    ('alien_jelly', 'Aliens', 'Sky Jelly', 32, lambda: jelly('neon_cyan')),
    ('alien_beetle', 'Aliens', 'Plasma Beetle', 32, lambda: crawler('cloth_teal', legs=6, eyecol='neon_cyan', shell='neon_cyan')),

    ('shadow_wraith', 'Shadow Creatures', 'Wraith', 32, lambda: floater('shadow', face='hood', eyecol='magic_blue')),
    ('shadow_specter', 'Shadow Creatures', 'Specter', 32, lambda: floater('cloth_white', face='hood', eyecol='neon_cyan', hands='cloth_white')),
    ('shadow_reaper', 'Shadow Creatures', 'Reaper', 32, lambda: floater('cloth_black', face='skull', eyecol='ruby', accessory='scythe')),
    ('shadow_hound', 'Shadow Creatures', 'Shadow Hound', 32, lambda: quadruped('shadow', kind='hound', eyecol='ruby')),
    ('shadow_eye', 'Shadow Creatures', 'Gazer', 32, lambda: eye_beast('amethyst', 'ruby')),
    ('shadow_wisp', 'Shadow Creatures', 'Void Wisp', 32, lambda: wisp('magic_purple')),
    ('shadow_bat', 'Shadow Creatures', 'Night Bat', 32, lambda: bat('shadow')),
    ('shadow_crawler', 'Shadow Creatures', 'Void Crawler', 32, lambda: crawler('shadow', legs=8, eyecol='magic_purple')),

    ('boss_slime_king', 'Bosses', 'Slime King', 64, lambda: slime('grass', 'crown', k=2.0)),
    ('boss_elder_dragon', 'Bosses', 'Elder Dragon', 64, lambda: whelp('cloth_red', 'sand', k=2.0, breath='fire')),
    ('boss_frost_wyrm', 'Bosses', 'Frost Wyrm', 64, lambda: wyrm('ice', 'snow', k=2.0)),
    ('boss_lich_king', 'Bosses', 'Lich King', 64, lambda: floater('cloth_purple', k=2.0, face='skull', eyecol='emerald', accessory='crown')),
    ('boss_shadow_lord', 'Bosses', 'Shadow Lord', 64, lambda: floater('shadow', k=2.0, face='hood', eyecol='ruby', accessory='scythe')),
    ('boss_stone_golem', 'Bosses', 'Stone Golem', 64, lambda: golem('stone', k=2.0, core='crystal', moss=True)),
    ('boss_mech_titan', 'Bosses', 'Mech Titan', 64, lambda: mech('tech', k=2.0)),
    ('boss_overmind', 'Bosses', 'Alien Overmind', 64, lambda: brain('neon_pink', k=2.0)),
]
