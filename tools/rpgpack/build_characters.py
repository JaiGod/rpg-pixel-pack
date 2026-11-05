"""Export character layers, baked presets, previews and metadata."""
import json
import os
from multiprocessing import Pool

from PIL import Image

from . import characters as C
from .core import Canvas, key_map, save, upscale
from .palette import SKINS, HAIR_COLORS
from .presets import PRESETS

LAYER_ORDER = ['hair_back', 'body', 'legs', 'torso', 'cape', 'hair', 'head', 'accessory', 'offhand', 'weapon']
SEXES = ['male', 'female']
LONG_HAIR = [k for k, v in C.HAIR_STYLES.items() if v['behind']]


def _layer_fn(kind, style, wclass):
    if kind == 'body':
        return lambda p: C.draw_body(p, style)
    if kind == 'hair':
        return lambda p: C.draw_hair(p, style)
    if kind == 'hair_back':
        return lambda p: C.draw_hair(p, style, behind=True)
    if kind == 'torso':
        return lambda p: C.draw_torso(p, style)
    if kind == 'legs':
        return lambda p: C.draw_legs(p, style)
    if kind == 'head':
        return lambda p: C.draw_head(p, style)
    if kind == 'accessory':
        return lambda p: C.draw_acc(p, style)
    if kind == 'cape':
        return lambda p: C.draw_cape(p, style)
    if kind == 'weapon':
        return lambda p: C.draw_weapon(p, style)
    if kind == 'offhand':
        return lambda p: C.draw_offhand(p, style)


def layer_jobs():
    jobs = []
    for sex in SEXES:
        for s in SKINS:
            jobs.append((sex, 'body', s))
        for s in C.HAIR_STYLES:
            jobs.append((sex, 'hair', s))
        for s in LONG_HAIR:
            jobs.append((sex, 'hair_back', s))
        for s in C.TORSO_STYLES:
            jobs.append((sex, 'torso', s))
        for s in C.LEG_STYLES:
            jobs.append((sex, 'legs', s))
        for s in C.HEAD_STYLES:
            jobs.append((sex, 'head', s))
        for s in C.ACC_STYLES:
            jobs.append((sex, 'accessory', s))
        for s in C.CAPE_STYLES:
            jobs.append((sex, 'cape', s))
        for s in C.WEAPONS:
            jobs.append((sex, 'weapon', s))
        for s in C.OFFHANDS:
            jobs.append((sex, 'offhand', s))
    return jobs


def _render_layer(job):
    out, sex, kind, style = job
    wclass = C.weapon_class(style) if kind == 'weapon' else 'swing'
    sheet = C.render_sheet(_layer_fn(kind, style, wclass), sex, wclass)
    path = os.path.join(out, 'characters', 'layers', sex, kind, f'{style}.png')
    save(sheet, path)
    return path


def preset_layers(pr, sex):
    """[(kind, style, recolor_map)] in draw order for a preset."""
    L = []
    hs = pr['hair'][sex]
    hc = pr['hair_color']
    t, tp, ts = pr['torso']
    if hs in LONG_HAIR and not (pr['head'] and pr['head'][0] in ('knight_helm', 'space_helmet', 'hood', 'necro_cowl')):
        L.append(('hair_back', hs, key_map(hc)))
    L.append(('body', pr['skin'][sex], {}))
    l, lp, ls = pr['legs']
    L.append(('legs', l, key_map(lp, ls)))
    L.append(('torso', t, key_map(tp, ts)))
    if pr['cape']:
        L.append(('cape', pr['cape'], key_map(tp if tp not in ('cloth_white',) else 'cloth_red', 'gold')))
    if not (pr['head'] and pr['head'][0] in ('knight_helm', 'space_helmet', 'hood', 'necro_cowl')):
        L.append(('hair', hs, key_map(hc)))
    acc = pr['acc'][sex]
    if pr['head']:
        h, hp, hs2 = pr['head']
        L.append(('head', h, key_map(hp, hs2)))
    if acc and not (acc == 'beard' and pr['head'] and pr['head'][0] in ('knight_helm', 'space_helmet')):
        L.append(('accessory', acc, key_map(hc if acc == 'beard' else tp, ts)))
    if pr['offhand']:
        L.append(('offhand', pr['offhand'], key_map(tp, ts)))
    if pr['weapon']:
        L.append(('weapon', pr['weapon'], {}))
    return L


