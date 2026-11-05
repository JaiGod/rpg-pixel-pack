extends Control
## Character creator: cycle every layer style and palette ramp, preview all animations.

var hero: LayeredCharacter
var cat: Dictionary
var state := {}
var _rows := {}
var _anim := "idle"

const ANIM_LIST := ["idle", "walk", "run", "attack", "hurt", "death"]


func _ready() -> void:
	cat = RPGSheet.catalog("characters/characters.json")
	var L: Dictionary = cat["layers"]
	var cloth := RPGSheet.ramp_names("cloth_")
	state = {
		"sex": ["male", "female"],
		"skin": L["body"]["styles"],
		"hair": [""] + _keys(L["hair"]["styles"]),
		"hair color": L["hair"]["colors"],
		"torso": _keys(L["torso"]["styles"]),
		"torso color": cloth,
		"trim color": cloth,
		"legs": _keys(L["legs"]["styles"]),
		"legs color": cloth,
		"head": [""] + _keys(L["head"]["styles"]),
		"head color": cloth,
		"cape": [""] + _keys(L["cape"]["styles"]),
		"accessory": [""] + _keys(L["accessory"]["styles"]),
		"weapon": [""] + _keys(L["weapon"]["styles"]),
		"offhand": [""] + _keys(L["offhand"]["styles"]),
	}
	var bg := ColorRect.new()
	bg.color = Color(0.16, 0.15, 0.24)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var panel := VBoxContainer.new()
	panel.position = Vector2(12, 8)
	panel.add_theme_constant_override("separation", 0)
	add_child(panel)
	for key in state:
		var row := HBoxContainer.new()
		var name_l := DemoWorld.make_label(key, 8, Color(0.8, 0.8, 0.95))
		name_l.custom_minimum_size = Vector2(70, 0)
		row.add_child(name_l)
		var prev := Button.new()
		prev.text = "<"
		prev.add_theme_font_size_override("font_size", 8)
		prev.pressed.connect(_step.bind(key, -1))
		row.add_child(prev)
		var val := DemoWorld.make_label("", 8)
		val.custom_minimum_size = Vector2(96, 0)
		val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		row.add_child(val)
		var nxt := Button.new()
		nxt.text = ">"
		nxt.add_theme_font_size_override("font_size", 8)
		nxt.pressed.connect(_step.bind(key, 1))
		row.add_child(nxt)
		panel.add_child(row)
		_rows[key] = {"values": state[key], "i": 0, "label": val}
	_rows["torso color"]["i"] = cloth.find("cloth_blue")
	_rows["trim color"]["i"] = cloth.find("cloth_yellow")
	_rows["legs color"]["i"] = cloth.find("cloth_brown")
	_rows["head color"]["i"] = cloth.find("cloth_red")
	_rows["hair"]["i"] = 1
	hero = LayeredCharacter.new()
	hero.position = Vector2(470, 210)
	hero.scale = Vector2(5, 5)
	add_child(hero)
	var anims := HBoxContainer.new()
	anims.position = Vector2(330, 300)
	add_child(anims)
	for a in ANIM_LIST:
		var b := Button.new()
		b.text = a
		b.add_theme_font_size_override("font_size", 8)
		b.pressed.connect(_set_anim.bind(a))
		anims.add_child(b)
	var dirs := HBoxContainer.new()
	dirs.position = Vector2(372, 324)
	add_child(dirs)
	for d in [["down", Vector2.DOWN], ["up", Vector2.UP], ["left", Vector2.LEFT], ["right", Vector2.RIGHT]]:
		var b := Button.new()
		b.text = d[0]
		b.add_theme_font_size_override("font_size", 8)
		b.pressed.connect(_face.bind(d[1]))
		dirs.add_child(b)
	var rnd := Button.new()
	rnd.text = "Randomize"
	rnd.position = Vector2(420, 20)
	rnd.pressed.connect(_randomize)
	add_child(rnd)
	_apply()


func _keys(d: Variant) -> Array:
	return d.keys() if d is Dictionary else d


func _val(key: String) -> String:
	var r: Dictionary = _rows[key]
	return str(r["values"][r["i"]])


func _step(key: String, d: int) -> void:
	var r: Dictionary = _rows[key]
	r["i"] = posmod(r["i"] + d, r["values"].size())
	_apply()


func _randomize() -> void:
	for key in _rows:
		_rows[key]["i"] = randi() % _rows[key]["values"].size()
	_apply()


func _apply() -> void:
	for key in _rows:
		var v := _val(key)
		_rows[key]["label"].text = v.replace("cloth_", "").replace("hair_", "").replace("skin_", "") if v != "" else "(none)"
	hero.sex = _val("sex")
	hero.set_layer("body", _val("skin"))
	hero.set_hair(_val("hair"), _val("hair color"))
	hero.set_layer("torso", _val("torso"), _val("torso color"), _val("trim color"))
	hero.set_layer("legs", _val("legs"), _val("legs color"), "leather")
	hero.set_layer("head", _val("head"), _val("head color"), _val("trim color"))
	hero.set_layer("cape", _val("cape"), _val("torso color"), _val("trim color"))
	var acc := _val("accessory")
	hero.set_layer("accessory", acc, _val("hair color") if acc == "beard" else _val("torso color"), _val("trim color"))
	hero.set_layer("weapon", _val("weapon"))
	hero.set_layer("offhand", _val("offhand"), _val("torso color"), _val("trim color"))
	hero.play_anim(_anim, true)


func _set_anim(a: String) -> void:
	_anim = a
	hero.play_anim(a, true)


func _face(v: Vector2) -> void:
	hero.face(v)
