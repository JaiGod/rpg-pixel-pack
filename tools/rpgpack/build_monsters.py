"""Export monsters + metadata."""
import json
import os
from multiprocessing import Pool

from . import characters as C
from . import monsters as M
from .core import Canvas, key_map, save


def _slug(s):
    return s.lower().replace(' ', '_')


def _humanoid(job):
    out, (mid, fam, name, kind, ramp, layers, weapon, offhand) = job
    body = M.monster_body(kind, ramp)
    wclass = C.weapon_class(weapon) if weapon else 'none'
    fns = {'legs': C.draw_legs, 'torso': C.draw_torso, 'head': C.draw_head, 'cape': C.draw_cape}
    order = ['legs', 'torso', 'cape', 'head']
    layers = sorted(layers, key=lambda l: order.index(l[0]))

    def comp(p):
        cv = body(p)
        for (k, style, P, S) in layers:
            cv.paste(fns[k](p, style).recolor(key_map(P, S)))
        if offhand:
            cv.paste(C.draw_offhand(p, offhand).recolor(key_map(layers[0][2], layers[0][3])))
        if weapon:
            cv.paste(C.draw_weapon(p, weapon))
        return cv
    sheet = C.render_sheet(comp, 'male', wclass)
    path = f'monsters/{_slug(fam)}/{mid}.png'
    save(sheet, os.path.join(out, path))
    return dict(id=mid, family=fam, name=name, layout='character', frame_size=[32, 32], file=path,
                weapon=weapon, offhand=offhand)


def _creature(job):
    out, idx = job
    mid, fam, name, size, factory = M.CREATURES[idx]
    sheet = M.render_creature(factory(), size, seed=idx)
    path = f'monsters/{_slug(fam)}/{mid}.png'
    save(sheet, os.path.join(out, path))
    return dict(id=mid, family=fam, name=name, layout='creature', frame_size=[size, size], file=path)


def build(out, procs=4):
    with Pool(procs) as pool:
        hum = pool.map(_humanoid, [(out, h) for h in M.HUMANOID_MONSTERS])
        cre = pool.map(_creature, [(out, i) for i in range(len(M.CREATURES))])
    allm = hum + cre
    fam_order = ['Slimes', 'Skeletons', 'Goblins', 'Orcs', 'Dragons', 'Robots', 'Aliens', 'Shadow Creatures', 'Bosses']
    allm.sort(key=lambda m: (fam_order.index(m['family']), m['id']))
    meta = dict(
        layouts=dict(
            character=dict(columns=C.COLS, rows=C.ROWS, directions=C.DIRS, animations=C.anim_table(),
                           note='Same layout as player characters; side faces right'),
            creature=dict(columns=5, rows=len(M.MON_ANIMS), directions=['side'], animations=M.anim_table(),
                          note='Single facing (right). Flip horizontally for left.'),
        ),
        monsters=allm,
    )
    with open(os.path.join(out, 'monsters', 'monsters.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    return len(allm)
