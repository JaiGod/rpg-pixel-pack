"""Interior tileset + 35 furnished room layouts.

Interior tileset atlas (8 x 4 tiles):
  row 0: 8 floor types
  row 1: 8 wall types, upper half (with crown moulding)
  row 2: 8 wall types, lower half (with baseboard)
  row 3: col 0 wall-cap (top-down dark edge), col 1 doorway floor mat, col 2 shadowed floor
Rooms are data: a JSON layout of tiles + furniture placements, also rendered to PNG.
"""
import random
import numpy as np

from .core import Canvas, R, rgba
from .palette import OUTLINE, INK
from .environments import surface
from . import furniture as F

T = 32
FLOORS = ['planks', 'planks_dark', 'stone', 'carpet', 'checker', 'metal', 'lab', 'cobble']
WALLS = ['wallpaper', 'wood_panel', 'stone', 'brick', 'plaster', 'tech', 'lab', 'dungeon']
FLOOR_SPEC = {'planks': ('planks', 'wood_light'), 'planks_dark': ('planks', 'wood'), 'stone': ('flagstone', 'stone'),
              'carpet': ('carpet', 'cloth_crimson'), 'checker': ('checker', 'cloth_white'), 'metal': ('metal', 'tech'),
              'lab': ('lab', 'tech_light'), 'cobble': ('cobble', 'cobble')}


