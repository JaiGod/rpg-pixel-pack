# Customization system

Characters are built from **independent layer sheets** that share one pose model, so every combination lines up frame-perfectly. Each layer is a full 192 × 576 sheet (6 × 18 frames of 32 × 32).

```
characters/layers/<male|female>/<layer>/<style>.png
```

## Layers and styles

| Layer | Styles | Tint |
|---|---|---|
| `body` | `skin_porcelain`, `skin_light`, `skin_tan`, `skin_olive`, `skin_brown`, `skin_deep` | none (baked skin) |
| `hair` (+ `hair_back` for long hair) | `short`, `spiky`, `long`, `ponytail`, `bob`, `bun`, `mohawk`, `braids`, `bald`, `curly`, `sidepart`, `pigtails` | primary = hair color |
| `torso` | `tunic`, `plate`, `leather`, `robe`, `overalls`, `vest`, `coat`, `labcoat`, `spacesuit`, `cyberjacket`, `shirt`, `dress`, `hooded_cloak`, `chainmail` | primary + secondary |
| `legs` | `pants`, `boots`, `greaves`, `shorts`, `skirt`, `suit`, `robe`, `cyber` | primary + secondary |
| `head` | `knight_helm`, `viking_helm`, `hood`, `wizard_hat`, `necro_cowl`, `bandana`, `tricorn`, `straw_hat`, `goggles`, `space_helmet`, `cyber_visor`, `cap`, `turban`, `circlet`, `feather_hat` | primary + secondary |
| `accessory` | `beard`, `glasses`, `eyepatch`, `mask`, `scarf`, `headphones` | primary (+ secondary) |
| `cape` | `cape`, `tattered_cape` | primary + secondary |
| `weapon` | `sword`, `greatsword`, `axe`, `spear`, `bow`, `crossbow`, `staff`, `necro_staff`, `wand`, `dagger`, `hammer`, `wrench`, `blaster`, `katana`, `hoe`, `scythe`, `cutlass`, `flask`, `pickaxe`, `scanner` | none |
| `offhand` | `round_shield`, `kite_shield`, `buckler`, `tome`, `lantern`, `energy_shield` | `kite_shield`, `tome` |

**Draw order:** `hair_back → body → legs → torso → cape → hair → head → accessory → offhand → weapon`.
Headgear `knight_helm`, `space_helmet`, `hood` and `necro_cowl` hide the hair.

Weapons animate with their own attack style: **swing** (swords, axes, hammers, tools), **thrust** (spear, dagger), **shoot** (bows, crossbows, guns, flask; with arrow / muzzle flash) and **cast** (staves, wands; with a sparkle on the impact frame).

## Palette swap

Tintable layers are drawn with two 4-shade **key ramps** instead of final colors:

| Channel | Keys (dark → light) |
|---|---|
| primary | `#3c3c3c` `#6e6e6e` `#a5a5a5` `#dcdcdc` |
| secondary | `#34285c` `#5c4898` `#8c78cc` `#beb0ec` |

Any ramp from [`assets/palette/ramps.json`](../assets/palette/ramps.json) can replace them:

* **In Godot:** `LayeredCharacter.set_layer(kind, style, "cloth_red", "gold")` sets the uniforms of `palette_swap.gdshader` for you. You can also put the shader on any `CanvasItem` and set `primary_0..3` / `secondary_0..3` yourself.
* **In the browser demo / Python:** the same exact-color replacement (`Canvas.recolor(key_map(primary, secondary))` in `tools/rpgpack/core.py`).

Ramp families: 16 `cloth_*`, 8 `hair_*`, 6 `skin_*`, metals (`iron`, `steel`, `gold`, `bronze`, `silver`), gems (`crystal`, `amethyst`, `ruby`, `emerald`), magic & neon (`magic_blue`, `magic_purple`, `neon_pink`, `neon_cyan`, `neon_green`, `fire`, `poison`) and nature, building and tech ramps.

## Baked presets

`characters/presets/<class>/<id>_<sex>.png` are the 52 presets with layers and colors baked in, for when you don't need runtime customization. The recipe for each one (layer, style, primary, secondary) is in `characters/characters.json → presets[].layer_recipe`.

## Making your own sheet without code
Use the **[web Character Creator](https://jaigod.github.io/rpg-pixel-pack/#creator)** → *Download sprite sheet*, then in Godot:
```gdscript
$AnimatedSprite2D.sprite_frames = RPGSheet.character_frames(load("res://hero.png"))
```

## Adding a new style
1. Add a style to the dict in `tools/rpgpack/characters.py` (e.g. a new `elif style == 'samurai':` branch in `draw_torso`).
2. `python tools/generate_all.py`. It renders both body types, every animation and direction, and updates the Godot project and web demo.
