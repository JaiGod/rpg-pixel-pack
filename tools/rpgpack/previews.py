"""README screenshots, galleries and animated GIF previews."""
import json
import os
import random

from PIL import Image, ImageDraw, ImageFont

from .core import Canvas, key_map
from . import characters as C
from . import environments as EN

BG = (34, 32, 52, 255)
BG2 = (46, 44, 68, 255)
TXT = (236, 232, 244)
SUB = (160, 156, 184)


def _font(size=10):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _j(root, p):
    with open(os.path.join(root, p)) as f:
        return json.load(f)


def _up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def _frame(sheet, col, row, w=32, h=32):
    return sheet.crop((col * w, row * h, col * w + w, row * h + h))


def _title(draw, text, sub, W, y=14):
    f, fs = _font(26), _font(14)
    tw = draw.textlength(text, font=f)
    draw.text(((W - tw) / 2, y), text, font=f, fill=TXT)
    sw = draw.textlength(sub, font=fs)
    draw.text(((W - sw) / 2, y + 34), sub, font=fs, fill=SUB)


def _grid(cells, cols, cell_w, cell_h, title, sub, label_h=14, scale=1, pad=10):
    rows = (len(cells) + cols - 1) // cols
    W = cols * cell_w + pad * 2
    H = 70 + rows * (cell_h + label_h) + pad
    out = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(out)
    _title(d, title, sub, W)
    f = _font(10)
    for i, (im, label) in enumerate(cells):
        cx, cy = pad + (i % cols) * cell_w, 70 + (i // cols) * (cell_h + label_h)
        d.rectangle([cx + 2, cy + 2, cx + cell_w - 3, cy + cell_h - 3], fill=BG2)
        im = _up(im, scale)
        out.alpha_composite(im, (cx + (cell_w - im.width) // 2, cy + (cell_h - im.height) // 2))
        if label:
            lw = d.textlength(label, font=f)
            if lw > cell_w - 4:
                while lw > cell_w - 8 and len(label) > 3:
                    label = label[:-1]
                    lw = d.textlength(label + '…', font=f)
                label += '…'
            d.text((cx + (cell_w - lw) / 2, cy + cell_h), label, font=f, fill=SUB)
    return out


def _gif(frames, path, duration=120, bg=BG):
    rgb = []
    for fr in frames:
        b = Image.new('RGBA', fr.size, bg)
        b.alpha_composite(fr)
        rgb.append(b.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255))
    rgb[0].save(path, save_all=True, append_images=rgb[1:], duration=duration, loop=0, optimize=False, disposal=2)


# =============================================================================
def characters_gallery(root, out):
    meta = _j(root, 'characters/characters.json')
    cells = []
    for pr in meta['presets']:
        sm = Image.open(os.path.join(root, 'characters', pr['files']['male']))
        sf = Image.open(os.path.join(root, 'characters', pr['files']['female']))
        pair = Image.new('RGBA', (64, 32))
        pair.alpha_composite(_frame(sm, 0, 0), (0, 0)); pair.alpha_composite(_frame(sf, 0, 0), (32, 0))
        cells.append((pair, pr['name']))
    g = _grid(cells, 9, 150, 104, 'Character Gallery', '52 class presets  ·  male + female  ·  6 skin tones  ·  fully layered', scale=2)
    g.save(os.path.join(out, 'characters_gallery.png'))
    # animation GIF: 6 characters doing every animation in the side direction + down walk
    picks = ['knight_paladin', 'mage_wizard', 'ranger_woodland', 'rogue_assassin', 'pirate_captain', 'space_astronaut', 'cyber_netrunner', 'engineer_tinkerer']
    sheets = {}
    for pr in meta['presets']:
        if pr['id'] in picks:
            sheets[pr['id']] = (Image.open(os.path.join(root, 'characters', pr['files']['male'])),
                                Image.open(os.path.join(root, 'characters', pr['files']['female'])))
    seq = []
    for a in meta['animations']:
        if a['name'].endswith('_side') or a['name'] in ('walk_down', 'walk_up'):
            reps = 2 if a['loop'] else 1
            for r in range(reps):
                for fi in range(a['frames']):
                    seq.append((a['row'], fi, a['name']))
            if not a['loop']:
                for _ in range(3):
                    seq.append((a['row'], a['frames'] - 1, a['name']))
    frames = []
    f = _font(12)
    for (row, col, name) in seq:
        im = Image.new('RGBA', (8 * 96 + 16, 140), BG)
        d = ImageDraw.Draw(im)
        for i, pid in enumerate(picks):
            fr = _frame(sheets[pid][i % 2], col, row)
            im.alpha_composite(_up(fr, 3), (8 + i * 96, 18))
        d.text((10, 118), name.replace('_', ' '), font=f, fill=SUB)
        frames.append(im)
    _gif(frames, os.path.join(out, 'character_animations.gif'), 110)


def customization(root, out):
    """Same body, different layers + colors: demonstrates the layer & palette system."""
    lay = os.path.join(root, 'characters', 'layers')
    def L(sex, kind, style, P=None, S=None):
        cv = Canvas.from_pil(Image.open(os.path.join(lay, sex, kind, style + '.png')))
        if P or S:
            cv.recolor(key_map(P, S))
        return cv
    rnd = random.Random(7)
    from .palette import SKINS, HAIR_COLORS
    cols = ['cloth_red', 'cloth_blue', 'cloth_green', 'cloth_purple', 'cloth_teal', 'cloth_orange', 'cloth_black', 'cloth_white', 'cloth_yellow', 'cloth_pink']
    hairs = list(C.HAIR_STYLES)
    torsos = list(C.TORSO_STYLES)
    heads = [None, None] + list(C.HEAD_STYLES)
    cells = []
    for i in range(30):
        sex = 'male' if i % 2 == 0 else 'female'
        skin = SKINS[i % 6]
        hair = hairs[rnd.randrange(len(hairs))]
        t = torsos[rnd.randrange(len(torsos))]
        legs = rnd.choice(list(C.LEG_STYLES))
        head = heads[rnd.randrange(len(heads))]
        hc = rnd.choice(HAIR_COLORS)
        p, s = rnd.choice(cols), rnd.choice(cols)
        sheet = Canvas(192, 576)
        parts = []
        if hair in ('long',):
            parts.append(L(sex, 'hair_back', hair, hc))
        parts += [L(sex, 'body', skin), L(sex, 'legs', legs, rnd.choice(cols), 'leather'), L(sex, 'torso', t, p, s)]
        parts.append(L(sex, 'hair', hair, hc))
        if head:
            parts.append(L(sex, 'head', head, rnd.choice(cols), s))
        for pt in parts:
            sheet.paste(pt)
        im = sheet.to_pil()
        cells.append((_frame(im, 0, 0), None))
    g = _grid(cells, 10, 84, 84, 'Customization System', 'body × skin × hair × hair color × torso × legs × headgear × 2 tint channels — all random combos below', label_h=4, scale=2)
    g.save(os.path.join(out, 'customization.png'))
    # palette swap strip: one layered outfit in 8 colorways
    cells = []
    for i, (p, s) in enumerate([('cloth_red', 'cloth_yellow'), ('cloth_blue', 'cloth_white'), ('cloth_green', 'cloth_brown'), ('cloth_purple', 'cloth_yellow'),
                                ('cloth_black', 'cloth_crimson'), ('cloth_teal', 'cloth_white'), ('cloth_orange', 'cloth_navy'), ('cloth_pink', 'cloth_white')]):
        sheet = Canvas(192, 576)
        for pt in [L('female', 'body', SKINS[i % 6]), L('female', 'legs', 'boots', p, 'leather'), L('female', 'torso', 'robe', p, s),
                   L('female', 'cape', 'cape', s, p), L('female', 'hair', 'ponytail', HAIR_COLORS[i]), L('female', 'head', 'wizard_hat', p, s)]:
            sheet.paste(pt)
        cells.append((_frame(sheet.to_pil(), 0, 0), p.replace('cloth_', '')))
    _grid(cells, 8, 90, 84, 'Palette Swap', 'one set of layer sheets, any color — via palette_swap.gdshader or the Python baker', scale=2).save(os.path.join(out, 'palette_swap.png'))


def monsters_gallery(root, out):
    meta = _j(root, 'monsters/monsters.json')
    cells, big = [], []
    for m in meta['monsters']:
        sh = Image.open(os.path.join(root, m['file']))
        s = m['frame_size'][0]
        if m['layout'] == 'character':
            fr = _frame(sh, 0, 2)  # idle_side
        else:
            fr = _frame(sh, 0, 0, s, s)
        if s == 64:
            big.append((fr, m['name']))
        else:
            cells.append((fr, m['name']))
    g = _grid(cells, 12, 96, 76, 'Monster Gallery', f"{len(meta['monsters'])} monsters · slimes · skeletons · goblins · orcs · dragons · robots · aliens · shadow creatures", scale=2)
    b = _grid(big, 8, 150, 148, 'Bosses', '64×64 boss monsters with full animation sets', scale=2)
    W = max(g.width, b.width)
    out_im = Image.new('RGBA', (W, g.height + b.height), BG)
    out_im.alpha_composite(g, ((W - g.width) // 2, 0)); out_im.alpha_composite(b, ((W - b.width) // 2, g.height))
    out_im.save(os.path.join(out, 'monsters_gallery.png'))
    # GIF of monsters attacking
    picks = [m for m in meta['monsters'] if m['id'] in ('slime_green', 'slime_fire', 'skeleton_warrior', 'goblin_shaman', 'orc_warlord', 'dragon_red',
                                                          'robot_drone', 'alien_jelly', 'shadow_reaper', 'shadow_eye')]
    bosses = [m for m in meta['monsters'] if m['id'] in ('boss_elder_dragon', 'boss_lich_king', 'boss_overmind', 'boss_mech_titan')]
    frames = []
    seq = [('idle', 4, 2), ('move', 4, 2), ('attack', 4, 2), ('hurt', 2, 1), ('death', 5, 1)]
    char_rows = {'idle': (0, 4), 'move': (5, 6), 'attack': (11, 4), 'hurt': (14, 2), 'death': (17, 5)}
    cre_rows = {'idle': 0, 'move': 1, 'attack': 2, 'hurt': 3, 'death': 4}
    f = _font(12)
    for (anim, n, reps) in seq:
        for r in range(reps):
            for fi in range(n):
                im = Image.new('RGBA', (10 * 72 + 16, 232), BG)
                d = ImageDraw.Draw(im)
                for i, m in enumerate(picks):
                    sh = Image.open(os.path.join(root, m['file']))
                    if m['layout'] == 'character':
                        row, cnt = char_rows[anim]
                        fr = _frame(sh, min(fi, cnt - 1), row)
                    else:
                        fr = _frame(sh, fi, cre_rows[anim])
                    im.alpha_composite(_up(fr, 2), (8 + i * 72, 8))
                for i, m in enumerate(bosses):
                    sh = Image.open(os.path.join(root, m['file']))
                    im.alpha_composite(_up(_frame(sh, fi, cre_rows[anim], 64, 64), 2), (8 + i * 184, 80 - 8 + 4))
                d.text((10, 212), anim, font=f, fill=SUB)
                frames.append(im)
        if anim in ('death', 'hurt'):
            frames += [frames[-1]] * 3
    _gif(frames, os.path.join(out, 'monster_animations.gif'), 130)


def simple_gallery(root, out, meta_path, key, title, sub, cols, cw, ch, scale, fname, size_key=None, max_w=None):
    meta = _j(root, meta_path)
    items = meta[key]
    cells = []
    for it in items:
        im = Image.open(os.path.join(root, it['file']))
        if max_w and im.width * scale > max_w:
            pass
        cells.append((im, it['name']))
    _grid(cells, cols, cw, ch, title, sub, scale=scale).save(os.path.join(out, fname))


def buildings_gallery(root, out):
    meta = _j(root, 'buildings/buildings.json')
    ims = [(Image.open(os.path.join(root, b['file'])), b['name']) for b in meta['items']]
    W = 1400
    pad, x, y, rowh = 14, 14, 74, 0
    placements = []
    for im, n in ims:
        if x + im.width + pad > W:
            x, y = 14, y + rowh + 22
            rowh = 0
        placements.append((im, n, x, y))
        x += im.width + pad
        rowh = max(rowh, im.height)
    H = y + rowh + 30
    out_im = Image.new('RGBA', (W, H), (74, 112, 66, 255))
    d = ImageDraw.Draw(out_im)
    d.rectangle([0, 0, W, 66], fill=BG)
    _title(d, 'Buildings', '40 buildings · 10 types × 4 variants · houses · inns · shops · farms · smithies · towers · castles · habitats · arcologies', W)
    f = _font(10)
    for im, n, x, y in placements:
        out_im.alpha_composite(im, (x, y))
        d.text((x, y + im.height + 3), n, font=f, fill=(230, 240, 220))
    out_im.save(os.path.join(out, 'buildings_gallery.png'))


def environments_gallery(root, out):
    meta = _j(root, 'environments/environments.json')
    tiles = []
    for b in meta['biomes']:
        at = Image.open(os.path.join(root, b['file']))
        tiles.append((sample_map(at, 12, 7, seed=len(tiles)), b['name']))
    _grid(tiles, 4, 400, 238, 'Environments', '11 biome tilesets with Godot terrain auto-tiling (match corners) + 20 biome props', scale=1).save(os.path.join(out, 'environments_gallery.png'))
    props = [(Image.open(os.path.join(root, p['file'])), p['name']) for p in meta['props']]
    _grid(props, 10, 140, 140, 'Biome Props', 'trees · crystals · statues · antennas · holo trees', scale=2).save(os.path.join(out, 'props_gallery.png'))


def sample_map(atlas, W, H, seed=0):
    rnd = random.Random(seed)
    V = [[0] * (W + 1) for _ in range(H + 1)]
    cx, cy = rnd.uniform(3, W - 3), rnd.uniform(2.5, H - 2.5)
    for y in range(H + 1):
        for x in range(W + 1):
            V[y][x] = 1 if ((x - cx) ** 2 / 7 + (y - cy) ** 2 / 3.5) < 1 or (y in (int(cy), int(cy) + 1) and x > cx) else 0
    out = Image.new('RGBA', (W * 32, H * 32))
    for y in range(H):
        for x in range(W):
            c = (V[y][x], V[y][x + 1], V[y + 1][x], V[y + 1][x + 1])
            idx = c[0] * 8 + c[1] * 4 + c[2] * 2 + c[3]
            if idx == 0:
                col, row = rnd.choice([0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7]), 0
                if rnd.random() < 0.06 and 0 < x < W - 1:
                    col, row = rnd.choice([4, 5, 6, 7]), 3
            elif idx == 15:
                col, row = rnd.choice([0, 1, 2, 3]), 3
            else:
                col, row = idx % 8, 1 + idx // 8
            out.alpha_composite(atlas.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)), (x * 32, y * 32))
    return out


def interiors_gallery(root, out):
    meta = _j(root, 'interiors/interiors.json')
    cells = [(Image.open(os.path.join(root, r['file'])), r['name']) for r in meta['rooms']]
    _grid(cells, 5, 372, 300, 'Interiors', '35 furnished rooms · bedrooms · kitchens · taverns · workshops · libraries · labs · command centers', scale=1).save(os.path.join(out, 'interiors_gallery.png'))


def animations_gif(root, out):
    meta = _j(root, 'animations/animations.json')
    strips = [(Image.open(os.path.join(root, a['file'])), a) for a in meta['items']]
    W = 980
    pos, x, y, rowh = [], 10, 60, 0
    for im, a in strips:
        w, h = a['frame_size'][0] * 2, a['frame_size'][1] * 2
        if x + w > W - 10:
            x, y, rowh = 10, y + rowh + 22, 0
        pos.append((x, y))
        x += w + 18
        rowh = max(rowh, h)
    H = y + rowh + 28
    frames = []
    f = _font(10)
    for t in range(24):
        im = Image.new('RGBA', (W, H), BG)
        d = ImageDraw.Draw(im)
        _title(d, 'Environmental Animations', 'water · lava · fire · torches · doors · portals · props', W, 6)
        for (strip, a), (px, py) in zip(strips, pos):
            n = a['frames']
            fi = t % n if a['loop'] else min(t % (n + 4), n - 1)
            fw, fh = a['frame_size']
            im.alpha_composite(_up(strip.crop((fi * fw, 0, fi * fw + fw, fh)), 2), (px, py))
            d.text((px, py + fh * 2 + 3), a['name'], font=f, fill=SUB)
        frames.append(im)
    _gif(frames, os.path.join(out, 'environment_animations.gif'), 125)


def banner(root, out):
    """Hero scene composited from pack assets."""
    W, H = 22, 12
    vil = Image.open(os.path.join(root, 'environments/tilesets/village.png'))
    rnd = random.Random(3)
    V = [[0] * (W + 1) for _ in range(H + 1)]
    for y in range(H + 1):
        for x in range(W + 1):
            V[y][x] = 1 if (y in (7, 8) and 0 <= x <= W) or (x in (10, 11) and y >= 7) or ((x - 15) ** 2 / 6 + (y - 7.5) ** 2 / 3 < 1) else 0
    scene = Image.new('RGBA', (W * 32, H * 32))
    for y in range(H):
        for x in range(W):
            c = (V[y][x], V[y][x + 1], V[y + 1][x], V[y + 1][x + 1])
            idx = c[0] * 8 + c[1] * 4 + c[2] * 2 + c[3]
            if idx == 0:
                col, row = rnd.choice([0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6]), 0
            elif idx == 15:
                col, row = rnd.choice([0, 1, 2, 3]), 3
            else:
                col, row = idx % 8, 1 + idx // 8
            scene.alpha_composite(vil.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)), (x * 32, y * 32))
    def put(path, x, y):
        im = Image.open(os.path.join(root, path))
        scene.alpha_composite(im, (int(x), int(y - im.height)))
    def frame(path, col, row, x, y, s=32):
        im = Image.open(os.path.join(root, path))
        scene.alpha_composite(im.crop((col * s, row * s, col * s + s, row * s + s)), (int(x), int(y - s)))
    put('environments/props/tree_oak.png', -18, 120)
    put('environments/props/tree_cherry.png', 150, 96)
    put('buildings/small_houses/house_small_cottage.png', 30, 228)
    put('buildings/inns/inn_tavern.png', 400, 228)
    put('buildings/shops/shop_potion.png', 224, 228)
    put('buildings/wizard_towers/tower_arcane.png', 620, 228)
    put('environments/props/tree_oak.png', 560, 380)
    put('environments/props/tree_autumn.png', 20, 395)
    put('environments/props/well.png', 330, 330)
    put('environments/props/lamp_post.png', 300, 250)
    put('animations/fire/campfire.png', 0, 0) if False else None
    frame('animations/fire/campfire.png', 1, 0, 520, 330)
    frame('animations/props/flag_red.png', 0, 0, 380, 250, 32) if False else None
    for (pid, sex, x, y, row, col) in [('knight_paladin', 'male', 330, 268, 2, 0), ('mage_wizard', 'female', 370, 268, 2, 1),
                                       ('ranger_woodland', 'female', 290, 300, 5, 2), ('merchant_trader', 'male', 250, 266, 0, 0),
                                       ('farmer_homesteader', 'female', 120, 300, 3, 3), ('pirate_captain', 'male', 460, 290, 0, 1),
                                       ('space_astronaut', 'female', 600, 300, 2, 0), ('cyber_netrunner', 'male', 640, 302, 2, 2)]:
        meta = _j(root, 'characters/characters.json')
        pr = next(p for p in meta['presets'] if p['id'] == pid)
        frame('characters/' + pr['files'][sex], col, row, x, y)
    frame('monsters/slimes/slime_green.png', 0, 0, 470, 350)
    frame('monsters/slimes/slime_blue.png', 1, 0, 500, 370)
    frame('monsters/dragons/dragon_red.png', 1, 0, 660, 360)
    banner = _up(scene, 2)
    d = ImageDraw.Draw(banner)
    d.rectangle([0, 0, banner.width, 70], fill=(20, 18, 32, 215))
    f, fs = _font(34), _font(16)
    d.text((24, 12), 'RPG PIXEL PACK', font=f, fill=TXT)
    d.text((340, 26), '32×32 open-source RPG assets for Godot 4  ·  v1.0', font=fs, fill=(250, 220, 120))
    banner.save(os.path.join(out, 'banner.png'))


def build(root):
    out = os.path.join(root, 'previews')
    os.makedirs(out, exist_ok=True)
    banner(root, out)
    characters_gallery(root, out)
    customization(root, out)
    monsters_gallery(root, out)
    simple_gallery(root, out, 'equipment/equipment.json', 'items', 'Equipment', '62 icons · swords · axes · spears · bows · crossbows · staves · wands · shields · helmets · capes · armor', 12, 96, 76, 2, 'equipment_gallery.png')
    simple_gallery(root, out, 'furniture/furniture.json', 'items', 'Furniture', '120 pieces · tables · beds · chairs · shelves · crates · barrels · computers · consoles · decorations', 12, 112, 112, 1, 'furniture_gallery.png')
    buildings_gallery(root, out)
    environments_gallery(root, out)
    interiors_gallery(root, out)
    animations_gif(root, out)
