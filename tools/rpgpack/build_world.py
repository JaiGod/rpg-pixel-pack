"""Export equipment, furniture, environments, buildings, interiors, animations, palette and UI."""
import json
import os
from multiprocessing import Pool

from PIL import Image

from .core import Canvas, save, R, rgba
from .palette import RAMPS, all_colors, KEY_PRIMARY, KEY_SECONDARY, OUTLINE
from . import equipment as EQ
from . import furniture as FU
from . import environments as EN
from . import buildings as BU
from . import interiors as IN
from . import anims as AN


def _w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=1)


# ---------------------------------------------------------------- palette
def build_palette(out):
    cols = all_colors()
    d = os.path.join(out, 'assets', 'palette')
    os.makedirs(d, exist_ok=True)
    # swatch strip + ramp chart
    names = list(RAMPS)
    chart = Canvas(4 * 12 + 2, len(names) * 12)
    for i, n in enumerate(names):
        for j, c in enumerate(RAMPS[n]):
            chart.rect(j * 12, i * 12, j * 12 + 11, i * 12 + 11, c)
    save(chart, os.path.join(d, 'ramps.png'))
    strip = Canvas(len(cols), 1)
    for i, c in enumerate(cols):
        strip.px(i, 0, c)
    save(strip, os.path.join(d, 'palette.png'))
    with open(os.path.join(d, 'palette.hex'), 'w') as f:
        f.write('\n'.join('%02x%02x%02x' % c for c in cols) + '\n')
    with open(os.path.join(d, 'palette.gpl'), 'w') as f:
        f.write('GIMP Palette\nName: RPG Pixel Pack\nColumns: 4\n#\n')
        for n in names:
            for j, c in enumerate(RAMPS[n]):
                f.write('%3d %3d %3d\t%s_%d\n' % (c[0], c[1], c[2], n, j))
    _w(os.path.join(d, 'ramps.json'), {n: ['#%02x%02x%02x' % c for c in r] for n, r in RAMPS.items()})
    _w(os.path.join(d, 'swap_keys.json'), {'primary': ['#%02x%02x%02x' % c for c in KEY_PRIMARY],
                                           'secondary': ['#%02x%02x%02x' % c for c in KEY_SECONDARY]})
    return len(cols)


# ---------------------------------------------------------------- UI kit (used by the inventory demo)
def build_ui(out):
    d = os.path.join(out, 'assets', 'ui')
    # 9-slice panel 48x48 (16px borders)
    p = Canvas(48, 48)
    p.rect(0, 0, 47, 47, OUTLINE)
    p.rect(1, 1, 46, 46, R('wood_dark')[1])
    p.rect(3, 3, 44, 44, R('wood')[2])
    p.rect(4, 4, 43, 43, R('cloth_tan')[2])
    p.hline(4, 43, 4, R('cloth_tan')[3]); p.vline(4, 4, 43, R('cloth_tan')[3])
    for (x, y) in [(2, 2), (45, 2), (2, 45), (45, 45)]:
        p.px(x, y, R('gold')[3])
    save(p, os.path.join(d, 'panel.png'))
    # slot 36x36 + selected
    for name, rim in (('slot', 'wood'), ('slot_selected', 'gold')):
        s = Canvas(36, 36)
        s.rect(0, 0, 35, 35, OUTLINE)
        s.rect(1, 1, 34, 34, R(rim)[2])
        s.rect(3, 3, 32, 32, R('cloth_tan')[0])
        s.hline(3, 32, 3, R('leather_dark')[1]); s.vline(3, 3, 32, R('leather_dark')[1])
        if name == 'slot_selected':
            s.rect(1, 1, 34, 2, R('gold')[3])
        save(s, os.path.join(d, f'{name}.png'))
    # icons 16x16
    def icon(fn, name):
        c = Canvas(16)
        fn(c)
        c.outline(OUTLINE)
        save(c, os.path.join(d, f'{name}.png'))
    icon(lambda c: (c.shade(c.mask_ellipse(5, 6, 3.6, 3.6) | c.mask_ellipse(10.5, 6, 3.6, 3.6) | c.mask_poly([(1.5, 7), (14, 7), (8, 14)]), 'cloth_red')), 'heart')
    icon(lambda c: (c.shade(c.mask_ellipse(8, 8, 5.5, 5.5), 'gold'), c.vline(8, 5, 10, R('gold')[1])), 'coin')
    icon(lambda c: c.shade(c.mask_poly([(8, 1), (13, 8), (8, 15), (3, 8)]), 'magic_blue'), 'mana')
    icon(lambda c: c.shade(c.mask_poly([(8, 1), (10, 6), (15, 6), (11, 9), (13, 15), (8, 11), (3, 15), (5, 9), (1, 6), (6, 6)]), 'gold'), 'star')
    # bars
    b = Canvas(64, 8)
    b.rect(0, 0, 63, 7, OUTLINE); b.rect(1, 1, 62, 6, R('tech_dark')[1])
    save(b, os.path.join(d, 'bar_back.png'))
    for n, rr in (('bar_health', 'ruby'), ('bar_mana', 'magic_blue'), ('bar_xp', 'poison')):
        f = Canvas(62, 6)
        f.rect(0, 0, 61, 5, R(rr)[2]); f.hline(0, 61, 0, R(rr)[3]); f.hline(0, 61, 5, R(rr)[1])
        save(f, os.path.join(d, f'{n}.png'))
    return 11