def floor_tile(name, seed=0):
    kind, ramp = FLOOR_SPEC[name]
    if kind == 'checker':
        cv = Canvas(T)
        yy, xx = np.mgrid[0:T, 0:T]
        cv.img[:] = rgba(R('cloth_white')[2])
        cv.img[((xx // 16) + (yy // 16)) % 2 == 1] = rgba(R('cloth_navy')[2])
        cv.img[(xx % 16 == 0) | (yy % 16 == 0)] = rgba(R('cloth_gray')[2])
        return cv
    return surface(kind, ramp, seed)


def wall_tile(name, half):
    cv = Canvas(T)
    yy, xx = np.mgrid[0:T, 0:T]
    spec = {'wallpaper': 'cloth_tan', 'wood_panel': 'wood', 'stone': 'stone', 'brick': 'brick', 'plaster': 'plaster',
            'tech': 'tech', 'lab': 'tech_light', 'dungeon': 'stone_dark'}[name]
    rr = R(spec)
    cv.img[:] = rgba(rr[1])
    if name == 'wallpaper':
        cv.img[:] = rgba(rr[2])
        cv.img[(xx % 8 == 0)] = rgba(rr[1])
        cv.img[(xx % 8 == 4) & (yy % 6 == 3)] = rgba(R('cloth_red')[1])
    elif name == 'wood_panel':
        cv.img[(xx % 8 == 0)] = rgba(rr[0]); cv.img[(xx % 8 == 1)] = rgba(rr[2])
    elif name in ('stone', 'brick', 'dungeon'):
        bh, bw = (8, 16) if name != 'brick' else (6, 12)
        cv.img[:] = rgba(rr[0])
        for ri, y in enumerate(range(0, T, bh)):
            off = (bw // 2) * (ri % 2)
            for x in range(-off, T, bw):
                m = cv.mask_rect(x + 1, y + 1, x + bw - 1, y + bh - 1)
                cv.img[m] = rgba(rr[1]); cv.img[m & (yy == y + 1)] = rgba(rr[2])
    elif name == 'plaster':
        cv.img[:] = rgba(rr[2])
        rnd = random.Random(4)
        for i in range(20):
            cv.px(rnd.randrange(T), rnd.randrange(T), rr[1])
    elif name in ('tech', 'lab'):
        cv.img[(xx % 16 == 0)] = rgba(rr[0]); cv.img[(xx % 16 == 1)] = rgba(rr[2])
        if name == 'tech':
            cv.img[(yy == 20) & (xx % 16 > 3) & (xx % 16 < 12)] = rgba(R('neon_cyan')[2])
    if half == 'upper':
        cv.hline(0, T - 1, 0, R('wood_dark' if name not in ('tech', 'lab') else 'tech_dark')[1])
        cv.hline(0, T - 1, 1, R('wood_dark' if name not in ('tech', 'lab') else 'tech_dark')[2])
        cv.hline(0, T - 1, 2, rr[0])
    else:
        bb = 'wood_dark' if name not in ('tech', 'lab', 'dungeon', 'stone') else ('tech_dark' if name in ('tech', 'lab') else 'stone_dark')
        cv.rect(0, 25, T - 1, 31, R(bb)[1]); cv.hline(0, T - 1, 25, R(bb)[3]); cv.hline(0, T - 1, 31, R(bb)[0])
    return cv


def build_tileset():
    at = Canvas(8 * T, 4 * T)
    for i, f in enumerate(FLOORS):
        at.paste(floor_tile(f, i), i * T, 0)
    for i, w in enumerate(WALLS):
        at.paste(wall_tile(w, 'upper'), i * T, T)
        at.paste(wall_tile(w, 'lower'), i * T, 2 * T)
    cap = Canvas(T); cap.img[:] = rgba((24, 20, 34)); cap.hline(0, T - 1, T - 1, R('stone_dark')[2])
    at.paste(cap, 0, 3 * T)
    mat = floor_tile('planks', 1); mat.rect(4, 8, 27, 23, R('cloth_red')[1]); mat.rect(6, 10, 25, 21, R('cloth_red')[2])
    at.paste(mat, T, 3 * T)
    sh = floor_tile('planks', 2); sh.img[:, :, :3] = (sh.img[:, :, :3] * 0.7).astype(np.uint8)
    at.paste(sh, 2 * T, 3 * T)
    return at


FURN = {f[0]: f for f in F.FURNITURE}


def R_(id, x, y):
    return (id, x, y)


ROOMS = []


def room(id, cat, name, floor, wall, items, w=10, h=8):
    ROOMS.append(dict(id=id, category=cat, name=name, floor=floor, wall=wall, w=w, h=h, items=items))


# --- bedrooms
room('bedroom_cottage', 'bedrooms', 'Cottage Bedroom', 'planks', 'wallpaper',
     [R_('wall_window', 3, 1), R_('painting_landscape', 6, 1), R_('bed_single_red', 1, 4), R_('dresser_wood', 3, 2), R_('rug_round', 4, 5),
      R_('wardrobe_wood', 8, 3), R_('plant_flowers', 7, 2), R_('chest_wood', 1, 6), R_('floor_lamp', 8, 6), R_('chair_wood', 6, 4)])
room('bedroom_royal', 'bedrooms', 'Royal Bedchamber', 'carpet', 'stone',
     [R_('banner_red', 2, 1), R_('banner_red', 7, 1), R_('wall_mirror', 5, 1), R_('bed_royal', 4, 4), R_('chest_gold', 1, 3), R_('candelabra', 2, 2),
      R_('candelabra', 7, 2), R_('wardrobe_wood', 8, 4), R_('rug_royal', 4, 6), R_('chair_armchair', 1, 6), R_('vase_blue', 8, 6)])
room('bedroom_inn', 'bedrooms', 'Inn Room', 'planks_dark', 'wood_panel',
     [R_('wall_window', 4, 1), R_('bed_single_blue', 1, 4), R_('bed_single_green', 7, 4), R_('table_wood', 4, 3), R_('chair_wood', 3, 3),
      R_('rug_fur', 4, 6), R_('barrel_wood', 8, 6), R_('candles', 5, 2)])
room('bedroom_scifi', 'bedrooms', 'Crew Quarters', 'metal', 'tech',
     [R_('console_wall_panel', 4, 1), R_('wall_neon_sign', 7, 1), R_('bed_cryopod', 1, 4), R_('bed_cryopod', 3, 4), R_('chest_locker', 7, 3),
      R_('fridge_scifi', 8, 4), R_('chair_scifi', 6, 5), R_('plant_alien', 1, 6), R_('trash_bin', 8, 6)])
room('bedroom_hut', 'bedrooms', 'Peasant Hut', 'cobble', 'plaster',
     [R_('bed_straw', 1, 4), R_('firewood', 7, 2), R_('stove_iron', 8, 2), R_('sack', 6, 2), R_('table_round', 4, 4), R_('chair_stool', 3, 4),
      R_('chair_stool', 5, 5), R_('barrel_water', 8, 6), R_('rug_fur', 3, 6)])
# --- kitchens
room('kitchen_farmhouse', 'kitchens', 'Farmhouse Kitchen', 'checker', 'wallpaper',
     [R_('wall_window', 4, 1), R_('wall_clock', 7, 1), R_('stove_iron', 1, 2), R_('shelf_low_books', 2, 2), R_('shelf_pantry', 8, 3),
      R_('table_long', 3, 4), R_('chair_wood', 2, 4), R_('chair_wood', 6, 4), R_('barrel_open', 1, 6), R_('crate_apples', 8, 6), R_('grain_sacks', 7, 6)])
room('kitchen_castle', 'kitchens', 'Castle Kitchen', 'stone', 'stone',
     [R_('fireplace', 1, 3), R_('cauldron', 4, 3), R_('table_long', 6, 3), R_('shelf_pantry', 8, 5), R_('barrel_keg', 1, 6), R_('barrel_wood', 2, 6),
      R_('crate_fish', 4, 6), R_('sack', 6, 6), R_('table_stone', 5, 5)])
room('kitchen_tavern', 'kitchens', 'Tavern Kitchen', 'planks_dark', 'brick',
     [R_('stove_iron', 1, 2), R_('stove_iron', 2, 2), R_('shelf_pantry', 4, 3), R_('table_wood', 6, 3), R_('crate_apples', 8, 2), R_('barrel_water', 1, 5),
      R_('crate_stack', 8, 5), R_('grain_sacks', 4, 6), R_('firewood', 7, 6)])
room('kitchen_galley', 'kitchens', 'Starship Galley', 'metal', 'tech',
     [R_('fridge_scifi', 1, 3), R_('fridge_scifi', 2, 3), R_('vending_machine', 8, 3), R_('table_lab', 4, 4), R_('chair_scifi', 4, 5), R_('chair_scifi', 6, 5),
      R_('crate_tech', 1, 6), R_('trash_bin', 8, 6), R_('console_wall_panel', 5, 1)])
room('kitchen_witch', 'kitchens', 'Witch\'s Kitchen', 'cobble', 'dungeon',
     [R_('cauldron', 4, 3), R_('shelf_potions', 1, 3), R_('shelf_potions', 8, 3), R_('table_alchemy', 6, 4), R_('candles', 3, 4), R_('barrel_toxic', 1, 6),
      R_('plant_fern', 8, 6), R_('book_stack', 6, 6), R_('rug_fur', 3, 6)])
# --- taverns
room('tavern_common', 'taverns', 'Common Room', 'planks', 'wood_panel',
     [R_('wall_trophy', 2, 1), R_('banner_green', 7, 1), R_('barrel_keg', 1, 2), R_('barrel_keg', 2, 2), R_('table_tavern', 4, 3), R_('table_tavern', 4, 6),
      R_('chair_stool', 3, 3), R_('chair_stool', 6, 3), R_('chair_stool', 3, 6), R_('chair_stool', 6, 6), R_('fireplace', 8, 3), R_('table_round', 8, 6)], w=11)
room('tavern_harbor', 'taverns', 'Harbor Tavern', 'planks_dark', 'wood_panel',
     [R_('wall_window', 3, 1), R_('wall_window', 7, 1), R_('barrel_wood', 1, 2), R_('crate_fish', 9, 2), R_('table_tavern', 2, 4), R_('table_round', 7, 4),
      R_('chair_bench', 2, 5), R_('chair_wood', 6, 4), R_('chair_wood', 8, 4), R_('rug_blue', 5, 6), R_('barrel_open', 9, 6)], w=11)
room('tavern_noble', 'taverns', 'Noble Lounge', 'carpet', 'wallpaper',
     [R_('painting_portrait', 3, 1), R_('painting_landscape', 7, 1), R_('piano', 1, 3), R_('couch_red', 5, 3), R_('table_round', 5, 5), R_('chair_armchair', 4, 5),
      R_('chair_armchair', 7, 5), R_('candelabra', 9, 3), R_('plant_bush', 1, 6), R_('vase_amphora', 9, 6)], w=11)
room('tavern_dive', 'taverns', 'Cyber Dive Bar', 'metal', 'brick',
     [R_('wall_neon_sign', 3, 1), R_('wall_neon_sign', 7, 1), R_('arcade_cabinet', 1, 3), R_('arcade_cabinet', 2, 3), R_('vending_machine', 9, 3),
      R_('table_round', 5, 4), R_('chair_stool', 4, 4), R_('chair_stool', 7, 4), R_('neon_lamp', 9, 6), R_('couch_blue', 2, 6), R_('trash_bin', 6, 6)], w=11)
room('tavern_dwarf', 'taverns', 'Dwarven Mead Hall', 'stone', 'stone',
     [R_('banner_red', 2, 1), R_('banner_red', 8, 1), R_('barrel_keg', 1, 2), R_('barrel_keg', 9, 2), R_('table_banquet', 4, 4), R_('chair_bench', 4, 5),
      R_('chair_throne', 5, 2), R_('fireplace', 8, 6), R_('barrel_wood', 1, 6), R_('rack_weapons', 3, 6)], w=11)
# --- workshops
room('workshop_blacksmith', 'workshops', 'Blacksmith Workshop', 'cobble', 'brick',
     [R_('fireplace', 1, 3), R_('anvil', 4, 3), R_('rack_weapons', 6, 2), R_('rack_armor', 8, 2), R_('barrel_water', 4, 5), R_('crate_reinforced', 8, 5),
      R_('firewood', 1, 6), R_('table_wood', 6, 5)])
room('workshop_carpenter', 'workshops', 'Carpenter Shop', 'planks', 'wood_panel',
     [R_('wall_window', 4, 1), R_('table_long', 2, 3), R_('firewood', 6, 2), R_('crate_stack', 8, 3), R_('crate_wood', 1, 6), R_('chair_stool', 4, 4),
      R_('barrel_wood', 8, 6), R_('rug_fur', 4, 6)])
room('workshop_garage', 'workshops', 'Engineer Garage', 'metal', 'tech',
     [R_('console_wall_panel', 2, 1), R_('computer_workstation', 4, 2), R_('crate_tech', 1, 4), R_('barrel_oil', 1, 6), R_('crate_cargo', 8, 3),
      R_('table_lab', 4, 5), R_('chair_office', 3, 5), R_('barrel_toxic', 8, 6)])
room('workshop_alchemy', 'workshops', 'Alchemy Lab', 'stone', 'dungeon',
     [R_('shelf_potions', 1, 3), R_('shelf_books_dark', 2, 3), R_('cauldron', 5, 3), R_('table_alchemy', 7, 3), R_('candelabra', 8, 2), R_('scroll_table', 3, 5),
      R_('book_stack', 7, 5), R_('barrel_toxic', 8, 6), R_('rug_round', 4, 6)])
room('workshop_tinker', 'workshops', 'Tinker\'s Bench', 'planks_dark', 'brick',
     [R_('wall_clock', 3, 1), R_('grandfather_clock', 1, 3), R_('table_desk', 3, 3), R_('chair_office', 4, 4), R_('computer_retro', 7, 2), R_('crate_tech', 8, 2),
      R_('globe', 8, 5), R_('telescope', 1, 6), R_('crate_wood', 6, 6)])
# --- libraries
room('library_grand', 'libraries', 'Grand Library', 'carpet', 'wood_panel',
     [R_('shelf_books', 1, 3), R_('shelf_books', 2, 3), R_('shelf_books_dark', 3, 3), R_('shelf_books', 7, 3), R_('shelf_books_dark', 8, 3),
      R_('table_desk', 4, 5), R_('chair_cushion', 5, 4), R_('globe', 1, 6), R_('floor_lamp', 8, 6), R_('rug_royal', 4, 6)])
room('library_study', 'libraries', 'Scholar\'s Study', 'planks', 'wallpaper',
     [R_('wall_window', 5, 1), R_('shelf_books', 1, 3), R_('shelf_low_books', 2, 2), R_('table_desk', 4, 3), R_('chair_cushion', 5, 4), R_('chair_armchair', 8, 4),
      R_('book_stack', 1, 6), R_('globe', 8, 6), R_('rug_round', 4, 6)])
room('library_arcane', 'libraries', 'Arcane Archive', 'stone', 'dungeon',
     [R_('shelf_books_dark', 1, 3), R_('shelf_potions', 2, 3), R_('shelf_books_dark', 7, 3), R_('shelf_books_dark', 8, 3), R_('scroll_table', 4, 3),
      R_('candelabra', 5, 2), R_('book_stack', 4, 5), R_('crystal_cluster' if False else 'specimen_tank', 1, 6), R_('rug_fur', 5, 6)])
room('library_monastery', 'libraries', 'Monastery Scriptorium', 'cobble', 'plaster',
     [R_('banner_blue', 5, 1), R_('shelf_books', 1, 3), R_('shelf_books', 8, 3), R_('scroll_table', 3, 3), R_('scroll_table', 6, 3), R_('chair_stool', 3, 4),
      R_('chair_stool', 6, 4), R_('candles', 4, 6), R_('book_stack', 1, 6)])
room('library_datavault', 'libraries', 'Data Vault', 'metal', 'tech',
     [R_('shelf_server', 1, 3), R_('shelf_server', 2, 3), R_('shelf_server', 7, 3), R_('shelf_server', 8, 3), R_('computer_terminal', 4, 2),
      R_('computer_terminal', 5, 2), R_('console_hologram', 4, 5), R_('chair_office', 6, 5), R_('crate_tech', 8, 6)])
# --- laboratories
room('lab_bio', 'laboratories', 'Bio Lab', 'lab', 'lab',
     [R_('specimen_tank', 1, 3), R_('specimen_tank', 2, 3), R_('table_lab', 4, 3), R_('computer_terminal', 8, 2), R_('bed_medical', 8, 5),
      R_('chair_office', 5, 4), R_('plant_alien', 1, 6), R_('barrel_toxic', 4, 6), R_('trash_bin', 6, 6)])
room('lab_chem', 'laboratories', 'Chemistry Lab', 'checker', 'lab',
     [R_('shelf_potions', 1, 3), R_('table_lab', 3, 3), R_('table_lab', 3, 6), R_('computer_crt', 7, 2), R_('chair_office', 8, 4), R_('shelf_display', 8, 6),
      R_('barrel_toxic', 1, 6)])
room('lab_robotics', 'laboratories', 'Robotics Lab', 'metal', 'tech',
     [R_('computer_workstation', 1, 2), R_('console_reactor', 8, 2), R_('table_lab', 4, 4), R_('crate_tech', 1, 5), R_('crate_cargo', 8, 5),
      R_('chair_office', 4, 5), R_('barrel_oil', 1, 6), R_('rack_armor', 8, 6)])
room('lab_physics', 'laboratories', 'Physics Lab', 'lab', 'lab',
     [R_('console_reactor', 4, 3), R_('console_reactor', 5, 3), R_('computer_terminal', 1, 2), R_('computer_terminal', 8, 2), R_('console_hologram', 1, 6),
      R_('table_lab', 6, 6), R_('chair_office', 4, 5), R_('telescope', 8, 6)])
room('lab_xeno', 'laboratories', 'Xeno Containment', 'metal', 'lab',
     [R_('specimen_tank', 2, 3), R_('specimen_tank', 4, 3), R_('specimen_tank', 6, 3), R_('specimen_tank', 8, 3), R_('console_control', 3, 5),
      R_('chair_scifi', 4, 6), R_('barrel_toxic', 1, 6), R_('plant_alien', 8, 6)])
# --- command centers
room('command_bridge', 'command_centers', 'Starship Bridge', 'metal', 'tech',
     [R_('console_wall_panel', 2, 1), R_('console_wall_panel', 7, 1), R_('console_nav', 4, 2), R_('console_control', 1, 3), R_('console_control', 7, 3),
      R_('chair_scifi', 5, 4), R_('console_hologram', 4, 6), R_('chair_scifi', 2, 5), R_('chair_scifi', 8, 5)], w=10)
room('command_war_room', 'command_centers', 'War Room', 'stone', 'stone',
     [R_('banner_red', 2, 1), R_('banner_blue', 7, 1), R_('table_banquet', 4, 4), R_('chair_cushion', 3, 4), R_('chair_cushion', 6, 4), R_('chair_throne', 5, 2),
      R_('rack_weapons', 1, 3), R_('rack_armor', 8, 3), R_('globe', 1, 6), R_('candelabra', 8, 6)])
room('command_ops', 'command_centers', 'Ops Center', 'lab', 'tech',
     [R_('computer_workstation', 1, 2), R_('computer_workstation', 6, 2), R_('computer_holo_desk', 3, 5), R_('chair_office', 2, 3), R_('chair_office', 7, 3),
      R_('shelf_server', 8, 6), R_('console_comms', 1, 6), R_('trash_bin', 6, 6)])
room('command_colony', 'command_centers', 'Colony Control', 'metal', 'lab',
     [R_('console_nav', 1, 2), R_('console_comms', 7, 2), R_('console_reactor', 8, 2), R_('computer_holo_desk', 4, 4), R_('chair_scifi', 4, 5),
      R_('chair_scifi', 6, 5), R_('crate_tech', 1, 6), R_('plant_alien', 8, 6)])
room('command_throne', 'command_centers', 'Throne Room', 'carpet', 'stone',
     [R_('banner_red', 2, 1), R_('banner_red', 4, 1), R_('banner_red', 6, 1), R_('banner_red', 8, 1), R_('chair_throne', 5, 2), R_('pillar_stone', 1, 4),
      R_('pillar_stone', 9, 4), R_('rug_royal', 4, 5), R_('candelabra', 3, 3), R_('candelabra', 7, 3), R_('statue_hero', 1, 7), R_('statue_hero', 9, 7)], w=11, h=9)


def render_room(rm):
    W, H = rm['w'], rm['h']
    cv = Canvas(W * T, H * T)
    fi, wi = FLOORS.index(rm['floor']), WALLS.index(rm['wall'])
    tiles = []
    for y in range(H):
        row = []
        for x in range(W):
            if x == 0 or x == W - 1 or y == H - 1:
                t = ('cap', 0, 3)
            elif y == 0:
                t = ('wall_upper', wi, 1)
            elif y == 1:
                t = ('wall_lower', wi, 2)
            elif y == H - 2 and x == W // 2:
                t = ('mat', 1, 3)
            else:
                t = ('floor', fi, 0)
            row.append([t[1], t[2]])
            if t[0] == 'floor':
                tile = floor_tile(rm['floor'], x * 7 + y)
            elif t[0] == 'cap':
                tile = Canvas(T); tile.img[:] = rgba((24, 20, 34))
            elif t[0] == 'mat':
                tile = floor_tile(rm['floor'], 3); tile.rect(4, 8, 27, 23, R('cloth_red')[1]); tile.rect(6, 10, 25, 21, R('cloth_red')[2])
            else:
                tile = wall_tile(rm['wall'], 'upper' if y == 0 else 'lower')
            cv.paste(tile, x * T, y * T)
        tiles.append(row)
    # floor contact shadow under the wall
    sh = cv.mask_rect(T, 2 * T, (W - 1) * T - 1, 2 * T + 3)
    cv.img[sh, :3] = (cv.img[sh, :3] * 0.72).astype(np.uint8)
    placed = []
    for (fid, tx, ty) in sorted(rm['items'], key=lambda it: (it[2], it[1])):
        _, cat, name, (fw, fh), fn = FURN[fid]
        px, py = tx * T, (ty + 1) * T - fh
        cv.paste(fn(), px, py)
        placed.append(dict(furniture=fid, tile=[tx, ty], pixel=[px, py], size=[fw, fh]))
    return cv, dict(id=rm['id'], category=rm['category'], name=rm['name'], size_tiles=[W, H], floor=rm['floor'], wall=rm['wall'],
                    tiles=tiles, furniture=placed, door_tile=[W // 2, H - 2])