def _bake(job):
    out, pr, sex = job
    s = None
    for kind, style, cmap in preset_layers(pr, sex):
        src = Image.open(os.path.join(out, 'characters', 'layers', sex, kind, f'{style}.png'))
        cv = Canvas.from_pil(src)
        if cmap:
            cv.recolor(cmap)
        if s is None:
            s = cv
        else:
            s.paste(cv)
    path = os.path.join(out, 'characters', 'presets', pr['cls'].lower().replace(' ', '_'), f"{pr['id']}_{sex}.png")
    save(s, path)
    return path


def build(out, procs=8):
    jobs = [(out,) + j for j in layer_jobs()]
    with Pool(procs) as pool:
        paths = pool.map(_render_layer, jobs)
        baked = pool.map(_bake, [(out, pr, sex) for pr in PRESETS for sex in SEXES])
    meta = {
        'frame_size': [C.FW, C.FH],
        'sheet_columns': C.COLS,
        'sheet_rows': C.ROWS,
        'directions': C.DIRS,
        'side_faces': 'right (flip_h for left)',
        'animations': C.anim_table(),
        'layer_order': LAYER_ORDER,
        'palette_swap': {
            'primary_keys': [list(k) for k in __import__('rpgpack.palette', fromlist=['x']).KEY_PRIMARY],
            'secondary_keys': [list(k) for k in __import__('rpgpack.palette', fromlist=['x']).KEY_SECONDARY],
            'note': 'Tintable layers use these exact key colors; replace with any ramp from assets/palette/ramps.json',
        },
        'layers': {
            'body': {'styles': SKINS, 'tintable': False},
            'hair': {'styles': list(C.HAIR_STYLES), 'tintable': 'primary', 'colors': HAIR_COLORS},
            'hair_back': {'styles': LONG_HAIR, 'tintable': 'primary'},
            'torso': {'styles': {k: v['desc'] for k, v in C.TORSO_STYLES.items()}, 'tintable': 'primary+secondary'},
            'legs': {'styles': C.LEG_STYLES, 'tintable': 'primary+secondary'},
            'head': {'styles': C.HEAD_STYLES, 'tintable': 'primary+secondary'},
            'accessory': {'styles': C.ACC_STYLES, 'tintable': 'primary+secondary'},
            'cape': {'styles': C.CAPE_STYLES, 'tintable': 'primary+secondary'},
            'weapon': {'styles': {k: {'kind': v[0], 'attack': v[1]} for k, v in C.WEAPONS.items()}, 'tintable': False},
            'offhand': {'styles': C.OFFHANDS, 'tintable': 'primary+secondary (kite_shield, tome)'},
        },
        'presets': [],
    }
    for pr in PRESETS:
        d = dict(pr)
        d['files'] = {sex: f"presets/{pr['cls'].lower().replace(' ', '_')}/{pr['id']}_{sex}.png" for sex in SEXES}
        d['layers'] = {sex: [[k, s, {f'{a}': list(b) for a, b in []}] for k, s, m in preset_layers(pr, sex)] for sex in SEXES}
        d['layer_recipe'] = {sex: [{'layer': k, 'style': s,
                                    'primary': _ramp_name(m, 0), 'secondary': _ramp_name(m, 1)}
                                   for k, s, m in preset_layers(pr, sex)] for sex in SEXES}
        del d['layers']
        meta['presets'].append(d)
    with open(os.path.join(out, 'characters', 'characters.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    return len(paths), len(baked)


def _ramp_name(m, ch):
    from .palette import RAMPS, KEY_PRIMARY, KEY_SECONDARY
    key = (KEY_PRIMARY if ch == 0 else KEY_SECONDARY)[1]
    if key not in m:
        return None
    col = m[key]
    for n, r in RAMPS.items():
        if r[1] == col:
            return n
    return None