# ---------------------------------------------------------------- simple sprite sets
def _equip(i):
    return i, EQ.EQUIPMENT[i][3]()


def _furn(i):
    return i, FU.FURNITURE[i][4]()


def _bld(i):
    return i, BU.BUILDINGS[i][3]()


def build_equipment(out, pool):
    meta = []
    res = dict(pool.map(_equip, range(len(EQ.EQUIPMENT))))
    atlas = Canvas(16 * 32, ((len(EQ.EQUIPMENT) + 15) // 16) * 32)
    for i, (eid, cat, name, _) in enumerate(EQ.EQUIPMENT):
        path = f'equipment/{cat}/{eid}.png'
        save(res[i], os.path.join(out, path))
        atlas.paste(res[i], (i % 16) * 32, (i // 16) * 32)
        vis = EQ.VISUAL.get(eid)
        meta.append(dict(id=eid, category=cat, name=name, file=path, atlas_index=i, atlas_cell=[i % 16, i // 16],
                         slot=EQ.SLOT[cat], character_layer=vis[0] if vis else None,
                         colors=vis[1] if vis and vis[1] else None))
    save(atlas, os.path.join(out, 'equipment', 'equipment_atlas.png'))
    _w(os.path.join(out, 'equipment', 'equipment.json'), dict(icon_size=[32, 32], atlas_columns=16, items=meta))
    return len(meta)


def build_furniture(out, pool):
    meta = []
    res = dict(pool.map(_furn, range(len(FU.FURNITURE))))
    for i, (fid, cat, name, size, _) in enumerate(FU.FURNITURE):
        path = f'furniture/{cat}/{fid}.png'
        save(res[i], os.path.join(out, path))
        meta.append(dict(id=fid, category=cat, name=name, file=path, size=list(size),
                         footprint_tiles=[size[0] // 32, 1 if size[1] <= 32 else size[1] // 32 - 1],
                         origin='bottom-left tile'))
    _w(os.path.join(out, 'furniture', 'furniture.json'), dict(items=meta))
    return len(meta)


def build_buildings(out, pool):
    meta = []
    res = dict(pool.map(_bld, range(len(BU.BUILDINGS))))
    for i, (bid, cat, name, _) in enumerate(BU.BUILDINGS):
        cv = res[i]
        path = f'buildings/{cat}/{bid}.png'
        save(cv, os.path.join(out, path))
        w, h = cv.w, cv.h
        # collision: lower 45% of the sprite; door: bottom-center tile
        meta.append(dict(id=bid, category=cat, name=name, file=path, size=[w, h], size_tiles=[w // 32, h // 32],
                         collision_rect=[4, int(h * 0.5), w - 8, int(h * 0.5) - 6], door_tile=[(w // 32) // 2, h // 32 - 1]))
    _w(os.path.join(out, 'buildings', 'buildings.json'), dict(items=meta))
    return len(meta)


def build_environments(out):
    meta = {'tile_size': [32, 32], 'atlas_columns': 8, 'atlas_rows': 4,
            'layout': {
                'row0': 'cols 0-3 base ground variants, cols 4-7 decorated base ground',
                'rows1-2': '16 corner-matched transition tiles; index = TL*8 + TR*4 + BL*2 + BR (1 = secondary)',
                'row3': 'cols 0-3 secondary terrain variants, cols 4-7 obstacle tiles (with collision)'},
            'biomes': [], 'props': []}
    for b in EN.BIOMES:
        bid, name, (bk, br, bl), (sk, sr, sl, edge), decos, obst = b
        at = EN.build_tileset(b)
        path = f'environments/tilesets/{bid}.png'
        save(at, os.path.join(out, path))
        meta['biomes'].append(dict(id=bid, name=name, file=path, base_terrain=bl, secondary_terrain=sl,
                                   decorations=decos, obstacles=obst,
                                   godot_tileset=f'res://rpg_pixel_pack/resources/tilesets/{bid}.tres'))
    for (pid, biome, name, size, fn) in EN.BIOME_PROPS:
        path = f'environments/props/{pid}.png'
        save(fn(), os.path.join(out, path))
        meta['props'].append(dict(id=pid, biome=biome, name=name, size=list(size), file=path))
    _w(os.path.join(out, 'environments', 'environments.json'), meta)
    return len(meta['biomes']), len(meta['props'])


def build_interiors(out):
    at = IN.build_tileset()
    save(at, os.path.join(out, 'interiors', 'tileset', 'interior_tileset.png'))
    rooms = []
    for rm in IN.ROOMS:
        cv, lay = IN.render_room(rm)
        path = f"interiors/rooms/{rm['category']}/{rm['id']}.png"
        save(cv, os.path.join(out, path))
        lay['file'] = path
        _w(os.path.join(out, 'interiors', 'rooms', rm['category'], rm['id'] + '.json'), lay)
        rooms.append(dict(id=rm['id'], category=rm['category'], name=rm['name'], file=path,
                          layout=f"interiors/rooms/{rm['category']}/{rm['id']}.json", size_tiles=[rm['w'], rm['h']]))
    _w(os.path.join(out, 'interiors', 'interiors.json'), dict(
        tileset='interiors/tileset/interior_tileset.png',
        tileset_layout={'row0': IN.FLOORS, 'row1': ['%s (upper)' % w for w in IN.WALLS], 'row2': ['%s (lower)' % w for w in IN.WALLS],
                        'row3': ['wall cap', 'door mat', 'shadowed floor']},
        rooms=rooms))
    return len(rooms)


def build_animations(out):
    meta = []
    for (aid, cat, name, fps, loop, fn) in AN.ANIMATIONS:
        frames = fn()
        w, h = frames[0].w, frames[0].h
        strip = Canvas(w * len(frames), h)
        for i, fr in enumerate(frames):
            strip.paste(fr, i * w, 0)
        path = f'animations/{cat}/{aid}.png'
        save(strip, os.path.join(out, path))
        meta.append(dict(id=aid, category=cat, name=name, file=path, frame_size=[w, h], frames=len(frames), fps=fps, loop=loop))
    _w(os.path.join(out, 'animations', 'animations.json'), dict(layout='horizontal strip', items=meta))
    return len(meta)


def build(out, procs=4):
    counts = {}
    counts['palette_colors'] = build_palette(out)
    counts['ui'] = build_ui(out)
    with Pool(procs) as pool:
        counts['equipment'] = build_equipment(out, pool)
        counts['furniture'] = build_furniture(out, pool)
        counts['buildings'] = build_buildings(out, pool)
    counts['tilesets'], counts['environment_props'] = build_environments(out)
    counts['interiors'] = build_interiors(out)
    counts['animations'] = build_animations(out)
    return counts
