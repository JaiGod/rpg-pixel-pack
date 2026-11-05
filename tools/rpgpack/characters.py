"""Layered 32x32 character system.

Every character frame is built from independent layers that share one pose
model, so any hair/clothing/headgear/weapon combination lines up perfectly.

Sheet layout (all layers and baked characters):
  6 columns x 18 rows of 32x32 frames (192 x 576 px)
  rows = for anim in ANIMS: for dir in DIRS  ->  idle_down, idle_up, idle_side, walk_down ...
  'side' faces RIGHT; flip horizontally for left.
"""
import math
import numpy as np

from .core import Canvas, R, key_map, rgba, mix
from .palette import OUTLINE, INK, EYE_WHITE, KEY_PRIMARY, KEY_SECONDARY, SKINS, RAMPS

FW = FH = 32
DIRS = ['down', 'up', 'side']
ANIMS = [  # name, frames, fps, loop
    ('idle', 4, 6, True),
    ('walk', 6, 10, True),
    ('run', 6, 14, True),
    ('attack', 4, 12, False),
    ('hurt', 2, 8, False),
    ('death', 5, 8, False),
]
COLS = 6
ROWS = len(ANIMS) * len(DIRS)

KP = KEY_PRIMARY
KS = KEY_SECONDARY


# =============================================================================
# Pose model
# =============================================================================
class Pose:
    pass


def _shoulders(d, sex):
    f = sex == 'female'
    if d == 'down':   # weapon (right) hand appears on the viewer's left
        return (10 if f else 9, 16), (20 if f else 21, 16)
    if d == 'up':
        return (20 if f else 21, 16), (10 if f else 9, 16)
    return (15, 16), (13, 16)  # side: near (weapon), far (offhand)


# attack hand path (absolute, before body offset) + weapon angles per class
ATTACK_HANDS = {
    'side': [(12, 14), (16, 11), (21, 17), (20, 19)],
    'down': [(9, 12), (11, 11), (12, 21), (13, 22)],
    'up':   [(21, 12), (19, 11), (19, 13), (18, 15)],
}
ATTACK_ANGLES = {
    'swing':  {'side': [135, 90, 0, 315], 'down': [135, 90, 270, 270], 'up': [45, 90, 90, 90]},
    'thrust': {'side': [0, 0, 0, 0], 'down': [270, 270, 270, 270], 'up': [90, 90, 90, 90]},
    'shoot':  {'side': [0, 0, 0, 0], 'down': [270, 270, 270, 270], 'up': [90, 90, 90, 90]},
    'cast':   {'side': [90, 90, 45, 45], 'down': [90, 90, 90, 90], 'up': [90, 90, 90, 90]},
    'none':   {'side': [90, 90, 0, 0], 'down': [90, 90, 270, 270], 'up': [90, 90, 90, 90]},
}


def make_pose(anim, d, f, sex, wclass='swing'):
    p = Pose()
    p.anim, p.dir, p.f, p.sex = anim, d, f, sex
    p.by, p.bx, p.hx = 0, 0, 0          # body offset y/x, head extra x (lean)
    p.lift = [0, 0]                      # leg lifts
    p.ldx = [0, 0]                       # leg dx (side view)
    p.crouch = 0
    p.eyes = 'open'
    p.lie = False
    p.sparkle = False
    p.flash = False
    p.muzzle = False
    sw, so = _shoulders(d, sex)
    wdy = odx = wdx = ody = 0
    rest_angle = {'side': 45, 'down': 90, 'up': 90}[d]
    p.wangle = rest_angle

    if anim == 'idle':
        p.by = [0, 0, 1, 1][f]
    elif anim in ('walk', 'run'):
        amp = 2 if anim == 'walk' else 3
        s = math.sin(2 * math.pi * f / 6)
        c = math.cos(2 * math.pi * f / 6)
        if d == 'side':
            p.ldx = [int(round(amp * s)), -int(round(amp * s))]
            lift = 1 if anim == 'walk' else 2
            p.lift = [lift if c > 0.4 else 0, lift if c < -0.4 else 0]
            wdx = -int(round((amp - 0.5) * s))
            odx = int(round((amp - 0.5) * s))
            if anim == 'run':
                p.hx = 1
        else:
            lift = 1 if anim == 'walk' else 2
            p.lift = [lift if s > 0.3 else 0, lift if s < -0.3 else 0]
            wdy = -int(round(s * (1 if anim == 'walk' else 2)))
            ody = -wdy
        p.by = ([1, 0, 0, 1, 0, 0] if anim == 'walk' else [1, 0, -1, 1, 0, -1])[f]
    elif anim == 'attack':
        p.by = [0, -1, 1, 1][f]
        if d == 'side':
            p.hx = [-1, 0, 1, 1][f]
        p.wangle = ATTACK_ANGLES.get(wclass, ATTACK_ANGLES['swing'])[d][f]
        p.sparkle = (wclass == 'cast' and f == 2)
        p.muzzle = (wclass == 'shoot' and f == 2)
    elif anim == 'hurt':
        p.eyes = 'hurt'
        if d == 'side':
            p.bx = [-2, -1][f]
        else:
            p.by = [-1, 0][f]
        p.hx = [-1, 0][f] if d == 'side' else 0
    elif anim == 'death':
        p.eyes = 'hurt' if f == 0 else 'closed'
        if f == 0:
            p.bx = -1 if d == 'side' else 0
        elif f == 1:
            p.crouch = 2
        elif f == 2:
            p.crouch = 4
        else:
            p.lie = True

    by = p.by + p.crouch
    if anim == 'attack':
        hx, hy = ATTACK_HANDS[d][f]
        p.whand = (hx + p.bx, hy + by)
    else:
        p.whand = (sw[0] + wdx + p.bx, 22 + wdy + by)
    p.ohand = (so[0] + odx + p.bx, 22 + ody + by)
    p.wshoulder = (sw[0] + p.bx, sw[1] + by)
    p.oshoulder = (so[0] + p.bx, so[1] + by)
    return p


# =============================================================================
# Geometry helpers
# =============================================================================
def head_center(p):
    return 16 + p.bx + p.hx, 9.5 + p.by + p.crouch


def arm_masks(cv, shoulder, hand):
    """Return (arm_mask, hand_mask) for a 2px-thick arm."""
    arm = Canvas(cv.w, cv.h)
    hx, hy = hand
    arm.line(shoulder[0], shoulder[1], hx, hy - 1, (1, 1, 1), width=2)
    hm = cv.mask_rect(hx, hy, hx + 1, hy + 1)
    am = arm.alpha & ~hm
    return am, hm


def arm_portion(am, shoulder, frac):
    """Part of an arm mask within `frac` of its length from the shoulder."""
    ys, xs = np.nonzero(am)
    if len(xs) == 0:
        return am
    d = np.hypot(xs - shoulder[0], ys - shoulder[1])
    lim = d.max() * frac
    out = np.zeros_like(am)
    keep = d <= lim + 0.01
    out[ys[keep], xs[keep]] = True
    return out


def torso_mask(cv, p, length=23, flare=0):
    """Clothing/skin torso silhouette. length = bottom row (before offsets)."""
    by, bx = p.by + p.crouch, p.bx
    m = cv.empty_mask()
    fem = p.sex == 'female'
    bottom = length
    for row in range(16, bottom + 1):
        y = row + by
        if p.dir in ('down', 'up'):
            if fem:
                if row <= 19:
                    x0, x1 = 12, 19
                elif row <= 21:
                    x0, x1 = 12, 19
                else:
                    x0, x1 = 11, 20
            else:
                x0, x1 = (11, 20) if row <= 20 else (12, 19)
            if row > 23:
                k = (row - 23 + 1) // 2 * flare
                x0, x1 = min(x0, 12) - k, max(x1, 19) + k
                x0, x1 = min(x0, 11) if flare else x0, max(x1, 20) if flare else x1
        else:
            x0, x1 = 13, 19
            if fem and row in (18, 19):
                x1 = 20
            if row > 23:
                k = (row - 23 + 1) // 2 * flare
                x0, x1 = 13 - k, 19 + k
        m[max(0, min(31, y)), max(0, x0 + bx):min(32, x1 + bx + 1)] = True if 0 <= y < 32 else False
    return m


def leg_boxes(p):
    """[(x0, x1, top, bottom)] for each leg, after offsets. bottom = foot row."""
    by = p.crouch
    out = []
    for i in range(2):
        top = 24 + by
        bot = 30 - p.lift[i]
        if p.dir == 'side':
            x0 = 14 + p.ldx[i] + p.bx
            out.append((x0, x0 + 2, top, max(bot, top + 1)))
        else:
            x0 = (12 if i == 0 else 17) + p.bx
            out.append((x0, x0 + 2, top, max(bot, top + 1)))
    return out


def hand_masks(cv, p):
    hm = cv.mask_rect(p.whand[0], p.whand[1], p.whand[0] + 1, p.whand[1] + 1)
    if p.dir != 'side':
        hm |= cv.mask_rect(p.ohand[0], p.ohand[1], p.ohand[0] + 1, p.ohand[1] + 1)
    return hm


