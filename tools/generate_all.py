#!/usr/bin/env python3
"""Regenerate the entire RPG Pixel Pack from source.

    python tools/generate_all.py            # everything
    python tools/generate_all.py --skip-godot

Requires Python 3.9+, Pillow and NumPy.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from rpgpack import build_characters, build_monsters, build_world  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-godot', action='store_true')
    ap.add_argument('--skip-previews', action='store_true')
    ap.add_argument('--procs', type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    t0 = time.time()
    counts = {}
    print('characters ...', flush=True)
    layers, baked = build_characters.build(ROOT, a.procs)
    counts['character_layer_sheets'] = layers
    counts['character_presets'] = baked // 2
    counts['character_baked_sheets'] = baked
    print('monsters ...', flush=True)
    counts['monsters'] = build_monsters.build(ROOT, a.procs)
    print('world ...', flush=True)
    counts.update(build_world.build(ROOT, a.procs))
    if not a.skip_previews:
        print('previews ...', flush=True)
        from rpgpack import previews
        previews.build(ROOT)
    if not a.skip_godot:
        print('godot ...', flush=True)
        from rpgpack import godot
        counts.update(godot.build(ROOT))
    # manifest
    pngs = 0
    for d in ('assets', 'characters', 'monsters', 'equipment', 'buildings', 'environments', 'interiors', 'furniture', 'animations'):
        for _, _, fs in os.walk(os.path.join(ROOT, d)):
            pngs += sum(1 for f in fs if f.endswith('.png'))
    counts['png_files'] = pngs
    counts['headline_assets'] = (counts['character_presets'] + counts['monsters'] + counts['equipment'] + counts['furniture']
                                 + counts['buildings'] + counts['tilesets'] + counts['environment_props']
                                 + counts['interiors'] + counts['animations'])
    with open(os.path.join(ROOT, 'pack_manifest.json'), 'w') as f:
        json.dump(dict(name='RPG Pixel Pack', version='1.0.0', tile_size=32, counts=counts), f, indent=1)
    print('web demo ...', flush=True)
    from rpgpack import web
    web.build(ROOT)
    print(json.dumps(counts, indent=1))
    print('done in %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
