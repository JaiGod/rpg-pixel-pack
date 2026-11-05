# Godot 4 setup guide

Requires **Godot 4.3 or newer** (uses `TileMapLayer`, static vars and `AnimatedSprite2D.frame_progress`). No C# needed.

## 1. Run the demo project

1. Open the Godot Project Manager → **Import** → choose `godot_project/project.godot`.
2. The first import takes a few seconds (≈700 PNGs).
3. Press **F5**. From the menu:

| Demo | What it shows | Controls |
|---|---|---|
| **Village** | terrain-painted `TileMapLayer`, buildings with collision, y-sorting, NPCs, monsters, animated props | WASD / arrows move · Shift run · Space attack · E talk |
| **Character Creator** | every layer, style and palette ramp on a `LayeredCharacter` | click `<` `>` · animation & direction buttons · Randomize |
| **Inventory & Equipment** | `Inventory` + `EquipmentComponent` + `InventoryUI`; equipping changes the visual layers | click items · arrows rotate the hero |
| **Interiors** | `RoomLoader` building all 35 rooms from JSON | Q / R previous / next room |
| **Asset Gallery** | all 76 monster `SpriteFrames` + 21 environment animations | mouse wheel / arrows to scroll |

**Esc** returns to the menu from any demo.

## 2. Add the pack to your own project

Copy `godot_project/rpg_pixel_pack/` to your project root so it lives at **`res://rpg_pixel_pack/`** (scripts and resources use that path).

**Recommended project settings**

| Setting | Value | Why |
|---|---|---|
| Rendering → Textures → Canvas Textures → Default Texture Filter | **Nearest** | crisp pixel art |
| Display → Window → Size → Viewport | **640 × 360** (window override 1280 × 720) | 32-px tiles at a comfortable scale |
| Display → Window → Stretch → Mode / Scale Mode | **canvas_items** / **integer** | sharp scaling |
| Rendering → 2D → Snap 2D Transforms to Pixel | **On** | no sub-pixel shimmer |
| Autoload | `res://rpg_pixel_pack/scripts/input_setup.gd` (optional) | creates the input actions used by the controllers |

If you don't use the autoload, create these Input Map actions yourself:
`move_left`, `move_right`, `move_up`, `move_down`, `run`, `attack`, `interact`, `inventory`.

**Exporting:** the scripts read JSON catalogs at runtime. In your export preset add
`*.json` to **Resources → Filters to export non-resource files/folders**.

## 3. AnimatedSprite2D

Ready-made `SpriteFrames` resources:

```
rpg_pixel_pack/resources/frames/characters/<preset>_<male|female>.tres   (104)
rpg_pixel_pack/resources/frames/monsters/<monster_id>.tres                (76)
rpg_pixel_pack/resources/frames/animations/<animation_id>.tres            (21)
```

**Character / humanoid monster animations** (18): `idle_down`, `idle_up`, `idle_side`, `walk_*`, `run_*`, `attack_*`, `hurt_*`, `death_*`.
`side` faces **right**; set `flip_h = true` for left. `attack`, `hurt` and `death` don't loop.

**Creature monster animations** (5): `idle`, `move`, `attack`, `hurt`, `death`, facing right.

Sprite origin: frames are 32 × 32 with the feet at y≈30. Put the `AnimatedSprite2D` at `position = (0, -14)` under a body whose origin is the feet, and enable **Y Sort** on the parent.

Need frames for a sheet you made yourself (e.g. one exported from the web Character Creator)?
```gdscript
$Sprite.sprite_frames = RPGSheet.character_frames(load("res://my_hero.png"))
```

## 4. TileMaps

Each biome has `rpg_pixel_pack/resources/tilesets/<biome>.tres`:

* **Terrain set 0, mode *Match Corners***: terrain 0 = base ground, terrain 1 = secondary (path / water / carpet…). Select a `TileMapLayer` → **TileMap** panel → **Terrains** tab and paint.
* Row 0 base variants have probability 1.0 (decorated variants 0.15), giving natural variation.
* Row 3 columns 4-7 are **obstacles with collision** (physics layer 0).

From code (deterministic, no terrain solver needed):
```gdscript
var c := RPGTerrain.empty_corners(40, 24)        # (w+1) x (h+1) corner grid, 0 = base
RPGTerrain.fill_rect(c, Rect2i(0, 11, 40, 1))    # 1 = secondary terrain
RPGTerrain.paint($Ground, c)
RPGTerrain.obstacle($Ground, Vector2i(3, 3), 0)  # solid tile
```

Atlas layout (8 × 4 tiles of 32 px):

| Row | Columns 0-3 | Columns 4-7 |
|---|---|---|
| 0 | base ground variants | decorated base ground |
| 1-2 | 16 transition tiles, index = TL·8 + TR·4 + BL·2 + BR | ← continued |
| 3 | secondary terrain variants | obstacles (collision) |

**Interiors:** `resources/tilesets/interior.tres`, row 0 = 8 floors, rows 1-2 = 8 wall styles (upper/lower, with collision), row 3 = wall cap / door mat / shaded floor. `RoomLoader` builds any of the 35 rooms.

## 5. Characters & customization

```gdscript
var hero := LayeredCharacter.new()   # or instance prefabs/layered_character.tscn
add_child(hero)
hero.set_layer("torso", "robe", "cloth_purple", "gold")
hero.set_hair("long", "hair_silver")
hero.face(Vector2.UP)
hero.play_anim("walk")
hero.flash()                         # hit flash (shader uniform)
hero.action_finished.connect(func(anim): print(anim, " done"))
```

Layer kinds (draw order): `hair_back, body, legs, torso, cape, hair, head, accessory, offhand, weapon`.
See [CUSTOMIZATION.md](CUSTOMIZATION.md) for every style name and how palette swapping works.

## 6. Controllers

| Script | Node | Notes |
|---|---|---|
| `PlayerController` | `CharacterBody2D` + child `Visual` (`LayeredCharacter` or `CharacterSprite`) | 4-way movement, run, melee attack hits nodes in group `monsters`, `interact` calls `interact(player)` on the nearest node in group `interactable`; signals `health_changed`, `died` |
| `NPCController` | `CharacterBody2D` + `Visual` | wanders around its spawn, speech bubble, signal `talked(name, line)` |
| `MonsterController` | `CharacterBody2D` | set `monster_id`; loads the right sheet + layout from `monsters.json`; wander / chase / attack / hurt / death |

## 7. Inventory & equipment

```gdscript
var inv := Inventory.new()                     # Resource: save it with ResourceSaver
inv.load_items(PackedStringArray(["sword_iron", "shield_kite"]))
var eq := EquipmentComponent.new()
eq.character_path = ^"../Hero"
add_child(eq)
eq.equip(inv.remove_at(0))                      # hero now holds a sword
var ui := InventoryUI.new()
$CanvasLayer.add_child(ui)
ui.inventory = inv
ui.equipment = eq
```

Each `ItemData` (`resources/items/*.tres`) has `slot`, `layer_style`, `primary_ramp`, `secondary_ramp`, `attack`, `defense`, `magic`, `value` and an `icon`. Make new items in the Inspector: **New Resource → ItemData**.

## 8. Troubleshooting

* **Blurry sprites**: set the default texture filter to *Nearest* (or `texture_filter = Nearest` on the node).
* **Tintable layers look grey/purple**: they need the palette-swap shader (`LayeredCharacter` adds it automatically) or bake colors with the Python tools.
* **JSON not found in an exported build**: add `*.json` to the export filters (see §2).
* **Player walks over NPCs/monsters**: they share collision layer 1 by default; adjust layers/masks to taste.