def finish_overlay(cv, p, outline=True):
    """Outline then punch out the visible hands so skin shows through."""
    if outline:
        cv.outline(OUTLINE)
    cv.img[hand_masks(cv, p)] = 0
    return cv


# =============================================================================
# BODY (skin) layer
# =============================================================================
def draw_body(p, skin, outline=True):
    cv = Canvas(32)
    sk = R(skin)
    under = R('cloth_white')
    by = p.by + p.crouch
    # far arm (side view, behind torso)
    if p.dir == 'side':
        am, hm = arm_masks(cv, p.oshoulder, p.ohand)
        cv.fill(am | hm, sk, 0)
    # legs
    legs = cv.empty_mask()
    for (x0, x1, top, bot) in leg_boxes(p):
        legs |= cv.mask_rect(x0, top, x1, bot)
        if p.dir == 'side':
            legs |= cv.mask_rect(x1 + 1, bot, x1 + 1, bot)
    cv.shade(legs, sk)
    # underwear
    uw = cv.empty_mask()
    for (x0, x1, top, bot) in leg_boxes(p):
        uw |= cv.mask_rect(x0, top, x1, top + 1)
    uw |= torso_mask(cv, p, 24) & cv.mask_rect(0, 23 + by, 31, 24 + by)
    cv.shade(uw, under)
    # torso + neck
    tm = torso_mask(cv, p, 23) & ~cv.mask_rect(0, 23 + by, 31, 31)
    cx, cy = head_center(p)
    neck = cv.mask_rect(15 + p.bx, 14 + by, 16 + p.bx, 16 + by)
    cv.shade(tm | neck, sk)
    if p.sex == 'female' and p.dir == 'up':
        pass
    # arms
    if p.dir == 'side':
        am, hm = arm_masks(cv, p.wshoulder, p.whand)
        cv.shade(am | hm, sk)
    else:
        for sh, hd in ((p.wshoulder, p.whand), (p.oshoulder, p.ohand)):
            am, hm = arm_masks(cv, sh, hd)
            cv.shade(am | hm, sk)
    # head
    head = cv.mask_ellipse(cx, cy, 6.5, 6)
    cv.shade(head, sk)
    if p.dir == 'side':
        cv.px(int(cx) - 2, int(cy) + 1, sk[0])          # ear
    _face(cv, p, sk)
    if not outline:
        return cv
    cv.outline(OUTLINE)
    return _maybe_lie(cv, p)


def _face(cv, p, sk):
    if p.dir == 'up':
        return
    cx, cy = head_center(p)
    ey = int(cy + 0.5)
    fem = p.sex == 'female'
    blush = mix(sk[2], (230, 110, 120), 0.35)
    if p.dir == 'down':
        eyes = [int(cx) - 3, int(cx) + 2]
    else:
        eyes = [int(cx) + 4]
    for i, ex in enumerate(eyes):
        if p.eyes == 'open':
            cv.px(ex, ey, INK); cv.px(ex, ey + 1, INK)
            if fem:
                outer = ex - 1 if (p.dir == 'down' and i == 0) else ex + 1
                cv.px(outer, ey, INK)
        elif p.eyes == 'hurt':
            cv.px(ex, ey, INK); cv.px(ex + (1 if i else -1), ey + 1, INK)
        else:
            cv.px(ex, ey + 1, INK); cv.px(ex + 1 if p.dir == 'side' else ex, ey + 1, INK)
    if p.dir == 'down':
        cv.px(eyes[0] - 1, ey + 2, blush); cv.px(eyes[1] + 1, ey + 2, blush)
        if p.eyes != 'open':
            cv.px(int(cx) - 1, ey + 3, sk[0]); cv.px(int(cx), ey + 3, sk[0])
    else:
        cv.px(eyes[0] - 1, ey + 2, blush)


def _maybe_lie(cv, p):
    if not p.lie:
        return cv
    r = cv.rot90(1)
    out = Canvas(32)
    out.paste(r, 0 if p.dir != 'side' else -1, 8 + (1 if p.f >= 4 else 0))
    return out


# =============================================================================
# HAIR
# =============================================================================
HAIR_STYLES = {
    #            fringe side back  behind  extras
    'short':    dict(fringe=6, side=10, back=13, behind=0, extra=[]),
    'spiky':    dict(fringe=6, side=10, back=13, behind=0, extra=['spikes']),
    'long':     dict(fringe=6, side=19, back=20, behind=20, extra=[]),
    'ponytail': dict(fringe=6, side=10, back=13, behind=0, extra=['ponytail']),
    'bob':      dict(fringe=7, side=14, back=14, behind=0, extra=[]),
    'bun':      dict(fringe=6, side=10, back=12, behind=0, extra=['bun']),
    'mohawk':   dict(fringe=0, side=0, back=0, behind=0, extra=['mohawk']),
    'braids':   dict(fringe=6, side=12, back=14, behind=0, extra=['braids']),
    'bald':     dict(fringe=0, side=0, back=0, behind=0, extra=[]),
    'curly':    dict(fringe=7, side=13, back=15, behind=0, extra=['curly']),
    'sidepart': dict(fringe=7, side=11, back=13, behind=0, extra=['sweep']),
    'pigtails': dict(fringe=6, side=10, back=13, behind=0, extra=['pigtails']),
}


def draw_hair(p, style, ramp=KP, behind=False):
    cv = Canvas(32)
    st = HAIR_STYLES[style]
    if p.lie and False:
        pass
    cx, cy = head_center(p)
    top = cy - 6
    m = cv.empty_mask()
    yy, xx = np.mgrid[0:32, 0:32]
    if behind:
        if st['behind'] and p.dir == 'down':
            m |= cv.mask_rect(cx - 7, cy - 2, cx + 6, cy - 9.5 + st['behind'] - 2)
            m |= cv.mask_rect(cx - 6, cy - 2, cx + 5, cy - 9.5 + st['behind'])
            m |= cv.mask_ellipse(cx, cy - 0.5, 7.5, 7)
            cv.shade(m, ramp)
            cv.outline(OUTLINE)
        return _maybe_lie(cv, p)
    rx = 7 + (0.6 if 'curly' in st['extra'] else 0)
    cap = cv.mask_ellipse(cx, cy - 0.5, rx, 6.8)
    ex = st['extra']
    if style == 'bald':
        return _maybe_lie(cv, p)
    if 'mohawk' in ex:
        if p.dir == 'side':
            m |= cv.mask_rect(cx - 4, top - 2, cx + 2, top + 1) & cv.mask_ellipse(cx - 1, cy - 2, 6, 8)
            m |= cv.mask_rect(cx - 2, top - 3, cx + 0, top - 2)
        else:
            m |= cv.mask_rect(cx - 2, top - 3, cx + 1, cy - 2)
        cv.shade(m, ramp)
        cv.outline(OUTLINE)
        return _maybe_lie(cv, p)
    rel_y = yy - (cy - 9.5)  # row in head-local coords (head top ~ row 3.5)
    if p.dir == 'down':
        m |= cap & (rel_y <= st['fringe'])
        if st['side']:
            m |= cap & (rel_y <= st['side']) & ((xx <= cx - 6) | (xx >= cx + 5))
            if st['side'] > 15:
                m |= cv.mask_rect(cx - 8, cy - 2, cx - 6, cy - 9.5 + st['side'] - 2)
                m |= cv.mask_rect(cx + 5, cy - 2, cx + 7, cy - 9.5 + st['side'] - 2)
            elif st['side'] > 12:
                m |= cv.mask_rect(cx - 8, cy - 2, cx - 6, cy - 9.5 + st['side'])
                m |= cv.mask_rect(cx + 5, cy - 2, cx + 7, cy - 9.5 + st['side'])
        # fringe teeth
        for x in range(int(cx) - 4, int(cx) + 4, 3):
            m[int(cy - 9.5 + st['fringe']) + 1, x:x + 1] = True
        if 'sweep' in ex:
            m |= cv.mask_rect(cx - 5, cy - 9.5 + st['fringe'], cx - 1, cy - 9.5 + st['fringe'] + 1)
    elif p.dir == 'up':
        m |= cap & (rel_y <= max(st['back'], 9))
        if st['back'] > 13:
            m |= cv.mask_rect(cx - 7, cy - 2, cx + 6, cy - 9.5 + min(st['back'], 16))
            m |= cv.mask_rect(cx - 5, cy - 2, cx + 4, cy - 9.5 + st['back'])
    else:  # side, facing right
        m |= cap & (rel_y <= st['fringe'])
        m |= cap & (xx <= cx + 1) & (rel_y <= max(st['back'], 11))
        if st['back'] > 13:
            m |= cv.mask_rect(cx - 7, cy - 1, cx - 2, cy - 9.5 + st['back'])
        m[int(cy - 9.5 + st['fringe']) + 1, int(cx) + 4] = True
        if 'sweep' in ex:
            m |= cv.mask_rect(cx + 2, cy - 9.5 + st['fringe'], cx + 6, cy - 9.5 + st['fringe'] + 1)
        # keep face clear
        m &= ~(cv.mask_rect(cx + 3, cy - 0.5, cx + 7, cy + 6))
    # extras
    if 'spikes' in ex:
        for k, sx in enumerate(range(int(cx) - 6, int(cx) + 6, 3)):
            m |= cv.mask_poly([(sx, top + 2), (sx + 3, top + 2), (sx + 1.5, top - 2 - (k % 2))])
    if 'bun' in ex:
        bx = cx - 0.5 if p.dir != 'side' else cx - 4
        m |= cv.mask_ellipse(bx, top - 0.5, 3, 2.6)
    if 'ponytail' in ex:
        if p.dir == 'side':
            m |= cv.mask_rect(cx - 9, cy - 4, cx - 7, cy + 4)
            m |= cv.mask_rect(cx - 8, cy - 5, cx - 6, cy - 3)
        elif p.dir == 'up':
            m |= cv.mask_rect(cx - 1.5, cy - 2, cx + 0.5, cy + 8)
    if 'pigtails' in ex:
        if p.dir == 'side':
            m |= cv.mask_rect(cx - 8, cy - 1, cx - 6, cy + 6)
        else:
            m |= cv.mask_rect(cx - 10, cy - 3, cx - 8, cy + 5)
            m |= cv.mask_rect(cx + 7, cy - 3, cx + 9, cy + 5)
    if 'braids' in ex:
        if p.dir == 'down':
            m |= cv.mask_rect(cx - 7, cy, cx - 6, cy + 10)
            m |= cv.mask_rect(cx + 5, cy, cx + 6, cy + 10)
        elif p.dir == 'up':
            m |= cv.mask_rect(cx - 4, cy + 2, cx - 3, cy + 10)
            m |= cv.mask_rect(cx + 2, cy + 2, cx + 3, cy + 10)
        else:
            m |= cv.mask_rect(cx - 6, cy, cx - 5, cy + 10)
    if 'curly' in ex:
        for (ox, oy) in [(-6, -3), (6, -3), (-6, 1), (6, 1), (0, -6), (-4, -5), (4, -5)]:
            if p.dir == 'side' and ox > 2:
                continue
            m |= cv.mask_ellipse(cx + ox - 0.5, cy + oy, 1.8, 1.8) & ~cv.mask_rect(cx - 3, cy - 0.5, cx + 3, cy + 6)
    cv.shade(m, ramp)
    # strand texture
    tex = m & ((xx + yy) % 4 == 0) & ~_edge(m)
    cv.img[tex & (cv.img[:, :, 3] > 0)] = rgba(R(ramp)[1])
    if 'braids' in ex:
        cv.img[m & (yy % 2 == 0) & (yy > cy + 1)] = rgba(R(ramp)[0])
    cv.outline(OUTLINE)
    return _maybe_lie(cv, p)


