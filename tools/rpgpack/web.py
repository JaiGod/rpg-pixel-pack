"""Assemble the GitHub Pages site (docs/) from demo/web + a copy of the pack's art."""
import json
import os
import shutil

COPY_DIRS = ['characters', 'monsters', 'environments', 'buildings', 'animations', 'equipment', 'furniture', 'interiors', 'assets']


def _j(root, p):
    with open(os.path.join(root, p)) as f:
        return json.load(f)


def build(root):
    src = os.path.join(root, 'demo', 'web')
    docs = os.path.join(root, 'docs')
    site = docs  # site lives at docs/ (GitHub Pages: main branch, /docs folder)
    os.makedirs(site, exist_ok=True)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(site, name)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    pack = os.path.join(site, 'pack')
    if os.path.exists(pack):
        shutil.rmtree(pack)
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(root, d), os.path.join(pack, d), ignore=shutil.ignore_patterns('*.json'))
    prev = os.path.join(site, 'previews')
    if os.path.exists(prev):
        shutil.rmtree(prev)
    shutil.copytree(os.path.join(root, 'previews'), prev)
    data = {
        'characters': _j(root, 'characters/characters.json'),
        'monsters': _j(root, 'monsters/monsters.json'),
        'buildings': _j(root, 'buildings/buildings.json'),
        'environments': _j(root, 'environments/environments.json'),
        'animations': _j(root, 'animations/animations.json'),
        'equipment': _j(root, 'equipment/equipment.json'),
        'furniture': _j(root, 'furniture/furniture.json'),
        'interiors': _j(root, 'interiors/interiors.json'),
        'ramps': _j(root, 'assets/palette/ramps.json'),
        'manifest': _j(root, 'pack_manifest.json') if os.path.exists(os.path.join(root, 'pack_manifest.json')) else {},
    }
    with open(os.path.join(site, 'data.js'), 'w') as f:
        f.write('window.PACK = ' + json.dumps(data, separators=(',', ':')) + ';\n')
    open(os.path.join(site, '.nojekyll'), 'w').close()
