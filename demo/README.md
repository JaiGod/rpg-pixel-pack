# Demos

## 🌐 Web demo (play in the browser)
**https://jaigod.github.io/rpg-pixel-pack/**

Source: [`web/`](web). `tools/generate_all.py` copies it to [`../docs/`](../docs) together with the art (`docs/pack/`) and a `data.js` built from the JSON catalogs. GitHub Pages serves `docs/` from the `main` branch.

* **Play**: a walkable village with NPCs to talk to and slimes to fight (keyboard or on-screen touch controls).
* **Character Creator**: every layer and palette ramp, live animation preview, and an exportable 192 × 576 sprite sheet.
* **Gallery**: all 76 monsters and 21 environmental animations, animated.

Run it locally (the canvas recoloring needs http, not `file://`):
```bash
cd docs && python -m http.server 8000   # then open http://localhost:8000
```

## 🎮 Godot demo scenes
Open `godot_project/project.godot` in Godot 4.3+ and press F5.

| Scene | File |
|---|---|
| Menu | `godot_project/demo/main_menu.tscn` |
| Village (playable) | `godot_project/demo/village_demo.tscn` |
| Character Creator | `godot_project/demo/character_creator.tscn` |
| Inventory & Equipment | `godot_project/demo/inventory_demo.tscn` |
| Interiors | `godot_project/demo/interior_demo.tscn` |
| Asset Gallery | `godot_project/demo/gallery_demo.tscn` |

See [`../docs/GODOT_SETUP.md`](../docs/GODOT_SETUP.md).