def _edge(m):
    from .core import _shift
    return m & (~_shift(m, -1, 0) | ~_shift(m, 1, 0) | ~_shift(m, 0, -1) | ~_shift(m, 0, 1))


# =============================================================================
# TORSO clothing
# =============================================================================
# P = primary tint channel, S = secondary tint channel, others are fixed ramps
TORSO_STYLES = {
    'tunic':      dict(length=24, flare=1, sleeve=0.45, desc='Belted cloth tunic'),
    'plate':      dict(length=23, flare=0, sleeve=1.0, desc='Steel plate cuirass with tabard'),
    'leather':    dict(length=23, flare=0, sleeve=0.5, desc='Leather jerkin over shirt'),
    'robe':       dict(length=29, flare=1, sleeve=1.0, desc='Full-length mage robe'),
    'overalls':   dict(length=24, flare=0, sleeve=0.4, desc='Work overalls over shirt'),
    'vest':       dict(length=23, flare=0, sleeve=1.0, desc='Merchant vest over long shirt'),
    'coat':       dict(length=27, flare=1, sleeve=1.0, desc='Long captain coat with gold trim'),
    'labcoat':    dict(length=27, flare=0, sleeve=1.0, desc='Lab coat over shirt'),
    'spacesuit':  dict(length=24, flare=0, sleeve=1.0, desc='Pressurized EVA suit'),
    'cyberjacket':dict(length=24, flare=0, sleeve=1.0, desc='Neon-trimmed street jacket'),
    'shirt':      dict(length=23, flare=0, sleeve=0.45, desc='Simple shirt'),
    'dress':      dict(length=27, flare=1, sleeve=0.4, desc='Long dress with apron'),
    'hooded_cloak':dict(length=26, flare=1, sleeve=1.0, desc='Hooded rogue cloak'),
    'chainmail':  dict(length=24, flare=0, sleeve=0.6, desc='Chainmail hauberk'),
}


