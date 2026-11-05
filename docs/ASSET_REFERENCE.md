# Asset reference

All sizes are in pixels. Every folder has a JSON catalog with ids, names, files and metadata.

## Characters: `characters/`
* **Sheet:** 192 × 576 = 6 columns × 18 rows of 32 × 32 frames.
* **Rows:** for each animation, for each direction (`down`, `up`, `side`):

| Rows | Animation | Frames | FPS | Loop |
|---|---|---|---|---|
| 0-2 | idle | 4 | 6 | ✓ |
| 3-5 | walk | 6 | 10 | ✓ |
| 6-8 | run | 6 | 14 | ✓ |
| 9-11 | attack | 4 | 12 | – |
| 12-14 | hurt | 2 | 8 | – |
| 15-17 | death | 5 | 8 | – |

* `side` faces right. Feet at y ≈ 30 in each frame.
* `characters.json`: `animations`, `layer_order`, `palette_swap`, `layers` (styles per layer), `presets` (52, with `layer_recipe`).

### Presets (13 classes × 4)
| Class | Presets |
|---|---|
| Warrior | Mercenary, Berserker, Gladiator, Ronin |
| Knight | Paladin, Royal Guard, Black Knight, Squire |
| Ranger | Woodland Ranger, Hunter, Elf Scout, Beastmaster |
| Rogue | Thief, Assassin, Bandit, Shadowblade |
| Mage | Wizard, Pyromancer, Frost Mage, Apprentice |
| Necromancer | Lich Acolyte, Bone Caller, Grave Warden, Blood Witch |
| Engineer | Tinkerer, Steamwright, Mechanic, Artificer |
| Merchant | Trader, Shopkeeper, Noble Merchant, Peddler |
| Farmer | Homesteader, Shepherd, Orchard Keeper, Miner |
| Pirate | Captain, Deckhand, Quartermaster, Corsair |
| Scientist | Chemist, Biologist, Physicist, Roboticist |
| Space Explorer | Astronaut, Star Marine, Pilot, Xenobotanist |
| Cyberpunk | Netrunner, Street Samurai, Fixer, Courier |

## Monsters: `monsters/`
Two layouts (see `monsters.json → layouts`):
* **character**: humanoids (skeletons, goblins, orcs, humanoid robots/aliens) use the character sheet above.
* **creature**: 5 columns × 5 rows (`idle 4`, `move 4`, `attack 4`, `hurt 2`, `death 5`), facing right. 32 × 32, bosses 64 × 64.

| Family | Count | Monsters |
|---|---|---|
| Slimes | 12 | green, blue, magma, frost, toxic, metal, gold, shadow, crystal, sprout, demon, arcane |
| Skeletons | 8 | warrior, archer, mage, knight, pirate, miner, lancer, bone priest |
| Goblins | 8 | grunt, archer, shaman, tinker, raider, thief, chief, buccaneer |
| Orcs | 8 | brute, berserker, warrior, shaman, hunter, warlord, pikeman, smith |
| Dragons | 8 | red, forest, storm, frost, gold, shadow, bone, amethyst whelps |
| Robots | 8 | security droid, worker bot, android, assault trooper, recon drone, roller bot, sentry turret, spider bot |
| Aliens | 8 | grey, reptilian trooper, insectoid soldier, psion, xeno blob, xeno crawler, sky jelly, plasma beetle |
| Shadow creatures | 8 | wraith, specter, reaper, shadow hound, gazer, void wisp, night bat, void crawler |
| **Bosses (64 px)** | 8 | Slime King, Elder Dragon, Frost Wyrm, Lich King, Shadow Lord, Stone Golem, Mech Titan, Alien Overmind |

## Equipment: `equipment/`
32 × 32 icons (+ `equipment_atlas.png`, 16 per row). `equipment.json` items include `slot` and the matching `character_layer` style. Categories: swords 8, axes 6, spears 5, bows 5, crossbows 4, staves 6, wands 5, shields 6, helmets 6, capes 5, armor 6.

