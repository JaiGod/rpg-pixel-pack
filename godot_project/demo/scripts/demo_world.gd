class_name DemoWorld
extends RefCounted
## Helpers shared by the demo scenes for spawning pack content by id.

static var _index: Dictionary = {}


static func _find(catalog_path: String, list_key: String, id: String) -> Dictionary:
	var key := catalog_path + ":" + id
	if _index.has(key):
		return _index[key]
	var cat: Dictionary = RPGSheet.catalog(catalog_path)
	for it in cat.get(list_key, []):
		_index[catalog_path + ":" + str(it["id"])] = it
	return _index.get(key, {})


## Static sprite with its origin at the bottom-center (for y-sorting) + optional collider.
static func add_static(parent: Node, tex_path: String, pos: Vector2, collider: Rect2 = Rect2()) -> StaticBody2D:
	var tex: Texture2D = load(RPGSheet.res_path(tex_path))
	var body := StaticBody2D.new()
	body.position = pos
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = false
	spr.offset = Vector2(-tex.get_width() / 2.0, -tex.get_height())
	body.add_child(spr)
	if collider.size != Vector2.ZERO:
		var cs := CollisionShape2D.new()
		var sh := RectangleShape2D.new()
		sh.size = collider.size
		cs.shape = sh
		cs.position = collider.position + collider.size / 2.0
		body.add_child(cs)
	parent.add_child(body)
	return body


static func add_building(parent: Node, id: String, bottom_center: Vector2) -> StaticBody2D:
	var b := _find("buildings/buildings.json", "items", id)
	if b.is_empty():
		push_warning("unknown building " + id)
		return null
	var w: float = b["size"][0]
	var h: float = b["size"][1]
	var cr: Array = b["collision_rect"]
	# collision_rect is in sprite pixels (top-left origin) -> convert to bottom-center origin
	var rect := Rect2(cr[0] - w / 2.0, cr[1] - h, cr[2], cr[3])
	return add_static(parent, b["file"], bottom_center, rect)


static func add_prop(parent: Node, id: String, bottom_center: Vector2, solid: bool = true) -> StaticBody2D:
	var p := _find("environments/environments.json", "props", id)
	if p.is_empty():
		push_warning("unknown prop " + id)
		return null
	var w: float = p["size"][0]
	var col := Rect2(-w * 0.15, -10, w * 0.3, 8) if solid else Rect2()
	return add_static(parent, p["file"], bottom_center, col)


static func add_furniture(parent: Node, id: String, bottom_center: Vector2, solid: bool = true) -> StaticBody2D:
	var f := _find("furniture/furniture.json", "items", id)
	if f.is_empty():
		return null
	var w: float = f["size"][0]
	return add_static(parent, f["file"], bottom_center, Rect2(-w / 2.0 + 3, -14, w - 6, 12) if solid else Rect2())


static func add_animation(parent: Node, id: String, bottom_center: Vector2) -> AnimatedSprite2D:
	var path := "%s/resources/frames/animations/%s.tres" % [RPGSheet.PACK, id]
	var spr := AnimatedSprite2D.new()
	spr.sprite_frames = load(path)
	spr.centered = false
	var tex: Texture2D = spr.sprite_frames.get_frame_texture(&"default", 0)
	spr.offset = Vector2(-tex.get_width() / 2.0, -tex.get_height())
	spr.position = bottom_center
	parent.add_child(spr)
	spr.play(&"default")
	return spr


static func preset_sheet(preset_id: String, sex: String) -> Texture2D:
	var cat: Dictionary = RPGSheet.catalog("characters/characters.json")
	for p in cat.get("presets", []):
		if p["id"] == preset_id:
			return load(RPGSheet.res_path("characters/" + p["files"][sex]))
	return null


static func make_label(text: String, size: int = 8, color: Color = Color(1, 1, 0.94)) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0.08, 0.06, 0.12))
	l.add_theme_constant_override("outline_size", 4)
	return l