def draw_torso(p, style, P=KP, S=KS):
    cv = Canvas(32)
    st = TORSO_STYLES[style]
    by = p.by + p.crouch
    yy, xx = np.mgrid[0:32, 0:32]
    tm = torso_mask(cv, p, st['length'], st['flare'])
    if st['length'] > 24:
        # garment hem must not hide feet: cut at row 29
        tm &= ~cv.mask_rect(0, 30, 31, 31)
    sleeves = []
    arms = [(p.wshoulder, p.whand)] + ([(p.oshoulder, p.ohand)])
    for i, (sh, hd) in enumerate(arms):
        am, _ = arm_masks(cv, sh, hd)
        sleeves.append(arm_portion(am, sh, st['sleeve']))
    if p.dir == 'side':
        far_sleeve, near_sleeve = sleeves[1], sleeves[0]
    else:
        far_sleeve, near_sleeve = cv.empty_mask(), sleeves[0] | sleeves[1]

    def body_and_sleeves(ramp, extra_mask=None):
        if p.dir == 'side':
            cv.fill(far_sleeve, ramp, 0)
        cv.shade(tm if extra_mask is None else extra_mask, ramp, depth=1)
        cv.shade(near_sleeve, ramp)

    waist = 22 + by
    cxb = 15.5 + p.bx
    if style in ('tunic', 'shirt'):
        body_and_sleeves(P)
        if style == 'tunic':
            belt = tm & (yy == waist)
            cv.fill(belt, 'leather', 1)
            cv.px(int(cxb) if p.dir != 'side' else 18 + p.bx, waist, R('gold')[2])
            # collar
            cv.img[tm & (yy == 16 + by) & (abs(xx - cxb) < 2)] = rgba(R(P)[0])
        else:
            cv.img[tm & (yy == 16 + by) & (abs(xx - cxb) < 1.5)] = rgba(R(P)[0])
    elif style == 'plate':
        body_and_sleeves('steel')
        if p.dir == 'down':
            tab = tm & (abs(xx - cxb) <= 2) & (yy >= 18 + by)
            cv.shade(tab, P)
            cv.img[tab & (yy == 20 + by) & (abs(xx - cxb) <= 0.5)] = rgba(R(S)[2])
        elif p.dir == 'side':
            cv.shade(tm & (xx >= 17 + p.bx) & (yy >= 18 + by), P)
        cv.fill(tm & (yy == waist), 'leather', 1)
        # pauldrons
        for sh in ([p.wshoulder, p.oshoulder] if p.dir != 'side' else [p.wshoulder]):
            cv.shade(cv.mask_ellipse(sh[0] + 1, sh[1] + 0.5, 2.2, 1.8), 'steel')
    elif style == 'chainmail':
        body_and_sleeves('iron')
        cv.img[(tm | near_sleeve) & ((xx + yy) % 2 == 0) & (cv.img[:, :, 3] > 0)] = rgba(R('iron')[1])
        cv.fill(tm & (yy == waist), 'leather', 1)
        if p.dir != 'up':
            cv.shade(tm & (abs(xx - (cxb if p.dir == 'down' else 17 + p.bx)) <= 1.5) & (yy >= 17 + by) & (yy < waist), P)
    elif style == 'leather':
        body_and_sleeves(S)
        vest = tm & ~((abs(xx - cxb) < 1) & (yy < 20 + by)) if p.dir == 'down' else tm
        cv.shade(vest, 'leather')
        cv.fill(tm & (yy == waist), 'leather_dark', 1)
        cv.img[tm & (yy == waist) & (abs(xx - cxb) < 1)] = rgba(R('bronze')[2])
        if p.dir == 'down':
            cv.line(cxb - 3, 16 + by, cxb + 2, 21 + by, R(P)[1])   # bandolier
    elif style in ('robe', 'hooded_cloak'):
        body_and_sleeves(P)
        if p.dir == 'down':
            trim = tm & (abs(xx - cxb) <= 0.5) & (yy >= 17 + by)
            cv.fill(trim, S, 2)
            cv.img[tm & (yy == 22 + by)] = rgba(R(S)[1])
        elif p.dir == 'side':
            cv.img[tm & (yy == 22 + by)] = rgba(R(S)[1])
        hem = tm & (yy == 29)
        cv.img[hem] = rgba(R(S)[1])
        # sleeve cuffs
        for sl in (near_sleeve,):
            ys, xs = np.nonzero(sl)
            if len(ys):
                far = np.argmax(np.hypot(xs - p.wshoulder[0], ys - p.wshoulder[1]))
                cv.px(xs[far], ys[far], R(S)[2])
    elif style == 'overalls':
        body_and_sleeves(S)
        bib = tm & (yy >= 18 + by) & ((abs(xx - cxb) <= 2.5) | (yy >= 21 + by)) if p.dir != 'side' else tm & (yy >= 19 + by)
        cv.shade(bib, P)
        if p.dir == 'down':
            for sx in (cxb - 2.5, cxb + 2.5):
                cv.line(sx, 16 + by, sx, 18 + by, R(P)[1])
            cv.px(int(cxb - 2), 18 + by, R('gold')[2]); cv.px(int(cxb + 2), 18 + by, R('gold')[2])
            cv.px(int(cxb), 20 + by, R(P)[0])
    elif style == 'vest':
        body_and_sleeves(S)
        if p.dir == 'down':
            v = tm & ~((abs(xx - cxb) < 1.6) & (yy < 23 + by))
            cv.shade(v, P)
            for yb in (18, 20, 22):
                cv.px(int(cxb) + 1, yb + by, R('gold')[2])
        elif p.dir == 'up':
            cv.shade(tm, P)
        else:
            cv.shade(tm & (xx <= 18 + p.bx), P)
        cv.fill(tm & (yy == waist + 1), 'leather', 1)
    elif style == 'coat':
        body_and_sleeves(P)
        if p.dir == 'down':
            shirt = tm & (abs(xx - cxb) < 1.6) & (yy < 22 + by)
            cv.shade(shirt, 'cloth_white')
            open_ = tm & (abs(xx - cxb) < 1) & (yy >= 22 + by)
            cv.img[open_] = 0
            edge = tm & (abs(abs(xx - cxb) - 1.6) < 0.6) & ~open_
            cv.fill(edge, 'gold', 2)
        cv.fill(tm & (yy == 22 + by) & ~(abs(xx - cxb) < 1), 'leather', 1)
        ys, xs = np.nonzero(near_sleeve)
        for sl in (sleeves[0], sleeves[1] if p.dir != 'side' else None):
            if sl is None:
                continue
            ys, xs = np.nonzero(sl)
            if len(ys):
                cv.img[sl & (yy >= ys.max() - 1)] = rgba(R('gold')[2])
    elif style == 'labcoat':
        body_and_sleeves('cloth_white')
        if p.dir == 'down':
            shirt = tm & (abs(xx - cxb) < 1.6) & (yy < 22 + by)
            cv.shade(shirt, P)
            cv.img[tm & (abs(xx - cxb) < 0.6) & (yy >= 16 + by) & (yy <= 20 + by)] = rgba(R(S)[1])  # tie
            cv.img[tm & (abs(xx - cxb) < 0.6) & (yy >= 22 + by)] = rgba(R('cloth_white')[0])
            cv.px(int(cxb) - 3, 19 + by, R(S)[2]); cv.px(int(cxb) - 3, 18 + by, R('steel')[2])  # pocket pen
    elif style == 'spacesuit':
        body_and_sleeves('cloth_white')
        panel = tm & (yy >= 18 + by) & (yy <= 21 + by)
        if p.dir == 'down':
            cv.shade(panel & (abs(xx - cxb) <= 2.5), P)
            cv.px(int(cxb) - 1, 19 + by, R('neon_cyan')[3]); cv.px(int(cxb) + 1, 19 + by, R('neon_green')[2])
            cv.px(int(cxb), 20 + by, R('ruby')[2])
        elif p.dir == 'up':
            pack = cv.mask_rect(cxb - 3.5, 16 + by, cxb + 3.5, 23 + by)
            cv.shade(pack, 'tech_light')
            cv.img[pack & (yy == 18 + by) & (abs(xx - cxb) < 2)] = rgba(R(P)[1])
        else:
            pack = cv.mask_rect(10 + p.bx, 16 + by, 13 + p.bx, 23 + by)
            cv.shade(pack, 'tech_light')
            cv.shade(panel & (xx >= 17 + p.bx), P)
        cv.img[tm & (yy == 23 + by)] = rgba(R(S)[1])
        for sl in sleeves[: (1 if p.dir == 'side' else 2)]:
            ys, xs = np.nonzero(sl)
            if len(ys):
                cv.img[sl & (yy == ys.max())] = rgba(R(S)[1])
    elif style == 'cyberjacket':
        body_and_sleeves('cloth_black')
        neon = S
        if p.dir == 'down':
            cv.shade(tm & (abs(xx - cxb) < 1.6) & (yy < 23 + by), P)
            cv.img[tm & (abs(abs(xx - cxb) - 1.6) < 0.6)] = rgba(R(neon)[2])
        elif p.dir == 'up':
            cv.img[tm & (yy == 19 + by) & (abs(xx - cxb) < 3)] = rgba(R(neon)[2])
            cv.img[tm & (abs(xx - cxb) < 0.6) & (yy > 19 + by)] = rgba(R(neon)[1])
        else:
            cv.img[tm & (xx == 18 + p.bx)] = rgba(R(neon)[2])
        cv.img[(tm) & (yy == 24 + by)] = rgba(R(neon)[1])
        for sl in sleeves[: (1 if p.dir == 'side' else 2)]:
            ys, xs = np.nonzero(sl)
            if len(ys):
                cv.img[sl & (yy == ys.max())] = rgba(R(neon)[2])
    elif style == 'dress':
        body_and_sleeves(P)
        if p.dir == 'down':
            apron = tm & (abs(xx - cxb) <= 2.5) & (yy >= 20 + by)
            cv.shade(apron, S)
            cv.img[tm & (yy == 20 + by)] = rgba(R(S)[1])
        elif p.dir == 'side':
            cv.shade(tm & (xx >= 17 + p.bx) & (yy >= 20 + by), S)
        else:
            cv.img[tm & (yy == 20 + by)] = rgba(R(S)[1])
            cv.px(int(cxb), 21 + by, R(S)[2]); cv.px(int(cxb) - 1, 22 + by, R(S)[1]); cv.px(int(cxb) + 1, 22 + by, R(S)[1])
    if style == 'hooded_cloak':
        # hood lies down on the shoulders
        hood = cv.mask_ellipse(cxb + (0 if p.dir != 'side' else -2), 16 + by, 4.5, 1.6)
        cv.shade(hood, P)
    finish_overlay(cv, p)
    return _maybe_lie(cv, p)


# =============================================================================
# LEGS / footwear
# =============================================================================
LEG_STYLES = {
    'pants':   'Cloth trousers with leather shoes',
    'boots':   'Trousers tucked into tall boots',
    'greaves': 'Steel greaves and sabatons',
    'shorts':  'Shorts with sandals',
    'skirt':   'Knee skirt with boots',
    'suit':    'EVA suit legs with mag-boots',
    'robe':    'Soft shoes (for robes / long coats)',
    'cyber':   'Cargo pants with neon sneakers',
}


def draw_legs(p, style, P=KP, S=KS):
    cv = Canvas(32)
    by = p.by + p.crouch
    yy, xx = np.mgrid[0:32, 0:32]
    legs, feet = cv.empty_mask(), cv.empty_mask()
    for (x0, x1, top, bot) in leg_boxes(p):
        legs |= cv.mask_rect(x0, top, x1, bot - 1)
        f = cv.mask_rect(x0, bot - 1, x1, bot)
        if p.dir == 'side':
            f |= cv.mask_rect(x1 + 1, bot, x1 + 1, bot)
        feet |= f
    hip = torso_mask(cv, p, 24) & (yy >= 23 + by) & (yy <= 24 + by)
    shoe = 'leather'
    if style == 'pants':
        cv.shade(legs | hip, P)
        cv.shade(feet, 'leather_dark')
    elif style == 'boots':
        cv.shade(legs | hip, P)
        boot = (legs & (yy >= 27)) | feet
        cv.shade(boot, S)
        cv.img[boot & (yy == 27)] = rgba(R(S)[2])
    elif style == 'greaves':
        cv.shade(legs | hip, 'steel')
        cv.img[legs & (yy == 26)] = rgba(R('steel')[3])
        cv.shade(feet, 'iron')
        cv.shade(hip, P)
    elif style == 'shorts':
        cv.shade(hip | (legs & (yy <= 25 + p.crouch)), P)
        cv.shade(feet, 'leather')
    elif style == 'skirt':
        sk = hip | (torso_mask(cv, p, 27, 1) & (yy >= 23 + by) & (yy <= 27))
        cv.shade(feet | (legs & (yy >= 28)), S)
        cv.shade(sk, P)
        cv.img[sk & (yy == 27)] = rgba(R(P)[0])
    elif style == 'suit':
        cv.shade(legs | hip, 'cloth_white')
        cv.img[legs & (yy == 26)] = rgba(R(P)[1])
        cv.shade(feet | (legs & (yy >= 28)), 'tech')
        cv.img[feet & (yy == 30)] = rgba(R(S)[2])
    elif style == 'robe':
        cv.shade(feet, P)
    elif style == 'cyber':
        cv.shade(legs | hip, P)
        cv.img[legs & (xx % 3 == 0) & (yy == 26)] = rgba(R(P)[0])
        cv.shade(feet, 'cloth_white')
        cv.img[feet & (yy == 30 - 0)] = rgba(R(S)[2])
    finish_overlay(cv, p)
    return _maybe_lie(cv, p)


