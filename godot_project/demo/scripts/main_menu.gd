extends Control
## Demo launcher.

const SCENES := [
	["Village (play)", "res://demo/village_demo.tscn", "Walk, run, attack slimes, talk to NPCs."],
	["Character Creator", "res://demo/character_creator.tscn", "Mix every layer, color and animation."],
	["Inventory & Equipment", "res://demo/inventory_demo.tscn", "Equip items and watch the character change."],
	["Interiors", "res://demo/interior_demo.tscn", "Walk through all 35 furnished rooms."],
	["Asset Gallery", "res://demo/gallery_demo.tscn", "Every monster and environmental animation."],
]


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.13, 0.12, 0.2)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var cat: Dictionary = RPGSheet.catalog("characters/characters.json")
	var box := VBoxContainer.new()
	box.position = Vector2(160, 40)
	box.custom_minimum_size = Vector2(320, 0)
	box.add_theme_constant_override("separation", 6)
	add_child(box)
	var title := DemoWorld.make_label("RPG PIXEL PACK", 20, Color(1, 0.86, 0.45))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(title)
	var sub := DemoWorld.make_label("Godot 4 demo · %d presets · Esc returns here" % cat.get("presets", []).size(), 8, Color(0.75, 0.74, 0.88))
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(sub)
	for s in SCENES:
		var b := Button.new()
		b.text = s[0]
		b.tooltip_text = s[2]
		b.add_theme_font_size_override("font_size", 10)
		b.custom_minimum_size = Vector2(320, 28)
		b.pressed.connect(get_tree().change_scene_to_file.bind(s[1]))
		box.add_child(b)
	# parade of characters along the bottom
	var presets: Array = cat.get("presets", [])
	for i in 14:
		var p: Dictionary = presets[(i * 4) % presets.size()]
		var spr := CharacterSprite.new()
		spr.sheet = load(RPGSheet.res_path("characters/" + p["files"]["male" if i % 2 == 0 else "female"]))
		spr.start_direction = "side"
		spr.position = Vector2(30 + i * 44, 330)
		spr.scale = Vector2(1, 1)
		add_child(spr)
		spr.direction = "side"
		spr.play_anim("walk", true)
