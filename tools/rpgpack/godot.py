"""Generate Godot 4 resources (.tres) and copy the pack into godot_project/rpg_pixel_pack/."""
import json
import os
import shutil

from . import characters as C
from . import monsters as M
from . import environments as EN

PACK = 'rpg_pixel_pack'
ART_DIRS = ['assets', 'characters', 'monsters', 'equipment', 'buildings', 'environments', 'interiors', 'furniture', 'animations']


def _j(root, p):
    with open(os.path.join(root, p)) as f:
        return json.load(f)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='\n') as f:
        f.write(text)


def _res(rel):
    return f'res://{PACK}/{rel}'


def sprite_frames_tres(tex_rel, anims, fw, fh):
    """anims: [(name, row, frames, fps, loop)] -> SpriteFrames .tres text."""
    subs, anim_txt = [], []
    sid = 0
    for (name, row, n, fps, loop) in anims:
        frames = []
        for f in range(n):
            sid += 1
            subs.append(f'[sub_resource type="AtlasTexture" id="AtlasTexture_{sid}"]\natlas = ExtResource("1_tex")\n'
                        f'region = Rect2({f * fw}, {row * fh}, {fw}, {fh})\n')
            frames.append('{\n"duration": 1.0,\n"texture": SubResource("AtlasTexture_%d")\n}' % sid)
        anim_txt.append('{\n"frames": [%s],\n"loop": %s,\n"name": &"%s",\n"speed": %.1f\n}' % (
            ', '.join(frames), 'true' if loop else 'false', name, float(fps)))
    head = f'[gd_resource type="SpriteFrames" load_steps={len(subs) + 2} format=3]\n\n' \
           f'[ext_resource type="Texture2D" path="{_res(tex_rel)}" id="1_tex"]\n\n'
    return head + '\n'.join(subs) + '\n[resource]\nanimations = [' + ', '.join(anim_txt) + ']\n'


def char_anims():
    out = []
    for (anim, n, fps, loop) in C.ANIMS:
        for d in C.DIRS:
            row = C.ANIMS.index((anim, n, fps, loop)) * len(C.DIRS) + C.DIRS.index(d)
            out.append((f'{anim}_{d}', row, n, fps, loop))
    return out


def creature_anims():
    return [(a, i, n, fps, lp) for i, (a, n, fps, lp) in enumerate(M.MON_ANIMS)]


COLOR_NAMES = {'grass': (0.35, 0.65, 0.27), 'cobble': (0.5, 0.48, 0.5)}