# =============================================================================
# HEADGEAR
# =============================================================================
HEAD_STYLES = {
    'knight_helm':  'Great helm with visor slit',
    'viking_helm':  'Horned steel helm',
    'hood':         'Cloth hood',
    'wizard_hat':   'Pointed wizard hat',
    'necro_cowl':   'Bone-crowned cowl',
    'bandana':      'Tied bandana',
    'tricorn':      'Pirate tricorn',
    'straw_hat':    'Wide straw hat',
    'goggles':      'Engineer goggles',
    'space_helmet': 'Glass-dome EVA helmet',
    'cyber_visor':  'Neon visor',
    'cap':          'Peaked cap',
    'turban':       'Merchant turban with jewel',
    'circlet':      'Gold circlet',
    'feather_hat':  'Ranger hat with feather',
}


def draw_head(p, style, P=KP, S=KS):
    cv = Canvas(32)
    cx, cy = head_center(p)
    top = cy - 6
    yy, xx = np.mgrid[0:32, 0:32]
    side = p.dir == 'side'
    front = p.dir == 'down'
    face_x = cx + 4 if side else cx
    if style == 'knight_helm':
        m = cv.mask_ellipse(cx, cy - 0.5, 7.2, 7)
        m &= yy <= cy + 5
        cv.shade(m, 'steel', depth=2)
        if front:
            cv.img[m & (yy == int(cy + 0.5)) & (abs(xx - cx + 0.5) <= 4)] = rgba(OUTLINE)
            cv.img[m & (abs(xx - cx + 0.5) < 0.6) & (yy > cy + 1)] = rgba(R('steel')[0])
            cv.img[m & (yy == int(top))] = rgba(R(P)[2])
        elif side:
            cv.img[m & (yy == int(cy + 0.5)) & (xx >= cx + 1)] = rgba(OUTLINE)
        plume = cv.mask_rect(cx - 1, top - 3, cx, top) | cv.mask_rect(cx - 3 if side else cx - 1, top - 3, cx, top - 2)
        cv.shade(plume, P)
    elif style == 'viking_helm':
        m = cv.mask_ellipse(cx, cy - 1, 7, 6) & (yy <= cy - 1)
        cv.shade(m, 'iron')
        cv.img[m & (yy == int(cy - 1))] = rgba(R('bronze')[2])
        if not side:
            for sx in (-1, 1):
                hx = cx + sx * 7.5
                horn = cv.mask_poly([(hx, cy - 3), (hx + sx * 2, cy - 4), (hx + sx * 3, cy - 9), (hx + sx * 1, cy - 6), (hx - sx * 1, cy - 4)])
                cv.shade(horn, 'bone')
        else:
            horn = cv.mask_poly([(cx - 1, cy - 4), (cx + 1, cy - 4), (cx + 2, cy - 10), (cx, cy - 7)])
            cv.shade(horn, 'bone')
        if front:
            cv.img[m & (abs(xx - cx + 0.5) < 0.6) & (yy >= cy - 2)] = rgba(R('iron')[2])
    elif style in ('hood', 'necro_cowl'):
        m = cv.mask_ellipse(cx, cy - 0.5, 7.5, 7.2)
        m |= cv.mask_rect(cx - 7, cy, cx + 6, cy + 6) if not side else cv.mask_rect(cx - 7, cy, cx + 2, cy + 6)
        if front:
            m &= ~cv.mask_ellipse(cx, cy + 1.5, 5, 5)
        elif side:
            m &= ~cv.mask_ellipse(cx + 3, cy + 1.5, 4, 5)
        cv.shade(m, P, depth=2)
        if p.dir == 'up':
            cv.img[m & (abs(xx - cx + 0.5) < 0.6) & (yy > top + 2)] = rgba(R(P)[0])
        if style == 'necro_cowl':
            for k, ox in enumerate((-4, -2, 0, 2, 4) if not side else (-4, -2, 0, 2)):
                h = 3 if ox == 0 else 2
                cv.shade(cv.mask_rect(cx + ox - 0.5, top - h, cx + ox, top), 'bone')
            cv.img[m & (yy == int(top + 1))] = rgba(R(S)[2])
    elif style == 'wizard_hat':
        brim = cv.mask_ellipse(cx, cy - 4, 9.5, 2.0)
        cone = cv.mask_poly([(cx - 5.5, cy - 4.5), (cx + 5.5, cy - 4.5), (cx + 1, top - 7), (cx - 1 + (3 if side else 0) * -1, top - 8)])
        tip = cv.mask_poly([(cx + 1, top - 7), (cx - 1, top - 8), (cx + 4, top - 9)]) if not side else cv.mask_poly([(cx - 1, top - 7), (cx - 3, top - 7), (cx - 5, top - 9)])
        cv.shade(cone | tip, P, depth=2)
        cv.shade(brim, P)
        band = cone & (yy >= cy - 7) & (yy <= cy - 6)
        cv.img[band] = rgba(R(S)[2])
        if front:
            cv.px(int(cx), int(cy - 6.5), R('gold')[3])
    elif style == 'bandana':
        m = cv.mask_ellipse(cx, cy - 0.5, 7, 6.8) & (yy <= top + 4)
        cv.shade(m, P)
        cv.img[m & ((xx + yy) % 4 == 0)] = rgba(R(P)[3])
        knot = cv.mask_rect(cx - 9, cy - 3, cx - 7, cy - 1) if side or p.dir == 'up' else cv.empty_mask()
        if p.dir == 'up':
            knot = cv.mask_rect(cx - 1.5, cy - 2, cx + 0.5, cy + 2)
        cv.shade(knot, P)
    elif style == 'tricorn':
        crown = cv.mask_ellipse(cx, cy - 4.5, 5.5, 4) & (yy <= cy - 2)
        brim = cv.mask_poly([(cx - 10, cy - 4), (cx + 9, cy - 4), (cx + 6, cy - 1), (cx - 7, cy - 1)])
        cv.shade(crown, P, depth=2)
        cv.shade(brim, P)
        cv.img[brim & (yy == int(cy - 4))] = rgba(R('gold')[2])
        if front:
            sk = cv.mask_rect(cx - 1.5, cy - 7, cx + 0.5, cy - 5)
            cv.fill(sk, 'bone', 2)
            cv.px(int(cx) - 1, int(cy - 6), OUTLINE); cv.px(int(cx), int(cy - 6), OUTLINE)
    elif style == 'straw_hat':
        brim = cv.mask_ellipse(cx, cy - 3.5, 11, 2.2)
        crown = cv.mask_ellipse(cx, cy - 5.5, 5, 3.5) & (yy <= cy - 4)
        cv.shade(brim | crown, 'thatch')
        cv.img[crown & (yy == int(cy - 4))] = rgba(R(P)[1])
        cv.img[(brim | crown) & ((xx * 2 + yy) % 5 == 0)] = rgba(R('thatch')[1])
    elif style == 'goggles':
        strap = cv.mask_ellipse(cx, cy - 0.5, 7, 6.8) & (yy >= cy - 4) & (yy <= cy - 3)
        cv.fill(strap, 'leather', 1)
        lenses = []
        if front:
            lenses = [(cx - 3.5, cy - 3.5), (cx + 2.5, cy - 3.5)]
        elif side:
            lenses = [(cx + 4, cy - 3.5)]
        for lx, ly in lenses:
            ring = cv.mask_ellipse(lx + 0.5, ly + 0.5, 2.2, 2.2)
            cv.fill(ring, 'bronze', 2)
            cv.fill(cv.mask_ellipse(lx + 0.5, ly + 0.5, 1.2, 1.2), 'glass', 2)
            cv.px(int(lx), int(ly), R('glass')[3])
    elif style == 'space_helmet':
        dome = cv.mask_ellipse(cx, cy, 8.2, 8)
        cv.shade(dome, 'tech_light', depth=2)
        visor = cv.mask_ellipse(face_x - (1 if side else 0), cy + 0.5, 5.5 if not side else 3.5, 4.5)
        if p.dir != 'up':
            glass = visor & dome
            cv.fill(glass, 'glass', 1)
            cv.img[glass & (yy < cy - 1)] = rgba(R('glass')[2])
            cv.img[glass & (xx < face_x - 2.5) & (yy < cy + 1)] = rgba(R('glass')[3])
        cv.img[dome & (yy == int(cy + 7))] = rgba(R(P)[1])
        cv.px(int(cx) + 5, int(cy - 6), R('ruby')[3])
    elif style == 'cyber_visor':
        band = cv.mask_ellipse(cx, cy - 0.5, 7.1, 6.8) & (yy >= cy - 0.5) & (yy <= cy + 1.5)
        cv.fill(band, 'tech_dark', 1)
        if p.dir != 'up':
            cv.img[band & (yy == int(cy + 0.5))] = rgba(R(P)[2])
            cv.img[band & (yy == int(cy + 0.5)) & (xx == int(face_x) - 1)] = rgba(R(P)[3])
        ear = cv.mask_rect(cx - 7.5, cy - 1, cx - 6.5, cy + 2) if not side else cv.mask_rect(cx - 2, cy - 1, cx - 1, cy + 2)
        cv.fill(ear, 'tech', 2)
    elif style == 'cap':
        crown = cv.mask_ellipse(cx, cy - 1.5, 7, 6) & (yy <= cy - 2)
        cv.shade(crown, P)
        if front:
            peak = cv.mask_rect(cx - 5, cy - 2, cx + 4, cy - 1)
        elif side:
            peak = cv.mask_rect(cx + 2, cy - 2, cx + 8, cy - 1)
        else:
            peak = cv.empty_mask()
        cv.shade(peak, S)
        if front:
            cv.px(int(cx), int(cy - 5), R(S)[2])
    elif style == 'turban':
        m = cv.mask_ellipse(cx, cy - 3, 7.5, 5) & (yy <= cy - 1)
        m |= cv.mask_ellipse(cx, top - 0.5, 4, 2.2)
        cv.shade(m, P)
        cv.img[m & ((yy - xx) % 3 == 0)] = rgba(R(P)[0])
        if front:
            gem = cv.mask_rect(cx - 1, cy - 4, cx, cy - 3)
            cv.fill(gem, S, 2)
            cv.px(int(cx) - 1, int(cy - 4), R(S)[3])
    elif style == 'circlet':
        band = cv.mask_ellipse(cx, cy - 0.5, 7.1, 6.8) & (yy == int(cy - 3))
        cv.fill(band, 'gold', 2)
        if front:
            cv.fill(cv.mask_rect(cx - 1, cy - 4, cx, cy - 3), S, 2)
    elif style == 'feather_hat':
        crown = cv.mask_ellipse(cx, cy - 4, 6, 4) & (yy <= cy - 2)
        brim = cv.mask_ellipse(cx, cy - 2.5, 8.5, 1.8)
        cv.shade(crown | brim, P)
        cv.img[crown & (yy == int(cy - 3))] = rgba(R('leather')[1])
        fx = cx - 5 if not side else cx - 6
        feather = cv.mask_poly([(fx, cy - 4), (fx + 1, cy - 4), (fx - 2, cy - 11), (fx - 3, cy - 10)])
        cv.shade(feather, S)
    finish_overlay(cv, p)
    return _maybe_lie(cv, p)