## Environments: `environments/`
`tilesets/<biome>.png`: 256 × 128 atlas (see [GODOT_SETUP.md §4](GODOT_SETUP.md#4-tilemaps)).

| Biome | Base → secondary | Obstacles |
|---|---|---|
| village | grass → cobblestone | bush, fence, rock, barrel |
| forest | forest floor → dirt path | stump, log, bush, rock |
| desert | sand → hardpan | cactus, boulder, bones |
| swamp | bog → murky water | reeds, log, stump |
| snow | snow → frozen lake | snowy rock, ice block |
| dungeon | dungeon floor → abyss | stone wall, bones, pit, barrel |
| castle | flagstone → royal carpet | castle wall, barrel, rock |
| ruins | wild grass → ruined tiles | broken pillar, rock, bush |
| space_colony | regolith → hab plating | moon rock, solar panel, supply crate |
| research_lab | lab tile → hazard zone | barrier, pipe, crate |
| cyber_city | asphalt → neon sidewalk | hydrant, bollard, barrier, barrel |

`props/`: 20 biome props (trees 32 × 64 / 64 × 64, crystals, antenna, holo tree, statues…).

## Buildings: `buildings/`
`buildings.json` gives `size`, `size_tiles`, `collision_rect` (x, y, w, h from the sprite's top-left) and `door_tile`.

| Type | Size | Variants |
|---|---|---|
| small_houses | 96 × 96 | cottage, thatched hut, stone cottage, log cabin |
| large_houses | 128 × 128 | manor, townhouse, villa, hunting lodge |
| inns | 160 × 128 | 4 inns |
| shops | 96 × 96 | general store, potion shop, armory, bakery |
| farms | 128 × 128 | red barn & silo, barn, stable, granary |
| blacksmiths | 128 × 96 | 4 forges |
| wizard_towers | 64 × 160 | arcane, frost, dark, druid |
| castles | 192 × 192 | royal, dark citadel, desert palace, frost keep |
| space_habitats | 128 × 96 | hab dome, greenhouse, mining outpost, research module |
| futuristic_apartments | 96 × 192 | neon tower, corporate block, stack housing, skyline residences |

## Interiors: `interiors/`
* `tileset/interior_tileset.png`: 8 floors, 8 wall styles (upper + lower), wall cap, door mat, shaded floor.
* `rooms/<category>/<id>.png`: rendered room; `<id>.json`: `tiles` (atlas coords per cell), `furniture` (id, tile, pixel, size), `door_tile`.
* 35 rooms: 5 each of bedrooms, kitchens, taverns, workshops, libraries, laboratories, command centers.

## Furniture: `furniture/`
120 pieces in 3/4 view; `size` is 32 × 32, 64 × 32, 32 × 64 or 64 × 64 (origin = bottom-left tile).
tables 9 · beds 9 · chairs 10 · shelves 12 · crates 7 · barrels 7 · computers 6 · consoles 6 · decorations 54.

## Environmental animations: `animations/`
Horizontal strips; `animations.json` gives `frame_size`, `frames`, `fps`, `loop`.

| Category | Animations |
|---|---|
| water | water, deep water, swamp water, lava (32 × 32 tiles, 4 f), waterfall (32 × 64) |
| fire / torches | campfire (6 f), wall torch, standing torch, brazier (32 × 64) |
| doors | wooden door (32 × 64), castle portcullis (64 × 64), sliding airlock (32 × 64) |
| portals | arcane portal, warp gate (64 × 64, 8 f) |
| props / pickups / effects | chest opening, glowing crystals, red & blue flags, windmill (64 × 96), spinning coin, smoke puff |

## Palette & UI: `assets/`
* `palette/`: `palette.png` (1 × 348 strip), `ramps.png` chart, `palette.gpl` (GIMP / Aseprite / Krita), `palette.hex` (Lospec), `ramps.json`, `swap_keys.json`.
* `ui/`: 9-slice panel, inventory slots, heart / coin / mana / star icons, bar frames + fills.