def tileset_tres(tex_rel, base_name, sec_name, solid_obstacles=True):
    lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', '',
             f'[ext_resource type="Texture2D" path="{_res(tex_rel)}" id="1_tex"]', '',
             '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_1"]',
             'texture = ExtResource("1_tex")', 'texture_region_size = Vector2i(32, 32)']
    bits = ['top_left_corner', 'top_right_corner', 'bottom_left_corner', 'bottom_right_corner']

    def tile(x, y, corners, prob=None):
        k = f'{x}:{y}/0'
        lines.append(f'{k} = 0')
        if prob is not None:
            lines.append(f'{k}/probability = {prob}')
        center = 1 if sum(corners) >= 2 else 0
        lines.append(f'{k}/terrain_set = 0')
        lines.append(f'{k}/terrain = {center}')
        for b, c in zip(bits, corners):
            lines.append(f'{k}/terrains_peering_bit/{b} = {c}')

    for i in range(4):
        tile(i, 0, (0, 0, 0, 0), 1.0)
    for i in range(4):
        tile(4 + i, 0, (0, 0, 0, 0), 0.15)
    for idx, c in enumerate(EN.CORNERS):
        if idx in (0, 15):
            # duplicates of the pure tiles: keep them paintable but rare
            tile(idx % 8, 1 + idx // 8, c, 0.05)
        else:
            tile(idx % 8, 1 + idx // 8, c)
    for i in range(4):
        tile(i, 3, (1, 1, 1, 1), 1.0)
    for i in range(4):
        k = f'{4 + i}:3/0'
        lines.append(f'{k} = 0')
        if solid_obstacles:
            lines.append(f'{k}/physics_layer_0/polygon_0/points = PackedVector2Array(-14, -10, 14, -10, 14, 14, -14, 14)')
    lines += ['', '[resource]', 'tile_size = Vector2i(32, 32)', 'physics_layer_0/collision_layer = 1',
              'terrain_set_0/mode = 1',
              f'terrain_set_0/terrain_0/name = "{base_name}"', 'terrain_set_0/terrain_0/color = Color(0.36, 0.62, 0.3, 1)',
              f'terrain_set_0/terrain_1/name = "{sec_name}"', 'terrain_set_0/terrain_1/color = Color(0.62, 0.52, 0.36, 1)',
              'sources/0 = SubResource("TileSetAtlasSource_1")', '']
    return '\n'.join(lines)


def interior_tileset_tres(tex_rel):
    lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', '',
             f'[ext_resource type="Texture2D" path="{_res(tex_rel)}" id="1_tex"]', '',
             '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_1"]',
             'texture = ExtResource("1_tex")', 'texture_region_size = Vector2i(32, 32)']
    full = 'PackedVector2Array(-16, -16, 16, -16, 16, 16, -16, 16)'
    for x in range(8):
        lines.append(f'{x}:0/0 = 0')
    for y in (1, 2):
        for x in range(8):
            lines.append(f'{x}:{y}/0 = 0')
            lines.append(f'{x}:{y}/0/physics_layer_0/polygon_0/points = {full}')
    lines.append('0:3/0 = 0')
    lines.append(f'0:3/0/physics_layer_0/polygon_0/points = {full}')
    lines.append('1:3/0 = 0')
    lines.append('2:3/0 = 0')
    lines += ['', '[resource]', 'tile_size = Vector2i(32, 32)', 'physics_layer_0/collision_layer = 1',
              'sources/0 = SubResource("TileSetAtlasSource_1")', '']
    return '\n'.join(lines)


def item_tres(it, stats):
    vis_style = it.get('character_layer') or ''
    cols = it.get('colors') or ['', '']
    return (f'[gd_resource type="Resource" script_class="ItemData" load_steps=3 format=3]\n\n'
            f'[ext_resource type="Script" path="res://{PACK}/scripts/item_data.gd" id="1_script"]\n'
            f'[ext_resource type="Texture2D" path="{_res(it["file"])}" id="2_icon"]\n\n'
            f'[resource]\nscript = ExtResource("1_script")\n'
            f'id = "{it["id"]}"\nname = "{it["name"]}"\ncategory = "{it["category"]}"\n'
            f'icon = ExtResource("2_icon")\nslot = "{it["slot"]}"\nlayer_style = "{vis_style}"\n'
            f'primary_ramp = "{cols[0] or ""}"\nsecondary_ramp = "{cols[1] or ""}"\n'
            f'attack = {stats[0]}\ndefense = {stats[1]}\nmagic = {stats[2]}\nvalue = {stats[3]}\n')


def _stats(it, i):
    cat = it['category']
    tier = 1 + (i % 6)
    if it['slot'] == 'weapon':
        mag = 3 * tier if cat in ('staves', 'wands') else 0
        return (4 + tier * 3 if cat not in ('staves', 'wands') else 2 + tier, 0, mag, 25 * tier)
    if cat == 'capes':
        return (0, 1 + tier, tier, 20 * tier)
    return (0, 2 + tier * 2, 1 if cat == 'helmets' and 'wizard' in it['id'] else 0, 30 * tier)


def build(root):
    gp = os.path.join(root, 'godot_project')
    pack = os.path.join(gp, PACK)
    # 1) copy art (pngs + json) so the Godot project is self-contained
    for d in ART_DIRS:
        dst = os.path.join(pack, d)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(root, d), dst)
    res = os.path.join(pack, 'resources')
    if os.path.exists(res):
        shutil.rmtree(res)
    n = {}
    # 2) SpriteFrames for baked characters
    cm = _j(root, 'characters/characters.json')
    cnt = 0
    for pr in cm['presets']:
        for sex, f in pr['files'].items():
            rel = 'characters/' + f
            _write(os.path.join(res, 'frames', 'characters', f'{pr["id"]}_{sex}.tres'), sprite_frames_tres(rel, char_anims(), 32, 32))
            cnt += 1
    n['godot_character_frames'] = cnt
    # 3) monsters
    mm = _j(root, 'monsters/monsters.json')
    for m in mm['monsters']:
        s = m['frame_size'][0]
        anims = char_anims() if m['layout'] == 'character' else creature_anims()
        _write(os.path.join(res, 'frames', 'monsters', f'{m["id"]}.tres'), sprite_frames_tres(m['file'], anims, s, s))
    n['godot_monster_frames'] = len(mm['monsters'])
    # 4) environment animations
    am = _j(root, 'animations/animations.json')
    for a in am['items']:
        w, h = a['frame_size']
        _write(os.path.join(res, 'frames', 'animations', f'{a["id"]}.tres'),
               sprite_frames_tres(a['file'], [('default', 0, a['frames'], a['fps'], a['loop'])], w, h))
    n['godot_animation_frames'] = len(am['items'])
    # 5) tilesets
    em = _j(root, 'environments/environments.json')
    for b in em['biomes']:
        _write(os.path.join(res, 'tilesets', f'{b["id"]}.tres'), tileset_tres(b['file'], b['base_terrain'], b['secondary_terrain']))
    _write(os.path.join(res, 'tilesets', 'interior.tres'), interior_tileset_tres('interiors/tileset/interior_tileset.png'))
    n['godot_tilesets'] = len(em['biomes']) + 1
    # 6) items
    eq = _j(root, 'equipment/equipment.json')
    for i, it in enumerate(eq['items']):
        _write(os.path.join(res, 'items', f'{it["id"]}.tres'), item_tres(it, _stats(it, i)))
    n['godot_items'] = len(eq['items'])
    return n