# =============================================================================
# ACCESSORIES
# =============================================================================
ACC_STYLES = {
    'beard':     'Full beard (tintable with hair color)',
    'glasses':   'Round glasses',
    'eyepatch':  'Pirate eyepatch',
    'mask':      'Rogue face mask',
    'scarf':     'Scarf',
    'headphones':'Cyber headphones',
}


def draw_acc(p, style, P=KP, S=KS):
    cv = Canvas(32)
    cx, cy = head_center(p)
    ey = int(cy + 0.5)
    yy, xx = np.mgrid[0:32, 0:32]
    side, front = p.dir == 'side', p.dir == 'down'
    if style == 'beard' and p.dir != 'up':
        if front:
            m = cv.mask_ellipse(cx, cy + 3.5, 5.2, 3.2) & (yy >= ey + 2)
            m |= cv.mask_rect(cx - 6, ey, cx - 5, ey + 3) | cv.mask_rect(cx + 4, ey, cx + 5, ey + 3)
            m &= ~cv.mask_rect(cx - 1, ey + 3, cx, ey + 3)
        else:
            m = cv.mask_ellipse(cx + 3, cy + 3.5, 3.5, 3) & (yy >= ey + 2)
            m |= cv.mask_rect(cx, ey, cx + 1, ey + 3)
        cv.shade(m, P)
    elif style == 'glasses' and p.dir != 'up':
        col = R('gold')[1]
        if front:
            for ex in (int(cx) - 3, int(cx) + 2):
                for (dx, dy) in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
                    cv.px(ex + dx, ey + dy + 0, col)
            cv.px(int(cx) - 1, ey - 1, col); cv.px(int(cx), ey - 1, col)
        else:
            ex = int(cx) + 4
            for (dx, dy) in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
                cv.px(ex + dx, ey + dy, col)
            cv.line(cx, ey - 1, ex - 2, ey - 1, col)
        return _maybe_lie(cv, p)
    elif style == 'eyepatch' and p.dir != 'up':
        if front:
            cv.line(cx - 6, ey - 3, cx + 5, ey + 0, OUTLINE)
            cv.fill(cv.mask_rect(cx + 1, ey - 1, cx + 3, ey + 1), 'cloth_black', 1)
        elif side:
            cv.line(cx - 4, ey - 3, cx + 5, ey - 1, OUTLINE)
        return _maybe_lie(cv, p)
    elif style == 'mask' and p.dir != 'up':
        if front:
            m = cv.mask_ellipse(cx, cy, 6.5, 6) & (yy >= ey + 2)
        else:
            m = cv.mask_ellipse(cx, cy, 6.5, 6) & (yy >= ey + 2) & (xx >= cx - 1)
        cv.shade(m, P)
    elif style == 'scarf':
        by = p.by + p.crouch
        m = cv.mask_ellipse(16 + p.bx, 15.5 + by, 4.5, 1.8)
        if p.dir == 'down':
            m |= cv.mask_rect(17 + p.bx, 16 + by, 18 + p.bx, 20 + by)
        elif p.dir == 'side':
            m |= cv.mask_rect(10 + p.bx, 15 + by, 13 + p.bx, 16 + by)
        cv.shade(m, P)
        cv.img[m & (yy % 2 == 0)] = rgba(R(S)[2]) if False else cv.img[m & (yy % 2 == 0)]
    elif style == 'headphones':
        band = cv.mask_ellipse(cx, cy - 0.5, 7.4, 7.2) & ~cv.mask_ellipse(cx, cy - 0.5, 6.5, 6.3) & (yy <= cy)
        cv.fill(band, 'tech_dark', 2)
        cups = [cv.mask_rect(cx - 8, cy - 1, cx - 6, cy + 2), cv.mask_rect(cx + 5, cy - 1, cx + 7, cy + 2)] if not side else [cv.mask_rect(cx - 2, cy - 1, cx, cy + 2)]
        for c in cups:
            cv.fill(c, 'tech_dark', 1)
            cv.img[c & (yy == int(cy))] = rgba(R(P)[2])
    finish_overlay(cv, p)
    return _maybe_lie(cv, p)


# =============================================================================
# CAPE
# =============================================================================
CAPE_STYLES = {'cape': 'Flowing cape', 'tattered_cape': 'Tattered cape'}


def draw_cape(p, style, P=KP, S=KS):
    cv = Canvas(32)
    by = p.by + p.crouch
    yy, xx = np.mgrid[0:32, 0:32]
    sway = {'walk': [0, 1, 1, 0, 1, 1], 'run': [1, 2, 2, 1, 2, 2]}.get(p.anim, [0] * 6)[p.f % 6] if p.anim in ('walk', 'run') else 0
    bot = 28 + (0 if style == 'cape' else -1)
    if p.dir == 'up':
        m = cv.mask_poly([(10 + p.bx, 16 + by), (21 + p.bx, 16 + by), (23 + p.bx, bot), (8 + p.bx, bot)])
        cv.shade(m, P, depth=2)
        cv.img[m & (xx % 4 == 1) & (yy > 18 + by)] = rgba(R(P)[1])
        cv.img[m & (yy == 16 + by)] = rgba(R(S)[2])
    elif p.dir == 'down':
        m = cv.mask_rect(8 + p.bx, 17 + by, 9 + p.bx, bot - 1) | cv.mask_rect(22 + p.bx, 17 + by, 23 + p.bx, bot - 1)
        m |= cv.mask_rect(9 + p.bx, 16 + by, 22 + p.bx, 16 + by)
        cv.shade(m, P)
        cv.img[m & (yy == 16 + by)] = rgba(R(S)[2])
        cv.fill(cv.mask_rect(15 + p.bx, 16 + by, 16 + p.bx, 17 + by), 'gold', 2)
    else:
        m = cv.mask_poly([(12 + p.bx, 16 + by), (15 + p.bx, 16 + by), (13 + p.bx, bot), (8 + p.bx - sway, bot - 1)])
        cv.shade(m, P, depth=2)
        cv.img[m & (yy == 16 + by)] = rgba(R(S)[2])
    if style == 'tattered_cape':
        cv.img[(yy >= bot - 1) & (xx % 3 == 0)] = 0
    cv.outline(OUTLINE)
    if p.dir == 'down':
        cv.img[cv.mask_rect(10 + p.bx, 17 + by, 21 + p.bx, 31)] = 0
    elif p.dir == 'side':
        cv.img[cv.mask_rect(13 + p.bx, 17 + by, 31, 31)] = 0
    cv.img[hand_masks(cv, p)] = 0
    return _maybe_lie(cv, p)


# =============================================================================
# HELD ITEMS (weapon hand + offhand)
# =============================================================================
ANG = {0: (1, 0), 45: (1, -1), 90: (0, -1), 135: (-1, -1), 180: (-1, 0), 225: (-1, 1), 270: (0, 1), 315: (1, 1)}

WEAPONS = {
    # name: (kind, class, materials)
    'sword':     ('blade', 'swing', dict(blade='steel', guard='gold', grip='leather'), 9),
    'greatsword':('blade', 'swing', dict(blade='steel', guard='iron', grip='leather_dark'), 11),
    'axe':       ('axe', 'swing', dict(head='iron', shaft='wood'), 9),
    'spear':     ('spear', 'thrust', dict(head='steel', shaft='wood_light'), 13),
    'bow':       ('bow', 'shoot', dict(wood='wood', string='cloth_white'), 6),
    'crossbow':  ('crossbow', 'shoot', dict(wood='wood_dark', metal='iron'), 6),
    'staff':     ('staff', 'cast', dict(shaft='wood', orb='crystal'), 13),
    'necro_staff':('staff', 'cast', dict(shaft='wood_dark', orb='poison', skull=True), 13),
    'wand':      ('wand', 'cast', dict(shaft='wood_light', orb='magic_purple'), 5),
    'dagger':    ('blade', 'thrust', dict(blade='silver', guard='bronze', grip='leather_dark'), 4),
    'hammer':    ('hammer', 'swing', dict(head='iron', shaft='wood'), 8),
    'wrench':    ('wrench', 'swing', dict(head='steel'), 6),
    'blaster':   ('gun', 'shoot', dict(body='tech', glow='neon_cyan'), 5),
    'katana':    ('blade', 'swing', dict(blade='neon_pink', guard='tech_dark', grip='cloth_black'), 10),
    'hoe':       ('hoe', 'swing', dict(head='iron', shaft='wood_light'), 11),
    'scythe':    ('scythe', 'swing', dict(head='steel', shaft='wood_dark'), 12),
    'cutlass':   ('blade', 'swing', dict(blade='silver', guard='gold', grip='leather', curved=True), 8),
    'flask':     ('flask', 'shoot', dict(liquid='poison'), 0),
    'pickaxe':   ('pick', 'swing', dict(head='iron', shaft='wood'), 9),
    'scanner':   ('gun', 'shoot', dict(body='tech_light', glow='neon_green'), 3),
}

OFFHANDS = {
    'round_shield': 'Wooden round shield with iron boss',
    'kite_shield':  'Heater shield with heraldry',
    'buckler':      'Small steel buckler',
    'tome':         'Spell tome',
    'lantern':      'Oil lantern',
    'energy_shield':'Hard-light energy shield',
}


def weapon_class(name):
    return WEAPONS[name][1] if name in WEAPONS else 'none'


def _grip_point(p):
    return p.whand[0] + 0.5, p.whand[1] + 0.5


def draw_item_line(cv, x, y, ang, length, ramp, width=1, shade_side=True):
    dx, dy = ANG[ang]
    x1, y1 = x + dx * length, y + dy * length
    rr = R(ramp)
    if width == 2:
        ox, oy = (1, 0) if dy != 0 else (0, 1)
        if dx != 0 and dy != 0:
            ox, oy = (1, 0)
        cv.line(x + ox, y + oy, x1 + ox, y1 + oy, rr[1])
    cv.line(x, y, x1, y1, rr[2])
    return x1, y1


def draw_weapon_at(cv, name, gx, gy, ang, p=None):
    kind, wcls, mats, L = WEAPONS[name]
    dx, dy = ANG[ang]
    px_, py_ = -dy, dx            # perpendicular
    gx, gy = int(gx), int(gy)
    if kind == 'blade':
        # grip behind the hand, guard, blade
        cv.line(gx - dx * 2, gy - dy * 2, gx, gy, R(mats['grip'])[1])
        cv.px(gx - dx * 2, gy - dy * 2, R(mats['guard'])[2])  # pommel
        bx, by_ = gx + dx, gy + dy
        for s in (-1, 0, 1):
            cv.px(bx + px_ * s, by_ + py_ * s, R(mats['guard'])[2 if s <= 0 else 1])
        sx, sy = bx + dx, by_ + dy
        ex, ey = sx + dx * (L - 1), sy + dy * (L - 1)
        if dx and dy:
            cv.line(sx + 1 * (1 if dx > 0 else 0), sy, ex, ey - (0), R(mats['blade'])[1])
        else:
            cv.line(sx + px_, sy + py_, ex + px_, ey + py_, R(mats['blade'])[1])
        cv.line(sx, sy, ex, ey, R(mats['blade'])[3 if mats['blade'] in ('neon_pink',) else 2])
        cv.px(ex + dx, ey + dy, R(mats['blade'])[3])
        if mats.get('curved'):
            cv.px(ex + dx + px_, ey + dy + py_, R(mats['blade'])[2])
    elif kind in ('axe', 'hammer', 'hoe', 'scythe', 'pick'):
        ex, ey = gx + dx * L, gy + dy * L
        cv.line(gx - dx * 2, gy - dy * 2, ex, ey, R(mats['shaft'])[2])
        if kind == 'axe':
            hm = Canvas(cv.w, cv.h)
            for t in range(0, 3):
                for s in range(1, 4 - (t == 0)):
                    hm.px(ex - dx * t + px_ * s, ey - dy * t + py_ * s, R(mats['head'])[2 if t < 2 else 1])
            hm.px(ex + px_ * 3 + dx, ey + py_ * 3 + dy, R(mats['head'])[3])
            cv.paste(hm)
        elif kind == 'hammer':
            for t in range(-1, 2):
                for s in range(-2, 3):
                    cv.px(ex - dx * t + px_ * s, ey - dy * t + py_ * s, R(mats['head'])[2 if s < 1 else 1])
        elif kind == 'hoe':
            for s in range(1, 4):
                cv.px(ex + px_ * s, ey + py_ * s, R(mats['head'])[2])
            cv.px(ex + px_ * 3 - dx, ey + py_ * 3 - dy, R(mats['head'])[1])
        elif kind == 'pick':
            for s in range(-3, 4):
                cv.px(ex + px_ * s - dx * (abs(s) == 3), ey + py_ * s - dy * (abs(s) == 3), R(mats['head'])[2 if s < 0 else 1])
        else:  # scythe
            pts = [(ex + px_ * s - dx * (s * s // 4), ey + py_ * s - dy * (s * s // 4)) for s in range(0, 7)]
            for i, (x, y) in enumerate(pts):
                cv.px(x, y, R(mats['head'])[3 if i == 6 else 2])
                cv.px(x - dx, y - dy, R(mats['head'])[1])
    elif kind == 'spear':
        ex, ey = gx + dx * (L - 4), gy + dy * (L - 4)
        cv.line(gx - dx * 4, gy - dy * 4, ex, ey, R(mats['shaft'])[2])
        for t in range(1, 4):
            cv.px(ex + dx * t, ey + dy * t, R(mats['head'])[2 if t < 3 else 3])
        cv.px(ex + dx + px_, ey + dy + py_, R(mats['head'])[1])
        cv.px(ex + dx - px_, ey + dy - py_, R(mats['head'])[1])
        cv.px(ex, ey, R('cloth_red')[2])
    elif kind == 'bow':
        pts = []
        for i in range(-6, 7):
            s = i / 6
            fwd = round(2.5 * (1 - s * s))
            pts.append((gx + px_ * i + dx * fwd, gy + py_ * i + dy * fwd))
        for (x, y) in pts:
            cv.px(x, y, R(mats['wood'])[2])
        drawn = p is not None and p.anim == 'attack' and p.f in (0, 1)
        sx_off = -2 if drawn else 0
        a, b = pts[0], pts[-1]
        mid = (gx + dx * sx_off, gy + dy * sx_off)
        cv.line(a[0], a[1], mid[0], mid[1], R(mats['string'])[1])
        cv.line(mid[0], mid[1], b[0], b[1], R(mats['string'])[1])
        if drawn:
            cv.line(mid[0], mid[1], gx + dx * 5, gy + dy * 5, R('wood_light')[2])
            cv.px(gx + dx * 5, gy + dy * 5, R('steel')[3])
        if p is not None and p.muzzle:
            cv.line(gx + dx * 6, gy + dy * 6, gx + dx * 9, gy + dy * 9, R('wood_light')[2])
            cv.px(gx + dx * 10, gy + dy * 10, R('steel')[3])
    elif kind == 'crossbow':
        cv.line(gx - dx * 2, gy - dy * 2, gx + dx * L, gy + dy * L, R(mats['wood'])[2])
        fx, fy = gx + dx * (L - 1), gy + dy * (L - 1)
        for s in range(-3, 4):
            cv.px(fx + px_ * s - dx * (abs(s) >= 2), fy + py_ * s - dy * (abs(s) >= 2), R(mats['metal'])[2])
        if p is not None and p.muzzle:
            cv.line(fx + dx * 3, fy + dy * 3, fx + dx * 6, fy + dy * 6, R('steel')[2])
    elif kind in ('staff', 'wand'):
        ex, ey = gx + dx * L, gy + dy * L
        cv.line(gx - dx * (3 if kind == 'staff' else 1), gy - dy * (3 if kind == 'staff' else 1), ex, ey, R(mats['shaft'])[2])
        if kind == 'staff':
            if mats.get('skull'):
                sk = Canvas(cv.w, cv.h)
                sk.fill(sk.mask_ellipse(ex + dx * 2 + 0.5, ey + dy * 2 + 0.5, 2.2, 2.2), 'bone', 2)
                sk.px(ex + dx * 2 - 1 + (dx > 0), ey + dy * 2, OUTLINE)
                sk.px(ex + dx * 2 + 1 - (dx < 0), ey + dy * 2, R(mats['orb'])[3])
                cv.paste(sk)
            else:
                orb = cv.mask_ellipse(ex + dx * 2 + 0.5, ey + dy * 2 + 0.5, 1.8, 1.8)
                cv.shade(orb, mats['orb'])
                cv.px(ex + px_, ey + py_, R(mats['shaft'])[1]); cv.px(ex - px_, ey - py_, R(mats['shaft'])[1])
        else:
            cv.px(ex + dx, ey + dy, R(mats['orb'])[3])
        if p is not None and p.sparkle:
            sx, sy = ex + dx * 3, ey + dy * 3
            col = R(mats['orb'])
            for (ox, oy) in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
                cv.px(sx + ox, sy + oy, col[2])
            for (ox, oy) in [(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)]:
                cv.px(sx + ox, sy + oy, col[3])
    elif kind == 'wrench':
        ex, ey = gx + dx * L, gy + dy * L
        cv.line(gx - dx, gy - dy, ex, ey, R(mats['head'])[2])
        for s in (-1, 1):
            cv.px(ex + px_ * s, ey + py_ * s, R(mats['head'])[2])
            cv.px(ex + px_ * s + dx, ey + py_ * s + dy, R(mats['head'])[1])
    elif kind == 'gun':
        ex, ey = gx + dx * L, gy + dy * L
        cv.line(gx - dx, gy - dy, ex, ey, R(mats['body'])[2])
        cv.line(gx - dx + px_, gy - dy + py_, ex - dx + px_, ey - dy + py_, R(mats['body'])[1])
        cv.px(gx - px_, gy - py_, R(mats['body'])[0])
        cv.px(ex, ey, R(mats['glow'])[3])
        if p is not None and p.muzzle:
            mx, my = ex + dx * 2, ey + dy * 2
            for (ox, oy) in [(0, 0), (dx, dy), (px_, py_), (-px_, -py_)]:
                cv.px(mx + ox, my + oy, R(mats['glow'])[3])
            cv.px(mx + dx * 2, my + dy * 2, R(mats['glow'])[2])
    elif kind == 'flask':
        fl = Canvas(cv.w, cv.h)
        fl.fill(fl.mask_rect(gx - 1, gy - 2, gx + 1, gy), 'glass', 3)
        fl.fill(fl.mask_rect(gx - 1, gy - 1, gx + 1, gy), mats['liquid'], 2)
        fl.px(gx, gy - 3, R('cloth_white')[2]); fl.px(gx, gy - 4, R('wood')[2])
        if p is not None and p.muzzle:
            for (ox, oy) in [(3, -4), (5, -3), (4, -6)]:
                fl.px(gx + ox * (1 if ang != 180 else -1), gy + oy, R(mats['liquid'])[3])
        cv.paste(fl)


def draw_weapon(p, name):
    cv = Canvas(32)
    gx, gy = _grip_point(p)
    ang = p.wangle
    kind = WEAPONS[name][0]
    if p.anim != 'attack':
        if kind in ('spear', 'staff', 'wand', 'hoe', 'scythe', 'pick'):
            ang = 90
        elif kind in ('bow', 'crossbow', 'gun', 'flask'):
            ang = {'side': 0, 'down': 270, 'up': 90}[p.dir]
            if kind == 'bow':
                ang = 0 if p.dir == 'side' else (180 if p.dir == 'down' else 0)
    draw_weapon_at(cv, name, gx, gy, ang, p)
    cv.outline(OUTLINE)
    if p.dir == 'up' and p.anim != 'attack':
        pass
    return _maybe_lie(cv, p)


def draw_offhand(p, name):
    cv = Canvas(32)
    hx, hy = p.ohand
    by = p.by + p.crouch
    if p.dir == 'side':
        hx, hy = 18 + p.bx, 19 + by
    show_front = p.dir != 'up'
    if name in ('round_shield', 'buckler', 'energy_shield', 'kite_shield'):
        if name == 'kite_shield':
            m = cv.mask_poly([(hx - 3, hy - 4), (hx + 4, hy - 4), (hx + 4, hy + 1), (hx + 0.5, hy + 5), (hx - 3, hy + 1)])
        else:
            r = 2.6 if name == 'buckler' else 3.6
            m = cv.mask_ellipse(hx + 1, hy + 0.5, r if p.dir != 'side' else r * 0.6, r + 0.4)
        if not show_front:
            cv.shade(m, 'wood_dark')
            cv.fill(m & cv.mask_rect(hx - 4, hy, hx + 5, hy), 'leather', 1)
        elif name == 'round_shield':
            cv.shade(m, 'wood')
            cv.img[m & _edge(m)] = rgba(R('iron')[1])
            cv.fill(cv.mask_rect(hx, hy, hx + 1, hy + 1), 'iron', 3)
        elif name == 'buckler':
            cv.shade(m, 'steel')
            cv.px(hx + 1, hy, R('steel')[3])
        elif name == 'kite_shield':
            cv.shade(m, KP)
            cv.img[m & _edge(m)] = rgba(R('steel')[2])
            if p.dir == 'down':
                cv.fill(cv.mask_rect(hx, hy - 3, hx + 1, hy + 3) & m, KS, 2)
                cv.fill(cv.mask_rect(hx - 2, hy - 1, hx + 3, hy) & m, KS, 2)
        else:
            cv.fill(m, 'neon_cyan', 2)
            cv.img[m & ~_edge(m) & ((np.mgrid[0:32, 0:32][0] % 2) == 0)] = rgba(R('neon_cyan')[1])
            cv.img[m & _edge(m)] = rgba(R('neon_cyan')[3])
    elif name == 'tome':
        m = cv.mask_rect(hx - 1, hy - 2, hx + 2, hy + 1)
        cv.shade(m, KP)
        cv.vline(hx + 2, hy - 2, hy + 1, R('cloth_white')[2])
        cv.px(hx, hy - 1, R('gold')[3])
    elif name == 'lantern':
        cv.vline(hx + 0, hy - 1, hy + 1, R('iron')[1])
        m = cv.mask_rect(hx - 1, hy + 2, hx + 1, hy + 5)
        cv.fill(m, 'fire', 3)
        cv.img[m & _edge(m)] = rgba(R('iron')[1])
        cv.px(hx, hy + 3, R('fire')[3])
    cv.outline(OUTLINE)
    if p.dir == 'side':
        cv.img[cv.mask_rect(p.whand[0], p.whand[1], p.whand[0] + 1, p.whand[1] + 1)] = 0
    return _maybe_lie(cv, p)


# =============================================================================
# Sheet rendering
# =============================================================================
def render_sheet(draw_fn, sex, wclass='swing'):
    rows = []
    for (anim, n, fps, loop) in ANIMS:
        for d in DIRS:
            row = []
            for f in range(n):
                p = make_pose(anim, d, f, sex, wclass)
                row.append(draw_fn(p))
            rows.append(row)
    s = Canvas(COLS * FW, ROWS * FH)
    for ry, row in enumerate(rows):
        for cx, fr in enumerate(row):
            s.paste(fr, cx * FW, ry * FH)
    return s


def anim_table():
    """Animation metadata shared by Godot + web tooling."""
    out = []
    for ai, (anim, n, fps, loop) in enumerate(ANIMS):
        for di, d in enumerate(DIRS):
            out.append(dict(name=f'{anim}_{d}', row=ai * len(DIRS) + di, frames=n, fps=fps, loop=loop))
    return out
